#!/usr/bin/env python3
"""
arXiv Ingester - Download and ingest arXiv papers by date range
Uses arXiv OAI-PMH API for metadata access

Usage:
    python arxiv_ingester.py --year 2025                    # All 2025 papers
    python arxiv_ingester.py --from 2025-01-01 --to 2025-12-31
    python arxiv_ingester.py --year 2025 --categories cs.AI,cs.LG  # Specific categories
    python arxiv_ingester.py --year 2025 --limit 1000       # Test with 1000 papers
"""

import sys
import argparse
import time
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import shared framework
sys.path.append(str(Path(__file__).parent / 'ROOT_SCRIPTS'))
from shared_ingestion_framework import (
    process_file_unified, 
    get_default_config, 
    PaperRecord, 
    MetadataRecord,
    create_connection_factory,
    ensure_metadata_table_exists
)

# arXiv API configuration
ARXIV_API_BASE = "http://export.arxiv.org/api/query"
BATCH_SIZE = 1000  # Papers per database batch
REQUEST_DELAY = 3  # Seconds between API requests (be polite!)
API_MAX_RESULTS = 1000  # Max results per API call

def parse_arxiv_date(date_str: str) -> Optional[str]:
    """Parse arXiv date to ISO format."""
    try:
        # arXiv dates are in YYYY-MM-DD format
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y-%m-%d')
    except:
        try:
            # Try ISO format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return None

