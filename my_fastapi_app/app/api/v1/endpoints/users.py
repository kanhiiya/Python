from typing import Annotated
from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get user profile (protected route)"""
    return current_user
