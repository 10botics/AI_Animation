# AI Animation Studio — one-click local dashboard (no Streamlit account needed)
param(
    [int]$Port = 0,
    [string]$Chapter = ""
)

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python not found. Install Python 3.10+ and try again."
        exit 1
    }
}

Write-Host "Installing dependencies..."
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed."
    exit 1
}

$args = @()
if ($Port -gt 0) { $args += "--port"; $args += $Port }
if ($Chapter) { $args += "--chapter"; $args += $Chapter }

Write-Host ""
if ($args.Count -gt 0) {
    Write-Host "Starting AI Animation Studio with: $($args -join ' ')"
} else {
    Write-Host "Starting AI Animation Studio (port 8501, pick chapter in sidebar)..."
    Write-Host "Examples: .\Start-Studio.ps1 -Port 8502 -Chapter Chapter-82"
}
& .\.venv\Scripts\python.exe scripts\start_studio.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
