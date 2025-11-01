"""
Base enrichment framework for DocTrove system.
Provides standardized patterns for adding new enrichment types.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable, Optional, Tuple
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
from db import create_connection_factory

logger = logging.getLogger(__name__)

class BaseEnrichment(ABC):
    """
    Base class for all enrichment modules.
    
    This provides a standardized interface for creating new enrichment types
    that can be easily integrated into the DocTrove system.
    """
    
    def __init__(self, enrichment_name: str, enrichment_type: str = "derived"):
        """
        Initialize enrichment module.
        
        Args:
            enrichment_name: Name of the enrichment (e.g., "credibility", "topic")
            enrichment_type: Type of enrichment ("fundamental", "derived", "source")
        """
        self.enrichment_name = enrichment_name
        self.enrichment_type = enrichment_type
        self.connection_factory = create_connection_factory()
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Get list of fields required from main table or source metadata.
        
        Returns:
            List of field names required for this enrichment
        """
        pass
    
    @abstractmethod
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process papers and return enrichment results.
        
        Args:
            papers: List of paper dictionaries with required fields
            
        Returns:
            List of enrichment result dictionaries
        """
        pass
    
    def get_source_metadata(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get source-specific metadata for a paper.
        
        Args:
            paper: Paper dictionary with doctrove_source and doctrove_source_id
            
        Returns:
            Source metadata dictionary
        """
        source = paper.get('doctrove_source', '').lower()
        source_id = paper.get('doctrove_source_id')
        
        if not source or not source_id:
            return {}
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Try to get metadata from source-specific table
                try:
                    cur.execute(f"""
                        SELECT * FROM {source}_metadata 
                        WHERE doctrove_paper_id = %s
                    """, (paper['doctrove_paper_id'],))
                    
                    row = cur.fetchone()
                    if row:
                        # Convert row to dict using column names
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, row))
                except Exception as e:
                    logger.warning(f"Could not get metadata from {source}_metadata: {e}")
        
        return {}
    
    def create_table_if_needed(self) -> None:
        """Create enrichment table if it doesn't exist."""
        if self.enrichment_type == "fundamental":
            # Fundamental enrichments go in main table - no separate table needed
            return
        
        # Get field definitions from subclass
        fields = self.get_field_definitions()
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Build table creation SQL
                field_definitions = [
                    'doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id)'
                ]
                
                for field_name, field_type in fields.items():
                    field_definitions.append(f'{self.enrichment_name}_{field_name} {field_type}')
                
                field_definitions.extend([
                    f'{self.enrichment_name}_processed_at TIMESTAMP DEFAULT NOW()',
                    f'{self.enrichment_name}_version TEXT DEFAULT \'v1\'',
                    'PRIMARY KEY (doctrove_paper_id)'
                ])
                
                create_sql = f'''
                    CREATE TABLE IF NOT EXISTS {self.enrichment_name}_enrichment (
                        {', '.join(field_definitions)}
                    );
                '''
                
                cur.execute(create_sql)
                conn.commit()
                logger.debug(f"Created enrichment table: {self.enrichment_name}_enrichment")
    
    def get_field_definitions(self) -> Dict[str, str]:
        """
        Get field definitions for the enrichment table.
        
        Override this method to define custom fields.
        
        Returns:
            Dictionary mapping field names to SQL types
        """
        return {
            "score": "DECIMAL(5,3)",
            "confidence": "DECIMAL(3,2)",
            "factors": "JSONB",
            "metadata": "JSONB"
        }
    
    def register_enrichment(self, description: str) -> None:
        """
        Register this enrichment in the enrichment registry.
        
        Args:
            description: Human-readable description of the enrichment
        """
        fields = self.get_field_definitions()
        
        table_name = f"{self.enrichment_name}_enrichment" if self.enrichment_type == "derived" else "doctrove_papers"
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                # Check if enrichment_registry table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'enrichment_registry'
                    );
                """)
                
                if not cur.fetchone()[0]:
                    logger.warning("enrichment_registry table does not exist. Skipping registration.")
                    return
                
                # Check if enrichment_type column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'enrichment_registry' 
                    AND column_name = 'enrichment_type';
                """)
                
                has_enrichment_type = cur.fetchone() is not None
                
                if has_enrichment_type:
                    cur.execute("""
                        INSERT INTO enrichment_registry 
                        (enrichment_name, table_name, description, fields, enrichment_type)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (enrichment_name) DO UPDATE SET
                            table_name = EXCLUDED.table_name,
                            description = EXCLUDED.description,
                            fields = EXCLUDED.fields,
                            enrichment_type = EXCLUDED.enrichment_type,
                            updated_at = NOW()
                    """, (self.enrichment_name, table_name, description, json.dumps(fields), self.enrichment_type))
                else:
                    cur.execute("""
                        INSERT INTO enrichment_registry 
                        (enrichment_name, table_name, description, fields)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (enrichment_name) DO UPDATE SET
                            table_name = EXCLUDED.table_name,
                            description = EXCLUDED.description,
                            fields = EXCLUDED.fields,
                            updated_at = NOW()
                    """, (self.enrichment_name, table_name, description, json.dumps(fields)))
                
                conn.commit()
                logger.debug(f"Registered enrichment: {self.enrichment_name}")
    
    def insert_results(self, results: List[Dict[str, Any]]) -> int:
        """
        Insert enrichment results into the database.
        
        Args:
            results: List of enrichment result dictionaries
            
        Returns:
            Number of results inserted
        """
        if not results:
            return 0
        
        if self.enrichment_type == "fundamental":
            return self._insert_fundamental_results(results)
        else:
            return self._insert_derived_results(results)
    
    def _insert_fundamental_results(self, results: List[Dict[str, Any]]) -> int:
        """Insert results into main table for fundamental enrichments."""
        # This would be implemented for fundamental enrichments
        # For now, we'll focus on derived enrichments
        raise NotImplementedError("Fundamental enrichments not yet implemented")
    
    def _insert_derived_results(self, results: List[Dict[str, Any]]) -> int:
        """Insert results into dedicated enrichment table."""
        if not results:
            return 0
        
        # Get field definitions
        fields = self.get_field_definitions()
        field_names = list(fields.keys())
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                inserted_count = 0
                
                for result in results:
                    # Build field list and values
                    sql_fields = ['doctrove_paper_id']
                    values = [result['paper_id']]
                    
                    for field_name in field_names:
                        sql_fields.append(f'{self.enrichment_name}_{field_name}')
                        values.append(result.get(f'{self.enrichment_name}_{field_name}'))
                    
                    # Build INSERT SQL
                    placeholders = ', '.join(['%s'] * len(values))
                    field_list = ', '.join(sql_fields)
                    
                    insert_sql = f"""
                        INSERT INTO {self.enrichment_name}_enrichment ({field_list})
                        VALUES ({placeholders})
                        ON CONFLICT (doctrove_paper_id) DO UPDATE SET
                    """
                    
                    # Build UPDATE clause
                    update_clauses = []
                    for field_name in field_names:
                        update_clauses.append(f'{self.enrichment_name}_{field_name} = EXCLUDED.{self.enrichment_name}_{field_name}')
                    
                    update_clauses.append(f'{self.enrichment_name}_processed_at = NOW()')
                    insert_sql += ', '.join(update_clauses)
                    
                    cur.execute(insert_sql, values)
                    inserted_count += 1
                
                conn.commit()
                logger.debug(f"Inserted {inserted_count} {self.enrichment_name} enrichment results")
                return inserted_count
    
    def run_enrichment(self, papers: List[Dict[str, Any]], description: str = None) -> int:
        """
        Run the complete enrichment pipeline.
        
        Args:
            papers: List of papers to enrich
            description: Description for registry (if not already registered)
            
        Returns:
            Number of papers successfully enriched
        """
        logger.debug(f"Starting {self.enrichment_name} enrichment for {len(papers)} papers")
        
        # Register enrichment if description provided
        if description:
            self.register_enrichment(description)
        
        # Create table if needed
        self.create_table_if_needed()
        
        # Process papers
        results = self.process_papers(papers)
        
        # Insert results
        inserted_count = self.insert_results(results)
        
        logger.debug(f"Completed {self.enrichment_name} enrichment: {inserted_count} papers enriched")
        return inserted_count
    
    def run_enrichment_with_interceptors(self, papers: List[Dict[str, Any]], 
                                       interceptors: List = None, 
                                       description: str = None) -> int:
        """
        Run enrichment pipeline with interceptor support.
        
        Args:
            papers: List of papers to enrich
            interceptors: List of interceptors to apply
            description: Description for registry (if not already registered)
            
        Returns:
            Number of papers successfully enriched
        """
        from interceptor import InterceptorStack, Interceptor, log_enter, log_leave, log_error
        
        # Default interceptors if none provided
        if interceptors is None:
            interceptors = [
                Interceptor(enter=log_enter, leave=log_leave, error=log_error),
                Interceptor(enter=self._setup_enrichment_interceptor),
                Interceptor(enter=self._validate_papers_interceptor),
                Interceptor(enter=self._process_papers_interceptor),
                Interceptor(enter=self._insert_results_interceptor),
                Interceptor(enter=self._log_completion_interceptor)
            ]
        
        # Create interceptor stack
        stack = InterceptorStack(interceptors)
        
        # Execute with context
        context = {
            'phase': f'{self.enrichment_name}_enrichment',
            'papers': papers,
            'enrichment_name': self.enrichment_name,
            'enrichment_type': self.enrichment_type,
            'description': description,
            'connection_factory': self.connection_factory
        }
        
        result = stack.execute(context)
        
        if 'error' in result:
            logger.error(f"Enrichment failed: {result['error']}")
            return 0
        
        return result.get('inserted_count', 0)
    
    def _setup_enrichment_interceptor(self, ctx):
        """Setup enrichment environment"""
        description = ctx.get('description')
        if description:
            self.register_enrichment(description)
        
        self.create_table_if_needed()
        logger.debug(f"Setup complete for {self.enrichment_name} enrichment")
        return ctx
    
    def _validate_papers_interceptor(self, ctx):
        """Validate papers before processing"""
        papers = ctx.get('papers', [])
        required_fields = self.get_required_fields()
        
        # Functional approach: filter valid papers
        def has_required_fields(paper: Dict[str, Any]) -> bool:
            """Check if paper has all required fields"""
            return all(field in paper for field in required_fields)
        
        valid_papers = list(filter(has_required_fields, papers))
        invalid_count = len(papers) - len(valid_papers)
        
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} papers missing required fields: {required_fields}")
        
        ctx['valid_papers'] = valid_papers
        ctx['invalid_count'] = invalid_count
        logger.debug(f"Validation complete: {len(valid_papers)} valid papers, {invalid_count} invalid")
        
        return ctx
    
    def _process_papers_interceptor(self, ctx):
        """Process papers using pure function"""
        valid_papers = ctx.get('valid_papers', [])
        results = self.process_papers(valid_papers)
        
        ctx['results'] = results
        logger.debug(f"Processing complete: {len(results)} results generated")
        
        return ctx
    
    def _insert_results_interceptor(self, ctx):
        """Insert results into database"""
        results = ctx.get('results', [])
        inserted_count = self.insert_results(results)
        
        ctx['inserted_count'] = inserted_count
        logger.debug(f"Insertion complete: {inserted_count} results inserted")
        
        return ctx
    
    def _log_completion_interceptor(self, ctx):
        """Log completion summary"""
        papers = ctx.get('papers', [])
        inserted_count = ctx.get('inserted_count', 0)
        invalid_count = ctx.get('invalid_count', 0)
        
        logger.debug(f"Enrichment completed: {inserted_count}/{len(papers)} papers enriched")
        if invalid_count > 0:
            logger.debug(f"Skipped {invalid_count} papers due to missing required fields")
        
        return ctx


