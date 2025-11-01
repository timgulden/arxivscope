# Ingestion Organization

## 📁 File Organization

### **Core Ingestion Files** (in `doc-ingestor/`)
- **`main.py`** - Main ingestion entry point
- **`ingestor.py`** - Core ingestion logic
- **`main_ingestor.py`** - Main ingestion orchestration
- **`db.py`** - Database operations
- **`config.py`** - Configuration management
- **`source_configs.py`** - Source-specific configurations

### **Source-Specific Ingestors** (in `doc-ingestor/`)
- **`aipickle_ingester.py`** - AI Pickle data ingestion
- **`json_ingestor.py`** - JSON data ingestion
- **`marc_ingester.py`** - MARC data ingestion

### **Shared Framework** (in project root)
- **`shared_ingestion_framework.py`** - Shared ingestion logic and patterns
- **`openalex_ingester.py`** - OpenAlex data ingestion
- **`marc_ingester.py`** - MARC data ingestion (root level)

## 🔧 Import Paths

**Note**: Files in `doc-ingestor/` that need to access `shared_ingestion_framework.py` use:
```python
import sys
sys.path.append('..')  # Add parent directory to path
from shared_ingestion_framework import ...
```

## 🚀 Running Ingestion

### **From doc-ingestor directory:**
```bash
cd doc-ingestor/
python aipickle_ingester.py ../data/final_df_country.pkl
python json_ingestor.py ../data/sample.json
```

### **From project root:**
```bash
python doc-ingestor/aipickle_ingester.py data/final_df_country.pkl
python openalex_ingester.py data/openalex_sample.json
```

## 📝 Adding New Ingestors

When adding new ingestion sources:
1. **Place in `doc-ingestor/`** if it's a new source type
2. **Use `shared_ingestion_framework.py`** for common patterns
3. **Update this documentation** with the new ingestor
4. **Add appropriate tests** in the `tests/` directory

---

*This organization keeps related ingestion code together while maintaining access to shared frameworks.*


