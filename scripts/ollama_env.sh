#!/usr/bin/env bash
set -euo pipefail

# Sets up PATH for lab install and checks Ollama server health.

export PATH="$PATH:$HOME/opt/ollama/bin"

echo "==> ollama binary:"
if command -v ollama >/dev/null 2>&1; then
  echo "  $(command -v ollama)"
else
  echo "  NOT FOUND (did you run scripts/lab_install_ollama.sh ?)"
  exit 1
fi

echo
echo "==> ollama version:"
ollama -v

echo
echo "==> server health:"
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "  ✅ Ollama server reachable at http://localhost:11434"
else
  echo "  ❌ Ollama server not reachable."
  echo "     Start it with: nohup ollama serve > ~/ollama_serve.log 2>&1 &"
fi

echo
echo "==> available models (ollama list):"
ollama list || true