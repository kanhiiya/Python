from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.services.item_service import ItemService
from app.api.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """Create a new item (requires authentication)"""
    return ItemService.create_item(db, item)

@router.get("", response_model=List[ItemResponse])
def get_items(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """Get all items with pagination (requires authentication)"""
    return ItemService.get_items(db, skip, limit)

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """Get a specific item by ID (requires authentication)"""
    item = ItemService.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """Update an item (requires authentication)"""
    updated_item = ItemService.update_item(db, item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_active_user)] = None
):
    """Delete an item (requires authentication)"""
    if not ItemService.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}
