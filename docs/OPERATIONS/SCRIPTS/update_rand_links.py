#!/usr/bin/env python3
"""
Update RAND publication links to use Primo catalog URLs instead of HTTP links.
This script updates only the doctrove_links field without re-ingesting everything.
"""

import psycopg2
import json
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

def extract_marc_001_from_file(marc_file):
    """Extract MARC 001 control numbers from the MARC file"""
    marc_ids = {}
    with open(marc_file, 'rb') as f:
        reader = pymarc.MARCReader(f)
        for record in reader:
            if record.get_fields('001'):
                marc_001 = record.get_fields('001')[0].value()
                # Use title as key to match with database records
                title = ""
                if record.get("245"):
                    title = record["245"].get("a", "")
                    if record["245"].get("b"):
                        title += " " + record["245"]["b"]
                title = title.strip()
                if title:
                    marc_ids[title] = marc_001
    return marc_ids

def update_rand_links():
    """Update RAND publication links with Primo catalog URLs"""
    
    # Extract MARC 001 control numbers
    print("Extracting MARC 001 control numbers...")
    marc_ids = extract_marc_001_from_file('data/RANDPUB_20250707.mrc')
    print(f"Found {len(marc_ids)} MARC records with control numbers")
    
    # Connect to database
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all RAND publications
    cur.execute("""
        SELECT doctrove_paper_id, doctrove_title, doctrove_links 
        FROM doctrove_papers 
        WHERE doctrove_source = 'randpub'
    """)
    
    records = cur.fetchall()
    print(f"Found {len(records)} RAND publications in database")
    
    updated_count = 0
    
    for paper_id, title, current_links in tqdm(records, desc="Updating links"):
        # Check if we have a MARC 001 for this title
        if title in marc_ids:
            marc_001 = marc_ids[title]
            
            # Create Primo catalog URL
            primo_url = f"https://rand.primo.exlibrisgroup.com/permalink/01RAND_INST/8jidjm/alma{marc_001}"
            
            # Create new links array with Primo catalog link
            new_links = [{
                "href": primo_url,
                "rel": "alternate", 
                "type": "text/html",
                "title": "Library Catalog"
            }]
            
            # Update the record
            cur.execute("""
                UPDATE doctrove_papers 
                SET doctrove_links = %s 
                WHERE doctrove_paper_id = %s
            """, (json.dumps(new_links), paper_id))
            
            updated_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Updated {updated_count} RAND publications with Primo catalog links")

if __name__ == "__main__":
    update_rand_links()
