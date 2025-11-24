import os
import asyncio
from typing import Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from db import SessionLocal, init_db, User, Message, InventoryItem, InventoryTransaction, Supplier
from auth import get_password_hash, verify_password, create_access_token, get_current_user_token
from websocket_manager import ConnectionManager
from llm import chat_completion
from llm_core import llm_router

load_dotenv()

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
# Use PORT environment variable or default to 8000
APP_PORT = int(os.getenv("PORT", os.getenv("APP_PORT", "8000")))

app = FastAPI(title="Group Chat with LLM Bot")

# Allow same-origin and dev origins by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

# --------- Schemas ---------
class AuthPayload(BaseModel):
    username: str
    password: str

class MessagePayload(BaseModel):
    content: str

# --------- Dependencies ---------
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

# --------- Utilities ---------
async def broadcast_message(session: AsyncSession, msg: Message):
    # Load username
    username = None
    if msg.user_id:
        u = await session.get(User, msg.user_id)
        username = u.username if u else "unknown"
    await manager.broadcast({
        "type": "message",
        "message": {
            "id": msg.id,
            "username": username if not msg.is_bot else "LLM Bot",
            "content": msg.content,
            "is_bot": msg.is_bot,
            "created_at": str(msg.created_at)
        }
    })

async def maybe_answer_with_llm(content: str, username: str = "unknown"):
    """
    Route user messages through the LLM router to appropriate agents.
    Always attempt to respond for better user experience.
    Creates its own database session to avoid conflicts.
    """
    # Create a new database session for this background task
    async with SessionLocal() as session:
        try:
            # Build context
            context = {
                "username": username,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Route to appropriate agent
            result = await llm_router.route_message(content, context, session)
            
            reply_text = result["response"]
            
        except Exception as e:
            reply_text = f"Sorry, I encountered an error: {str(e)}"
        
        bot_msg = Message(user_id=None, content=reply_text, is_bot=True)
        session.add(bot_msg)
        await session.commit()
        await session.refresh(bot_msg)
        await broadcast_message(session, bot_msg)

# --------- Routes ---------
@app.on_event("startup")
async def on_startup():
    # Run database initialization in background to avoid blocking server startup
    async def init_db_background():
        try:
            await init_db()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            print("Server will continue, but database operations may fail")
    
    # Start initialization but don't wait for it
    import asyncio
    asyncio.create_task(init_db_background())
    print("Server starting... (database initialization in background)")

@app.post("/api/signup")
async def signup(payload: AuthPayload, session: AsyncSession = Depends(get_db)):
    # Validate username and password
    if not payload.username or len(payload.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
    if not payload.password or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    username = payload.username.strip()
    
    # check unique username
    existing = await session.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    u = User(username=username, password_hash=get_password_hash(payload.password))
    session.add(u)
    await session.commit()
    token = create_access_token({"sub": u.username})
    return {"ok": True, "token": token}

@app.post("/api/login")
async def login(payload: AuthPayload, session: AsyncSession = Depends(get_db)):
    # Validate inputs
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Please enter your username and password as both are compulsory")
    
    username = payload.username.strip()
    
    res = await session.execute(select(User).where(User.username == username))
    u = res.scalar_one_or_none()
    
    # Check if user exists
    if not u:
        raise HTTPException(status_code=401, detail="User does not exist. Please sign up first")
    
    # Check if password is correct
    if not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again")
    
    token = create_access_token({"sub": u.username})
    return {"ok": True, "token": token}

@app.get("/api/messages")
async def get_messages(username: str = Depends(get_current_user_token), limit: int = 50, session: AsyncSession = Depends(get_db)):
    res = await session.execute(select(Message).order_by(desc(Message.created_at)).limit(limit))
    items = list(reversed(res.scalars().all()))
    out = []
    for m in items:
        msg_username = None
        if not m.is_bot and m.user_id:
            u = await session.get(User, m.user_id)
            msg_username = u.username if u else "unknown"
        out.append({
            "id": m.id,
            "username": "LLM Bot" if m.is_bot else (msg_username or "unknown"),
            "content": m.content,
            "is_bot": m.is_bot,
            "created_at": str(m.created_at)
        })
    return {"messages": out}

@app.delete("/api/messages")
async def clear_messages(username: str = Depends(get_current_user_token), session: AsyncSession = Depends(get_db)):
    """Clear all messages from the chat"""
    await session.execute(delete(Message))
    await session.commit()
    return {"ok": True, "message": "All messages cleared"}

@app.post("/api/messages")
async def post_message(payload: MessagePayload, username: str = Depends(get_current_user_token), session: AsyncSession = Depends(get_db)):
    res = await session.execute(select(User).where(User.username == username))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="Invalid user")
    m = Message(user_id=u.id, content=payload.content, is_bot=False)
    session.add(m)
    await session.commit()
    await session.refresh(m)
    await broadcast_message(session, m)
    
    # Only trigger agent if message starts with '#' (like GitHub Copilot)
    if payload.content.strip().startswith('#'):
        # Remove the '#' trigger and process the actual message
        actual_content = payload.content.strip()[1:].strip()
        if actual_content:  # Only process if there's content after '#'
            # fire-and-forget LLM answer with agent routing (uses its own session)
            asyncio.create_task(maybe_answer_with_llm(actual_content, username))
    
    return {"ok": True, "id": m.id}

@app.put("/api/messages/{message_id}")
async def edit_message(message_id: int, payload: MessagePayload, username: str = Depends(get_current_user_token), session: AsyncSession = Depends(get_db)):
    """Edit a message - only the owner can edit their messages"""
    res = await session.execute(select(User).where(User.username == username))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Get the message
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check ownership (only user's own messages, not bot messages)
    if msg.is_bot or msg.user_id != u.id:
        raise HTTPException(status_code=403, detail="You can only edit your own messages")
    
    # Find and delete the bot's response to this message (if any)
    # Bot messages come after user messages, so find the next bot message
    next_bot_result = await session.execute(
        select(Message).where(
            Message.id > message_id,
            Message.is_bot == True
        ).order_by(Message.id).limit(1)
    )
    next_bot_msg = next_bot_result.scalar_one_or_none()
    
    bot_msg_deleted_id = None
    if next_bot_msg:
        # Check if the next message is indeed the bot's response (no user messages in between)
        between_result = await session.execute(
            select(Message).where(
                Message.id > message_id,
                Message.id < next_bot_msg.id,
                Message.is_bot == False
            )
        )
        if not between_result.scalar_one_or_none():
            # This is the bot's response to this message
            bot_msg_deleted_id = next_bot_msg.id
            await session.delete(next_bot_msg)
    
    # Update the message
    msg.content = payload.content
    await session.commit()
    await session.refresh(msg)
    
    # Broadcast the update
    await manager.broadcast({
        "type": "message_edited",
        "message": {
            "id": msg.id,
            "username": username,
            "content": msg.content,
            "is_bot": False,
            "created_at": str(msg.created_at)
        }
    })
    
    # If we deleted a bot message, broadcast that too
    if bot_msg_deleted_id:
        await manager.broadcast({
            "type": "message_deleted",
            "message_id": bot_msg_deleted_id
        })
    
    # Only regenerate LLM answer if edited message starts with '#'
    if payload.content.strip().startswith('#'):
        actual_content = payload.content.strip()[1:].strip()
        if actual_content:
            asyncio.create_task(maybe_answer_with_llm(actual_content, username))
    
    return {"ok": True, "id": msg.id}

@app.delete("/api/messages/{message_id}")
async def delete_single_message(message_id: int, username: str = Depends(get_current_user_token), session: AsyncSession = Depends(get_db)):
    """Delete a single message and its bot response - only the owner can delete their messages"""
    res = await session.execute(select(User).where(User.username == username))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    # Get the message
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check ownership (only user's own messages, not bot messages)
    if msg.is_bot or msg.user_id != u.id:
        raise HTTPException(status_code=403, detail="You can only delete your own messages")
    
    # Find and delete the bot's response to this message (if any)
    next_bot_result = await session.execute(
        select(Message).where(
            Message.id > message_id,
            Message.is_bot == True
        ).order_by(Message.id).limit(1)
    )
    next_bot_msg = next_bot_result.scalar_one_or_none()
    
    bot_msg_deleted_id = None
    if next_bot_msg:
        # Check if the next message is indeed the bot's response (no user messages in between)
        between_result = await session.execute(
            select(Message).where(
                Message.id > message_id,
                Message.id < next_bot_msg.id,
                Message.is_bot == False
            )
        )
        if not between_result.scalar_one_or_none():
            # This is the bot's response to this message
            bot_msg_deleted_id = next_bot_msg.id
            await session.delete(next_bot_msg)
    
    # Delete the user message
    await session.delete(msg)
    await session.commit()
    
    # Broadcast the deletion of the user message
    await manager.broadcast({
        "type": "message_deleted",
        "message_id": message_id
    })
    
    # If we also deleted a bot message, broadcast that too
    if bot_msg_deleted_id:
        await manager.broadcast({
            "type": "message_deleted",
            "message_id": bot_msg_deleted_id
        })
    
    return {"ok": True, "message": "Message deleted"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Optional auth via query param token
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client over WS; ignore/echo if any
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ack", "echo": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ========== Inventory Management API Endpoints ==========

class InventoryItemPayload(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    quantity: float
    unit: str = "units"
    min_quantity: float = 10.0
    location: Optional[str] = None

class SupplierPayload(BaseModel):
    name: str
    item_name: str
    contact_info: Optional[str] = None
    order_url: Optional[str] = None
    price_per_unit: Optional[float] = None
    lead_time_days: Optional[int] = None
    notes: Optional[str] = None

@app.get("/api/inventory")
async def get_inventory(session: AsyncSession = Depends(get_db)):
    """Get all inventory items."""
    result = await session.execute(select(InventoryItem))
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "quantity": i.quantity,
                "unit": i.unit,
                "min_quantity": i.min_quantity,
                "location": i.location,
                "is_low_stock": i.quantity <= i.min_quantity
            }
            for i in items
        ]
    }

@app.get("/api/inventory/low-stock")
async def get_low_stock(session: AsyncSession = Depends(get_db)):
    """Get items below minimum threshold."""
    result = await session.execute(
        select(InventoryItem).where(InventoryItem.quantity <= InventoryItem.min_quantity)
    )
    items = result.scalars().all()
    return {
        "low_stock_items": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "quantity": i.quantity,
                "unit": i.unit,
                "min_quantity": i.min_quantity
            }
            for i in items
        ]
    }

