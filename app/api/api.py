from fastapi import APIRouter
from app.api.endpoints import summarizer
from app.api.endpoints import history

api_router = APIRouter()
api_router.include_router(summarizer.router, prefix="/v1", tags=["summarizer"])
api_router.include_router(history.router, prefix="/v1/history", tags=["history"]) 