# Database and Large File Cleanup Plan

## Current Problem
- Git repository is 2.1GB due to large files being committed
- Main culprits:
  - `embedding-enrichment/umap_model.pkl` (2.2GB)
  - `final_df_country.pkl` (42MB)
  - Virtual environment files in `arxivscope/` directory

## Immediate Actions (Tomorrow)

### 1. Update .gitignore
Add these patterns to `.gitignore`:
```
# Large data files
*.pkl
*.pickle
*.db
*.sqlite
*.sqlite3

# Virtual environment
arxivscope/
venv/
env/

# Log files
*.log

# Cache files
__pycache__/
*.pyc
*.pyo
*.pyd

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
```

### 2. Remove Large Files from Git History
```bash
# Remove files from Git tracking (but keep them locally)
git rm --cached embedding-enrichment/umap_model.pkl
git rm --cached final_df_country.pkl
git rm --cached -r arxivscope/

# Commit the removal
git commit -m "Remove large files from repository tracking"
```

### 3. Clean Git History (Optional but Recommended)
If you want to completely remove these files from Git history:
```bash
# Use git filter-branch or BFG Repo-Cleaner to remove large files from history
# This will rewrite Git history and require force push
```

### 4. Alternative: Use Git LFS
For files that need version control but are large:
```bash
# Install Git LFS
git lfs install

# Track large files with LFS
git lfs track "*.pkl"
git lfs track "*.pickle"
git lfs track "*.db"

# Add .gitattributes
git add .gitattributes
```

## Long-term Solutions

### 1. Data Storage Strategy
- **Development**: Use small sample datasets for testing
- **Production**: Store large files in cloud storage (S3, Azure Blob)
- **Backup**: Use database dumps and cloud backups instead of Git

### 2. Model Management
- Store trained models in model registries (MLflow, DVC)
- Use cloud storage for model artifacts
- Keep only model configuration in Git

### 3. Environment Management
- Use `requirements.txt` or `pyproject.toml` instead of committing virtual environment
- Use Docker for consistent environments
- Document setup process in README

## Implementation Steps

### Phase 1: Immediate Cleanup
1. Update `.gitignore`
2. Remove large files from tracking
3. Commit changes
4. Push to remote

### Phase 2: History Cleanup (Optional)
1. Use BFG Repo-Cleaner or git filter-branch
2. Force push to remote
3. Notify team members to re-clone

### Phase 3: Infrastructure Setup
1. Set up cloud storage for large files
2. Update code to load data from cloud storage
3. Create data loading scripts
4. Document new workflow

## Files to Keep in Repository
- Configuration files
- Schema definitions
- Small sample datasets for testing
- Documentation
- Code and scripts

## Files to Move to Cloud Storage
- Large pickle files (models, dataframes)
- Database files
- Log files
- Virtual environment directories

## Backup Strategy
- Regular database dumps to cloud storage
- Model versioning with MLflow or similar
- Configuration versioning in Git
- Documentation of data sources and processing steps 