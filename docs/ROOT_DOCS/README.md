# DocScope/DocTrove - Document Visualization Platform [Legacy]

> This README is retained for historical reference. For current docs, begin at `../README.md` and `../DEVELOPMENT/QUICK_START.md`. React + TypeScript migration guidance: `../DEVELOPMENT/REACT_TS_GUIDE.md`.

A comprehensive document visualization and exploration platform with AI-powered embeddings and 2D projections.

## 🚀 Quick Start

### For Individual Development
```bash
# Clone and setup
git clone <repository-url>
cd arxivscope-back-end
python -m venv arxivscope
source arxivscope/bin/activate  # Windows: arxivscope\Scripts\activate
pip install -r requirements.txt

# Start all services
./startup.sh --with-enrichment --background

# Open browser to http://localhost:8050
```

### For Team/Server Deployment
```bash
# Run team setup (requires sudo)
sudo ./scripts/server_setup_team.sh

# Add team members
sudo usermod -a -G arxivscope <username>

# Start services
cd /opt/arxivscope
./startup.sh --with-enrichment --background
```

## 📚 Documentation Guide

### **Start Here** (Choose One):
- **[Individual Setup](QUICK_START.md)** - For local development and testing
- **[Team Deployment](TEAM_DEPLOYMENT_GUIDE.md)** - For server deployment and team management

### **Service Management**:
- **[Service Commands](QUICK_REFERENCE.md)** - Essential commands and troubleshooting
- **[Startup Guide](STARTUP_GUIDE.md)** - Detailed startup procedures and options

### **Advanced Topics**:
- **[Performance Optimization](PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Database indexes and query optimization
- **[Data Ingestion](OPENALEX_INGESTION_GUIDE.md)** - Ingesting papers from various sources
- **[MARC Processing](MARC_DATA_PROCESSING.md)** - RAND/External publications with dual links
- **[Large Scale Ingestion](LARGE_SCALE_INGESTION_GUIDE.md)** - Processing up to 5M papers
- **[API Documentation](doctrove-api/API_DOCUMENTATION.md)** - Complete API reference

## 🏗️ System Architecture

- **`docscope/`** - Dash frontend for document visualization
- **`doctrove-api/`** - Flask API server (port 5001)
- **`embedding-enrichment/`** - 2D embedding generation service
- **`doc-ingestor/`** - Document ingestion pipeline

## 🔧 Essential Commands

```bash
# Start all services
./startup.sh --with-enrichment --background

# Check status
./check_services.sh

# Stop services
./stop_services.sh

# Restart everything
./startup.sh --with-enrichment --background --restart
```

## 🌐 Access Points

- **Frontend**: http://localhost:8050
- **API**: http://localhost:5001
- **API Health**: http://localhost:5001/api/health

## 📊 Performance Estimates

- **Embedding Generation**: ~50,000 papers/hour
- **Cost**: ~$10 per million papers (Azure OpenAI)
- **Database**: PostgreSQL with pgvector extension

## 🤝 Contributing

See [DEVELOPER_QUICK_REFERENCE.md](docscope/DEVELOPER_QUICK_REFERENCE.md) for development workflow and guidelines.

## 📋 System Requirements

- **Python 3.10+**
- **PostgreSQL 14+** with pgvector extension
- **Git** for version control
- **Virtual environment** (recommended)
