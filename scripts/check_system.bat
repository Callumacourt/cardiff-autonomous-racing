@echo off
REM Cardiff Autonomous Racing - System Check (Windows)
REM Run this script to verify your setup before starting

echo 🏎️  Cardiff Autonomous Racing - System Check
echo ==============================================

REM Check Docker
echo.
echo 🔍 Checking Docker installation...
docker --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Docker found
    docker --version
) else (
    echo ❌ Docker not found! Please install Docker Desktop
    pause
    exit /b 1
)

REM Check Docker Compose
echo.
echo 🔍 Checking Docker Compose...
docker-compose --version >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Docker Compose found
    docker-compose --version
) else (
    echo ❌ Docker Compose not found! Please install Docker Desktop
    pause
    exit /b 1
)

REM Check Docker daemon
echo.
echo 🔍 Checking Docker daemon...
docker info >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo ✅ Docker daemon is running
) else (
    echo ❌ Docker daemon not running! Please start Docker Desktop
    pause
    exit /b 1
)

REM Check for docker-compose.yml
echo.
echo 🔍 Checking project files...
if exist "docker-compose.yml" (
    echo ✅ docker-compose.yml found
) else (
    echo ❌ docker-compose.yml not found! Are you in the right directory?
    pause
    exit /b 1
)

REM Check for main directories
if exist "Control" (
    echo ✅ Directory found: Control
) else (
    echo ⚠️  Directory missing: Control
)

if exist "docker" (
    echo ✅ Directory found: docker
) else (
    echo ⚠️  Directory missing: docker
)

if exist "Path Planning" (
    echo ✅ Directory found: Path Planning
) else (
    echo ⚠️  Directory missing: Path Planning
)

if exist "perception_ws" (
    echo ✅ Directory found: perception_ws
) else (
    echo ⚠️  Directory missing: perception_ws
)

echo.
echo 🎉 System check complete!
echo.
echo 🚀 Next steps:
echo 1. Run: docker-compose build
echo 2. Run: docker-compose up
echo 3. Watch the autonomous racing system start!
echo.
echo 📚 For detailed instructions, see: QUICK_START.md
echo.
pause
