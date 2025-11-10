from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    quantity: int
    created_at: datetime
    
    class Config:
        from_attributes = True
