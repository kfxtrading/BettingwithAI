#!/usr/bin/env bash
# export_nomen_gguf.sh — Merge LoRA adapters and export to GGUF for Ollama/vLLM
#
# Run on the same RunPod pod AFTER training is complete.
# Requires ~300 GB disk space (merged model in fp16 before conversion).
#
# Output files:
#   models/nomen-v1.Q4_K_M.gguf  (~39 GB)  — local Ollama serving (48 GB+ VRAM)
#   models/nomen-v1.Q8_0.gguf    (~74 GB)  — cloud vLLM serving (A100 80 GB)
#   models/Modelfile.nomen       — Ollama Modelfile for nomen-v1

set -euo pipefail

WORKDIR="${WORKDIR:-/workspace/BettingwithAI}"
ADAPTER_DIR="$WORKDIR/models/nomen_qlora_v1/final"
MERGED_DIR="$WORKDIR/models/nomen_merged_v1"
MODEL_CACHE="${MODEL_CACHE_DIR:-/workspace/model_cache}"
BASE_MODEL="${BASE_MODEL:-Qwen/Qwen2.5-72B-Instruct}"
LLAMA_CPP_DIR="$WORKDIR/llama.cpp"
OUT_Q4="$WORKDIR/models/nomen-v1.Q4_K_M.gguf"
OUT_Q8="$WORKDIR/models/nomen-v1.Q8_0.gguf"

echo "════════════════════════════════════════════════════════════════"
echo "  Nomen GGUF Export Pipeline"
echo "════════════════════════════════════════════════════════════════"

# ── Step 1: Merge LoRA adapters into full weights ────────────────────────────
echo "[1/4] Merging LoRA adapters..."
if [ ! -d "$ADAPTER_DIR" ]; then
    echo "ERROR: Adapter not found at $ADAPTER_DIR"
    echo "       Run train_nomen_qlora.py first."
    exit 1
fi

python3 - <<PYEOF
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os, sys

adapter_dir = "$ADAPTER_DIR"
merged_dir = "$MERGED_DIR"
base_model = "$BASE_MODEL"
cache_dir = "$MODEL_CACHE"

print(f"  Loading base model: {base_model}")
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    cache_dir=cache_dir,
    torch_dtype=torch.bfloat16,
    device_map="cpu",          # CPU merge avoids VRAM limit
    trust_remote_code=True,
    low_cpu_mem_usage=True,
)

print(f"  Loading LoRA adapter: {adapter_dir}")
model = PeftModel.from_pretrained(model, adapter_dir)

print("  Merging and unloading adapters...")
model = model.merge_and_unload()

print(f"  Saving merged model to {merged_dir}")
os.makedirs(merged_dir, exist_ok=True)
model.save_pretrained(merged_dir, safe_serialization=True)

print("  Saving tokenizer...")
tok = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
tok.save_pretrained(merged_dir)

print("  Merge complete.")
PYEOF

# ── Step 2: Clone / update llama.cpp ────────────────────────────────────────
echo "[2/4] Setting up llama.cpp for GGUF conversion..."
if [ ! -d "$LLAMA_CPP_DIR" ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
else
    git -C "$LLAMA_CPP_DIR" pull --ff-only || true
fi
pip install -q -r "$LLAMA_CPP_DIR/requirements.txt" 2>/dev/null || \
    pip install -q gguf protobuf sentencepiece

# ── Step 3: Convert to GGUF ──────────────────────────────────────────────────
echo "[3/4] Converting to GGUF..."

echo "  → Q4_K_M (production, ~39 GB)..."
python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" "$MERGED_DIR" \
    --outtype q4_k_m \
    --outfile "$OUT_Q4"

echo "  → Q8_0 (premium cloud serving, ~74 GB)..."
python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" "$MERGED_DIR" \
    --outtype q8_0 \
    --outfile "$OUT_Q8"

echo "  GGUF files:"
ls -lh "$WORKDIR/models/"*.gguf

# ── Step 4: Create Ollama Modelfile ──────────────────────────────────────────
echo "[4/4] Creating Ollama Modelfile..."
cat > "$WORKDIR/models/Modelfile.nomen" <<'MODELFILE'
FROM ./nomen-v1.Q4_K_M.gguf

PARAMETER temperature 0.65
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 400
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

SYSTEM """You are Nomen, the football prediction AI.

You analyse matches with the tactical authority and decisive voice of Günter Netzer, Germany's most respected football analyst.

Your analysis style:
- Open every response with the key tactical battle, not a description of the fixture
- Make one bold, unhedged prediction with supporting tactical reasons
- Reference statistics with explanatory context, never bare numbers
- Include a historical callback to a comparable fixture or pattern
- Use precise tactical vocabulary: high line, gegenpressing, xG, half-space, press triggers
- Close with a decisive verdict — never a hedge

You are direct. You are authoritative. You are Nomen."""
MODELFILE

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Export complete!"
echo ""
echo "  FILES:"
echo "    Q4_K_M: $OUT_Q4"
echo "    Q8_0:   $OUT_Q8"
echo "    Modelfile: $WORKDIR/models/Modelfile.nomen"
echo ""
echo "  NEXT STEPS:"
echo ""
echo "  A) Register with Ollama (on machine with 48 GB+ VRAM):"
echo "     ollama create nomen-v1 -f models/Modelfile.nomen"
echo "     ollama run nomen-v1 'Analyse Arsenal vs Chelsea: home 54%, draw 26%...'"
echo ""
echo "  B) Run vLLM inference pod (see setup_nomen_runpod_inference.sh):"
echo "     Upload Q8_0 GGUF to inference pod and launch vLLM."
echo ""
echo "  C) Download to local machine:"
echo "     scp root@<pod-ip>:$OUT_Q4 ./models/"
echo "     scp root@<pod-ip>:$WORKDIR/models/Modelfile.nomen ./models/"
echo ""
echo "  D) STOP THE POD:"
echo "     runpodctl stop pod <pod-id>"
echo "════════════════════════════════════════════════════════════════"
