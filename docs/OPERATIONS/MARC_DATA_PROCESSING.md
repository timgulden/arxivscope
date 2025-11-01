# MARC Data Processing Guide

## Modern Ingestion Architecture: Shared Framework & Parallelization

### Overview

As of 2025, the MARC ingestion system uses a **shared functional ingestion framework** for all major data sources (MARC, OpenAlex, etc.). This approach provides:

- **Functional programming principles**: Pure transformation functions, immutable data structures, and clear separation of pure/impure code.
- **Testability**: All pure functions are unit tested.
- **Code reuse**: The same ingestion logic is used for MARC, OpenAlex, and other sources.
- **Parallelization**: Ingestion can be run in parallel across multiple MARC files if needed, but is typically run one file at a time due to file size and workflow.

### Key Components

- `shared_ingestion_framework.py`: Core ingestion logic, database operations, error handling, and functional patterns.
- `marc_ingester.py`: MARC-specific file reading, transformation, and metadata extraction, using the shared framework.
- `marc_to_json.py`: MARC file conversion with comprehensive field extraction and dual link generation.
- `test_marc_ingester.py`: Unit tests for all pure MARC ingestion functions.

### How Parallel Ingestion Works

- **Multiple files**: If you have multiple MARC files, you can use Python's `concurrent.futures.ProcessPoolExecutor` to run multiple ingester processes in parallel, each on a different file.
- **Single large file**: Typically processed as a single job, but you could split into chunks if needed.
- **Batch inserts**: The framework supports efficient, reliable inserts with proper error handling.

**Example: Parallel Ingestion Script**

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from marc_ingester import main as ingest_marc_file

def ingest_file(file_path):
    # You may want to call marc_ingester.py as a subprocess, or refactor main() to be callable
    return ingest_marc_file([str(file_path), '--source', 'randpub'])

if __name__ == '__main__':
    files = list(Path('data/marc-files/').glob('*.json'))
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(ingest_file, files))
    print('All MARC files ingested!')
```

### Design Principles

- **Functional programming**: All data transformations are pure functions.
- **Immutability**: Data structures are immutable for safety and testability.
- **Separation of concerns**: File reading, transformation, and database operations are clearly separated.
- **Testability**: All pure functions are unit tested (see `test_marc_ingester.py`).

## File Storage Strategy

### **Where to Store MARC Files**

```bash
# Create dedicated data directory in Documents
mkdir -p ~/Documents/doctrove-data/marc-files
mkdir -p ~/Documents/doctrove-data/processed
mkdir -p ~/Documents/doctrove-data/logs

# Move your MARC files here
mv /path/to/your/157mb-file.mrc ~/Documents/doctrove-data/marc-files/randpubs.mrc
mv /path/to/your/35mb-file.mrc ~/Documents/doctrove-data/marc-files/external_authors.mrc
```

### **Why Not in Repo?**

```yaml
Problems with putting in repo:
  - Git doesn't handle large binary files well
  - Repository becomes huge and slow
  - Version control overhead for data files
  - Potential for accidental commits
  - CI/CD pipeline slowdowns

Better approach:
  - Keep data separate from code
  - Use .gitignore to prevent accidental commits
  - Version control only processing scripts
  - Document data sources and formats
```

## Directory Structure

```bash
~/Documents/doctrove-data/
├── marc-files/                    # Raw MARC files
│   ├── randpubs.mrc      # 157MB RAND publications
│   └── external_authors.mrc       # 35MB external author papers
├── processed/                     # Processed data
│   ├── json/                      # Converted to JSON
│   ├── cleaned/                   # Cleaned and standardized
│   └── ready_for_ingestion/       # Final format for database
├── logs/                          # Processing logs
│   ├── marc_processing.log
│   └── error_reports.log
└── scripts/                       # Processing scripts
    ├── marc_to_json.py
    ├── data_cleaning.py
    └── validation.py
```

## MARC Processing Pipeline

### **Step 1: Install MARC Processing Tools**

```bash
# Install pymarc for MARC processing
pip install pymarc

# Optional: Install additional tools
pip install pandas
pip install tqdm  # for progress bars
```

### **Step 2: Create MARC Processing Script**

```python
#!/usr/bin/env python3
# ~/Documents/doctrove-data/scripts/marc_to_json.py

import pymarc
import json
import os
from datetime import datetime
from tqdm import tqdm

def process_marc_file(input_file, output_file, source_type):
    """
    Convert MARC file to JSON format for further processing
    """
    records = []
    error_count = 0
    
    print(f"Processing {input_file}...")
    
    with open(input_file, 'rb') as f:
        reader = pymarc.MARCReader(f)
        
        for record in tqdm(reader):
            try:
                processed_record = extract_marc_data(record, source_type)
                if processed_record:
                    records.append(processed_record)
            except Exception as e:
                error_count += 1
                print(f"Error processing record: {e}")
                continue
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2, default=str)
    
    print(f"Processed {len(records)} records, {error_count} errors")
    return records

