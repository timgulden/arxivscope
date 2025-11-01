# Database Migration Strategy for Portable Demo

> **Current Database Size**: 393GB (PostgreSQL 14)  
> **Challenge**: Create portable demonstration version on 2TB USB drive  
> **Goal**: Maintain full functionality while ensuring data portability and security

---

## **I. CURRENT DATABASE ANALYSIS**

### **A. Database Scale and Structure**

**Total Size**: 393GB in `/var/lib/postgresql/14/main14/`
- **Main Papers Table**: ~326GB (17.8M papers)
- **OpenAlex Metadata**: ~62GB 
- **Enrichment Tables**: ~2GB
- **Other Tables**: ~3GB

**Data Sources Breakdown**:
- **OpenAlex**: 17,785,865 papers (✅ Public, safe for demo)
- **RAND Publications**: 71,622 papers (⚠️ Filter required)
- **External Publications**: 10,221 papers (⚠️ Review required)
- **AI Pickle**: 2,749 papers (✅ Public ArXiv subset)

### **B. Migration Complexity Assessment**

**High Complexity Factors**:
- **Massive Size**: 393GB requires careful planning
- **Multiple Data Sources**: Complex filtering requirements
- **Rich Metadata**: Extensive enrichment and relationship data
- **Performance Dependencies**: Indexes, constraints, and optimizations

**Simplification Opportunities**:
- **Source Filtering**: Can reduce to ~280GB by using only OpenAlex + ArXiv
- **Selective Export**: Can create focused subsets for different demo scenarios
- **Compression**: Database dumps compress significantly (5-10x reduction)

---

## **II. MIGRATION STRATEGIES**

### **A. Strategy 1: Full Database Clone with Filtering (Recommended)**

**Approach**: Clone entire database structure, then filter data by source

**Advantages**:
- ✅ Preserves all relationships and constraints
- ✅ Maintains full functionality
- ✅ Simple to implement and test
- ✅ Easy to update with new filtered criteria

**Implementation**:
```bash
#!/bin/bash
# full-clone-migration.sh

echo "🗄️ Creating filtered database clone..."

# 1. Create new database with same structure
PGPORT=5434 PGPASSWORD=doctrove_admin createdb -h localhost -U doctrove_admin doctrove_demo

# 2. Clone schema (structure only, no data)
PGPORT=5434 PGPASSWORD=doctrove_admin pg_dump -h localhost -U doctrove_admin \
    --schema-only --no-owner --no-privileges doctrove | \
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin doctrove_demo

# 3. Copy filtered data (safe sources only)
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove -c "
    INSERT INTO doctrove_demo.doctrove_papers 
    SELECT * FROM doctrove_papers 
    WHERE doctrove_source IN ('openalex', 'aipickle');
    
    -- Copy related metadata tables
    INSERT INTO doctrove_demo.openalex_metadata 
    SELECT om.* FROM openalex_metadata om
    INNER JOIN doctrove_demo.doctrove_papers dp 
    ON om.openalex_id = dp.doctrove_openalex_id;
    
    INSERT INTO doctrove_demo.aipickle_metadata 
    SELECT am.* FROM aipickle_metadata am
    INNER JOIN doctrove_demo.doctrove_papers dp 
    ON am.aipickle_id = dp.doctrove_aipickle_id;
"

# 4. Rebuild indexes and constraints
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove_demo -c "
    REINDEX DATABASE doctrove_demo;
    ANALYZE;
"

echo "✅ Filtered database created: doctrove_demo"
```

**Expected Size**: ~280GB (OpenAlex + ArXiv only)

### **B. Strategy 2: Selective Sample Database**

**Approach**: Create smaller, curated datasets for different demonstration scenarios

**Sample Sizes**:
- **Quick Demo**: 100K papers (~2GB) - Fast startup, basic functionality
- **Performance Demo**: 1M papers (~20GB) - Show scale capabilities
- **Full Feature Demo**: 5M papers (~100GB) - Complete functionality showcase

**Implementation**:
```bash
#!/bin/bash
# selective-sample-migration.sh

echo "🎯 Creating curated demonstration datasets..."

# Create quick demo database (100K papers)
PGPORT=5434 PGPASSWORD=doctrove_admin createdb -h localhost -U doctrove_admin doctrove_quick_demo

# Sample recent AI/ML papers for focused demonstration
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove_quick_demo -c "
    -- Copy schema
    $(PGPORT=5434 PGPASSWORD=doctrove_admin pg_dump -h localhost -U doctrove_admin --schema-only doctrove)
    
    -- Sample 100K recent papers with AI/ML keywords
    INSERT INTO doctrove_papers 
    SELECT * FROM doctrove.doctrove_papers 
    WHERE doctrove_source = 'openalex'
    AND doctrove_primary_date >= '2020-01-01'
    AND (doctrove_title ILIKE '%artificial intelligence%' 
         OR doctrove_title ILIKE '%machine learning%'
         OR doctrove_title ILIKE '%neural network%'
         OR doctrove_title ILIKE '%deep learning%')
    ORDER BY doctrove_primary_date DESC
    LIMIT 100000;
"

echo "✅ Quick demo database created: 100K papers, ~2GB"
```