class CredibilityEnrichment(BaseEnrichment):
    """
    Example credibility score enrichment.
    
    This demonstrates how to implement a derived enrichment that combines
    data from multiple sources to calculate a credibility score.
    """
    
    def __init__(self):
        super().__init__("credibility", "derived")
    
    def get_required_fields(self) -> List[str]:
        return ["doctrove_paper_id", "doctrove_source", "doctrove_source_id"]
    
    def get_field_definitions(self) -> Dict[str, str]:
        return {
            "score": "DECIMAL(5,3)",      # 0.000 to 1.000
            "confidence": "DECIMAL(3,2)",  # 0.00 to 1.00
            "factors": "JSONB",           # Contributing factors
            "metadata": "JSONB"           # Raw metadata
        }
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process papers and calculate credibility scores."""
        def process_single_paper(paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Process a single paper and return result if successful, None if failed"""
            try:
                # Get source metadata
                source_metadata = self.get_source_metadata(paper)
                
                # Calculate credibility score
                score, confidence, factors, metadata = self.calculate_credibility(paper, source_metadata)
                
                return {
                    'paper_id': paper['doctrove_paper_id'],
                    'credibility_score': score,
                    'credibility_confidence': confidence,
                    'credibility_factors': factors,
                    'credibility_metadata': metadata
                }
                
            except Exception as e:
                # Log error but don't include paper ID to reduce log verbosity
                logger.error(f"Error processing paper: {e}")
                return None
        
        # Map papers to results and filter out None values
        results = list(filter(None, map(process_single_paper, papers)))
        
        return results
    
    def calculate_credibility(self, paper: Dict[str, Any], source_metadata: Dict[str, Any]) -> Tuple[float, float, Dict[str, Any], Dict[str, Any]]:
        """
        Calculate credibility score from paper and metadata.
        
        Args:
            paper: Paper dictionary
            source_metadata: Source-specific metadata
            
        Returns:
            Tuple of (score, confidence, factors, metadata)
        """
        factors = {}
        total_score = 0.0
        max_possible_score = 0.0
        
        # Journal impact factor (if available)
        if 'journal_impact_factor' in source_metadata:
            try:
                impact_factor = float(source_metadata['journal_impact_factor'])
                journal_score = min(impact_factor / 50.0, 1.0)  # Normalize to 0-1
                factors['journal_impact'] = journal_score
                total_score += journal_score * 0.3
                max_possible_score += 0.3
            except (ValueError, TypeError):
                pass
        
        # Citation count
        if 'citation_count' in source_metadata:
            try:
                citations = int(source_metadata['citation_count'])
                citation_score = min(citations / 1000.0, 1.0)  # Normalize to 0-1
                factors['citations'] = citation_score
                total_score += citation_score * 0.4
                max_possible_score += 0.4
            except (ValueError, TypeError):
                pass
        
        # Author count (more authors = higher credibility)
        if 'author_count' in source_metadata:
            try:
                authors = int(source_metadata['author_count'])
                author_score = min(authors / 10.0, 1.0)
                factors['authors'] = author_score
                total_score += author_score * 0.1
                max_possible_score += 0.1
            except (ValueError, TypeError):
                pass
        
        # Source reputation
        source_scores = {
            'nature': 0.9, 'science': 0.9, 'arxiv': 0.7, 'rand': 0.8,
            'aipickle': 0.6, 'pubmed': 0.8, 'ieee': 0.7
        }
        source = paper['doctrove_source'].lower()
        source_score = source_scores.get(source, 0.5)
        factors['source'] = source_score
        total_score += source_score * 0.2
        max_possible_score += 0.2
        
        # Normalize score if we have partial data
        if max_possible_score > 0:
            final_score = total_score / max_possible_score
        else:
            final_score = 0.0
        
        # Calculate confidence based on available data
        confidence = len(factors) / 4.0  # Higher if more factors available
        
        metadata = {
            'journal_name': source_metadata.get('journal_name'),
            'citation_count': source_metadata.get('citation_count'),
            'author_count': source_metadata.get('author_count'),
            'source': paper['doctrove_source'],
            'source_id': paper['doctrove_source_id']
        }
        
        return final_score, confidence, factors, metadata


