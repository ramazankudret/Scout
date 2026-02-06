# Scout - Geliştirme ortamı başlat
# 1) Docker Desktop'in acik oldugundan emin ol
# 2) Bu script: PostgreSQL'i ayaga kaldirir, backend'i baslatir

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "Scout - PostgreSQL ve Backend baslatiliyor..." -ForegroundColor Cyan

# PostgreSQL (Docker)
Set-Location $ProjectRoot
$dockerPs = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "HATA: Docker calisiyor gibi gorunmuyor. Docker Desktop'i acip tekrar deneyin." -ForegroundColor Red
    exit 1
}
if (-not ($dockerPs -match "scout_postgres|scout-pg")) {
    Write-Host "PostgreSQL container baslatiliyor (docker-compose up -d db)..." -ForegroundColor Yellow
    docker-compose up -d db
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "PostgreSQL baslatildi. 5 saniye bekleniyor..." -ForegroundColor Green
    Start-Sleep -Seconds 5
} else {
    Write-Host "PostgreSQL zaten calisiyor." -ForegroundColor Green
}

# Port 8000 doluysa once kapat (WinError 10048 onlemi)
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "Port 8000 dolu (PID $($conn.OwningProcess)), kapatiliyor..." -ForegroundColor Yellow
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Backend
Write-Host "Backend baslatiliyor (port 8000)..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\backend"
$env:PYTHONPATH = "src"
python -m uvicorn scout.main:app --host 127.0.0.1 --port 8000
