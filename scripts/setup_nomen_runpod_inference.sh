#!/usr/bin/env bash
# setup_nomen_runpod_inference.sh — Launch a RunPod vLLM inference pod for Nomen
#
# Serves the fine-tuned Nomen Q8_0 GGUF via vLLM's OpenAI-compatible API.
# The production match_analyst.py reads NOMEN_VLLM_URL and routes to this endpoint.
#
# Recommended pod spec:
#   Image:  runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
#   GPU:    1 × A100 SXM 80 GB  ($1.64/h community cloud)
#   Disk:   120 GB (Q8_0 GGUF = ~74 GB)
#   Ports:  8080/http (public)
#
# Environment variables:
#   GGUF_PATH  — path to the Q8_0 GGUF file (default: /workspace/nomen-v1.Q8_0.gguf)
#   HF_MODEL   — base model ID for vLLM config (default: Qwen/Qwen2.5-72B-Instruct)

set -euo pipefail

GGUF_PATH="${GGUF_PATH:-/workspace/nomen-v1.Q8_0.gguf}"
HF_MODEL="${HF_MODEL:-Qwen/Qwen2.5-72B-Instruct}"
PORT=8080

echo "════════════════════════════════════════════════════════════════"
echo "  Nomen vLLM Inference Pod"
echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "  GGUF: $GGUF_PATH"
echo "════════════════════════════════════════════════════════════════"

# ── Verify GGUF exists ───────────────────────────────────────────────────────
if [ ! -f "$GGUF_PATH" ]; then
    echo ""
    echo "ERROR: GGUF not found at $GGUF_PATH"
    echo ""
    echo "Upload the GGUF first:"
    echo "  scp ./models/nomen-v1.Q8_0.gguf root@<pod-ip>:/workspace/"
    exit 1
fi

echo "GGUF size: $(du -h "$GGUF_PATH" | cut -f1)"

# ── Install vLLM ────────────────────────────────────────────────────────────
echo "Installing vLLM..."
pip install -q "vllm>=0.6.0" "fastapi" "uvicorn" "huggingface_hub"

# ── Health check script ──────────────────────────────────────────────────────
cat > /workspace/health_check.sh <<'HCEOF'
#!/bin/bash
resp=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null)
if [ "$resp" = "200" ]; then
    echo "✓ Nomen vLLM is healthy"
else
    echo "✗ vLLM not ready (HTTP $resp)"
fi
HCEOF
chmod +x /workspace/health_check.sh

# ── Test prompt ──────────────────────────────────────────────────────────────
cat > /workspace/test_nomen.py <<'PYEOF'
"""Quick smoke test for the Nomen vLLM inference endpoint."""
import json, urllib.request, urllib.error

url = "http://localhost:8080/v1/chat/completions"
payload = {
    "model": "nomen-v1",
    "messages": [
        {"role": "system", "content": "You are Nomen, the football prediction AI."},
        {"role": "user", "content": json.dumps({
            "home_team": "Arsenal", "away_team": "Chelsea",
            "prob_home_pct": 54, "prob_draw_pct": 26, "prob_away_pct": 20,
            "recent_form_home": "WWDLW", "recent_form_away": "DWWLD",
            "value_bet_signal": "YES"
        })},
    ],
    "max_tokens": 400,
    "temperature": 0.65,
}
req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    article = data["choices"][0]["message"]["content"]
    print("✓ Nomen response:")
    print(article)
except Exception as e:
    print(f"✗ Test failed: {e}")
PYEOF

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Starting vLLM server..."
echo "  The server will be available at:"
echo "  https://<pod-id>-${PORT}.proxy.runpod.net"
echo ""
echo "  Set in Railway:"
echo "  NOMEN_VLLM_URL=https://<pod-id>-${PORT}.proxy.runpod.net/v1"
echo "════════════════════════════════════════════════════════════════"

# Launch vLLM (foreground — run in tmux: tmux new -s nomen)
python3 -m vllm.entrypoints.openai.api_server \
    --model "$HF_MODEL" \
    --tokenizer "$HF_MODEL" \
    --load-format gguf \
    --gguf-path "$GGUF_PATH" \
    --served-model-name "nomen-v1" \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.95 \
    --max-num-seqs 32 \
    --dtype bfloat16 \
    --host 0.0.0.0 \
    --port "$PORT" \
    --api-key "${VLLM_API_KEY:-nomen}"
