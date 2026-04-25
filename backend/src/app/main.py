"""GenLogs backend application entry point."""
import os
import json

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.responses import Response

from app.api.routes import health, search, cities, metrics
from app.logging_config import configure_logging
from app.providers.logging_provider import get_logger
from app.utils.redaction import (
    redact_pii,
    redact_text_pii,
    redact_headers,
)
from app.utils.request_id import (
    set_request_id,
    generate_request_id,
    reset_request_id,
)

# Configure structured logging as early as possible
configure_logging()
from app.telemetry import init_tracing, get_tracer, instrument_app

# Initialize tracing (no-op if OpenTelemetry not installed)
init_tracing()
logger = get_logger("app")

app = FastAPI(title="GenLogs API", version="0.1.0")

# Development-friendly CORS so the Vite dev server can call the API.
# Keep this narrow and only enable the local dev hosts; production should
# configure a stricter policy via environment/config.
# For local development allow all origins to simplify the dev flow. In
# production this should be set to a restricted list.
# Restrict CORS to the local Vite dev origin for development

# Attempt to auto-instrument FastAPI/requests/SQLAlchemy when OTEL is available
try:
    from app.providers.db.db import engine as _db_engine
except ImportError:
    _db_engine = None

try:
    instrument_app(app, engine=_db_engine)
except Exception as exc:
    # non-fatal - instrumentation best-effort
    logger.exception("instrumentation failed", exc_info=exc)

# Configure CORS origins from environment for safer production settings.
# Format: comma-separated list, e.g. "https://site1.example,https://site2.example"
_cors_env = os.getenv("GENLOGS_CORS_ORIGINS")
if _cors_env:
    _allow_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    # sensible defaults for local development
    _allow_origins = ["http://localhost:5173", "http://localhost:5175"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Top-level HTTP middleware orchestrating request/response logging and tracing.

    This function delegates parsing, redaction and response handling to helpers
    to keep the control flow simple and reduce local variable churn.
    """

    incoming = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    req_id = incoming or generate_request_id()
    token = set_request_id(req_id)

    span_ctx = get_tracer("http.server").start_as_current_span(f"{request.method} {request.url.path}")
    span = _enter_span(span_ctx)

    _attach_span_attrs_safe(span, req_id, request)

    try:
        body_json = await _read_request_body_safe(request)
        redacted_req_body = redact_pii(body_json) if body_json is not None else None
        redacted_headers = redact_headers(dict(request.headers))
        logger.info("request.start", extra={"method": request.method, "path": request.url.path, "body": redacted_req_body, "headers": redacted_headers, "request_id": req_id})

        response = await call_next(request)

        content_type = (response.headers.get("content-type") or "").split(";")[0].lower()
        should_buffer = ("json" in content_type) or content_type.startswith("text/")

        if should_buffer:
            return await _handle_buffered_response(response, request, req_id, span)
        else:
            return _handle_nonbuffered_response(response, request, req_id, span)

    except Exception:
        logger.exception("unhandled.exception", extra={"method": request.method, "path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "internal server error"})
    finally:
        # Always clear context var to avoid leaking request id across requests
        try:
            reset_request_id(token)
        except Exception:
            pass
        try:
            span_ctx.__exit__(None, None, None)
        except Exception:
            pass


def _enter_span(span_ctx):
    """Enter tracer span context and return span object if available.

    Some tracer implementations return None from __enter__ so this helper
    normalizes to either a span object or None.
    """
    try:
        return span_ctx.__enter__()
    except Exception:
        try:
            return None
        except Exception:
            return None


def _attach_span_attrs_safe(span, req_id: str, request: Request) -> None:
    """Attach common attributes to the span if supported. Swallows errors.

    Attempts to capture request id, method, path and enduser id when available.
    """
    try:
        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("request.id", req_id)
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.target", request.url.path)

            # attempt to capture user id if available
            user_id = None
            if "x-user-id" in request.headers:
                user_id = request.headers.get("x-user-id")
            elif hasattr(request.state, "user"):
                try:
                    user_obj = request.state.user
                    user_id = getattr(user_obj, "id", None) or getattr(user_obj, "user_id", None)
                except Exception:
                    user_id = None
            if user_id:
                span.set_attribute("enduser.id", str(user_id))
    except Exception:
        # non-fatal
        pass


async def _read_request_body_safe(request: Request):
    """Read request body and return parsed JSON when possible.

    Returns None if body empty or parsing fails.
    """
    try:
        body_bytes = await request.body()
        if not body_bytes:
            return None
        try:
            return json.loads(body_bytes.decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None
    except Exception:
        return None


async def _handle_buffered_response(response: Response, request: Request, req_id: str, span):
    """Buffer response body, redact when necessary, log and return a rebuilt Response.

    Preserves headers and media_type.
    """
    resp_body = b""
    async for chunk in response.body_iterator:
        resp_body += chunk

    new_response = Response(content=resp_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    new_response.headers["X-Request-ID"] = req_id

    # If error status, attempt to log/redact response body
    if response.status_code >= 400:
        try:
            if span is not None and hasattr(span, "set_attribute"):
                span.set_attribute("http.status_code", int(response.status_code))
        except Exception:
            pass

        redacted_resp = None
        try:
            resp_text = resp_body.decode("utf-8")
            try:
                resp_json = json.loads(resp_text)
                redacted_resp = redact_pii(resp_json)
            except (ValueError, json.JSONDecodeError):
                redacted_resp = redact_text_pii(resp_text)
        except (UnicodeDecodeError, OSError):
            redacted_resp = None

        logger.warning("response.error", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "response": redacted_resp,
            "headers": redact_headers(dict(response.headers)),
        })

    try:
        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("http.status_code", int(response.status_code))
    except Exception:
        pass

    logger.info("request.end", extra={"method": request.method, "path": request.url.path, "status_code": response.status_code, "headers": redact_headers(dict(response.headers))})
    return new_response


def _handle_nonbuffered_response(response: Response, request: Request, req_id: str, span):
    """Handle non-buffered (binary/streaming) responses: add headers and log summary."""
    response.headers["X-Request-ID"] = req_id
    try:
        if span is not None and hasattr(span, "set_attribute"):
            span.set_attribute("http.status_code", int(response.status_code))
    except Exception:
        pass

    logger.info("request.end", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "headers": redact_headers(dict(response.headers)),
        "body": "[omitted]",
    })
    return response


app.include_router(health.router)
app.include_router(search.router, prefix="/api")
app.include_router(cities.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException by logging and returning a JSON response.

    The handler logs the HTTP exception details and returns a JSON payload
    with the provided detail.
    """
    # Log HTTP exceptions (e.g., 400) including the provided detail/reason.
    logger.warning("http.exception", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": exc.status_code,
        "reason": exc.detail,
    })
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors by logging and returning a 422 JSON body."""
    # Validation errors are typically 422 but may be surfaced as 400 in some flows.
    errors = exc.errors()
    logger.warning("validation.exception", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": 422,
        "errors": errors,
    })
    return JSONResponse(status_code=422, content={"detail": errors})
