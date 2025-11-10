from sqlalchemy.orm import Session
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate
from typing import List, Optional

class ItemService:
    @staticmethod
    def create_item(db: Session, item: ItemCreate) -> Item:
        db_item = Item(**item.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    @staticmethod
    def get_items(db: Session, skip: int = 0, limit: int = 10) -> List[Item]:
        return db.query(Item).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_item(db: Session, item_id: int) -> Optional[Item]:
        return db.query(Item).filter(Item.id == item_id).first()
    
    @staticmethod
    def update_item(db: Session, item_id: int, item: ItemUpdate) -> Optional[Item]:
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if db_item:
            for key, value in item.model_dump().items():
                setattr(db_item, key, value)
            db.commit()
            db.refresh(db_item)
        return db_item
    
    @staticmethod
    def delete_item(db: Session, item_id: int) -> bool:
        db_item = db.query(Item).filter(Item.id == item_id).first()
        if db_item:
            db.delete(db_item)
            db.commit()
            return True
        return False
