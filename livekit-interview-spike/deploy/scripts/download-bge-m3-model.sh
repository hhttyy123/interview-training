#!/usr/bin/env bash
set -euo pipefail

# Run from your existing server root directory, or pass it as the first arg.
# It downloads BAAI/bge-m3 into ./ai_interview/models/bge-m3.

ROOT_DIR="${1:-$(pwd)}"
MODEL_DIR="${ROOT_DIR}/ai_interview/models/bge-m3"
VENV_DIR="${ROOT_DIR}/ai_interview/.modelscope-venv"

mkdir -p "${MODEL_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install it first: sudo apt update && sudo apt install -y python3 python3-venv" >&2
  exit 1
fi

python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install "modelscope>=1.20,<2.0"

"${VENV_DIR}/bin/modelscope" download \
  --model BAAI/bge-m3 \
  --local_dir "${MODEL_DIR}"

test -f "${MODEL_DIR}/config.json"
test -f "${MODEL_DIR}/tokenizer.json"

echo "BGE-M3 model is ready at ${MODEL_DIR}"
