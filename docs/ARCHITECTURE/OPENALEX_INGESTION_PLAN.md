# OpenAlex Ingestion Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for ingesting OpenAlex data into DocTrove, from initial proof-of-concept to full production with incremental daily updates.

## Phase 1: Proof of Concept (One Month Snapshot)

### 1.1 Environment Setup

```bash
# Create working directory
mkdir -p openalex_ingestion
cd openalex_ingestion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install boto3 psycopg2-binary pandas numpy requests
```

### 1.2 Download One Month of Data

```bash
# Set target month
MONTH=2025-05

# Preview size first
aws s3 ls --summarize --human-readable --no-sign-request \
          --recursive "s3://openalex/data/works/updated_date=${MONTH}-*"

# Download the month's data
aws s3 sync s3://openalex/data/works/ ./openalex_data/works \
     --no-sign-request \
     --exclude "*" --include "updated_date=${MONTH}-*/**"

# Verify download
find ./openalex_data/works -name "*.gz" | wc -l
```

### 1.3 Create OpenAlex Transformer

Create `openalex_transformer.py`:

```python
import gzip
import json
import pathlib
from typing import Dict, Any, Optional
from datetime import datetime

def flatten_abstract_index(abstract_inverted_index: Optional[Dict]) -> Optional[str]:
    """Convert OpenAlex's inverted abstract index to plaintext."""
    if not abstract_inverted_index:
        return None
    
    # Sort by position and reconstruct text
    words = []
    for word, positions in abstract_inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    
    words.sort(key=lambda x: x[0])
    return ' '.join(word for _, word in words)

def extract_authors(authorships: list) -> str:
    """Extract author names from authorships array."""
    if not authorships:
        return ""
    
    author_names = []
    for authorship in authorships:
        if 'author' in authorship and 'display_name' in authorship['author']:
            author_names.append(authorship['author']['display_name'])
    
    return '; '.join(author_names)

def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize OpenAlex date format to ISO format."""
    if not date_str:
        return None
    
    try:
        # Handle various OpenAlex date formats
        if 'T' in date_str:
            # ISO format with time
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Date only
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None

def transform_openalex_work(work_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform OpenAlex work to DocTrove format."""
    
    # Extract basic fields
    doctrove_data = {
        'doctrove_source': 'openalex',
        'doctrove_source_id': work_data.get('id', ''),
        'doctrove_title': work_data.get('display_name', ''),
        'doctrove_abstract': flatten_abstract_index(work_data.get('abstract_inverted_index')),
        'doctrove_authors': extract_authors(work_data.get('authorships', [])),
        'doctrove_primary_date': normalize_date(work_data.get('publication_date') or work_data.get('created_date')),
        'doctrove_date_posted': normalize_date(work_data.get('created_date')),
        'doctrove_date_published': normalize_date(work_data.get('publication_date')),
        'doctrove_links': json.dumps(work_data.get('open_access', {})),
        'country2': None,  # Will be enriched later
        'doi': work_data.get('doi', ''),
    }
    
    # Add optional fields
    if 'concepts' in work_data:
        concept_names = [c.get('display_name', '') for c in work_data['concepts'] if c.get('display_name')]
        doctrove_data['concepts'] = '; '.join(concept_names)
    
    return doctrove_data

def validate_work_data(work_data: Dict[str, Any]) -> bool:
    """Validate that work data has required fields."""
    required_fields = ['id', 'display_name']
    return all(field in work_data and work_data[field] for field in required_fields)
```

### 1.4 Create Ingestion Script

Create `ingest_openalex_month.py`:

