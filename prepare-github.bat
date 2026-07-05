@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Building standalone.html ...
python build_standalone.py

if not exist docs mkdir docs
copy /Y standalone.html docs\index.html >nul

echo.
echo Ready for GitHub Pages:
echo   docs\index.html
echo.
echo Push to GitHub, then Settings ^> Pages ^> Deploy from /docs
explorer docs
pause
