#!/usr/bin/env python3
"""
Ultra-Fast SQL Country Enrichment Service
Uses pure SQL for lightning-fast processing - no slow status checks!
- Zero LLM calls
- Pure SQL bulk operations
- No expensive COUNT queries
- Just process papers efficiently
"""

import sys
import os
import logging
import time
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Batch processing configuration
SMALL_BATCH_SIZE = 1000      # Fast processing for small batches
MEDIUM_BATCH_SIZE = 5000     # Balanced approach for medium batches
LARGE_BATCH_SIZE = 50000     # Efficient bulk processing for large batches

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def create_table_if_needed(connection_factory) -> None:
    """Create the simplified country enrichment table if it doesn't exist."""
    create_sql = """
        CREATE TABLE IF NOT EXISTS openalex_enrichment_country (
            doctrove_paper_id UUID PRIMARY KEY,
            openalex_country_country TEXT,
            openalex_country_uschina TEXT
        );
    """
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()
    logger.info("Country enrichment table ready")

def has_papers_needing_enrichment(connection_factory) -> bool:
    """
    Ultra-fast check: just see if there are ANY papers needing enrichment.
    Returns True/False instead of exact count.
    """
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Just check if there's at least one paper needing enrichment
                cur.execute("""
                    SELECT 1 FROM openalex_metadata om
                    LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                    WHERE ec.doctrove_paper_id IS NULL
                    LIMIT 1
                """)
                return cur.fetchone() is not None
                
    except Exception as e:
        logger.error(f"Error checking for papers needing enrichment: {e}")
        return False

# ============================================================================
# OPTIMIZED SQL PROCESSING FUNCTIONS
# ============================================================================

