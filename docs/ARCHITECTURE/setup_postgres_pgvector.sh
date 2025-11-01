#!/bin/bash

# DocTrove PostgreSQL + pgvector setup script (Cross-Platform)
# This script installs PostgreSQL and pgvector, creates the doctrove database,
# enables the extension, and creates the initial tables.
# Run with: bash setup_postgres_pgvector.sh

set -e

# Source platform detection script if available
if [ -f "../scripts/detect_platform.sh" ]; then
    source "../scripts/detect_platform.sh"
    PLATFORM=$(detect_platform)
    PACKAGE_MANAGER=$(get_package_manager)
else
    # Fallback platform detection
    case "$(uname -s)" in
        Darwin*)    PLATFORM="macos"; PACKAGE_MANAGER="brew";;
        Linux*)     PLATFORM="linux"; PACKAGE_MANAGER="apt";;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) PLATFORM="windows"; PACKAGE_MANAGER="choco";;
        *)          PLATFORM="unknown"; PACKAGE_MANAGER="unknown";;
    esac
fi

echo "Detected platform: $PLATFORM"
echo "Using package manager: $PACKAGE_MANAGER"

# Function to install PostgreSQL based on platform
install_postgresql() {
    case "$PLATFORM" in
        "macos")
            if ! command -v brew &> /dev/null; then
                echo "Homebrew not found. Please install Homebrew first: https://brew.sh/"
                exit 1
            fi
            
            if ! brew list postgresql &> /dev/null; then
                echo "Installing PostgreSQL via Homebrew..."
                brew install postgresql
            else
                echo "PostgreSQL already installed via Homebrew."
            fi
            ;;
        "linux")
            # Detect Linux distribution
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO="$ID"
            else
                DISTRO="unknown"
            fi
            
            case "$DISTRO" in
                "ubuntu"|"debian")
                    echo "Installing PostgreSQL on Ubuntu/Debian..."
                    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
                    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
                    sudo apt update
                    sudo apt install -y postgresql-15 postgresql-contrib-15 postgresql-server-dev-15
                    ;;
                "centos"|"rhel"|"fedora")
                    echo "Installing PostgreSQL on CentOS/RHEL/Fedora..."
                    sudo yum install -y postgresql15 postgresql15-server postgresql15-devel
                    ;;
                *)
                    echo "Unsupported Linux distribution: $DISTRO"
                    echo "Please install PostgreSQL manually for your distribution."
                    exit 1
                    ;;
            esac
            ;;
        "windows")
            if ! command -v choco &> /dev/null; then
                echo "Chocolatey not found. Please install Chocolatey first: https://chocolatey.org/install"
                exit 1
            fi
            
            echo "Installing PostgreSQL via Chocolatey..."
            choco install postgresql -y
            ;;
        *)
            echo "Unsupported platform: $PLATFORM"
            echo "Please install PostgreSQL manually for your platform."
            exit 1
            ;;
    esac
}

# Function to start PostgreSQL service
start_postgresql() {
    case "$PLATFORM" in
        "macos")
            echo "Starting PostgreSQL service via Homebrew..."
            brew services start postgresql
            ;;
        "linux")
            echo "Starting PostgreSQL service..."
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
            ;;
        "windows")
            echo "Starting PostgreSQL service..."
            net start postgresql
            ;;
    esac
    sleep 2
}

# Function to install pgvector
install_pgvector() {
    case "$PLATFORM" in
        "macos")
            if ! brew list pgvector &> /dev/null; then
                echo "Installing pgvector via Homebrew..."
                brew install pgvector
            else
                echo "pgvector already installed via Homebrew."
            fi
            ;;
        "linux")
            echo "Installing pgvector from source..."
            cd /tmp
            git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
            cd pgvector
            make
            sudo make install
            cd -
            ;;
        "windows")
            echo "pgvector installation on Windows requires manual setup."
            echo "Please download from: https://github.com/pgvector/pgvector/releases"
            echo "and follow the Windows installation instructions."
            ;;
    esac
}

# Install PostgreSQL
install_postgresql

# Start PostgreSQL service
start_postgresql

# Install pgvector
install_pgvector

# 5. Create the doctrove database and enable pgvector
DB_NAME="doctrove"

# 6. Create SQL file for schema
SCHEMA_FILE="doctrove_schema.sql"
cat > $SCHEMA_FILE <<EOF
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main papers table
CREATE TABLE IF NOT EXISTS doctrove_papers (
    doctrove_paper_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctrove_source TEXT NOT NULL,
    doctrove_source_id TEXT NOT NULL,
    doctrove_title TEXT NOT NULL,
    doctrove_abstract TEXT,
    doctrove_authors TEXT[],
    doctrove_date_posted DATE,
    doctrove_date_published DATE,
    doctrove_title_embedding VECTOR(1536),
    doctrove_abstract_embedding VECTOR(1536),
    embedding_model_version TEXT DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(doctrove_source, doctrove_source_id)
);

-- Example enrichment table
CREATE TABLE IF NOT EXISTS arxivscope_metadata (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    arxivscope_country TEXT,
    arxivscope_category TEXT,
    arxivscope_processed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (doctrove_paper_id)
);

-- Enrichment registry
CREATE TABLE IF NOT EXISTS enrichment_registry (
    enrichment_name TEXT PRIMARY KEY,
    table_name TEXT NOT NULL,
    description TEXT,
    fields JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
EOF

# 7. Create database and run schema
if psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
  echo "Database $DB_NAME already exists."
else
  echo "Creating database $DB_NAME..."
  createdb $DB_NAME
fi

# 8. Apply schema
echo "Applying schema to $DB_NAME..."
psql -d $DB_NAME -f $SCHEMA_FILE

# 9. Done
echo "PostgreSQL + pgvector setup complete. Database: $DB_NAME" 