@app.post("/api/inventory")
async def add_inventory_item(
    payload: InventoryItemPayload,
    username: str = Depends(get_current_user_token),
    session: AsyncSession = Depends(get_db)
):
    """Add a new inventory item."""
    item = InventoryItem(
        name=payload.name,
        category=payload.category,
        description=payload.description,
        quantity=payload.quantity,
        unit=payload.unit,
        min_quantity=payload.min_quantity,
        location=payload.location
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    
    # Log transaction
    trans = InventoryTransaction(
        item_id=item.id,
        transaction_type="add",
        quantity_change=payload.quantity,
        quantity_after=payload.quantity,
        reason="Initial stock"
    )
    session.add(trans)
    await session.commit()
    
    return {"ok": True, "item_id": item.id}

@app.put("/api/inventory/{item_id}")
async def update_inventory(
    item_id: int,
    quantity_change: float,
    reason: Optional[str] = None,
    username: str = Depends(get_current_user_token),
    session: AsyncSession = Depends(get_db)
):
    """Update inventory quantity."""
    item = await session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    old_qty = item.quantity
    item.quantity += quantity_change
    
    # Log transaction
    trans_type = "add" if quantity_change > 0 else "remove"
    trans = InventoryTransaction(
        item_id=item_id,
        transaction_type=trans_type,
        quantity_change=quantity_change,
        quantity_after=item.quantity,
        reason=reason
    )
    session.add(trans)
    await session.commit()
    
    return {"ok": True, "new_quantity": item.quantity}

@app.get("/api/suppliers")
async def get_suppliers(item_name: Optional[str] = None, session: AsyncSession = Depends(get_db)):
    """Get suppliers, optionally filtered by item name."""
    if item_name:
        result = await session.execute(
            select(Supplier).where(Supplier.item_name.ilike(f"%{item_name}%"))
        )
    else:
        result = await session.execute(select(Supplier))
    
    suppliers = result.scalars().all()
    return {
        "suppliers": [
            {
                "id": s.id,
                "name": s.name,
                "item_name": s.item_name,
                "contact_info": s.contact_info,
                "order_url": s.order_url,
                "price_per_unit": s.price_per_unit,
                "lead_time_days": s.lead_time_days
            }
            for s in suppliers
        ]
    }

@app.post("/api/suppliers")
async def add_supplier(
    payload: SupplierPayload,
    username: str = Depends(get_current_user_token),
    session: AsyncSession = Depends(get_db)
):
    """Add a new supplier."""
    supplier = Supplier(
        name=payload.name,
        item_name=payload.item_name,
        contact_info=payload.contact_info,
        order_url=payload.order_url,
        price_per_unit=payload.price_per_unit,
        lead_time_days=payload.lead_time_days,
        notes=payload.notes
    )
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return {"ok": True, "supplier_id": supplier.id}

@app.get("/api/agents")
async def get_available_agents():
    """Get information about available AI agents."""
    return {"agents": llm_router.get_available_agents()}

# Serve frontend static files - MUST BE LAST so API routes take precedence
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