```python
import gzip
import json
import pathlib
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Iterator, Dict, Any
from openalex_transformer import transform_openalex_work, validate_work_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAlexIngester:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
    
    def connect(self):
        """Establish database connection."""
        self.connection = psycopg2.connect(**self.db_config)
        logger.info("Connected to database")
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from database")
    
    def create_works_table_if_not_exists(self):
        """Create works table if it doesn't exist."""
        with self.connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS openalex_works (
                    id SERIAL PRIMARY KEY,
                    doctrove_source VARCHAR(50) NOT NULL,
                    doctrove_source_id VARCHAR(255) UNIQUE NOT NULL,
                    doctrove_title TEXT,
                    doctrove_abstract TEXT,
                    doctrove_authors TEXT,
                    doctrove_primary_date DATE,
                    doctrove_date_posted DATE,
                    doctrove_date_published DATE,
                    doctrove_links JSONB,
                    country2 VARCHAR(100),
                    doi VARCHAR(255),
                    concepts TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
            logger.info("Works table ready")
    
    def stream_works_from_files(self, data_dir: str) -> Iterator[Dict[str, Any]]:
        """Stream works from gzipped JSONL files."""
        data_path = pathlib.Path(data_dir)
        
        for gz_file in data_path.rglob("*.gz"):
            logger.info(f"Processing {gz_file}")
            
            with gzip.open(gz_file, 'rt', encoding='utf-8') as fh:
                for line_num, line in enumerate(fh, 1):
                    try:
                        work_data = json.loads(line.strip())
                        if validate_work_data(work_data):
                            yield work_data
                        else:
                            logger.warning(f"Invalid work data in {gz_file}:{line_num}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in {gz_file}:{line_num}: {e}")
                    except Exception as e:
                        logger.error(f"Error processing {gz_file}:{line_num}: {e}")
    
    def upsert_work(self, doctrove_data: Dict[str, Any]):
        """Insert or update work in database."""
        with self.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO openalex_works (
                    doctrove_source, doctrove_source_id, doctrove_title, 
                    doctrove_abstract, doctrove_authors, doctrove_primary_date,
                    doctrove_date_posted, doctrove_date_published, doctrove_links,
                    country2, doi, concepts, updated_at
                ) VALUES (
                    %(doctrove_source)s, %(doctrove_source_id)s, %(doctrove_title)s,
                    %(doctrove_abstract)s, %(doctrove_authors)s, %(doctrove_primary_date)s,
                    %(doctrove_date_posted)s, %(doctrove_date_published)s, %(doctrove_links)s,
                    %(country2)s, %(doi)s, %(concepts)s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (doctrove_source_id) 
                DO UPDATE SET
                    doctrove_title = EXCLUDED.doctrove_title,
                    doctrove_abstract = EXCLUDED.doctrove_abstract,
                    doctrove_authors = EXCLUDED.doctrove_authors,
                    doctrove_primary_date = EXCLUDED.doctrove_primary_date,
                    doctrove_date_posted = EXCLUDED.doctrove_date_posted,
                    doctrove_date_published = EXCLUDED.doctrove_date_published,
                    doctrove_links = EXCLUDED.doctrove_links,
                    country2 = EXCLUDED.country2,
                    doi = EXCLUDED.doi,
                    concepts = EXCLUDED.concepts,
                    updated_at = CURRENT_TIMESTAMP
            """, doctrove_data)
    
    def ingest_month(self, data_dir: str, batch_size: int = 1000):
        """Ingest one month of OpenAlex data."""
        logger.info(f"Starting ingestion from {data_dir}")
        
        self.connect()
        self.create_works_table_if_not_exists()
        
        processed_count = 0
        batch = []
        
        try:
            for work_data in self.stream_works_from_files(data_dir):
                doctrove_data = transform_openalex_work(work_data)
                batch.append(doctrove_data)
                
                if len(batch) >= batch_size:
                    for item in batch:
                        self.upsert_work(item)
                    self.connection.commit()
                    processed_count += len(batch)
                    logger.info(f"Processed {processed_count} works")
                    batch = []
            
            # Process remaining batch
            if batch:
                for item in batch:
                    self.upsert_work(item)
                self.connection.commit()
                processed_count += len(batch)
            
            logger.info(f"Ingestion complete. Total works processed: {processed_count}")
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            self.connection.rollback()
            raise
        finally:
            self.disconnect()

if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'doctrove',
        'user': 'tgulden',
        'password': 'your_password'
    }
    
    # Run ingestion
    ingester = OpenAlexIngester(db_config)
    ingester.ingest_month('./openalex_data/works')
```

### 1.5 Run Proof of Concept

```bash
# Run the ingestion
python ingest_openalex_month.py

# Verify results
psql -h localhost -U tgulden -d doctrove -c "SELECT COUNT(*) FROM openalex_works;"
psql -h localhost -U tgulden -d doctrove -c "SELECT doctrove_primary_date, COUNT(*) FROM openalex_works GROUP BY doctrove_primary_date ORDER BY doctrove_primary_date;"
```

## Phase 2: Schema Integration & Enrichment

### 2.1 Integrate with DocTrove Schema

