#!/usr/bin/env python3
"""
Patch program to populate doctrove_links field in doctrove_papers table
from existing metadata tables (aipickle_metadata and randpub_metadata).
"""

import psycopg2
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_to_db():
    """Connect to the database."""
    try:
        conn = psycopg2.connect(
            dbname="doctrove",
            user="doctrove_admin",
            password="doctrove_admin",
            host="localhost",
            port="5434"
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def extract_openalex_links(raw_data: dict) -> Optional[str]:
    """
    Extract links from OpenAlex raw_data JSONB.
    
    Args:
        raw_data: OpenAlex raw_data JSON object
        
    Returns:
        JSON string with normalized links or None if no links
    """
    if not raw_data:
        return None
    
    try:
        links = []
        
        # Extract landing page URL
        if raw_data.get('primary_location', {}).get('landing_page_url'):
            landing_url = raw_data['primary_location']['landing_page_url']
            links.append({
                "href": landing_url,
                "rel": "alternate",
                "type": "text/html",
                "title": "Landing Page"
            })
        
        # Extract PDF URL
        if raw_data.get('primary_location', {}).get('pdf_url'):
            pdf_url = raw_data['primary_location']['pdf_url']
            links.append({
                "href": pdf_url,
                "rel": "alternate",
                "type": "application/pdf",
                "title": "PDF"
            })
        
        # Extract DOI
        if raw_data.get('doi'):
            doi = raw_data['doi']
            if doi.startswith('http'):
                links.append({
                    "href": doi,
                    "rel": "alternate",
                    "type": "text/html",
                    "title": "DOI"
                })
        
        return json.dumps(links) if links else None
        
    except Exception as e:
        logger.error(f"Error extracting OpenAlex links: {e}")
        return None

def normalize_links(links_data: Any, source_type: str) -> Optional[str]:
    """
    Normalize links from different sources into a consistent format.
    
    Args:
        links_data: Raw links data from metadata table
        source_type: Type of source ('aipickle', 'randpub', etc.)
    
    Returns:
        JSON string with normalized links or None if no links
    """
    if not links_data:
        return None
    
    try:
        # Handle different link formats
        if source_type == 'aipickle':
            # AiPickle links are already in the correct format
            if isinstance(links_data, str):
                return links_data
            elif isinstance(links_data, list):
                return json.dumps(links_data)
            else:
                return None
        
        elif source_type == 'randpub':
            # RAND links are in format: {"RAND Publication": "http://..."}
            if isinstance(links_data, str):
                try:
                    # Parse the JSON and convert to standard format
                    rand_links = json.loads(links_data)
                    if isinstance(rand_links, dict) and rand_links:
                        # Convert to standard format
                        normalized_links = []
                        for link_type, url in rand_links.items():
                            if url and url.strip():
                                if "research_briefs" in url:
                                    normalized_links.append({
                                        "href": url,
                                        "rel": "alternate",
                                        "type": "text/html",
                                        "title": "RAND Research Brief"
                                    })
                                elif "occasional_papers" in url:
                                    normalized_links.append({
                                        "href": url,
                                        "rel": "alternate", 
                                        "type": "text/html",
                                        "title": "RAND Publication"
                                    })
                                else:
                                    normalized_links.append({
                                        "href": url,
                                        "rel": "alternate",
                                        "type": "text/html",
                                        "title": link_type
                                    })
                        return json.dumps(normalized_links) if normalized_links else None
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in RAND links: {links_data}")
                    return None
        
        elif source_type == 'extpub':
            # External publications might have different formats
            # For now, return as-is if it's a string
            if isinstance(links_data, str) and links_data.strip():
                return links_data
        
        return None
    
    except Exception as e:
        logger.error(f"Error normalizing links for {source_type}: {e}")
        return None

def populate_links_from_metadata():
    """Populate doctrove_links field from metadata tables."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        logger.info("Starting to populate doctrove_links field...")
        
        # Get total count for progress tracking
        cursor.execute("SELECT COUNT(*) FROM doctrove_papers")
        total_papers = cursor.fetchone()[0]
        logger.info(f"Total papers to process: {total_papers}")
        
        # Process AiPickle papers
        logger.info("Processing AiPickle papers...")
        cursor.execute("""
            UPDATE doctrove_papers 
            SET doctrove_links = am.links
            FROM aipickle_metadata am
            WHERE doctrove_papers.doctrove_paper_id = am.doctrove_paper_id
            AND doctrove_papers.doctrove_source = 'aipickle'
            AND am.links IS NOT NULL
            AND am.links != '[]'
        """)
        aipickle_updated = cursor.rowcount
        logger.info(f"Updated {aipickle_updated} AiPickle papers with links")
        
        # Process OpenAlex papers
        logger.info("Processing OpenAlex papers...")
        cursor.execute("""
            SELECT dp.doctrove_paper_id, om.openalex_raw_data
            FROM doctrove_papers dp
            JOIN openalex_metadata om ON dp.doctrove_paper_id = om.doctrove_paper_id
            WHERE dp.doctrove_source = 'openalex'
            AND om.openalex_raw_data IS NOT NULL
        """)
        
        openalex_papers = cursor.fetchall()
        openalex_updated = 0
        
        for paper_id, raw_data in openalex_papers:
            if raw_data:
                extracted_links = extract_openalex_links(raw_data)
                if extracted_links:
                    cursor.execute(
                        "UPDATE doctrove_papers SET doctrove_links = %s WHERE doctrove_paper_id = %s",
                        (extracted_links, paper_id)
                    )
                    openalex_updated += 1
        
        logger.info(f"Updated {openalex_updated} OpenAlex papers with links")
        
        # Commit OpenAlex changes immediately
        conn.commit()
        logger.info("Committed OpenAlex changes")
        
        # Process RAND papers
        logger.info("Processing RAND papers...")
        try:
            cursor.execute("""
                SELECT dp.doctrove_paper_id, rm.randpub_links
                FROM doctrove_papers dp
                JOIN randpub_metadata rm ON dp.doctrove_paper_id = rm.doctrove_paper_id
                WHERE dp.doctrove_source = 'randpub'
                AND rm.randpub_links IS NOT NULL
                AND rm.randpub_links != '{}'
            """)
            
            rand_papers = cursor.fetchall()
            rand_updated = 0
            
            for paper_id, rand_links in rand_papers:
                normalized_links = normalize_links(rand_links, 'randpub')
                if normalized_links:
                    cursor.execute(
                        "UPDATE doctrove_papers SET doctrove_links = %s WHERE doctrove_paper_id = %s",
                        (normalized_links, paper_id)
                    )
                    rand_updated += 1
            
            logger.info(f"Updated {rand_updated} RAND papers with links")
        except Exception as e:
            logger.warning(f"RAND processing skipped (no randpub_links column): {e}")
            rand_updated = 0
        
        # Process external publications
        logger.info("Processing external publications...")
        try:
            cursor.execute("""
                UPDATE doctrove_papers 
                SET doctrove_links = em.extpub_links
                FROM extpub_metadata em
                WHERE doctrove_papers.doctrove_paper_id = em.doctrove_paper_id
                AND doctrove_papers.doctrove_source = 'extpub'
                AND em.extpub_links IS NOT NULL
                AND em.extpub_links != '[]'
            """)
            extpub_updated = cursor.rowcount
            logger.info(f"Updated {extpub_updated} external publication papers with links")
        except Exception as e:
            logger.warning(f"External publication processing skipped (no extpub_links column): {e}")
            extpub_updated = 0
        
        # Final commit for any remaining changes
        conn.commit()
        
        # Summary
        total_updated = aipickle_updated + openalex_updated + rand_updated + extpub_updated
        logger.info(f"=== SUMMARY ===")
        logger.info(f"Total papers processed: {total_papers}")
        logger.info(f"AiPickle papers updated: {aipickle_updated}")
        logger.info(f"OpenAlex papers updated: {openalex_updated}")
        logger.info(f"RAND papers updated: {rand_updated}")
        logger.info(f"External publication papers updated: {extpub_updated}")
        logger.info(f"Total papers with links: {total_updated}")
        
        # Verify results
        cursor.execute("SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_links IS NOT NULL")
        papers_with_links = cursor.fetchone()[0]
        logger.info(f"Final count of papers with links: {papers_with_links}")
        
        return {
            'total_papers': total_papers,
            'aipickle_updated': aipickle_updated,
            'openalex_updated': openalex_updated,
            'rand_updated': rand_updated,
            'extpub_updated': extpub_updated,
            'total_updated': total_updated,
            'final_count_with_links': papers_with_links
        }
        
    except Exception as e:
        logger.error(f"Error during population: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def verify_results():
    """Verify the results of the patch."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        logger.info("Verifying results...")
        
        # Check by source type
        cursor.execute("""
            SELECT doctrove_source, 
                   COUNT(*) as total,
                   COUNT(doctrove_links) as with_links,
                   COUNT(CASE WHEN doctrove_links IS NOT NULL AND doctrove_links != '' THEN 1 END) as non_empty_links
            FROM doctrove_papers 
            GROUP BY doctrove_source
            ORDER BY doctrove_source
        """)
        
        results = cursor.fetchall()
        logger.info("=== VERIFICATION RESULTS ===")
        for source, total, with_links, non_empty in results:
            logger.info(f"{source}: {total} total, {with_links} with links, {non_empty} non-empty links")
        
        # Show some sample links
        cursor.execute("""
            SELECT doctrove_source, doctrove_title, doctrove_links 
            FROM doctrove_papers 
            WHERE doctrove_links IS NOT NULL 
            AND doctrove_links != ''
            LIMIT 3
        """)
        
        samples = cursor.fetchall()
        logger.info("=== SAMPLE LINKS ===")
        for source, title, links in samples:
            logger.info(f"{source}: {title[:50]}... -> {links[:100]}...")
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    try:
        logger.info("Starting doctrove_links population patch...")
        results = populate_links_from_metadata()
        verify_results()
        logger.info("Patch completed successfully!")
        
    except Exception as e:
        logger.error(f"Patch failed: {e}")
        exit(1) 