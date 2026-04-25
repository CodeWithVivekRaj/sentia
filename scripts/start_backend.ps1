# Start Sentia backend
$env:PATH = "C:\Users\$env:USERNAME\.local\bin;" + $env:PATH
Set-Location "$PSScriptRoot\..\backend"

Write-Host "Starting Sentia backend..." -ForegroundColor Cyan

# Check if virtual environment exists, create if not
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment and installing dependencies..." -ForegroundColor Yellow
    poetry install
}

Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

poetry run python -m uvicorn sentia.api.main:app --host 0.0.0.0 --port 8000 --reload
