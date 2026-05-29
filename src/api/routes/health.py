from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check. Returns 200 if the server is running."""
    return {"status": "healthy", "service": "codesentinel-ai"}
