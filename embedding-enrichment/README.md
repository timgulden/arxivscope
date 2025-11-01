# Embedding Enrichment Service

> **Current Environment (October 2025)**: This service runs on a local laptop environment. PostgreSQL on port 5432 (internal drive). UMAP model stored on internal drive. See [CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md) for current setup details.

Generates vector embeddings (1536-dimensional) for papers using OpenAI's text-embedding-3-small model and 2D projections for visualization using UMAP.

## Current Status

**🚀 Functional Event Listener Active**: The system is currently running a high-performance functional event listener for embedding generation.

### Performance Metrics
- **Processing Rate**: ~2,500 papers/minute
- **Batch Size**: 250 papers per API call
- **Database Optimization**: NULL index for fast paper fetching
- **Expected Completion**: ~3.5 days for 13.6M papers

> **Note**: For detailed performance analysis and optimization techniques, see [Embedding Generation Performance Guide](../../docs/OPERATIONS/EMBEDDING_GENERATION_PERFORMANCE.md)

## Architecture

This service follows **functional programming principles** with **interceptor pattern** for dependency injection and cross-cutting concerns:

- **Pure Functions**: All business logic in `enrichment.py` is pure and testable
- **Interceptor Pattern**: Database operations, logging, and error handling via interceptors
- **Dependency Injection**: Connection factory pattern for database operations
- **Comprehensive Testing**: Unit tests for pure functions + integration tests for workflows
- **Adaptive Batch Sizing**: Intelligent batch size selection based on dataset characteristics
- **General Enrichment Framework**: Extensible architecture for adding new enrichment types

## Features

- **Incremental Processing**: Process new papers without rebuilding the entire model
- **Full Rebuild**: Annual rebuild of all 2D embeddings as research space evolves
- **Production Ready**: Robust error handling and monitoring
- **Scalable**: Handles millions of records with adaptive batch sizing
- **Testable**: Pure functions with comprehensive test coverage
- **Adaptive**: Automatically determines optimal batch sizes based on dataset size
- **Extensible**: General enrichment framework for adding new enrichment types

## Quick Start

### Check Status
```bash
python main.py --mode status
```

### Functional Event Listener (Embedding Generation)
```bash
# Start the high-performance functional event listener
cd embedding-enrichment
python event_listener_functional.py

# Run tests for the functional event listener
python run_event_listener_tests.py
```

### Daily Incremental Processing
```bash
python main.py --mode incremental
```

### Annual Full Rebuild
```bash
python main.py --mode full-rebuild
```

### Production Workflow
```bash
# Monitor system health
python production_workflow.py monitor

# Daily processing
python production_workflow.py daily

# Annual rebuild
python production_workflow.py annual

# View adaptive batch sizing recommendations
python production_workflow.py batch-info
```

### Test Enrichment Framework
```bash
# Test the general enrichment framework
python test_enrichment_framework.py
```

## Testing

### Unit Tests (Pure Functions)
```bash
python test_enrichment.py
```

### Integration Tests (Full Workflows)
```bash
python test_integration.py
```

### Enrichment Framework Tests
```bash
python test_enrichment_framework.py
```

## Architecture Details

### Interceptor Pattern
The service uses interceptors for:
- **Database Setup**: Connection factory injection
- **Logging**: Entry/exit logging for all phases
- **Error Handling**: Graceful error recovery
- **Status Reporting**: Progress and completion tracking
- **Adaptive Batch Sizing**: Intelligent batch size determination

### Pure Functions
All business logic in `enrichment.py` is pure:
- `parse_embedding_string()`: Parse JSON embeddings
- `extract_embeddings_from_papers()`: Extract embeddings from papers
- `fit_umap_model()`: Fit UMAP model to embeddings
- `transform_embeddings_to_2d()`: Transform to 2D coordinates
- `validate_2d_coordinates()`: Validate coordinate tuples

### Database Layer
Standardized database functions using connection factory pattern:
- `create_connection_factory()`: Dependency injection
- `get_papers_with_embeddings()`: Retrieve papers with embeddings
- `insert_2d_embeddings()`: Insert 2D embeddings
- `clear_2d_embeddings()`: Clear existing embeddings

