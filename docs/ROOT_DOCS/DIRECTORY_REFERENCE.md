# Directory Reference - ArXivScope Backend [Needs Update]

> This reference predates the React + TypeScript migration. Verify frontend paths and commands against `docs/DEVELOPMENT/REACT_TS_GUIDE.md` and `docs/README.md`.

## Key Directories

### Main Project Root
- **Location**: `./` (current directory where repo is cloned)
- **Purpose**: Main project directory containing all services
- **Key Files**: README.md, requirements.txt, .gitignore

### API Service
- **Location**: `./doctrove-api`
- **Purpose**: DocTrove REST API service (runs on port 5001)
- **Key Files**: api.py, config.py, enrichment.py
- **Start Command**: `cd doctrove-api && python api.py`

### Frontend Service  
- **Location**: `./docscope`
- **Purpose**: DocScope Dash frontend (legacy); migrating to React app
- **Key Files**: docscope.py, components/ (legacy)
- **Start Command**: `python -m docscope.app` (legacy); React app: see React guide

### Data Ingestion
- **Location**: `./doc-ingestor`
- **Purpose**: Data ingestion pipeline for papers
- **Key Files**: main.py, transformers.py, ingestor.py

### Embedding Enrichment
- **Location**: `./embedding-enrichment`
- **Purpose**: ML pipeline for embedding generation and clustering
- **Key Files**: enrichment.py, umap_model.pkl

### Configuration Files
- **Location**: `./config`
- **Purpose**: Platform-specific configuration files
- **Key Files**: macos.sh, windows.ps1, linux.sh

### Scripts
- **Location**: `./scripts`
- **Purpose**: Cross-platform utility scripts
- **Key Files**: detect_platform.sh, setup_environment.sh

## Common Commands

### Start API
```bash
cd doctrove-api
python api.py
```

### Start Frontend
```bash
cd docscope  
python docscope.py
```

### Test API Health
```bash
curl http://localhost:5001/api/health
```

### Test Frontend
```bash
curl http://localhost:8050
```

## Ports
- **API**: 5001 (DocTrove backend)
- **Frontend**: 8050 (DocScope frontend)

## Quick Check
If you're unsure which directory you're in:
```bash
pwd  # Shows current directory
ls   # Lists files in current directory
```

## Cross-Platform Setup

### Quick Environment Setup
```bash
# Run the unified setup script
./scripts/setup_environment.sh
```

### Platform Detection
```bash
# Check your platform
./scripts/detect_platform.sh info

# Get platform-specific commands
./scripts/detect_platform.sh postgresql-install
./scripts/detect_platform.sh ssh-cmd
```

### Platform-Specific Configuration
```bash
# macOS
source config/macos.sh

# Linux
source config/linux.sh

# Windows (PowerShell)
. config/windows.ps1
```

## Troubleshooting

### Directory Confusion
- **ALWAYS** start from the project root directory
- Use `pwd` to verify current directory
- Use `ls -la` to confirm you're in the right place

### Platform Issues
- Run `./scripts/detect_platform.sh info` to verify platform detection
- Check that your platform configuration file exists in `./config/`
- Ensure required tools (Python, Git, package manager) are installed 