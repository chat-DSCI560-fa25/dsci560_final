# STEM Center Inventory Management - ML Training Guide

## Overview

This guide covers the complete process of fine-tuning Meta-Llama-3.1-8B-Instruct for STEM center inventory management.

## 🎯 Goal

Train a specialized LLM that understands:
- Inventory queries (stock checks, quantity lookups)
- Low stock alerts and urgency detection
- Supplier management and ordering
- STEM-specific terminology (lab equipment, electronics, teaching materials)

## 📋 Prerequisites

### Hardware Requirements
- **Recommended**: NVIDIA GPU with 16GB+ VRAM (RTX 4090, A100, etc.)
- **Minimum**: NVIDIA GPU with 8GB VRAM (RTX 3060, T4)
- **RAM**: 32GB+ system RAM recommended
- **Storage**: 50GB free space for models and datasets

### Software Requirements
- Python 3.10+
- CUDA 11.8+ or 12.1+
- Linux or WSL2 (recommended), or macOS with M1/M2/M3

## 🚀 Quick Start

### Step 1: Install Training Dependencies

```bash
cd ml_training

# Create a virtual environment
python -m venv venv_training
source venv_training/bin/activate  # On Windows: venv_training\Scripts\activate

# Install training requirements
pip install -r requirements_training.txt
```

### Step 2: Generate Training Data

```bash
python generate_training_data.py
```

This creates:
- `inventory_training_data.jsonl` - Main training dataset (~300+ examples)
- `inventory_validation_data.jsonl` - Validation dataset

### Step 3: Fine-tune the Model

```bash
python finetune_llm.py
```

**Training Time Estimates:**
- RTX 4090: ~30-45 minutes
- RTX 3090: ~45-60 minutes
- T4 (Colab): ~60-90 minutes

**Output Files:**
- `./inventory_llm_model/` - LoRA adapters (lightweight, ~100MB)
- `./inventory_llm_model_gguf/` - Quantized GGUF format for llama.cpp

### Step 4: Test the Model

The training script automatically tests the model. You can also run manual tests:

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./inventory_llm_model",
    max_seq_length=2048,
)

FastLanguageModel.for_inference(model)

# Test query
messages = [
    {"role": "system", "content": "You are an AI assistant for STEM center inventory management."},
    {"role": "user", "content": "We're running low on pencils for tomorrow"}
]

inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to("cuda")
outputs = model.generate(inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0]))
```

## 🔧 Configuration Options

### Model Selection

You can use different Llama models by changing `MODEL_NAME` in `finetune_llm.py`:

```python
# 8B model (recommended for balance of quality and speed)
MODEL_NAME = "unsloth/Meta-Llama-3.1-8B-Instruct"

# 70B model (higher quality, needs more VRAM)
MODEL_NAME = "unsloth/Meta-Llama-3.1-70B-Instruct"  # Requires 48GB+ VRAM
```

### LoRA Parameters

Adjust for different memory/quality tradeoffs:

```python
LORA_R = 16  # Higher = more parameters (8, 16, 32, 64)
LORA_ALPHA = 16  # Usually same as LORA_R
LORA_DROPOUT = 0.05  # Regularization (0.0 - 0.1)
```

### Training Parameters

```python
num_train_epochs = 3  # 2-5 epochs typical
learning_rate = 2e-4  # 1e-4 to 5e-4
per_device_train_batch_size = 2  # Adjust based on VRAM
```

## 📊 Understanding the Training Data

Our dataset focuses on real-world STEM center scenarios:

### Example Categories:

1. **Inventory Checks** (30%)
   - "How many Arduino kits do we have?"
   - "Check stock for beakers"

2. **Low Stock Alerts** (25%)
   - "We're running low on pencils"
   - "Almost out of test tubes"

3. **Order Requests** (25%)
   - "Can someone order more chemistry sets?"
   - "Where can we buy microscopes?"

4. **General Management** (20%)
   - "Show all inventory"
   - "What's running low?"

### Data Format

Training data uses Llama-3.1's chat template:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an AI assistant for STEM center inventory management..."
    },
    {
      "role": "user",
      "content": "We're running low on pencils"
    },
    {
      "role": "assistant",
      "content": "⚠️ Low stock alert for pencils. Current: 5 boxes. I found School Supply Co can deliver within 24 hours..."
    }
  ]
}
```

## 🎓 Advanced Topics

### Adding Custom Training Data

1. Edit `generate_training_data.py` to add your specific items/scenarios
2. Regenerate datasets
3. Re-run training

### Expanding to Other Domains

To add procurement or lesson plan capabilities:

1. Create new data generation functions
2. Add examples to the dataset
3. Register new agents in `llm_core.py`

### Evaluating Model Performance

```python
# After training, check validation loss
# Lower validation loss = better generalization

# Manual testing checklist:
# ✓ Recognizes STEM-specific items
# ✓ Detects urgency in messages
# ✓ Provides supplier information
# ✓ Formats responses clearly
```

## 🐛 Troubleshooting

### Out of Memory Errors

1. Reduce `MAX_SEQ_LENGTH` from 2048 to 1024
2. Set `per_device_train_batch_size = 1`
3. Enable more aggressive quantization: `LOAD_IN_4BIT = True`
4. Use gradient checkpointing (already enabled)

### Slow Training

1. Ensure you're using GPU: `torch.cuda.is_available()` should return `True`
2. Check CUDA version matches PyTorch
3. Enable mixed precision (already enabled)
4. Use Unsloth (already configured)

### Model Not Learning

1. Check learning rate (try 5e-4 if 2e-4 is too low)
2. Increase epochs to 5
3. Verify training data quality
4. Check validation loss - should decrease over time

## 🚢 Deployment

### Option 1: llama.cpp (Recommended for Production)

```bash
# Use the GGUF model
llama-server --model inventory_llm_model_gguf/model.gguf --port 8001
```

### Option 2: vLLM (High throughput)

```bash
vllm serve ./inventory_llm_model --port 8001
```

### Option 3: Transformers (Simple)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("./inventory_llm_model")
tokenizer = AutoTokenizer.from_pretrained("./inventory_llm_model")
```

## 📈 Performance Metrics

After fine-tuning, expect:
- **Inventory Recognition**: 95%+ accuracy on STEM items
- **Intent Classification**: 90%+ accuracy
- **Response Quality**: Contextual, action-oriented
- **Inference Speed**: ~20-50 tokens/sec (depends on hardware)

## 🔄 Continuous Improvement

1. **Collect Real Usage Data**: Save actual chat messages
2. **Human Feedback**: Mark good/bad responses
3. **Iterative Training**: Add feedback data to training set
4. **A/B Testing**: Compare model versions

## 📚 Additional Resources

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [Llama 3.1 Model Card](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Instruction Fine-tuning Guide](https://huggingface.co/docs/trl/sft_trainer)

## 💡 Tips

1. **Start Small**: Fine-tune on 8B model first, scale to 70B if needed
2. **Monitor GPU Usage**: Use `nvidia-smi` to watch memory
3. **Save Checkpoints**: Training can be interrupted and resumed
4. **Version Control**: Track model versions and training configs
5. **Document Changes**: Keep notes on what works/doesn't work

## 🤝 Contributing Training Data

To contribute more training examples:
1. Follow the format in `generate_training_data.py`
2. Ensure diverse query phrasings
3. Include edge cases and error scenarios
4. Test with validation set

---

**Need Help?** Check the troubleshooting section or review training logs in `./inventory_llm_model/`
