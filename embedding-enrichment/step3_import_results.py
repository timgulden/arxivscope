#!/usr/bin/env python3
"""
Step 3: Import Results from CSV (Run on AWS)
Reads enrichment_results.csv and inserts into enrichment_country table
"""

import sys
import os
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

def import_results(csv_file='enrichment_results.csv'):
    conn = create_connection_factory()()
    cur = conn.cursor()
    
    # Read CSV
    print(f"Reading {csv_file}...")
    results = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    
    total = len(results)
    print(f"Loaded {total:,} enrichment results")
    
    # Insert into database
    inserted = 0
    skipped = 0
    
    for i, result in enumerate(results, 1):
        try:
            cur.execute("""
                INSERT INTO enrichment_country (
                    doctrove_paper_id,
                    institution_name,
                    institution_country_code,
                    country_name,
                    country_uschina,
                    enrichment_method,
                    enrichment_confidence,
                    enrichment_source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (doctrove_paper_id) DO NOTHING
            """, (
                result['paper_id'],
                result['institution_name'],
                result['institution_country_code'],
                result['country_name'],
                result['country_uschina'],
                'openalex_api',
                'high',
                'OpenAlex API'
            ))
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
                
        except Exception as e:
            print(f"Error on row {i}: {e}")
            continue
        
        if i % 10000 == 0:
            print(f"Progress: {i:,}/{total:,} ({100*i/total:.1f}%) - "
                  f"Inserted: {inserted:,}, Skipped: {skipped:,}")
            conn.commit()
    
    conn.commit()
    
    # Show summary
    print(f"\n{'='*80}")
    print(f"Import Complete!")
    print(f"Total rows: {total:,}")
    print(f"Inserted: {inserted:,}")
    print(f"Skipped (duplicates): {skipped:,}")
    print(f"{'='*80}")
    
    # Show current totals
    cur.execute("""
        SELECT enrichment_method, COUNT(*) 
        FROM enrichment_country 
        GROUP BY enrichment_method
        ORDER BY enrichment_method
    """)
    
    print("\nCurrent enrichment_country totals:")
    print("-" * 80)
    for method, count in cur.fetchall():
        print(f"{method:<25} {count:>10,} papers")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    import_results()


