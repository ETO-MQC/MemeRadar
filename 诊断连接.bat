@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先双击“启动_MVP.bat”完成首次安装。
  pause & exit /b 1
)
call .venv\Scripts\activate.bat
python -m app.diagnostics
pause