Create `integrate_with_doctrove.py`:

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def integrate_openalex_to_doctrove(db_config: Dict[str, str]):
    """Integrate OpenAlex works into main DocTrove schema."""
    
    conn = psycopg2.connect(**db_config)
    
    try:
        with conn.cursor() as cur:
            # Insert OpenAlex works into main doctrove_papers table
            cur.execute("""
                INSERT INTO doctrove_papers (
                    doctrove_source, doctrove_source_id, doctrove_title,
                    doctrove_abstract, doctrove_authors, doctrove_primary_date,
                    doctrove_date_posted, doctrove_date_published, doctrove_links,
                    country2, doi
                )
                SELECT 
                    doctrove_source, doctrove_source_id, doctrove_title,
                    doctrove_abstract, doctrove_authors, doctrove_primary_date,
                    doctrove_date_posted, doctrove_date_published, doctrove_links,
                    country2, doi
                FROM openalex_works
                WHERE doctrove_source_id NOT IN (
                    SELECT doctrove_source_id FROM doctrove_papers 
                    WHERE doctrove_source = 'openalex'
                )
            """)
            
            inserted_count = cur.rowcount
            conn.commit()
            logger.info(f"Integrated {inserted_count} new OpenAlex works into DocTrove")
            
    except Exception as e:
        logger.error(f"Integration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'doctrove',
        'user': 'tgulden',
        'password': 'your_password'
    }
    
    integrate_openalex_to_doctrove(db_config)
```

### 2.2 Generate Embeddings

Create `generate_openalex_embeddings.py`:

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

def generate_embeddings_for_openalex(db_config: Dict[str, str]):
    """Generate embeddings for OpenAlex works that don't have them."""
    
    # Initialize embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    conn = psycopg2.connect(**db_config)
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get works without embeddings
            cur.execute("""
                SELECT doctrove_paper_id, doctrove_title, doctrove_abstract
                FROM doctrove_papers 
                WHERE doctrove_source = 'openalex'
                AND (title_embedding IS NULL OR abstract_embedding IS NULL)
                LIMIT 1000
            """)
            
            works = cur.fetchall()
            
            for work in works:
                # Generate title embedding
                if work['doctrove_title']:
                    title_embedding = model.encode(work['doctrove_title'])
                    title_embedding_array = f"[{','.join(map(str, title_embedding))}]"
                else:
                    title_embedding_array = None
                
                # Generate abstract embedding
                if work['doctrove_abstract']:
                    abstract_embedding = model.encode(work['doctrove_abstract'])
                    abstract_embedding_array = f"[{','.join(map(str, abstract_embedding))}]"
                else:
                    abstract_embedding_array = None
                
                # Update database
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET title_embedding = %s, abstract_embedding = %s
                    WHERE doctrove_paper_id = %s
                """, (title_embedding_array, abstract_embedding_array, work['doctrove_paper_id']))
            
            conn.commit()
            logger.info(f"Generated embeddings for {len(works)} works")
            
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'doctrove',
        'user': 'tgulden',
        'password': 'your_password'
    }
    
    generate_embeddings_for_openalex(db_config)
```

## Phase 3: API Integration

### 3.1 Create OpenAlex API Client

Create `openalex_api_client.py`:

```python
import requests
import json
import logging
from typing import Dict, List, Optional, Iterator
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OpenAlexAPIClient:
    def __init__(self, base_url: str = "https://api.openalex.org"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DocTrove/1.0 (mailto:your-email@example.com)'
        })
    
    def get_works_by_date_range(self, 
                               from_date: str, 
                               to_date: str, 
                               per_page: int = 200) -> Iterator[Dict]:
        """Get works updated in a date range."""
        
        url = f"{self.base_url}/works"
        params = {
            'filter': f'updated_date:>{from_date},updated_date:<{to_date}',
            'per_page': per_page,
            'cursor': '*'
        }
        
        while True:
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                if not results:
                    break
                
                for work in results:
                    yield work
                
                # Get next page cursor
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                
                params['cursor'] = next_cursor
                
            except requests.RequestException as e:
                logger.error(f"API request failed: {e}")
                break
    
    def get_work_by_id(self, work_id: str) -> Optional[Dict]:
        """Get a specific work by ID."""
        try:
            response = self.session.get(f"{self.base_url}/works/{work_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get work {work_id}: {e}")
            return None

def sync_recent_works(db_config: Dict[str, str], days_back: int = 1):
    """Sync recent works from OpenAlex API."""
    
    from openalex_transformer import transform_openalex_work
    from ingest_openalex_month import OpenAlexIngester
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    client = OpenAlexAPIClient()
    ingester = OpenAlexIngester(db_config)
    
    ingester.connect()
    ingester.create_works_table_if_not_exists()
    
    try:
        processed_count = 0
        
        for work_data in client.get_works_by_date_range(
            start_date.isoformat(), 
            end_date.isoformat()
        ):
            doctrove_data = transform_openalex_work(work_data)
            ingester.upsert_work(doctrove_data)
            processed_count += 1
            
            if processed_count % 100 == 0:
                ingester.connection.commit()
                logger.info(f"Processed {processed_count} works")
        
        ingester.connection.commit()
        logger.info(f"Sync complete. Processed {processed_count} works")
        
    finally:
        ingester.disconnect()

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'doctrove',
        'user': 'tgulden',
        'password': 'your_password'
    }
    
    sync_recent_works(db_config)
```

