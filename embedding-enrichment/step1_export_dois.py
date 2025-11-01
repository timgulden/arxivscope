#!/usr/bin/env python3
"""
Step 1: Export DOIs to CSV (Run on AWS)
Creates a CSV file with papers that need country enrichment
"""

import sys
import os
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

def export_dois():
    conn = create_connection_factory()()
    cur = conn.cursor()
    
    # Get papers needing enrichment
    cur.execute("""
        SELECT dp.doctrove_paper_id, am.arxiv_doi
        FROM doctrove_papers dp
        JOIN arxiv_metadata am ON dp.doctrove_paper_id = am.doctrove_paper_id
        LEFT JOIN enrichment_country ec ON dp.doctrove_paper_id = ec.doctrove_paper_id
        WHERE dp.doctrove_source = 'arxiv'
        AND am.arxiv_doi IS NOT NULL
        AND ec.doctrove_paper_id IS NULL
        ORDER BY dp.doctrove_paper_id
    """)
    
    papers = cur.fetchall()
    total = len(papers)
    
    print(f"Found {total:,} papers needing enrichment")
    
    # Write to CSV
    output_file = 'dois_to_process.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['paper_id', 'doi'])  # Header
        writer.writerows(papers)
    
    print(f"Exported {total:,} papers to {output_file}")
    print(f"File size: {os.path.getsize(output_file):,} bytes")
    print()
    print("Next steps:")
    print(f"1. Download file to your laptop:")
    print(f"   scp arxivscope@54.158.170.226:/opt/arxivscope/embedding-enrichment/{output_file} ~/Documents/Arxivscope/")
    print(f"2. Run step2_process_dois.py on your laptop")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    export_dois()


