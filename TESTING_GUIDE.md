# 🧪 Testing Guide

## Quick Test Checklist

### ✅ Phase 1: Basic Setup Test (5 minutes)

```bash
# 1. Check Python
python3 --version  # Should be 3.10+

# 2. Check MySQL
mysql --version
mysql -u root -p -e "SELECT 1"  # Should work

# 3. Check directory
cd groupchat_app_src/backend
ls -la  # Should see app.py, db.py, etc.
```

### ✅ Phase 2: Installation Test (10 minutes)

```bash
# Run quickstart
./quickstart.sh

# Should complete without errors
# Check output for:
# ✅ Virtual environment created
# ✅ Dependencies installed
# ✅ .env file created
# ✅ Database created
# ✅ Sample data loaded
```

### ✅ Phase 3: Database Test

```bash
# Connect to MySQL
mysql -u chatuser -p groupchat
# Password: chatpass

# Run these queries:
SELECT COUNT(*) FROM users;           -- Should return 2
SELECT COUNT(*) FROM inventory_items; -- Should return 16
SELECT COUNT(*) FROM suppliers;       -- Should return 10

# Check low stock items
SELECT name, quantity, min_quantity 
FROM inventory_items 
WHERE quantity <= min_quantity;
-- Should return ~5 items
```

### ✅ Phase 4: Backend Test

```bash
# Start server
source venv/bin/activate
python app.py

# Should see:
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

In another terminal:
```bash
# Test health
curl http://localhost:8000/api/agents

# Should return JSON with agents list
```

### ✅ Phase 5: Authentication Test

```bash
# Test signup
curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'

# Should return: {"ok":true,"token":"..."}

# Test login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Should return: {"ok":true,"token":"..."}
# Save this token!
```

### ✅ Phase 6: Inventory API Test

```bash
# Set token from previous step
TOKEN="your_token_here"

# Get all inventory
curl http://localhost:8000/api/inventory

# Get low stock items
curl http://localhost:8000/api/inventory/low-stock

# Get suppliers
curl http://localhost:8000/api/suppliers

# Add new item
curl -X POST http://localhost:8000/api/inventory \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Test Item",
    "category":"Test",
    "quantity":10,
    "unit":"units",
    "min_quantity":5
  }'
```

### ✅ Phase 7: LLM Setup Test

Choose one option:

#### Option A: Ollama (Easiest)
```bash
# Install Ollama from https://ollama.ai

# Pull model
ollama pull llama3.1:8b

# Start server
ollama serve

# Test
curl http://localhost:11434/v1/models

# Update backend/.env
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL=llama3.1:8b
```

#### Option B: llama.cpp
```bash
# Download llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Download a GGUF model (or use your fine-tuned one)
# Example: wget https://huggingface.co/.../model.gguf

# Start server
./server -m model.gguf --port 8001 -c 4096

# Test
curl http://localhost:8001/v1/models
```

### ✅ Phase 8: Chat Integration Test

```bash
# With backend and LLM server running...

# Send test message
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"How many pencils do we have?"}'

# Wait a moment, then get messages
curl http://localhost:8000/api/messages

# Should see:
# 1. Your message
# 2. Bot response with inventory info
```

### ✅ Phase 9: Web Interface Test

1. Open browser to `http://localhost:8000`
2. Login with `admin` / `admin123`
3. Type test queries (see below)
4. Verify bot responses

### ✅ Phase 10: Training Data Generation

```bash
cd ml_training

# Generate data
python generate_training_data.py

# Should create:
# - inventory_training_data.jsonl
# - inventory_validation_data.jsonl

# Check files
wc -l *.jsonl
# training: ~300 lines
# validation: ~10 lines

# Inspect format
head -n 1 inventory_training_data.jsonl | python -m json.tool
```

---

## Test Queries

### ✅ Inventory Check Queries

```
✓ "How many pencils do we have?"
✓ "Check stock for Arduino kits"
✓ "What's the inventory for beakers?"
✓ "Show me all lab equipment"
✓ "How many microscopes are available?"
✓ "Check electronics inventory"
✓ "What do we have in storage room A?"
```

**Expected**:
- Bot identifies as inventory query
- Routes to InventoryAgent
- Shows current stock levels
- Formatted with emoji and markdown

### ✅ Low Stock Alert Queries

```
✓ "We're running low on markers"
✓ "Almost out of test tubes"
✓ "Running short on safety goggles"
✓ "Need more jumper wires"
✓ "What items need restocking?"
✓ "Show me low stock items"
✓ "We're short on microscopes for tomorrow"
```

**Expected**:
- Detects urgency if present
- Shows current vs minimum stock
- Lists suppliers with links
- Provides ordering options

### ✅ Order Request Queries

```
✓ "Can someone order more beakers?"
✓ "We need to buy Arduino kits"
✓ "Where can we order safety goggles?"
✓ "Get quotes for Raspberry Pi"
✓ "Purchase more chemistry sets"
✓ "Who supplies microscopes?"
```

**Expected**:
- Shows supplier information
- Provides pricing
- Includes order links
- Shows delivery time

### ✅ General Queries

```
✓ "Show all inventory"
✓ "What's in the electronics category?"
✓ "List lab equipment"
✓ "Inventory summary"
```

**Expected**:
- Organizes by category
- Shows quantities
- Indicates low stock items
- Clear formatting

---

## Advanced Testing

### Fine-tuning Test (If you trained a model)