## Phase 4: Production Automation

### 4.1 Create Automated Sync Script

Create `automated_sync.py`:

```python
#!/usr/bin/env python3
"""
Automated OpenAlex sync script for production use.
"""

import schedule
import time
import logging
import os
from datetime import datetime
from openalex_api_client import sync_recent_works

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openalex_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def daily_sync():
    """Perform daily sync of OpenAlex data."""
    logger.info("Starting daily OpenAlex sync")
    
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'doctrove'),
            'user': os.getenv('DB_USER', 'tgulden'),
            'password': os.getenv('DB_PASSWORD', 'your_password')
        }
        
        sync_recent_works(db_config, days_back=1)
        logger.info("Daily sync completed successfully")
        
    except Exception as e:
        logger.error(f"Daily sync failed: {e}")

def main():
    """Main function to run the automated sync."""
    
    # Schedule daily sync at 2 AM
    schedule.every().day.at("02:00").do(daily_sync)
    
    logger.info("OpenAlex automated sync started")
    logger.info("Daily sync scheduled for 2:00 AM")
    
    # Run initial sync
    daily_sync()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
```

### 4.2 Create Systemd Service (Linux)

Create `/etc/systemd/system/openalex-sync.service`:

```ini
[Unit]
Description=OpenAlex Sync Service
After=network.target

[Service]
Type=simple
User=tgulden
WorkingDirectory=/path/to/your/project
Environment=DB_HOST=localhost
Environment=DB_PORT=5432
Environment=DB_NAME=doctrove
Environment=DB_USER=tgulden
Environment=DB_PASSWORD=your_password
ExecStart=/path/to/your/project/venv/bin/python automated_sync.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.3 Create Cron Job (Alternative)

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line for daily sync at 2 AM
0 2 * * * cd /path/to/your/project && /path/to/your/project/venv/bin/python sync_recent_works.py
```

## Phase 5: Monitoring & Maintenance

### 5.1 Create Health Check Script

Create `health_check.py`:

```python
#!/usr/bin/env python3
"""
Health check script for OpenAlex ingestion pipeline.
"""

import psycopg2
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def check_database_health(db_config: Dict[str, str]) -> Dict[str, Any]:
    """Check database health and statistics."""
    
    try:
        conn = psycopg2.connect(**db_config)
        
        with conn.cursor() as cur:
            # Check total works
            cur.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex'")
            total_works = cur.fetchone()[0]
            
            # Check recent additions
            yesterday = datetime.now().date() - timedelta(days=1)
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex' 
                AND created_at >= %s
            """, (yesterday,))
            recent_works = cur.fetchone()[0]
            
            # Check works without embeddings
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'openalex' 
                AND (title_embedding IS NULL OR abstract_embedding IS NULL)
            """)
            works_without_embeddings = cur.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'healthy',
                'total_works': total_works,
                'recent_works': recent_works,
                'works_without_embeddings': works_without_embeddings
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}

def check_api_health() -> Dict[str, Any]:
    """Check OpenAlex API health."""
    
    try:
        response = requests.get('https://api.openalex.org/works?per_page=1')
        response.raise_for_status()
        
        return {
            'status': 'healthy',
            'response_time': response.elapsed.total_seconds()
        }
        
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return {'status': 'unhealthy', 'error': str(e)}

def main():
    """Run health checks."""
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'doctrove',
        'user': 'tgulden',
        'password': 'your_password'
    }
    
    print("=== OpenAlex Ingestion Health Check ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Database health
    db_health = check_database_health(db_config)
    print("Database Health:")
    for key, value in db_health.items():
        print(f"  {key}: {value}")
    print()
    
    # API health
    api_health = check_api_health()
    print("API Health:")
    for key, value in api_health.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
```

## Configuration Management

### Environment Variables

Create `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=doctrove
DB_USER=tgulden
DB_PASSWORD=your_password

# OpenAlex Configuration
OPENALEX_API_BASE_URL=https://api.openalex.org
OPENALEX_USER_AGENT=DocTrove/1.0 (mailto:your-email@example.com)

# Sync Configuration
SYNC_DAYS_BACK=1
SYNC_BATCH_SIZE=1000
SYNC_SCHEDULE_TIME=02:00

# Logging
LOG_LEVEL=INFO
LOG_FILE=openalex_sync.log
```

