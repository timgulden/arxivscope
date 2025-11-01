# RAND Publications Ingestion Plan

## Overview
Ingest ~20,000 additional papers (RAND publications + external RAND author papers) locally before server deployment.

## Dataset Breakdown
```yaml
Total Target: ~20,000 papers
  - RAND Publications: ~10,000 papers
  - External RAND Author Papers: ~10,000 papers
  - Current Dataset: 2,749 papers
  - Final Dataset: ~22,749 papers
```

## Ingestion Pipeline

### **Phase 1: Data Collection (1-2 days)**

#### **RAND Publications Sources**
```yaml
Primary Sources:
  - RAND Publications Database
  - RAND Research Reports
  - RAND Working Papers
  - RAND Journal Articles

Data Fields:
  - Title, Abstract, Authors
  - Publication Date, DOI
  - RAND Project/Program
  - Document Type (Report, Article, etc.)
  - Full Text (if available)
```

#### **External RAND Author Papers**
```yaml
Sources:
  - Google Scholar (RAND author profiles)
  - ResearchGate (RAND author profiles)
  - arXiv (RAND author submissions)
  - PubMed (RAND author publications)

Identification:
  - Author affiliation with RAND
  - Publication date during RAND employment
  - Cross-reference with RAND author database
```

### **Phase 2: Data Processing (2-3 days)**

#### **Standardization**
```python
# Data cleaning pipeline
def process_randpub(raw_data):
    return {
        'title': clean_title(raw_data['title']),
        'abstract': extract_abstract(raw_data),
        'authors': parse_authors(raw_data['authors']),
        'date': standardize_date(raw_data['date']),
        'doi': extract_doi(raw_data),
        'source': 'RAND_PUBLICATION',
        'rand_project': raw_data.get('project'),
        'document_type': raw_data.get('type'),
        'full_text': raw_data.get('full_text')
    }
```

#### **Deduplication**
```python
# Remove duplicates based on:
# 1. DOI match
# 2. Title similarity (>95%)
# 3. Abstract similarity (>90%)
# 4. Author overlap (>80%)
```

### **Phase 3: Embedding Generation (1-2 days)**

#### **Batch Processing**
```yaml
Current Setup:
  - Batch Size: 100,000 (optimized)
  - Processing: ~2,749 papers in ~30 minutes
  - Estimated Time: ~4-6 hours for 20,000 papers

Resources:
  - Local machine already configured
  - Azure OpenAI quota available
  - UMAP model can handle 22K+ papers
```

#### **UMAP Projection**
```python
# Update UMAP model with new data
def update_umap_model(new_papers):
    # Combine existing + new embeddings
    all_embeddings = existing_embeddings + new_embeddings
    
    # Retrain UMAP model
    umap_model = UMAP(n_components=2, random_state=42)
    umap_model.fit(all_embeddings)
    
    # Generate 2D projections
    projections_2d = umap_model.transform(all_embeddings)
    
    return umap_model, projections_2d
```

## **Database Migration Strategy**

### **Pre-Migration Preparation**
```bash
# 1. Backup current database
pg_dump -h localhost -U tgulden -d doctrove --verbose --clean --no-owner > doctrove_backup_$(date +%Y%m%d).sql

# 2. Create migration script
cat > migrate_rand_data.py << 'EOF'
#!/usr/bin/env python3
import psycopg2
import json
from datetime import datetime

def migrate_randpubs():
    # Connect to database
    conn = psycopg2.connect(
        host="localhost",
        database="doctrove",
        user="tgulden",
        password="your_password"
    )
    
    # Insert new papers
    # Insert embeddings
    # Update UMAP model
    # Generate 2D projections
    
    conn.close()
EOF
```

### **Migration Steps**
```yaml
1. Complete local ingestion
2. Test all functionality locally
3. Create complete database dump
4. Deploy to server
5. Restore database on server
6. Verify all data and functionality
```

## **Timeline Estimate**

```yaml
Week 1:
  - Data collection (RAND publications)
  - Data cleaning and standardization
  - Initial embedding generation

Week 2:
  - External author paper collection
  - Deduplication and validation
  - Complete embedding generation
  - UMAP model update

Week 3:
  - Local testing and validation
  - Database backup and preparation
  - Server deployment
  - Data migration and verification
```

## **Resource Requirements**

### **Local Processing**
```yaml
Storage:
  - Current: ~2GB
  - Additional: ~8GB (20K papers)
  - Total: ~10GB

Memory:
  - UMAP processing: 16GB+ recommended
  - Current setup: Sufficient

Processing Time:
  - Embedding generation: 4-6 hours
  - UMAP projection: 1-2 hours
  - Total: 1-2 days
```

### **Database Impact**
```yaml
Table Growth:
  - doctrove_papers: +20K records
  - aipickle_metadata: +20K records
  - embeddings: +20K records
  - Total growth: ~60K records

Performance:
  - Query time: Minimal impact
  - Indexes: May need optimization
  - Storage: +8GB
```

## **Quality Assurance**

### **Data Validation**
```python
def validate_rand_ingestion():
    # Check data completeness
    # Verify embedding quality
    # Test semantic search
    # Validate clustering
    # Performance testing
```

### **Testing Checklist**
```yaml
- [ ] All 20K papers ingested
- [ ] Embeddings generated correctly
- [ ] 2D projections look reasonable
- [ ] Semantic search works
- [ ] Clustering quality maintained
- [ ] API performance acceptable
- [ ] Frontend displays correctly
```

## **Benefits of This Approach**

### **Technical Benefits**
1. **Proven Pipeline** - Use existing, tested ingestion system
2. **Quality Control** - Validate data before deployment
3. **Performance Testing** - Ensure system handles larger dataset
4. **Simple Migration** - One-time database transfer

### **Operational Benefits**
1. **Parallel Work** - Ingestion and deployment can happen simultaneously
2. **Risk Mitigation** - Issues caught locally before server deployment
3. **Cost Effective** - No cloud costs during ingestion
4. **Flexible Timeline** - Can adjust based on deployment readiness

## **Next Steps**

1. **Start data collection** for RAND publications
2. **Set up external author identification** process
3. **Prepare ingestion scripts** for new data sources
4. **Plan database migration** strategy
5. **Coordinate with server deployment** timeline

This approach gives you a complete, tested dataset ready for production deployment! 