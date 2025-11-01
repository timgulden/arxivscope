#!/bin/bash
# macOS Configuration for DocScope/DocTrove

# Platform-specific variables for macOS
export PLATFORM="macos"
export PACKAGE_MANAGER="brew"
export SSH_KEY_DIR="$HOME/.ssh"
export VENV_ACTIVATION="source arxivscope/bin/activate"
export PROJECT_ROOT="$(pwd)"

# PostgreSQL configuration
export POSTGRESQL_INSTALL_CMD="brew install postgresql"
export POSTGRESQL_START_CMD="brew services start postgresql"
export POSTGRESQL_STOP_CMD="brew services stop postgresql"
export POSTGRESQL_STATUS_CMD="brew services list | grep postgresql"

# pgvector configuration
export PGVECTOR_INSTALL_CMD="brew install pgvector"

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
export SUDO_CMD=""  # macOS doesn't typically need sudo for these operations
export UPDATE_CMD="brew update"
export UPGRADE_CMD="brew upgrade"

echo "macOS configuration loaded"
echo "  Platform: $PLATFORM"
echo "  Package Manager: $PACKAGE_MANAGER"
echo "  SSH Key Directory: $SSH_KEY_DIR"
echo "  Project Root: $PROJECT_ROOT" 