```bash
cd ml_training

# Install training deps (first time only)
pip install -r requirements_training.txt

# Train model (30-90 min)
python finetune_llm.py

# Check output
ls -lh inventory_llm_model/
ls -lh inventory_llm_model_gguf/

# Deploy
llama-server --model inventory_llm_model_gguf/model.gguf --port 8001

# Test with same queries as before
# Compare responses to base model
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.token = response.json()["token"]
    
    @task
    def send_message(self):
        self.client.post("/api/messages",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"content": "How many pencils do we have?"})
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

Open `http://localhost:8089` and start test with:
- Users: 10
- Spawn rate: 2
- Run time: 1 minute

### Performance Benchmarks

Target metrics:
- **Response time**: < 2 seconds
- **Throughput**: 10+ req/sec
- **Error rate**: < 1%
- **Database queries**: < 100ms
- **LLM latency**: < 1 second

---

## Troubleshooting Tests

### Test 1: Database Connection

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    engine = create_async_engine(
        "mysql+asyncmy://chatuser:chatpass@localhost:3306/groupchat"
    )
    async with engine.begin() as conn:
        result = await conn.execute("SELECT 1")
        print("✅ Database connected:", result.scalar())

asyncio.run(test())
```

### Test 2: Agent Routing

```python
import asyncio
from llm_core import llm_router

async def test():
    context = {"username": "test", "timestamp": 0}
    
    queries = [
        "How many pencils do we have?",
        "We're running low on markers",
        "Can someone order beakers?",
    ]
    
    for query in queries:
        result = await llm_router.route_message(query, context, None)
        print(f"\nQuery: {query}")
        print(f"Agent: {result['agent_used']}")
        print(f"Confidence: {result['confidence']}")

asyncio.run(test())
```

### Test 3: LLM Connection

```bash
# Test OpenAI-compatible endpoint
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Meta-Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "user", "content": "Say hello"}
    ],
    "max_tokens": 50
  }'
```

### Test 4: WebSocket

```javascript
// Open browser console at http://localhost:8000
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('✅ WebSocket connected');
};

ws.onmessage = (event) => {
  console.log('📨 Message:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.log('❌ Error:', error);
};
```

---

## Validation Checklist

### Functional Tests
- [ ] Users can signup
- [ ] Users can login
- [ ] Messages are saved
- [ ] Bot responds to inventory queries
- [ ] Stock levels are accurate
- [ ] Suppliers are shown correctly
- [ ] Low stock alerts work
- [ ] WebSocket updates in real-time

### Agent Tests
- [ ] InventoryAgent triggers on inventory queries
- [ ] Agent can parse item names from natural language
- [ ] Agent detects urgency correctly
- [ ] Agent provides actionable responses
- [ ] Agent handles errors gracefully

### Database Tests
- [ ] Inventory items created
- [ ] Transactions logged
- [ ] Suppliers stored
- [ ] Foreign keys work
- [ ] Timestamps accurate

### LLM Tests
- [ ] Server responds
- [ ] Reasonable latency (< 2s)
- [ ] Responses are coherent
- [ ] Fine-tuned model understands STEM items
- [ ] Model follows instruction format

### Security Tests
- [ ] JWT authentication works
- [ ] Unauthorized requests blocked
- [ ] Passwords hashed (not stored plain)
- [ ] SQL injection prevented (ORM)
- [ ] XSS prevented (frontend sanitization)

---

## Success Criteria

### Must Have (Phase 1)
- ✅ Backend runs without errors
- ✅ Database connected and seeded
- ✅ Authentication works
- ✅ Inventory agent responds correctly
- ✅ Supplier lookup functions
- ✅ Web interface accessible

### Should Have
- ✅ LLM server running
- ✅ Training data generated
- ✅ WebSocket real-time updates
- ✅ API documentation accessible
- ✅ Error handling robust

### Nice to Have
- 🎯 Fine-tuned model deployed
- 🎯 Load testing passed
- 🎯 Mobile app tested
- 🎯 Production deployment

---

## Bug Reporting Template

If you find issues:

```markdown
**Bug Description:**
Clear description of what's wrong

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: macOS/Linux/Windows
- Python version: 
- MySQL version:
- LLM server: Ollama/llama.cpp/vLLM

**Logs:**
Paste relevant error messages

**Screenshots:**
If applicable
```

---

## Testing Schedule

### Day 1: Basic Setup
- ✅ Installation
- ✅ Database setup
- ✅ Backend startup
- ✅ API testing

### Day 2: Integration
- ✅ LLM server setup
- ✅ Agent testing
- ✅ Web interface
- ✅ End-to-end flow

### Day 3: Training
- ✅ Data generation
- ✅ Fine-tuning
- ✅ Model comparison
- ✅ Deployment

### Day 4: Production
- ✅ Load testing
- ✅ Security audit
- ✅ Performance tuning
- ✅ Documentation review

---

## Test Results Template

```markdown
# Test Results - [Date]

## Environment
- Backend: Running ✅ / Failed ❌
- Database: Connected ✅ / Failed ❌
- LLM Server: Running ✅ / Failed ❌

## Functional Tests
- Authentication: ✅ / ❌
- Chat messaging: ✅ / ❌
- Inventory queries: ✅ / ❌
- Supplier lookup: ✅ / ❌
- Low stock alerts: ✅ / ❌

## Performance
- Average response time: X.XX seconds
- Throughput: XX req/sec
- Error rate: X.X%

## Issues Found
1. Issue description - Priority: High/Medium/Low
2. Issue description - Priority: High/Medium/Low

## Next Steps
- [ ] Action item 1
- [ ] Action item 2
```

---

**Ready to test! Start with Phase 1 and work through the checklist.** 🧪

```bash
cd groupchat_app_src/backend
./quickstart.sh
```
