#!/usr/bin/env bash
# setup_runpod_nomen.sh — Bootstrap a RunPod pod for Nomen QLoRA fine-tuning
#
# Recommended pod spec:
#   Image:  runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
#   GPU:    2 × H100 SXM5 80 GB   ($7.78/h community cloud)
#   Disk:   250 GB volume (Qwen 72B = ~140 GB fp16 + working space)
#
# Usage (run inside the pod after SSH/terminal):
#   bash setup_runpod_nomen.sh
#
# Environment variables (set before running or export in shell):
#   HF_TOKEN        — HuggingFace token (read access) for Qwen download
#   WANDB_API_KEY   — Weights & Biases API key for training metrics
#   REPO_URL        — Git repo URL (default: https://github.com/kfxtrading/BettingwithAI)
#   BRANCH          — Git branch to use (default: main)
#   BASE_MODEL      — HF model ID (default: Qwen/Qwen2.5-72B-Instruct)

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/kfxtrading/BettingwithAI}"
BRANCH="${BRANCH:-main}"
BASE_MODEL="${BASE_MODEL:-Qwen/Qwen2.5-72B-Instruct}"
WORKDIR="/workspace/BettingwithAI"

echo "════════════════════════════════════════════════════════════════"
echo "  Nomen QLoRA Training — RunPod Bootstrap"
echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
echo "  GPU count: $(nvidia-smi -L | wc -l)"
echo "  CUDA: $(nvcc --version 2>/dev/null | grep release | awk '{print $6}' | tr -d ,)"
echo "════════════════════════════════════════════════════════════════"

# ── 1. System packages ───────────────────────────────────────────────────────
echo "[1/7] Installing system packages..."
apt-get update -qq && apt-get install -y -qq git tmux htop nvtop aria2c pigz 2>/dev/null || true

# ── 2. Verify CUDA ───────────────────────────────────────────────────────────
echo "[2/7] Verifying CUDA + PyTorch..."
python3 -c "
import torch
assert torch.cuda.is_available(), 'CUDA not available — check pod image'
n = torch.cuda.device_count()
print(f'  ✓ PyTorch {torch.__version__}, {n} GPU(s)')
for i in range(n):
    props = torch.cuda.get_device_properties(i)
    vram = props.total_memory / 1024**3
    print(f'  GPU {i}: {props.name} ({vram:.0f} GB VRAM)')
assert n >= 1, 'Need ≥1 GPU'
"

# ── 3. Clone / update repo ───────────────────────────────────────────────────
echo "[3/7] Cloning repo..."
if [ -d "$WORKDIR/.git" ]; then
    echo "  Repo exists, pulling latest..."
    git -C "$WORKDIR" fetch origin && git -C "$WORKDIR" checkout "$BRANCH" && git -C "$WORKDIR" pull
else
    git clone --branch "$BRANCH" "$REPO_URL" "$WORKDIR"
fi
cd "$WORKDIR"

# ── 4. Install Python dependencies ──────────────────────────────────────────
echo "[4/7] Installing LLM fine-tuning dependencies..."

# Core training stack (pinned for reproducibility)
pip install -q --upgrade pip
pip install -q \
    "transformers>=4.45.0" \
    "trl>=0.11.0" \
    "peft>=0.13.0" \
    "bitsandbytes>=0.43.0" \
    "accelerate>=0.33.0" \
    "datasets>=2.20.0" \
    "safetensors>=0.4.3" \
    "sentencepiece" \
    "tokenizers>=0.19.0"

# Monitoring & logging
pip install -q "wandb>=0.17.0" "rich"

# llama.cpp Python bindings (for GGUF conversion on same pod)
pip install -q "llama-cpp-python" || echo "  llama-cpp-python optional, skipping"

# Install repo package
pip install -q -e ".[api]" --no-deps 2>/dev/null || pip install -q -e "." --no-deps

# ── 5. Configure HuggingFace token ──────────────────────────────────────────
echo "[5/7] Configuring HuggingFace..."
if [ -n "${HF_TOKEN:-}" ]; then
    python3 -c "from huggingface_hub import login; login('${HF_TOKEN}')"
    echo "  ✓ HF token set"
else
    echo "  WARNING: HF_TOKEN not set — Qwen download may fail if model is gated"
fi

# ── 6. Pre-download base model ───────────────────────────────────────────────
echo "[6/7] Pre-downloading base model: $BASE_MODEL (~140 GB, ~45 min)..."
echo "  This runs in background — check logs/model_download.log"
mkdir -p logs models/nomen_qlora_v1

python3 - <<'PYEOF' > logs/model_download.log 2>&1 &
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch, os

model_id = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-72B-Instruct")
cache_dir = "/workspace/model_cache"
os.makedirs(cache_dir, exist_ok=True)

print(f"Downloading tokenizer: {model_id}")
tok = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
print(f"Tokenizer done. Downloading model weights...")
# Download only — do not load into RAM yet
from huggingface_hub import snapshot_download
snapshot_download(repo_id=model_id, cache_dir=cache_dir,
                  ignore_patterns=["*.msgpack", "*.h5", "flax_model*"])
print("Download complete.")
PYEOF

DOWNLOAD_PID=$!
echo "  Download PID: $DOWNLOAD_PID (tail -f logs/model_download.log to monitor)"

# ── 7. Configure accelerate for multi-GPU ───────────────────────────────────
echo "[7/7] Configuring accelerate for multi-GPU training..."
cat > /workspace/accelerate_config.yaml <<'YAML'
compute_environment: LOCAL_MACHINE
debug: false
distributed_type: MULTI_GPU
downcast_bf16: 'no'
enable_cpu_affinity: false
gpu_ids: all
machine_rank: 0
main_training_function: main
mixed_precision: bf16
num_machines: 1
num_processes: 2
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false
YAML

if [ -n "${WANDB_API_KEY:-}" ]; then
    python3 -c "import wandb; wandb.login(key='${WANDB_API_KEY}')" 2>/dev/null && echo "  ✓ WandB authenticated"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Setup complete. Model download running in background."
echo ""
echo "  NEXT STEPS:"
echo "  1. Wait for model download:"
echo "     tail -f $WORKDIR/logs/model_download.log"
echo ""
echo "  2. Upload training dataset from your local machine:"
echo "     scp data/nomen_training/dataset_v1.jsonl root@<pod-ip>:/workspace/BettingwithAI/data/nomen_training/"
echo ""
echo "  3. Start training in a tmux session:"
echo "     tmux new -s train"
echo "     cd $WORKDIR"
echo "     accelerate launch --config_file /workspace/accelerate_config.yaml \\"
echo "       scripts/train_nomen_qlora.py \\"
echo "       --dataset data/nomen_training/dataset_v1.jsonl \\"
echo "       --output models/nomen_qlora_v1 \\"
echo "       --wandb-project nomen-training"
echo ""
echo "  4. After training, run GGUF export:"
echo "     bash scripts/export_nomen_gguf.sh"
echo ""
echo "  5. Download the GGUF + adapter to your local machine:"
echo "     scp root@<pod-ip>:/workspace/BettingwithAI/models/nomen-v1.Q4_K_M.gguf ./models/"
echo "     scp -r root@<pod-ip>:/workspace/BettingwithAI/models/nomen_qlora_v1/ ./models/"
echo ""
echo "  6. STOP THE POD to avoid ongoing charges:"
echo "     runpodctl stop pod <pod-id>"
echo "════════════════════════════════════════════════════════════════"
