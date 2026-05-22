# Print LeafyMind local URLs from .env (run after: docker compose up -d)

$envFile = Join-Path (Join-Path $PSScriptRoot "..") ".env"
$frontend = "5173"
$bff = "3001"
$backend = "8000"

if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*FRONTEND_PORT=(.+)$') { $frontend = $matches[1].Trim() }
    if ($_ -match '^\s*BFF_PORT=(.+)$') { $bff = $matches[1].Trim() }
    if ($_ -match '^\s*BACKEND_PORT=(.+)$') { $backend = $matches[1].Trim() }
  }
}

Write-Host ""
Write-Host "LeafyMind is running. Open in your browser:" -ForegroundColor Green
Write-Host "  UI (landing):  http://localhost:$frontend/" -ForegroundColor Cyan
Write-Host "  Agent Hub:     http://localhost:$frontend/hub" -ForegroundColor Cyan
Write-Host "  Guest chat:    http://localhost:$frontend/chat" -ForegroundColor Cyan
Write-Host "  BFF health:    http://localhost:$bff/health" -ForegroundColor DarkGray
Write-Host "  API health:    http://localhost:$backend/health" -ForegroundColor DarkGray
Write-Host ""
