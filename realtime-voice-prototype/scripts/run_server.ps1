$ErrorActionPreference = "Stop"
$serverPath = Join-Path $PSScriptRoot "..\server"
Set-Location $serverPath

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    throw "Server virtual environment is missing. Run the installation steps in README.md first."
}

& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000
