# General Enrichment Architecture

## Overview

This document outlines the architecture for adding new enrichment types to the DocTrove system. The goal is to make adding new enrichments (like credibility scores, topic classification, etc.) as simple as possible while maintaining consistency and scalability.

## Current Architecture

### 1. Main Table (`doctrove_papers`)
- Core paper data and fundamental enrichments
- **Embeddings**: `doctrove_embedding` (VECTOR)
- **2D Embeddings**: `doctrove_embedding_2d` (POINT)
- **2D Metadata**: `doctrove_embedding_2d_metadata` (JSONB)

### 2. Source-Specific Metadata (`{source}_metadata`)
- **Raw metadata from ingestion sources** - should remain pure and unmodified
- Example: `aipickle_metadata`, `arxiv_metadata`, `randpub_metadata`
- **No enrichments should be added to these tables** - they are for raw data only

### 3. Enrichment Registry (`enrichment_registry`)
- Tracks all enrichment modules
- Schema: `enrichment_name`, `table_name`, `description`, `fields` (JSONB)

## Proposed General Enrichment Architecture

### 1. Enrichment Types Classification

#### **Type A: Fundamental Enrichments** (Main Table)
- **Criteria**: Core to document understanding, used by most queries
- **Examples**: Embeddings, 2D embeddings, basic classification
- **Storage**: Directly in `doctrove_papers` table
- **Naming**: `doctrove_{enrichment_name}`

#### **Type B: Derived Enrichments** (Dedicated Tables) ⭐ **Primary Pattern**
- **Criteria**: Computed from multiple sources, complex logic, optional
- **Examples**: Credibility scores, citation analysis, topic modeling, journal impact analysis
- **Storage**: `{enrichment_name}_enrichment` tables
- **Naming**: `{enrichment_name}_{field_name}`
- **Data Sources**: Can read from main table, source metadata tables, or external APIs

### 2. Key Principle: Source Metadata Tables Remain Pure

**Source metadata tables should NEVER be modified by enrichment processes:**

- ✅ **Source tables contain**: Raw data exactly as ingested from sources
- ✅ **Source tables are**: Read-only for enrichments
- ✅ **Enrichments read from**: Source tables but never write to them
- ✅ **All computed values**: Go into dedicated enrichment tables

**Example:**
```sql
-- Source table (pure, unmodified)
CREATE TABLE aipickle_metadata (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    journal_name TEXT,           -- Raw from source
    citation_count TEXT,         -- Raw from source
    author_count TEXT,           -- Raw from source
    -- ... other raw fields
);

-- Enrichment table (computed values)
CREATE TABLE credibility_enrichment (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    credibility_score DECIMAL(5,3),      -- Computed from source data
    credibility_confidence DECIMAL(3,2),  -- Computed confidence
    credibility_factors JSONB,           -- Contributing factors
    credibility_metadata JSONB,          -- Processed metadata
    credibility_processed_at TIMESTAMP DEFAULT NOW(),
    credibility_version TEXT DEFAULT 'v1',
    PRIMARY KEY (doctrove_paper_id)
);
```

### 3. Enrichment Table Schema Pattern

```sql
-- Pattern for all derived enrichments
CREATE TABLE {enrichment_name}_enrichment (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    {enrichment_name}_score DECIMAL(5,3),           -- Main enrichment value
    {enrichment_name}_confidence DECIMAL(3,2),      -- Confidence in the enrichment
    {enrichment_name}_factors JSONB,                -- Contributing factors
    {enrichment_name}_metadata JSONB,               -- Additional metadata
    {enrichment_name}_processed_at TIMESTAMP DEFAULT NOW(),
    {enrichment_name}_version TEXT DEFAULT 'v1',
    PRIMARY KEY (doctrove_paper_id)
);

-- Example: credibility_enrichment
CREATE TABLE credibility_enrichment (
    doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id),
    credibility_score DECIMAL(5,3),                 -- 0.000 to 1.000
    credibility_confidence DECIMAL(3,2),            -- 0.00 to 1.00
    credibility_factors JSONB,                      -- {"journal_impact": 0.3, "citations": 0.4, ...}
    credibility_metadata JSONB,                     -- {"journal_name": "Nature", "citation_count": 150, ...}
    credibility_processed_at TIMESTAMP DEFAULT NOW(),
    credibility_version TEXT DEFAULT 'v1',
    PRIMARY KEY (doctrove_paper_id)
);
```

### 4. Enrichment Service Architecture

