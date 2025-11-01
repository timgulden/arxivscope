#!/usr/bin/env python3
"""
OpenAlex Details Enrichment Script
Extracts comprehensive metadata from OpenAlex raw data for research quality analysis.
This script follows the existing enrichment pattern and database schema.
"""

import sys
import os
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

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

class OpenAlexDetailsEnrichment:
    """Main enrichment class for OpenAlex details extraction."""
    
    def __init__(self, connection_factory):
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
                        
                        -- Best available author data (highest ranked with data)
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
                        related_works_count INTEGER,
                        referenced_works_count INTEGER,
                        citation_counts_by_year JSONB,
                        
                        -- Financial & publishing
                        apc_amount DECIMAL,
                        apc_currency VARCHAR,
                        apc_amount_usd DECIMAL,
                        apc_paid DECIMAL,
                        license_type VARCHAR,
                        license_id VARCHAR,
                        
                        -- Source quality indicators
                        source_is_core BOOLEAN,
                        source_is_in_doaj BOOLEAN,
                        source_is_indexed_in_scopus BOOLEAN,
                        indexed_in VARCHAR[],
                        
                        -- Bibliographic details
                        volume VARCHAR,
                        issue VARCHAR,
                        first_page VARCHAR,
                        last_page VARCHAR,
                        doi_registration_agency VARCHAR,
                        
                        -- Medical & health (MeSH)
                        mesh_terms VARCHAR[],
                        mesh_major_topics VARCHAR[],
                        mesh_descriptors VARCHAR[],
                        
                        -- Fulltext & access
                        has_fulltext BOOLEAN,
                        fulltext_origin VARCHAR,
                        any_repository_has_fulltext BOOLEAN,
                        version VARCHAR,
                        is_accepted BOOLEAN,
                        is_published BOOLEAN,
                        
                        -- Keywords & concepts
                        keywords VARCHAR[],
                        keyword_scores DECIMAL[],
                        top_keyword_score DECIMAL,
                        
                        -- Sustainable development goals
                        sdg_goals VARCHAR[],
                        sdg_scores DECIMAL[],
                        sdg_top_score DECIMAL,
                        
                        -- Temporal & update data
                        created_date DATE,
                        updated_date TIMESTAMP,
                        
                        -- Quality & processing fields
                        is_retracted BOOLEAN,
                        extraction_confidence DECIMAL,
                        extraction_source VARCHAR,
                        processed_at TIMESTAMP DEFAULT NOW(),
                        
                        -- Analysis fields
                        country_coding_quality VARCHAR,
                        institution_coding_quality VARCHAR,
                        metadata_completeness_score DECIMAL,
                        
                        -- Derived quality indicators
                        is_highly_cited BOOLEAN,
                        is_field_leading BOOLEAN,
                        research_quality_score DECIMAL,
                        metadata_richness_score DECIMAL,
                        relevance_confidence DECIMAL,
                        
                        -- Data source tracking
                        country_data_source VARCHAR,
                        institution_data_source VARCHAR,
                        country_data_quality VARCHAR,
                        institution_data_quality VARCHAR
                    )
                """)
                
                # Create indexes for performance
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_openalex_id ON {self.table_name} (openalex_id)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_publication_year ON {self.table_name} (publication_year)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_source_name ON {self.table_name} (source_name)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_best_author_country ON {self.table_name} (best_author_country)")
                
                conn.commit()
                logger.info(f"✅ Table {self.table_name} created/verified with indexes")
    
    def extract_best_author_data(self, authorships: List[Dict]) -> Tuple[Dict, Dict]:
        """Extract country and institution data from the best available author."""
        if not authorships:
            return {}, {}
        
        country_data = {}
        institution_data = {}
        
        # Scan authors in order to find the best available data
        for i, authorship in enumerate(authorships):
            position = i + 1
            author = authorship.get('author', {})
            
            # Check for country data
            if not country_data and authorship.get('countries'):
                country_data = {
                    'country': authorship['countries'][0] if authorship['countries'] else None,
                    'position': position,
                    'author_name': author.get('display_name'),
                    'author_orcid': author.get('orcid'),
                    'quality': 'high' if position == 1 else 'medium' if position <= 3 else 'low'
                }
            
            # Check for institution data
            if not institution_data and authorship.get('institutions'):
                institution_data = {
                    'institution': authorship['institutions'][0].get('display_name') if authorship['institutions'] else None,
                    'position': position,
                    'author_name': author.get('display_name'),
                    'author_orcid': author.get('orcid'),
                    'quality': 'high' if position == 1 else 'medium' if position <= 3 else 'low'
                }
            
            # If we have both, we can stop
            if country_data and institution_data:
                break
        
        return country_data, institution_data
    
    def extract_paper_details(self, raw_data: Dict) -> Dict[str, Any]:
        """Extract all paper details from OpenAlex raw data."""
        try:
            # Basic document info
            details = {}
            
            # Safely extract openalex_id
            openalex_id = raw_data.get('id')
            if openalex_id:
                details['openalex_id'] = openalex_id.replace('https://openalex.org/W', '')
            else:
                details['openalex_id'] = None
            
            details.update({
                'document_type': raw_data.get('type'),
                'document_type_crossref': raw_data.get('type_crossref'),
                'publication_year': raw_data.get('publication_year'),
                'publication_date': raw_data.get('publication_date'),
                'language': raw_data.get('language'),

                # Source info
                'source_name': raw_data.get('primary_location', {}).get('source', {}).get('display_name') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'source_id': raw_data.get('primary_location', {}).get('source', {}).get('id', '').replace('https://openalex.org/S', '') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') and raw_data.get('primary_location', {}).get('source', {}).get('id') else None,
                'source_type': raw_data.get('primary_location', {}).get('source', {}).get('type') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'source_publisher': raw_data.get('primary_location', {}).get('source', {}).get('publisher') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'source_host_organization': raw_data.get('primary_location', {}).get('source', {}).get('host_organization_name') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'source_issn': raw_data.get('primary_location', {}).get('source', {}).get('issn', []) if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else [],
                'landing_page_url': raw_data.get('primary_location', {}).get('landing_page_url') if raw_data.get('primary_location') else None,
                'pdf_url': raw_data.get('primary_location', {}).get('pdf_url') if raw_data.get('primary_location') else None,
                'is_open_access': raw_data.get('open_access', {}).get('is_oa') if raw_data.get('open_access') else None,
                'oa_status': raw_data.get('open_access', {}).get('oa_status') if raw_data.get('open_access') else None,

                # Author counts
                'authors_count': raw_data.get('authors_count'),
                'corresponding_author_count': len(raw_data.get('corresponding_author_ids', [])),
                'corresponding_institution_count': len(raw_data.get('corresponding_institution_ids', [])),
                'institution_count': raw_data.get('institutions_distinct_count'),
                'institution_countries_distinct': raw_data.get('countries_distinct_count'),

                # Academic classification
                'primary_domain': raw_data.get('primary_topic', {}).get('domain', {}).get('display_name') if raw_data.get('primary_topic') and raw_data.get('primary_topic', {}).get('domain') else None,
                'primary_field': raw_data.get('primary_topic', {}).get('field', {}).get('display_name') if raw_data.get('primary_topic') and raw_data.get('primary_topic', {}).get('field') else None,
                'primary_subfield': raw_data.get('primary_topic', {}).get('subfield', {}).get('display_name') if raw_data.get('primary_topic') and raw_data.get('primary_topic', {}).get('subfield') else None,
                'primary_topic_name': raw_data.get('primary_topic', {}).get('display_name') if raw_data.get('primary_topic') else None,
                'primary_topic_score': raw_data.get('primary_topic', {}).get('score') if raw_data.get('primary_topic') else None,
                'concepts_count': raw_data.get('concepts_count'),
                'topics_count': raw_data.get('topics_count'),

                # Citation data
                'cited_by_count': raw_data.get('cited_by_count'),
                'cited_by_count_2yr': raw_data.get('summary_stats', {}).get('2yr_cited_by_count') if raw_data.get('summary_stats') else None,
                'fwci': raw_data.get('fwci'),
                'related_works_count': raw_data.get('related_works_count'),
                'referenced_works_count': raw_data.get('referenced_works_count'),

                # Financial data
                'apc_amount': raw_data.get('apc_list', {}).get('value') if raw_data.get('apc_list') else None,
                'apc_currency': raw_data.get('apc_list', {}).get('currency') if raw_data.get('apc_list') else None,
                'apc_amount_usd': raw_data.get('apc_list', {}).get('value_usd') if raw_data.get('apc_list') else None,
                'apc_paid': raw_data.get('apc_paid', {}).get('value') if raw_data.get('apc_paid') else None,
                'license_type': raw_data.get('primary_location', {}).get('license') if raw_data.get('primary_location') else None,
                'license_id': raw_data.get('primary_location', {}).get('license_id') if raw_data.get('primary_location') else None,

                # Source quality
                'source_is_core': raw_data.get('primary_location', {}).get('source', {}).get('is_core') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'source_is_in_doaj': raw_data.get('primary_location', {}).get('source', {}).get('is_in_doaj') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'source_is_indexed_in_scopus': raw_data.get('primary_location', {}).get('source', {}).get('is_indexed_in_scopus') if raw_data.get('primary_location') and raw_data.get('primary_location', {}).get('source') else None,
                'indexed_in': raw_data.get('indexed_in', []) or [],

                # Bibliographic
                'volume': raw_data.get('biblio', {}).get('volume') if raw_data.get('biblio') else None,
                'issue': raw_data.get('biblio', {}).get('issue') if raw_data.get('biblio') else None,
                'first_page': raw_data.get('biblio', {}).get('first_page') if raw_data.get('biblio') else None,
                'last_page': raw_data.get('biblio', {}).get('last_page') if raw_data.get('biblio') else None,
                'doi_registration_agency': raw_data.get('doi_registration_agency'),

                # Fulltext
                'has_fulltext': raw_data.get('has_fulltext'),
                'fulltext_origin': raw_data.get('fulltext_origin'),
                'any_repository_has_fulltext': raw_data.get('open_access', {}).get('any_repository_has_fulltext') if raw_data.get('open_access') else None,
                'version': raw_data.get('primary_location', {}).get('version') if raw_data.get('primary_location') else None,
                'is_accepted': raw_data.get('primary_location', {}).get('is_accepted') if raw_data.get('primary_location') else None,
                'is_published': raw_data.get('primary_location', {}).get('is_published') if raw_data.get('primary_location') else None,

                # Keywords
                'keywords': [kw.get('display_name') for kw in raw_data.get('keywords', []) if kw and kw.get('display_name')] or [],
                'keyword_scores': [kw.get('score') for kw in raw_data.get('keywords', []) if kw and kw.get('score') is not None] or [],

                # SDGs
                'sdg_goals': [sdg.get('display_name') for sdg in raw_data.get('sustainable_development_goals', []) if sdg and sdg.get('display_name')] or [],
                'sdg_scores': [sdg.get('score') for sdg in raw_data.get('sustainable_development_goals', []) if sdg and sdg.get('score') is not None] or [],

                # Temporal
                'created_date': raw_data.get('created_date'),
                'updated_date': raw_data.get('updated_date'),

                # Quality indicators
                'is_retracted': raw_data.get('is_retracted'),
                'extraction_confidence': 1.0,  # High confidence for direct extraction
                'extraction_source': 'openalex_direct'
            })

            # Extract best author data
            authorships = raw_data.get('authorships', [])
            if authorships:
                country_data, institution_data = self.extract_best_author_data(authorships)
                
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
                
                # Set best author position to the highest one we found
                if country_data or institution_data:
                    max_position = max(
                        country_data.get('position', 0) if country_data else 0,
                        institution_data.get('position', 0) if institution_data else 0
                    )
                    details['best_author_position'] = max_position

            # Extract concept and topic data
            concepts = raw_data.get('concepts', [])
            if concepts:
                details['concept_levels'] = [c.get('level') for c in concepts if c and c.get('level') is not None] or []
                details['concept_scores'] = [c.get('score') for c in concepts if c and c.get('score') is not None] or []
                if concepts and concepts[0]:
                    details['primary_concept_score'] = concepts[0].get('score')

            topics = raw_data.get('topics', [])
            if topics:
                details['topic_scores'] = [t.get('score') for t in topics if t and t.get('score') is not None] or []

            # Citation percentile data
            citation_percentile = raw_data.get('citation_normalized_percentile', {})
            if citation_percentile:
                details['citation_percentile_raw'] = citation_percentile.get('value')
                details['is_top_1_percent'] = citation_percentile.get('is_in_top_1_percent')
                details['is_top_10_percent'] = citation_percentile.get('is_in_top_10_percent')

            # Citation counts by year
            counts_by_year = raw_data.get('counts_by_year', [])
            if counts_by_year:
                # Convert to JSONB-compatible format
                details['citation_counts_by_year'] = json.dumps(counts_by_year)

            # MeSH terms
            mesh = raw_data.get('mesh', [])
            if mesh:
                details['mesh_terms'] = [m.get('descriptor_name') for m in mesh if m and m.get('descriptor_name')] or []
                details['mesh_major_topics'] = [m.get('descriptor_name') for m in mesh if m and m.get('is_major_topic') and m.get('descriptor_name')] or []
                details['mesh_descriptors'] = [m.get('descriptor_name') for m in mesh if m and m.get('descriptor_name')] or []

            # Derived quality indicators
            if details.get('fwci'):
                details['is_highly_cited'] = details['fwci'] > 2.0
                details['is_field_leading'] = details['fwci'] > 5.0

            # Metadata richness score (simple heuristic)
            richness_factors = [
                bool(details.get('best_author_country')),
                bool(details.get('best_author_institution')),
                bool(details.get('concepts_count', 0) > 5),
                bool(details.get('topics_count', 0) > 2),
                bool(details.get('keywords')),
                bool(details.get('mesh_terms')),
                bool(details.get('has_fulltext'))
            ]
            details['metadata_richness_score'] = sum(richness_factors) / len(richness_factors)

            return details

        except Exception as e:
            logger.error(f"Error extracting paper details: {e}")
            return {}
    
    def get_papers_to_process(self, limit: Optional[int] = None) -> List[Tuple[str, str]]:
        """Get papers that need processing."""
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                query = f"""
                    SELECT p.doctrove_paper_id::text, om.openalex_raw_data
                    FROM doctrove_papers p
                    JOIN openalex_metadata om ON p.doctrove_paper_id = om.doctrove_paper_id
                    WHERE om.openalex_raw_data IS NOT NULL 
                      AND om.openalex_raw_data != '{{}}'
                      AND om.openalex_raw_data LIKE '%authorships%'
                      AND NOT EXISTS (
                          SELECT 1 FROM {self.table_name} e 
                          WHERE e.doctrove_paper_id = p.doctrove_paper_id
                      )
                """
                
                query += " ORDER BY p.doctrove_paper_id"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cur.execute(query)
                return cur.fetchall()
    
    def process_papers(self, limit: Optional[int] = None, dry_run: bool = False) -> int:
        """Process papers and extract details."""
        papers = self.get_papers_to_process(limit)
        
        if not papers:
            logger.info("✅ No papers to process")
            return 0
        
        logger.info(f"🔍 Processing {len(papers)} papers...")
        
        processed = 0
        errors = 0
        
        for i, (paper_id, raw_data_str) in enumerate(papers):
            if i % 100 == 0:
                logger.info(f"   Processed {i}/{len(papers)} papers...")
            
            try:
                raw_data = json.loads(raw_data_str)
                logger.info(f"Processing paper {paper_id}, raw_data keys: {list(raw_data.keys()) if raw_data else 'None'}")
                details = self.extract_paper_details(raw_data)
                
                if not details:
                    errors += 1
                    continue
                
                # Add paper ID
                details['doctrove_paper_id'] = paper_id
                
                if not dry_run:
                    self.insert_paper_details(details)
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing paper {paper_id}: {e}")
                # Log more details about the error
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                errors += 1
                continue
        
        logger.info(f"✅ Processing complete: {processed} processed, {errors} errors")
        return processed
    
    def insert_paper_details(self, details: Dict[str, Any]):
        """Insert paper details into the enrichment table."""
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Build the INSERT statement dynamically
                columns = list(details.keys())
                placeholders = ['%s'] * len(columns)
                values = [details[col] for col in columns]
                
                query = f"""
                    INSERT INTO {self.table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                        processed_at = NOW()
                """
                
                cur.execute(query, values)
                conn.commit()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about processing status."""
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
                      AND om.openalex_raw_data != '{}'
                      AND om.openalex_raw_data LIKE '%authorships%'
                """)
                papers_with_metadata = cur.fetchone()[0]
                
                # Papers already processed
                cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                papers_processed = cur.fetchone()[0]
                
                # Papers remaining
                papers_remaining = papers_with_metadata - papers_processed
                
                return {
                    'total_papers': total_papers,
                    'papers_with_metadata': papers_with_metadata,
                    'papers_processed': papers_processed,
                    'papers_remaining': papers_remaining,
                    'completion_percentage': (papers_processed / papers_with_metadata * 100) if papers_with_metadata > 0 else 0
                }

def main():
    """Main function to run the enrichment."""
    parser = argparse.ArgumentParser(description='OpenAlex Details Enrichment')
    parser.add_argument('--limit', type=int, default=None, 
                        help='Limit processing to first N papers (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--create-table', action='store_true',
                        help='Create the enrichment table')
    parser.add_argument('--stats', action='store_true',
                        help='Show processing statistics')
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting OpenAlex Details Enrichment")
    
    try:
        # Create connection factory
        connection_factory = create_connection_factory()
        
        # Initialize enrichment
        enrichment = OpenAlexDetailsEnrichment(connection_factory)
        
        if args.create_table:
            enrichment.create_table_if_not_exists()
        
        if args.stats:
            stats = enrichment.get_processing_stats()
            logger.info(f"\n📊 PROCESSING STATISTICS:")
            logger.info(f"   Total papers: {stats['total_papers']:,}")
            logger.info(f"   Papers with OpenAlex metadata: {stats['papers_with_metadata']:,}")
            logger.info(f"   Papers already processed: {stats['papers_processed']:,}")
            logger.info(f"   Papers remaining: {stats['papers_remaining']:,}")
            logger.info(f"   Completion: {stats['completion_percentage']:.1f}%")
            return
        
        # Process papers
        processed_count = enrichment.process_papers(
            limit=args.limit,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            logger.info(f"🧪 DRY RUN COMPLETE - Would process {processed_count} papers")
        else:
            logger.info(f"🎉 ENRICHMENT COMPLETE - Processed {processed_count} papers")
            
            # Show final stats
            stats = enrichment.get_processing_stats()
            logger.info(f"📊 Final completion: {stats['completion_percentage']:.1f}%")
    
    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
