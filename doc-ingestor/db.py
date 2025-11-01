"""
Database operations for doc-ingestor.
These functions handle database I/O and are impure.
"""

import psycopg2
from typing import Dict, Any, List, Callable
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

def create_connection_factory():
    """
    Pure function: creates a connection factory function.
    
    Returns:
        Function that creates database connections
    """
    def get_connection():
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    return get_connection

def insert_paper(connection_factory, paper: Dict[str, Any]) -> bool:
    """
    Insert a paper into the doctrove_papers table.
    
    Args:
        connection_factory: Function that creates database connections
        paper: Paper dictionary with all required fields
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # Insert into main papers table
                cur.execute("""
                    INSERT INTO doctrove_papers (
                        doctrove_paper_id, doctrove_source, doctrove_source_id,
                        doctrove_title, doctrove_abstract, doctrove_authors,
                        doctrove_primary_date, doctrove_embedding,
                        embedding_model_version, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    paper['doctrove_paper_id'],
                    paper['doctrove_source'],
                    paper['doctrove_source_id'],
                    paper['doctrove_title'],
                    paper['doctrove_abstract'],
                    paper['doctrove_authors'],
                    paper['doctrove_primary_date'],
                    paper.get('doctrove_embedding'),
                    paper.get('embedding_model_version')
                ))
                
                conn.commit()
                logger.debug(f"Inserted paper {paper['doctrove_paper_id']}")
                return True
                
    except Exception as e:
        logger.error(f"Error inserting paper {paper['doctrove_paper_id']}: {e}")
        logger.error(f"Unified embedding: {paper.get('doctrove_embedding')[:50] if paper.get('doctrove_embedding') else 'None'}")
        return False

