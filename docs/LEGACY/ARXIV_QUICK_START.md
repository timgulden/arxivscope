# ArXiv Data Ingestion - Quick Start Guide

## For Lucas: Getting Started with 10K Records

### Prerequisites
- Python 3.8+
- PostgreSQL database running
- Your ArXiv JSON data file

### Step 1: Test the System
```bash
cd doc-ingestor
python test_arxiv_ingestion.py
```

This will test all components and generate sample data to verify everything works.

### Step 2: Prepare Your ArXiv Data
Your JSON file should have this structure:
```json
[
  {
    "id": "2401.00001",
    "title": "Paper Title",
    "abstract": "Paper abstract...",
    "authors": ["Author 1", "Author 2"],
    "categories": ["cs.AI", "cs.LG"],
    "created": "2024-01-01",
    "updated": "2024-01-15",
    "doi": "10.1234/arxiv.2401.00001"
  }
]
```

### Step 3: Test with Your Data (10K records)
```bash
# Test with first 100 records
python main_ingestor.py your_arxiv_data.json --limit 100

# If successful, run with 10K records
python main_ingestor.py your_arxiv_data.json --limit 10000
```

### Step 4: Full Dataset (when ready)
```bash
# Run with full dataset
python main_ingestor.py your_arxiv_data.json --batch-size 500
```

## What the System Does

1. **Loads** your JSON file (supports both array and lines format)
2. **Validates** data structure matches ArXiv format
3. **Transforms** data to canonical schema
4. **Stores** in database with proper indexing

## Database Tables Created

- `doctrove_papers` - Main paper data
- `arxiv_metadata` - ArXiv-specific fields (categories, DOI, etc.)

## Expected Performance

- **10K records**: ~2-5 minutes
- **100K records**: ~15-30 minutes  
- **1M records**: ~2-4 hours

## Embedding Generation (Batch Processing)

- **Speed:** ~50,000 papers per hour (title + abstract) using Azure OpenAI API
- **Cost:** $10 per million papers (conservative estimate)
- **Examples:**
  - 1M papers: ~20 hours, $10
  - 5M papers: ~100 hours, $50
  - 10M papers: ~200 hours, $100

These estimates assume typical scientific metadata lengths and continuous operation. Actual performance may vary with text length, API rate limits, or infrastructure changes.

## Troubleshooting

### Common Issues

1. **"Missing required field"**: Check your JSON has `id`, `title`, `abstract`
2. **"Database connection failed"**: Check PostgreSQL is running
3. **"JSON format error"**: Ensure valid JSON (try `jq . your_file.json`)

### Data Format Issues

If your ArXiv data has different field names, edit `source_configs.py`:
```python
ARXIV_CONFIG = {
    'field_mappings': {
        'your_id_field': 'doctrove_source_id',
        'your_title_field': 'doctrove_title',
        # ... etc
    }
}
```

## Next Steps After 10K Test

1. **Verify data quality** in the frontend
2. **Check embeddings** (if you have them)
3. **Scale up** to full dataset
4. **Optimize** batch size if needed

## Questions?

- **Data format**: What does your ArXiv JSON look like?
- **Embeddings**: Do you have pre-computed embeddings?
- **Size**: How many records total?
- **Fields**: Any special ArXiv fields to preserve?

## Files Created for You

- `json_ingestor.py` - Generic JSON loading
- `source_configs.py` - ArXiv field mappings  
- `generic_transformers.py` - Data transformation
- `main_ingestor.py` - Generic ingestion entry point
- `test_arxiv_ingestion.py` - Test suite

## Quick Commands

```bash
# Test everything
python test_arxiv_ingestion.py

# Check your JSON format
python -c "import json; data=json.load(open('your_file.json')); print(f'Records: {len(data)}'); print('Fields:', list(data[0].keys()))"

# Ingest with progress
python main_ingestor.py your_file.json --limit 1000 --batch-size 200
```

The system is designed to be robust and handle large datasets efficiently. Start with the test, then scale up! 