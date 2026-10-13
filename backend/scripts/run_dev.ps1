# scripts/run_dev.ps1
# Activate venv, ensure data dir, apply migrations, run uvicorn with reload.

$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
Push-Location $BackendDir

try {
    $VenvActivate = Join-Path $BackendDir ".venv\Scripts\Activate.ps1"
    if (Test-Path $VenvActivate) {
        Write-Host "Activating virtual environment..."
        . $VenvActivate
    } else {
        Write-Warning "Virtual env not found at $VenvActivate. Using system Python."
    }

    $DataDir = Join-Path $BackendDir "data"
    if (-not (Test-Path $DataDir)) {
        Write-Host "Creating data directory: $DataDir"
        New-Item -ItemType Directory -Path $DataDir | Out-Null
    }

    Write-Host "Applying database migrations..."
    alembic upgrade head

    Write-Host "Starting uvicorn on http://127.0.0.1:8000 ..."
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
}
finally {
    Pop-Location
}