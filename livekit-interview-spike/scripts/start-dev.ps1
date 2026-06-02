$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$server = Join-Path $root "server"
$web = Join-Path $root "web"
$livekit = Join-Path $root "bin\livekit-server.exe"

if (-not (Test-Path -LiteralPath $livekit)) {
  throw "Missing LiveKit server executable: $livekit"
}

if (-not (Test-Path -LiteralPath (Join-Path $server ".venv\Scripts\python.exe"))) {
  throw "Missing Python virtual environment. Run: cd $server; python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt"
}

Start-Process powershell -WindowStyle Normal -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$root'; .\bin\livekit-server.exe --dev --bind 0.0.0.0"
)

Start-Sleep -Seconds 2

Start-Process powershell -WindowStyle Normal -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$server'; .\.venv\Scripts\Activate.ps1; python -m uvicorn token_server:app --host 127.0.0.1 --port 8787"
)

Start-Sleep -Seconds 1

Start-Process powershell -WindowStyle Normal -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$server'; .\.venv\Scripts\Activate.ps1; python agent.py"
)

Start-Sleep -Seconds 1

Start-Process powershell -WindowStyle Normal -ArgumentList @(
  "-NoExit",
  "-Command",
  "cd '$web'; npm run dev"
)

Write-Host "Started LiveKit spike windows. Open the Vite URL, usually http://localhost:5173"