# Utility functions for working with enrichments

def get_available_enrichments(connection_factory: Callable) -> List[Dict[str, Any]]:
    """
    Get list of available enrichments from registry.
    
    Args:
        connection_factory: Database connection factory
        
    Returns:
        List of enrichment dictionaries
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT enrichment_name, table_name, description, fields, 
                           enrichment_type, created_at, updated_at
                    FROM enrichment_registry
                    ORDER BY enrichment_name
                """)
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
                
            except Exception as e:
                logger.warning(f"Could not get enrichment registry: {e}")
                return []


def build_enrichment_query(base_query: str, enrichments: List[str], 
                          connection_factory: Callable) -> str:
    """
    Build query with enrichment joins.
    
    Args:
        base_query: Base SQL query
        enrichments: List of enrichment names to join
        connection_factory: Database connection factory
        
    Returns:
        SQL query with enrichment joins
    """
    available_enrichments = get_available_enrichments(connection_factory)
    enrichment_tables = {e['enrichment_name']: e['table_name'] for e in available_enrichments}
    
    joins = []
    for enrichment in enrichments:
        if enrichment in enrichment_tables:
            table_name = enrichment_tables[enrichment]
            if table_name != 'doctrove_papers':  # Don't join main table to itself
                joins.append(f"""
                    LEFT JOIN {table_name} 
                    ON doctrove_papers.doctrove_paper_id = {table_name}.doctrove_paper_id
                """)
    
    return f"""
        {base_query}
        {' '.join(joins)}
    """


