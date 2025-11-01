# Windows PowerShell Configuration for DocScope/DocTrove

# Platform-specific variables for Windows
$env:PLATFORM = "windows"
$env:PACKAGE_MANAGER = "choco"
$env:SSH_KEY_DIR = "$env:USERPROFILE\.ssh"
$env:VENV_ACTIVATION = "arxivscope\Scripts\Activate.ps1"
$env:PROJECT_ROOT = (Get-Location).Path

# PostgreSQL configuration
$env:POSTGRESQL_INSTALL_CMD = "choco install postgresql -y"
$env:POSTGRESQL_START_CMD = "net start postgresql"
$env:POSTGRESQL_STOP_CMD = "net stop postgresql"
$env:POSTGRESQL_STATUS_CMD = "Get-Service postgresql"

# pgvector configuration (manual installation required)
$env:PGVECTOR_INSTALL_CMD = "Manual installation required - download from https://github.com/pgvector/pgvector/releases"

# SSH configuration
$env:SSH_CMD = "ssh -i $env:SSH_KEY_DIR\your-key.pem"
$env:SCP_CMD = "scp -i $env:SSH_KEY_DIR\your-key.pem"

# File paths
$env:DATA_DIR = "$env:PROJECT_ROOT\data"
$env:LOGS_DIR = "$env:PROJECT_ROOT\logs"
$env:CONFIG_DIR = "$env:PROJECT_ROOT\config"

# Python configuration
$env:PYTHON_CMD = "python"
$env:PIP_CMD = "pip"

# Docker configuration
$env:DOCKER_CMD = "docker"
$env:DOCKER_COMPOSE_CMD = "docker-compose"

# System commands
$env:SUDO_CMD = ""  # Windows doesn't use sudo
$env:UPDATE_CMD = "choco upgrade all -y"
$env:UPGRADE_CMD = "choco upgrade all -y"

Write-Host "Windows configuration loaded" -ForegroundColor Green
Write-Host "  Platform: $env:PLATFORM" -ForegroundColor Cyan
Write-Host "  Package Manager: $env:PACKAGE_MANAGER" -ForegroundColor Cyan
Write-Host "  SSH Key Directory: $env:SSH_KEY_DIR" -ForegroundColor Cyan
Write-Host "  Project Root: $env:PROJECT_ROOT" -ForegroundColor Cyan 