## Testing Strategy

### 1. Unit Tests

Create `test_openalex_transformer.py`:

```python
import unittest
from openalex_transformer import transform_openalex_work, flatten_abstract_index

class TestOpenAlexTransformer(unittest.TestCase):
    
    def test_flatten_abstract_index(self):
        """Test abstract index flattening."""
        abstract_index = {
            "machine": [0, 5],
            "learning": [1, 6],
            "is": [2],
            "important": [3],
            "for": [4],
            "research": [7]
        }
        
        expected = "machine learning is important for machine learning research"
        result = flatten_abstract_index(abstract_index)
        self.assertEqual(result, expected)
    
    def test_transform_work(self):
        """Test work transformation."""
        work_data = {
            'id': 'https://openalex.org/W1234567890',
            'display_name': 'Test Paper',
            'abstract_inverted_index': {'test': [0], 'paper': [1]},
            'authorships': [{'author': {'display_name': 'John Doe'}}],
            'publication_date': '2023-01-15',
            'created_date': '2023-01-10'
        }
        
        result = transform_openalex_work(work_data)
        
        self.assertEqual(result['doctrove_source'], 'openalex')
        self.assertEqual(result['doctrove_source_id'], 'https://openalex.org/W1234567890')
        self.assertEqual(result['doctrove_title'], 'Test Paper')
        self.assertEqual(result['doctrove_abstract'], 'test paper')
        self.assertEqual(result['doctrove_authors'], 'John Doe')
        self.assertEqual(result['doctrove_primary_date'], '2023-01-15')

if __name__ == '__main__':
    unittest.main()
```

### 2. Integration Tests

Create `test_integration.py`:

```python
import unittest
import psycopg2
from ingest_openalex_month import OpenAlexIngester

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test database connection."""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'doctrove_test',
            'user': 'tgulden',
            'password': 'your_password'
        }
        
        self.ingester = OpenAlexIngester(self.db_config)
    
    def test_ingestion_pipeline(self):
        """Test complete ingestion pipeline."""
        # This would test the full pipeline with sample data
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'ingester'):
            self.ingester.disconnect()

if __name__ == '__main__':
    unittest.main()
```

## Performance Optimization

### 1. Database Indexes

```sql
-- Create indexes for better performance
CREATE INDEX idx_openalex_source_id ON doctrove_papers(doctrove_source_id) WHERE doctrove_source = 'openalex';
CREATE INDEX idx_openalex_primary_date ON doctrove_papers(doctrove_primary_date) WHERE doctrove_source = 'openalex';
CREATE INDEX idx_openalex_created_at ON doctrove_papers(created_at) WHERE doctrove_source = 'openalex';

-- Composite index for date range queries
CREATE INDEX idx_openalex_date_range ON doctrove_papers(doctrove_primary_date, doctrove_source) WHERE doctrove_source = 'openalex';
```

### 2. Batch Processing

```python
def batch_upsert_works(works_data: List[Dict], batch_size: int = 1000):
    """Batch upsert works for better performance."""
    
    conn = psycopg2.connect(**db_config)
    
    try:
        with conn.cursor() as cur:
            for i in range(0, len(works_data), batch_size):
                batch = works_data[i:i + batch_size]
                
                # Use executemany for batch insert
                cur.executemany("""
                    INSERT INTO openalex_works (...) VALUES (...)
                    ON CONFLICT (doctrove_source_id) DO UPDATE SET ...
                """, batch)
                
                conn.commit()
                logger.info(f"Processed batch {i//batch_size + 1}")
    
    finally:
        conn.close()
```

## Troubleshooting Guide

### Common Issues

1. **Memory Issues**: Reduce batch size or use streaming
2. **API Rate Limits**: Implement exponential backoff
3. **Database Connection Issues**: Use connection pooling
4. **Data Quality Issues**: Add validation and logging

### Monitoring Commands

```bash
# Check sync status
python health_check.py

# Monitor logs
tail -f openalex_sync.log

# Check database statistics
psql -h localhost -U tgulden -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex';"

# Check recent additions
psql -h localhost -U tgulden -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_source = 'openalex' AND created_at >= CURRENT_DATE - INTERVAL '1 day';"
```

## Conclusion

This implementation plan provides a complete roadmap from proof-of-concept to production-ready OpenAlex ingestion. The modular approach allows for incremental development and testing at each phase, while the final production setup ensures reliable, automated data synchronization.

Key success factors:
- Start small with one month of data
- Validate each phase before proceeding
- Implement proper error handling and monitoring
- Use batch processing for performance
- Maintain data quality through validation
- Plan for scale from the beginning 