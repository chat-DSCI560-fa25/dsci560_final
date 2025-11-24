"""
Training data generator for STEM center inventory management.
Generates synthetic training examples for fine-tuning the LLM.
"""

import json
import random
from typing import List, Dict

# Common STEM center inventory items
INVENTORY_ITEMS = [
    # Stationery
    "pencils", "pens", "markers", "erasers", "rulers", "notebooks", "paper",
    "staplers", "paper clips", "folders", "binders",
    
    # Lab Equipment
    "beakers", "test tubes", "microscopes", "petri dishes", "pipettes",
    "bunsen burners", "safety goggles", "lab coats", "graduated cylinders",
    "thermometers", "scales", "chemistry sets",
    
    # Electronics & Technology
    "resistors", "capacitors", "LEDs", "breadboards", "Arduino kits",
    "Raspberry Pi", "sensors", "wires", "batteries", "multimeters",
    
    # Tools
    "screwdrivers", "pliers", "wire cutters", "soldering irons",
    "hot glue guns", "measuring tapes", "scissors",
    
    # Art & Craft
    "glue sticks", "construction paper", "paint", "brushes", "clay",
    
    # Teaching Materials
    "models", "charts", "calculators", "graph paper"
]

CATEGORIES = {
    "Stationery": ["pencils", "pens", "markers", "erasers", "rulers", "notebooks", "paper"],
    "Lab Equipment": ["beakers", "test tubes", "microscopes", "petri dishes", "chemistry sets"],
    "Electronics": ["Arduino kits", "Raspberry Pi", "sensors", "LEDs", "resistors"],
    "Tools": ["screwdrivers", "pliers", "wire cutters", "soldering irons"],
    "Art Supplies": ["glue sticks", "paint", "brushes", "clay"]
}

SUPPLIERS = [
    "School Supply Co", "STEM Warehouse", "EduMart", "Science Direct",
    "Tech Education Supplies", "Lab Pro", "Amazon Business"
]


def generate_inventory_check_examples() -> List[Dict[str, str]]:
    """Generate examples for inventory checking queries."""
    examples = []
    templates = [
        ("How many {item} do we have?", "check_quantity"),
        ("What's the stock level for {item}?", "check_quantity"),
        ("Check inventory for {item}", "check_quantity"),
        ("Do we have enough {item}?", "check_adequacy"),
        ("Show me the {item} inventory", "view_inventory"),
        ("What {item} are available?", "view_inventory"),
        ("Can you check if we have {item} in stock?", "check_availability"),
    ]
    
    for item in INVENTORY_ITEMS[:20]:
        for template, intent in templates:
            query = template.format(item=item)
            response = _generate_check_response(item, intent)
            examples.append({
                "query": query,
                "intent": "inventory_check",
                "sub_intent": intent,
                "response": response,
                "agent": "InventoryAgent"
            })
    
    return examples


def generate_low_stock_examples() -> List[Dict[str, str]]:
    """Generate examples for low stock alerts."""
    examples = []
    templates = [
        ("We're running low on {item}", "alert_low_stock"),
        ("We're short on {item} for tomorrow", "urgent_low_stock"),
        ("Almost out of {item}", "alert_low_stock"),
        ("Need more {item} urgently", "urgent_reorder"),
        ("{item} stock is getting low", "alert_low_stock"),
        ("Running short on {item}", "alert_low_stock"),
        ("We need {item} restocked", "restock_request"),
    ]
    
    for item in INVENTORY_ITEMS[:15]:
        for template, intent in templates:
            query = template.format(item=item)
            response = _generate_low_stock_response(item, intent)
            examples.append({
                "query": query,
                "intent": "low_stock_alert",
                "sub_intent": intent,
                "response": response,
                "agent": "InventoryAgent"
            })
    
    return examples


def generate_order_request_examples() -> List[Dict[str, str]]:
    """Generate examples for ordering supplies."""
    examples = []
    templates = [
        ("Can someone order more {item}?", "order_request"),
        ("Please order {item} from supplier", "order_request"),
        ("We need to purchase {item}", "purchase_request"),
        ("Order {item} for next week", "scheduled_order"),
        ("Buy more {item}", "purchase_request"),
        ("Get quotes for {item}", "quote_request"),
        ("Where can we order {item}?", "supplier_inquiry"),
    ]
    
    for item in INVENTORY_ITEMS[:15]:
        for template, intent in templates:
            query = template.format(item=item)
            supplier = random.choice(SUPPLIERS)
            response = _generate_order_response(item, intent, supplier)
            examples.append({
                "query": query,
                "intent": "order_request",
                "sub_intent": intent,
                "response": response,
                "agent": "InventoryAgent"
            })
    
    return examples


def generate_general_inventory_examples() -> List[Dict[str, str]]:
    """Generate general inventory management examples."""
    examples = [
        {
            "query": "Show me all inventory",
            "intent": "full_inventory_view",
            "response": "Here's the complete inventory organized by category: [categories listed]",
            "agent": "InventoryAgent"
        },
        {
            "query": "What items are running low?",
            "intent": "low_stock_check",
            "response": "The following items are below minimum threshold: [list items]",
            "agent": "InventoryAgent"
        },
        {
            "query": "Which supplies need reordering?",
            "intent": "reorder_check",
            "response": "These items need reordering: [list with quantities and suppliers]",
            "agent": "InventoryAgent"
        },
        {
            "query": "Check lab equipment inventory",
            "intent": "category_check",
            "response": "Lab Equipment inventory: [list items in category]",
            "agent": "InventoryAgent"
        },
        {
            "query": "What electronics do we have?",
            "intent": "category_check",
            "response": "Electronics inventory: [list electronics with quantities]",
            "agent": "InventoryAgent"
        }
    ]
    return examples


