#!/usr/bin/env bash
set -euo pipefail

# Run this from the existing server root directory, the one containing:
# docker-compose.yml / nginx / my_blog / mysql_data / chem_project / ai_chem

ROOT_DIR="${1:-$(pwd)}"
cd "${ROOT_DIR}"

docker compose --env-file .env.production -f docker-compose.yml pull \
  ai-interview-web \
  ai-interview-token-api \
  ai-interview-agent \
  ai-interview-livekit

docker compose --env-file .env.production -f docker-compose.yml up -d \
  ai-interview-web \
  ai-interview-token-api \
  ai-interview-agent \
  ai-interview-livekit \
  nginx

docker compose --env-file .env.production -f docker-compose.yml ps
