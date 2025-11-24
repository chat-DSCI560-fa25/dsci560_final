# STEM Center AI Chatbot - Setup & Deployment Guide

## Project Overview

This is a modular AI chatbot system for STEM centers that helps teachers manage:
- **Inventory Management** (Phase 1 - Current Implementation)
- Lesson Plans (Future)
- Procurement & Approvals (Future)
- General Assistance

### Architecture

```
User Message → LLM Core Router → Specialized Agents → Database/Actions → Response
                     ↓
              Fine-tuned Llama-3.1-8B
              (Inventory Domain Expert)
```

## Prerequisites

- **Python**: 3.10 or higher
- **MySQL**: 8.0 or higher (or MariaDB)
- **Node.js**: 16+ (for frontend, optional)
- **GPU**: Recommended for LLM training (NVIDIA with CUDA)

## Quick Start (Development)

### 1. Clone and Setup

```bash
cd groupchat_app_src/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup MySQL Database

```bash
# Login to MySQL
mysql -u root -p

# Run the schema script
source ../sql/schema.sql
```

Or manually:
```sql
CREATE DATABASE IF NOT EXISTS groupchat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'chatuser'@'localhost' IDENTIFIED BY 'chatpass';
GRANT ALL PRIVILEGES ON groupchat.* TO 'chatuser'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configure Environment

Create `.env` file in `backend/` directory:

```bash
# Database
DATABASE_URL=mysql+asyncmy://chatuser:chatpass@localhost:3306/groupchat

# JWT Secret (generate a secure random string)
SECRET_KEY=your-secret-key-here-change-this-in-production

# LLM API Configuration
LLM_API_BASE=http://localhost:8001/v1
LLM_MODEL=Meta-Llama-3.1-8B-Instruct
LLM_API_KEY=

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 4. Setup LLM Server (Choose One Option)

#### Option A: llama.cpp (Recommended for Local Development)

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Download Llama model (or use your fine-tuned model)
# Get from HuggingFace or use your fine-tuned GGUF

# Run server
./server -m path/to/model.gguf -c 4096 --port 8001
```

#### Option B: Ollama (Easiest)

```bash
# Install Ollama from https://ollama.ai

# Pull model
ollama pull llama3.1:8b

# Run (Ollama serves on port 11434 by default)
# Update LLM_API_BASE in .env to http://localhost:11434/v1
```

#### Option C: vLLM (Best for Production)

```bash
pip install vllm

vllm serve meta-llama/Meta-Llama-3.1-8B-Instruct --port 8001
```

### 5. Initialize Database and Start Server

```bash
# The app will auto-create tables on startup
python app.py

# Or use uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 6. Add Sample Inventory Data

```bash
# Create a Python script or use the API

curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"password123"}'

# Get token from response, then:

curl -X POST http://localhost:8000/api/inventory \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pencils",
    "category": "Stationery",
    "quantity": 50,
    "unit": "boxes",
    "min_quantity": 10,
    "location": "Storage Room A"
  }'
```

Or use the provided script:

```python
python scripts/seed_inventory.py  # Create this script
```

## Training Your Own LLM (Phase 1)

### 1. Generate Training Data

```bash
cd ml_training
python generate_training_data.py
```

This creates domain-specific training data for inventory management.

### 2. Install Training Dependencies

```bash
pip install -r requirements_training.txt
```

**Note**: This requires significant resources. See `ml_training/README.md` for details.

### 3. Fine-tune the Model

```bash
python finetune_llm.py
```

**Training time**: 30-90 minutes depending on GPU.

### 4. Deploy Fine-tuned Model

```bash
# Option 1: llama.cpp
llama-server --model inventory_llm_model_gguf/model.gguf --port 8001

# Option 2: Update .env to point to your model
LLM_MODEL=./ml_training/inventory_llm_model
```

## Testing the System

### Test Inventory Agent

1. Start the server
2. Login to the web interface at `http://localhost:8000`
3. Try these queries:

```
- "How many pencils do we have?"
- "We're running low on beakers"
- "Can you order more Arduino kits?"
- "Show me all inventory"
- "What items need restocking?"
```

### API Testing

```bash
# Get all inventory
curl http://localhost:8000/api/inventory

# Get low stock items
curl http://localhost:8000/api/inventory/low-stock

# Get available agents
curl http://localhost:8000/api/agents
```

## Production Deployment