## General Enrichment Architecture

The service includes a **general enrichment framework** that makes adding new enrichment types (like credibility scores, topic classification, etc.) as simple as possible.

### Enrichment Types

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

### Key Principle: Source Metadata Tables Remain Pure

**Source metadata tables should NEVER be modified by enrichment processes:**

- ✅ **Source tables contain**: Raw data exactly as ingested from sources
- ✅ **Source tables are**: Read-only for enrichments
- ✅ **Enrichments read from**: Source tables but never write to them
- ✅ **All computed values**: Go into dedicated enrichment tables

### Adding New Enrichments

#### **Step 1: Create Enrichment Class**
```python
from enrichment_framework import BaseEnrichment

class CredibilityEnrichment(BaseEnrichment):
    def __init__(self):
        super().__init__("credibility", "derived")
    
    def get_required_fields(self) -> List[str]:
        return ["doctrove_paper_id", "doctrove_source", "doctrove_source_id"]
    
    def process_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Your enrichment logic here
        results = []
        for paper in papers:
            # Calculate credibility score
            score = self.calculate_credibility(paper)
            results.append({
                'paper_id': paper['doctrove_paper_id'],
                'credibility_score': score,
                'credibility_confidence': 0.8,
                'credibility_factors': {'source': 0.9},
                'credibility_metadata': {'source': paper['doctrove_source']}
            })
        return results
```

#### **Step 2: Run Enrichment**
```python
# Create and run enrichment
credibility = CredibilityEnrichment()
papers = get_papers_for_enrichment(connection_factory)
result_count = credibility.run_enrichment(
    papers, 
    "Credibility score based on journal impact, citations, and source reputation"
)
```

#### **Step 3: Query with Enrichment**
```sql
SELECT p.doctrove_paper_id, p.doctrove_title, c.credibility_score
FROM doctrove_papers p
LEFT JOIN credibility_enrichment c ON p.doctrove_paper_id = c.doctrove_paper_id
WHERE c.credibility_score > 0.8
ORDER BY c.credibility_score DESC;
```

### Example: Credibility Score Enrichment

The framework includes a complete example implementation of a credibility score enrichment that:

- **Combines multiple factors**: Journal impact factor, citation count, author count, source reputation
- **Handles missing data**: Gracefully processes papers with partial metadata
- **Provides confidence scores**: Indicates reliability of the enrichment
- **Stores detailed factors**: JSONB fields for transparency and debugging
- **Follows standard patterns**: Consistent with all other enrichments

### Benefits of the Enrichment Framework

1. **Consistency**: Standard patterns for all enrichment types
2. **Scalability**: Separate tables prevent main table bloat
3. **Flexibility**: JSONB fields allow complex metadata
4. **Maintainability**: Clear separation of concerns
5. **Queryability**: Easy to join and filter by enrichments
6. **Versioning**: Built-in version tracking for enrichments
7. **Registry**: Central tracking of all enrichments
8. **Data Integrity**: Source tables remain pure and unmodified
9. **Clear Boundaries**: Raw data vs. computed data clearly separated

## Adaptive Batch Sizing

The service automatically determines optimal batch sizes based on dataset characteristics:

### Batch Size Recommendations

| Dataset Size | First Batch | Subsequent Batches | Rationale |
|--------------|-------------|-------------------|-----------|
| ≤ 5,000 papers | 500 | 500 | Small datasets: 500 papers sufficient for local structure |
| 5,000 - 50,000 papers | 2,000 | 1,000 | Medium datasets: 2000 papers for good field coverage |
| 50,000 - 500,000 papers | 10,000 | 2,000 | Large datasets: 10000 papers for comprehensive coverage |
| > 500,000 papers | 20,000 | 5,000 | Very large datasets: 20000 papers for maximum quality |

### Why Larger Initial Batches Matter

**UMAP's Neighborhood Structure**:
- Each paper connects to ~15 nearest neighbors (`n_neighbors=15`)
- Larger initial batches create richer local connectivity
- Better coverage of the embedding space across diverse subjects

