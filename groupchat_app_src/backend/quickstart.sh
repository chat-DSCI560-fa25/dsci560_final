#!/bin/bash

# Quick Start Script for STEM Center Chatbot
# This script helps you get up and running quickly

set -e

echo "=========================================="
echo "🚀 STEM Center Chatbot - Quick Start"
echo "=========================================="
echo ""

# Check Python version
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION found"

# Check if MySQL is running
if ! command -v mysql &> /dev/null; then
    echo "⚠️  MySQL not found. Please install MySQL 8.0 or higher."
    exit 1
fi
echo "✅ MySQL found"

# Navigate to backend directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cat > .env << EOL
# Database Configuration
DATABASE_URL=mysql+asyncmy://chatuser:chatpass@localhost:3306/groupchat

# JWT Secret (CHANGE THIS IN PRODUCTION!)
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# LLM API Configuration
LLM_API_BASE=http://localhost:8001/v1
LLM_MODEL=Meta-Llama-3.1-8B-Instruct
LLM_API_KEY=

# Server Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
EOL
    echo "✅ .env file created"
else
    echo "ℹ️  .env file already exists"
fi

# Setup database
echo ""
read -p "🗄️  Would you like to set up the MySQL database? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Please enter your MySQL root password:"
    mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS groupchat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'chatuser'@'localhost' IDENTIFIED BY 'chatpass';
GRANT ALL PRIVILEGES ON groupchat.* TO 'chatuser'@'localhost';
FLUSH PRIVILEGES;
EOF
    echo "✅ Database created"
fi

# Seed database
echo ""
read -p "🌱 Would you like to populate the database with sample data? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 seed_database.py
fi

# Generate training data
echo ""
read -p "📊 Would you like to generate training data for fine-tuning? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ml_training
    python3 generate_training_data.py
    cd ..
fi

# Check for LLM server
echo ""
echo "🤖 Checking for LLM server..."
if curl -s http://localhost:8001/v1/models > /dev/null 2>&1; then
    echo "✅ LLM server is running at http://localhost:8001"
else
    echo "⚠️  LLM server not detected at http://localhost:8001"
    echo ""
    echo "To run an LLM server, choose one option:"
    echo ""
    echo "Option 1 - Ollama (Easiest):"
    echo "  1. Install from https://ollama.ai"
    echo "  2. Run: ollama pull llama3.1:8b"
    echo "  3. Update .env: LLM_API_BASE=http://localhost:11434/v1"
    echo ""
    echo "Option 2 - llama.cpp:"
    echo "  1. Download llama.cpp from https://github.com/ggerganov/llama.cpp"
    echo "  2. Get a GGUF model"
    echo "  3. Run: ./server -m model.gguf --port 8001"
    echo ""
    echo "Option 3 - vLLM:"
    echo "  pip install vllm"
    echo "  vllm serve meta-llama/Meta-Llama-3.1-8B-Instruct --port 8001"
    echo ""
fi

# Start server
echo ""
echo "=========================================="
echo "✨ Setup complete!"
echo "=========================================="
echo ""
echo "🎯 To start the server, run:"
echo "   source venv/bin/activate"
echo "   python3 app.py"
echo ""
echo "   Or with uvicorn:"
echo "   uvicorn app:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📱 Access the app at: http://localhost:8000"
echo ""
echo "🔑 Default login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📚 For more details, see README_SETUP.md"
echo "=========================================="
echo ""

read -p "Would you like to start the server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting server..."
    python3 app.py
fi
