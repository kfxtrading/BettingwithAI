# Nomen Training Plan — Günter Netzer Style

Fine-tune Qwen2.5-72B-Instruct with QLoRA to give Nomen the analytical voice of Günter Netzer — direct, tactical, decisive. No hedging. No generic summaries. Pure football intelligence.

---

## Prerequisites

| What | Where |
|------|-------|
| Anthropic API key | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| RunPod account | [runpod.io](https://runpod.io) |
| Ollama running locally | [ollama.com](https://ollama.com) (for serving after training) |
| WandB account (optional) | [wandb.ai](https://wandb.ai) — for training metrics |

---

## Step 1 — Generate Training Data

Run locally. No GPU needed. Takes ~30 minutes.

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Generate 2,000 Netzer-style match analysis examples (400 per language)
python scripts/generate_nomen_dataset.py --count 400

# Validate quality — target is ≥ 85% pass rate
python scripts/validate_nomen_dataset.py --report
```

**Output:** `data/nomen_training/dataset_v1.jsonl`
**Cost:** ~$10–15 (Claude Opus 4)

> **Smoke test first** (optional, ~$0.10):
> ```bash
> python scripts/generate_nomen_dataset.py --lang en --count 10
> python scripts/validate_nomen_dataset.py --report
> ```

---

## Step 2 — Launch RunPod Training Pod

Go to [runpod.io](https://runpod.io) → **Deploy** and configure:

| Setting | Value |
|---------|-------|
| Image | `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` |
| GPU | **2 × H100 SXM5 80 GB** |
| Disk | **250 GB** |
| HTTP Port | 8080 |

**Estimated cost:** ~$7.78/h × 7h = **~$55**

---

## Step 3 — Set Up the Pod

SSH into the pod, then:

```bash
# 1. Clone repo and install dependencies (~10 min)
bash setup_runpod_nomen.sh
# This also starts downloading Qwen2.5-72B in the background (~45 min)

# 2. Monitor the model download
tail -f logs/model_download.log

# 3. Upload your training dataset from your local machine
#    (run this on your LOCAL machine, not the pod)
scp data/nomen_training/dataset_v1.jsonl root@<pod-ip>:/workspace/BettingwithAI/data/nomen_training/
```

---

## Step 4 — Train Nomen

Start a tmux session so training keeps running if your connection drops.

```bash
# On the pod:
tmux new -s train

accelerate launch --config_file /workspace/accelerate_config.yaml \
  scripts/train_nomen_qlora.py \
  --dataset data/nomen_training/dataset_v1.jsonl \
  --output  models/nomen_qlora_v1 \
  --wandb-project nomen-training
```

**Expected runtime:** ~6h on 2 × H100 SXM5

You can close your laptop — training keeps running in tmux. Re-attach anytime:
```bash
tmux attach -t train
```

> **Monitor on WandB:** loss should drop from ~2.8 → ~1.1 over 3 epochs.

---

## Step 5 — Export to GGUF

When training finishes, still on the pod:

```bash
bash scripts/export_nomen_gguf.sh
```

This will:
1. Merge LoRA adapters into the full model weights
2. Convert to `nomen-v1.Q4_K_M.gguf` (~39 GB) for local Ollama serving
3. Convert to `nomen-v1.Q8_0.gguf` (~74 GB) for cloud vLLM serving
4. Generate `models/Modelfile.nomen` for Ollama

**Takes ~1h.**

---

## Step 6 — Download the Model

Run on your **local machine**:

```bash
scp root@<pod-ip>:/workspace/BettingwithAI/models/nomen-v1.Q4_K_M.gguf ./models/
scp root@<pod-ip>:/workspace/BettingwithAI/models/Modelfile.nomen ./models/
```

Then **stop the pod** to avoid ongoing charges:
```bash
runpodctl stop pod <pod-id>
```

---

## Step 7 — Register with Ollama

```bash
ollama create nomen-v1 -f models/Modelfile.nomen

# Quick smoke test
ollama run nomen-v1 "Analyse Arsenal vs Chelsea: home 54%, draw 26%, away 20%, form WWDLW / DWWLD, value bet detected"
```

Nomen should respond with a 4–6 sentence tactical analysis — bold, decisive, no hedging.

---

## Step 8 — Benchmark

```bash
# Get today's fixtures
fb snapshot

# Run benchmark — Nomen v1 must score ≥ 80% to go live
python scripts/bench_match_analyst.py --compare-base --verbose --lang en
```

The benchmark compares **nomen-v1** (fine-tuned) vs **qwen2.5:7b** (base model) on 11 criteria:

| Category | Criteria |
|----------|----------|
| Factual | team names mentioned, probability referenced, form mentioned, news integrated, correct length, value-bet signal |
| Style (Netzer) | tactical vocabulary, no hedging, historical callback, 4–6 sentences, strong tactical opener |

**Quality gate: ≥ 80% aggregate score.** If it passes, `match_analyst.py` automatically uses `nomen-v1` — no further changes needed.

---

## Optional: Cloud Serving via vLLM

If your local machine doesn't have 48 GB+ VRAM for the Q4_K_M GGUF, run Nomen on a persistent RunPod inference pod:

```bash
# On a new RunPod pod (1 × A100 SXM 80GB, ~$1.64/h)
# Upload Q8_0 GGUF first, then:
bash scripts/setup_nomen_runpod_inference.sh
```

Then set in Railway (or your `.env.local`):
```
NOMEN_VLLM_URL=https://<pod-id>-8080.proxy.runpod.net/v1
```

`match_analyst.py` will automatically route to the vLLM endpoint instead of local Ollama.

---

## Cost Summary

| Item | Time | Cost |
|------|------|------|
| Dataset generation (Claude Opus 4) | ~30 min | ~$15 |
| RunPod 2 × H100 SXM5 training | ~7h | ~$55 |
| **Total one-time training cost** | | **~$70** |
| RunPod A100 inference pod (optional, per month) | persistent | ~$1,200/mo |
| RunPod A100 inference pod (optional, on-demand) | ~20h/mo | ~$33/mo |

---

## File Reference

| File | Purpose |
|------|---------|
| `data/nomen_training/style_guide.md` | The 6 Netzer style rules — single source of truth |
| `scripts/generate_nomen_dataset.py` | Dataset generation via Claude Opus 4 |
| `scripts/validate_nomen_dataset.py` | Quality gate + per-language report |
| `scripts/setup_runpod_nomen.sh` | RunPod pod bootstrap (H100, 72B download) |
| `scripts/train_nomen_qlora.py` | QLoRA SFT training (trl + PEFT + bitsandbytes) |
| `scripts/export_nomen_gguf.sh` | Merge adapters → GGUF Q4_K_M + Q8_0 + Modelfile |
| `scripts/setup_nomen_runpod_inference.sh` | vLLM inference pod setup |
| `src/football_betting/support/match_analyst.py` | Auto-routes vLLM → Ollama nomen-v1 → fallback |
| `scripts/bench_match_analyst.py` | 11-criteria benchmark with A/B comparison |