**Academic Diversity Coverage**:
- **Major fields**: ~50-100 (Physics, Chemistry, Biology, History, etc.)
- **Subfields**: ~500-1,000 (Quantum Physics, Medieval History, ML, etc.)
- **Specialized topics**: ~5,000-10,000 (Specific algorithms, periods, etc.)

**Quality vs. Speed Trade-offs**:
- **10,000 papers**: ~2-5 minutes processing, ~200-500MB RAM
- **20,000 papers**: ~5-10 minutes processing, ~500MB-1GB RAM
- **Better model quality** justifies longer initial processing time

### Manual Override
You can override adaptive sizing with command-line arguments:
```bash
# Force specific batch sizes
python main.py --mode incremental --first-batch-size 10000 --batch-size 2000
```

## Incremental UMAP Processing
1. **First Batch**: Fit UMAP model on initial papers (adaptive size based on dataset)
2. **Model Persistence**: Save fitted UMAP model to disk
3. **Subsequent Batches**: Load model and use `transform()` for new papers
4. **Consistency**: All papers projected into same 2D coordinate space

## Database Schema
- `title_embedding_2d`: PostgreSQL point type for spatial indexing
- `title_embedding_2d_metadata`: JSONB with UMAP parameters and version
- `embedding_2d_updated_at`: Timestamp for tracking
- `{enrichment_name}_enrichment`: Dedicated tables for derived enrichments
- `enrichment_registry`: Central registry of all enrichment modules

## Production Workflow

### Daily Operations
```bash
# 1. Monitor system health
python production_workflow.py monitor

# 2. Process new papers incrementally
python production_workflow.py daily
```

### Annual Maintenance
```bash
# Full rebuild with adaptive batch sizing for optimal quality
python production_workflow.py annual
```

### System Monitoring
```bash
# Check adaptive batch sizing recommendations
python production_workflow.py batch-info
```

### Enrichment Management
```bash
# Test new enrichment types
python test_enrichment_framework.py

# View available enrichments
python -c "from enrichment_framework import get_available_enrichments; print(get_available_enrichments())"
```

## Configuration

### UMAP Parameters (`config.py`)
```python
UMAP_CONFIG = {
    'n_neighbors': 15,      # Local neighborhood size
    'min_dist': 0.1,        # Minimum distance between points
    'n_components': 2,      # Output dimensions
    'metric': 'cosine',     # Distance metric
    'random_state': 42,     # Reproducibility
    'verbose': True         # Progress logging
}
```

### Adaptive Batch Sizing
```python
BATCH_SIZING_CONFIG = {
    'small_dataset': {
        'max_papers': 5000,
        'first_batch_size': 500,
        'subsequent_batch_size': 500,
        'rationale': 'Small datasets: 500 papers sufficient for local structure'
    },
    'large_dataset': {
        'max_papers': 500000,
        'first_batch_size': 10000,
        'subsequent_batch_size': 2000,
        'rationale': 'Large datasets: 10000 papers for comprehensive coverage'
    }
    # ... more configurations
}
```

### Database Configuration
Set environment variables via `.env.local` file (project root):
```bash
DB_HOST=localhost
DOC_TROVE_PORT=5432
DB_NAME=doctrove
DB_USER=doctrove_admin
DB_PASSWORD=  # Empty for trust authentication (local setup)
```

### UMAP Model Configuration
UMAP model path configured via `.env.local`:
```bash
UMAP_MODEL_PATH=/Users/tgulden/Documents/DocTrove/arxivscope/models/umap_model.pkl
```

**Note**: Model stored on internal drive (not external drive dependency)

## Monitoring

### Status Check
```bash
python main.py --mode status
```
Shows:
- Total papers with embeddings
- Papers with 2D embeddings
- Papers needing processing
- Completion percentage
- **Adaptive batch sizing recommendations**

### System Health
```bash
python production_workflow.py monitor
```
Checks:
- UMAP model file existence and size
- Database connectivity
- Current processing status
- **Dataset size and batch sizing rationale**

