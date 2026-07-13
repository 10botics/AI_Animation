# AI Animation Studio — one-click local dashboard (no Streamlit account needed)
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

Write-Host ""
Write-Host "Starting AI Animation Studio — browser will open at http://localhost:8501"
Write-Host "Press Ctrl+C in this window to stop."
Write-Host ""

& .\.venv\Scripts\python.exe -m streamlit run scripts\beginner_dashboard.py --server.headless true
