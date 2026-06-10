#!/usr/bin/env bash
set -euo pipefail

: "${ACR_REGISTRY:?Set ACR_REGISTRY, e.g. crpi-xxx.cn-shanghai.personal.cr.aliyuncs.com}"
: "${ACR_NAMESPACE:?Set ACR_NAMESPACE, e.g. your_namespace}"
: "${IMAGE_VERSION:?Set IMAGE_VERSION, e.g. v1}"
: "${VITE_API_BASE_URL:?Set VITE_API_BASE_URL, e.g. https://catal.online/ai-interview-gateway-2606}"
: "${VITE_BASE_PATH:=/}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WEB_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/interview-web:${IMAGE_VERSION}"
SERVER_IMAGE="${ACR_REGISTRY}/${ACR_NAMESPACE}/interview-server:${IMAGE_VERSION}"

cd "${ROOT_DIR}"

echo "Building ${WEB_IMAGE}"
docker build \
  -f deploy/Dockerfile.web \
  --build-arg VITE_API_BASE_URL="${VITE_API_BASE_URL}" \
  --build-arg VITE_BASE_PATH="${VITE_BASE_PATH}" \
  -t "${WEB_IMAGE}" \
  .

echo "Building ${SERVER_IMAGE}"
docker build \
  -f deploy/Dockerfile.server \
  -t "${SERVER_IMAGE}" \
  .

echo "Pushing images"
docker push "${WEB_IMAGE}"
docker push "${SERVER_IMAGE}"

echo "Done"
echo "WEB_IMAGE=${WEB_IMAGE}"
echo "SERVER_IMAGE=${SERVER_IMAGE}"