### Batch Sizing Recommendations
```bash
python production_workflow.py batch-info
```
Shows:
- Recommended batch sizes for different dataset sizes
- Rationale for each recommendation
- Memory and processing time estimates

### Enrichment Status
```bash
python -c "from enrichment_framework import get_available_enrichments; enrichments = get_available_enrichments(); print('Available enrichments:', [e['enrichment_name'] for e in enrichments])"
```

## Error Handling

- **Model Loading**: Graceful fallback to new model creation
- **Database Errors**: Connection retry and rollback
- **Invalid Embeddings**: Skip and log warnings
- **Batch Failures**: Continue with remaining batches
- **Interceptor Errors**: Comprehensive error logging and recovery
- **Adaptive Sizing**: Fallback to conservative batch sizes if errors occur
- **Enrichment Errors**: Individual paper failures don't stop batch processing

## Performance Considerations

### Memory Usage
- UMAP model: ~3MB for 2,749 papers, scales with dataset size
- **Adaptive batch processing**: Configurable to fit available RAM
- Database connections: Proper cleanup and connection pooling

### Processing Speed
- **First batch (model fitting)**: ~30-60 seconds for 2,000 papers, ~2-5 minutes for 10,000 papers
- **Subsequent batches (transform)**: ~1-2 seconds for 500 papers, ~5-10 seconds for 2,000 papers
- **Database updates**: ~0.1 seconds per paper
- **Enrichment processing**: Varies by complexity, typically 0.1-1 second per paper

### Scalability
- **Linear scaling**: Processing time scales linearly with paper count
- **Batch efficiency**: Larger batches reduce overhead
- **Model persistence**: Avoids repeated model fitting
- **Adaptive sizing**: Optimizes for both quality and performance
- **Enrichment isolation**: Each enrichment type scales independently

## Design Principles

This service follows our established design principles. See `DESIGN_PRINCIPLES.md` for detailed documentation and `DESIGN_PRINCIPLES_QUICK_REFERENCE.md` for a quick reference.

### Core Principles
- **Functional Programming**: Pure functions with no side effects
- **Interceptor Pattern**: Cross-cutting concerns via composable interceptors
- **Dependency Injection**: Connection factory pattern for testability
- **Comprehensive Testing**: Unit, integration, and framework tests
- **Data Integrity**: Source tables remain pure and unmodified
- **Standardized Patterns**: Consistent architecture across all components

### Key Benefits
- **Maintainable**: Clear patterns and comprehensive testing
- **Scalable**: Adaptive design and efficient resource usage
- **Reliable**: Robust error handling and data integrity
- **Testable**: Pure functions and dependency injection
- **Observable**: Comprehensive logging and monitoring

## Troubleshooting

### Common Issues
1. **No UMAP model found**: Run with `--mode incremental` to create new model
2. **Database connection errors**: Check credentials and network connectivity
3. **Memory errors**: Reduce batch size in configuration
4. **Inconsistent coordinates**: Run full rebuild to ensure consistency
5. **Poor model quality**: Increase first batch size for better coverage
6. **Enrichment failures**: Check source metadata availability and enrichment logic

### Logs
- UMAP progress: Verbose output during model fitting
- Database operations: Connection and transaction logs
- Error details: Full stack traces for debugging
- Interceptor logs: Phase entry/exit and error handling
- **Adaptive sizing**: Batch size determination and rationale
- **Enrichment logs**: Processing progress and individual paper results

## Future Enhancements

- **Parallel processing**: Multi-threaded batch processing
- **Model versioning**: Track UMAP model versions and parameters
- **A/B testing**: Compare different UMAP configurations
- **Automated scheduling**: Cron jobs for daily processing
- **Metrics collection**: Processing time and quality metrics
- **Health checks**: Automated system health monitoring
- **Dynamic batch sizing**: Real-time adjustment based on system resources
- **Enrichment marketplace**: Shared enrichment modules across projects
- **Real-time enrichments**: Stream processing for new papers
- **Enrichment quality metrics**: Automated assessment of enrichment accuracy 