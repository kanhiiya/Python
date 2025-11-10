from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Item(Base):
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