#### **Enrichment Module Pattern**
```python
class BaseEnrichment:
    """Base class for all enrichment modules."""
    
    def __init__(self, enrichment_name: str, enrichment_type: str):
        self.enrichment_name = enrichment_name
        self.enrichment_type = enrichment_type  # 'fundamental' or 'derived'
    
    def get_required_fields(self) -> List[str]:
        """Fields required from main table or source metadata."""
        raise NotImplementedError
    
    def process_papers(self, papers: List[Dict], connection_factory) -> List[Dict]:
        """Process papers and return enrichment results."""
        raise NotImplementedError
    
    def create_table_if_needed(self, connection_factory) -> None:
        """Create enrichment table if it doesn't exist."""
        raise NotImplementedError

class CredibilityEnrichment(BaseEnrichment):
    """Example: Credibility score enrichment."""
    
    def __init__(self):
        super().__init__("credibility", "derived")
    
    def get_required_fields(self) -> List[str]:
        return ["doctrove_paper_id", "doctrove_source", "doctrove_source_id"]
    
    def process_papers(self, papers: List[Dict], connection_factory) -> List[Dict]:
        results = []
        for paper in papers:
            # READ from source metadata (never write)
            source_metadata = self.get_source_metadata(paper, connection_factory)
            
            # Calculate credibility score
            score, confidence, factors, metadata = self.calculate_credibility(
                paper, source_metadata
            )
            
            results.append({
                'paper_id': paper['doctrove_paper_id'],
                'credibility_score': score,
                'credibility_confidence': confidence,
                'credibility_factors': factors,
                'credibility_metadata': metadata
            })
        
        return results
    
    def get_source_metadata(self, paper: Dict, connection_factory) -> Dict[str, Any]:
        """READ from source metadata tables (never write)."""
        source = paper.get('doctrove_source', '').lower()
        
        with connection_factory() as conn:
            with conn.cursor() as cur:
                # READ ONLY from source table
                cur.execute(f"""
                    SELECT * FROM {source}_metadata 
                    WHERE doctrove_paper_id = %s
                """, (paper['doctrove_paper_id'],))
                
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
        
        return {}
    
    def calculate_credibility(self, paper: Dict, source_metadata: Dict) -> Tuple:
        """Calculate credibility score from paper and metadata."""
        # Implementation here
        pass
```

#### **Enrichment Registry Integration**
```python
def register_enrichment(enrichment_name: str, enrichment_type: str, 
                       fields: Dict[str, str], description: str,
                       connection_factory) -> None:
    """Register a new enrichment in the registry."""
    
    table_name = f"{enrichment_name}_enrichment" if enrichment_type == "derived" else "doctrove_papers"
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
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
            """, (enrichment_name, table_name, description, json.dumps(fields), enrichment_type))
            conn.commit()
```

### 5. Database Schema Updates

#### **Enhanced Enrichment Registry**
```sql
-- Add enrichment_type to registry
ALTER TABLE enrichment_registry 
ADD COLUMN enrichment_type TEXT DEFAULT 'derived' 
CHECK (enrichment_type IN ('fundamental', 'derived'));

-- Add version tracking
ALTER TABLE enrichment_registry 
ADD COLUMN current_version TEXT DEFAULT 'v1';
```

#### **Enrichment Table Creation Helper**
```python
def create_enrichment_table(enrichment_name: str, fields: Dict[str, str], 
                           connection_factory) -> None:
    """Create enrichment table with standard pattern."""
    
    field_definitions = [
        'doctrove_paper_id UUID REFERENCES doctrove_papers(doctrove_paper_id)'
    ]
    
    for field_name, field_type in fields.items():
        field_definitions.append(f'{enrichment_name}_{field_name} {field_type}')
    
    field_definitions.extend([
        f'{enrichment_name}_processed_at TIMESTAMP DEFAULT NOW()',
        f'{enrichment_name}_version TEXT DEFAULT \'v1\'',
        'PRIMARY KEY (doctrove_paper_id)'
    ])
    
    create_sql = f'''
        CREATE TABLE IF NOT EXISTS {enrichment_name}_enrichment (
            {', '.join(field_definitions)}
        );
    '''
    
    with connection_factory() as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
            conn.commit()
```

### 6. Adding New Enrichments: Step-by-Step

#### **Step 1: Define Enrichment Type**
```python
# Determine enrichment type
if enrichment_requires_main_table_only:
    enrichment_type = "fundamental"
else:
    enrichment_type = "derived"  # Most common case
```

#### **Step 2: Create Enrichment Module**
```python
class MyEnrichment(BaseEnrichment):
    def __init__(self):
        super().__init__("my_enrichment", "derived")
    
    def get_required_fields(self) -> List[str]:
        return ["doctrove_paper_id", "doctrove_title", "doctrove_abstract"]
    
    def process_papers(self, papers: List[Dict], connection_factory) -> List[Dict]:
        # Your enrichment logic here
        # READ from source tables, but never write to them
        pass
```

