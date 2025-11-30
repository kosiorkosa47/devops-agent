"""
User management endpoints (placeholder)
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_current_user

router = APIRouter()


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    name: str


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.get("sub", "user-1"),
        email=current_user.get("email", "user@devops-agent.local"),
        name=current_user.get("name", "DevOps User")
    )
