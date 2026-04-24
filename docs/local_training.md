# Local Full-Training Guide (AMD W7700 / DirectML)

Complete recipe for running the two-head support classifier fine-tune
(`xlm-roberta-base` + chapter/intent heads, SupCon, `cw=0.3`, `gate=0.7`)
on all 5 languages locally.

---

## Hardware / stack

| Component        | Value                                       |
|------------------|---------------------------------------------|
| GPU              | AMD Radeon PRO W7700 (20 GB VRAM)           |
| Backend          | torch-directml 0.2.x                        |
| Python / torch   | 3.11.9  /  2.4.1+cpu                        |
| venv             | `.venv-amd`                                 |
| Dataset          | `dataset_augmented_v3.jsonl` (82 806 rows)  |

---

## Runtime estimate

| Phase                              | Per language   | Total (5 langs)  |
|------------------------------------|----------------|------------------|
| Smoke (1 ep × 20 rows/intent)      | ~8 min         | ~40 min          |
| 4 epochs × full data               | ~1.8 h         | ~9 h             |
| **7 epochs × full data (recommended)** | **~2.5–3.5 h** | **~13–17 h**     |

---

## Pre-flight checklist

- [ ] Close other GPU-hungry apps (`fb train-tab`, games, video editing)
- [ ] Plug in laptop / AC power (no battery runs)
- [ ] Disable Windows Update auto-reboot:
      Settings → Windows Update → Advanced → "Pause updates 5 weeks"
- [ ] 40 GB free on C:\ (HF cache + model artefacts ≈ 8 GB, but safety)
- [ ] Accept that the box will be busy for ~15 h — plan to sleep through it

The script itself handles:
- [x] `.venv-amd` selection
- [x] DirectML sanity test (4×4 matmul)
- [x] Dataset SHA256 verification
- [x] Sleep prevention (`SetThreadExecutionState`)
- [x] Full stdout+stderr tee to `logs/train_support_<timestamp>.log`

---

## Run

```powershell
# Default — 7 epochs, all 5 languages, OOD seeds included
pwsh ./scripts/train_support_local.ps1
```

### Variants

```powershell
# Quick smoke test (~40 min, 1 epoch × 20 rows/intent)
pwsh ./scripts/train_support_local.ps1 -Smoke

# 4 epochs (compromise, ~9 h)
pwsh ./scripts/train_support_local.ps1 -Epochs 4

# Single language (debug / resume)
pwsh ./scripts/train_support_local.ps1 -Lang de -Epochs 7

# Skip OOD seeds (HP-tuning style, cleaner metrics)
pwsh ./scripts/train_support_local.ps1 -NoOod
```

---

## Run it detached (recommended)

So the job survives VS Code reloads / accidental terminal closes:

```powershell
# Start as background PowerShell job
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    pwsh ./scripts/train_support_local.ps1 -Epochs 7
}
$job.Id   # remember this

# Tail the log live (in any terminal)
Get-Content logs/train_support_*.log -Wait -Tail 40

# Check status later
Get-Job $job.Id
Receive-Job $job.Id -Keep    # print collected output without removing
```

Alternatively, a dedicated **VS Code async terminal** works equally well and
keeps the stdout pane attached — close VS Code's workspace carefully (do
**not** quit the whole VS Code app, that kills child processes).

---

## Monitor VRAM / GPU

In a second PowerShell window:

```powershell
# Windows Task Manager → Performance → GPU 1 (W7700) → "3D" + "Dedicated GPU memory"
# OR via CLI:
while ($true) {
    Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine `
      | Where-Object { $_.utilization -gt 0 } `
      | Sort-Object -Property utilization -Descending `
      | Select-Object -First 3 Name, utilization `
      | Format-Table -AutoSize
    Start-Sleep 5
}
```

Expected: `3D` engine at ~80-95 %, VRAM 11-14 GB during transformer fine-tune.

---

## Artefacts produced

Per language (`<lg>` ∈ `{de, en, es, fr, it}`):

```
models/support/
  twohead_<lg>/
    encoder/                      # HF pretrained save of fine-tuned backbone
    tokenizer/
    heads.pt                      # chapter+intent head state dicts
    meta.json                     # HP record, label maps, metrics
    calibrator.joblib             # temperature scaler
  support_intent_twohead_metrics.json            # aggregate (all langs)
  support_intent_twohead_metrics_<lg>.json       # per-language detail
```

Crash-safe: each language is saved immediately after training, so a
mid-run crash only loses the *current* language. Resume via:

```powershell
pwsh ./scripts/train_support_local.ps1 -Lang <failed_lang> -Epochs 7
```

---

## After training — evaluation + commit

```powershell
# Run support-transformer regression tests
& .venv-amd\Scripts\pytest.exe tests/test_support_transformer.py -v

# Inspect metrics
Get-Content models/support/support_intent_twohead_metrics.json `
  | ConvertFrom-Json `
  | Select-Object -ExpandProperty per_language `
  | Select-Object lang, val_top1, val_macro_f1, chapter_top1 `
  | Format-Table -AutoSize

# Commit the metrics JSON (models themselves are gitignored)
git add models/support/support_intent_twohead_metrics*.json
git commit -m "support: full 5-lang two-head fine-tune (7 ep, cw=0.3 gate=0.7)"
```

---

## Troubleshooting

| Symptom | Remedy |
|---|---|
| `ModuleNotFoundError: torch_directml` | Run in `.venv-amd`, not `.venv` — the script enforces this. |
| VRAM OOM (out-of-memory) on a specific language | Close other GPU apps; lower batch via env: `$env:FB_SUPPORT_BATCH=8; pwsh scripts/train_support_local.ps1` (needs a matching config hook). |
| One language crashes, others should continue | `train_two_head_all` already catches per-language exceptions and continues. Check log for `[red]Failed for <lg>` entries. |
| Laptop sleeps anyway | The script uses `ES_SYSTEM_REQUIRED`; for deeper hibernate disable:  `powercfg /hibernate off`  (reversible). |
| Log grows huge | Expected (~50-100 MB). Gets `.log`-ignored by .gitignore already. |
| `sdpa_mask` shape error in transformers | We already pin `attn_implementation="eager"` in `two_head_transformer.py`. If it reappears, update: `& .venv-amd\Scripts\pip install "transformers>=4.40,<4.50"` |