### **C. Strategy 3: Compressed Archive Approach**

**Approach**: Export database as compressed SQL dump for maximum portability

**Implementation**:
```bash
#!/bin/bash
# compressed-archive-migration.sh

echo "📦 Creating compressed database archive..."

# 1. Export filtered data as compressed SQL
PGPORT=5434 PGPASSWORD=doctrove_admin pg_dump -h localhost -U doctrove_admin \
    --no-owner --no-privileges --compress=9 \
    --exclude-table='*log*' --exclude-table='*cache*' \
    --where="doctrove_source IN ('openalex', 'aipickle')" \
    doctrove > doctrove_demo_compressed.sql.gz

# 2. Create restoration script
cat > restore-demo-database.sh << 'EOF'
#!/bin/bash
echo "🔄 Restoring demonstration database..."

# Create database
createdb doctrove_demo

# Restore from compressed archive
gunzip -c doctrove_demo_compressed.sql.gz | psql doctrove_demo

echo "✅ Database restored and ready for demonstration"
EOF

chmod +x restore-demo-database.sh

echo "✅ Compressed archive created: ~30-50GB (10x compression)"
```

---

## **III. PORTABLE DEPLOYMENT OPTIONS**

### **A. Option 1: Docker-based Portable Database**

**Advantages**: 
- ✅ Self-contained environment
- ✅ Consistent across different systems
- ✅ Easy startup/shutdown
- ✅ No system PostgreSQL conflicts

**Docker Compose Setup**:
```yaml
# docker-compose-demo.yml
version: '3.8'
services:
  doctrove-demo-db:
    image: postgres:14
    environment:
      POSTGRES_DB: doctrove_demo
      POSTGRES_USER: demo_user
      POSTGRES_PASSWORD: demo_pass
    volumes:
      - ./database-data:/var/lib/postgresql/data
      - ./database-init:/docker-entrypoint-initdb.d
    ports:
      - "5433:5432"  # Different port to avoid conflicts
    command: >
      postgres 
      -c shared_preload_libraries=pg_stat_statements
      -c max_connections=100
      -c shared_buffers=2GB
      -c effective_cache_size=6GB
```

**Startup Script**:
```bash
#!/bin/bash
# start-portable-demo.sh

echo "🚀 Starting DocScope Portable Demonstration..."

# Check available disk space
AVAILABLE_GB=$(df . | tail -1 | awk '{print int($4/1024/1024)}')
if [ $AVAILABLE_GB -lt 100 ]; then
    echo "⚠️  Warning: Less than 100GB available. Demo may be slow."
fi

# Start database container
docker-compose -f docker-compose-demo.yml up -d doctrove-demo-db

# Wait for database to be ready
echo "⏳ Waiting for database to initialize..."
until docker-compose -f docker-compose-demo.yml exec -T doctrove-demo-db pg_isready -U demo_user; do
    sleep 5
done

# Start application services
docker-compose -f docker-compose-demo.yml up -d

echo "✅ Demo ready at: http://localhost:8080"
echo "📊 Database: $(docker-compose -f docker-compose-demo.yml exec -T doctrove-demo-db psql -U demo_user -d doctrove_demo -t -c 'SELECT COUNT(*) FROM doctrove_papers;' | xargs) papers loaded"
```

### **B. Option 2: Portable PostgreSQL Installation**

**Advantages**:
- ✅ No Docker dependency
- ✅ Direct file access
- ✅ Maximum performance
- ✅ Smaller footprint

**Implementation**: Use PostgreSQL Portable or create custom portable installation

### **C. Option 3: SQLite Conversion (For Smaller Demos)**

**Advantages**:
- ✅ Single file database
- ✅ No server required
- ✅ Maximum portability
- ✅ Built into most systems

**Limitations**:
- ❌ Limited to smaller datasets (< 1M papers)
- ❌ No advanced PostgreSQL features
- ❌ Slower for complex queries

---

## **IV. RECOMMENDED IMPLEMENTATION PLAN**

### **Phase 1: Assessment and Planning (1 day)**

```bash
# 1. Analyze current database for RAND content
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove -c "
    SELECT doctrove_source, COUNT(*) 
    FROM doctrove_papers 
    GROUP BY doctrove_source;
"

# 2. Estimate filtered database size
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove -c "
    SELECT COUNT(*) as safe_papers 
    FROM doctrove_papers 
    WHERE doctrove_source IN ('openalex', 'aipickle');
"

# 3. Test sample export performance
PGPORT=5434 PGPASSWORD=doctrove_admin pg_dump -h localhost -U doctrove_admin \
    --table=doctrove_papers --where="doctrove_source = 'aipickle'" \
    --no-owner --no-privileges doctrove > sample_export_test.sql
```

### **Phase 2: Create Filtered Database (2-3 days)**

