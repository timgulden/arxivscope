# Cross-Platform Development Guide

## Overview

This guide addresses platform-specific issues in our documentation and provides unified instructions that work across **macOS**, **Windows**, and **Linux** for all team members.

## Platform-Specific Issues Identified

### **❌ Current Problems**

1. **Mac-Centric Paths**: Hardcoded `/Users/tgulden/Documents/` paths
2. **Homebrew Dependencies**: macOS-specific package manager
3. **SSH Key Paths**: Unix-style `~/.ssh/` paths
4. **Shell Commands**: Bash-specific syntax
5. **File Separators**: Unix-style forward slashes
6. **Environment Activation**: Different commands per platform

### **✅ Solutions Implemented**

1. **Relative Paths**: Use project-relative paths instead of absolute
2. **Cross-Platform Package Managers**: Support for multiple package managers
3. **Platform Detection**: Automatic platform-specific instructions
4. **Unified Commands**: Platform-agnostic command syntax
5. **Environment Variables**: Use `$HOME` and `$PROJECT_ROOT`

---

## Platform-Agnostic Setup Instructions

### **1. Project Structure (All Platforms)**

```bash
# Instead of hardcoded paths, use relative paths
PROJECT_ROOT="$(pwd)"  # Current directory where repo is cloned
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"
CONFIG_DIR="$PROJECT_ROOT/config"
```

### **2. Database Setup (Cross-Platform)**

#### **Option A: Docker (Recommended - All Platforms)**
```bash
# Works on macOS, Windows, Linux
docker-compose -f docker-compose.prod.yml up -d postgres
```

#### **Option B: Native Installation**

**macOS (Homebrew):**
```bash
brew install postgresql pgvector
brew services start postgresql
```

**Windows (Chocolatey):**
```powershell
choco install postgresql
# Install pgvector manually from source
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql-15 postgresql-contrib-15
# Install pgvector from source
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install postgresql15 postgresql15-server
# Install pgvector from source
```

### **3. Python Environment (Cross-Platform)**

#### **Virtual Environment Creation**
```bash
# All platforms
python -m venv arxivscope

# Activation
# macOS/Linux:
source arxivscope/bin/activate

# Windows (Command Prompt):
arxivscope\Scripts\activate.bat

# Windows (PowerShell):
arxivscope\Scripts\Activate.ps1
```

#### **Dependencies Installation**
```bash
# All platforms
pip install -r requirements.txt
```

### **4. SSH and Remote Access (Cross-Platform)**

#### **SSH Key Management**
```bash
# Generate SSH key (all platforms)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Key location (platform-specific)
# macOS/Linux: ~/.ssh/id_rsa
# Windows: C:\Users\YourUser\.ssh\id_rsa
```

#### **SSH Connection (Cross-Platform)**
```bash
# macOS/Linux
ssh -i ~/.ssh/your-key.pem ubuntu@your-instance-ip

# Windows (PowerShell)
ssh -i C:\Users\YourUser\.ssh\your-key.pem ubuntu@your-instance-ip

# Windows (Git Bash)
ssh -i ~/.ssh/your-key.pem ubuntu@your-instance-ip
```

### **5. File Operations (Cross-Platform)**

#### **Path Handling**
```bash
# Use platform-agnostic path construction
PROJECT_ROOT="$(pwd)"
DATA_FILE="$PROJECT_ROOT/data/papers.pkl"
CONFIG_FILE="$PROJECT_ROOT/config/settings.py"

# Instead of hardcoded paths like:
# /Users/tgulden/Documents/ArXivScope/arxivscope-back-end/
```

#### **File Copy Operations**
```bash
# Cross-platform file copy
# macOS/Linux:
scp -i ~/.ssh/your-key.pem file.sql ubuntu@ip:/tmp/

# Windows (PowerShell):
scp -i C:\Users\YourUser\.ssh\your-key.pem file.sql ubuntu@ip:/tmp/

# Windows (Git Bash):
scp -i ~/.ssh/your-key.pem file.sql ubuntu@ip:/tmp/
```

---

## Updated Documentation Structure

### **1. Platform Detection Scripts**

Create platform detection scripts that automatically choose the right commands:

```bash
#!/bin/bash
# detect_platform.sh

detect_platform() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) echo "windows";;
        *)          echo "unknown";;
    esac
}

get_ssh_key_path() {
    local platform=$(detect_platform)
    case "$platform" in
        "macos"|"linux") echo "$HOME/.ssh";;
        "windows") echo "$USERPROFILE/.ssh";;
        *) echo "$HOME/.ssh";;
    esac
}
```

### **2. Cross-Platform Configuration Files**

