# ─────────────────────────────────────────────────────────────────────────────
# train_support_local.ps1 — full 5-language two-head support-classifier run
# on the AMD W7700 via torch-directml.
#
# Runtime estimate (Bundesliga box):
#   DE/EN/ES/FR/IT  ≈  2.5-3.5 h each  ×  5  =  ~13-17 h
#
# Usage (from repo root, *any* shell — this activates .venv-amd itself):
#   pwsh ./scripts/train_support_local.ps1              # default: 7 epochs, lang=all
#   pwsh ./scripts/train_support_local.ps1 -Epochs 4    # shorter run
#   pwsh ./scripts/train_support_local.ps1 -Lang de     # single language
#   pwsh ./scripts/train_support_local.ps1 -Smoke       # 1 epoch × 20 rows/intent
#
# The script:
#   1. Verifies .venv-amd + torch-directml
#   2. Verifies dataset checksum
#   3. Prevents the box from sleeping while training runs
#   4. Tees stdout+stderr into logs/train_support_<timestamp>.log
#   5. Saves per-language artefacts → crash-safe (partial progress kept)
# ─────────────────────────────────────────────────────────────────────────────
[CmdletBinding()]
param(
    [string]$Lang = "all",
    [int]$Epochs = 7,
    [switch]$Smoke,
    [switch]$NoOod,
    [string]$Venv = ".venv-amd"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ─── 1. venv sanity ─────────────────────────────────────────────────────────
$py = Join-Path $root "$Venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    throw "venv not found: $py  — create with:  python -m venv $Venv"
}
Write-Host "==> using venv: $Venv" -ForegroundColor Cyan

& $py -c @"
import torch, torch_directml, sys
d = torch_directml.device()
print(f'torch={torch.__version__}  dml device={torch_directml.device_name(0)}  count={torch_directml.device_count()}')
x = torch.randn(4,4, device=d)
assert torch.isfinite((x @ x.T).sum()).item(), 'DML sanity failed'
"@
if ($LASTEXITCODE -ne 0) { throw "DirectML sanity check failed — see output above" }

# ─── 2. dataset checksum ────────────────────────────────────────────────────
$ds = "data/support_faq/dataset_augmented_v3.jsonl"
if (-not (Test-Path $ds)) { throw "Missing dataset: $ds  — rebuild with scripts/augment_support_llm.py" }
$expected = "6211D5265E2EBA002FF582D87B2B0CD53976869A14AC227EDA2D37E2488B9021"
$actual   = (Get-FileHash $ds -Algorithm SHA256).Hash
if ($actual -ne $expected) {
    Write-Warning "dataset SHA256 drift detected"
    Write-Warning "  expected $expected"
    Write-Warning "  actual   $actual"
    $ans = Read-Host "Continue anyway? [y/N]"
    if ($ans -notmatch '^[yY]') { throw "aborted by user" }
} else {
    Write-Host "==> dataset checksum ok ($([math]::Round((Get-Item $ds).Length/1MB,2)) MB, 82 806 rows)" -ForegroundColor Green
}

# ─── 3. prevent sleep (thread-level request, auto-released on exit) ─────────
Write-Host "==> requesting ES_CONTINUOUS | ES_SYSTEM_REQUIRED (sleep blocked)" -ForegroundColor Cyan
$sig = @"
[DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
"@
$stes = Add-Type -MemberDefinition $sig -Name PowerUtil -Namespace Win32 -PassThru
$ES_CONTINUOUS      = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED = [uint32]"0x00000001"
$ES_AWAYMODE        = [uint32]"0x00000040"
[void]$stes::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_AWAYMODE)

# ─── 4. log file ────────────────────────────────────────────────────────────
$null = New-Item -ItemType Directory -Force -Path logs
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = "logs/train_support_${stamp}.log"
Write-Host "==> logging to $log" -ForegroundColor Cyan

# ─── 5. assemble fb command ─────────────────────────────────────────────────
$effectiveEpochs = if ($Smoke) { 1 } else { $Epochs }
$fbArgs = @("train-support-twohead", "--lang", $Lang, "--epochs", "$effectiveEpochs")
if ($NoOod) { $fbArgs += "--no-ood" }
if ($Smoke) { $fbArgs += @("--max-rows-per-intent", "20") }

Write-Host "==> command: $py -m football_betting.cli $($fbArgs -join ' ')" -ForegroundColor Cyan
Write-Host ""

# Unbuffered stdout for live progress + tee
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

$started = Get-Date
& $py -u -m football_betting.cli @fbArgs 2>&1 | Tee-Object -FilePath $log
$exit = $LASTEXITCODE
$duration = (Get-Date) - $started

Write-Host ""
Write-Host "==> done  (exit=$exit  duration=$([math]::Round($duration.TotalMinutes,1)) min)" -ForegroundColor Cyan
Write-Host "==> log:    $log"
Write-Host "==> models: models/support/twohead_*.safetensors"

# release sleep lock
[void]$stes::SetThreadExecutionState($ES_CONTINUOUS)

exit $exit
