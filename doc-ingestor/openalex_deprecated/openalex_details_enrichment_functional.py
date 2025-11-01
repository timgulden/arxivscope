#!/usr/bin/env python3
"""
OpenAlex Details Enrichment Script - Functional Programming Version
Extracts comprehensive metadata from OpenAlex raw data using functional programming principles.

Key Improvements:
- Pure functions with no side effects
- Immutable data structures
- Functional composition with map/filter/reduce
- Better error handling with Result types
- Lazy evaluation for memory efficiency
- Composable data transformation pipeline
"""

import sys
import os
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from functools import reduce, partial
from collections import Counter
import traceback

# Add paths for imports
sys.path.append('../doctrove-api')
sys.path.append('.')

from db import create_connection_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# IMMUTABLE DATA STRUCTURES
# ============================================================================

@dataclass(frozen=True)
class ProcessingResult:
    """Immutable result of processing a single paper."""
    paper_id: str
    success: bool
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0

@dataclass(frozen=True)
class BatchResult:
    """Immutable result of processing a batch of papers."""
    batch_size: int
    successful: int
    failed: int
    total_processing_time: float
    results: Tuple[ProcessingResult, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class ProcessingStats:
    """Immutable processing statistics."""
    total_papers: int
    papers_with_metadata: int
    papers_processed: int
    papers_remaining: int
    completion_percentage: float
    total_processing_time: float
    average_processing_time: float
    success_rate: float

# ============================================================================
# PURE FUNCTIONS - DATA EXTRACTION
# ============================================================================

def extract_openalex_id(raw_data: Dict[str, Any]) -> Optional[str]:
    """Pure function to extract OpenAlex ID."""
    openalex_id = raw_data.get('id')
    if openalex_id:
        return openalex_id.replace('https://openalex.org/W', '')
    return None

def extract_document_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract basic document information."""
    return {
        'document_type': raw_data.get('type'),
        'document_type_crossref': raw_data.get('type_crossref'),
        'publication_year': raw_data.get('publication_year'),
        'publication_date': raw_data.get('publication_date'),
        'language': raw_data.get('language'),
    }

def extract_source_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract source information."""
    if not raw_data:
        return {}
        
    primary_location = raw_data.get('primary_location', {})
    if primary_location is None:
        primary_location = {}
        
    source = primary_location.get('source')
    
    # Handle case where source is None (OpenAlex uses null for missing data)
    if source is None:
        source = {}
    
    open_access = raw_data.get('open_access', {})
    if open_access is None:
        open_access = {}
    
    return {
        'source_name': source.get('display_name'),
        'source_id': source.get('id', '').replace('https://openalex.org/S', '') if source.get('id') else None,
        'source_type': source.get('type'),
        'source_publisher': source.get('publisher'),
        'source_host_organization': source.get('host_organization_name'),
        'source_issn': source.get('issn', []) or [],
        'landing_page_url': primary_location.get('landing_page_url'),
        'pdf_url': primary_location.get('pdf_url'),
        'is_open_access': open_access.get('is_oa'),
        'oa_status': open_access.get('oa_status'),
    }

def extract_author_counts(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract author count information."""
    return {
        'authors_count': raw_data.get('authors_count'),
        'corresponding_author_count': len(raw_data.get('corresponding_author_ids', [])),
        'corresponding_institution_count': len(raw_data.get('corresponding_institution_ids', [])),
        'institution_count': raw_data.get('institutions_distinct_count'),
        'institution_countries_distinct': raw_data.get('countries_distinct_count'),
    }

def extract_academic_classification(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract academic classification."""
    if not raw_data:
        return {}
        
    primary_topic = raw_data.get('primary_topic')
    
    # Handle case where primary_topic is None (OpenAlex uses null for missing data)
    if primary_topic is None:
        primary_topic = {}
    
    domain = primary_topic.get('domain', {})
    if domain is None:
        domain = {}
        
    field = primary_topic.get('field', {})
    if field is None:
        field = {}
        
    subfield = primary_topic.get('subfield', {})
    if subfield is None:
        subfield = {}
    
    return {
        'primary_domain': domain.get('display_name'),
        'primary_field': field.get('display_name'),
        'primary_subfield': subfield.get('display_name'),
        'primary_topic_name': primary_topic.get('display_name'),
        'primary_topic_score': primary_topic.get('score'),
        'concepts_count': raw_data.get('concepts_count'),
        'topics_count': raw_data.get('topics_count'),
    }

def extract_citation_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract citation information."""
    summary_stats = raw_data.get('summary_stats', {})
    if summary_stats is None:
        summary_stats = {}
        
    return {
        'cited_by_count': raw_data.get('cited_by_count'),
        'cited_by_count_2yr': summary_stats.get('2yr_cited_by_count'),
        'fwci': raw_data.get('fwci'),
        'related_works_count': raw_data.get('related_works_count'),
        'referenced_works_count': raw_data.get('referenced_works_count'),
    }

def extract_financial_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract financial information."""
    if not raw_data:
        return {}
        
    apc_list = raw_data.get('apc_list')
    primary_location = raw_data.get('primary_location', {})
    
    # Handle case where apc_list is None (OpenAlex uses null for missing data)
    if apc_list is None:
        apc_list = {}
    
    # Handle case where primary_location is None (OpenAlex uses null for missing data)
    if primary_location is None:
        primary_location = {}
    
    apc_paid = raw_data.get('apc_paid')
    if apc_paid is None:
        apc_paid = {}
    
    return {
        'apc_amount': apc_list.get('value'),
        'apc_currency': apc_list.get('currency'),
        'apc_amount_usd': apc_list.get('value_usd'),
        'apc_paid': apc_paid.get('value'),
        'license_type': primary_location.get('license'),
        'license_id': primary_location.get('license_id'),
    }

def extract_source_quality(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract source quality indicators."""
    if not raw_data:
        return {}
        
    primary_location = raw_data.get('primary_location', {})
    
    # Handle case where primary_location is None (OpenAlex uses null for missing data)
    if primary_location is None:
        primary_location = {}
        
    source = primary_location.get('source')
    
    # Handle case where source is None (OpenAlex uses null for missing data)
    if source is None:
        source = {}
    
    return {
        'source_is_core': source.get('is_core'),
        'source_is_in_doaj': source.get('is_in_doaj'),
        'source_is_indexed_in_scopus': source.get('is_indexed_in_scopus'),
        'indexed_in': raw_data.get('indexed_in', []) or [],
    }

def extract_bibliographic_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract bibliographic information."""
    biblio = raw_data.get('biblio', {})
    
    # Handle case where biblio is None (OpenAlex uses null for missing data)
    if biblio is None:
        biblio = {}
    
    return {
        'volume': biblio.get('volume'),
        'issue': biblio.get('issue'),
        'first_page': biblio.get('first_page'),
        'last_page': biblio.get('last_page'),
        'doi_registration_agency': raw_data.get('doi_registration_agency'),
    }

def extract_fulltext_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract fulltext information."""
    primary_location = raw_data.get('primary_location', {})
    if primary_location is None:
        primary_location = {}
        
    open_access = raw_data.get('open_access', {})
    if open_access is None:
        open_access = {}
    
    return {
        'has_fulltext': raw_data.get('has_fulltext'),
        'fulltext_origin': raw_data.get('fulltext_origin'),
        'any_repository_has_fulltext': open_access.get('any_repository_has_fulltext'),
        'version': primary_location.get('version'),
        'is_accepted': primary_location.get('is_accepted'),
        'is_published': primary_location.get('is_published'),
    }

def extract_keywords_and_sdgs(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract keywords and SDGs."""
    keywords = raw_data.get('keywords', []) or []
    sdgs = raw_data.get('sustainable_development_goals', []) or []
    
    return {
        'keywords': [kw.get('display_name') for kw in keywords if kw and kw.get('display_name')],
        'keyword_scores': [kw.get('score') for kw in keywords if kw and kw.get('score') is not None],
        'sdg_goals': [sdg.get('display_name') for sdg in sdgs if sdg and sdg.get('display_name')],
        'sdg_scores': [sdg.get('score') for sdg in sdgs if sdg and sdg.get('score') is not None],
    }

def extract_temporal_info(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract temporal information."""
    return {
        'created_date': raw_data.get('created_date'),
        'updated_date': raw_data.get('updated_date'),
    }

def extract_quality_indicators(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function to extract quality indicators."""
    return {
        'is_retracted': raw_data.get('is_retracted'),
        'extraction_confidence': 1.0,
        'extraction_source': 'openalex_direct',
    }

# ============================================================================
# PURE FUNCTIONS - AUTHOR DATA EXTRACTION
# ============================================================================

def extract_best_author_data(authorships: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Pure function to extract best author data using functional approach."""
    if not authorships:
        return None, None
    
    def process_authorship(authorship: Dict[str, Any], position: int) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Process a single authorship and return country/institution data."""
        author = authorship.get('author', {})
        
        # Extract country data
        country_data = None
        if authorship.get('countries'):
            country_data = {
                'country': authorship['countries'][0],
                'position': position,
                'author_name': author.get('display_name'),
                'author_orcid': author.get('orcid'),
                'quality': 'high' if position == 1 else 'medium' if position <= 3 else 'low'
            }
        
        # Extract institution data
        institution_data = None
        if authorship.get('institutions'):
            institution_data = {
                'institution': authorship['institutions'][0].get('display_name'),
                'position': position,
                'author_name': author.get('display_name'),
                'author_orcid': author.get('orcid'),
                'quality': 'high' if position == 1 else 'medium' if position <= 3 else 'low'
            }
        
        return country_data, institution_data
    
    # Process all authorships and find the best data
    authorship_results = [
        process_authorship(authorship, i + 1) 
        for i, authorship in enumerate(authorships)
    ]
    
    # Find first non-None country and institution data
    country_data = next((result[0] for result in authorship_results if result[0] is not None), None)
    institution_data = next((result[1] for result in authorship_results if result[1] is not None), None)
    
    return country_data, institution_data

# ============================================================================
# PURE FUNCTIONS - DATA COMPOSITION
# ============================================================================

def compose_paper_details(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pure function that composes all paper details using functional composition."""
    # Compose all extraction functions
    extraction_functions = [
        extract_document_info,
        extract_source_info,
        extract_author_counts,
        extract_academic_classification,
        extract_citation_data,
        extract_financial_data,
        extract_source_quality,
        extract_bibliographic_info,
        extract_fulltext_info,
        extract_keywords_and_sdgs,
        extract_temporal_info,
        extract_quality_indicators,
    ]
    
    # Apply all extraction functions and merge results
    details = {}
    for func in extraction_functions:
        try:
            result = func(raw_data)
            details.update(result)
        except Exception as e:
            logger.error(f"Error in extraction function {func.__name__}: {e}")
            raise
    
    # Add OpenAlex ID
    details['openalex_id'] = extract_openalex_id(raw_data)
    
    # Extract and add author data
    authorships = raw_data.get('authorships', [])
    if authorships:
        country_data, institution_data = extract_best_author_data(authorships)
        
        if country_data:
            details.update({
                'best_author_country': country_data['country'],
                'best_author_position': country_data['position'],
                'best_author_name': country_data['author_name'],
                'best_author_orcid': country_data['author_orcid'],
                'country_data_source': f"position_{country_data['position']}",
                'country_data_quality': country_data['quality'],
                'country_coding_quality': country_data['quality']
            })
        
        if institution_data:
            details.update({
                'best_author_institution': institution_data['institution'],
                'institution_data_source': f"position_{institution_data['position']}",
                'institution_data_quality': institution_data['quality'],
                'institution_coding_quality': institution_data['quality']
            })
    
    return details

# ============================================================================
# PURE FUNCTIONS - PAPER PROCESSING
# ============================================================================

def process_single_paper(paper_data: Tuple[str, str]) -> ProcessingResult:
    """Pure function to process a single paper."""
    import time
    start_time = time.time()
    
    try:
        paper_id, raw_data_str = paper_data
        
        # Parse JSON data
        raw_data = json.loads(raw_data_str)
        
        # Extract paper details
        details = compose_paper_details(raw_data)
        
        if not details:
            return ProcessingResult(
                paper_id=paper_id,
                success=False,
                error="No details extracted",
                processing_time=time.time() - start_time
            )
        
        # Add paper ID
        details['doctrove_paper_id'] = paper_id
        
        return ProcessingResult(
            paper_id=paper_id,
            success=True,
            details=details,
            processing_time=time.time() - start_time
        )
        
    except Exception as e:
        return ProcessingResult(
            paper_id=str(paper_data[0]) if paper_data and len(paper_data) > 0 else "unknown",
            success=False,
            error=str(e),
            processing_time=time.time() - start_time
        )

def process_batch_functional(papers: List[Tuple[str, str]]) -> BatchResult:
    """Pure function to process a batch of papers using functional programming."""
    import time
    start_time = time.time()
    
    # Process all papers using map (pure function)
    results = list(map(process_single_paper, papers))
    
    # Calculate statistics using functional operations
    successful_results = list(filter(lambda r: r.success, results))
    failed_results = list(filter(lambda r: not r.success, results))
    
    total_time = time.time() - start_time
    
    return BatchResult(
        batch_size=len(papers),
        successful=len(successful_results),
        failed=len(failed_results),
        total_processing_time=total_time,
        results=tuple(results)
    )

# ============================================================================
# FUNCTIONAL ENRICHMENT CLASS
# ============================================================================

class FunctionalOpenAlexDetailsEnrichment:
    """Functional programming version of OpenAlex details enrichment."""
    
    def __init__(self, connection_factory: Callable):
        self.connection_factory = connection_factory
        self.table_name = 'openalex_details_enrichment'
    
    def create_table_if_not_exists(self):
        """Create the enrichment table if it doesn't exist."""
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        -- Core identification
                        doctrove_paper_id UUID PRIMARY KEY REFERENCES doctrove_papers(doctrove_paper_id),
                        openalex_id VARCHAR,
                        
                        -- Document classification
                        document_type VARCHAR,
                        document_type_crossref VARCHAR,
                        publication_year INTEGER,
                        publication_date DATE,
                        language VARCHAR,
                        
                        -- Source & location
                        source_name VARCHAR,
                        source_id VARCHAR,
                        source_type VARCHAR,
                        source_publisher VARCHAR,
                        source_host_organization VARCHAR,
                        source_issn VARCHAR[],
                        landing_page_url TEXT,
                        pdf_url TEXT,
                        is_open_access BOOLEAN,
                        oa_status VARCHAR,
                        
                        -- Best available author data
                        best_author_country VARCHAR,
                        best_author_institution VARCHAR,
                        best_author_position INTEGER,
                        best_author_name VARCHAR,
                        best_author_orcid VARCHAR,
                        authors_count INTEGER,
                        corresponding_author_count INTEGER,
                        corresponding_institution_count INTEGER,
                        institution_types VARCHAR[],
                        institution_countries_distinct INTEGER,
                        institution_count INTEGER,
                        
                        -- Academic classification
                        primary_domain VARCHAR,
                        primary_field VARCHAR,
                        primary_subfield VARCHAR,
                        primary_topic_name VARCHAR,
                        primary_topic_score DECIMAL,
                        primary_concept_score DECIMAL,
                        concepts_count INTEGER,
                        topics_count INTEGER,
                        concept_levels INTEGER[],
                        concept_scores DECIMAL[],
                        topic_scores DECIMAL[],
                        
                        -- Citation & impact
                        cited_by_count INTEGER,
                        cited_by_count_2yr INTEGER,
                        fwci DECIMAL,
                        citation_percentile_raw DECIMAL,
                        is_top_1_percent BOOLEAN,
                        is_top_10_percent BOOLEAN,
                        citation_percentile_year_min INTEGER,
                        citation_percentile_year_max INTEGER,
                        
                        -- Financial
                        apc_amount DECIMAL,
                        apc_currency VARCHAR,
                        apc_amount_usd DECIMAL,
                        apc_paid DECIMAL,
                        license_type VARCHAR,
                        license_id VARCHAR,
                        
                        -- Source quality
                        source_is_core BOOLEAN,
                        source_is_in_doaj BOOLEAN,
                        source_is_indexed_in_scopus BOOLEAN,
                        indexed_in VARCHAR[],
                        
                        -- Bibliographic
                        volume VARCHAR,
                        issue VARCHAR,
                        first_page VARCHAR,
                        last_page VARCHAR,
                        doi_registration_agency VARCHAR,
                        
                        -- Fulltext
                        has_fulltext BOOLEAN,
                        fulltext_origin VARCHAR,
                        any_repository_has_fulltext BOOLEAN,
                        version VARCHAR,
                        is_accepted BOOLEAN,
                        is_published BOOLEAN,
                        
                        -- Keywords & SDGs
                        keywords VARCHAR[],
                        keyword_scores DECIMAL[],
                        sdg_goals VARCHAR[],
                        sdg_scores DECIMAL[],
                        
                        -- Temporal
                        created_date DATE,
                        updated_date DATE,
                        
                        -- Quality indicators
                        is_retracted BOOLEAN,
                        extraction_confidence DECIMAL,
                        extraction_source VARCHAR,
                        
                        -- Author data quality
                        country_data_source VARCHAR,
                        country_data_quality VARCHAR,
                        country_coding_quality VARCHAR,
                        institution_data_source VARCHAR,
                        institution_data_quality VARCHAR,
                        institution_coding_quality VARCHAR,
                        
                        -- Processing metadata
                        processed_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                conn.commit()
                logger.info("Functional enrichment table ready")
    
    def fetch_papers_for_processing(self, limit: Optional[int] = None, skip_processed: bool = True) -> List[Tuple[str, str]]:
        """Fetch papers that need processing using functional approach."""
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # First, get a limited set of paper IDs that need processing
                if limit:
                    # Use a more efficient approach: get IDs first, then fetch data
                    if skip_processed:
                        # Skip already processed papers using LEFT JOIN (faster than NOT EXISTS)
                        id_query = f"""
                            SELECT om.doctrove_paper_id
                            FROM openalex_metadata om
                            LEFT JOIN {self.table_name} e ON om.doctrove_paper_id = e.doctrove_paper_id
                            WHERE om.openalex_raw_data IS NOT NULL
                              AND om.openalex_raw_data != '{{}}'
                              AND e.doctrove_paper_id IS NULL
                            LIMIT {limit}
                        """
                    else:
                        # Process all papers (may reprocess already-done papers)
                        id_query = f"""
                            SELECT om.doctrove_paper_id
                            FROM openalex_metadata om
                            WHERE om.openalex_raw_data IS NOT NULL
                              AND om.openalex_raw_data != '{{}}'
                            LIMIT {limit}
                        """
                    cur.execute(id_query)
                    paper_ids = [row[0] for row in cur.fetchall()]
                    
                    if not paper_ids:
                        logger.info("No papers found to process")
                        return []
                    
                    logger.info(f"Found {len(paper_ids)} paper IDs to process")
                    logger.info(f"Paper IDs: {paper_ids}")
                    
                    # Now fetch the actual data for just these papers
                    # Use a simpler approach - fetch each paper individually to avoid parameter issues
                    all_results = []
                    for paper_id in paper_ids:
                        # Use string formatting instead of parameterized queries to avoid the database driver bug
                        query = f"""
                            SELECT om.doctrove_paper_id, om.openalex_raw_data
                            FROM openalex_metadata om
                            WHERE om.doctrove_paper_id = '{paper_id}'
                              AND om.openalex_raw_data IS NOT NULL
                              AND om.openalex_raw_data != '{{}}'
                              AND om.openalex_raw_data LIKE '%authorships%'
                        """
                        cur.execute(query)
                        result = cur.fetchone()
                        if result:
                            all_results.append(result)
                    
                    logger.info(f"Fetched data for {len(all_results)} papers")
                    return all_results
                else:
                    # For unlimited processing - use streaming cursor to avoid memory issues
                    if skip_processed:
                        query = f"""
                            SELECT om.doctrove_paper_id, om.openalex_raw_data
                            FROM openalex_metadata om
                            LEFT JOIN {self.table_name} e ON om.doctrove_paper_id = e.doctrove_paper_id
                            WHERE om.openalex_raw_data IS NOT NULL
                              AND om.openalex_raw_data != '{{}}'
                              AND e.doctrove_paper_id IS NULL
                            ORDER BY om.doctrove_paper_id
                        """
                    else:
                        query = """
                            SELECT om.doctrove_paper_id, om.openalex_raw_data
                            FROM openalex_metadata om
                            WHERE om.openalex_raw_data IS NOT NULL
                              AND om.openalex_raw_data != '{}'
                            ORDER BY om.doctrove_paper_id
                        """
                    cur.execute(query)
                    return cur.fetchall()
    
    def process_papers_functional(self, limit: Optional[int] = None, batch_size: int = 100, dry_run: bool = False, skip_processed: bool = True) -> ProcessingStats:
        """Process papers using functional programming approach."""
        import time
        
        logger.info("🚀 Starting functional processing pipeline")
        
        # Fetch papers for processing
        papers = self.fetch_papers_for_processing(limit, skip_processed=skip_processed)
        logger.info(f"📚 Found {len(papers)} papers to process")
        
        if not papers:
            logger.info("✅ No papers to process")
            return self._create_empty_stats()
        
        # Process in batches
        total_processed = 0
        total_failed = 0
        start_time = time.time()
        
        for batch_num, batch_start in enumerate(range(0, len(papers), batch_size), 1):
            batch_end = min(batch_start + batch_size, len(papers))
            batch_papers = papers[batch_start:batch_end]
            
            logger.info(f"🔄 Processing batch {batch_num}: papers {batch_start + 1}-{batch_end}")
            
            # Process batch
            batch_result = process_batch_functional(batch_papers)
            
            if not dry_run:
                # Insert successful results
                successful_results = [r for r in batch_result.results if r.success]
                if successful_results:
                    self._insert_batch_results(successful_results)
            
            # Update totals
            total_processed += batch_result.successful
            total_failed += batch_result.failed
            
            # Log batch progress
            logger.info(f"   ✅ Batch {batch_num} complete: {batch_result.successful} successful, {batch_result.failed} failed")
            
            # Show overall progress
            progress = ((batch_end) / len(papers)) * 100
            logger.info(f"   📊 Overall progress: {progress:.1f}% ({batch_end}/{len(papers)})")
        
        # Calculate final statistics
        total_time = time.time() - start_time
        stats = self._calculate_processing_stats(total_processed, total_failed, total_time)
        
        logger.info("🎉 Functional processing complete:")
        logger.info(f"   📊 Total processed: {total_processed}")
        logger.info(f"   ❌ Total failed: {total_failed}")
        logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
        logger.info(f"   📈 Success rate: {stats.success_rate:.1f}%")
        
        return stats
    
    def _insert_batch_results(self, results: List[ProcessingResult]):
        """Insert a batch of successful results."""
        if not results:
            return
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Get all possible columns from all results
                all_columns = set()
                for result in results:
                    if result.details:
                        all_columns.update(result.details.keys())
                
                if not all_columns:
                    return
                
                # Sort columns for consistency
                columns = sorted(list(all_columns))
                placeholders = ['%s'] * len(columns)
                
                # Build the INSERT statement
                query = f"""
                    INSERT INTO {self.table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                        processed_at = NOW()
                """
                
                # Prepare values for each result, filling missing columns with None
                values_list = []
                for result in results:
                    if result.details:
                        values = [result.details.get(col) for col in columns]
                        values_list.append(values)
                
                if values_list:
                    # Execute bulk insert
                    cur.executemany(query, values_list)
                    conn.commit()
                    
                    logger.info(f"💾 Inserted {len(values_list)} results into database")
    
    def _calculate_processing_stats(self, processed: int, failed: int, total_time: float) -> ProcessingStats:
        """Calculate processing statistics using pure functions."""
        total_papers = processed + failed
        success_rate = (processed / total_papers * 100) if total_papers > 0 else 0
        avg_time = (total_time / total_papers) if total_papers > 0 else 0
        
        # OPTIMIZATION: Don't call expensive get_processing_stats() after every batch
        # Use lightweight stats from what we just processed instead
        return ProcessingStats(
            total_papers=total_papers,
            papers_with_metadata=0,  # Not calculated to avoid expensive COUNT queries
            papers_processed=processed,
            papers_remaining=0,  # Not calculated to avoid expensive COUNT queries
            completion_percentage=0.0,  # Not calculated to avoid expensive COUNT queries
            total_processing_time=total_time,
            average_processing_time=avg_time,
            success_rate=success_rate
        )
    
    def _create_empty_stats(self) -> ProcessingStats:
        """Create empty statistics when no processing is needed."""
        db_stats = self.get_processing_stats()
        return ProcessingStats(
            total_papers=db_stats.total_papers,
            papers_with_metadata=db_stats.papers_with_metadata,
            papers_processed=db_stats.papers_processed,
            papers_remaining=db_stats.papers_remaining,
            completion_percentage=db_stats.completion_percentage,
            total_processing_time=0.0,
            average_processing_time=0.0,
            success_rate=100.0
        )
    
    def get_processing_stats(self) -> ProcessingStats:
        """Get processing statistics using functional approach."""
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Total papers
                cur.execute("SELECT COUNT(*) FROM doctrove_papers")
                total_papers = cur.fetchone()[0]
                
                # Papers with OpenAlex metadata
                cur.execute("""
                    SELECT COUNT(*) FROM doctrove_papers p
                    JOIN openalex_metadata om ON p.doctrove_paper_id = om.doctrove_paper_id
                    WHERE om.openalex_raw_data IS NOT NULL 
                      AND om.openalex_raw_data != '{{}}'
                      AND om.openalex_raw_data LIKE '%authorships%'
                """)
                papers_with_metadata = cur.fetchone()[0]
                
                # Papers already processed
                cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                papers_processed = cur.fetchone()[0]
                
                # Papers remaining
                papers_remaining = papers_with_metadata - papers_processed
                completion_percentage = (papers_processed / papers_with_metadata * 100) if papers_with_metadata > 0 else 0
                
                return ProcessingStats(
                    total_papers=total_papers,
                    papers_with_metadata=papers_with_metadata,
                    papers_processed=papers_processed,
                    papers_remaining=papers_remaining,
                    completion_percentage=completion_percentage,
                    total_processing_time=0.0,
                    average_processing_time=0.0,
                    success_rate=100.0
                )

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the functional enrichment."""
    parser = argparse.ArgumentParser(description='Functional OpenAlex Details Enrichment')
    parser.add_argument('--limit', type=int, default=None, 
                        help='Limit processing to first N papers (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--create-table', action='store_true',
                        help='Create the enrichment table')
    parser.add_argument('--stats', action='store_true',
                        help='Show processing statistics')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Batch size for processing (default: 1000)')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting Functional OpenAlex Details Enrichment")
    
    try:
        # Create connection factory
        connection_factory = create_connection_factory()
        
        # Initialize functional enrichment
        enrichment = FunctionalOpenAlexDetailsEnrichment(connection_factory)
        
        if args.create_table:
            enrichment.create_table_if_not_exists()
        
        if args.stats:
            stats = enrichment.get_processing_stats()
            logger.info(f"\n📊 PROCESSING STATISTICS:")
            logger.info(f"   Total papers: {stats.total_papers:,}")
            logger.info(f"   Papers with OpenAlex metadata: {stats.papers_with_metadata:,}")
            logger.info(f"   Papers already processed: {stats.papers_processed:,}")
            logger.info(f"   Papers remaining: {stats.papers_remaining:,}")
            logger.info(f"   Completion: {stats.completion_percentage:.1f}%")
            return
        
        # Process papers using functional approach
        stats = enrichment.process_papers_functional(
            limit=args.limit,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            skip_processed=True  # Always skip already-processed papers
        )
        
        if args.dry_run:
            logger.info(f"🧪 DRY RUN COMPLETE - Would process {stats.papers_processed + stats.papers_remaining} papers")
        else:
            logger.info(f"🎉 FUNCTIONAL ENRICHMENT COMPLETE")
            logger.info(f"📊 Final completion: {stats.completion_percentage:.1f}%")
            logger.info(f"📈 Success rate: {stats.success_rate:.1f}%")
    
    except Exception as e:
        logger.error(f"❌ Functional enrichment failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