#### **Environment Setup Script**
```bash
#!/bin/bash
# setup_environment.sh

# Detect platform
PLATFORM=$(detect_platform)

# Set platform-specific variables
case "$PLATFORM" in
    "macos")
        PACKAGE_MANAGER="brew"
        SSH_KEY_DIR="$HOME/.ssh"
        ;;
    "linux")
        PACKAGE_MANAGER="apt"
        SSH_KEY_DIR="$HOME/.ssh"
        ;;
    "windows")
        PACKAGE_MANAGER="choco"
        SSH_KEY_DIR="$USERPROFILE/.ssh"
        ;;
esac

# Export for use in other scripts
export PLATFORM
export PACKAGE_MANAGER
export SSH_KEY_DIR
```

### **3. Updated Documentation Templates**

#### **Before (Mac-Centric):**
```bash
# Install PostgreSQL
brew install postgresql

# SSH to server
ssh -i ~/.ssh/your-key.pem ubuntu@ip

# Navigate to project
cd /Users/tgulden/Documents/ArXivScope/arxivscope-back-end
```

#### **After (Cross-Platform):**
```bash
# Install PostgreSQL
case "$PLATFORM" in
    "macos") brew install postgresql ;;
    "linux") sudo apt install postgresql-15 ;;
    "windows") choco install postgresql ;;
esac

# SSH to server
ssh -i "$SSH_KEY_DIR/your-key.pem" ubuntu@ip

# Navigate to project
cd "$PROJECT_ROOT"
```

---

## Implementation Plan

### **Phase 1: Core Documentation Updates**

1. **Update `README.md`**
   - Remove hardcoded paths
   - Add platform detection
   - Include Windows PowerShell commands

2. **Update `DATABASE_SETUP_GUIDE.md`**
   - Add Windows installation instructions
   - Include Chocolatey package manager
   - Add Linux distribution-specific commands

3. **Update `AWS_MIGRATION_GUIDE.md`**
   - Add Windows SSH instructions
   - Include PuTTY alternatives
   - Add Windows path handling

### **Phase 2: Script Updates**

1. **Create `detect_platform.sh`**
   - Platform detection logic
   - Path resolution functions
   - Package manager selection

2. **Update `setup_postgres_pgvector.sh`**
   - Add Windows support
   - Include Chocolatey installation
   - Add Linux distribution detection

3. **Create `setup_environment.sh`**
   - Cross-platform environment setup
   - Platform-specific variable export
   - Unified configuration

### **Phase 3: Configuration Files**

1. **Update `.env` templates**
   - Use relative paths
   - Platform-agnostic variables
   - Environment detection

2. **Create platform-specific configs**
   - `config.macos.sh`
   - `config.windows.ps1`
   - `config.linux.sh`

---

## Quick Reference: Platform-Specific Commands

### **Package Managers**
| Platform | Package Manager | Install Command |
|----------|----------------|-----------------|
| macOS | Homebrew | `brew install package` |
| Windows | Chocolatey | `choco install package` |
| Ubuntu/Debian | apt | `sudo apt install package` |
| CentOS/RHEL | yum | `sudo yum install package` |

### **SSH Key Locations**
| Platform | Default Location |
|----------|------------------|
| macOS | `~/.ssh/id_rsa` |
| Linux | `~/.ssh/id_rsa` |
| Windows | `C:\Users\YourUser\.ssh\id_rsa` |

### **Python Virtual Environment**
| Platform | Activation Command |
|----------|-------------------|
| macOS/Linux | `source venv/bin/activate` |
| Windows (CMD) | `venv\Scripts\activate.bat` |
| Windows (PowerShell) | `venv\Scripts\Activate.ps1` |

### **File Paths**
| Platform | Path Separator | Example |
|----------|----------------|---------|
| macOS/Linux | `/` | `/home/user/project` |
| Windows | `\` | `C:\Users\User\project` |

---

## Testing Checklist

### **Before Committing Changes**

- [ ] Test on macOS (Homebrew)
- [ ] Test on Windows (PowerShell + Chocolatey)
- [ ] Test on Ubuntu (apt)
- [ ] Test on CentOS (yum)
- [ ] Verify SSH connections work on all platforms
- [ ] Verify database setup works on all platforms
- [ ] Verify Python environment works on all platforms

### **Documentation Review**

- [ ] Remove all hardcoded paths
- [ ] Add platform detection where needed
- [ ] Include Windows PowerShell commands
- [ ] Add Linux distribution-specific instructions
- [ ] Verify all commands work cross-platform

---

## Benefits of Cross-Platform Approach

### **For Team Members**
- **Windows Users**: Can follow the same documentation as Mac/Linux users
- **Linux Users**: Get distribution-specific instructions
- **Mac Users**: Continue using familiar Homebrew commands

### **For Deployment**
- **AWS**: Works with Ubuntu instances
- **Azure**: Works with Windows Server instances
- **Local Development**: Works on any developer's machine

### **For Maintenance**
- **Single Source of Truth**: One set of documentation for all platforms
- **Easier Updates**: Changes apply to all platforms
- **Better Testing**: Can test on multiple platforms

---

**Next Steps**: Implement the platform detection scripts and update the core documentation files to be cross-platform compatible. 