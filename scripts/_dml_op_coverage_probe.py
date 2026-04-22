"""Phase-0 op-coverage probe for ModernGBERT on torch-directml.

Runs a tiny 1-batch forward+backward on the AMD W7700 via DML.
If any op is missing, prints a clear failure so we can decide to fall
back to XLM-R-base for DE.
"""

from __future__ import annotations

import sys
import time
import traceback


def main() -> int:
    print("=" * 70)
    print("Phase-0: ModernGBERT op-coverage probe on DirectML")
    print("=" * 70)

    try:
        import torch
        import torch_directml as dml
        import transformers
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] import: {exc}")
        return 2

    print(f"torch            : {torch.__version__}")
    print(f"transformers     : {transformers.__version__}")
    print(f"dml.device_count : {dml.device_count()}")
    for i in range(dml.device_count()):
        print(f"  device[{i}]    : {dml.device_name(i)}")

    device = dml.device()
    print(f"selected device  : {device}")

    import os

    backbone = os.environ.get("FB_PROBE_BACKBONE", "LSX-UniWue/ModernGBERT_134M")
    print(f"\nLoading tokenizer + model: {backbone}")
    t0 = time.time()
    try:
        tok = transformers.AutoTokenizer.from_pretrained(backbone, use_fast=True)
        model = transformers.AutoModelForSequenceClassification.from_pretrained(
            backbone,
            num_labels=5,
            problem_type="single_label_classification",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] model load: {exc}")
        traceback.print_exc()
        return 3
    print(f"model loaded in  : {time.time() - t0:.1f}s")

    print("\nMoving model to DML device ...")
    try:
        model.to(device)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] model.to(dml): {exc}")
        traceback.print_exc()
        return 4

    texts = [
        "Was ist eine Value Bet?",
        "Wie kündige ich mein Abo?",
        "Ich habe mein Passwort vergessen.",
        "Wie funktionieren die Pi-Ratings?",
    ]
    labels = torch.tensor([0, 1, 2, 3], dtype=torch.long, device=device)
    enc = tok(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
    input_ids = enc["input_ids"].to(device)
    attn = enc["attention_mask"].to(device)
    print(f"input_ids.shape  : {tuple(input_ids.shape)}  device={input_ids.device}")

    print("\n[1/3] Forward pass ...")
    t0 = time.time()
    try:
        model.train()
        out = model(
            input_ids=input_ids,
            attention_mask=attn,
            output_hidden_states=True,
        )
        logits = out.logits
        hidden = out.hidden_states[-1]
        print(f"      logits.shape  = {tuple(logits.shape)} device={logits.device}")
        print(f"      hidden.shape  = {tuple(hidden.shape)}")
        print(f"      forward       = {time.time() - t0:.2f}s")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] forward: {exc}")
        traceback.print_exc()
        return 5

    print("\n[2/3] Hybrid loss (CE + SupCon) ...")
    try:
        from football_betting.support.losses import sup_con_loss

        ce_fn = torch.nn.CrossEntropyLoss()
        ce = ce_fn(logits, labels)
        pooled = hidden[:, 0, :]
        sc = sup_con_loss(pooled, labels, temperature=0.07)
        loss = 1.0 * ce + 0.3 * sc
        print(f"      ce            = {float(ce.item()):.4f}")
        print(f"      supcon        = {float(sc.item()):.4f}")
        print(f"      total         = {float(loss.item()):.4f}")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] loss: {exc}")
        traceback.print_exc()
        return 6

    print("\n[3/3] Backward pass + optimizer step ...")
    t0 = time.time()
    try:
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        print(f"      backward+step = {time.time() - t0:.2f}s")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] backward: {exc}")
        traceback.print_exc()
        return 7

    print("\n" + "=" * 70)
    print("[OK] ModernGBERT-134M runs end-to-end on DirectML.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
