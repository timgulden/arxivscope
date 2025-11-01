#!/usr/bin/env python3
"""
Recreate RAND metadata table by matching existing papers with MARC data.
This script reads the MARC JSON and creates metadata entries for existing papers.
"""

import psycopg2
import json
from tqdm import tqdm

def get_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        port=5434,
        database="doctrove",
        user="doctrove_admin",
        password="doctrove_admin"
    )

def create_metadata_table(conn):
    """Create the randpub_metadata table if it doesn't exist"""
    cur = conn.cursor()
    
    # Create the metadata table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS randpub_metadata (
            doctrove_paper_id UUID PRIMARY KEY,
            doi TEXT,
            marc_id TEXT,
            processing_date TEXT,
            source_type TEXT,
            publication_date TEXT,
            document_type TEXT,
            rand_project TEXT,
            links TEXT,
            local_call_number TEXT,
            funding_info TEXT,
            corporate_names TEXT,
            subjects TEXT,
            general_notes TEXT,
            source_acquisition TEXT,
            local_processing TEXT,
            local_data TEXT,
            FOREIGN KEY (doctrove_paper_id) REFERENCES doctrove_papers(doctrove_paper_id)
        )
    """)
    
    conn.commit()
    cur.close()

def recreate_randpub_metadata():
    """Recreate RAND metadata by matching papers with MARC data"""
    
    # Load MARC JSON data
    print("Loading MARC JSON data...")
    with open('/opt/arxivscope/data/processed/randpubs.json', 'r') as f:
        marc_data = json.load(f)
    
    # Create mapping from source_id to metadata
    print("Creating source_id to metadata mapping...")
    source_id_to_metadata = {}
    for record in marc_data:
        source_id = record.get('source_id', '')
        if source_id:
            source_id_to_metadata[source_id] = record
    
    print(f"Found {len(source_id_to_metadata)} MARC records with source_ids")
    
    # Connect to database
    conn = get_connection()
    
    # Create metadata table
    create_metadata_table(conn)
    
    cur = conn.cursor()
    
    # Get all RAND papers with MARC 001 source_ids
    cur.execute("""
        SELECT doctrove_paper_id, doctrove_source_id, doctrove_title
        FROM doctrove_papers 
        WHERE doctrove_source = 'randpub' 
        AND doctrove_source_id ~ '^[0-9]+$'
    """)
    
    papers = cur.fetchall()
    print(f"Found {len(papers)} RAND papers with MARC 001 source_ids")
    
    inserted_count = 0
    skipped_count = 0
    
    for paper_id, source_id, title in tqdm(papers, desc="Creating metadata entries"):
        if source_id in source_id_to_metadata:
            metadata = source_id_to_metadata[source_id]
            
            # Extract metadata fields
            metadata_fields = {
                'doctrove_paper_id': paper_id,
                'doi': metadata.get('doi', ''),
                'marc_id': metadata.get('marc_id', ''),
                'processing_date': metadata.get('processing_date', ''),
                'source_type': metadata.get('source_type', ''),
                'publication_date': metadata.get('publication_date', ''),
                'document_type': metadata.get('document_type', ''),
                'rand_project': metadata.get('rand_project', ''),
                'links': json.dumps(metadata.get('links', [])),
                'local_call_number': metadata.get('local_call_number', ''),
                'funding_info': metadata.get('funding_info', ''),
                'corporate_names': json.dumps(metadata.get('corporate_names', [])),
                'subjects': json.dumps(metadata.get('subjects', [])),
                'general_notes': json.dumps(metadata.get('general_notes', [])),
                'source_acquisition': metadata.get('source_acquisition', ''),
                'local_processing': metadata.get('local_processing', ''),
                'local_data': metadata.get('local_data', '')
            }
            
            # Insert metadata
            try:
                cur.execute("""
                    INSERT INTO randpub_metadata (
                        doctrove_paper_id, doi, marc_id, processing_date, source_type,
                        publication_date, document_type, rand_project, links,
                        local_call_number, funding_info, corporate_names, subjects,
                        general_notes, source_acquisition, local_processing, local_data
                    ) VALUES (
                        %(doctrove_paper_id)s, %(doi)s, %(marc_id)s, %(processing_date)s,
                        %(source_type)s, %(publication_date)s, %(document_type)s,
                        %(rand_project)s, %(links)s, %(local_call_number)s,
                        %(funding_info)s, %(corporate_names)s, %(subjects)s,
                        %(general_notes)s, %(source_acquisition)s, %(local_processing)s,
                        %(local_data)s
                    )
                """, metadata_fields)
                inserted_count += 1
            except psycopg2.IntegrityError:
                # Already exists, skip
                skipped_count += 1
                conn.rollback()
        else:
            skipped_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Created {inserted_count} metadata entries")
    print(f"Skipped {skipped_count} papers (no MARC data or already exists)")

if __name__ == "__main__":
    recreate_randpub_metadata()
