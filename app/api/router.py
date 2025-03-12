from fastapi import APIRouter, Depends
from app.api.endpoints import advisor
from app.api.dependencies import get_token_header

# Main API router
api_router = APIRouter()

# Public endpoints (no authentication)
api_router.include_router(advisor.router, prefix="/advisor", tags=["advisor"])

# Example of protected endpoints (with authentication)
# Create a separate router for authenticated routes
auth_router = APIRouter(dependencies=[Depends(get_token_header)])
# Include any protected endpoints here
# auth_router.include_router(some_protected_endpoints, prefix="/protected", tags=["protected"])

# Include the auth router in the main API router
# api_router.include_router(auth_router, prefix="/auth")
