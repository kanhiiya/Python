from sqlalchemy.orm import Session
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate
from app.core.cache import cache_service
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ItemService:
    @staticmethod
    def create_item(db: Session, item: ItemCreate) -> Item:
        db_item = Item(**item.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    async def get_items(db: Session, skip: int = 0, limit: int = 10) -> List[Item]:
        cache_key = f"items:list:{skip}:{limit}"
        
        # Try cache first
        cached_items = await cache_service.get(cache_key)
        if cached_items:
            logger.info("Cache hit for items list (skip=%s, limit=%s)", skip, limit)
            # Convert cached dict back to Item objects
            return [Item(**item) for item in cached_items]
        
        # Cache miss - get from database
        items = db.query(Item).offset(skip).limit(limit).all()
        
        # Cache the result (convert to dicts for JSON serialization)
        items_dict = [item.__dict__.copy() for item in items]
        for item_dict in items_dict:
            item_dict.pop('_sa_instance_state', None)  # Remove SQLAlchemy internal state
        
        await cache_service.set(cache_key, items_dict, expire_seconds=300)
        logger.info("Cached items list (skip=%s, limit=%s)", skip, limit)
        
        return items
    
    @staticmethod
    async def get_item(db: Session, item_id: int) -> Optional[Item]:
        cache_key = f"item:{item_id}"
        
        # Try cache first
        cached_item = await cache_service.get(cache_key)
        if cached_item:
            logger.info("Cache hit for item %s", item_id)
            return Item(**cached_item)
        
        # Cache miss - get from database
        item = db.query(Item).filter(Item.id == item_id).first()
        if item:
            # Cache the result
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            await cache_service.set(cache_key, item_dict, expire_seconds=600)
            logger.info("Cached item %s", item_id)
        
        return item
    
    @staticmethod
    async def update_item(db: Session, item_id: int, item: ItemUpdate) -> Optional[Item]:
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if db_item:
            # Only update fields that are provided (not None)
            update_data = item.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_item, key, value)
            db.commit()
            db.refresh(db_item)
            
            # Invalidate cache for this item and lists
            await cache_service.delete(f"item:{item_id}")
            await cache_service.delete_pattern("items:list:*")
            logger.info("Invalidated cache for item %s after update", item_id)
        
        return db_item
    
    @staticmethod
    async def delete_item(db: Session, item_id: int) -> bool:
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if db_item:
            db.delete(db_item)
            db.commit()
            
            # Invalidate cache for this item and lists
            await cache_service.delete(f"item:{item_id}")
            await cache_service.delete_pattern("items:list:*")
            logger.info("Invalidated cache for item %s after deletion", item_id)
            return True
        return False
