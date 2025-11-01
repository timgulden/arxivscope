# DocTrove/DocScope Installation Guide for Amazon Linux (ACCS)

This guide describes how to install and configure DocTrove/DocScope on an Amazon Linux (ACCS) cloud instance. You can use the provided `setup_accs_amazon_linux.sh` script to automate the process, or follow the steps manually.

---

## **Step 1: Update System Packages**

Update all system packages to the latest versions:
```bash
sudo yum update -y
```
**Check:** No errors, prompt returns to shell.

---

## **Step 2: Install Core Dependencies**

Install essential build and development tools:
```bash
sudo yum install -y git gcc make wget curl openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel
```
**Check:**
- `git --version`, `gcc --version`, `curl --version` should all print version info.

---

## **Step 3: Install Python 3.10+**

If Python 3.10 is not already installed, build it from source:
```bash
# Check if Python 3.10 is present
python3.10 --version
# If not, run:
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
sudo tar xzf Python-3.10.14.tgz
cd Python-3.10.14
sudo ./configure --enable-optimizations
sudo make altinstall
cd ~
```
**Check:**
- `python3.10 --version` should print `Python 3.10.x`.

---

## **Step 4: Install PostgreSQL 15+**

Add the PostgreSQL repository and install PostgreSQL 15:
```bash
sudo tee /etc/yum.repos.d/pgdg.repo<<EOF
[pgdg15]
name=PostgreSQL 15 for RHEL/CentOS 7 - x86_64
baseurl=https://download.postgresql.org/pub/repos/yum/15/redhat/rhel-7-x86_64
enabled=1
gpgcheck=0
EOF

sudo yum install -y postgresql15 postgresql15-server postgresql15-contrib postgresql15-devel
sudo /usr/pgsql-15/bin/postgresql-15-setup initdb
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15
sudo systemctl status postgresql-15 --no-pager
```
**Check:**
- `sudo systemctl status postgresql-15` should show "active (running)".

---

## **Step 5: Install pgvector Extension**

Enable the pgvector extension in PostgreSQL:
```bash
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
**Check:**
- `sudo -u postgres psql -c "\dx"` should list `vector` as installed.

---

## **Step 6: Create Database and User**

Create the `doctrove` database and ensure the extension is enabled:
```bash
sudo -u postgres createdb doctrove
sudo -u postgres psql -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
**Check:**
- `sudo -u postgres psql -d doctrove -c "\dt"` should show no tables (yet).

---

## **Step 7: Clone the Project Repository**

Clone your project repository (replace with your repo URL):
```bash
git clone https://github.com/tgulden/arxivscope-back-end.git arxivscope-back-end
cd arxivscope-back-end
```