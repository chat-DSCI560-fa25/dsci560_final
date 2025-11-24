# Flow AI

> Flow AI is an intelligent, modular chatbot system for STEM center teachers to manage inventory, lesson plans, and procurement through natural language conversations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![Llama](https://img.shields.io/badge/Llama-3.1--8B-red.svg)](https://huggingface.co/meta-llama)

---

## Quick Start

```bash
# 1. Navigate to backend
cd groupchat_app_src/backend

# 2. Run setup script
./quickstart.sh

# 3. Start LLM server (choose one)
ollama pull llama3.1:8b && ollama serve

# 4. Start backend
source venv/bin/activate
python app.py

# 5. Open http://localhost:8000
# Login: admin / admin123
```

**First time?** See [Setup Guide](groupchat_app_src/README_SETUP.md)

---

## What This Does

Teachers in STEM centers often text in group chats:
> "We're short on pencils for tomorrow. Can someone order more?"

**This chatbot joins your group chat to:**
- Instantly check inventory levels
- Alert on low stock with urgency detection  
- Suggest suppliers with direct ordering links
- Handle approvals (future)
- Find lesson plans (future)
- All through natural conversation

### Example Interaction

**Teacher**: "We're running low on Arduino kits for tomorrow's robotics class"

**Bot**: 
```
[InventoryAgent]

Arduino Uno Kits - Current stock: 15 kits
Stock is above minimum threshold (10 kits).

Available Suppliers:
• TechEd Supplies - $35.99/kit - [Order Now](link)
• Amazon Business - $32.99/kit - [Order Now](link)

Tip: You have enough for tomorrow's class!
```

---

## Features

### Phase 1: Inventory Management (IMPLEMENTED)

- **Stock Queries**: "How many microscopes do we have?"
- **Low Stock Alerts**: "Running short on beakers"
- **Supplier Lookup**: "Where can we order safety goggles?"
- **Order Assistance**: "Can someone buy more chemistry sets?"
- **Transaction History**: Full audit trail
- **Multi-category**: Stationery, Lab Equipment, Electronics, Tools

### Phase 2: Lesson Plans (PLANNED)

- RAG-based search over lesson plan library
- "Find photosynthesis lessons for grade 7"
- Curriculum alignment
- Teacher recommendations

### Phase 3: Procurement & Approvals (PLANNED)

- Purchase order generation
- Approval workflows
- Budget tracking
- Vendor management

---

## Architecture

```
User Message → LLM Core Router → Specialized Agents → Actions → Response
                     ↓
            Fine-tuned Llama-3.1-8B
            (Inventory Domain Expert)
```

**Modular Design**: Each feature is an independent agent. Easy to add, remove, or debug.

**Tech Stack**:
- **Backend**: FastAPI (Python 3.10+)
- **Database**: MySQL 8.0
- **LLM**: Meta-Llama-3.1-8B-Instruct (fine-tuned)
- **Training**: Unsloth + LoRA
- **Inference**: llama.cpp / vLLM / Ollama

See [Architecture Diagrams](ARCHITECTURE_DIAGRAMS.md) for details.

---

## Project Structure

```
final/
├── groupchat_app_src/
│   ├── backend/
│   │   ├── agents/              # Modular agent system
│   │   ├── ml_training/         # LLM fine-tuning pipeline
│   │   ├── app.py               # Main application
│   │   ├── db.py                # Database models
│   │   ├── llm_core.py          # Agent router
│   │   ├── seed_database.py     # Sample data
│   │   └── quickstart.sh        # Setup script
│   ├── frontend/                # Web interface
│   └── twa_android_src/         # Android app wrapper
├── Lesson Plans/                # Sample lesson plans
├── embedding/                   # RAG system (future)
└── Documentation files...
```

---

## Documentation

- [**Setup Guide**](groupchat_app_src/README_SETUP.md) - Complete installation & deployment
- [**Project Documentation**](groupchat_app_src/PROJECT_DOCUMENTATION.md) - Full system docs
- [**Training Guide**](groupchat_app_src/backend/ml_training/README.md) - Fine-tune your own LLM
- [**Quick Reference**](groupchat_app_src/QUICK_REFERENCE.md) - Common commands
- [**Testing Guide**](TESTING_GUIDE.md) - Test procedures
- [**Architecture Diagrams**](ARCHITECTURE_DIAGRAMS.md) - Visual system overview
- [**Implementation Summary**](IMPLEMENTATION_SUMMARY.md) - What we built

---

## Fine-Tuning Your Own LLM

We provide a **complete training pipeline** to specialize Llama-3.1-8B for your domain:

```bash
cd groupchat_app_src/backend/ml_training

# 1. Generate training data (300+ examples)
python generate_training_data.py

# 2. Install training dependencies
pip install -r requirements_training.txt

# 3. Fine-tune (30-90 minutes)
python finetune_llm.py

# 4. Deploy
llama-server --model inventory_llm_model_gguf/model.gguf --port 8001
```

**Result**: A model that understands STEM-specific terminology, recognizes inventory queries, and provides contextual responses.

See [Training Guide](groupchat_app_src/backend/ml_training/README.md) for details.

---

## Modular Design

Adding new features is straightforward:

```python
# 1. Create new agent
class LessonPlanAgent(BaseAgent):
    async def can_handle(self, message, context):
        return "lesson" in message.lower(), 0.8
    
    async def execute(self, message, context, session):
        # Implement RAG search
        return {"success": True, "message": "Found lesson plans..."}

# 2. Register agent
llm_router.agents.append(LessonPlanAgent())
```

That's it! The router automatically delegates queries to your new agent.

---

## Development

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- GPU (optional, for training)

### Setup
```bash
cd groupchat_app_src/backend
./quickstart.sh  # Automated setup
```

### Run
```bash
# Terminal 1: LLM Server
ollama serve

# Terminal 2: Backend
source venv/bin/activate
python app.py

# Access at http://localhost:8000
```

### Test
```bash
# API Tests
curl http://localhost:8000/api/inventory
curl http://localhost:8000/api/inventory/low-stock

# Web Interface
# Open browser, login as admin/admin123
# Type: "How many pencils do we have?"
```

See [Testing Guide](TESTING_GUIDE.md) for comprehensive tests.

---

## Database Schema

### Inventory System
- **inventory_items**: Stock levels, categories, thresholds
- **inventory_transactions**: Complete audit trail
- **suppliers**: Vendor information, pricing, order links

### User System
- **users**: Authentication, profiles
- **messages**: Chat history

Full schema in `groupchat_app_src/sql/schema.sql`

---

## Roadmap

### Phase 1: Inventory (Current)
- [x] Agent architecture
- [x] Database models
- [x] LLM fine-tuning pipeline
- [x] API endpoints
- [x] Web interface
- [ ] Mobile app testing

### Phase 2: Lesson Plans (Next)
- [ ] RAG system with vector DB
- [ ] Lesson plan indexing
- [ ] Search & recommendations
- [ ] Curriculum alignment

### Phase 3: Procurement
- [ ] Approval workflows
- [ ] Purchase orders
- [ ] Budget tracking
- [ ] Email notifications

### Phase 4: Advanced
- [ ] Multi-tenant support
- [ ] Analytics dashboard
- [ ] Voice interface
- [ ] Mobile notifications

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

**Want to add an agent?** See [Project Documentation](groupchat_app_src/PROJECT_DOCUMENTATION.md#modular-design)

---

## Troubleshooting

### Can't connect to database
```bash
sudo systemctl start mysql
mysql -u root -p
# Run schema.sql
```

### LLM not responding
```bash
# Check LLM server
curl http://localhost:8001/v1/models

# Restart if needed
ollama serve  # or llama-server ...
```

### Agent not triggering
- Check keywords in agent's `can_handle()` method
- View logs for confidence scores
- Test agent directly via API: `/api/agents`

See [Setup Guide](groupchat_app_src/README_SETUP.md#troubleshooting) for more.

---

## License

[Your License Here]

---

## Acknowledgments

- Meta AI for Llama 3.1
- Unsloth for efficient training
- FastAPI community
- STEM educators everywhere

---

## Support

- Check documentation first
- [Create an issue](your-repo/issues)
- [Discussions](your-repo/discussions)

---

## Star History

If this helps your STEM center, please star the repo!

---

<div align="center">

**Built for STEM educators**

[Setup Guide](groupchat_app_src/README_SETUP.md) • [Documentation](groupchat_app_src/PROJECT_DOCUMENTATION.md) • [Training Guide](groupchat_app_src/backend/ml_training/README.md)

</div>
