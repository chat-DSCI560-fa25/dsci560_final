# LLM Server Setup Guide

All three LLM options are now installed! Choose the one that works best for you.

## ✅ Option 1: Ollama (Currently Active - EASIEST)

**Status:** ✅ Running as a service  
**Model:** llama3.1:8b (4.9GB) - Already downloaded

### Commands:
```bash
# Start Ollama (already started as service)
brew services start ollama

# Stop Ollama
brew services stop ollama

# Test if running
curl http://localhost:11434/v1/models

# Pull other models
ollama pull llama3.2:3b  # Smaller, faster
ollama pull codellama:7b  # Code-specialized
```

### Current .env configuration:
```
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL=llama3.1:8b
```

---

## Option 2: llama.cpp Server

**Status:** ✅ Installed  
**Requires:** GGUF model file

### Setup:
1. **Download a GGUF model** (if you don't have one):
   ```bash
   # Example: Download from Hugging Face
   cd ~/Downloads
   wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
   ```

2. **Start llama.cpp server:**
   ```bash
   llama-server \
     --model ~/Downloads/llama-2-7b-chat.Q4_K_M.gguf \
     --port 8001 \
     --host 0.0.0.0 \
     --n-gpu-layers 99
   ```

3. **Update .env:**
   ```
   LLM_API_BASE=http://localhost:8001/v1
   LLM_MODEL=llama-2-7b-chat
   ```

### Advantages:
- More control over quantization
- Can use custom GGUF models
- Lower memory usage with quantization

---

## Option 3: vLLM (For GPU Acceleration)

**Status:** ✅ Installed in venv  
**Best for:** Production, high throughput, GPU acceleration

### Setup:
1. **Start vLLM server:**
   ```bash
   cd /Users/dhyeydesai/Desktop/USC_MATERIAL/SEM3_MATERIAL/DSCI560/final/final/groupchat_app_src/backend
   
   venv/bin/vllm serve meta-llama/Meta-Llama-3.1-8B-Instruct \
     --port 8001 \
     --host 0.0.0.0 \
     --dtype auto
   ```

2. **Update .env:**
   ```
   LLM_API_BASE=http://localhost:8001/v1
   LLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
   ```

### Advantages:
- Fastest inference (GPU required)
- Best for production deployments
- Supports tensor parallelism
- Continuous batching for multiple requests

### Note:
- First run will download the model (~16GB)
- Requires Metal GPU support (M1/M2/M3 Mac)
- May need Hugging Face token for gated models

---

## Testing Your LLM Server

After starting any option, test the connection:

```bash
# Test API endpoint
curl http://localhost:11434/v1/models  # For Ollama
# OR
curl http://localhost:8001/v1/models   # For llama.cpp/vLLM

# Test chat completion
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## Restart Your FastAPI Server

After changing LLM server, restart the backend:

```bash
cd /Users/dhyeydesai/Desktop/USC_MATERIAL/SEM3_MATERIAL/DSCI560/final/final/groupchat_app_src/backend
venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## Current Status Summary

✅ **Homebrew:** Installed  
✅ **Ollama:** Running on port 11434  
✅ **llama.cpp:** Installed  
✅ **vLLM:** Installed in venv  
✅ **Model:** llama3.1:8b downloaded (4.9GB)  
✅ **.env:** Configured for Ollama  

**You're all set!** The chatbot should now respond to messages with "?" in them.
