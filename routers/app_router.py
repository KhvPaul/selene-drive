from fastapi import APIRouter

router = APIRouter(prefix="/app", tags=["App"])


@router.get("/health_check")
def hello_world():
    return {"message": "Hello, World!"}
