"""
Inventory Management Agent
Handles all inventory-related queries and actions:
- Check stock levels
- Add/remove items
- Get low stock alerts
- Search for items
- Generate inventory reports
"""

import re
from typing import Dict, List, Any, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from agents.base_agent import BaseAgent
from db import InventoryItem, InventoryTransaction, Supplier
from llm import chat_completion


class InventoryAgent(BaseAgent):
    """
    Specialized agent for inventory management in STEM centers.
    """
    
    def __init__(self):
        super().__init__(
            name="InventoryAgent",
            description="Manages inventory tracking, stock levels, and supply chain for STEM center materials"
        )
        self.keywords = [
            "inventory", "stock", "supplies", "materials", "items",
            "pencils", "chemistry set", "equipment", "tools",
            "low on", "need", "order", "shortage", "available",
            "check stock", "how many", "count", "quantity"
        ]
    
    async def can_handle(self, user_message: str, context: Dict[str, Any]) -> tuple[bool, float]:
        """
        Determine if this message is about inventory management.
        """
        # Strip any command prefixes like "#"
        message_lower = user_message.lower().strip().lstrip('#').strip()
        
        # Quickly filter out education/lesson requests so we don't hijack them
        lesson_terms = ["lesson", "curriculum", "plan", "worksheet", "activity", "grade"]
        if any(term in message_lower for term in lesson_terms):
            # Only continue if the message also contains strong inventory cues
            strong_inventory_terms = ["inventory", "stock", "supplies", "materials", "order", "restock"]
            if not any(term in message_lower for term in strong_inventory_terms):
                return False, 0.0
        
        # High confidence patterns - expanded to catch more variations
        high_confidence_patterns = [
            r"(check|what's|show|get|tell|display|list).*(stock|inventory|supplies|available|items)",
            r"(low on|short on|running low|out of).*(stock|inventory|supplies|materials|items)",
            r"need (more|to restock|to reorder|to order)",
            r"how many .* (do we have|available|in stock)",
            r"(order|purchase|buy|get more|add|new).*(to|in).*(inventory|stock)",
            r"inventory (check|status|report|list)",
            r"(add|new|register).*\d+.*(to|in).*(inventory|stock)",
            r"#.*(stock|inventory|add|check|available)",
            r"(pencils|microscopes|kits|equipment|materials|supplies).*(available|stock|inventory)",
        ]
        
        for pattern in high_confidence_patterns:
            if re.search(pattern, message_lower):
                return True, 0.9
        
        # Medium confidence - keyword matching
        keyword_matches = sum(1 for kw in self.keywords if kw in message_lower)
        if keyword_matches >= 2:
            return True, 0.7
        elif keyword_matches == 1:
            return True, 0.5
        
        # Check for common inventory-related words even without patterns
        inventory_words = ["stock", "inventory", "supplies", "materials", "items", "available", "add", "check"]
        if any(word in message_lower for word in inventory_words):
            return True, 0.4
        
        return False, 0.0
    
    async def execute(self, user_message: str, context: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
        """
        Execute inventory-related actions based on user intent.
        """
        # Strip command prefix if present
        message_lower = user_message.lower().strip().lstrip('#').strip()
        
        # Classify the specific intent
        # Check for add/new item commands first (most specific)
        if re.search(r"(add|new).*\d+.*(to|in).*(inventory|stock)", message_lower) or \
           re.search(r"add.*\d+.*new", message_lower):
            return await self._handle_add_item(user_message, session)
        
        # Check for low stock / restocking queries
        elif re.search(r"(low on|short on|need|out of|running low|restock|restocking|need to (order|reorder)|what.*need)", message_lower):
            return await self._handle_low_stock_alert(user_message, session)
        
        # Check for stock check queries (including "available")
        elif re.search(r"(check|what's|show|get|tell|display).*(stock|inventory|available)", message_lower) or \
             re.search(r".*(available|stock|inventory)", message_lower):
            return await self._handle_stock_check(user_message, session)
        
        elif re.search(r"how many .* (do we have|available|in stock)", message_lower):
            return await self._handle_quantity_query(user_message, session)
        
        elif re.search(r"(order|purchase|buy|get more)", message_lower):
            return await self._handle_order_request(user_message, session)
        
        else:
            # General inventory query - try stock check as fallback
            return await self._handle_stock_check(user_message, session)
    
    async def _handle_low_stock_alert(self, message: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Handle alerts about low stock items.
        """
        # Extract item name from message
        item_name = self._extract_item_name(message)
        
        if item_name:
            # Check if item exists
            result = await session.execute(
                select(InventoryItem).where(
                    or_(
                        InventoryItem.name.ilike(f"%{item_name}%"),
                        InventoryItem.category.ilike(f"%{item_name}%")
                    )
                )
            )
            items = result.scalars().all()
            
            if items:
                item = items[0]
                
                # Check suppliers
                suppliers_result = await session.execute(
                    select(Supplier).where(Supplier.item_name.ilike(f"%{item_name}%"))
                )
                suppliers = suppliers_result.scalars().all()
                
                # Prepare facts for LLM
                item_facts = {
                    "name": item.name,
                    "current_stock": item.quantity,
                    "unit": item.unit,
                    "min_threshold": item.min_quantity,
                    "is_critical": item.quantity < item.min_quantity * 0.5,
                    "is_low": item.quantity <= item.min_quantity,
                    "category": item.category,
                    "location": item.location,
                    "suppliers": [
                        {
                            "name": s.name,
                            "price": s.price_per_unit,
                            "order_url": s.order_url,
                            "lead_time": s.lead_time_days
                        } for s in suppliers
                    ]
                }
                
                # Generate natural language response with LLM
                response = await self._generate_low_stock_response(message, item_facts)
                
                return {
                    "success": True,
                    "message": response,
                    "data": {
                        "item": {
                            "id": item.id,
                            "name": item.name,
                            "quantity": item.quantity,
                            "unit": item.unit
                        },
                        "suppliers": [{"name": s.name, "url": s.order_url, "price": s.price_per_unit} for s in suppliers]
                    },
                    "actions": ["stock_check", "supplier_lookup"]
                }
            else:
                return {
                    "success": False,
                    "message": f"Item '{item_name}' not found in inventory. Would you like to add it?",
                    "data": None,
                    "actions": ["item_not_found"]
                }
        else:
            # No specific item mentioned - show all low stock items
            result = await session.execute(
                select(InventoryItem).where(
                    InventoryItem.quantity <= InventoryItem.min_quantity
                )
            )
            low_stock_items = result.scalars().all()
            
            if low_stock_items:
                # Prepare facts for LLM about all low stock items
                low_stock_facts = []
                for item in low_stock_items:
                    # Get suppliers for this item
                    suppliers_result = await session.execute(
                        select(Supplier).where(Supplier.item_name.ilike(f"%{item.name}%"))
                    )
                    suppliers = suppliers_result.scalars().all()
                    
                    low_stock_facts.append({
                        "name": item.name,
                        "current_stock": item.quantity,
                        "unit": item.unit,
                        "min_threshold": item.min_quantity,
                        "category": item.category,
                        "location": item.location or "Not specified",
                        "is_critical": item.quantity < item.min_quantity * 0.5,
                        "suppliers_available": len(suppliers) > 0,
                        "supplier_names": [s.name for s in suppliers]
                    })
                
                # Generate natural language response with LLM
                response = await self._generate_all_low_stock_response(message, low_stock_facts)
                
                return {
                    "success": True,
                    "message": response,
                    "data": {"low_stock_items": [{"name": i.name, "quantity": i.quantity} for i in low_stock_items]},
                    "actions": ["low_stock_check"]
                }
            else:
                return {
                    "success": True,
                    "message": "All inventory items are adequately stocked.",
                    "data": None,
                    "actions": ["low_stock_check"]
                }
    
    async def _handle_stock_check(self, message: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Handle general stock checking queries.
        """
        item_name = self._extract_item_name(message)
        
        if item_name:
            result = await session.execute(
                select(InventoryItem).where(
                    or_(
                        InventoryItem.name.ilike(f"%{item_name}%"),
                        InventoryItem.category.ilike(f"%{item_name}%")
                    )
                )
            )
            items = result.scalars().all()
            
            if items:
                # Prepare facts for LLM
                facts = []
                for item in items:
                    status = "adequate" if item.quantity > item.min_quantity else "low"
                    facts.append({
                        "name": item.name,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "category": item.category,
                        "location": item.location or "Not specified",
                        "min_threshold": item.min_quantity,
                        "status": status
                    })
                
                # Generate natural language response with LLM
                response = await self._generate_stock_response(message, facts)
                
                return {
                    "success": True,
                    "message": response,
                    "data": {"items": [{"name": i.name, "quantity": i.quantity, "unit": i.unit} for i in items]},
                    "actions": ["stock_check"]
                }
            else:
                # Check if similar items exist (fuzzy search)
                all_items_result = await session.execute(select(InventoryItem))
                all_items = all_items_result.scalars().all()
                
                # Find similar item names
                similar_items = []
                item_words = set(item_name.lower().split())
                for item in all_items:
                    item_words_set = set(item.name.lower().split())
                    if item_words & item_words_set:  # If there's any word overlap
                        similar_items.append(item.name)
                
                if similar_items:
                    similar_list = ", ".join(similar_items[:5])
                    return {
                        "success": False,
                        "message": f"No items found matching '{item_name}'. Did you mean: {similar_list}?",
                        "data": {"similar_items": similar_items[:5]},
                        "actions": ["stock_check", "suggestion"]
                    }
                else:
                    return {
                        "success": False,
                        "message": f"No items found matching '{item_name}'. The inventory might be empty or this item hasn't been added yet. You can add it by saying 'Add [quantity] [item name] to inventory'.",
                        "data": None,
                        "actions": ["stock_check", "item_not_found"]
                    }
        else:
            # Show all inventory
            result = await session.execute(select(InventoryItem))
            all_items = result.scalars().all()
            
            if all_items:
                # Prepare facts for LLM
                facts = []
                for item in all_items:
                    status = "adequate" if item.quantity > item.min_quantity else "low"
                    facts.append({
                        "name": item.name,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "category": item.category,
                        "location": item.location or "Not specified",
                        "min_threshold": item.min_quantity,
                        "status": status
                    })
                
                # Generate natural language response with LLM
                response = await self._generate_full_inventory_response(message, facts)
                
                return {
                    "success": True,
                    "message": response,
                    "data": {"total_items": len(all_items)},
                    "actions": ["full_inventory_check"]
                }
            else:
                return {
                    "success": True,
                    "message": "Inventory is empty. Start by adding items!",
                    "data": None,
                    "actions": ["empty_inventory"]
                }
    
    async def _handle_quantity_query(self, message: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Handle specific quantity queries like "How many pencils do we have?"
        """
        return await self._handle_stock_check(message, session)
    
    async def _handle_order_request(self, message: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Handle requests to order items.
        """
        item_name = self._extract_item_name(message)
        
        if item_name:
            # Look up suppliers
            result = await session.execute(
                select(Supplier).where(Supplier.item_name.ilike(f"%{item_name}%"))
            )
            suppliers = result.scalars().all()
            
            if suppliers:
                response = f"**Order Options for '{item_name}':**\n\n"
                for s in suppliers:
                    response += f"**{s.name}**\n"
                    response += f"  • Price: ${s.price_per_unit} per unit\n"
                    response += f"  • Contact: {s.contact_info}\n"
                    response += f"  • Order: {s.order_url}\n\n"
                
                return {
                    "success": True,
                    "message": response + "Click on a link to proceed with ordering.",
                    "data": {"suppliers": [{"name": s.name, "url": s.order_url} for s in suppliers]},
                    "actions": ["supplier_lookup", "order_request"]
                }
            else:
                return {
                    "success": False,
                    "message": f"No suppliers found for '{item_name}'. Please add supplier information first.",
                    "data": None,
                    "actions": ["supplier_not_found"]
                }
        else:
            return {
                "success": False,
                "message": "Please specify which item you'd like to order.",
                "data": None,
                "actions": ["order_request"]
            }
    
    async def _handle_add_item(self, message: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Handle adding new items to inventory.
        Parses messages like "Add 10 new microscopes to inventory" or "Add 5 pencils"
        """
        message_lower = message.lower().strip().lstrip('#').strip()
        
        # Extract quantity - look for numbers
        quantity_match = re.search(r'(\d+(?:\.\d+)?)', message)
        if not quantity_match:
            return {
                "success": False,
                "message": "I couldn't find a quantity in your message. Please specify a number, e.g., 'Add 10 microscopes'",
                "data": None,
                "actions": ["add_item_help"]
            }
        
        quantity = float(quantity_match.group(1))
        
        # Extract item name - prioritize add-specific patterns first
        item_name = None
        
        # Try add-specific patterns first (more accurate for add commands)
        add_patterns = [
            # "Add 25 new beakers to the inventory" -> "beakers"
            r"add\s+\d+\s+(?:new\s+)?([a-z\s]+?)(?:\s+to\s+(?:the\s+)?(?:inventory|stock)|\s+in\s+(?:the\s+)?(?:inventory|stock)|\?|$)",
            # "Add 10 microscopes" -> "microscopes"
            r"add\s+\d+\s+([a-z\s]+?)(?:\s+to|\s+in|\?|$)",
            # "Add 5 of pencils" -> "pencils"
            r"add\s+\d+\s+of\s+([a-z\s]+?)(?:\s+to|\s+in|\?|$)",
        ]
        
        for pattern in add_patterns:
            match = re.search(pattern, message_lower)
            if match:
                item_name = match.group(1).strip()
                # Filter out stop words
                stop_words = {"the", "a", "an", "new", "to", "in", "inventory", "stock", "of"}
                words = [w for w in item_name.split() if w not in stop_words and len(w) > 1]
                if words:
                    item_name = " ".join(words)
                    break
        
        # Fallback to general extraction if add patterns didn't work
        if not item_name:
            item_name = self._extract_item_name(message)
        
        if not item_name:
            return {
                "success": False,
                "message": "I couldn't identify the item name. Please specify what you want to add, e.g., 'Add 10 microscopes'",
                "data": None,
                "actions": ["add_item_help"]
            }
        
        # Determine category based on item name (simple heuristic)
        category = self._infer_category(item_name)
        
        # Check if item already exists
        result = await session.execute(
            select(InventoryItem).where(
                or_(
                    InventoryItem.name.ilike(f"%{item_name}%"),
                    InventoryItem.name.ilike(f"%{item_name.replace(' ', '%')}%")
                )
            )
        )
        existing_items = result.scalars().all()
        
        if existing_items:
            # Update existing item
            item = existing_items[0]
            old_quantity = item.quantity
            item.quantity += quantity
            item.updated_at = datetime.now()
            
            # Create transaction record
            transaction = InventoryTransaction(
                item_id=item.id,
                transaction_type="add",
                quantity_change=quantity,
                quantity_after=item.quantity,
                reason=f"Added via chat: {message}"
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(item)
            
            return {
                "success": True,
                "message": f"Added {quantity} {item.unit} of '{item.name}'. New total: {item.quantity} {item.unit} (was {old_quantity})",
                "data": {
                    "item": {
                        "id": item.id,
                        "name": item.name,
                        "quantity": item.quantity,
                        "unit": item.unit
                    }
                },
                "actions": ["add_item", "update_quantity"]
            }
        else:
            # Create new item
            new_item = InventoryItem(
                name=item_name,
                category=category,
                quantity=quantity,
                unit="units",
                min_quantity=10.0,  # Default minimum
                description=f"Added via chat"
            )
            session.add(new_item)
            await session.flush()  # Get the ID
            
            # Create transaction record
            transaction = InventoryTransaction(
                item_id=new_item.id,
                transaction_type="add",
                quantity_change=quantity,
                quantity_after=quantity,
                reason=f"Initial addition via chat: {message}"
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(new_item)
            
            return {
                "success": True,
                "message": f"Added new item '{new_item.name}' to inventory with quantity {quantity} {new_item.unit} (category: {category})",
                "data": {
                    "item": {
                        "id": new_item.id,
                        "name": new_item.name,
                        "quantity": new_item.quantity,
                        "unit": new_item.unit,
                        "category": new_item.category
                    }
                },
                "actions": ["add_item", "create_item"]
            }
    
    def _infer_category(self, item_name: str) -> str:
        """
        Infer category from item name using simple heuristics.
        """
        name_lower = item_name.lower()
        
        if any(word in name_lower for word in ["microscope", "beaker", "flask", "test tube", "bunsen", "lab", "equipment"]):
            return "Lab Equipment"
        elif any(word in name_lower for word in ["pencil", "pen", "marker", "paper", "notebook", "eraser"]):
            return "Stationery"
        elif any(word in name_lower for word in ["arduino", "sensor", "circuit", "battery", "wire", "led", "resistor"]):
            return "Electronics"
        elif any(word in name_lower for word in ["kit", "set", "box", "pack"]):
            return "Kits & Sets"
        else:
            return "General Supplies"
    
    async def _handle_general_query(self, message: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Handle general inventory-related queries.
        """
        return {
            "success": True,
            "message": "I can help you with:\n• Checking stock levels\n• Finding low stock items\n• Looking up suppliers\n• Ordering materials\n\nWhat would you like to know?",
            "data": None,
            "actions": ["help"]
        }
    
    def _extract_item_name(self, message: str) -> Optional[str]:
        """
        Extract item name from user message using pattern matching.
        Returns None if the message is asking for all/complete inventory or low stock list.
        """
        # Strip command prefix
        message_lower = message.lower().strip().lstrip('#').strip()
        
        # Check if user wants to see ALL inventory (should return None)
        if re.search(r"\b(all|everything|complete|entire|full|whole)\b.*(inventory|stock|items|supplies)", message_lower):
            return None
        if re.search(r"(show|list|display|get).*(all|everything|complete)", message_lower):
            return None
        
        # Check if asking for generic low stock / restocking without specific item
        if re.search(r"(what|which).*(need|low|restock)", message_lower) and not re.search(r"\b(pencil|marker|beaker|arduino|kit|box|pack|microscope|lab)\b", message_lower):
            return None
        
        # Patterns for extracting item names - improved to catch more variations
        patterns = [
            # "Add 10 new microscopes to inventory" -> "microscopes"
            r"(?:add|new).*\d+.*(?:new|of)?\s+([a-z\s]+?)(?:\s+to|\s+in|\?|$)",
            # "show me the current stock of science lab kits" -> "science lab kits"
            r"(?:stock|inventory|available).*of\s+([a-z\s]+?)(?:\?|$)",
            # "check pencils available" -> "pencils"
            r"(?:check|show|get|tell|what's).*?([a-z\s]+?)(?:\s+available|\s+stock|\s+inventory|\?|$)",
            # "low on X" or "need X"
            r"(?:low on|short on|need|out of)\s+([a-z\s]+?)(?:\s+for|\?|$)",
            # "how many X do we have"
            r"(?:how many|check|stock of)\s+([a-z\s]+?)(?:\s+do|\?|$)",
            # "order X" or "buy X"
            r"(?:order|buy|purchase)\s+([a-z\s]+?)(?:\s+from|\?|$)",
            # "X stock" or "X inventory"
            r"([a-z\s]+?)\s+(?:stock|inventory|supplies)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                item = match.group(1).strip()
                # Filter out common words, action words, and query words
                stop_words = {"the", "a", "an", "some", "more", "any", "all", "everything", "complete", "entire", "full", "me", "restocking", "restock", "need", "items", "things", "stuff", "current", "show", "check", "get", "tell", "what's", "display", "list"}
                words = [w for w in item.split() if w not in stop_words and len(w) > 1]
                if words:
                    return " ".join(words)
        
        return None
    
    async def _generate_stock_response(self, user_message: str, facts: List[Dict]) -> str:
        """
        Use LLM to generate natural language response for stock checks.
        """
        # Format facts for LLM
        facts_str = "\n".join([
            f"- {f['name']}: {f['quantity']} {f['unit']} (min: {f['min_threshold']}, status: {f['status']}, location: {f['location']})"
            for f in facts
        ])
        
        system_prompt = """You are a helpful inventory management assistant for a STEM center. 
Respond naturally and conversationally to inventory queries. Be concise and professional.
Do not use emojis. If stock is low, be helpful about what to do next."""
        
        user_prompt = f"""User asked: "{user_message}"

Current inventory data:
{facts_str}

Provide a helpful, natural response about the inventory status."""
        
        try:
            response = await chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=256
            )
            return response
        except Exception as e:
            # Fallback to simple response if LLM fails
            return f"Found {len(facts)} item(s): " + ", ".join([f"{f['name']} ({f['quantity']} {f['unit']})" for f in facts])
    
    async def _generate_full_inventory_response(self, user_message: str, facts: List[Dict]) -> str:
        """
        Use LLM to generate natural language response for full inventory listing.
        """
        # Group by category
        by_category = {}
        for f in facts:
            cat = f['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)
        
        # Format for LLM
        inventory_str = ""
        for category, items in by_category.items():
            inventory_str += f"\n{category}:\n"
            for item in items:
                status = "adequate" if item['status'] == "adequate" else "low"
                inventory_str += f"  - {item['name']}: {item['quantity']} {item['unit']} (status: {status})\n"
        
        system_prompt = """You are a helpful inventory management assistant for a STEM center.
When showing complete inventory, organize it clearly by category and highlight any low-stock items.
Be professional and concise. Do not use emojis. Use clear text-based formatting."""
        
        user_prompt = f"""User asked: "{user_message}"

Complete inventory organized by category:
{inventory_str}

Provide a helpful summary of the inventory, organized by category. Mention if there are any items that need attention."""
        
        try:
            response = await chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            return response
        except Exception as e:
            # Fallback to structured response
            response = "**Complete Inventory:**\n\n"
            for category, items in by_category.items():
                response += f"**{category}**\n"
                for item in items:
                    status = "OK" if item['status'] == "adequate" else "LOW"
                    response += f"  [{status}] {item['name']}: {item['quantity']} {item['unit']}\n"
                response += "\n"
            return response
    
    async def _generate_low_stock_response(self, user_message: str, item_facts: Dict) -> str:
        """
        Use LLM to generate natural language response for low stock alerts.
        """
        suppliers_str = ""
        if item_facts['suppliers']:
            suppliers_str = "\n".join([
                f"- {s['name']}: ${s['price']}/{item_facts['unit']}, lead time: {s['lead_time']} days, order: {s['order_url']}"
                for s in item_facts['suppliers']
            ])
        else:
            suppliers_str = "No suppliers configured"
        
        system_prompt = """You are a helpful inventory management assistant for a STEM center.
When items are low or out of stock, provide clear, actionable advice.
Be professional and concise. Include supplier information when available.
Do not use emojis. Use clear text-based formatting."""
        
        user_prompt = f"""User said: "{user_message}"

Item: {item_facts['name']}
Current stock: {item_facts['current_stock']} {item_facts['unit']}
Minimum threshold: {item_facts['min_threshold']} {item_facts['unit']}
Status: {"CRITICAL - below 50% of minimum" if item_facts['is_critical'] else "LOW - at or below minimum" if item_facts['is_low'] else "Adequate"}
Location: {item_facts.get('location', 'Not specified')}

Available suppliers:
{suppliers_str}

Provide a natural, helpful response about this inventory situation. If suppliers are available, mention them with ordering links."""
        
        try:
            response = await chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response
        except Exception as e:
            # Fallback response
            status = "LOW" if item_facts['is_low'] else "OK"
            msg = f"Status: {status} - {item_facts['name']}: {item_facts['current_stock']} {item_facts['unit']}"
            if item_facts['suppliers']:
                msg += f"\n\nSuppliers: " + ", ".join([s['name'] for s in item_facts['suppliers']])
            return msg
    
    async def _generate_all_low_stock_response(self, user_message: str, low_stock_items: List[Dict]) -> str:
        """
        Use LLM to generate natural language response for multiple low stock items.
        """
        # Format all low stock items for LLM
        items_summary = []
        critical_count = 0
        for item in low_stock_items:
            status = "CRITICAL" if item['is_critical'] else "LOW"
            if item['is_critical']:
                critical_count += 1
            
            supplier_info = ""
            if item['suppliers_available']:
                supplier_info = f" (suppliers: {', '.join(item['supplier_names'][:2])})"
            
            items_summary.append(
                f"- {item['name']}: {item['current_stock']} {item['unit']} (minimum: {item['min_threshold']}) - {status}{supplier_info}"
            )
        
        items_str = "\n".join(items_summary)
        
        system_prompt = """You are a helpful inventory management assistant for a STEM center.
When reporting on multiple low stock items, provide a clear summary with:
1. Total count and urgency level
2. Most critical items highlighted
3. Practical recommendations for restocking
Be professional and concise. Do not use emojis. Organize by urgency if needed."""
        
        user_prompt = f"""User asked: "{user_message}"

Low stock items summary:
Total items needing attention: {len(low_stock_items)}
Critical items (below 50% of minimum): {critical_count}

Details:
{items_str}

Provide a helpful, organized response about these inventory items that need restocking. Highlight the most critical ones and provide actionable recommendations."""
        
        try:
            response = await chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            return response
        except Exception as e:
            # Fallback to simple list
            fallback = f"**Low Stock Alert** - {len(low_stock_items)} items need restocking:\n\n"
            for item in low_stock_items:
                status = "[CRITICAL]" if item['is_critical'] else "[LOW]"
                fallback += f"{status} {item['name']}: {item['current_stock']} {item['unit']} (min: {item['min_threshold']})\n"
            return fallback
    
    async def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides.
        """
        return [
            "Check current stock levels",
            "Alert on low inventory items",
            "Search for specific materials",
            "Look up supplier information",
            "Generate ordering links",
            "Track inventory history",
            "Categorize supplies",
            "Set minimum stock thresholds"
        ]
