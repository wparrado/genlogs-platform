"""GenLogs backend application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import health, search, cities, metrics
from app.logging_config import configure_logging
from app.providers.logging_provider import get_logger
from app.utils.redaction import redact_pii, redact_text_pii, redact_headers
from starlette.responses import Response

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
except Exception:
    _db_engine = None

try:
    instrument_app(app, engine=_db_engine)
except Exception:
    # non-fatal
    pass

import os

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
    # Determine or generate a request id and bind it to the context for all log records
    from app.utils.request_id import set_request_id, generate_request_id, reset_request_id

    incoming = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    req_id = incoming or generate_request_id()
    token = set_request_id(req_id)

    # Start a root span for this incoming HTTP request (no-op if OTEL not installed)
    span_ctx = get_tracer("http.server").start_as_current_span(f"{request.method} {request.url.path}")
    span = None
    # Enter the span context and try to retrieve the underlying span object
    try:
        span = span_ctx.__enter__()
    except Exception:
        try:
            # Some tracer implementations return a contextmanager whose __enter__ returns None
            span = None
        except Exception:
            span = None

    # Attach attributes: request_id and basic request info
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

    try:
        # Read and attempt to parse request body for logging (may be empty)
        body_bytes = await request.body()
        body_json = None
        if body_bytes:
            try:
                import json

                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                body_json = None

        redacted_req_body = redact_pii(body_json) if body_json is not None else None
        redacted_headers = redact_headers(dict(request.headers))
        logger.info("request.start", extra={"method": request.method, "path": request.url.path, "body": redacted_req_body, "headers": redacted_headers, "request_id": req_id})

        response = await call_next(request)

        # Decide whether to buffer response body based on content-type
        content_type = (response.headers.get("content-type") or "").split(";")[0].lower()
        should_buffer = ("json" in content_type) or content_type.startswith("text/")

        if should_buffer:
            # Capture response body (buffer it) so we can inspect and re-create the response
            resp_body = b""
            async for chunk in response.body_iterator:
                resp_body += chunk

            # Rebuild response to return the same content to the client
            new_response = Response(content=resp_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
            # Attach request id header so callers can correlate
            new_response.headers["X-Request-ID"] = req_id

            # If error status, attempt to log/redact response body
            if response.status_code >= 400:
                # attach status to span
                try:
                    if span is not None and hasattr(span, "set_attribute"):
                        span.set_attribute("http.status_code", int(response.status_code))
                except Exception:
                    pass
                redacted_resp = None
                try:
                    import json

                    resp_text = resp_body.decode("utf-8")
                    try:
                        resp_json = json.loads(resp_text)
                        redacted_resp = redact_pii(resp_json)
                    except Exception:
                        redacted_resp = redact_text_pii(resp_text)
                except Exception:
                    redacted_resp = None

                logger.warning("response.error", extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "response": redacted_resp,
                    "headers": redact_headers(dict(response.headers)),
                })

            try:
                # attach status to span for successful responses as well
                if span is not None and hasattr(span, "set_attribute"):
                    span.set_attribute("http.status_code", int(response.status_code))
            except Exception:
                pass

            logger.info("request.end", extra={"method": request.method, "path": request.url.path, "status_code": response.status_code, "headers": redact_headers(dict(response.headers))})
            return new_response
        else:
            # Do not buffer binary/streaming responses — just log headers and status
            # Attach request id header for correlation
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


app.include_router(health.router)
app.include_router(search.router, prefix="/api")
app.include_router(cities.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")


from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
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
    # Validation errors are typically 422 but may be surfaced as 400 in some flows.
    errors = exc.errors()
    logger.warning("validation.exception", extra={
        "method": request.method,
        "path": request.url.path,
        "status_code": 422,
        "errors": errors,
    })
    return JSONResponse(status_code=422, content={"detail": errors})
