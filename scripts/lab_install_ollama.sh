#!/usr/bin/env bash
set -euo pipefail

# Versioned Ollama install for lab machines.
#
# Installs into:
#   ~/opt/ollama-vX.Y.Z
# Updates symlink:
#   ~/opt/ollama -> ~/opt/ollama-vX.Y.Z
#
# Downloads cached in:
#   ~/src/ollama

VERSION="${1:-0.17.6}"    # usage: ./lab_install_ollama.sh 0.17.6
TAG="v${VERSION}"

BASE_OPT_DIR="$HOME/opt"
INSTALL_DIR="$BASE_OPT_DIR/ollama-${TAG}"
SYMLINK_DIR="$BASE_OPT_DIR/ollama"

SRC_DIR="$HOME/src/ollama"
mkdir -p "$SRC_DIR" "$INSTALL_DIR"
cd "$SRC_DIR"

AMD64_URL="https://github.com/ollama/ollama/releases/download/${TAG}/ollama-linux-amd64.tar.zst"
ROCM_URL="https://github.com/ollama/ollama/releases/download/${TAG}/ollama-linux-amd64-rocm.tar.zst"

AMD64_TARBALL="ollama-linux-amd64.${TAG}.tar.zst"
ROCM_TARBALL="ollama-linux-amd64-rocm.${TAG}.tar.zst"

echo "==> Installing Ollama ${TAG}"
echo "==> Downloading tarballs into: $SRC_DIR"

curl -fL --retry 5 --retry-delay 2 -o "$AMD64_TARBALL" "$AMD64_URL"
curl -fL --retry 5 --retry-delay 2 -o "$ROCM_TARBALL" "$ROCM_URL"

echo
echo "==> Downloaded files:"
ls -lh "$AMD64_TARBALL" "$ROCM_TARBALL"

echo
echo "==> Extracting into: $INSTALL_DIR"
if tar --help 2>/dev/null | grep -q -- '--zstd'; then
  tar --zstd -C "$INSTALL_DIR" -xf "$AMD64_TARBALL"
  tar --zstd -C "$INSTALL_DIR" -xf "$ROCM_TARBALL"
else
  if ! command -v zstd >/dev/null 2>&1; then
    echo "ERROR: tar has no --zstd support and 'zstd' is not installed."
    echo "Ask CS support to install zstd, or use a machine where it exists."
    exit 1
  fi
  zstd -d -c "$AMD64_TARBALL" | tar -C "$INSTALL_DIR" -xf -
  zstd -d -c "$ROCM_TARBALL"  | tar -C "$INSTALL_DIR" -xf -
fi

echo
echo "==> Pointing symlink: $SYMLINK_DIR -> $INSTALL_DIR"
# If ~/opt/ollama exists as a real directory (not a symlink), move it aside
if [ -e "$SYMLINK_DIR" ] && [ ! -L "$SYMLINK_DIR" ]; then
  backup="$BASE_OPT_DIR/ollama-old-$(date +%Y%m%d-%H%M%S)"
  echo "==> Detected existing directory at $SYMLINK_DIR; moving to $backup"
  mv "$SYMLINK_DIR" "$backup"
fi

ln -sfn "$INSTALL_DIR" "$SYMLINK_DIR"

echo
echo "==> Done."
echo "Next steps:"
echo "  1) export PATH=\"$HOME/opt/ollama/bin:\$PATH\""
echo "  2) hash -r"
echo "  3) ollama -v"
echo "  4) restart the server (see instructions below)"