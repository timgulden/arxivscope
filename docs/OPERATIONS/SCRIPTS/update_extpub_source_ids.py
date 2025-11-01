#!/usr/bin/env python3
"""
Update external publication source_ids from hash-based to MARC 001 control numbers.
This script carefully maps titles to MARC 001 IDs and updates the source_id field.
"""

import psycopg2
import pymarc
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

def extract_marc_mapping(marc_file):
    """Extract title to MARC 001 mapping from MARC file"""
    title_to_marc = {}
    with open(marc_file, 'rb') as f:
        reader = pymarc.MARCReader(f)
        for record in reader:
            if record.get_fields('001'):
                marc_001 = record.get_fields('001')[0].value()
                # Extract title
                title = ""
                if record.get("245"):
                    title = record["245"].get("a", "")
                    if record["245"].get("b"):
                        title += " " + record["245"]["b"]
                title = title.strip()
                if title:
                    # If we have multiple MARC records for the same title, 
                    # we'll use the first one we encounter
                    if title not in title_to_marc:
                        title_to_marc[title] = marc_001
    return title_to_marc

def update_source_ids():
    """Update external publication source_ids with MARC 001 control numbers"""
    
    # Extract MARC 001 mapping
    print("Extracting MARC 001 control numbers...")
    title_to_marc = extract_marc_mapping('data/EXTPUB_20250707.mrc')
    print(f"Found {len(title_to_marc)} unique titles with MARC 001 control numbers")
    
    # Connect to database
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all external publications with hash-based IDs
    cur.execute("""
        SELECT doctrove_paper_id, doctrove_title, doctrove_source_id 
        FROM doctrove_papers 
        WHERE doctrove_source = 'external_publication' 
        AND doctrove_source_id LIKE 'EXTERNAL_PUBLICATION_%'
    """)
    
    records = cur.fetchall()
    print(f"Found {len(records)} external publications with hash-based IDs")
    
    updated_count = 0
    skipped_count = 0
    
    for paper_id, title, current_source_id in tqdm(records, desc="Updating source_ids"):
        # Check if we have a MARC 001 for this title
        if title in title_to_marc:
            marc_001 = title_to_marc[title]
            
            # Check if this MARC 001 is already used by another paper
            cur.execute("""
                SELECT COUNT(*) FROM doctrove_papers 
                WHERE doctrove_source = 'external_publication' 
                AND doctrove_source_id = %s
            """, (marc_001,))
            
            existing_count = cur.fetchone()[0]
            
            if existing_count == 0:
                # Safe to update - no conflict
                cur.execute("""
                    UPDATE doctrove_papers 
                    SET doctrove_source_id = %s 
                    WHERE doctrove_paper_id = %s
                """, (marc_001, paper_id))
                updated_count += 1
            else:
                # Conflict - skip this one
                skipped_count += 1
                print(f"Conflict for title: {title[:50]}... (MARC 001: {marc_001})")
        else:
            # No MARC 001 found for this title
            skipped_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Updated {updated_count} external publications with MARC 001 control numbers")
    print(f"Skipped {skipped_count} publications (no MARC 001 or conflicts)")

if __name__ == "__main__":
    update_source_ids()
