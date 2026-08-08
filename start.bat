@echo off
echo ========================================================
echo     GORGONA-ONE AI // HIGH-TECH CYBER LAUNCHER
echo ========================================================
echo.
cd /d "%~dp0"
echo Starting Gorgona-One AI Core Server...
echo Access Web UI at: http://localhost:8000
echo.
"%USERPROFILE%\.local\bin\uv.exe" run --with "fastapi>=0.100.0" --with "uvicorn>=0.22.0" --with "httpx>=0.24.0" --with "pydantic>=2.0" --with "websockets>=11.0" main.py
pause
