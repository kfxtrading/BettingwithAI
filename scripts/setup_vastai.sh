#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_vastai.sh — bootstrap a Vast.ai CUDA instance for support-classifier
#                   training (two-head transformer, 5 languages).
#
# Image recommendation:  pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime
# GPU recommendation:    RTX 4090 24 GB (or RTX 3090 24 GB)
# Disk:                  ≥ 40 GB  (HF cache + 5 × ~1.2 GB model output)
#
# Usage (inside the rented container, as root):
#   bash setup_vastai.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Cingolainie/BettingwithAI.git}"
REPO_DIR="${REPO_DIR:-/workspace/BettingwithAI}"
BRANCH="${BRANCH:-main}"

echo "==> apt packages"
apt-get update -qq
apt-get install -y --no-install-recommends git git-lfs tmux htop nvtop ca-certificates >/dev/null
git lfs install --skip-repo

echo "==> clone repo  ($REPO_URL @ $BRANCH)"
if [[ ! -d "$REPO_DIR/.git" ]]; then
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"

echo "==> python / pip sanity"
python -V
pip install --upgrade pip wheel setuptools

echo "==> install torch (CUDA 12.1 wheels)"
pip install --index-url https://download.pytorch.org/whl/cu121 "torch==2.4.1"

echo "==> install training deps"
pip install -r requirements-cuda.txt
pip install -e . --no-deps

echo "==> sanity check — CUDA visible?"
python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA not available — wrong image or no GPU attached"
print("CUDA ok  |  device:", torch.cuda.get_device_name(0),
      " |  capability:", torch.cuda.get_device_capability(0),
      " |  bf16:", torch.cuda.is_bf16_supported())
PY

echo "==> pre-download HF backbone (xlm-roberta-base, ~1.1 GB)"
python - <<'PY'
from transformers import AutoTokenizer, AutoModel
AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")
AutoModel.from_pretrained("FacebookAI/xlm-roberta-base")
print("backbone cached")
PY

mkdir -p data/support_faq models/support

cat <<'EOF'

─────────────────────────────────────────────────────────────────────────────
 Setup done.

 NEXT STEPS (from your local Windows box):

   # 1) upload dataset (from repo root on Windows)
   scp data/support_faq/dataset_augmented_v3.jsonl \
       data/support_faq/intents.json \
       root@<vast-host>:<port>:/workspace/BettingwithAI/data/support_faq/

   # 2) verify checksum on the VM
   sha256sum data/support_faq/dataset_augmented_v3.jsonl
   # expected:
   # 6211d5265e2eba002ff582d87b2b0cd53976869a14ac227eda2d37e2488b9021

   # 3) start training in tmux (so it survives ssh drops)
   tmux new -s train
   fb train-support-twohead --lang all --epochs 7 2>&1 | tee logs/train_$(date +%Y%m%d_%H%M).log
   # detach: Ctrl+b d   |   reattach: tmux attach -t train

   # 4) after training completes, download models back to Windows
   scp -r root@<vast-host>:<port>:/workspace/BettingwithAI/models/support \
       ./models/
─────────────────────────────────────────────────────────────────────────────
EOF
