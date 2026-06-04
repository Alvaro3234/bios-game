@echo off
REM Build bios.exe on Windows.
REM Requires: Python 3.10+ installed and on PATH.

cd /d "%~dp0"

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pygame numpy pyinstaller

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller bios.spec

echo.
echo Build complete. Output:
dir dist
