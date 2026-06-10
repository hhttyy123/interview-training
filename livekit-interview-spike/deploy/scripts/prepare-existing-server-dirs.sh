#!/usr/bin/env bash
set -euo pipefail

# Run from your existing server root directory:
# docker-compose.yml / nginx / my_blog / mysql_data / chem_project / ai_chem

ROOT_DIR="${1:-$(pwd)}"

mkdir -p "${ROOT_DIR}/ai_interview/livekit"
mkdir -p "${ROOT_DIR}/ai_interview/models/bge-m3"
mkdir -p "${ROOT_DIR}/ai_interview/data/qdrant"
mkdir -p "${ROOT_DIR}/ai_interview/data/tei"

echo "Prepared:"
echo "${ROOT_DIR}/ai_interview/livekit"
echo "${ROOT_DIR}/ai_interview/models/bge-m3"
echo "${ROOT_DIR}/ai_interview/data/qdrant"
echo "${ROOT_DIR}/ai_interview/data/tei"
