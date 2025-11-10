from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com", 
                           description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, 
                         example="johndoe",
                         description="Unique username")
    full_name: Optional[str] = Field(None, example="John Doe",
                                   description="User's full name (optional)")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, 
                         example="securepassword123",
                         description="Password for the new account")

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, 
                         example="johndoe",
                         description="Username for login")
    password: str = Field(..., min_length=6, 
                         example="securepassword123",
                         description="User password")

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str = Field(..., 
                             example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                             description="JWT access token")
    token_type: str = Field(..., 
                           example="bearer",
                           description="Token type (always 'bearer')")

class TokenData(BaseModel):
    username: Optional[str] = None