```bash
# Day 1: Create filtered database with safe data only
./full-clone-migration.sh

# Day 2: Test functionality with filtered data
# - Start application with doctrove_demo database
# - Test all major features (search, clustering, filtering)
# - Verify performance with reduced dataset

# Day 3: Optimize and validate
# - Rebuild indexes for optimal performance
# - Run full test suite against demo database
# - Document any functionality differences
```

### **Phase 3: Portable Package Creation (2 days)**

```bash
# Day 1: Create Docker-based portable environment
# - Set up Docker Compose configuration
# - Create database initialization scripts
# - Test startup/shutdown procedures

# Day 2: USB drive preparation
# - Export database to compressed format
# - Create complete portable package
# - Test on clean system (different computer)
```

### **Phase 4: Documentation and Testing (1 day)**

```bash
# Create comprehensive documentation
# - Database migration procedure
# - Portable deployment instructions
# - Troubleshooting guide
# - Performance benchmarks

# Final testing
# - Test complete portable package on different systems
# - Verify all demonstration scenarios work
# - Document system requirements and limitations
```

---

## **V. SIZING AND STORAGE REQUIREMENTS**

### **A. Storage Breakdown for 2TB USB Drive**

```
2TB USB Drive Allocation:
├── Database (Filtered)                    ~300GB
│   ├── PostgreSQL Data Files             ~280GB
│   ├── Database Dumps (Compressed)       ~30GB
│   └── Database Initialization Scripts   ~100MB
├── Application Code                       ~5GB
│   ├── DocScope Platform Repository      ~2GB
│   ├── Docker Images                      ~2GB
│   └── Dependencies and Tools             ~1GB
├── Documentation and Presentations        ~10GB
│   ├── Technical Documentation           ~1GB
│   ├── Presentation Materials            ~5GB
│   └── Screenshots and Videos            ~4GB
├── Demonstration Scenarios                ~50GB
│   ├── Quick Demo Dataset (100K papers)  ~5GB
│   ├── Performance Demo (1M papers)      ~25GB
│   └── Feature Demo (2M papers)          ~20GB
└── Free Space (Buffer)                    ~1.6TB
```

### **B. Performance Considerations**

**USB 3.0/3.1 Performance**:
- **Read Speed**: 100-200 MB/s (adequate for database queries)
- **Write Speed**: 50-100 MB/s (sufficient for demo scenarios)
- **Startup Time**: 2-5 minutes for full database initialization

**System Requirements**:
- **RAM**: 8GB minimum (16GB recommended for full dataset)
- **CPU**: Modern multi-core processor
- **Available Disk**: 100GB for temporary operations
- **Docker**: Required for containerized deployment

---

## **VI. RISK MITIGATION AND BACKUP STRATEGIES**

### **A. Data Security**

```bash
# Verify no proprietary content in demo database
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove_demo -c "
    SELECT DISTINCT doctrove_source FROM doctrove_papers;
    -- Should only show: openalex, aipickle
"

# Sample titles for manual review
PGPORT=5434 PGPASSWORD=doctrove_admin psql -h localhost -U doctrove_admin -d doctrove_demo -c "
    SELECT doctrove_title, doctrove_source 
    FROM doctrove_papers 
    ORDER BY RANDOM() 
    LIMIT 20;
"
```

### **B. Backup and Recovery**

```bash
# Create multiple backup formats
# 1. Compressed SQL dump (most portable)
pg_dump --compress=9 doctrove_demo > doctrove_demo.sql.gz

# 2. Binary backup (fastest restore)
pg_dump --format=custom doctrove_demo > doctrove_demo.backup

# 3. Directory format (parallel restore)
pg_dump --format=directory --jobs=4 doctrove_demo --file=doctrove_demo_dir
```

### **C. Testing and Validation**

```bash
# Comprehensive testing script
#!/bin/bash
# test-demo-database.sh

echo "🧪 Testing demonstration database..."

# 1. Basic connectivity
psql -d doctrove_demo -c "SELECT version();"

# 2. Data integrity
psql -d doctrove_demo -c "SELECT COUNT(*) FROM doctrove_papers;"

# 3. Search functionality
psql -d doctrove_demo -c "SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_title ILIKE '%machine learning%';"

# 4. Performance test
time psql -d doctrove_demo -c "SELECT doctrove_source, COUNT(*) FROM doctrove_papers GROUP BY doctrove_source;"

echo "✅ Database testing complete"
```

---

## **VII. CONCLUSION**

### **Recommended Approach**: Full Database Clone with Filtering

**Why This Approach**:
1. **Preserves Functionality**: Maintains all relationships and features
2. **Manageable Size**: ~280GB fits comfortably on 2TB drive
3. **Professional Quality**: Full-featured demonstration capability
4. **Secure**: Only public data sources (OpenAlex + ArXiv)
5. **Portable**: Docker-based deployment works anywhere

**Timeline**: 1 week total
- **2 days**: Database analysis and filtering
- **2 days**: Portable environment creation
- **2 days**: Testing and documentation
- **1 day**: Final packaging and validation

**Result**: Professional, portable demonstration showcasing your technical capabilities with 17.8M papers and full system functionality.


