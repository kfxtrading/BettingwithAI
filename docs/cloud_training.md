# Cloud GPU Training on Vast.ai

End-to-end recipe to fine-tune the two-head support classifier
(`xlm-roberta-base` + chapter/intent heads, SupCon loss,
`cw=0.3`, `gate=0.7`) on all 5 languages using a rented CUDA GPU.

Expected wall-time on an RTX 4090: **≈ 2–3 h for 5 langs × 7 epochs**,
VRAM footprint `~14 GB`.

---

## 0. Dataset status

- Dataset file: `data/support_faq/dataset_augmented_v3.jsonl`
- Rows: `82 806` (269 intents × 5 langs, de/en/es/fr/it, seed = 42)
- Size: `~41 MB` (uncompressed JSONL)
- SHA256: `6211d5265e2eba002ff582d87b2b0cd53976869a14ac227eda2d37e2488b9021`
- The file is **gitignored** and must be uploaded separately (see §2).

To rebuild the checksum locally:

```powershell
Get-FileHash data/support_faq/dataset_augmented_v3.jsonl -Algorithm SHA256
```

---

## 1. Rent a Vast.ai instance

Recommended search filters:

| Filter          | Value                                                  |
|-----------------|--------------------------------------------------------|
| GPU             | `RTX 4090` (or RTX 3090 — both 24 GB)                  |
| GPU count       | `1`                                                    |
| Image (template)| `pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime`        |
| Disk            | `≥ 40 GB`                                              |
| Internet down   | `≥ 200 Mbit/s` (for HF backbone download)              |
| Reliability     | `≥ 98 %`                                               |

Expected price: **≈ USD 0.35 – 0.60 / h** → a full run costs **≈ USD 1 – 2**.

After renting, vast.ai shows an SSH command of the form

```bash
ssh -p <PORT> root@<HOST>
```

Also note the matching SCP syntax: `scp -P <PORT> ...`.

---

## 2. Upload the dataset

On your local Windows box:

```powershell
# build the minimal tarball + SHA256 manifest
pwsh ./scripts/pack_cloud_dataset.ps1

# upload it
scp -P <PORT> build/cloud/support_dataset_v3.tar.gz `
              build/cloud/SHA256SUMS.txt `
              root@<HOST>:/workspace/
```

---

## 3. Bootstrap the instance

Inside the container (`ssh -p <PORT> root@<HOST>`):

```bash
cd /workspace
# clone + install deps + CUDA check + pre-cache backbone
curl -fsSL https://raw.githubusercontent.com/Cingolainie/BettingwithAI/main/scripts/setup_vastai.sh \
  | bash

# unpack and verify the dataset
cd /workspace/BettingwithAI
tar -xzf /workspace/support_dataset_v3.tar.gz
cp /workspace/SHA256SUMS.txt .
sha256sum -c SHA256SUMS.txt
# → data/support_faq/dataset_augmented_v3.jsonl: OK
# → data/support_faq/intents.json: OK
```

If `setup_vastai.sh` is not reachable (branch differs), clone manually:

```bash
git clone --depth 1 https://github.com/Cingolainie/BettingwithAI.git /workspace/BettingwithAI
cd /workspace/BettingwithAI
bash scripts/setup_vastai.sh
```

---

## 4. Run training

Use `tmux` so the job survives SSH disconnects:

```bash
cd /workspace/BettingwithAI
mkdir -p logs
tmux new -s train

# 5 languages × 7 epochs, calibrated, default cw=0.3 / gate=0.7
fb train-support-twohead --lang all --epochs 7 2>&1 \
  | tee logs/train_$(date +%Y%m%d_%H%M).log

# Ctrl+b d   — detach and let it run
# tmux attach -t train   — re-attach later
```

Per-language smoke test first (recommended — 1 epoch, ~8 min):

```bash
fb train-support-twohead --lang de --epochs 1 --max-rows-per-intent 20
```

---

## 5. Download the trained models

After training finishes, from your Windows box:

```powershell
scp -P <PORT> -r root@<HOST>:/workspace/BettingwithAI/models/support ./models/
```

The `models/support/` directory will contain per-language artefacts:

```
twohead_<lang>.safetensors        # encoder + heads
twohead_<lang>.meta.json          # intent ↔ chapter map, HP record, metrics
twohead_<lang>.calibrator.joblib  # temperature scaler
```

---

## 6. Destroy the instance

Don't forget — idle instances keep billing.
Go to **Vast.ai → Instances → Destroy**.

---

## Troubleshooting

| Symptom                                    | Fix                                                              |
|--------------------------------------------|------------------------------------------------------------------|
| `CUDA not available`                       | Wrong template image → use a `*-cuda12.1-*` PyTorch image.       |
| `bf16: False`                              | Old GPU (e.g. T4). Training still works in fp32, ~1.7× slower.   |
| `torch_directml` import errors             | Should never happen on CUDA host — we don't install it.          |
| `transformers` `sdpa_mask` shape error     | Pin `transformers<4.50`; already pinned in `requirements-cuda.txt`.|
| Disk full during HF download               | Delete `~/.cache/huggingface/hub/models--*` or resize disk.      |
