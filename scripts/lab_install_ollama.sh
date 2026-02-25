#!/usr/bin/env bash
set -euo pipefail

# Installs Ollama (and ROCm libs) into:
#   ~/opt/ollama
# Downloads go to:
#   ~/src

OLLAMA_DIR="$HOME/opt/ollama"
SRC_DIR="$HOME/src"

mkdir -p "$SRC_DIR" "$OLLAMA_DIR"
cd "$SRC_DIR"

echo "==> Downloading Ollama packages (.tar.zst)..."
curl -fL --retry 5 --retry-delay 2 \
  -o ollama-linux-amd64.tar.zst \
  https://ollama.com/download/ollama-linux-amd64.tar.zst

curl -fL --retry 5 --retry-delay 2 \
  -o ollama-linux-amd64-rocm.tar.zst \
  https://ollama.com/download/ollama-linux-amd64-rocm.tar.zst

echo
echo "==> Downloaded files:"
ls -lh ollama-linux-amd64.tar.zst ollama-linux-amd64-rocm.tar.zst

echo
echo "==> Extracting to $OLLAMA_DIR ..."
if tar --help 2>/dev/null | grep -q -- '--zstd'; then
  tar --zstd -C "$OLLAMA_DIR" -xf ollama-linux-amd64.tar.zst
  tar --zstd -C "$OLLAMA_DIR" -xf ollama-linux-amd64-rocm.tar.zst
else
  if ! command -v zstd >/dev/null 2>&1; then
    echo "ERROR: tar has no --zstd support and 'zstd' is not installed."
    echo "Ask CS support to install zstd or use a machine where it exists."
    exit 1
  fi
  zstd -d -c ollama-linux-amd64.tar.zst | tar -C "$OLLAMA_DIR" -xf -
  zstd -d -c ollama-linux-amd64-rocm.tar.zst | tar -C "$OLLAMA_DIR" -xf -
fi

echo
echo "==> Installation complete."
echo "To use Ollama in your current shell:"
echo '  export PATH="$PATH:$HOME/opt/ollama/bin"'
echo
echo "To start the server in the background:"
echo '  nohup ollama serve > ~/ollama_serve.log 2>&1 &'
echo
echo "Verify:"
echo '  ollama -v'
echo '  curl -s http://localhost:11434/api/tags | head'