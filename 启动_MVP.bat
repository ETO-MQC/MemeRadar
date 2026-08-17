@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title MemeRadar MVP 1.0
if not exist ".env" copy /Y ".env.example" ".env" >nul
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% --version >nul 2>nul || (
  echo [错误] 未找到 Python 3。请先安装 Python 3.11+ 并勾选 Add Python to PATH。
  pause & exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [首次运行] 正在创建虚拟环境...
  %PY% -m venv .venv || (pause & exit /b 1)
)
call .venv\Scripts\activate.bat
python -c "import fastapi,httpx" >nul 2>nul || (
  echo [首次运行] 正在安装开源依赖...
  python -m pip install --upgrade pip
  pip install -r requirements.txt || (pause & exit /b 1)
)
start "" http://127.0.0.1:8765
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
pause
