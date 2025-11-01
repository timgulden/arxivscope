#!/bin/bash
# Platform Detection Script for DocScope/DocTrove
# This script detects the current platform and provides platform-specific variables

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

# Detect operating system
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) echo "windows";;
        *)          echo "unknown";;
    esac
}

# Detect Linux distribution
detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# Get SSH key directory
get_ssh_key_path() {
    local platform=$(detect_platform)
    case "$platform" in
        "macos"|"linux") 
            echo "$HOME/.ssh"
            ;;
        "windows") 
            echo "$USERPROFILE/.ssh"
            ;;
        *) 
            echo "$HOME/.ssh"
            ;;
    esac
}

# Get package manager
get_package_manager() {
    local platform=$(detect_platform)
    case "$platform" in
        "macos")
            echo "brew"
            ;;
        "linux")
            local distro=$(detect_linux_distro)
            case "$distro" in
                "ubuntu"|"debian") echo "apt";;
                "centos"|"rhel"|"fedora") echo "yum";;
                *) echo "apt";;
            esac
            ;;
        "windows")
            echo "choco"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Get Python virtual environment activation command
get_venv_activation() {
    local platform=$(detect_platform)
    case "$platform" in
        "macos"|"linux")
            echo "source arxivscope/bin/activate"
            ;;
        "windows")
            echo "arxivscope\\Scripts\\Activate.ps1"
            ;;
        *)
            echo "source arxivscope/bin/activate"
            ;;
    esac
}

# Get PostgreSQL installation command
get_postgresql_install_cmd() {
    local platform=$(detect_platform)
    case "$platform" in
        "macos")
            echo "brew install postgresql"
            ;;
        "linux")
            local distro=$(detect_linux_distro)
            case "$distro" in
                "ubuntu"|"debian")
                    echo "sudo apt install postgresql-15 postgresql-contrib-15"
                    ;;
                "centos"|"rhel"|"fedora")
                    echo "sudo yum install postgresql15 postgresql15-server"
                    ;;
                *)
                    echo "sudo apt install postgresql-15 postgresql-contrib-15"
                    ;;
            esac
            ;;
        "windows")
            echo "choco install postgresql"
            ;;
        *)
            echo "echo 'Unknown platform for PostgreSQL installation'"
            ;;
    esac
}

# Get PostgreSQL service start command
get_postgresql_start_cmd() {
    local platform=$(detect_platform)
    case "$platform" in
        "macos")
            echo "brew services start postgresql"
            ;;
        "linux")
            echo "sudo systemctl start postgresql"
            ;;
        "windows")
            echo "net start postgresql"
            ;;
        *)
            echo "echo 'Unknown platform for PostgreSQL start'"
            ;;
    esac
}

# Get SSH connection command
get_ssh_cmd() {
    local platform=$(detect_platform)
    local key_path=$(get_ssh_key_path)
    case "$platform" in
        "macos"|"linux")
            echo "ssh -i $key_path/your-key.pem ubuntu@your-instance-ip"
            ;;
        "windows")
            echo "ssh -i $key_path\\your-key.pem ubuntu@your-instance-ip"
            ;;
        *)
            echo "ssh -i $key_path/your-key.pem ubuntu@your-instance-ip"
            ;;
    esac
}

# Get SCP command
get_scp_cmd() {
    local platform=$(detect_platform)
    local key_path=$(get_ssh_key_path)
    case "$platform" in
        "macos"|"linux")
            echo "scp -i $key_path/your-key.pem file.sql ubuntu@ip:/tmp/"
            ;;
        "windows")
            echo "scp -i $key_path\\your-key.pem file.sql ubuntu@ip:/tmp/"
            ;;
        *)
            echo "scp -i $key_path/your-key.pem file.sql ubuntu@ip:/tmp/"
            ;;
    esac
}

# Export all platform-specific variables
export_platform_vars() {
    local platform=$(detect_platform)
    local distro=$(detect_linux_distro)
    local package_manager=$(get_package_manager)
    local ssh_key_path=$(get_ssh_key_path)
    local venv_activation=$(get_venv_activation)
    
    export PLATFORM="$platform"
    export LINUX_DISTRO="$distro"
    export PACKAGE_MANAGER="$package_manager"
    export SSH_KEY_DIR="$ssh_key_path"
    export VENV_ACTIVATION="$venv_activation"
    export PROJECT_ROOT="$(pwd)"
    
    print_success "Platform detected: $platform"
    if [ "$platform" = "linux" ]; then
        print_success "Linux distribution: $distro"
    fi
    print_success "Package manager: $package_manager"
    print_success "SSH key directory: $ssh_key_path"
    print_success "Project root: $PROJECT_ROOT"
}

# Main function
main() {
    if [ "$1" = "export" ]; then
        export_platform_vars
    elif [ "$1" = "detect" ]; then
        detect_platform
    elif [ "$1" = "distro" ]; then
        detect_linux_distro
    elif [ "$1" = "package-manager" ]; then
        get_package_manager
    elif [ "$1" = "ssh-path" ]; then
        get_ssh_key_path
    elif [ "$1" = "venv-activation" ]; then
        get_venv_activation
    elif [ "$1" = "postgresql-install" ]; then
        get_postgresql_install_cmd
    elif [ "$1" = "postgresql-start" ]; then
        get_postgresql_start_cmd
    elif [ "$1" = "ssh-cmd" ]; then
        get_ssh_cmd
    elif [ "$1" = "scp-cmd" ]; then
        get_scp_cmd
    elif [ "$1" = "info" ]; then
        print_status "Platform Information:"
        echo "  Platform: $(detect_platform)"
        echo "  Linux Distro: $(detect_linux_distro)"
        echo "  Package Manager: $(get_package_manager)"
        echo "  SSH Key Path: $(get_ssh_key_path)"
        echo "  Project Root: $(pwd)"
        echo "  Virtual Env Activation: $(get_venv_activation)"
    else
        print_error "Usage: $0 {export|detect|distro|package-manager|ssh-path|venv-activation|postgresql-install|postgresql-start|ssh-cmd|scp-cmd|info}"
        echo ""
        echo "Commands:"
        echo "  export              - Export all platform variables"
        echo "  detect              - Detect platform only"
        echo "  distro              - Detect Linux distribution"
        echo "  package-manager     - Get package manager for platform"
        echo "  ssh-path            - Get SSH key directory"
        echo "  venv-activation     - Get virtual environment activation command"
        echo "  postgresql-install  - Get PostgreSQL installation command"
        echo "  postgresql-start    - Get PostgreSQL start command"
        echo "  ssh-cmd             - Get SSH connection command"
        echo "  scp-cmd             - Get SCP file transfer command"
        echo "  info                - Show all platform information"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 