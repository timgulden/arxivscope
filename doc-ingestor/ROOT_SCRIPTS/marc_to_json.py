#!/usr/bin/env python3
"""
MARC to JSON conversion script for DocScope ingestion.
Converts MARC files to JSON format suitable for the ingestion pipeline.

This script processes MARC files and extracts relevant metadata fields
for ingestion into the DocScope/DocTrove system.

Usage:
    python marc_to_json.py [--input-dir /path/to/marc/files] [--output-dir /path/to/output]

Author: DocScope Team
Date: 2024
"""

import pymarc
import json
import os
import argparse
from datetime import datetime
from tqdm import tqdm

def process_marc_file(input_file, output_file, source_type):
    """
    Convert MARC file to JSON format for further processing
    
    Args:
        input_file: Path to input MARC file
        output_file: Path to output JSON file
        source_type: Type of source (e.g., 'RAND_PUBLICATION', 'EXTERNAL_PUBLICATION')
    
    Returns:
        Number of records processed
    """
    records = []
    error_count = 0
    
    print(f"Processing {input_file}...")
    
    with open(input_file, "rb") as f:
        reader = pymarc.MARCReader(f)
        
        for record in tqdm(reader, desc=f"Processing {source_type}"):
            try:
                processed_record = extract_marc_data(record, source_type)
                if processed_record:
                    records.append(processed_record)
            except Exception as e:
                error_count += 1
                print(f"Error processing record: {e}")
                continue
    
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2, default=str)
    
    print(f"Processed {len(records)} records, {error_count} errors")
    print(f"Output saved to: {output_file}")
    return len(records)

def extract_marc_data(record, source_type):
    """
    Extract relevant data from MARC record
    
    Args:
        record: MARC record object
        source_type: Type of source
    
    Returns:
        Dictionary with extracted data or None if error
    """
    try:
        # Extract title
        title = ""
        if record.get("245"):
            title = record["245"].get("a", "")
            if record["245"].get("b"):
                title += " " + record["245"]["b"]
        
        # Extract authors
        authors = []
        for field in record.get_fields("100", "700"):
            if field.get("a"):
                authors.append(field["a"])
        
        # Extract abstract/summary
        abstract = ""
        if record.get("520"):
            abstract = record["520"].get("a", "")
        
        # Extract publication date
        pub_date = ""
        if record.get("260"):
            pub_date = record["260"].get("c", "")
        elif record.get("264"):
            pub_date = record["264"].get("c", "")
        
        # Extract DOI
        doi = ""
        for field in record.get_fields("024"):
            if field.get("2") == "doi":
                doi = field.get("a", "")
        
        # Extract additional metadata fields
        local_call_number = ""
        if record.get("099"):
            local_call_number = record["099"].get("a", "")
        
        funding_info = ""
        if record.get("536"):
            funding_info = record["536"].get("a", "")
            if record["536"].get("b"):
                funding_info += " " + record["536"]["b"]
        
        corporate_names = []
        for field in record.get_fields("610"):
            if field.get("a"):
                corporate_names.append(field["a"])
            if field.get("b"):
                corporate_names.append(field["b"])
        
        subjects = []
        for field in record.get_fields("650"):
            if field.get("a"):
                subjects.append(field["a"])
        
        general_notes = []
        for field in record.get_fields("500"):
            if field.get("a"):
                general_notes.append(field["a"])
        
        source_acquisition = ""
        if record.get("037"):
            source_acquisition = record["037"].get("a", "")
        
        local_processing = ""
        if record.get("925"):
            local_processing = record["925"].get("a", "")
        
        local_data = ""
        if record.get("981"):
            local_data = record["981"].get("a", "")
        
        # Extract MARC 001 control number (catalog ID)
        marc_001 = ""
        if record.get_fields("001"):
            marc_001 = record.get_fields("001")[0].value()
        
        # Extract links from MARC fields
        links = []
        
        # For RAND and External publications, create Primo catalog links using MARC 001
        if (source_type in ["RAND_PUBLICATION", "EXTERNAL_PUBLICATION"]) and marc_001:
            primo_url = f"https://rand.primo.exlibrisgroup.com/permalink/01RAND_INST/8jidjm/alma{marc_001}"
            links.append({
                "href": primo_url,
                "rel": "alternate",
                "type": "text/html",
                "title": "Library Catalog (Internal)"
            })
        
        # Extract URLs from 856 field (Electronic Location and Access) - these are public links
        for field in record.get_fields("856"):
            url = field.get("u", "")
            if url:
                link_type = field.get("3", "")  # Subfield 3 often contains link description
                # Default title based on the URL or field content
                if not link_type:
                    if "rand.org" in url:
                        link_type = "Public Website"
                    else:
                        link_type = "Full Text"
                
                links.append({
                    "href": url,
                    "rel": "alternate",
                    "type": "text/html",
                    "title": link_type
                })
        
        # Extract DOI as a link if available
        if doi:
            if doi.startswith("http"):
                doi_url = doi
            else:
                doi_url = f"https://doi.org/{doi}"
            links.append({
                "href": doi_url,
                "rel": "alternate",
                "type": "text/html",
                "title": "DOI"
            })
        
        # Use MARC 001 control number as source_id (unique within the source)
        # If no MARC 001, skip this record as we can't ensure uniqueness
        if not marc_001:
            return None
        source_id = marc_001
        
        return {
            "source_id": source_id,
            "title": title.strip(),
            "authors": [author.strip() for author in authors],
            "abstract": abstract.strip(),
            "publication_date": pub_date.strip(),
            "doi": doi.strip(),
            "links": links,  # Add links to the output
            "source_type": source_type,
            "marc_id": marc_001,
            "processing_date": datetime.now().isoformat(),
            # Additional metadata fields
            "local_call_number": local_call_number.strip(),
            "funding_info": funding_info.strip(),
            "corporate_names": corporate_names,
            "subjects": subjects,
            "general_notes": general_notes,
            "source_acquisition": source_acquisition.strip(),
            "local_processing": local_processing.strip(),
            "local_data": local_data.strip()
        }
    
    except Exception as e:
        print(f"Error extracting data from MARC record: {e}")
        return None

