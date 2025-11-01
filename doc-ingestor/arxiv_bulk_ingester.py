#!/usr/bin/env python3
"""
arXiv Bulk Metadata Ingester
Ingests papers from the arXiv bulk metadata snapshot (JSON Lines format)
into the DocTrove system.

Data source: arXiv metadata snapshot (Kaggle)
https://www.kaggle.com/datasets/Cornell-University/arxiv

This script processes the arxiv-metadata-oai-snapshot.json file which contains
metadata for all arXiv papers in JSON Lines format (one JSON object per line).
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import execute_batch

# Add parent directory to path for shared framework imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_SCRIPTS = os.path.dirname(SCRIPT_DIR)
sys.path.append(ROOT_SCRIPTS)

from doc_ingestor.shared_ingestion_framework import (
    PaperRecord,
    MetadataRecord,
    get_db_connection,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from shared framework during bulk operations
logging.getLogger('doc_ingestor.shared_ingestion_framework').setLevel(logging.WARNING)

BATCH_SIZE = 5000  # Process papers in batches for performance

def insert_paper_batch(papers_batch: List[tuple], metadata_batch: List[tuple], conn) -> tuple:
    """
    Insert a batch of papers and their metadata into the database.
    Uses ON CONFLICT DO NOTHING for efficient duplicate handling.
    
    Returns: (successful_inserts, errors)
    """
    successful = 0
    errors = 0
    
    cursor = conn.cursor()
    
    try:
        # Insert papers with ON CONFLICT DO NOTHING
        paper_insert_sql = """
            INSERT INTO doctrove_papers (
                doctrove_source,
                doctrove_source_id,
                title,
                authors,
                abstract,
                doctrove_primary_date,
                publication_url,
                pdf_url,
                tags,
                links
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (doctrove_source, doctrove_source_id) DO NOTHING
            RETURNING doctrove_paper_id;
        """
        
        # Track which papers were actually inserted
        inserted_paper_ids = []
        for paper_data in papers_batch:
            try:
                cursor.execute(paper_insert_sql, paper_data)
                result = cursor.fetchone()
                if result:
                    inserted_paper_ids.append((result[0], paper_data[1]))  # (uuid, source_id)
                    successful += 1
            except Exception as e:
                logger.error(f"Error inserting paper: {e}")
                errors += 1
                continue
        
        # Only insert metadata for successfully inserted papers
        if inserted_paper_ids:
            # Create a mapping from source_id to paper_id
            source_id_to_uuid = {source_id: uuid for uuid, source_id in inserted_paper_ids}
            
            # Update metadata batch with actual UUIDs
            metadata_insert_sql = """
                INSERT INTO arxiv_metadata (
                    doctrove_paper_id,
                    fields
                ) VALUES (%s, %s)
                ON CONFLICT (doctrove_paper_id) DO NOTHING;
            """
            
            for meta_data in metadata_batch:
                source_id = meta_data[2]  # Original source_id we stored temporarily
                if source_id in source_id_to_uuid:
                    actual_uuid = source_id_to_uuid[source_id]
                    try:
                        cursor.execute(metadata_insert_sql, (actual_uuid, meta_data[1]))
                    except Exception as e:
                        logger.error(f"Error inserting metadata: {e}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Batch insert error: {e}")
        conn.rollback()
        errors += len(papers_batch)
    finally:
        cursor.close()
    
    return successful, errors


def parse_arxiv_date(date_str: str) -> Optional[str]:
    """
    Parse arXiv date string to YYYY-MM-DD format.
    arXiv dates can be in various formats, most commonly 'YYYY-MM-DD' or 'Mon, DD MMM YYYY ...'
    """
    if not date_str:
        return None
    
    try:
        # Try direct parsing first (YYYY-MM-DD format)
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            return date_str
        
        # Try parsing RFC 2822 format: "Mon, 31 Dec 2007 13:57:39 GMT"
        try:
            dt = datetime.strptime(date_str.strip(), "%a, %d %b %Y %H:%M:%S %Z")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
        # Try other common formats
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # If all else fails, try to extract just the date part
        if ' ' in date_str:
            date_part = date_str.split()[0]
            return parse_arxiv_date(date_part)
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    except Exception as e:
        logger.warning(f"Error parsing date '{date_str}': {e}")
        return None


def extract_arxiv_id(id_str: str) -> str:
    """
    Extract clean arXiv ID from the full ID string.
    Examples:
        'http://arxiv.org/abs/0704.0001v1' -> '0704.0001'
        '1234.5678v2' -> '1234.5678'
    """
    # Remove URL prefix if present
    if 'arxiv.org/abs/' in id_str:
        id_str = id_str.split('arxiv.org/abs/')[-1]
    
    # Remove version suffix (e.g., 'v1', 'v2')
    if 'v' in id_str:
        parts = id_str.rsplit('v', 1)
        if len(parts) == 2 and parts[1].isdigit():
            id_str = parts[0]
    
    return id_str


def parse_authors(authors_data: Any) -> List[str]:
    """
    Parse authors from various formats in the arXiv data.
    Can be a list of strings, list of dicts, or a single string.
    """
    if not authors_data:
        return []
    
    if isinstance(authors_data, str):
        # Single author or comma-separated
        return [a.strip() for a in authors_data.split(',') if a.strip()]
    
    if isinstance(authors_data, list):
        authors = []
        for author in authors_data:
            if isinstance(author, str):
                authors.append(author.strip())
            elif isinstance(author, dict):
                # Handle parsed author objects with 'keyname' field
                name = author.get('keyname', '') or author.get('name', '') or str(author)
                authors.append(name.strip())
        return [a for a in authors if a]
    
    return []


def convert_to_paper_record(record: Dict[str, Any]) -> Optional[tuple]:
    """
    Convert an arXiv JSON record to database insert tuple.
    Returns tuple for paper insert and metadata insert.
    """
    try:
        # Extract and clean arXiv ID
        arxiv_id = extract_arxiv_id(record.get('id', ''))
        if not arxiv_id:
            logger.warning("Skipping record with no valid arXiv ID")
            return None
        
        # Parse authors
        authors_list = parse_authors(record.get('authors_parsed') or record.get('authors', []))
        
        # Parse dates - use versions field to get original submission date
        versions = record.get('versions', [])
        if versions and len(versions) > 0:
            # First version is the original submission
            created_date = parse_arxiv_date(versions[0].get('created', ''))
        else:
            # Fallback to update_date or other fields
            created_date = parse_arxiv_date(
                record.get('update_date') or 
                record.get('published') or 
                record.get('created', '')
            )
        
        if not created_date:
            logger.warning(f"Skipping {arxiv_id}: no valid date")
            return None
        
        # Extract categories/tags
        categories = record.get('categories', '')
        if isinstance(categories, str):
            tags = [cat.strip() for cat in categories.split() if cat.strip()]
        else:
            tags = list(categories) if categories else []
        
        # Build URLs
        publication_url = f"https://arxiv.org/abs/{arxiv_id}"
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        # Extract links from metadata
        links = {}
        if 'doi' in record and record['doi']:
            links['doi'] = record['doi']
        if 'journal-ref' in record and record['journal-ref']:
            links['journal_ref'] = record['journal-ref']
        
        # Prepare metadata fields
        metadata_fields = {
            'submitter': record.get('submitter'),
            'categories': record.get('categories'),
            'comments': record.get('comments'),
            'journal_ref': record.get('journal-ref'),
            'doi': record.get('doi'),
            'report_no': record.get('report-no'),
            'license': record.get('license'),
            'versions': record.get('versions'),
            'update_date': record.get('update_date'),
            'authors_parsed': record.get('authors_parsed'),
        }
        
        # Remove None values
        metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}
        
        # Create paper insert tuple
        paper_data = (
            'arxiv',                          # doctrove_source
            arxiv_id,                        # doctrove_source_id
            record.get('title', '').strip(), # title
            authors_list,                    # authors (array)
            record.get('abstract', '').strip(), # abstract
            created_date,                    # doctrove_primary_date
            publication_url,                 # publication_url
            pdf_url,                        # pdf_url
            tags,                           # tags (array)
            json.dumps(links) if links else None  # links (JSONB)
        )
        
        # Create metadata insert tuple (temporarily store source_id for later UUID mapping)
        metadata_data = (
            None,  # Will be replaced with actual UUID after paper insert
            json.dumps(metadata_fields),  # fields (JSONB)
            arxiv_id  # Temporary: store source_id for UUID mapping
        )
        
        return (paper_data, metadata_data)
        
    except Exception as e:
        logger.error(f"Error converting record to paper: {e}")
        return None


def process_arxiv_bulk_file(
    file_path: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    categories: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> Dict[str, int]:
    """
    Process the arXiv bulk metadata file.
    
    Args:
        file_path: Path to the JSON Lines file
        start_year: Only process papers from this year onwards
        end_year: Only process papers up to this year
        start_date: Only process papers from this date onwards (YYYY-MM-DD)
        end_date: Only process papers up to this date (YYYY-MM-DD)
        categories: Only process papers in these categories (e.g., ['cs.AI', 'cs.LG'])
        limit: Maximum number of papers to process (for testing)
    
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'total_lines': 0,
        'filtered_out': 0,
        'processed': 0,
        'successful': 0,
        'errors': 0
    }
    
    conn = get_db_connection()
    
    papers_batch = []
    metadata_batch = []
    
    try:
        logger.info(f"Opening bulk file: {file_path}")
        logger.info(f"Filters: year={start_year}-{end_year}, date={start_date}-{end_date}, categories={categories}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                stats['total_lines'] = line_num
                
                # Progress logging (reduced verbosity)
                if line_num % 100000 == 0:
                    logger.info(f"   📊 Read {line_num:,} lines, processed {stats['processed']:,} papers so far...")
                
                # Check limit before processing
                if limit and stats['processed'] >= limit:
                    logger.info(f"Reached limit of {limit} papers")
                    break
                
                try:
                    record = json.loads(line.strip())
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_num}: {e}")
                    stats['errors'] += 1
                    continue
                
                # Apply filters
                skip = False
                
                # Date filters
                versions = record.get('versions', [])
                if versions and len(versions) > 0:
                    created_date = parse_arxiv_date(versions[0].get('created', ''))
                else:
                    created_date = parse_arxiv_date(
                        record.get('update_date') or 
                        record.get('published') or 
                        record.get('created', '')
                    )
                
                if created_date:
                    # Year filter
                    if start_year or end_year:
                        year = int(created_date[:4])
                        if start_year and year < start_year:
                            skip = True
                        if end_year and year > end_year:
                            skip = True
                    
                    # Date range filter
                    if start_date and created_date < start_date:
                        skip = True
                    if end_date and created_date > end_date:
                        skip = True
                
                # Category filter
                if categories:
                    record_categories = record.get('categories', '')
                    if isinstance(record_categories, str):
                        record_cats = set(record_categories.split())
                    else:
                        record_cats = set(record_categories)
                    
                    if not any(cat in record_cats for cat in categories):
                        skip = True
                
                if skip:
                    stats['filtered_out'] += 1
                    continue
                
                # Convert to paper record
                result = convert_to_paper_record(record)
                if result:
                    paper_data, metadata_data = result
                    papers_batch.append(paper_data)
                    metadata_batch.append(metadata_data)
                    stats['processed'] += 1
                    
                    # Check limit after adding to batch
                    if limit and stats['processed'] >= limit:
                        logger.info(f"Reached limit of {limit} papers")
                        break
                else:
                    stats['errors'] += 1
                
                # Process batch when it reaches BATCH_SIZE
                if len(papers_batch) >= BATCH_SIZE:
                    successful, errors = insert_paper_batch(papers_batch, metadata_batch, conn)
                    stats['successful'] += successful
                    stats['errors'] += errors
                    
                    # Reduced verbosity - only log every 1000 papers
                    if stats['processed'] % 1000 == 0:
                        logger.info(f"   ✅ Processed {stats['processed']:,} papers (batch: +{successful}, errors: {errors})")
                    
                    papers_batch = []
                    metadata_batch = []
                    
                    # Check limit after batch processing
                    if limit and stats['processed'] >= limit:
                        break
        
        # Process final batch
        if papers_batch:
            successful, errors = insert_paper_batch(papers_batch, metadata_batch, conn)
            stats['successful'] += successful
            stats['errors'] += errors
            logger.info(f"   ✅ Final batch: Processed {stats['processed']:,} papers total")
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise
    finally:
        conn.close()
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Ingest arXiv bulk metadata into DocTrove',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all papers from 2025
  python arxiv_bulk_ingester.py --file arxiv-metadata-oai-snapshot.json --start-year 2025

  # Ingest CS papers from 2023-2024
  python arxiv_bulk_ingester.py --file arxiv-metadata-oai-snapshot.json \\
      --start-year 2023 --end-year 2024 --categories cs.AI cs.LG

  # Test with first 100 papers
  python arxiv_bulk_ingester.py --file arxiv-metadata-oai-snapshot.json --limit 100
        """
    )
    
    parser.add_argument(
        '--file',
        required=True,
        help='Path to arXiv metadata JSON Lines file'
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        help='Only process papers from this year onwards'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        help='Only process papers up to this year'
    )
    
    parser.add_argument(
        '--start-date',
        help='Only process papers from this date onwards (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        help='Only process papers up to this date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        help='Only process papers in these categories (e.g., cs.AI cs.LG)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of papers to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("arXiv Bulk Metadata Ingestion")
    logger.info("=" * 80)
    
    # Process the file
    stats = process_arxiv_bulk_file(
        file_path=args.file,
        start_year=args.start_year,
        end_year=args.end_year,
        start_date=args.start_date,
        end_date=args.end_date,
        categories=args.categories,
        limit=args.limit
    )
    
    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ arXiv Bulk Ingestion Complete")
    logger.info("=" * 80)
    logger.info(f"Records read:       {stats['total_lines']:,}")
    logger.info(f"Filtered out:       {stats['filtered_out']:,}")
    logger.info(f"Successfully ingested: {stats['successful']:,}")
    logger.info(f"Errors:             {stats['errors']:,}")
    logger.info("")
    logger.info("📊 Papers will be automatically enriched with:")
    logger.info("   - Vector embeddings (1536-d semantic search)")
    logger.info("   - 2D projections (UMAP visualization)")
    logger.info("")
    logger.info("Monitor enrichment with:")
    logger.info("   screen -r enrichment_embeddings  # Vector embeddings")
    logger.info("   screen -r embedding_2d           # 2D projections")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
