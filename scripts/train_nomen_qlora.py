"""QLoRA fine-tuning script for Nomen — Günter Netzer style match analyst.

Fine-tunes Qwen2.5-72B-Instruct with LoRA adapters on the Nomen training dataset.
Designed for 2 × H100 SXM5 80 GB (RunPod). Also works on 1 × A100 80 GB (longer).

Training cost estimate:
    2 × H100 SXM5 (~6h) ≈ $47    |   1 × A100 80 GB (~11h) ≈ $18

Usage
-----
    # Single-GPU (A100 / H100)
    python scripts/train_nomen_qlora.py \\
        --dataset data/nomen_training/dataset_v1.jsonl \\
        --output  models/nomen_qlora_v1 \\
        --wandb-project nomen-training

    # Multi-GPU via accelerate (launched by setup script)
    accelerate launch --config_file /workspace/accelerate_config.yaml \\
        scripts/train_nomen_qlora.py \\
        --dataset data/nomen_training/dataset_v1.jsonl \\
        --output  models/nomen_qlora_v1 \\
        --wandb-project nomen-training
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger("train_nomen_qlora")


# ── Model + training hyperparameters ─────────────────────────────────────────

BASE_MODEL = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-72B-Instruct")
MODEL_CACHE = os.environ.get("MODEL_CACHE_DIR", "/workspace/model_cache")

LORA_CONFIG = dict(
    r=64,
    lora_alpha=128,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
)

TRAINING_CONFIG = dict(
    num_train_epochs=3,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,       # effective batch = 32 across 2 GPUs
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    weight_decay=0.01,
    max_grad_norm=1.0,
    bf16=True,
    fp16=False,
    gradient_checkpointing=True,
    dataloader_num_workers=4,
    save_strategy="steps",
    save_steps=100,
    save_total_limit=3,
    evaluation_strategy="steps",
    eval_steps=100,
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    report_to="wandb",
    run_name="nomen-qlora-v1",
    max_seq_length=1024,
    packing=True,
)


# ── Dataset loading ───────────────────────────────────────────────────────────

NOMEN_SYSTEM = (
    "You are Nomen, the football prediction AI. "
    "Analyse matches with the tactical authority and decisive voice of Günter Netzer. "
    "Be direct. Make bold predictions. Never hedge. "
    "Open with the tactical key, not a description. Close with a verdict."
)


def _format_example(row: dict) -> str:
    """Convert a training row to the Qwen2.5-instruct chat template string."""
    messages = row.get("messages", [])
    if not messages:
        # Fallback: reconstruct from match_data + article
        match_data = row.get("match_data", {})
        article = row.get("article", "")
        messages = [
            {"role": "system", "content": NOMEN_SYSTEM},
            {"role": "user", "content": json.dumps(match_data, ensure_ascii=False)},
            {"role": "assistant", "content": article},
        ]

    # Override system prompt with canonical Nomen voice
    formatted = []
    for m in messages:
        if m["role"] == "system":
            formatted.append({"role": "system", "content": NOMEN_SYSTEM})
        else:
            formatted.append(m)

    # Qwen2.5-instruct chat format
    out = ""
    for m in formatted:
        out += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
    out += "<|im_start|>assistant\n"
    return out


def load_dataset_splits(path: Path) -> tuple:
    """Load JSONL, format as strings, split 90/10 train/eval."""
    from datasets import Dataset  # type: ignore[import]

    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    texts = [_format_example(r) for r in rows]
    logger.info("Loaded %d training examples", len(texts))

    # Shuffle + split
    import random
    rng = random.Random(42)
    rng.shuffle(texts)
    split_idx = int(len(texts) * 0.9)

    train_ds = Dataset.from_dict({"text": texts[:split_idx]})
    eval_ds = Dataset.from_dict({"text": texts[split_idx:]})
    logger.info("Split: %d train, %d eval", len(train_ds), len(eval_ds))
    return train_ds, eval_ds


# ── Training ──────────────────────────────────────────────────────────────────

def train(args: argparse.Namespace) -> None:
    import torch  # type: ignore[import]
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments  # type: ignore[import]
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # type: ignore[import]
    from trl import SFTTrainer, SFTConfig  # type: ignore[import]
    from bitsandbytes.optim import AdamW8bit  # type: ignore[import]

    try:
        import bitsandbytes as bnb  # type: ignore[import]
        from transformers import BitsAndBytesConfig  # type: ignore[import]
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        logger.info("Using NF4 4-bit quantization (QLoRA)")
    except ImportError:
        bnb_config = None
        logger.warning("bitsandbytes not available — falling back to full precision LoRA (needs more VRAM)")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load tokenizer
    logger.info("Loading tokenizer: %s", BASE_MODEL)
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        cache_dir=MODEL_CACHE,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Load model with quantization
    logger.info("Loading base model: %s", BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        cache_dir=MODEL_CACHE,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )

    if bnb_config is not None:
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # Apply LoRA
    lora_cfg = LoraConfig(**LORA_CONFIG)
    model = get_peft_model(model, lora_cfg)
    model.print_trainable_parameters()

    # Load dataset
    train_ds, eval_ds = load_dataset_splits(Path(args.dataset))

    # Training arguments
    cfg = dict(TRAINING_CONFIG)
    cfg["output_dir"] = str(output_dir)
    if args.wandb_project:
        os.environ["WANDB_PROJECT"] = args.wandb_project
    if args.epochs:
        cfg["num_train_epochs"] = args.epochs

    sft_cfg = SFTConfig(**cfg)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=sft_cfg,
        dataset_text_field="text",
    )

    logger.info("Starting training...")
    trainer.train()

    # Save final adapter
    final_dir = output_dir / "final"
    final_dir.mkdir(exist_ok=True)
    trainer.model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    logger.info("Saved final adapter to %s", final_dir)

    # Save training summary
    summary = {
        "base_model": BASE_MODEL,
        "lora_config": LORA_CONFIG,
        "training_config": {k: v for k, v in TRAINING_CONFIG.items() if not callable(v)},
        "n_train": len(train_ds),
        "n_eval": len(eval_ds),
        "final_eval_loss": trainer.state.best_metric,
    }
    (output_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    logger.info("Training complete. Summary saved to %s/training_summary.json", output_dir)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Train Nomen with QLoRA")
    parser.add_argument("--dataset", required=True, help="Path to dataset_v1.jsonl")
    parser.add_argument("--output", default="models/nomen_qlora_v1", help="Output directory for adapter")
    parser.add_argument("--wandb-project", default="nomen-training", help="W&B project name")
    parser.add_argument("--epochs", type=int, default=None, help="Override num_train_epochs")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"[train] Dataset not found: {dataset_path}", file=sys.stderr)
        print("[train] Run generate_nomen_dataset.py + validate_nomen_dataset.py first.", file=sys.stderr)
        sys.exit(1)

    train(args)


if __name__ == "__main__":
    main()
