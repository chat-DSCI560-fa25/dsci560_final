# 🚀 Quick Reference Guide

## Getting Started in 5 Minutes

### 1. Setup (One Time)
```bash
cd groupchat_app_src/backend
./quickstart.sh
```

### 2. Start LLM Server
```bash
# Using Ollama (easiest)
ollama pull llama3.1:8b
ollama serve

# Update .env
LLM_API_BASE=http://localhost:11434/v1
```

### 3. Start Backend
```bash
source venv/bin/activate
python app.py
```

### 4. Access
- **Web**: http://localhost:8000
- **Login**: admin / admin123

---

## Common Commands

### Development
```bash
# Activate environment
source venv/bin/activate

# Run server with auto-reload
uvicorn app:app --reload

# Seed database
python seed_database.py

# Generate training data
cd ml_training && python generate_training_data.py
```

### Training
```bash
cd ml_training

# Install training deps
pip install -r requirements_training.txt

# Fine-tune model
python finetune_llm.py  # 30-90 min

# Deploy model
llama-server --model inventory_llm_model_gguf/model.gguf --port 8001
```

### Database
```bash
# Connect to MySQL
mysql -u chatuser -p groupchat

# Useful queries
SELECT * FROM inventory_items WHERE quantity <= min_quantity;
SELECT * FROM inventory_transactions ORDER BY created_at DESC LIMIT 10;
```

---

## Testing Queries

Try these in the chat:

### Inventory Checks
- "How many pencils do we have?"
- "Check stock for Arduino kits"
- "Show me all lab equipment"
- "What's in storage room A?"

### Low Stock
- "We're running low on beakers"
- "Almost out of markers"
- "What items need restocking?"

### Orders
- "Can someone order more microscopes?"
- "Where can we buy chemistry sets?"
- "Get quotes for Raspberry Pi"

### General
- "Show all inventory"
- "What's available in the electronics category?"

---

## API Quick Reference

### Auth
```bash
# Signup
curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass123"}'

# Login (get token)
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass123"}'
```

### Inventory
```bash
# Get all items
curl http://localhost:8000/api/inventory

# Get low stock
curl http://localhost:8000/api/inventory/low-stock

# Add item (requires auth)
curl -X POST http://localhost:8000/api/inventory \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Test Item",
    "category":"Test",
    "quantity":10,
    "unit":"units",
    "min_quantity":5
  }'
```

### Suppliers
```bash
# Get suppliers for item
curl http://localhost:8000/api/suppliers?item_name=Arduino

# List all suppliers
curl http://localhost:8000/api/suppliers
```

---

## File Locations

### Configuration
- **Environment**: `backend/.env`
- **Database**: MySQL on localhost:3306

### Code
- **Main App**: `backend/app.py`
- **Agents**: `backend/agents/`
- **Models**: `backend/db.py`
- **Router**: `backend/llm_core.py`

### Training
- **Scripts**: `backend/ml_training/`
- **Models**: `backend/ml_training/inventory_llm_model/`
- **Data**: `backend/ml_training/*.jsonl`

---

## Environment Variables

```bash
# Required
DATABASE_URL=mysql+asyncmy://chatuser:chatpass@localhost:3306/groupchat
SECRET_KEY=your-secret-key
LLM_API_BASE=http://localhost:8001/v1
LLM_MODEL=Meta-Llama-3.1-8B-Instruct

# Optional
LLM_API_KEY=
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## Adding New Features

### New Inventory Item
```python
from db import InventoryItem, SessionLocal

async def add_item():
    async with SessionLocal() as session:
        item = InventoryItem(
            name="New Item",
            category="Category",
            quantity=100,
            unit="units",
            min_quantity=20
        )
        session.add(item)
        await session.commit()
```

### New Agent
```python
# 1. Create agents/my_agent.py
from .base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyAgent", "Description")
    
    async def can_handle(self, message, context):
        # Return (True, confidence) if can handle
        return False, 0.0
    
    async def execute(self, message, context, session):
        return {
            "success": True,
            "message": "Response",
            "data": None
        }

# 2. Register in agents/__init__.py
from .my_agent import MyAgent
__all__ = ['BaseAgent', 'InventoryAgent', 'MyAgent']

# 3. Add to llm_core.py
def _register_agents(self):
    self.agents.append(InventoryAgent())
    self.agents.append(MyAgent())
```

---

## Troubleshooting Quick Fixes

### Can't connect to database
```bash
# Start MySQL
sudo systemctl start mysql

# Reset password
mysql -u root -p
ALTER USER 'chatuser'@'localhost' IDENTIFIED BY 'chatpass';
FLUSH PRIVILEGES;
```

### LLM not responding
```bash
# Check if server is running
curl http://localhost:8001/v1/models

# Restart LLM server
# For Ollama:
ollama serve

# For llama.cpp:
./server -m model.gguf --port 8001
```

### Dependencies issue
```bash
# Reinstall
pip install --force-reinstall -r requirements.txt

# Or create fresh environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Training out of memory
```python
# Edit finetune_llm.py
per_device_train_batch_size = 1  # Reduce from 2
gradient_accumulation_steps = 8  # Increase from 4
MAX_SEQ_LENGTH = 1024  # Reduce from 2048
```

---

## Performance Tips

### Speed Up Inference
- Use GGUF quantized models (Q4_K_M or Q5_K_M)
- Enable GPU: `llama-server --model model.gguf -ngl 35`
- Reduce max_tokens in llm.py

### Reduce Memory Usage
- Use 4-bit quantization during training
- Smaller batch sizes
- Gradient checkpointing (already enabled)

### Improve Accuracy
- Add more training examples
- Increase LoRA rank to 32
- Train for more epochs (5 instead of 3)
- Use larger model (70B instead of 8B)

---

## Monitoring

### Check System Health
```bash
# Backend
curl http://localhost:8000/api/agents

# Database
mysql -u chatuser -p -e "SELECT COUNT(*) FROM groupchat.inventory_items;"

# LLM
curl http://localhost:8001/v1/models
```

### View Logs
```bash
# Application
tail -f backend/app.log

# System service
journalctl -u stem-chatbot -f

# MySQL
tail -f /var/log/mysql/error.log
```

---

## Useful Links

- 📚 [Full Documentation](PROJECT_DOCUMENTATION.md)
- 🛠️ [Setup Guide](README_SETUP.md)
- 🎓 [Training Guide](backend/ml_training/README.md)
- 🐛 [GitHub Issues](your-repo/issues)

---

## Support

If something's not working:

1. ✅ Check this guide
2. ✅ Read error messages carefully
3. ✅ Review logs
4. ✅ Check troubleshooting section
5. ✅ Search documentation
6. ❓ Create GitHub issue with:
   - What you tried
   - Error message
   - System info (OS, Python version)

---

**Happy coding! 🚀**
