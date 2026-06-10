#!/usr/bin/env bash
set -euo pipefail

: "${APP_URL:?Set APP_URL, e.g. https://catal.online/ai-interview-studio-2606}"
: "${API_URL:?Set API_URL, e.g. https://catal.online/ai-interview-gateway-2606}"
: "${LIVEKIT_URL:?Set LIVEKIT_URL, e.g. wss://catal.online/ai-interview-realtime-2606}"

LIVEKIT_HTTP_URL="${LIVEKIT_URL/wss:\/\//https://}"
LIVEKIT_HTTP_URL="${LIVEKIT_HTTP_URL/ws:\/\//http://}"

check() {
  local name="$1"
  local url="$2"
  echo "Checking ${name}: ${url}"
  curl -fsS --max-time 15 "${url}" >/tmp/interview-smoke-response.txt
  echo "OK ${name}"
}

check_status() {
  local name="$1"
  local url="$2"
  echo "Checking ${name}: ${url}"
  local code
  code="$(curl -ksS -o /dev/null -w "%{http_code}" --max-time 15 "${url}")"
  if [[ "${code}" =~ ^(200|204|301|302|404)$ ]]; then
    echo "OK ${name} status=${code}"
  else
    echo "FAIL ${name} status=${code}" >&2
    exit 1
  fi
}

check_status "frontend" "${APP_URL}/"
check "api health" "${API_URL}/health"
check "training options" "${API_URL}/training-options"
check "interview options" "${API_URL}/interview-options"
check "tts options" "${API_URL}/tts-options"
check_status "livekit https endpoint" "${LIVEKIT_HTTP_URL}/"

echo "Smoke test passed"
