@echo off
title Meta Nexus Agent - Zero-API FB & IG Autonomous Studio Launcher
cls

echo ===================================================================
echo   META NEXUS AGENT: ZERO-API FACEBOOK ^& INSTAGRAM STUDIO LAUNCHER
echo ===================================================================
echo.

cd /d "%~dp0"

set "PYTHON_EXE="

if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Python\bin\python.exe"
)

if "%PYTHON_EXE%"=="" (
    where py >nul 2>nul
    if %errorlevel% equ 0 set "PYTHON_EXE=py"
)

if "%PYTHON_EXE%"=="" (
    where python >nul 2>nul
    if %errorlevel% equ 0 set "PYTHON_EXE=python"
)

if not "%PYTHON_EXE%"=="" (
    echo [OK] Detected Python: %PYTHON_EXE%
    echo Verifying dependencies...
    "%PYTHON_EXE%" -m pip install -r requirements.txt --quiet
    "%PYTHON_EXE%" run.py
    pause
    exit /b
)

echo [ERROR] Working Python installation was not found.
pause
