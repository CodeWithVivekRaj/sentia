# Start Sentia frontend
Set-Location "$PSScriptRoot\..\frontend"

Write-Host "Starting Sentia frontend..." -ForegroundColor Cyan

# Install deps if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages..." -ForegroundColor Yellow
    npm install
}

Write-Host "Frontend running at http://localhost:5173" -ForegroundColor Green
Write-Host ""

npm run dev