#### **Step 3: Register and Create Table**
```python
# Register in enrichment registry
register_enrichment(
    enrichment_name="my_enrichment",
    enrichment_type="derived",
    fields={
        "score": "DECIMAL(5,3)",
        "confidence": "DECIMAL(3,2)",
        "factors": "JSONB"
    },
    description="My custom enrichment",
    connection_factory=connection_factory
)

# Create table
create_enrichment_table("my_enrichment", fields, connection_factory)
```

#### **Step 4: Run Enrichment**
```python
# Process papers
enrichment = MyEnrichment()
results = enrichment.process_papers(papers, connection_factory)

# Insert results
insert_enrichment_results("my_enrichment", results, connection_factory)
```

### 7. Query Integration

#### **Enrichment-Aware Queries**
```python
def build_enrichment_query(base_query: str, enrichments: List[str]) -> str:
    """Build query with enrichment joins."""
    
    joins = []
    for enrichment in enrichments:
        joins.append(f"""
            LEFT JOIN {enrichment}_enrichment 
            ON doctrove_papers.doctrove_paper_id = {enrichment}_enrichment.doctrove_paper_id
        """)
    
    return f"""
        {base_query}
        {' '.join(joins)}
    """
```

#### **Example: Credibility-Filtered Query**
```sql
SELECT p.doctrove_paper_id, p.doctrove_title, c.credibility_score
FROM doctrove_papers p
LEFT JOIN credibility_enrichment c ON p.doctrove_paper_id = c.doctrove_paper_id
WHERE c.credibility_score > 0.8
ORDER BY c.credibility_score DESC;
```

### 8. Migration Strategy

#### **For Existing 2D Embeddings**
- Keep current structure (fundamental enrichment)
- Add to enrichment registry for consistency
- Future: Consider moving to derived table if complexity increases

#### **For New Enrichments**
- Use derived table pattern by default
- Only use fundamental (main table) for core, simple enrichments
- **Never modify source metadata tables**

### 9. Benefits of This Architecture

1. **Consistency**: Standard patterns for all enrichment types
2. **Scalability**: Separate tables prevent main table bloat
3. **Flexibility**: JSONB fields allow complex metadata
4. **Maintainability**: Clear separation of concerns
5. **Queryability**: Easy to join and filter by enrichments
6. **Versioning**: Built-in version tracking for enrichments
7. **Registry**: Central tracking of all enrichments
8. **Data Integrity**: Source tables remain pure and unmodified
9. **Clear Boundaries**: Raw data vs. computed data clearly separated

### 10. Example: Credibility Score Implementation

```python
class CredibilityEnrichment(BaseEnrichment):
    def calculate_credibility(self, paper: Dict, source_metadata: Dict) -> Tuple:
        """Calculate credibility score from multiple factors."""
        
        factors = {}
        total_score = 0.0
        
        # Journal impact factor (READ from source metadata)
        if 'journal_impact_factor' in source_metadata:
            impact_factor = float(source_metadata['journal_impact_factor'])
            journal_score = min(impact_factor / 50.0, 1.0)  # Normalize to 0-1
            factors['journal_impact'] = journal_score
            total_score += journal_score * 0.3
        
        # Citation count (READ from source metadata)
        if 'citation_count' in source_metadata:
            citations = int(source_metadata['citation_count'])
            citation_score = min(citations / 1000.0, 1.0)  # Normalize to 0-1
            factors['citations'] = citation_score
            total_score += citation_score * 0.4
        
        # Author count (READ from source metadata)
        if 'author_count' in source_metadata:
            authors = int(source_metadata['author_count'])
            author_score = min(authors / 10.0, 1.0)
            factors['authors'] = author_score
            total_score += author_score * 0.1
        
        # Source reputation
        source_scores = {
            'nature': 0.9, 'science': 0.9, 'arxiv': 0.7, 'rand': 0.8
        }
        source = paper['doctrove_source'].lower()
        source_score = source_scores.get(source, 0.5)
        factors['source'] = source_score
        total_score += source_score * 0.2
        
        # Calculate confidence based on available data
        confidence = len(factors) / 4.0  # Higher if more factors available
        
        metadata = {
            'journal_name': source_metadata.get('journal_name'),
            'citation_count': source_metadata.get('citation_count'),
            'author_count': source_metadata.get('author_count'),
            'source': paper['doctrove_source']
        }
        
        return total_score, confidence, factors, metadata
```

### 11. Key Principles

1. **Source Tables Are Sacred**: Never modify source metadata tables
2. **Read-Only Access**: Enrichments can read from source tables but never write
3. **Computed Values**: All computed values go into dedicated enrichment tables
4. **Clear Separation**: Raw data vs. processed data clearly separated
5. **Standard Patterns**: All enrichments follow the same patterns
6. **Scalable Design**: Each enrichment type scales independently

This architecture ensures that source metadata tables remain pure and unmodified while providing a flexible, scalable system for adding new enrichment types. 