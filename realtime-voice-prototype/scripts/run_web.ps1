$ErrorActionPreference = "Stop"
$webPath = Join-Path $PSScriptRoot "..\web"
Set-Location $webPath

if (-not (Test-Path -LiteralPath "node_modules")) {
    throw "Web dependencies are missing. Run npm install in web/ first."
}

npm run dev