### Using Docker (Recommended)

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: groupchat
      MYSQL_USER: chatuser
      MYSQL_PASSWORD: chatpass
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: mysql+asyncmy://chatuser:chatpass@mysql:3306/groupchat
    depends_on:
      - mysql

  llm_server:
    image: ghcr.io/ggerganov/llama.cpp:server
    ports:
      - "8001:8001"
    volumes:
      - ./models:/models
    command: --model /models/model.gguf --port 8001

volumes:
  mysql_data:
```

Deploy:
```bash
docker-compose up -d
```

### Manual Deployment (Linux Server)

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3.10 python3-pip mysql-server nginx

# 2. Setup MySQL (follow steps above)

# 3. Clone and install
git clone <your-repo>
cd groupchat_app_src/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Setup systemd service
sudo nano /etc/systemd/system/stem-chatbot.service
```

Service file:
```ini
[Unit]
Description=STEM Center Chatbot
After=network.target mysql.service

[Service]
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable stem-chatbot
sudo systemctl start stem-chatbot
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Security Considerations

1. **Change Secret Keys**: Generate strong `SECRET_KEY` in production
2. **Database Security**: Use strong passwords, restrict network access
3. **API Rate Limiting**: Add rate limiting middleware
4. **HTTPS**: Use SSL/TLS in production (Let's Encrypt)
5. **Input Validation**: Already implemented via Pydantic
6. **SQL Injection**: Protected via SQLAlchemy ORM

## Monitoring

### Application Logs

```bash
# View logs
tail -f /var/log/stem-chatbot/app.log

# Or with systemd
journalctl -u stem-chatbot -f
```

### Database Monitoring

```sql
-- Check inventory levels
SELECT * FROM inventory_items WHERE quantity <= min_quantity;

-- View recent transactions
SELECT * FROM inventory_transactions ORDER BY created_at DESC LIMIT 10;

-- User activity
SELECT username, COUNT(*) as message_count 
FROM users u 
JOIN messages m ON u.id = m.user_id 
GROUP BY username;
```

### LLM Performance

Monitor:
- Response time (should be < 2 seconds)
- Token usage
- Error rates

## Troubleshooting

### "Cannot connect to database"
- Check MySQL is running: `sudo systemctl status mysql`
- Verify credentials in `.env`
- Test connection: `mysql -u chatuser -p groupchat`

### "LLM API error"
- Check LLM server is running
- Verify `LLM_API_BASE` in `.env`
- Test endpoint: `curl http://localhost:8001/v1/models`

### "Agent not responding"
- Check agent registration in `llm_core.py`
- View logs for errors
- Test agent directly via API: `/api/agents`

### "Out of memory during training"
- Reduce batch size in `finetune_llm.py`
- Use smaller model (8B instead of 70B)
- Enable 4-bit quantization

## Adding New Features

### Adding a New Agent

1. Create agent file: `agents/new_agent.py`
2. Inherit from `BaseAgent`
3. Implement required methods
4. Register in `agents/__init__.py`
5. Add to `llm_core.py` router
6. Generate training data for the domain
7. Retrain LLM (optional but recommended)

Example:
```python
from agents.base_agent import BaseAgent

class ProcurementAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProcurementAgent", "Handles purchase orders")
    
    async def can_handle(self, message, context):
        # Implementation
        pass
    
    async def execute(self, message, context, session):
        # Implementation
        pass
```

## Android App Integration

The `twa_android_src/` folder contains a Trusted Web Activity wrapper. Update the URL in the app to point to your deployed backend.

## Roadmap

### Phase 1: Inventory Management (Current)
- [x] Agent architecture
- [x] Inventory database models
- [x] LLM fine-tuning pipeline
- [x] API endpoints
- [ ] Web UI improvements
- [ ] Mobile app testing

### Phase 2: Lesson Plans (Next)
- [ ] RAG system for lesson plans
- [ ] Vector database integration
- [ ] Lesson plan agent
- [ ] Search and recommendation

### Phase 3: Procurement & Approvals
- [ ] Approval workflow system
- [ ] Purchase order generation
- [ ] Email/notification integration

### Phase 4: Advanced Features
- [ ] Multi-tenant support
- [ ] Analytics dashboard
- [ ] Voice interface
- [ ] Mobile notifications

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Llama 3.1 Guide](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)
- [Fine-tuning Guide](ml_training/README.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes (follow existing code style)
4. Test thoroughly
5. Submit pull request

## License

[Your License Here]

## Support

For issues or questions:
- Check troubleshooting section
- Review logs
- Create an issue on GitHub

---

**Built for STEM educators**
