# RunPod Training Guide — €15 Budget

Complete recipe for running the 5-language two-head support classifier
fine-tune on RunPod with a €15 (~$16) credit budget.

---

## 1. Choose a pod

**Recommendation for your budget:**

| Variant | GPU | $/h | Runtime | Total cost | Interrupt risk |
|---|---|---|---|---|---|
| 💚 **Best value** | Community RTX 4090 24GB | ~$0.22 | ~3 h | ~$0.70 | Rare |
| 🚀 **Best speed** | Community A100 40GB | ~$0.49 | ~2 h | ~$1.00 | Rare |
| 🛡️ **Safest** | Secure A100 40GB | ~$1.19 | ~2 h | ~$2.40 | None |

With €15 you can comfortably run **3–4 full training attempts** on Secure-Cloud,
or **many iterations** on Community. Recommended: **Community RTX 4090** —
plenty for `xlm-roberta-base` and cheap enough to re-run if something fails.

### Pod configuration

1. https://www.runpod.io/console/pods → **+ Deploy**
2. **GPU:** RTX 4090 (or A100 40GB)
3. **Template:** `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
4. **Container Disk:** 30 GB
5. **Volume:** 20 GB mounted at `/workspace` (persistent, survives pod restart, $0.10/GB/month)
6. **Expose:** HTTP 8888 (Jupyter) + TCP 22 (SSH) — both default on
7. **Environment:** leave default
8. Click **Deploy** → wait ~30 sec

## 2. Connect (SSH recommended)

Add your public key in Console → Settings → SSH Public Keys, then:

```powershell
# From Windows PowerShell
ssh root@<pod-ip> -p <port> -i $HOME\.ssh\id_ed25519
```

(IP/port shown on pod detail page, e.g. `ssh root@213.173.105.xxx -p 15432`)

## 3. Bootstrap environment

On the pod:

```bash
cd /workspace
bash <(curl -sSL https://raw.githubusercontent.com/kfxtrading/BettingwithAI/main/scripts/setup_runpod.sh)
```

This clones the repo, installs `requirements-cuda.txt`, verifies CUDA, and
pre-caches the `xlm-roberta-base` backbone. Takes ~3 min.

## 4. Upload dataset

The augmented dataset (41 MB) is **not** in git. Push from Windows:

```powershell
# From repo root on Windows
$POD = "root@<pod-ip>"
$PORT = "<port>"

scp -P $PORT -i $HOME\.ssh\id_ed25519 `
    data\support_faq\dataset_augmented_v3.jsonl `
    data\support_faq\intents.json `
    "${POD}:/workspace/BettingwithAI/data/support_faq/"
```

Verify checksum on the pod:

```bash
cd /workspace/BettingwithAI
sha256sum data/support_faq/dataset_augmented_v3.jsonl
# expected: 6211d5265e2eba002ff582d87b2b0cd53976869a14ac227eda2d37e2488b9021
```

## 5. Train

```bash
cd /workspace/BettingwithAI
tmux new -s train
fb train-support-twohead --lang all --epochs 7 2>&1 \
    | tee logs/train_$(date +%Y%m%d_%H%M).log
# Detach: Ctrl+b  then  d     Reattach: tmux attach -t train
```

Monitor in a second tmux window (`Ctrl+b c` to create, `Ctrl+b 0/1` to switch):

```bash
watch -n 5 nvidia-smi
```

Expected VRAM: ~15 GB on RTX 4090 / A100. Expected utilization: 85-98 %.

## 6. Download artefacts

From Windows, once training is done:

```powershell
scp -P $PORT -i $HOME\.ssh\id_ed25519 -r `
    "${POD}:/workspace/BettingwithAI/models/support" `
    .\models\

scp -P $PORT -i $HOME\.ssh\id_ed25519 `
    "${POD}:/workspace/BettingwithAI/logs/*" `
    .\logs\
```

## 7. STOP the pod (critical!)

**Running pods keep billing.** Stop immediately after download:

**Option A — Web Console:** Pods → your pod → Stop button.
**Option B — From inside the pod:**

```bash
runpodctl stop pod $RUNPOD_POD_ID
```

**Stopped pod** keeps your volume (~$0.10/GB/month ≈ $2/month for 20 GB).
Click **Terminate** to remove everything.

## 8. Local validation

```powershell
& .venv-amd\Scripts\pytest.exe tests/test_support_transformer.py -v

Get-Content models\support\support_intent_twohead_metrics.json `
    | ConvertFrom-Json `
    | Select-Object -ExpandProperty per_language `
    | Format-Table lang, val_top1, val_macro_f1, val_chapter_top1
```

Commit metrics (models are gitignored):

```powershell
git add models/support/support_intent_twohead_metrics*.json
git commit -m "support: full 5-lang two-head fine-tune (RunPod 4090, 7 ep)"
git push
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `CUDA out of memory` | Lower batch: `FB_SUPPORT_BATCH=8 fb train-support-twohead ...` (needs config plumbing; RTX 4090 should be fine at default 16) |
| Pod disconnected / SSH drops | `tmux` protects you; reattach with `tmux attach -t train` |
| Community pod interrupted | Restart with same volume; one language may need re-train — use `fb train-support-twohead --lang <lg>` |
| `datasets_augmented_v3.jsonl missing` | Re-upload via scp step 4 |
| Slow HF download | Network spike; retry. Backbone is ~1.1 GB. |
| `git lfs` warnings | Harmless — repo has no LFS content |
| Cost creeping up | `runpodctl stop pod $RUNPOD_POD_ID` immediately |

---

## Cost breakdown (RTX 4090 Community, realistic)

| Item | Cost |
|---|---|
| Setup + upload (5 min) | $0.02 |
| Training 5 × 7 epochs (~3 h) | $0.66 |
| Download + stop (5 min) | $0.02 |
| Volume retention (30 days, optional) | $2.00 |
| **Total (single run, terminate after)** | **~$0.70** |
| **Total (keep volume 1 month)** | **~$2.70** |

You have 20 attempts worth of credit. Train with confidence.
