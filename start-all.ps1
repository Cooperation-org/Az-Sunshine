# PowerShell script to start both Django backend and Vite frontend servers
# Usage: .\start-all.ps1

# Set execution policy for this session if needed
$ExecutionPolicy = Get-ExecutionPolicy
if ($ExecutionPolicy -eq "Restricted") {
    Write-Host "Warning: Execution policy is Restricted. Attempting to set for current process..." -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting AZ Sunshine Full Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js $nodeVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Check if Python is installed
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check if npm is installed
Write-Host "Checking npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "✓ npm $npmVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ npm not found. Please install npm" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting servers..." -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Django backend in a new window
Write-Host "Starting Django backend (http://127.0.0.1:8000)..." -ForegroundColor Yellow
$backendPath = Join-Path $scriptDir "backend"
$venvPath = Join-Path $backendPath "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    $backendCommand = "cd `"$backendPath`"; .\venv\Scripts\Activate.ps1; Write-Host 'Virtual environment activated. Starting Django server...' -ForegroundColor Green; python manage.py runserver"
} else {
    $backendCommand = "cd `"$backendPath`"; Write-Host 'Starting Django server (no venv found)...' -ForegroundColor Yellow; python manage.py runserver"
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

# Wait a bit for Django to start
Start-Sleep -Seconds 3

# Start Vite frontend in a new window
Write-Host "Starting Vite frontend (http://localhost:5173)..." -ForegroundColor Yellow
$frontendPath = Join-Path $scriptDir "frontend"
$frontendCommand = "cd `"$frontendPath`"; Write-Host 'Starting Vite dev server...' -ForegroundColor Green; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Servers are starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Endpoint: http://127.0.0.1:8000/api/v1/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each server window to stop them." -ForegroundColor Yellow
Write-Host ""

