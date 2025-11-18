"""
Fine-tuning script for Meta-Llama-3.1-8B-Instruct using Unsloth and LoRA.
Optimized for STEM center inventory management domain.

Requirements:
- unsloth (for efficient fine-tuning)
- transformers
- datasets
- peft (for LoRA)
- trl (for SFTTrainer)
"""

import os
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
import json

# Configuration
MODEL_NAME = "unsloth/Meta-Llama-3.1-8B-Instruct"  # Using Unsloth's optimized version
MAX_SEQ_LENGTH = 2048
DTYPE = None  # Auto-detect (float16 for T4, bfloat16 for Ampere+)
LOAD_IN_4BIT = True  # Use 4-bit quantization to save memory

# LoRA Configuration
LORA_R = 16  # Rank
LORA_ALPHA = 16  # Scaling factor
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# Training Configuration
OUTPUT_DIR = "./inventory_llm_model"
TRAINING_DATA = "./inventory_training_data.jsonl"
VALIDATION_DATA = "./inventory_validation_data.jsonl"


def load_model_and_tokenizer():
    """
    Load the base model with 4-bit quantization and prepare for LoRA fine-tuning.
    """
    print(f"🔄 Loading model: {MODEL_NAME}")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=DTYPE,
        load_in_4bit=LOAD_IN_4BIT,
    )
    
    # Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=TARGET_MODULES,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Unsloth's optimized gradient checkpointing
        random_state=42,
    )
    
    print("✅ Model loaded with LoRA adapters")
    return model, tokenizer


def format_chat_template(example):
    """
    Format examples according to Llama-3.1-Instruct chat template.
    """
    messages = example["messages"]
    text = ""
    
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        if role == "system":
            text += f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
        elif role == "user":
            text += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
        elif role == "assistant":
            text += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
    
    return {"text": text}


def prepare_dataset():
    """
    Load and prepare the training and validation datasets.
    """
    print(f"📚 Loading datasets...")
    
    # Load JSONL files
    train_dataset = load_dataset('json', data_files=TRAINING_DATA, split='train')
    val_dataset = load_dataset('json', data_files=VALIDATION_DATA, split='train')
    
    # Format for chat template
    train_dataset = train_dataset.map(format_chat_template, remove_columns=train_dataset.column_names)
    val_dataset = val_dataset.map(format_chat_template, remove_columns=val_dataset.column_names)
    
    print(f"✅ Training samples: {len(train_dataset)}")
    print(f"✅ Validation samples: {len(val_dataset)}")
    
    return train_dataset, val_dataset


def train_model(model, tokenizer, train_dataset, val_dataset):
    """
    Fine-tune the model using SFTTrainer.
    """
    print("🚀 Starting fine-tuning...")
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,  # Effective batch size = 2 * 4 = 8
        warmup_steps=50,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        optim="adamw_8bit",  # 8-bit optimizer for memory efficiency
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",  # Disable wandb/tensorboard for simplicity
    )
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
    )
    
    # Train
    trainer.train()
    
    print("✅ Training complete!")
    return trainer


def save_model(model, tokenizer):
    """
    Save the fine-tuned model and tokenizer.
    """
    print(f"💾 Saving model to {OUTPUT_DIR}")
    
    # Save LoRA adapters (lightweight)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    # Also save in formats for different inference engines
    print("📦 Saving in GGUF format for llama.cpp...")
    model.save_pretrained_gguf(
        f"{OUTPUT_DIR}_gguf",
        tokenizer,
        quantization_method="q4_k_m"  # 4-bit quantization
    )
    
    print("✅ Model saved successfully!")
    print(f"   - LoRA adapters: {OUTPUT_DIR}")
    print(f"   - GGUF format: {OUTPUT_DIR}_gguf")


def test_model(model, tokenizer):
    """
    Test the fine-tuned model with sample queries.
    """
    print("\n🧪 Testing fine-tuned model...\n")
    
    FastLanguageModel.for_inference(model)  # Enable inference mode
    
    test_queries = [
        "We're running low on pencils for tomorrow",
        "How many Arduino kits do we have in stock?",
        "Can you order more beakers from the supplier?",
        "What lab equipment is running low?"
    ]
    
    for query in test_queries:
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant for STEM center inventory management. Help teachers check stock, manage supplies, and coordinate orders."
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        # Format with chat template
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        
        # Generate response
        outputs = model.generate(
            inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"Query: {query}")
        print(f"Response: {response}\n")
        print("-" * 80 + "\n")


def main():
    """
    Main fine-tuning pipeline.
    """
    print("=" * 80)
    print("🎯 STEM Center Inventory LLM Fine-Tuning")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Training data: {TRAINING_DATA}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 80 + "\n")
    
    # Check CUDA availability
    if not torch.cuda.is_available():
        print("⚠️  WARNING: CUDA not available. Training will be very slow on CPU.")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            return
    else:
        print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}\n")
    
    # Step 1: Load model
    model, tokenizer = load_model_and_tokenizer()
    
    # Step 2: Prepare datasets
    train_dataset, val_dataset = prepare_dataset()
    
    # Step 3: Train
    trainer = train_model(model, tokenizer, train_dataset, val_dataset)
    
    # Step 4: Save
    save_model(model, tokenizer)
    
    # Step 5: Test
    test_model(model, tokenizer)
    
    print("\n" + "=" * 80)
    print("✨ Fine-tuning complete! Your inventory-specialized LLM is ready.")
    print("=" * 80)


if __name__ == "__main__":
    main()