def process_country_enrichment_sql_fast(connection_factory, batch_size: int) -> Dict[str, Any]:
    """
    Fast SQL processing for small batches (1K-5K records).
    Uses simple, optimized SQL for maximum speed.
    """
    start_time = datetime.now()
    
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Fast SQL: Direct INSERT with inline country mapping
                insert_sql = """
                    INSERT INTO openalex_enrichment_country (doctrove_paper_id, openalex_country_country, openalex_country_uschina)
                    SELECT 
                        om.doctrove_paper_id,
                        CASE 
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'US' THEN 'United States'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CN' THEN 'China'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GB' THEN 'United Kingdom'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'DE' THEN 'Germany'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FR' THEN 'France'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CA' THEN 'Canada'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AU' THEN 'Australia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'JP' THEN 'Japan'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IN' THEN 'India'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BR' THEN 'Brazil'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IT' THEN 'Italy'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ES' THEN 'Spain'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NL' THEN 'Netherlands'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SE' THEN 'Sweden'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CH' THEN 'Switzerland'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'KR' THEN 'South Korea'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'RU' THEN 'Russia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SG' THEN 'Singapore'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IL' THEN 'Israel'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NO' THEN 'Norway'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'DK' THEN 'Denmark'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FI' THEN 'Finland'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BE' THEN 'Belgium'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AT' THEN 'Austria'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IE' THEN 'Ireland'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NZ' THEN 'New Zealand'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PL' THEN 'Poland'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PT' THEN 'Portugal'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GR' THEN 'Greece'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CZ' THEN 'Czech Republic'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'HU' THEN 'Hungary'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TR' THEN 'Turkey'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MX' THEN 'Mexico'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AR' THEN 'Argentina'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CL' THEN 'Chile'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CO' THEN 'Colombia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PE' THEN 'Peru'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'VE' THEN 'Venezuela'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ZA' THEN 'South Africa'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'EG' THEN 'Egypt'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NG' THEN 'Nigeria'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'KE' THEN 'Kenya'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GH' THEN 'Ghana'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ET' THEN 'Ethiopia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'UG' THEN 'Uganda'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TZ' THEN 'Tanzania'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MW' THEN 'Malawi'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ZM' THEN 'Zambia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ZW' THEN 'Zimbabwe'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BW' THEN 'Botswana'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NA' THEN 'Namibia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LS' THEN 'Lesotho'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SZ' THEN 'Eswatini'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MG' THEN 'Madagascar'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MU' THEN 'Mauritius'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SC' THEN 'Seychelles'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'DJ' THEN 'Djibouti'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SO' THEN 'Somalia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ER' THEN 'Eritrea'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SD' THEN 'Sudan'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SS' THEN 'South Sudan'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CF' THEN 'Central African Republic'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TD' THEN 'Chad'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CM' THEN 'Cameroon'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'UY' THEN 'Uruguay'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PY' THEN 'Paraguay'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BO' THEN 'Bolivia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'EC' THEN 'Ecuador'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GY' THEN 'Guyana'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SR' THEN 'Suriname'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FK' THEN 'Falkland Islands'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GF' THEN 'French Guiana'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'RO' THEN 'Romania'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BG' THEN 'Bulgaria'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'HR' THEN 'Croatia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SI' THEN 'Slovenia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SK' THEN 'Slovakia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'EE' THEN 'Estonia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LV' THEN 'Latvia'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LT' THEN 'Lithuania'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MT' THEN 'Malta'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CY' THEN 'Cyprus'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LU' THEN 'Luxembourg'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MC' THEN 'Monaco'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LI' THEN 'Liechtenstein'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SM' THEN 'San Marino'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'VA' THEN 'Vatican City'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AD' THEN 'Andorra'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IS' THEN 'Iceland'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FO' THEN 'Faroe Islands'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GL' THEN 'Greenland'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SJ' THEN 'Svalbard and Jan Mayen'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AX' THEN 'Åland Islands'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GI' THEN 'Gibraltar'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'JE' THEN 'Jersey'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GG' THEN 'Guernsey'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IM' THEN 'Isle of Man'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IO' THEN 'British Indian Ocean Territory'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SH' THEN 'Saint Helena'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AC' THEN 'Ascension Island'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TA' THEN 'Tristan da Cunha'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GS' THEN 'South Georgia and the South Sandwich Islands'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BV' THEN 'Bouvet Island'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TF' THEN 'French Southern Territories'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'HM' THEN 'Heard Island and McDonald Islands'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AQ' THEN 'Antarctica'
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 = 'UM' THEN 'United States Minor Outlying Islands'
                            ELSE 'Unknown'
                        END as country_name,
                        CASE 
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 IN ('US', 'CN') THEN om.openalex_raw_data->'authorships'->0->'countries'->>0
                            WHEN om.openalex_raw_data->'authorships'->0->'countries'->>0 IS NOT NULL THEN 'Rest of the World'
                            ELSE 'Unknown'
                        END as uschina
                    FROM openalex_metadata om
                    LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                    WHERE ec.doctrove_paper_id IS NULL
                    LIMIT %s;
                """
                
                cur.execute(insert_sql, (batch_size,))
                processed_count = cur.rowcount
                
                conn.commit()
                
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Fast SQL processing: {processed_count} papers in {processing_time:.3f}s")
                
                return {
                    'processed': processed_count,
                    'processing_time': processing_time,
                    'strategy': 'fast_sql'
                }
                
    except Exception as e:
        logger.error(f"Error in fast SQL processing: {e}")
        return {
            'processed': 0,
            'processing_time': 0,
            'strategy': 'fast_sql',
            'error': str(e)
        }

