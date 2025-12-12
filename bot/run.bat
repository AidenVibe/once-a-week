@echo off
cd /d "%~dp0"

REM Load .env file
for /f "tokens=1,2 delims==" %%a in (.env) do set %%a=%%b

python main.py
pause
