@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Local server: http://127.0.0.1:8765/
echo Open standalone.html directly for offline use (no server).
start http://127.0.0.1:8765/
python server.py
pause
