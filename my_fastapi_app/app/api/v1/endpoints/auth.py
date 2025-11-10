from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.services.user_service import UserService
from app.core.security import create_access_token
from app.core.config import get_settings
from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()
settings = get_settings()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
            summary="Register New User",
            description="Create a new user account")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **username**: Username (3-50 characters, must be unique)
    - **password**: Password (minimum 6 characters)
    - **full_name**: Optional full name
    
    Returns the created user information (without password).
    """
    # Check if user already exists
    db_user = UserService.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    db_user = UserService.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create new user
    return UserService.create_user(db=db, user=user)

@router.post("/login", 
            response_model=Token,
            status_code=status.HTTP_200_OK,
            summary="User Login",
            description="Authenticate user and get JWT access token",
            responses={
                200: {
                    "description": "Successful login",
                    "content": {
                        "application/json": {
                            "example": {
                                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "token_type": "bearer"
                            }
                        }
                    }
                },
                401: {
                    "description": "Incorrect username or password",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Incorrect username or password"}
                        }
                    }
                },
                422: {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": [
                                    {
                                        "type": "string_too_short",
                                        "loc": ["body", "username"],
                                        "msg": "String should have at least 3 characters"
                                    }
                                ]
                            }
                        }
                    }
                }
            })
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with username and password to get access token.
    
    - **username**: Your username (3-50 characters)
    - **password**: Your password (minimum 6 characters)
    
    Returns a JWT access token that expires in 30 minutes by default.
    Use this token in the Authorization header as: `Bearer <token>`
    """
    user = UserService.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", 
           response_model=UserResponse,
           summary="Get Current User",
           description="Get information about the currently authenticated user",
           responses={
               200: {
                   "description": "Current user information",
                   "content": {
                       "application/json": {
                           "example": {
                               "id": 1,
                               "email": "john.doe@example.com",
                               "username": "johndoe",
                               "full_name": "John Doe",
                               "is_active": True,
                               "created_at": "2025-11-10T14:30:00Z"
                           }
                       }
                   }
               },
               401: {
                   "description": "Invalid or expired token",
                   "content": {
                       "application/json": {
                           "example": {"detail": "Could not validate credentials"}
                       }
                   }
               }
           })
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get current user profile information.
    
    **Authentication Required**: This endpoint requires a valid JWT token.
    
    1. Login to get your JWT token
    2. Click the **Authorize** button above
    3. Enter: `Bearer <your_token>`
    
    Returns user details including ID, email, username, and account status.
    """
    return current_user
