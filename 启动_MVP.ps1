Set-Location $PSScriptRoot
if (!(Test-Path .env)) { Copy-Item .env.example .env }
if (!(Test-Path .venv)) { py -3 -m venv .venv }
& .\.venv\Scripts\Activate.ps1
python -c "import fastapi,httpx" 2>$null
if ($LASTEXITCODE -ne 0) { python -m pip install -r requirements.txt }
Start-Process "http://127.0.0.1:8765"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
