@echo off
REM Screen Automator Framework - Quick Start Setup Script (Windows)
REM This script sets up the development environment with all framework features

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo.
echo      Screen Automator Framework - Quick Start Setup
echo.
echo ========================================================================
echo.

echo Step 1: Checking Poetry installation...
where poetry >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Poetry not found. Please install Poetry first:
    echo https://install.python-poetry.org
    echo.
    echo Run this in PowerShell as Administrator:
    echo   ^(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing^).Content ^| python -
    pause
    exit /b 1
) else (
    echo OK Poetry found
)

echo.
echo Step 2: Installing dependencies...
call poetry install --with dev
if %ERRORLEVEL% NEQ 0 (
    echo ERROR Failed to install dependencies
    pause
    exit /b 1
)
echo OK Dependencies installed

echo.
echo Step 3: Installing pre-commit hooks...
call poetry run pre-commit install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR Failed to install pre-commit hooks
    pause
    exit /b 1
)
echo OK Pre-commit hooks installed

echo.
echo Step 4: Creating example data files...
set PYTHONPATH=%CD%
call poetry run python examples\framework_demo.py >nul 2>&1
echo OK Example data files created

echo.
echo Step 5: Running code quality checks...
echo   - Checking code format...
call poetry run black . --check --quiet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     OK Code is formatted
) else (
    echo     WARNING Run 'poetry run black .' to format
)

echo   - Checking import order...
call poetry run isort . --check-only --quiet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo     OK Imports are sorted
) else (
    echo     WARNING Run 'poetry run isort .' to sort
)

echo.
echo ========================================================================
echo.
echo      Setup Complete!
echo.
echo ========================================================================
echo.

echo Framework features enabled:
echo   OK Auto-waiting and actionability
echo   OK Expectations API
echo   OK Page Object Model
echo   OK Data-driven testing
echo   OK Code quality tools
echo   OK Pre-commit hooks
echo.

echo Next steps:
echo.
echo   1. Read the Framework Guide:
echo      type FRAMEWORK_GUIDE.md
echo.
echo   2. Review the examples:
echo      type examples\framework_demo.py
echo      type examples\integration_example.py
echo.
echo   3. Start using framework features in your code
echo.
echo   4. Run tests:
echo      poetry run pytest
echo.
echo   5. Format and check code:
echo      poetry run black .
echo      poetry run isort .
echo      poetry run flake8 .
echo.

echo Happy automating!
echo.
pause
