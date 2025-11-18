import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, Integer, Float, func
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+asyncmy://chatuser:chatpass@localhost:3306/groupchat")

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    content: Mapped[str] = mapped_column(Text())
    is_bot: Mapped[bool] = mapped_column(Boolean(), default=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="messages")

# ========== Inventory Management Models ==========

class InventoryItem(Base):
    """
    Represents items/materials in the STEM center inventory.
    """
    __tablename__ = "inventory_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., "Stationery", "Lab Equipment", "Electronics"
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    quantity: Mapped[float] = mapped_column(Float(), default=0.0)
    unit: Mapped[str] = mapped_column(String(20), default="units")  # e.g., "pieces", "boxes", "kg", "liters"
    min_quantity: Mapped[float] = mapped_column(Float(), default=10.0)  # Minimum threshold for alerts
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Storage location
    last_restocked: Mapped[Optional["DateTime"]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    transactions = relationship("InventoryTransaction", back_populates="item")

class InventoryTransaction(Base):
    """
    Tracks all inventory movements (additions, removals, adjustments).
    """
    __tablename__ = "inventory_transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id", ondelete="CASCADE"))
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "add", "remove", "adjustment", "order"
    quantity_change: Mapped[float] = mapped_column(Float(), nullable=False)  # Positive for additions, negative for removals
    quantity_after: Mapped[float] = mapped_column(Float(), nullable=False)  # Stock level after transaction
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)  # Why the transaction occurred
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    item = relationship("InventoryItem", back_populates="transactions")
    user = relationship("User")

class Supplier(Base):
    """
    Stores supplier/vendor information for procurement.
    """
    __tablename__ = "suppliers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # What item they supply
    contact_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email or phone
    order_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Direct link to order
    price_per_unit: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)  # Delivery time
    notes: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
