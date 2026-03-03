@echo off
REM ============================================
REM  FlowDictation Windows - Build Script
REM  Builds a single .exe using PyInstaller
REM ============================================

echo.
echo === FlowDictation Build ===
echo.

REM Navigate to project root
cd /d "%~dp0.."

REM Step 1: Install dependencies
echo [1/4] Installing dependencies...
pip install -r requirements.txt pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo Make sure Python and pip are on your PATH.
    pause
    exit /b 1
)

REM Step 2: Generate sound files
echo [2/4] Generating sound files...
python scripts\generate_sounds.py
if errorlevel 1 (
    echo WARNING: Sound generation failed. Continuing anyway...
)

REM Step 3: Build with PyInstaller using the spec file
echo [3/4] Building executable...
pyinstaller --noconfirm FlowDictation.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

REM Step 4: Verify output
echo [4/4] Verifying...
if exist "dist\FlowDictation.exe" (
    echo.
    echo ==========================================
    echo   BUILD SUCCESSFUL!
    echo   Output: dist\FlowDictation.exe
    echo ==========================================
    echo.
    echo You can now run dist\FlowDictation.exe
) else (
    echo ERROR: Build output not found.
)

pause
