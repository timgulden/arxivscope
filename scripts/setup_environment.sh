#!/bin/bash
# Unified Environment Setup Script for DocScope/DocTrove
# This script automatically detects the platform and loads the appropriate configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect platform
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) echo "windows";;
        *)          echo "unknown";;
    esac
}

# Load platform-specific configuration
load_platform_config() {
    local platform=$(detect_platform)
    local config_dir="$(dirname "$0")/../config"
    
    print_status "Detected platform: $platform"
    
    case "$platform" in
        "macos")
            if [ -f "$config_dir/macos.sh" ]; then
                source "$config_dir/macos.sh"
                print_success "macOS configuration loaded"
            else
                print_error "macOS configuration file not found: $config_dir/macos.sh"
                exit 1
            fi
            ;;
        "linux")
            if [ -f "$config_dir/linux.sh" ]; then
                source "$config_dir/linux.sh"
                print_success "Linux configuration loaded"
            else
                print_error "Linux configuration file not found: $config_dir/linux.sh"
                exit 1
            fi
            ;;
        "windows")
            print_warning "Windows detected - PowerShell configuration available at: $config_dir/windows.ps1"
            print_warning "For Windows, please run: . $config_dir/windows.ps1"
            print_warning "Or use Git Bash for bash-compatible commands"
            exit 1
            ;;
        *)
            print_error "Unsupported platform: $platform"
            exit 1
            ;;
    esac
}

# Verify required tools
verify_requirements() {
    print_status "Verifying platform requirements..."
    
    # Check for package manager
    case "$PACKAGE_MANAGER" in
        "brew")
            if ! command -v brew &> /dev/null; then
                print_error "Homebrew not found. Please install Homebrew first: https://brew.sh/"
                exit 1
            fi
            ;;
        "apt")
            if ! command -v apt &> /dev/null; then
                print_error "apt package manager not found"
                exit 1
            fi
            ;;
        "yum")
            if ! command -v yum &> /dev/null; then
                print_error "yum package manager not found"
                exit 1
            fi
            ;;
        *)
            print_warning "Unknown package manager: $PACKAGE_MANAGER"
            ;;
    esac
    
    # Check for Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        print_error "Python not found. Please install Python 3.10+"
        exit 1
    fi
    
    # Check for Git
    if ! command -v git &> /dev/null; then
        print_error "Git not found. Please install Git"
        exit 1
    fi
    
    print_success "Platform requirements verified"
}

# Setup virtual environment
setup_virtual_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "arxivscope" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv arxivscope
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    print_status "To activate the virtual environment, run:"
    echo "  $VENV_ACTIVATION"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment temporarily
    source arxivscope/bin/activate
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Core dependencies installed"
    fi
    
    # Install component-specific dependencies
    if [ -f "doc-ingestor/requirements.txt" ]; then
        pip install -r doc-ingestor/requirements.txt
        print_success "Doc-ingestor dependencies installed"
    fi
    
    if [ -f "embedding-enrichment/requirements.txt" ]; then
        pip install -r embedding-enrichment/requirements.txt
        print_success "Embedding-enrichment dependencies installed"
    fi
    
    if [ -f "doctrove-api/requirements.txt" ]; then
        pip install -r doctrove-api/requirements.txt
        print_success "DocTrove API dependencies installed"
    fi
    
    # Deactivate virtual environment
    deactivate
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$CONFIG_DIR"
    
    print_success "Directories created"
}

# Display setup summary
display_summary() {
    print_success "Environment setup completed!"
    echo
    echo "=== Setup Summary ==="
    echo "Platform: $PLATFORM"
    if [ "$PLATFORM" = "linux" ]; then
        echo "Distribution: $LINUX_DISTRO"
    fi
    echo "Package Manager: $PACKAGE_MANAGER"
    echo "Project Root: $PROJECT_ROOT"
    echo "SSH Key Directory: $SSH_KEY_DIR"
    echo
    echo "=== Next Steps ==="
    echo "1. Activate virtual environment:"
    echo "   $VENV_ACTIVATION"
    echo
    echo "2. Install PostgreSQL and pgvector:"
    echo "   $POSTGRESQL_INSTALL_CMD"
    echo "   $PGVECTOR_INSTALL_CMD"
    echo
    echo "3. Start PostgreSQL:"
    echo "   $POSTGRESQL_START_CMD"
    echo
    echo "4. Run database setup:"
    echo "   bash 'Design documents/setup_postgres_pgvector.sh'"
    echo
    echo "=== Available Commands ==="
    echo "SSH: $SSH_CMD"
    echo "SCP: $SCP_CMD"
    echo "Python: $PYTHON_CMD"
    echo "Pip: $PIP_CMD"
    echo "Docker: $DOCKER_CMD"
    echo "Docker Compose: $DOCKER_COMPOSE_CMD"
}

# Main function
main() {
    print_status "Starting DocScope/DocTrove environment setup..."
    
    # Load platform configuration
    load_platform_config
    
    # Verify requirements
    verify_requirements
    
    # Setup virtual environment
    setup_virtual_environment
    
    # Install dependencies
    install_dependencies
    
    # Create directories
    create_directories
    
    # Display summary
    display_summary
}

# Run main function
main "$@" 