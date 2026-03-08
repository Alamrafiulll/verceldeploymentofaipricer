$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Backend virtual environment Python was not found at $pythonExe"
}

Set-Location $scriptDir

& $pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