def generate_conversational_examples() -> List[Dict[str, str]]:
    """Generate natural conversational examples."""
    examples = [
        {
            "query": "Hey, we're running short on pencils for tomorrow's class",
            "intent": "urgent_low_stock",
            "response": "I see you're low on pencils. Current stock: 5 boxes. Would you like me to help you order more? Here are available suppliers: [list]",
            "agent": "InventoryAgent"
        },
        {
            "query": "Do we have enough Arduino kits for the robotics workshop next week?",
            "intent": "adequacy_check",
            "response": "Let me check Arduino kits... We have 8 kits available. How many students are attending? I can help you order more if needed.",
            "agent": "InventoryAgent"
        },
        {
            "query": "The chemistry lab needs safety goggles. Can you check stock?",
            "intent": "check_and_recommend",
            "response": "Safety goggles - Current stock: 15 pairs. Minimum required: 20. I recommend ordering 10 more pairs. Would you like supplier options?",
            "agent": "InventoryAgent"
        }
    ]
    return examples


def _generate_check_response(item: str, intent: str) -> str:
    """Generate appropriate response for inventory check."""
    qty = random.randint(5, 50)
    unit = "units" if item in ["microscopes", "Arduino kits"] else "pieces"
    
    if intent == "check_quantity":
        return f"We currently have {qty} {unit} of {item} in stock."
    elif intent == "check_adequacy":
        return f"Yes, we have {qty} {unit} of {item}, which is above the minimum threshold."
    else:
        return f"{item.title()}: {qty} {unit} available in storage room B."


def _generate_low_stock_response(item: str, intent: str) -> str:
    """Generate response for low stock situations."""
    qty = random.randint(1, 5)
    supplier = random.choice(SUPPLIERS)
    
    if "urgent" in intent:
        return f"⚠️ URGENT: Only {qty} {item} remaining. I found {supplier} can deliver within 24 hours. Order now?"
    else:
        return f"Stock alert: {item} is low ({qty} remaining). Recommended suppliers: {supplier}."


def _generate_order_response(item: str, intent: str, supplier: str) -> str:
    """Generate response for order requests."""
    price = random.randint(5, 50)
    
    if intent == "supplier_inquiry":
        return f"You can order {item} from {supplier} at ${price} per unit. I can generate an order link."
    elif intent == "quote_request":
        return f"Quote for {item}: {supplier} - ${price}/unit, 3-5 days delivery."
    else:
        return f"I'll help you order {item}. Best option: {supplier} at ${price}/unit. Shall I proceed?"


def generate_training_dataset(output_file: str = "inventory_training_data.jsonl"):
    """
    Generate complete training dataset in JSONL format for fine-tuning.
    """
    all_examples = []
    
    all_examples.extend(generate_inventory_check_examples())
    all_examples.extend(generate_low_stock_examples())
    all_examples.extend(generate_order_request_examples())
    all_examples.extend(generate_general_inventory_examples())
    all_examples.extend(generate_conversational_examples())
    
    # Shuffle examples
    random.shuffle(all_examples)
    
    # Convert to LLM fine-tuning format (instruction-following)
    training_data = []
    for ex in all_examples:
        # Format for instruction fine-tuning
        training_data.append({
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant for STEM center inventory management. Help teachers check stock, manage supplies, and coordinate orders. Be concise, helpful, and action-oriented."
                },
                {
                    "role": "user",
                    "content": ex["query"]
                },
                {
                    "role": "assistant",
                    "content": ex["response"]
                }
            ],
            "metadata": {
                "intent": ex["intent"],
                "agent": ex["agent"]
            }
        })
    
    # Write to JSONL file
    with open(output_file, 'w') as f:
        for item in training_data:
            f.write(json.dumps(item) + '\n')
    
    print(f"✅ Generated {len(training_data)} training examples")
    print(f"📁 Saved to: {output_file}")
    
    return training_data


def generate_validation_dataset(output_file: str = "inventory_validation_data.jsonl"):
    """
    Generate validation dataset (smaller, for testing).
    """
    examples = []
    
    # Add diverse validation examples
    validation_queries = [
        "Check pencil stock",
        "We need more beakers urgently",
        "Order Arduino kits from supplier",
        "What's running low?",
        "Show electronics inventory"
    ]
    
    for query in validation_queries:
        examples.append({
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant for STEM center inventory management."
                },
                {
                    "role": "user",
                    "content": query
                },
                {
                    "role": "assistant",
                    "content": "Validation response placeholder"
                }
            ]
        })
    
    with open(output_file, 'w') as f:
        for item in examples:
            f.write(json.dumps(item) + '\n')
    
    print(f"✅ Generated {len(examples)} validation examples")
    print(f"📁 Saved to: {output_file}")


if __name__ == "__main__":
    print("🚀 Generating training datasets for STEM inventory management...\n")
    generate_training_dataset()
    generate_validation_dataset()
    print("\n✨ Done! Ready for fine-tuning.")