def insert_paper_and_metadata(cur, paper: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
    """
    Insert a paper and its metadata into the database.
    
    Args:
        cur: Database cursor
        paper: Paper dictionary with all required fields
        metadata: Source-specific metadata dictionary
        
    Returns:
        True if successful, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Insert into main papers table
        cur.execute("""
            INSERT INTO doctrove_papers (
                doctrove_paper_id, doctrove_source, doctrove_source_id,
                doctrove_title, doctrove_abstract, doctrove_authors,
                doctrove_primary_date, doctrove_embedding,
                embedding_model_version, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (doctrove_source, doctrove_source_id) DO NOTHING
        """, (
            paper['doctrove_paper_id'],
            paper['doctrove_source'],
            paper['doctrove_source_id'],
            paper['doctrove_title'],
            paper['doctrove_abstract'],
            paper['doctrove_authors'],
            paper['doctrove_primary_date'],
            paper.get('doctrove_embedding'),
            paper.get('embedding_model_version')
        ))
        
        # Insert metadata if it exists
        if metadata and len(metadata) > 1:  # More than just doctrove_paper_id
            source_name = paper['doctrove_source']
            table_name = f"{source_name}_metadata"
            
            # Build dynamic INSERT statement for metadata
            metadata_fields = list(metadata.keys())
            placeholders = ', '.join(['%s'] * len(metadata_fields))
            field_names = ', '.join([f'"{field}"' for field in metadata_fields])
            
            insert_sql = f"""
                INSERT INTO {table_name} ({field_names})
                VALUES ({placeholders})
                ON CONFLICT (doctrove_paper_id) DO NOTHING
            """
            
            metadata_values = [metadata[field] for field in metadata_fields]
            cur.execute(insert_sql, metadata_values)
        
        return True
        
    except Exception as e:
        logger.error(f"Error inserting paper {paper.get('doctrove_paper_id', 'unknown')}: {e}")
        return False

def insert_papers_batch(cur, papers: List[Dict[str, Any]], source_metadata_list: List[Dict[str, Any]], batch_size: int = 100) -> int:
    """
    Impure function: inserts papers and their metadata in batches.
    
    Args:
        cur: Database cursor
        papers: List of paper dictionaries
        source_metadata_list: List of source-specific metadata dictionaries
        batch_size: Number of papers to insert per batch
        
    Returns:
        Number of papers successfully inserted
    """
    import logging
    logger = logging.getLogger(__name__)
    
    inserted_count = 0
    total_papers = len(papers)
    total_batches = (total_papers + batch_size - 1) // batch_size
    
    logger.debug(f"📊 Processing {total_papers} papers in {total_batches} batches")
    
    for i in range(0, len(papers), batch_size):
        batch_num = (i // batch_size) + 1
        batch_papers = papers[i:i + batch_size]
        batch_metadata = source_metadata_list[i:i + batch_size]
        
        logger.debug(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch_papers)} papers)")
        
        batch_inserted = 0
        for paper, metadata in zip(batch_papers, batch_metadata):
            try:
                insert_paper_and_metadata(cur, paper, metadata)
                batch_inserted += 1
                inserted_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to insert paper {paper.get('doctrove_paper_id', 'unknown')}: {e}")
                continue
            
        # Commit each batch
        cur.connection.commit()
        
        logger.debug(f"✅ Batch {batch_num} completed: {batch_inserted} papers inserted (Total: {inserted_count}/{total_papers})")
    
    logger.debug(f"🎉 All batches completed: {inserted_count} papers successfully inserted")
    return inserted_count

import re

def sanitize_field_name(field_name: str) -> str:
    """
    Pure function: sanitizes field names for SQL column names.
    
    Args:
        field_name: Original field name
        
    Returns:
        Sanitized field name safe for SQL
    """
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Convert to lowercase
    sanitized = sanitized.lower()
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = 'f_' + sanitized
    # If empty after sanitization, use a default name
    if not sanitized:
        sanitized = 'field'
    return sanitized

def create_field_mapping(original_fields: List[str]) -> Dict[str, str]:
    """
    Pure function: creates a mapping from original field names to sanitized SQL column names.
    
    Args:
        original_fields: List of original field names
        
    Returns:
        Dictionary mapping original names to sanitized names
    """
    mapping = {}
    used_names = set()
    
    for field in original_fields:
        sanitized = sanitize_field_name(field)
        # Handle duplicates by adding a number suffix
        counter = 1
        original_sanitized = sanitized
        while sanitized in used_names:
            sanitized = f"{original_sanitized}_{counter}"
            counter += 1
        
        mapping[field] = sanitized
        used_names.add(sanitized)
    
    return mapping

def create_source_metadata_table(cur, source_name: str, metadata_fields: List[str]) -> None:
    """
    Impure function: creates a source-specific metadata table if it doesn't exist.
    
    Args:
        cur: Database cursor
        source_name: Name of the source (e.g., 'aipickle')
        metadata_fields: List of field names for the metadata table
    """
    table_name = f"{source_name.lower()}_metadata"
    
    # Create field mapping for sanitized column names
    field_mapping = create_field_mapping(metadata_fields)
    
    # Build the CREATE TABLE SQL with sanitized field names
    field_definitions = ['doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id)']
    for field in metadata_fields:
        if field != 'doctrove_paper_id':  # Already defined above
            sanitized_field = field_mapping[field]
            field_definitions.append(f'"{sanitized_field}" TEXT')
    
    field_definitions.append('PRIMARY KEY (doctrove_paper_id)')
    
    create_sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(field_definitions)}
        );
    '''
    
    cur.execute(create_sql)
    cur.connection.commit()
    
    # Store the field mapping for use during inserts
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name}_field_mapping (
            original_name TEXT PRIMARY KEY,
            sanitized_name TEXT NOT NULL
        );
    ''')
    
    # Clear existing mappings and insert new ones
    cur.execute(f'DELETE FROM {table_name}_field_mapping')
    for original, sanitized in field_mapping.items():
        cur.execute(f'''
            INSERT INTO {table_name}_field_mapping (original_name, sanitized_name)
            VALUES (%s, %s)
        ''', (original, sanitized))
    
    cur.connection.commit()

def count_papers_in_database(connection_factory: Callable) -> int:
    """
    Impure function: counts papers in the database.
    
    Args:
        connection_factory: Function that creates database connections
        
    Returns:
        Number of papers in the database
    """
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM doctrove_papers")
            return cur.fetchone()[0]

def update_database_schema(cur) -> None:
    """
    Impure function: updates the database schema to use the new date structure.
    
    Args:
        cur: Database cursor
    """
    # Check if we need to update the schema
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'doctrove_papers' 
        AND column_name IN ('doctrove_primary_date', 'doctrove_date_posted', 'doctrove_date_published')
    """)
    
    existing_columns = {row[0] for row in cur.fetchall()}
    
    # If the new column doesn't exist, we need to update the schema
    if 'doctrove_primary_date' not in existing_columns:
        print("Updating database schema...")
        
        # Add the new primary_date column
        cur.execute("ALTER TABLE doctrove_papers ADD COLUMN doctrove_primary_date DATE")
        print("Added doctrove_primary_date column")
        
        # If the old columns exist, migrate data and then remove them
        if 'doctrove_date_posted' in existing_columns:
            # Use date_posted as the primary date for existing records
            cur.execute("""
                UPDATE doctrove_papers 
                SET doctrove_primary_date = doctrove_date_posted 
                WHERE doctrove_primary_date IS NULL AND doctrove_date_posted IS NOT NULL
            """)
            print("Migrated date_posted to primary_date")
            
            # Remove the old column
            cur.execute("ALTER TABLE doctrove_papers DROP COLUMN doctrove_date_posted")
            print("Removed doctrove_date_posted column")
        
        if 'doctrove_date_published' in existing_columns:
            # Remove the old column
            cur.execute("ALTER TABLE doctrove_papers DROP COLUMN doctrove_date_published")
            print("Removed doctrove_date_published column")
        
        cur.connection.commit()
        print("Database schema updated successfully") 