def extract_marc_data(record, source_type):
    """
    Extract relevant data from MARC record
    """
    try:
        # Extract title
        title = ""
        if record.get('245'):
            title = record['245']['a']
            if record['245'].get('b'):
                title += " " + record['245']['b']
        
        # Extract authors
        authors = []
        for field in record.get_fields('100', '700'):  # Personal names
            if field.get('a'):
                authors.append(field['a'])
        
        # Extract abstract/summary
        abstract = ""
        if record.get('520'):
            abstract = record['520']['a']
        
        # Extract publication date
        pub_date = ""
        if record.get('260'):
            pub_date = record['260'].get('c', '')
        elif record.get('264'):
            pub_date = record['264'].get('c', '')
        
        # Extract DOI
        doi = ""
        for field in record.get_fields('024'):
            if field.get('2') == 'doi':
                doi = field.get('a', '')
        
        # Extract document type
        doc_type = ""
        if record.get('245'):
            doc_type = record['245'].get('h', '')
        
        # Extract RAND project info (if available)
        rand_project = ""
        for field in record.get_fields('500'):
            if 'RAND' in field.get('a', ''):
                rand_project = field['a']
        
        return {
            'title': title.strip(),
            'authors': [author.strip() for author in authors],
            'abstract': abstract.strip(),
            'publication_date': pub_date.strip(),
            'doi': doi.strip(),
            'document_type': doc_type.strip(),
            'rand_project': rand_project.strip(),
            'source_type': source_type,
            'marc_id': record.get('001', {}).get('data', ''),
            'processing_date': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error extracting data from MARC record: {e}")
        return None

if __name__ == "__main__":
    # Process RAND publications
    process_marc_file(
        '~/Documents/doctrove-data/marc-files/randpubs.mrc',
        '~/Documents/doctrove-data/processed/json/randpubs.json',
        'RAND_PUBLICATION'
    )
    
    # Process external author papers
    process_marc_file(
        '~/Documents/doctrove-data/marc-files/external_authors.mrc',
        '~/Documents/doctrove-data/processed/json/external_authors.json',
        'EXTERNAL_AUTHOR'
    )
```

### **Step 3: Data Cleaning Script**

```python
#!/usr/bin/env python3
# ~/Documents/doctrove-data/scripts/data_cleaning.py

import json
import re
from datetime import datetime
from typing import List, Dict

def clean_title(title: str) -> str:
    """Clean and standardize title"""
    if not title:
        return ""
    
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Remove common prefixes
    title = re.sub(r'^\[.*?\]\s*', '', title)
    
    return title

def clean_abstract(abstract: str) -> str:
    """Clean and standardize abstract"""
    if not abstract:
        return ""
    
    # Remove extra whitespace
    abstract = re.sub(r'\s+', ' ', abstract.strip())
    
    # Remove common prefixes
    abstract = re.sub(r'^Abstract:\s*', '', abstract, flags=re.IGNORECASE)
    
    return abstract

def parse_authors(authors: List[str]) -> List[str]:
    """Clean and standardize author names"""
    cleaned_authors = []
    
    for author in authors:
        if not author:
            continue
            
        # Remove extra whitespace
        author = re.sub(r'\s+', ' ', author.strip())
        
        # Remove common suffixes
        author = re.sub(r',?\s*(Ph\.D\.|PhD|Dr\.|Prof\.|Professor)\s*$', '', author, flags=re.IGNORECASE)
        
        if author and len(author) > 2:
            cleaned_authors.append(author)
    
    return cleaned_authors

def standardize_date(date_str: str) -> str:
    """Standardize publication date format"""
    if not date_str:
        return ""
    
    # Extract year from various formats
    year_match = re.search(r'(\d{4})', date_str)
    if year_match:
        return year_match.group(1)
    
    return ""

def deduplicate_records(records: List[Dict]) -> List[Dict]:
    """Remove duplicate records"""
    seen_titles = set()
    seen_dois = set()
    unique_records = []
    
    for record in records:
        title = record.get('title', '').lower()
        doi = record.get('doi', '').lower()
        
        # Skip if we've seen this title or DOI
        if title in seen_titles or (doi and doi in seen_dois):
            continue
        
        seen_titles.add(title)
        if doi:
            seen_dois.add(doi)
        
        unique_records.append(record)
    
    return unique_records

def clean_and_validate_data(input_file: str, output_file: str):
    """Main cleaning function"""
    print(f"Cleaning data from {input_file}...")
    
    with open(input_file, 'r') as f:
        records = json.load(f)
    
    cleaned_records = []
    
    for record in records:
        cleaned_record = {
            'title': clean_title(record.get('title', '')),
            'authors': parse_authors(record.get('authors', [])),
            'abstract': clean_abstract(record.get('abstract', '')),
            'publication_date': standardize_date(record.get('publication_date', '')),
            'doi': record.get('doi', '').strip(),
            'document_type': record.get('document_type', '').strip(),
            'rand_project': record.get('rand_project', '').strip(),
            'source_type': record.get('source_type', ''),
            'marc_id': record.get('marc_id', ''),
            'cleaning_date': datetime.now().isoformat()
        }
        
        # Only include records with essential data
        if cleaned_record['title'] and cleaned_record['abstract']:
            cleaned_records.append(cleaned_record)
    
    # Remove duplicates
    cleaned_records = deduplicate_records(cleaned_records)
    
    # Save cleaned data
    with open(output_file, 'w') as f:
        json.dump(cleaned_records, f, indent=2, default=str)
    
    print(f"Cleaned {len(cleaned_records)} records (from {len(records)} original)")
    return cleaned_records

if __name__ == "__main__":
    # Clean both datasets
    clean_and_validate_data(
        '~/Documents/doctrove-data/processed/json/randpubs.json',
        '~/Documents/doctrove-data/processed/cleaned/randpubs_cleaned.json'
    )
    
    clean_and_validate_data(
        '~/Documents/doctrove-data/processed/json/external_authors.json',
        '~/Documents/doctrove-data/processed/cleaned/external_authors_cleaned.json'
    )
```

## Processing Commands

### **Modern Ingestion Pipeline**

```bash
# Set up directory structure
mkdir -p ~/Documents/doctrove-data/{marc-files,processed/{json,cleaned,ready_for_ingestion},logs,scripts}

# Move your MARC files
mv /path/to/your/files/*.mrc ~/Documents/doctrove-data/marc-files/

# Run processing pipeline
cd ~/Documents/doctrove-data/scripts

# Step 1: Convert MARC to JSON (if needed)
python marc_to_json.py

# Step 2: Clean and validate data (if needed)
python data_cleaning.py

# Step 3: Ingest using the modern framework
python marc_ingester.py ~/Documents/doctrove-data/processed/cleaned/randpubs_cleaned.json --source randpub
python marc_ingester.py ~/Documents/doctrove-data/processed/cleaned/external_authors_cleaned.json --source extpub

# Step 4: Check results
echo "Processing complete. Check database for ingested papers."
```

### **Parallel Processing (Multiple Files)**

If you have multiple MARC files to process:

```bash
# Create a parallel processing script
cat > parallel_marc_ingestion.py << 'EOF'
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import subprocess

def ingest_file(file_path):
    source = 'randpub' if 'rand' in str(file_path).lower() else 'extpub'
    result = subprocess.run([
        'python', 'marc_ingester.py', 
        str(file_path), '--source', source
    ], capture_output=True, text=True)
    return result.returncode == 0

if __name__ == '__main__':
    files = list(Path('~/Documents/doctrove-data/processed/cleaned/').glob('*_cleaned.json'))
    with ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(ingest_file, files))
    print(f'Successfully processed {sum(results)} out of {len(files)} files')
EOF

# Run parallel ingestion
python parallel_marc_ingestion.py
```

## Integration with Existing Pipeline

### **Using the Modern Ingestion Framework**

The ingestion framework is designed for code reuse and easy extension to new data sources. All ingestion logic is written in a functional style for reliability and maintainability.

#### **For New MARC Ingestion Jobs**

Use `marc_ingester.py` for all new ingestion jobs:

```bash
# Basic usage
python marc_ingester.py path/to/marc_file.json --source randpub

# With limit for testing
python marc_ingester.py path/to/marc_file.json --source randpub --limit 100

# For external publications
python marc_ingester.py path/to/external_file.json --source extpub
```

#### **For Legacy Integration**

If you need to integrate with existing processed data:

```python
# Load cleaned data and use the shared framework
from shared_ingestion_framework import process_file_unified, get_default_config
from marc_ingester import transform_marc_record, extract_marc_metadata

def ingest_legacy_processed_data(json_file_path, source_name):
    """Ingest legacy processed MARC data using the shared framework"""
    
    config = get_default_config()
    metadata_fields = ['publication_date', 'doi', 'document_type', 'rand_project']
    
    result = process_file_unified(
        file_path=json_file_path,
        source_name=source_name,
        transformer=transform_marc_record,
        metadata_extractor=extract_marc_metadata,
        config_provider=lambda: config,
        metadata_fields=metadata_fields
    )
    
    print(f"Inserted {result.inserted_count} papers from {result.total_processed} processed")
    return result
```

#### **Design Principles**

- **Functional programming**: All data transformations are pure functions.
- **Immutability**: Data structures are immutable for safety and testability.
- **Separation of concerns**: File reading, transformation, and database operations are clearly separated.
- **Testability**: All pure functions are unit tested (see `test_marc_ingester.py`).

## File Size Management

```yaml
File Sizes:
  - Raw MARC files: 157MB + 35MB = 192MB
  - Processed JSON: ~100-150MB
  - Final cleaned data: ~80-120MB
  
Storage Strategy:
  - Keep raw MARC files for reference
  - Process to JSON for easier handling
  - Clean and validate before ingestion
  - Archive raw files after successful processing
```

## Best Practices

1. **Keep data separate** from code repository
2. **Document data sources** and processing steps
3. **Version control** only the processing scripts
4. **Backup raw data** before processing
5. **Log all processing steps** for reproducibility
6. **Validate data quality** at each step
7. **Use consistent naming** conventions

## Modern MARC Ingestion Features (2025)

### **Dual Links Feature**

MARC ingestion now generates **both internal and external links** for publications:

- **Primo Catalog Links**: For RAND network users (`Library Catalog (Internal)`)
- **Public Website Links**: From MARC 856 field for external users (`Public Website`, `Full Text`)

```json
"doctrove_links": [
  {
    "href": "https://rand.primo.exlibrisgroup.com/permalink/01RAND_INST/8jidjm/alma991000650459707956",
    "title": "Library Catalog (Internal)"
  },
  {
    "href": "http://www.rand.org/pubs/drafts/DRU2769/",
    "title": "Public Website"
  }
]
```

### **Stable Source ID Management**

The system now uses **stable, deterministic identifiers** to prevent duplicate papers:

#### **Source ID Hierarchy**
1. **RAND/External Publications**: MARC 001 control number
2. **OpenAlex Papers**: OpenAlex work ID 
3. **arXiv Papers**: arXiv paper ID
4. **Legacy**: Hash-based IDs (being phased out)

#### **Duplicate Prevention**
- Records without stable IDs are skipped during ingestion
- Unique constraint on `(doctrove_source, doctrove_source_id)`
- Automatic conflict detection and resolution

### **Comprehensive MARC Field Extraction**

The `marc_to_json.py` script extracts extensive metadata:

```yaml
Core Fields:
  - 245: Title (with subtitle)
  - 100/700: Authors (personal names)
  - 520: Abstract/Summary
  - 260/264: Publication date
  - 024: DOI (when subfield 2 = "doi")

Enhanced Fields:
  - 001: Control number (for stable IDs)
  - 099: Local call number
  - 536: Funding information
  - 610: Corporate names
  - 650: Subject headings
  - 500: General notes
  - 037: Source acquisition
  - 925: Local processing notes
  - 981: Local data
  - 856: Electronic links (public access)
```

### **Current Processing Commands**

#### **RAND Publications**
```bash
# Convert MARC to JSON with dual links
python marc_to_json.py --randpub-file RANDPUB_20250707.mrc --output-dir data/processed

# Ingest with metadata
python marc_ingester.py data/processed/randpubs.json --source randpub
```

#### **External Publications**
```bash
# Convert MARC to JSON with dual links
python marc_to_json.py --extpub-file EXTPUB_20250707.mrc --output-dir data/processed

# Ingest with metadata  
python marc_ingester.py data/processed/external_publications.json --source extpub
```

### **Quality Assurance**

#### **Data Validation**
- MARC 001 control number validation
- Duplicate detection before insertion
- Link validation and formatting
- Metadata completeness checks

#### **Monitoring Commands**
```bash
# Check paper counts by source
psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "
SELECT doctrove_source, COUNT(*) as total_papers, 
       COUNT(CASE WHEN doctrove_links LIKE '%primo.exlibris%' THEN 1 END) as primo_links,
       COUNT(CASE WHEN doctrove_links LIKE '%rand.org%' THEN 1 END) as public_links
FROM doctrove_papers GROUP BY doctrove_source;"

# Check source ID stability
psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "
SELECT doctrove_source,
       COUNT(CASE WHEN doctrove_source_id LIKE '%PUBLICATION_%' THEN 1 END) as hash_based,
       COUNT(CASE WHEN doctrove_source_id NOT LIKE '%PUBLICATION_%' THEN 1 END) as stable_ids
FROM doctrove_papers GROUP BY doctrove_source;"
```

This approach keeps your repository clean while giving you a robust pipeline for processing the MARC data! 