def fetch_arxiv_metadata_api(from_date: str, until_date: str, start_index: int = 0, max_results: int = 1000) -> Dict[str, Any]:
    """
    Fetch arXiv metadata using main API (Atom feed).
    
    Args:
        from_date: Start date (YYYYMMDD)
        until_date: End date (YYYYMMDD)
        start_index: Starting index for pagination
        max_results: Maximum results to fetch
        
    Returns:
        Dict with 'records' list and 'total_results' count
    """
    # Convert dates to YYYYMMDD format for arXiv API
    from_str = from_date.replace('-', '')
    until_str = until_date.replace('-', '')
    
    # Build search query for date range
    search_query = f"submittedDate:[{from_str}+TO+{until_str}]"
    
    params = {
        'search_query': search_query,
        'start': start_index,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'ascending'
    }
    
    try:
        response = requests.get(ARXIV_API_BASE, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse Atom XML
        root = ET.fromstring(response.content)
        
        # Get namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        # Extract total results
        total_elem = root.find('.//atom:totalResults', ns) or root.find('.//{http://a9.com/-/spec/opensearch/1.1/}totalResults')
        total_results = int(total_elem.text) if total_elem is not None else 0
        
        # Extract records
        records = []
        for entry in root.findall('.//atom:entry', ns):
            try:
                # Extract ID
                id_elem = entry.find('atom:id', ns)
                arxiv_id = id_elem.text.split('/abs/')[-1] if id_elem is not None else None
                
                # Extract title
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip() if title_elem is not None else None
                
                # Extract abstract
                summary_elem = entry.find('atom:summary', ns)
                abstract = summary_elem.text.strip() if summary_elem is not None else None
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())
                
                # Extract published date
                published_elem = entry.find('atom:published', ns)
                created = published_elem.text.split('T')[0] if published_elem is not None else None
                
                # Extract categories
                categories = []
                for cat in entry.findall('atom:category', ns):
                    term = cat.get('term')
                    if term:
                        categories.append(term)
                
                # Also check arxiv:primary_category
                primary_cat = entry.find('arxiv:primary_category', ns)
                if primary_cat is not None:
                    term = primary_cat.get('term')
                    if term and term not in categories:
                        categories.insert(0, term)
                
                paper_data = {
                    'id': arxiv_id,
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'categories': categories,
                    'created': created,
                }
                
                # Extract DOI if present
                doi_elem = entry.find('arxiv:doi', ns)
                if doi_elem is not None:
                    paper_data['doi'] = doi_elem.text
                
                # Extract journal ref if present
                journal_elem = entry.find('arxiv:journal_ref', ns)
                if journal_elem is not None:
                    paper_data['journal_ref'] = journal_elem.text
                
                if arxiv_id and title:
                    records.append(paper_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing entry: {e}")
                continue
        
        return {
            'records': records,
            'total_results': total_results
        }
        
    except Exception as e:
        logger.error(f"Error fetching from arXiv API: {e}")
        return {'records': [], 'total_results': 0}

def download_arxiv_papers_by_date(from_date: str, until_date: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Download arXiv papers for a date range using main API.
    
    Args:
        from_date: Start date (YYYY-MM-DD)
        until_date: End date (YYYY-MM-DD)
        limit: Maximum papers to download (for testing)
        
    Returns:
        List of paper metadata dictionaries
    """
    all_records = []
    start_index = 0
    batch_num = 0
    
    logger.info(f"📥 Downloading arXiv papers from {from_date} to {until_date}")
    if limit:
        logger.info(f"   Limit: {limit} papers")
    
    # First request to get total count
    result = fetch_arxiv_metadata_api(from_date, until_date, 0, 1)
    total_available = result['total_results']
    logger.info(f"📊 Total papers available: {total_available:,}")
    
    # Determine how many to fetch
    total_to_fetch = min(total_available, limit) if limit else total_available
    logger.info(f"📥 Will fetch: {total_to_fetch:,} papers")
    
    while len(all_records) < total_to_fetch:
        batch_num += 1
        remaining = total_to_fetch - len(all_records)
        batch_size = min(API_MAX_RESULTS, remaining)
        
        logger.info(f"📦 Fetching batch {batch_num} (start: {start_index}, size: {batch_size})...")
        
        result = fetch_arxiv_metadata_api(from_date, until_date, start_index, batch_size)
        batch_records = result['records']
        
        if not batch_records:
            logger.warning(f"⚠️  No more records returned, stopping")
            break
        
        all_records.extend(batch_records)
        logger.info(f"   ✅ Got {len(batch_records)} papers (total: {len(all_records):,})")
        
        start_index += len(batch_records)
        
        # Check if we've hit the limit
        if limit and len(all_records) >= limit:
            logger.info(f"🎯 Reached limit of {limit} papers")
            all_records = all_records[:limit]
            break
        
        # Be polite - delay between requests
        if len(all_records) < total_to_fetch:
            time.sleep(REQUEST_DELAY)
    
    logger.info(f"✅ Download completed: {len(all_records):,} total papers")
    return all_records

def transform_arxiv_record(record: Dict[str, Any]) -> Optional[PaperRecord]:
    """Transform arXiv metadata to PaperRecord format."""
    try:
        paper_id = record.get('id', '').strip()
        title = record.get('title', '').strip()
        abstract = record.get('abstract', '').strip()
        authors = record.get('authors', [])
        created = record.get('created')
        
        # Validate required fields
        if not paper_id or not title:
            return None
        
        # Normalize arXiv ID (remove version if present)
        if 'v' in paper_id:
            paper_id = paper_id.split('v')[0]
        
        # Ensure full arXiv URL
        if not paper_id.startswith('http'):
            paper_id = f"http://arxiv.org/abs/{paper_id}"
        
        # Parse date
        primary_date = parse_arxiv_date(created) if created else None
        
        # Extract DOI if available (from doi field in record)
        doi = record.get('doi', '').strip() if record.get('doi') else None
        
        return PaperRecord(
            source='arxiv',
            source_id=paper_id,
            title=title,
            abstract=abstract or '',
            authors=tuple(authors) if authors else (),
            primary_date=primary_date,
            doi=doi
        )
        
    except Exception as e:
        logger.warning(f"Error transforming arXiv record: {e}")
        return None

def extract_arxiv_metadata(record: Dict[str, Any], paper_id: str) -> Dict[str, str]:
    """Extract arXiv-specific metadata for storage."""
    def build_links() -> list[dict]:
        """Pure: Build extpub-style links array (arXiv, PDF, DOI, Journal[URL only])."""
        links: list[dict] = []
        # paper_id here is the arXiv source_id URL (http://arxiv.org/abs/<id>) or an ID
        arxiv_id: str = ''
        pid = paper_id or ''
        if 'arxiv.org/abs/' in pid:
            arxiv_id = pid.split('arxiv.org/abs/')[-1]
        else:
            arxiv_id = pid
        # strip version if present
        if 'v' in arxiv_id:
            parts = arxiv_id.rsplit('v', 1)
            if len(parts) == 2 and parts[1].isdigit():
                arxiv_id = parts[0]

        if arxiv_id:
            links.append({
                'href': f'https://arxiv.org/abs/{arxiv_id}',
                'rel': 'alternate',
                'type': 'text/html',
                'title': 'arXiv'
            })
            links.append({
                'href': f'https://arxiv.org/pdf/{arxiv_id}.pdf',
                'rel': 'alternate',
                'type': 'text/html',
                'title': 'PDF'
            })

        # DOI link (if present)
        doi_val = record.get('doi', '')
        if isinstance(doi_val, str) and doi_val.strip():
            links.append({
                'href': f'https://doi.org/{doi_val.strip()}',
                'rel': 'alternate',
                'type': 'text/html',
                'title': 'DOI'
            })

        # Journal reference (only if looks like a URL)
        jref = record.get('journal_ref') or record.get('journal-ref')
        if isinstance(jref, str) and (jref.startswith('http://') or jref.startswith('https://')):
            links.append({
                'href': jref,
                'rel': 'alternate',
                'type': 'text/html',
                'title': 'Journal'
            })

        return links

    metadata = {
        'doctrove_paper_id': paper_id,
        'arxiv_categories': json.dumps(record.get('categories', [])),
        'arxiv_doi': record.get('doi', ''),
        'arxiv_journal_ref': record.get('journal_ref', ''),
        'arxiv_comments': record.get('comments', ''),
        'arxiv_license': record.get('license', ''),
    }
    
    # Remove empty values
    cleaned = {k: v for k, v in metadata.items() if v and v != '[]'}

    # Build extpub-style links for insertion into doctrove_papers via shared framework
    try:
        links_arr = build_links()
        if links_arr:
            cleaned['links'] = json.dumps(links_arr)
    except Exception:
        # Be robust: if link building fails, just skip
        pass

    return cleaned

def get_arxiv_metadata_fields() -> List[str]:
    """Get list of arXiv metadata fields."""
    return [
        'doctrove_paper_id',
        'arxiv_categories',
        'arxiv_doi',
        'arxiv_journal_ref',
        'arxiv_comments',
        'arxiv_license'
    ]

def ingest_arxiv_papers(papers: List[Dict[str, Any]], connection_factory) -> Dict[str, int]:
    """
    Ingest arXiv papers in batches.
    
    Returns:
        Dict with counts: total, processed, errors
    """
    total = len(papers)
    processed = 0
    errors = 0
    
    logger.info(f"📝 Ingesting {total:,} papers in batches of {BATCH_SIZE}")
    
    # Ensure metadata table exists
    ensure_metadata_table_exists(connection_factory, 'arxiv', get_arxiv_metadata_fields())
    
    # Process in batches
    for i in range(0, total, BATCH_SIZE):
        batch = papers[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        logger.info(f"📦 Processing batch {batch_num} ({len(batch)} papers)...")
        
        # Transform to PaperRecords
        paper_records = []
        for record in batch:
            paper = transform_arxiv_record(record)
            if paper:
                paper_records.append((paper, record))
        
        # Insert papers
        from shared_ingestion_framework import insert_paper_with_metadata
        
        for paper, original_record in paper_records:
            try:
                # Extract metadata
                metadata_dict = extract_arxiv_metadata(original_record, paper.source_id)
                metadata = MetadataRecord(paper_id=paper.source_id, fields=metadata_dict)
                
                # Insert
                result = insert_paper_with_metadata(connection_factory, paper, metadata, 'arxiv')
                if result:
                    processed += 1
            except Exception as e:
                errors += 1
                if errors <= 10:  # Only show first 10 errors
                    logger.error(f"Error inserting paper: {e}")
        
        logger.info(f"   ✅ Batch {batch_num} completed: {len(paper_records)} processed")
        logger.info(f"   📈 Total progress: {processed:,}/{total:,} papers")
    
    return {
        'total': total,
        'processed': processed,
        'errors': errors
    }

def main():
    """Main entry point for arXiv ingestion."""
    parser = argparse.ArgumentParser(description='Ingest arXiv papers by date range')
    parser.add_argument('--year', type=int, help='Ingest all papers from this year (e.g., 2025)')
    parser.add_argument('--from', dest='from_date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to', dest='to_date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--categories', help='Comma-separated list of categories (e.g., cs.AI,cs.LG)')
    parser.add_argument('--limit', type=int, help='Limit number of papers (for testing)')
    parser.add_argument('--output', help='Save downloaded metadata to JSON file')
    
    args = parser.parse_args()
    
    # Determine date range
    if args.year:
        from_date = f"{args.year}-01-01"
        to_date = f"{args.year}-12-31"
        logger.info(f"📅 Ingesting arXiv papers from year {args.year}")
    elif args.from_date and args.to_date:
        from_date = args.from_date
        to_date = args.to_date
        logger.info(f"📅 Ingesting arXiv papers from {from_date} to {to_date}")
    else:
        logger.error("❌ Must specify either --year or both --from and --to")
        sys.exit(1)
    
    # Download papers
    logger.info("🌐 Downloading arXiv metadata via API...")
    papers = download_arxiv_papers_by_date(from_date, to_date, limit=args.limit)
    
    if not papers:
        logger.error("❌ No papers downloaded")
        sys.exit(1)
    
    logger.info(f"✅ Downloaded {len(papers):,} papers")
    
    # Filter by categories if specified
    if args.categories:
        cats = [c.strip() for c in args.categories.split(',')]
        logger.info(f"🔍 Filtering for categories: {cats}")
        
        filtered = []
        for paper in papers:
            paper_cats = paper.get('categories', [])
            if any(cat in paper_cats for cat in cats):
                filtered.append(paper)
        
        logger.info(f"✅ Filtered to {len(filtered):,} papers in specified categories")
        papers = filtered
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        logger.info(f"💾 Saving metadata to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(papers, f, indent=2)
        logger.info(f"✅ Saved {len(papers):,} papers to {output_path}")
    
    # Ingest into database
    logger.info("🗄️  Ingesting into database...")
    connection_factory = create_connection_factory(get_default_config)
    
    result = ingest_arxiv_papers(papers, connection_factory)
    
    # Summary
    print()
    print("=" * 80)
    print("✅ arXiv Ingestion Complete")
    print("=" * 80)
    print(f"Total papers:     {result['total']:,}")
    print(f"Successfully ingested: {result['processed']:,}")
    if result['errors'] > 0:
        print(f"Errors:           {result['errors']:,}")
    print()
    print("📊 Papers will be automatically enriched with:")
    print("   - Vector embeddings (1536-d semantic search)")
    print("   - 2D projections (UMAP visualization)")
    print()
    print("Monitor enrichment with:")
    print("   screen -r enrichment_embeddings  # Vector embeddings")
    print("   screen -r embedding_2d           # 2D projections")
    print("=" * 80)

if __name__ == "__main__":
    main()

