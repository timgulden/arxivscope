#!/bin/bash
# Linux Configuration for DocScope/DocTrove

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
elif [ -f /etc/redhat-release ]; then
    DISTRO="rhel"
elif [ -f /etc/debian_version ]; then
    DISTRO="debian"
else
    DISTRO="unknown"
fi

# Platform-specific variables for Linux
export PLATFORM="linux"
export LINUX_DISTRO="$DISTRO"
export SSH_KEY_DIR="$HOME/.ssh"
export VENV_ACTIVATION="source arxivscope/bin/activate"
export PROJECT_ROOT="$(pwd)"

# Set package manager based on distribution
case "$DISTRO" in
    "ubuntu"|"debian")
        export PACKAGE_MANAGER="apt"
        export POSTGRESQL_INSTALL_CMD="sudo apt install -y postgresql-15 postgresql-contrib-15 postgresql-server-dev-15"
        export POSTGRESQL_START_CMD="sudo systemctl start postgresql"
        export POSTGRESQL_STOP_CMD="sudo systemctl stop postgresql"
        export POSTGRESQL_STATUS_CMD="sudo systemctl status postgresql"
        export UPDATE_CMD="sudo apt update"
        export UPGRADE_CMD="sudo apt upgrade -y"
        ;;
    "centos"|"rhel"|"fedora")
        export PACKAGE_MANAGER="yum"
        export POSTGRESQL_INSTALL_CMD="sudo yum install -y postgresql15 postgresql15-server postgresql15-devel"
        export POSTGRESQL_START_CMD="sudo systemctl start postgresql"
        export POSTGRESQL_STOP_CMD="sudo systemctl stop postgresql"
        export POSTGRESQL_STATUS_CMD="sudo systemctl status postgresql"
        export UPDATE_CMD="sudo yum update -y"
        export UPGRADE_CMD="sudo yum upgrade -y"
        ;;
    *)
        export PACKAGE_MANAGER="unknown"
        export POSTGRESQL_INSTALL_CMD="echo 'Manual installation required for $DISTRO'"
        export POSTGRESQL_START_CMD="echo 'Manual start required for $DISTRO'"
        export POSTGRESQL_STOP_CMD="echo 'Manual stop required for $DISTRO'"
        export POSTGRESQL_STATUS_CMD="echo 'Manual status check required for $DISTRO'"
        export UPDATE_CMD="echo 'Manual update required for $DISTRO'"
        export UPGRADE_CMD="echo 'Manual upgrade required for $DISTRO'"
        ;;
esac

# pgvector configuration (same for all Linux distributions)
export PGVECTOR_INSTALL_CMD="cd /tmp && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && cd pgvector && make && sudo make install"

# SSH configuration
export SSH_CMD="ssh -i $SSH_KEY_DIR/your-key.pem"
export SCP_CMD="scp -i $SSH_KEY_DIR/your-key.pem"

# File paths
export DATA_DIR="$PROJECT_ROOT/data"
export LOGS_DIR="$PROJECT_ROOT/logs"
export CONFIG_DIR="$PROJECT_ROOT/config"

# Python configuration
export PYTHON_CMD="python3"
export PIP_CMD="pip3"

# Docker configuration
export DOCKER_CMD="docker"
export DOCKER_COMPOSE_CMD="docker-compose"

# System commands
export SUDO_CMD="sudo"

echo "Linux configuration loaded"
echo "  Platform: $PLATFORM"
echo "  Distribution: $DISTRO"
echo "  Package Manager: $PACKAGE_MANAGER"
echo "  SSH Key Directory: $SSH_KEY_DIR"
echo "  Project Root: $PROJECT_ROOT" 