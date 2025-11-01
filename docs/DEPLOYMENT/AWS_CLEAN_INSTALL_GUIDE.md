# DocTrove/DocScope AWS Clean Install Guide (Fresh Database + Reingestion)

This guide walks you through deploying DocTrove/DocScope on a new AWS EC2 instance with a **clean, empty database** and reingesting all data from source files. No database migration is performed; all data is loaded fresh.

---

## **1. Launch and Prepare Your AWS EC2 Instance**
- Launch an Ubuntu 22.04 LTS (or similar) EC2 instance with at least 4 vCPUs, 16GB RAM, and 100GB+ storage.
- Open required ports (22, 80, 443, 5001, 8050) in your security group.
- SSH into your instance:
  ```bash
  ssh ubuntu@your-instance-ip
  ```

---

## **2. Install System Dependencies**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3.10 python3.10-venv python3-pip postgresql-15 postgresql-contrib-15 postgresql-server-dev-15 build-essential libpq-dev
```
**Check:**
- `psql --version` and `python3.10 --version` should print version info.

---

## **3. Set Up PostgreSQL and pgvector**

### **a. Switch to the postgres user**
```bash
sudo -u postgres psql
```

### **b. Create the database and user**
```sql
CREATE DATABASE doctrove;
CREATE USER doctrove_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE doctrove TO doctrove_admin;
\q
```

### **c. Enable the pgvector extension**
```bash
sudo -u postgres psql -d doctrove -c "CREATE EXTENSION IF NOT EXISTS vector;"
```
**Check:**
- `sudo -u postgres psql -d doctrove -c "\dx"` should list `vector` as installed.

---

## **4. Clone the Project Repository**
```bash
git clone https://github.com/tgulden/arxivscope-back-end.git
cd arxivscope-back-end
```
**Check:**
- `ls` should show the project files.

---

## **5. Set Up Python Virtual Environment**
```bash
python3.10 -m venv arxivscope
source arxivscope/bin/activate
pip install --upgrade pip
```
**Check:**
- Prompt should show `(arxivscope)` and `which python` should point to your venv.

---

## **6. Install Python Dependencies**
```bash
pip install -r requirements.txt
pip install -r doc-ingestor/requirements.txt
pip install -r embedding-enrichment/requirements.txt
pip install -r doctrove-api/requirements.txt
```
**Check:**
- No errors, and `pip list` shows installed packages.

---

## **7. Set Up Database Schema**
```bash
psql -U doctrove_admin -d doctrove -f "doctrove_schema.sql"
psql -U doctrove_admin -d doctrove -f "embedding-enrichment/setup_database_functions.sql"
psql -U doctrove_admin -d doctrove -f "embedding-enrichment/event_triggers.sql"  # REQUIRED for enrichment triggers
```
**Check:**
- `psql -U doctrove_admin -d doctrove -c "\dt"` should show your tables.

---

## **8. Copy Data Source Files to the Server**
- Use `scp` or `rsync` to copy your data files (MARC, JSON, pickle, etc.) to a dedicated directory, e.g.:
  ```bash
  mkdir -p /opt/doctrove/data/
  scp /path/to/your/datafile ubuntu@your-instance-ip:/opt/doctrove/data/
  ```
**Check:**
- `ls /opt/doctrove/data/` should show your data files.

---

## **9. Configure Environment Variables**
- Create a `.env` file in the project root with your database credentials:
  ```env
  DOC_TROVE_DB=doctrove
  DOC_TROVE_USER=doctrove_admin
  DOC_TROVE_PASSWORD=your_secure_password
  DOC_TROVE_HOST=localhost
  DOC_TROVE_PORT=5432
  ```
**Check:**
- `cat .env` should show your credentials.

---

## **10. Run the Ingestion Pipeline**
- Ingest your data using the appropriate command:
  ```bash
  # For pickle/JSON:
  python doc-ingestor/main.py --source aipickle --file-path /opt/doctrove/data/your_data_file.pkl
  # For MARC/JSON:
  python doc-ingestor/main_ingestor.py --source randpub --json-path /opt/doctrove/data/randpubs.json
  ```
**Check:**
- `psql -U doctrove_admin -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"` should show >0 records after ingestion.

---

## **11. Start Enrichment and Services**
- Start the enrichment system, API, and frontend as per your standard workflow.

---

## **12. Verification**
- Check API and frontend health endpoints.
- Check logs for errors.
- Validate that all expected data is present in the database.

---

**You now have a clean, production-ready DocTrove/DocScope deployment on AWS with a fresh database and reingested data!** 