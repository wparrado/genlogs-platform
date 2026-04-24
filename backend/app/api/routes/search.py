"""Search route placeholder — not yet implemented."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/search")
def search() -> JSONResponse:
    """Placeholder search endpoint. Business logic not yet implemented."""
    return JSONResponse(
        status_code=501,
        content={"detail": "Search endpoint not yet implemented."},
    )
