#!/usr/bin/env bash
# Start the host-side FastAPI and Streamlit services.
# The model backend must already be running, locally or on the board.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR/stage3_multimodal"

export LLAMA_BASE_URL="${LLAMA_BASE_URL:-http://127.0.0.1:8080}"
export LLAMA_MODEL="${LLAMA_MODEL:-Qwen3.5-0.8B-Q4_K_M.gguf}"
export API_URL="${API_URL:-http://127.0.0.1:9000}"

python -m uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-9000}" &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM

python -m streamlit run streamlit_app.py \
  --server.address="${UI_HOST:-0.0.0.0}" \
  --server.port="${UI_PORT:-8501}" \
  --server.headless=true
