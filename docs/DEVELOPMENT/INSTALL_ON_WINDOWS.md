# DocTrove/DocScope Installation Guide for Windows 10/11

This guide describes how to install and configure DocTrove/DocScope on Windows 10/11. You can use the provided `setup_windows.bat` script to automate the process, or follow the steps manually.

---

## **Step 1: Install Chocolatey (if not present)**

Chocolatey is a Windows package manager. The script will install it if missing:
```bat
where choco >nul 2>nul
REM If not found, install with PowerShell:
powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
```
**Check:**
- `choco --version` should print a version number.

---

## **Step 2: Install Core Dependencies**

Install Git, Python 3.10+, and PostgreSQL 15+:
```bat
choco install -y git python --version=3.10.14 postgresql15
```
**Check:**
- `git --version`, `python --version`, and `psql --version` should all print version info.

---

## **Step 3: Add Python and PostgreSQL to PATH**

The script will add these to your PATH if needed:
```bat
setx PATH "%PATH%;%ProgramFiles%\Python310;%ProgramFiles%\PostgreSQL\15\bin"
```
**Check:**
- Open a new Command Prompt and run `python --version` and `psql --version`.

---

## **Step 4: Initialize and Start PostgreSQL**

Initialize the database and start the service:
```bat
cd /d "%ProgramFiles%\PostgreSQL\15\bin"
initdb -D "%ProgramFiles%\PostgreSQL\15\data" -U postgres -A password --pwfile=postgres
pg_ctl -D "%ProgramFiles%\PostgreSQL\15\data" -l logfile start
```
**Check:**
- `psql -U postgres -c "\l"` should list databases.

---

## **Step 5: Install pgvector Extension and Create Database**

Enable the extension and create the `doctrove` database:
```bat
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -c "CREATE DATABASE doctrove;"
psql -U postgres -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
**Check:**
- `psql -U postgres -d doctrove -c "\dx"` should list `vector` as installed.

---

## **Step 6: Clone the Project Repository**

Clone your project repository (replace with your repo URL):
```bat
git clone https://github.com/tgulden/arxivscope-back-end.git arxivscope-back-end
cd arxivscope-back-end
```