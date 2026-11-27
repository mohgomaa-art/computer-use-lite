@echo off
REM Copyright 2026 Mohamed Gomaa
REM SPDX-License-Identifier: Apache-2.0
setlocal EnableExtensions DisableDelayedExpansion

set "CUL_REPO_ROOT=%~dp0.."
for %%I in ("%CUL_REPO_ROOT%") do set "CUL_REPO_ROOT=%%~fI"

if not exist "%CUL_REPO_ROOT%\pyproject.toml" (
    echo ERROR: Could not locate the CUL repository next to this installer.
    exit /b 1
)

set "CUL_BASE_PYTHON="
for /f "usebackq delims=" %%P in (`py -3 -c "import sys; print(sys.executable)" 2^>nul`) do set "CUL_BASE_PYTHON=%%P"
if not defined CUL_BASE_PYTHON (
    for /f "usebackq delims=" %%P in (`where python 2^>nul`) do (
        echo %%P | findstr /I /C:"\WindowsApps\" >nul
        if errorlevel 1 if not defined CUL_BASE_PYTHON set "CUL_BASE_PYTHON=%%P"
    )
)
if not defined CUL_BASE_PYTHON (
    echo ERROR: Native Windows Python was not found. Install Python 3.10 or newer and try again.
    exit /b 1
)

"%CUL_BASE_PYTHON%" -c "import os,sys; assert sys.platform == 'win32' and os.name == 'nt'; assert sys.version_info >= (3,10)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: The selected Python must be native Windows Python 3.10 or newer.
    exit /b 1
)

set "CUL_VENV_PYTHON=%CUL_REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%CUL_VENV_PYTHON%" (
    echo Creating repository virtual environment...
    "%CUL_BASE_PYTHON%" -m venv "%CUL_REPO_ROOT%\.venv"
    if errorlevel 1 (
        echo ERROR: Failed to create the repository virtual environment.
        exit /b 1
    )
)

echo Installing CUL and the configuration helper dependency...
"%CUL_VENV_PYTHON%" -m pip install -e "%CUL_REPO_ROOT%[setup]"
if errorlevel 1 (
    echo ERROR: Dependency installation failed. Review the pip output above.
    exit /b 1
)

echo Registering CUL with Codex, Antigravity, and Claude Code...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0merge_mcp_configs.ps1" -RepositoryRoot "%CUL_REPO_ROOT%" -PythonExe "%CUL_VENV_PYTHON%"
if errorlevel 1 (
    echo ERROR: MCP configuration update failed. Existing configuration backups, if created, are retained.
    exit /b 1
)

echo.
echo Setup completed. Restart or refresh MCP servers in Codex, Antigravity, and Claude Code.
echo Verify that the computer_use_lite server is connected and lists its 16 tools (15 core tools plus cul_reload).
echo This installer did not launch the server or interact with desktop applications.
exit /b 0