def process_country_enrichment_sql_bulk(connection_factory, batch_size: int) -> Dict[str, Any]:
    """
    Efficient bulk SQL processing for large batches (10K+ records).
    Uses CTEs for optimal performance.
    """
    start_time = datetime.now()
    
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Bulk SQL: Use CTE for efficient processing
                insert_sql = """
                    WITH papers_to_process AS (
                        SELECT om.doctrove_paper_id, om.openalex_raw_data
                        FROM openalex_metadata om
                        LEFT JOIN openalex_enrichment_country ec ON om.doctrove_paper_id = ec.doctrove_paper_id
                        WHERE ec.doctrove_paper_id IS NULL
                        LIMIT %s
                    )
                    INSERT INTO openalex_enrichment_country (doctrove_paper_id, openalex_country_country, openalex_country_uschina)
                    SELECT 
                        ptp.doctrove_paper_id,
                        CASE 
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'US' THEN 'United States'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CN' THEN 'China'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GB' THEN 'United Kingdom'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'DE' THEN 'Germany'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FR' THEN 'France'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CA' THEN 'Canada'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AU' THEN 'Australia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'JP' THEN 'Japan'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IN' THEN 'India'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BR' THEN 'Brazil'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IT' THEN 'Italy'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ES' THEN 'Spain'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NL' THEN 'Netherlands'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SE' THEN 'Sweden'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CH' THEN 'Switzerland'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'KR' THEN 'South Korea'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'RU' THEN 'Russia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SG' THEN 'Singapore'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IL' THEN 'Israel'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NO' THEN 'Norway'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'DK' THEN 'Denmark'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FI' THEN 'Finland'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BE' THEN 'Belgium'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AT' THEN 'Austria'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IE' THEN 'Ireland'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NZ' THEN 'New Zealand'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PL' THEN 'Poland'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PT' THEN 'Portugal'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GR' THEN 'Greece'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CZ' THEN 'Czech Republic'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'HU' THEN 'Hungary'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TR' THEN 'Turkey'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MX' THEN 'Mexico'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AR' THEN 'Argentina'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CL' THEN 'Chile'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CO' THEN 'Colombia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PE' THEN 'Peru'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'VE' THEN 'Venezuela'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ZA' THEN 'South Africa'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'EG' THEN 'Egypt'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NG' THEN 'Nigeria'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'KE' THEN 'Kenya'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GH' THEN 'Ghana'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ET' THEN 'Ethiopia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'UG' THEN 'Uganda'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TZ' THEN 'Tanzania'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MW' THEN 'Malawi'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ZM' THEN 'Zambia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ZW' THEN 'Zimbabwe'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BW' THEN 'Botswana'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'NA' THEN 'Namibia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LS' THEN 'Lesotho'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SZ' THEN 'Eswatini'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MG' THEN 'Madagascar'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MU' THEN 'Mauritius'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SC' THEN 'Seychelles'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'DJ' THEN 'Djibouti'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SO' THEN 'Somalia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'ER' THEN 'Eritrea'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SD' THEN 'Sudan'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SS' THEN 'South Sudan'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CF' THEN 'Central African Republic'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TD' THEN 'Chad'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CM' THEN 'Cameroon'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'UY' THEN 'Uruguay'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'PY' THEN 'Paraguay'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BO' THEN 'Bolivia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'EC' THEN 'Ecuador'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GY' THEN 'Guyana'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SR' THEN 'Suriname'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FK' THEN 'Falkland Islands'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GF' THEN 'French Guiana'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'RO' THEN 'Romania'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BG' THEN 'Bulgaria'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'HR' THEN 'Croatia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SI' THEN 'Slovenia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SK' THEN 'Slovakia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'EE' THEN 'Estonia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LV' THEN 'Latvia'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LT' THEN 'Lithuania'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MT' THEN 'Malta'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'CY' THEN 'Cyprus'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LU' THEN 'Luxembourg'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'MC' THEN 'Monaco'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'LI' THEN 'Liechtenstein'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SM' THEN 'San Marino'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'VA' THEN 'Vatican City'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AD' THEN 'Andorra'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IS' THEN 'Iceland'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'FO' THEN 'Faroe Islands'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GL' THEN 'Greenland'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SJ' THEN 'Svalbard and Jan Mayen'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AX' THEN 'Åland Islands'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GI' THEN 'Gibraltar'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'JE' THEN 'Jersey'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GG' THEN 'Guernsey'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IM' THEN 'Isle of Man'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'IO' THEN 'British Indian Ocean Territory'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'SH' THEN 'Saint Helena'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AC' THEN 'Ascension Island'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TA' THEN 'Tristan da Cunha'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'GS' THEN 'South Georgia and the South Sandwich Islands'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'BV' THEN 'Bouvet Island'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'TF' THEN 'French Southern Territories'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'HM' THEN 'Heard Island and McDonald Islands'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'AQ' THEN 'Antarctica'
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 = 'UM' THEN 'United States Minor Outlying Islands'
                            ELSE 'Unknown'
                        END as country_name,
                        CASE 
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 IN ('US', 'CN') THEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0
                            WHEN ptp.openalex_raw_data->'authorships'->0->'countries'->>0 IS NOT NULL THEN 'Rest of the World'
                            ELSE 'Unknown'
                        END as uschina
                    FROM papers_to_process ptp;
                """
                
                cur.execute(insert_sql, (batch_size,))
                processed_count = cur.rowcount
                
                conn.commit()
                
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Bulk SQL processing: {processed_count} papers in {processing_time:.3f}s")
                
                return {
                    'processed': processed_count,
                    'processing_time': processing_time,
                    'strategy': 'bulk_sql'
                }
                
    except Exception as e:
        logger.error(f"Error in bulk SQL processing: {e}")
        return {
            'processed': 0,
            'processing_time': 0,
            'strategy': 'bulk_sql',
            'error': str(e)
        }

