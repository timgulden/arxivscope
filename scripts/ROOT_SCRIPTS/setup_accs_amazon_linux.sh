#!/bin/bash
# Master setup script for DocTrove/DocScope on Amazon Linux (ACCS)
# This script installs all dependencies, sets up PostgreSQL + pgvector, Python, and the project environment.
# Run as root or with sudo privileges.

set -e
set -o pipefail

LOG=setup_accs_install.log
exec > >(tee -i $LOG)
exec 2>&1

# 1. Update system packages
echo "[Step 1] Updating system packages..."
sudo yum update -y

echo "[Check] System packages updated."

# 2. Install core dependencies
echo "[Step 2] Installing core dependencies..."
sudo yum install -y git gcc make wget curl openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel

echo "[Check] Core dependencies installed."

# 3. Install Python 3.10+ (from source if not present)
PYTHON_VERSION=$(python3.10 --version 2>/dev/null || true)
if [[ "$PYTHON_VERSION" == "Python 3.10."* ]]; then
    echo "[Check] Python 3.10 already installed."
else
    echo "[Step 3] Installing Python 3.10 from source..."
    cd /usr/src
    sudo wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
    sudo tar xzf Python-3.10.14.tgz
    cd Python-3.10.14
    sudo ./configure --enable-optimizations
    sudo make altinstall
    cd ~
    echo "[Check] Python 3.10 installed."
fi

# 4. Install PostgreSQL 15+ and start service
echo "[Step 4] Installing PostgreSQL 15..."
sudo tee /etc/yum.repos.d/pgdg.repo<<EOF
[pgdg15]
name=PostgreSQL 15 for RHEL/CentOS 7 - x86_64
baseurl=https://download.postgresql.org/pub/repos/yum/15/redhat/rhel-7-x86_64
enabled=1
gpgcheck=0
EOF

sudo yum install -y postgresql15 postgresql15-server postgresql15-contrib postgresql15-devel
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb || true
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15
sudo systemctl status postgresql-15 --no-pager

echo "[Check] PostgreSQL 15 installed and running."

# 5. Install pgvector extension
echo "[Step 5] Installing pgvector extension..."
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "[Check] pgvector extension installed."

# 6. Create database and user
echo "[Step 6] Creating doctrove database and user..."
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='doctrove';")
if [[ "$DB_EXISTS" == "1" ]]; then
    echo "[Check] Database 'doctrove' already exists."
else
    sudo -u postgres createdb doctrove
    echo "[Check] Database 'doctrove' created."
fi
sudo -u postgres psql -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 7. Clone the project repository (replace with your repo URL)
echo "[Step 7] Cloning project repository..."
if [ ! -d "arxivscope-back-end" ]; then
    git clone https://github.com/tgulden/arxivscope-back-end.git arxivscope-back-end
    echo "[Check] Project repository cloned."
else
    echo "[Check] Project repository already present."
fi
cd arxivscope-back-end

# 8. Set up Python virtual environment
echo "[Step 8] Setting up Python virtual environment..."
if [ ! -d "arxivscope" ]; then
    python3.10 -m venv arxivscope
    echo "[Check] Virtual environment created."
else
    echo "[Check] Virtual environment already exists."
fi
source arxivscope/bin/activate
pip install --upgrade pip

# 9. Install Python dependencies
echo "[Step 9] Installing Python dependencies..."
pip install -r requirements.txt
pip install -r doc-ingestor/requirements.txt
pip install -r embedding-enrichment/requirements.txt
pip install -r doctrove-api/requirements.txt

echo "[Check] Python dependencies installed."

# 10. Set up database schema
echo "[Step 10] Setting up database schema..."
bash "Design documents/setup_postgres_pgvector.sh"
echo "[Check] Database schema set up."

# 11. Final check
echo "[Step 11] Final checks..."
psql -d doctrove -c "\dt"

# 12. Done
echo "[SUCCESS] DocTrove/DocScope environment setup complete!"
echo "Check $LOG for full output and troubleshooting."
exit 0 