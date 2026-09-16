#!/usr/bin/env bash
# Board-side HTTP smoke test. GenieX must already expose /v1/chat/completions.
set -euo pipefail

API_URL="${GENIEX_URL:-http://127.0.0.1:18181}"
MODEL_ID="${GENIEX_MODEL_ID:-unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0}"
IMAGE="${1:-demo/test_image.jpg}"
QUESTION="${2:-Please describe the main content of the image and read visible text.}"

test -f "$IMAGE" || { echo "图片不存在: $IMAGE" >&2; exit 2; }
curl --fail-with-body --silent --show-error "$API_URL/v1/models"
echo

IMAGE_DATA="$(base64 -w 0 "$IMAGE")"
python3 - "$API_URL" "$MODEL_ID" "$QUESTION" "$IMAGE_DATA" <<'PY'
import json
import sys
import urllib.request

url, model, question, image_b64 = sys.argv[1:]
payload = {
    "model": model,
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}},
    ]}],
    "max_tokens": 32,
    "stream": False,
}
request = urllib.request.Request(
    url.rstrip("/") + "/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=300) as response:
    body = json.load(response)
print(json.dumps(body, ensure_ascii=False, indent=2))
PY