class Embedding2DEnrichment(BaseEnrichment):
    """
    Specialized enrichment for generating 2D embeddings.
    This is a fundamental enrichment that updates the main table.
    """
    
    def __init__(self):
        super().__init__("embedding_2d", "fundamental")
    
    def get_required_fields(self) -> List[str]:
        return ["doctrove_paper_id", "doctrove_embedding"]
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process papers to generate 2D embeddings."""
        if not papers:
            return []
        
        try:
            # Import UMAP processing functions
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'doctrove-api'))
            from enrichment import process_papers_for_2d_embeddings
            
            # Process papers for 2D embeddings using unified embeddings
            results = process_papers_for_2d_embeddings(papers, embedding_type='unified')
            
            # Convert to enrichment framework format
            enrichment_results = []
            for result in results:
                enrichment_results.append({
                    'paper_id': result['paper_id'],
                    'doctrove_embedding_2d': result['coords_2d']
                })
            
            return enrichment_results
            
        except Exception as e:
            logger.error(f"Error processing 2D embeddings: {e}")
            return []
    
    def insert_results(self, results: List[Dict[str, Any]]) -> int:
        """Insert 2D embedding results into main table."""
        if not results:
            return 0
        
        with self.connection_factory() as conn:
            with conn.cursor() as cur:
                updated_count = 0
                
                for result in results:
                    paper_id = result['paper_id']
                    coords_2d = result.get('doctrove_embedding_2d')
                    
                    if coords_2d:
                        # Update main table with 2D coordinates
                        cur.execute("""
                            UPDATE doctrove_papers 
                            SET doctrove_embedding_2d = point(%s, %s),
                                embedding_2d_updated_at = NOW()
                            WHERE doctrove_paper_id = %s
                        """, (
                            coords_2d[0], 
                            coords_2d[1],
                            paper_id
                        ))
                        updated_count += 1
                
                conn.commit()
                logger.debug(f"Updated {updated_count} papers with 2D embeddings")
                return updated_count


# Example usage
if __name__ == "__main__":
    # Example: Run credibility enrichment
    credibility = CredibilityEnrichment()
    
    # Get papers that need credibility scores
    connection_factory = create_connection_factory()
    
    # This would be implemented to get papers from database
    # papers = get_papers_for_credibility_enrichment(connection_factory)
    
    # Run enrichment
    # result_count = credibility.run_enrichment(papers, "Credibility score based on journal impact, citations, and source reputation")
    
    print("Enrichment framework ready for use!") 