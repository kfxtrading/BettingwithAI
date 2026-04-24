# ─────────────────────────────────────────────────────────────────────────────
# pack_cloud_dataset.ps1 — build a minimal tarball for upload to Vast.ai
#
# Bundles only the files needed to train the two-head support classifier
# on a cloud GPU. Writes a SHA256 manifest so integrity can be verified on
# the VM.
#
# Output: build/cloud/support_dataset_v3.tar.gz
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$outDir = Join-Path $root "build/cloud"
$null = New-Item -ItemType Directory -Force -Path $outDir

$files = @(
    "data/support_faq/dataset_augmented_v3.jsonl",
    "data/support_faq/intents.json"
)

# sanity
foreach ($f in $files) {
    if (-not (Test-Path $f)) {
        throw "Missing required file: $f"
    }
}

# checksum manifest
$manifest = Join-Path $outDir "SHA256SUMS.txt"
Remove-Item $manifest -ErrorAction SilentlyContinue
foreach ($f in $files) {
    $h = (Get-FileHash $f -Algorithm SHA256).Hash.ToLower()
    "$h  $f" | Out-File -Append -Encoding ascii $manifest
}
Write-Host "wrote $manifest" -ForegroundColor Green
Get-Content $manifest

# tarball (tar.exe is bundled with Windows 10+)
$tarball = Join-Path $outDir "support_dataset_v3.tar.gz"
Remove-Item $tarball -ErrorAction SilentlyContinue
tar -czf $tarball $files
Write-Host "wrote $tarball  ($([math]::Round((Get-Item $tarball).Length / 1MB, 2)) MB)" -ForegroundColor Green

Write-Host ""
Write-Host "Upload to Vast.ai:" -ForegroundColor Cyan
Write-Host "  scp -P <port> $tarball root@<host>:/workspace/BettingwithAI/"
Write-Host "On the VM:"
Write-Host "  cd /workspace/BettingwithAI && tar -xzf support_dataset_v3.tar.gz"
Write-Host "  sha256sum -c build/cloud/SHA256SUMS.txt   # (after copying manifest too)"
