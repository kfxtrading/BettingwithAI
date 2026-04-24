#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_runpod.sh — bootstrap a RunPod CUDA pod for support-classifier
#                   training (two-head transformer, 5 languages).
#
# Recommended pod template:
#   runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04
#
# Recommended GPU (budget €15 ≈ $16):
#   Community RTX 4090 24 GB       ~$0.22/h   →  ~3 h total  ≈  $0.70
#   Community A100 40GB            ~$0.49/h   →  ~2 h total  ≈  $1.00
#   Secure    A100 40GB            ~$1.19/h   →  ~2 h total  ≈  $2.40  (safest)
#
# Disk:  Container 30 GB + optional Volume 20 GB (persistent / $0.10 GB-month)
#
# Usage inside the pod (Web-Terminal or SSH):
#   bash <(curl -sSL https://raw.githubusercontent.com/kfxtrading/BettingwithAI/main/scripts/setup_runpod.sh)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/kfxtrading/BettingwithAI.git}"
REPO_DIR="${REPO_DIR:-/workspace/BettingwithAI}"
BRANCH="${BRANCH:-main}"

echo "==> apt packages"
apt-get update -qq
apt-get install -y --no-install-recommends git git-lfs tmux htop ca-certificates rsync >/dev/null
git lfs install --skip-repo || true

echo "==> clone repo  ($REPO_URL @ $BRANCH)"
if [[ ! -d "$REPO_DIR/.git" ]]; then
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi
cd "$REPO_DIR"

echo "==> python / pip sanity"
python -V
pip install --upgrade pip wheel setuptools

# RunPod pytorch template already has torch+cuda12.4 pre-installed; only install
# if missing or wrong major version.
echo "==> torch check"
python - <<'PY' || MUST_INSTALL_TORCH=1
import torch, sys
assert torch.cuda.is_available(), "no CUDA"
print(f"torch {torch.__version__}  cuda {torch.version.cuda}  gpu {torch.cuda.get_device_name(0)}")
PY
if [[ "${MUST_INSTALL_TORCH:-0}" == "1" ]]; then
    echo "==> installing torch (CUDA 12.1 wheels)"
    pip install --index-url https://download.pytorch.org/whl/cu121 "torch==2.4.1"
fi

echo "==> install training deps"
pip install -r requirements-cuda.txt
pip install -e . --no-deps

echo "==> sanity check — CUDA visible?"
python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA not available — wrong image or no GPU attached"
print("CUDA ok  |  device:", torch.cuda.get_device_name(0),
      " |  capability:", torch.cuda.get_device_capability(0),
      " |  bf16:", torch.cuda.is_bf16_supported(),
      " |  VRAM:", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1), "GB")
PY

echo "==> pre-download HF backbone (xlm-roberta-base, ~1.1 GB)"
python - <<'PY'
from transformers import AutoTokenizer, AutoModel
AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")
AutoModel.from_pretrained("FacebookAI/xlm-roberta-base")
print("backbone cached")
PY

mkdir -p data/support_faq models/support logs

cat <<'EOF'

─────────────────────────────────────────────────────────────────────────────
 Setup done.

 NEXT STEPS:

   # 1) upload dataset (from Windows repo root — replace <ip> and <port>)
   scp -P <port> -i ~/.ssh/id_ed25519 \
       data/support_faq/dataset_augmented_v3.jsonl \
       data/support_faq/intents.json \
       root@<pod-ip>:/workspace/BettingwithAI/data/support_faq/

   # 2) verify checksum on the pod
   sha256sum data/support_faq/dataset_augmented_v3.jsonl
   # expected:
   # 6211d5265e2eba002ff582d87b2b0cd53976869a14ac227eda2d37e2488b9021

   # 3) start training in tmux (survives SSH drops)
   tmux new -s train
   fb train-support-twohead --lang all --epochs 7 2>&1 \
       | tee logs/train_$(date +%Y%m%d_%H%M).log
   # detach: Ctrl+b d    reattach: tmux attach -t train

   # 4) download artefacts back to Windows
   scp -P <port> -i ~/.ssh/id_ed25519 -r \
       root@<pod-ip>:/workspace/BettingwithAI/models/support \
       ./models/

   # 5) STOP the pod (Console → Stop)  OR  via CLI on the pod itself:
   runpodctl stop pod $RUNPOD_POD_ID
   # (RUNPOD_POD_ID is auto-set inside every pod)
─────────────────────────────────────────────────────────────────────────────
EOF
