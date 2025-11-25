#!/usr/bin/env bash

# Convenience script to launch Ollama (if not already running) and the FastAPI backend.
# After this starts, open frontend/index.html in your browser to use the app.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
OLLAMA_LOG="$ROOT_DIR/ollama.log"

echo "-> Ensuring Ollama server is running..."
if pgrep -x "ollama" >/dev/null 2>&1; then
  echo "   Ollama already running."
else
  echo "   Starting Ollama in the background (logs: $OLLAMA_LOG)"
  (ollama serve >>"$OLLAMA_LOG" 2>&1 &)
  sleep 2
fi

echo "-> Checking Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
  echo "   Virtual env not found at $VENV_DIR"
  echo "   Run 'python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install -r backend/requirements.txt'"
  exit 1
fi

echo "-> Starting FastAPI backend..."
source "$VENV_DIR/bin/activate"
cd "$BACKEND_DIR"
export APP_HOST="${APP_HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
echo "   Uvicorn available at http://$APP_HOST:$PORT"
uvicorn app:app --host "$APP_HOST" --port "$PORT"

