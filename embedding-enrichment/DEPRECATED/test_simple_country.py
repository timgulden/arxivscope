#!/usr/bin/env python3
"""
Simple test for country enrichment SQL
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

def test_simple_country_enrichment():
    connection_factory = create_connection_factory()
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            # Clear existing data
            cur.execute("DELETE FROM openalex_enrichment_country;")
            
            # Simple test query with explicit jsonb casts
            insert_sql = """
                INSERT INTO openalex_enrichment_country (doctrove_paper_id, openalex_country_country, openalex_country_uschina)
                SELECT 
                    om.doctrove_paper_id,
                    CASE 
                        WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 = 'US' THEN 'United States'
                        WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 = 'CN' THEN 'China'
                        ELSE 'Unknown'
                    END as country_name,
                    CASE 
                        WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 IN ('US', 'CN') THEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0
                        WHEN (om.openalex_raw_data::jsonb)->'authorships'->0->'countries'->>0 IS NOT NULL THEN 'Rest of the World'
                        ELSE 'Unknown'
                    END as uschina
                FROM openalex_metadata om
                LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                WHERE ec.doctrove_paper_id IS NULL
                LIMIT %s;
            """
            
            cur.execute(insert_sql, (10,))
            processed_count = cur.rowcount
            
            conn.commit()
            
            print(f"Processed {processed_count} papers successfully!")

if __name__ == "__main__":
    test_simple_country_enrichment()
