from fastapi import APIRouter
from app.api.endpoints import advisor

api_router = APIRouter()
api_router.include_router(advisor.router, prefix="/advisor", tags=["advisor"])
