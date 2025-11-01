#!/usr/bin/env python3
"""
MARC Ingester using the Shared Ingestion Framework
Processes MARC data using the reliable patterns from the functional ingester.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re

# Import the shared framework
from shared_ingestion_framework import process_file_unified, get_default_config, PaperRecord, MetadataRecord

def transform_marc_record(record: Dict[str, Any]) -> Optional[PaperRecord]:
    """
    Pure function: Transform a MARC record to the canonical paper format.
    
    Args:
        record: Raw MARC record from JSON
        
    Returns:
        Transformed PaperRecord or None if invalid
    """
    try:
        # Extract required fields
        title = record.get('title', '').strip()
        if not title:
            return None
            
        source_id = record.get('source_id', '')
        if not source_id:
            return None
            
        # Extract optional fields
        abstract = record.get('abstract', '').strip()
        authors = record.get('authors', [])
        publication_date = record.get('publication_date', '').strip()
        source_type = record.get('source_type', '')
        
        # Clean up authors list and convert to tuple for immutability
        if isinstance(authors, list):
            # Remove trailing commas and clean up
            cleaned_authors = []
            for author in authors:
                if author.strip():
                    # Remove trailing comma and clean up
                    cleaned_author = author.strip().rstrip(',')
                    if cleaned_author:
                        cleaned_authors.append(cleaned_author)
            authors_tuple = tuple(cleaned_authors)
        else:
            authors_tuple = ()
        
        # Parse publication date (try to extract year)
        parsed_date = parse_publication_date(publication_date)
        
        # Extract DOI if available
        doi = record.get('doi', '').strip() if record.get('doi') else None
        
        return PaperRecord(
            source=source_type.lower(),
            source_id=source_id,
            title=title,
            abstract=abstract,
            authors=authors_tuple,
            primary_date=parsed_date,
            doi=doi
        )
        
    except Exception as e:
        print(f"Error transforming MARC record: {e}")
        return None

def parse_publication_date(date_str: str) -> Optional[str]:
    """
    Pure function: Parse publication date and extract year.
    
    Args:
        date_str: Raw date string from MARC
        
    Returns:
        ISO date string (YYYY-01-01) or None
    """
    if not date_str:
        return None
    
    try:
        # Try to extract year from various formats
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            return f"{year}-01-01"  # Use January 1st as default
    except:
        pass
    
    return None

def extract_marc_metadata(record: Dict[str, Any], paper_id: str) -> Dict[str, str]:
    """
    Pure function: Extract metadata from MARC record for storage in source-specific table.
    
    Args:
        record: Raw MARC record
        paper_id: The paper ID (not used in this case)
        
    Returns:
        Metadata dictionary
    """
    import json
    
    metadata = {
        'doctrove_paper_id': paper_id,  # Will be set by the framework
        'doi': record.get('doi', ''),
        'marc_id': record.get('marc_id', ''),
        'processing_date': record.get('processing_date', ''),
        'source_type': record.get('source_type', ''),
        'publication_date': record.get('publication_date', ''),
        'document_type': record.get('document_type', ''),
        'rand_project': record.get('rand_project', ''),
        # Additional MARC fields
        'local_call_number': record.get('local_call_number', ''),
        'funding_info': record.get('funding_info', ''),
        'corporate_names': json.dumps(record.get('corporate_names', [])) if record.get('corporate_names') else '',
        'subjects': json.dumps(record.get('subjects', [])) if record.get('subjects') else '',
        'general_notes': json.dumps(record.get('general_notes', [])) if record.get('general_notes') else '',
        'source_acquisition': record.get('source_acquisition', ''),
        'local_processing': record.get('local_processing', ''),
        'local_data': record.get('local_data', '')
    }
    
    # Handle links - convert to JSON string for storage
    links = record.get('links', [])
    if links:
        metadata['links'] = json.dumps(links)
    
    # Remove empty values
    return {k: v for k, v in metadata.items() if v}

def get_metadata_fields() -> List[str]:
    """Pure function: Get the list of metadata fields for MARC data."""
    return [
        'doctrove_paper_id',
        'doi',
        'marc_id', 
        'processing_date',
        'source_type',
        'publication_date',
        'document_type',
        'rand_project',
        'links',
        # Additional MARC fields
        'local_call_number',
        'funding_info',
        'corporate_names',
        'subjects',
        'general_notes',
        'source_acquisition',
        'local_processing',
        'local_data'
    ]

def main():
    """Main entry point for MARC ingestion."""
    parser = argparse.ArgumentParser(description='Ingest MARC data using unified framework')
    parser.add_argument('json_path', help='Path to processed JSON file from MARC conversion')
    parser.add_argument('--source', default='randpub', choices=['randpub', 'extpub'],
                       help='Source type (default: randpub)')
    parser.add_argument('--limit', type=int, help='Limit number of records to process (for testing)')
    
    args = parser.parse_args()
    
    file_path = Path(args.json_path)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    print(f"Processing MARC data from: {file_path}")
    print(f"Source type: {args.source}")
    
    # Process the file using the unified framework
    try:
        result = process_file_unified(
            file_path=file_path,
            source_name=args.source,
            transformer=transform_marc_record,
            metadata_extractor=extract_marc_metadata,
            config_provider=get_default_config,
            metadata_fields=get_metadata_fields(),
            limit=args.limit
        )
        
        print(f"✅ Successfully processed MARC data:")
        print(f"   - Papers inserted: {result.inserted_count}")
        print(f"   - Total processed: {result.total_processed}")
        if result.errors:
            print(f"   - Errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"     - {error}")
        
    except Exception as e:
        print(f"❌ Error processing MARC data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 