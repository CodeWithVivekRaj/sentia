# Start both Sentia services in new windows
$root = Split-Path $PSScriptRoot -Parent

Write-Host "=== Starting Sentia ===" -ForegroundColor Magenta
Write-Host ""

# Start backend in new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\scripts\start_backend.ps1"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start frontend in new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-File", "$root\scripts\start_frontend.ps1"

Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close those windows to stop Sentia." -ForegroundColor Yellow