def process_country_enrichment_sql(connection_factory, batch_size: int, strategy: str = 'auto') -> Dict[str, Any]:
    """
    Process country enrichment using optimized SQL strategies.
    
    Args:
        connection_factory: Database connection factory
        batch_size: Number of papers to process
        strategy: SQL strategy to use ('fast', 'bulk', or 'auto')
    
    Returns:
        Dictionary with processing results
    """
    # Auto-select strategy based on batch size
    if strategy == 'auto':
        if batch_size <= MEDIUM_BATCH_SIZE:
            strategy = 'fast'
        else:
            strategy = 'bulk'
    
    # Process using selected strategy
    if strategy == 'fast':
        return process_country_enrichment_sql_fast(connection_factory, batch_size)
    elif strategy == 'bulk':
        return process_country_enrichment_sql_bulk(connection_factory, batch_size)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

# ============================================================================
# SMART BATCHING AND BACKGROUND PROCESSING
# ============================================================================

def smart_country_enrichment_cycle(connection_factory) -> Dict[str, Any]:
    """
    Smart enrichment cycle that adapts to workload size.
    Chooses optimal SQL strategy and batch size automatically.
    """
    # Ensure table exists
    create_table_if_needed(connection_factory)
    
    # Quick check if there's work to do
    has_work = has_papers_needing_enrichment(connection_factory)
    
    if not has_work:
        return {
            'status': 'caught_up',
            'processed': 0,
            'batch_size': 0,
            'strategy': 'none'
        }
    
    # For now, just process a medium batch - we can optimize this later
    batch_size = MEDIUM_BATCH_SIZE
    strategy = 'fast'
    
    logger.info(f"Processing {batch_size} papers with {strategy} SQL strategy")
    
    # Process enrichment
    results = process_country_enrichment_sql(connection_factory, batch_size, strategy)
    
    return {
        'status': 'processing',  # Assume there's more work
        'processed': results['processed'],
        'batch_size': batch_size,
        'strategy': results['strategy'],
        'processing_time': results.get('processing_time', 0)
    }

def background_country_enrichment(connection_factory, check_interval: int = 60) -> None:
    """
    Background enrichment service that runs continuously.
    Adapts sleep time based on workload.
    """
    logger.info("Starting background country enrichment service")
    
    while True:
        try:
            # Run enrichment cycle
            results = smart_country_enrichment_cycle(connection_factory)
            
            if results['status'] == 'caught_up':
                # No work to do - sleep longer
                logger.debug("Background: Caught up, sleeping 5 minutes")
                time.sleep(300)  # 5 minutes
            else:
                # Work was done - check again soon
                logger.info(f"Background: Processed {results['processed']} papers in {results.get('processing_time', 0):.3f}s")
                logger.debug(f"Background: Sleeping {check_interval}s before next check")
                time.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"Background enrichment error: {e}")
            time.sleep(check_interval)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the ultra-fast SQL-based country enrichment service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ultra-Fast SQL Country Enrichment Service')
    parser.add_argument('--batch-size', type=int, default=SMALL_BATCH_SIZE,
                       help=f'Batch size for processing (default: {SMALL_BATCH_SIZE})')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of papers to process (for testing)')
    parser.add_argument('--strategy', choices=['fast', 'bulk', 'auto'], default='auto',
                       help='SQL strategy to use (default: auto)')
    parser.add_argument('--background', action='store_true',
                       help='Run as background service')
    
    args = parser.parse_args()
    
    # Setup database connection
    connection_factory = create_connection_factory()
    
    if args.background:
        # Run as background service
        print("Starting background country enrichment service...")
        print("Press Ctrl+C to stop")
        try:
            background_country_enrichment(connection_factory)
        except KeyboardInterrupt:
            print("\nBackground service stopped")
        return
    
    # Process enrichment
    if args.limit:
        batch_size = min(args.batch_size, args.limit)
    else:
        batch_size = args.batch_size
    
    print(f"Processing country enrichment with batch size {batch_size} using {args.strategy} strategy...")
    
    start_time = datetime.now()
    results = process_country_enrichment_sql(connection_factory, batch_size, args.strategy)
    total_time = (datetime.now() - start_time).total_seconds()
    
    print(f"\n=== Ultra-Fast SQL Country Enrichment Results ===")
    print(f"Papers processed: {results['processed']}")
    print(f"Processing time: {results.get('processing_time', 0):.3f}s")
    print(f"Total time: {total_time:.3f}s")
    print(f"SQL strategy: {results['strategy']}")
    if results.get('processing_time', 0) > 0:
        print(f"Performance: {results['processed'] / results['processing_time']:.0f} papers/second")

if __name__ == "__main__":
    main()
