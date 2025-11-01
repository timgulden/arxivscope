# Incremental UMAP Processing Guide

## Overview

The system now supports **true incremental processing** for UMAP 2D embeddings, allowing you to add new papers without rebuilding the entire model. This is essential for scalability when dealing with large datasets.

## How It Works

### 1. **Combined Title + Abstract Processing**
- Both title and abstract embeddings are processed together in the same UMAP model
- This ensures they're mapped to the same 2D coordinate space
- Connection lines between title and abstract points are meaningful

### 2. **Incremental Processing Flow**
```
New Papers Added → Event Listener → Batch Processing → UMAP Transform → Database Update
```

### 3. **UMAP Model Persistence**
- First batch: Train new UMAP model on initial papers
- Subsequent batches: Load existing model and use `transform()` for new papers
- Model is saved to `umap_model.pkl` with both model and scaler

## Usage

### Event-Driven Processing (Recommended)
```bash
# Start the event listener
cd embedding-enrichment
python event_listener.py

# In another terminal, ingest papers
cd doc-ingestor
python main.py --source aipickle --limit 1000
```

The event listener will automatically:
- Generate embeddings for new papers
- Process 2D projections in batches of 100,000 papers
- Use the existing UMAP model for incremental updates

### Manual Incremental Processing
```bash
cd embedding-enrichment

# Process only papers that need 2D projections (incremental)
python combined_2d_processor.py --mode incremental --batch-size 100000

# Process all papers (full rebuild)
python combined_2d_processor.py --mode full
```

### Check Processing Status
```bash
# Check how many papers need 2D projections
psql -U tgulden -d doctrove -h localhost -c "
SELECT 
    COUNT(*) FILTER (WHERE doctrove_title_embedding IS NOT NULL AND title_embedding_2d IS NULL) as title_2d_needed,
    COUNT(*) FILTER (WHERE doctrove_abstract_embedding IS NOT NULL AND abstract_embedding_2d IS NULL) as abstract_2d_needed
FROM doctrove_papers;"
```

## Scalability Benefits

### Memory Efficiency
- **Before**: Loaded ALL papers needing 2D projections into memory
- **After**: Processes papers in very large batches (default: 100,000)

### Processing Speed
- **Before**: Rebuilt entire UMAP model for each batch
- **After**: Uses existing model for incremental updates

### Event-Driven Architecture
- **Automatic processing**: New papers trigger enrichment automatically
- **Background monitoring**: Checks for missed papers every minute
- **Batch optimization**: Processes papers in optimal batch sizes

## Batch Sizing Strategy

### Default Settings
- **Incremental batch size**: 100,000 papers
- **Background check interval**: 60 seconds
- **UMAP model**: Shared between title and abstract embeddings

### Adaptive Batch Sizing
The system automatically adjusts batch sizes based on dataset size:
- **Small datasets (<100 papers)**: 50 papers per batch
- **Medium datasets (100-1000 papers)**: 100 papers per batch  
- **Large datasets (>1000 papers)**: 100,000 papers per batch (optimized for scale)

## Troubleshooting

### No UMAP Model Found
If you get "No UMAP model found" error:
```bash
# Run full processing first to create the model
python combined_2d_processor.py --mode full
```

### Memory Issues
If you encounter memory problems:
```bash
# Use smaller batch size
python combined_2d_processor.py --mode incremental --batch-size 10000
```

### Event Listener Not Processing
If the event listener isn't processing new papers:
```bash
# Check if it's running
ps aux | grep event_listener

# Restart if needed
pkill -f event_listener.py
python event_listener.py
```

## Performance Expectations

### Processing Times
- **100 papers**: ~30-60 seconds
- **1000 papers**: ~5-10 minutes
- **100,000 papers**: ~5-15 minutes (with very large batch size)

### Memory Usage
- **Incremental processing**: ~400MB-1GB RAM (with very large batch size)
- **Full processing**: ~1-2GB RAM (depending on dataset size)

### Database Impact
- **Minimal**: Only updates papers that need 2D projections
- **Efficient**: Uses batch updates for better performance

## Best Practices

### 1. **Start with Event Listener**
Always start the event listener before ingesting papers for automatic processing.

### 2. **Monitor Background Processing**
The event listener includes background monitoring that checks for missed papers every minute.

### 3. **Use Appropriate Batch Sizes**
- **Development**: 10,000-50,000 papers per batch
- **Production**: 100,000 papers per batch (default)
- **Large datasets**: 100,000+ papers per batch

### 4. **Regular Full Rebuilds**
Consider running a full rebuild monthly or quarterly to ensure optimal UMAP model quality:
```bash
python combined_2d_processor.py --mode full
```

### 5. **UMAP Environment Reset for New Domains**
When you ingest papers from significantly different semantic domains (e.g., Roman history vs. quantum physics), use the reset script:
```bash
python reset_umap_environment.py --sample-size 5000
```

This performs a complete reset:
- Stops enrichment services
- Clears all 2D embeddings
- Samples papers and trains new UMAP model
- Restarts incremental processing

See `UMAP_RESET_GUIDE.md` for detailed usage instructions.

## Migration from Old System

If you're migrating from the old system:

1. **Backup your data** (optional but recommended)
2. **Start event listener** in a new terminal
3. **Run incremental processing** to catch up any missing 2D projections:
   ```bash
   python combined_2d_processor.py --mode incremental
   ```
4. **Continue with normal operations**

The system will automatically handle new papers going forward. 