def main():
    """Main function to process MARC files"""
    parser = argparse.ArgumentParser(description='Convert MARC files to JSON for DocScope ingestion')
    parser.add_argument('--input-dir', default='/opt/arxivscope/data', 
                       help='Input directory containing MARC files (default: /opt/arxivscope/data)')
    parser.add_argument('--output-dir', default='/opt/arxivscope/data/processed',
                       help='Output directory for processed JSON files (default: /opt/arxivscope/data/processed)')
    parser.add_argument('--randpub-file', default='RANDPUB_20250707.mrc',
                       help='RAND publications MARC file name (default: RANDPUB_20250707.mrc)')
    parser.add_argument('--extpub-file', default='EXTPUB_20250707.mrc',
                       help='External publications MARC file name (default: EXTPUB_20250707.mrc)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    total_processed = 0
    
    # Process RAND publications
    randpub_input = os.path.join(args.input_dir, args.randpub_file)
    randpub_output = os.path.join(args.output_dir, 'randpubs.json')
    
    if os.path.exists(randpub_input):
        print(f"\n{'='*60}")
        print("Processing RAND Publications")
        print(f"{'='*60}")
        count = process_marc_file(
            randpub_input,
            randpub_output,
            "RAND_PUBLICATION"
        )
        total_processed += count
    else:
        print(f"RAND publications file not found: {randpub_input}")
    
    # Process external publications
    extpub_input = os.path.join(args.input_dir, args.extpub_file)
    extpub_output = os.path.join(args.output_dir, 'external_publications.json')
    
    if os.path.exists(extpub_input):
        print(f"\n{'='*60}")
        print("Processing External Publications")
        print(f"{'='*60}")
        count = process_marc_file(
            extpub_input,
            extpub_output,
            "EXTERNAL_PUBLICATION"
        )
        total_processed += count
    else:
        print(f"External publications file not found: {extpub_input}")
    
    print(f"\n{'='*60}")
    print("MARC Processing Summary")
    print(f"{'='*60}")
    print(f"Total records processed: {total_processed}")
    print(f"Output directory: {args.output_dir}")
    print("MARC processing complete!")
    
    # Print next steps
    print(f"\nNext steps:")
    print(f"1. Review the generated JSON files in: {args.output_dir}")
    print(f"2. Ingest RAND publications: python doc-ingestor/main_ingestor.py {randpub_output} --source randpub --streaming")
    print(f"3. Ingest external publications: python doc-ingestor/main_ingestor.py {extpub_output} --source extpub --streaming")

if __name__ == "__main__":
    main() 