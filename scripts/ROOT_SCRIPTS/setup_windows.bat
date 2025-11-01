@echo off
REM Master setup script for DocTrove/DocScope on Windows 10/11
REM This script automates installation of dependencies, PostgreSQL, Python, and project setup.
REM Run as Administrator for best results.

REM 1. Check for Chocolatey and install if missing
where choco >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing Chocolatey...
    powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Chocolatey. Exiting.
        exit /b 1
    )
)
echo [Check] Chocolatey is installed.

REM 2. Install Git, Python 3.10+, PostgreSQL 15+, and dependencies
choco install -y git python --version=3.10.14 postgresql15
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install core dependencies. Exiting.
    exit /b 1
)
echo [Check] Core dependencies installed.

REM 3. Add Python and PostgreSQL to PATH (if not already)
setx PATH "%PATH%;%ProgramFiles%\Python310;%ProgramFiles%\PostgreSQL\15\bin"

REM 4. Initialize and start PostgreSQL
cd /d "%ProgramFiles%\PostgreSQL\15\bin"
if not exist "%ProgramFiles%\PostgreSQL\15\data" (
    initdb -D "%ProgramFiles%\PostgreSQL\15\data" -U postgres -A password --pwfile=postgres
)
pg_ctl -D "%ProgramFiles%\PostgreSQL\15\data" -l logfile start

REM 5. Create pgvector extension and doctrove database
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -c "CREATE DATABASE doctrove;"
psql -U postgres -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo [Check] PostgreSQL and pgvector set up.

REM 6. Clone the project repository (replace with your repo URL)
if not exist arxivscope-back-end (
    git clone https://github.com/tgulden/arxivscope-back-end.git arxivscope-back-end
    echo [Check] Project repository cloned.
) else (
    echo [Check] Project repository already present.
)
cd arxivscope-back-end

REM 7. Set up Python virtual environment
python -m venv arxivscope
call arxivscope\Scripts\activate.bat
python -m pip install --upgrade pip

REM 8. Install Python dependencies
python -m pip install -r requirements.txt
python -m pip install -r doc-ingestor/requirements.txt
python -m pip install -r embedding-enrichment/requirements.txt
python -m pip install -r doctrove-api/requirements.txt

REM 9. Set up database schema (manual step if bash script is not supported)
echo [INFO] If you have WSL or Git Bash, run: bash "Design documents/setup_postgres_pgvector.sh"
echo [INFO] Otherwise, manually run the SQL in doctrove_schema.sql, embedding-enrichment/setup_database_functions.sql, and embedding-enrichment/event_triggers.sql using psql.  The last file is REQUIRED for enrichment triggers.

REM 10. Final check
psql -U postgres -d doctrove -c "\dt"

REM 11. Done
echo [SUCCESS] DocTrove/DocScope environment setup complete! Review output for any errors.
exit /b 0 