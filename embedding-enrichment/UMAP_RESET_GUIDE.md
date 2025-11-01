# UMAP Environment Reset Guide

## Overview

The UMAP environment reset script (`reset_umap_environment.py`) is designed to handle the scenario where you've ingested papers from significantly different semantic domains that don't map well into the existing UMAP space.

## When to Use This Script

### **Semantic Domain Mismatches**
Use this script when you've ingested papers from domains that are fundamentally different from your existing data:

- **Historical vs. Scientific**: Roman history papers vs. quantum physics papers
- **Different Academic Fields**: Literature vs. Computer Science vs. Medicine
- **Different Time Periods**: Ancient texts vs. modern research
- **Different Languages**: Papers in different languages with different semantic structures
- **Different Research Types**: Theoretical vs. experimental vs. review papers

### **Signs You Need a Reset**
- **Poor clustering**: Papers from the same domain are scattered across the visualization
- **Inconsistent connections**: Title-abstract connections don't make semantic sense
- **Poor search results**: Similar papers aren't grouped together
- **Visual confusion**: The 2D space doesn't reflect the expected semantic relationships

## How It Works

### **Complete Reset Process**
```
1. Stop Services → 2. Clear Data → 3. Sample Papers → 4. Train New Model → 5. Restart Processing
```

### **Step-by-Step Breakdown**

#### **Step 1: Stop Enrichment Services**
- Automatically finds and stops any running `event_listener.py` processes
- Ensures no new 2D embeddings are generated during the reset
- Waits for services to shut down gracefully

#### **Step 2: Clear 2D Embeddings**
- Removes all existing `doctrove_embedding_2d` values
- Clears associated metadata and timestamps
- Provides count of cleared embeddings for verification

#### **Step 3: Sample Papers**
- Takes a random sample of papers that have both title and abstract embeddings
- Production mode: Always uses 100,000 papers (or all available if less)
- Testing mode: Configurable sample size via --sample-size flag
- Ensures the new UMAP model captures the full semantic diversity

#### **Step 4: Train New UMAP Model**
- Trains a fresh UMAP model on the sampled embeddings
- Uses combined title + abstract embeddings for consistency
- Saves the new model with both model and scaler

#### **Step 5: Generate Sample 2D Embeddings**
- Uses the new model to generate 2D embeddings for the sample papers
- Saves these to the database as the new baseline

#### **Step 6: Restart Incremental Processing**
- Starts the event listener service
- Begins incremental processing of remaining papers
- Uses the new UMAP model for all future embeddings

## Usage

### **Production Usage (Recommended)**
```bash
cd embedding-enrichment
python reset_umap_environment.py
```
This will automatically use 100,000 papers (or all available if less) for optimal UMAP model quality.

### **Testing Usage**
```bash
# Use 2,000 papers for testing (faster processing)
python reset_umap_environment.py --sample-size 2000

# Use 10,000 papers for testing (medium quality)
python reset_umap_environment.py --sample-size 10000
```

### **Dry Run (Preview)**
```bash
# See what would be done without making changes
python reset_umap_environment.py --dry-run
```

### **Custom Model Path**
```bash
# Save model to a different location
python reset_umap_environment.py --model-path /path/to/custom_model.pkl
```

## Sample Size Guidelines

### **Production Sample Sizes**

| Dataset Size | Sample Size | Rationale |
|--------------|-------------|-----------|
| < 100,000 papers | All papers | Use all available papers for maximum quality |
| ≥ 100,000 papers | 100,000 papers | Optimal balance of quality and performance |

### **Testing Sample Sizes**

| Purpose | Sample Size | Use Case |
|---------|-------------|----------|
| Quick test | 1,000-2,000 | Verify system works |
| Medium test | 5,000-10,000 | Test with reasonable quality |
| Full test | 50,000+ | Test with production-like quality |

### **Factors to Consider**
- **Semantic Diversity**: More diverse domains need larger samples
- **Computational Resources**: Larger samples take more time and memory
- **Quality vs. Speed**: Larger samples = better model quality but longer training

## Example Scenarios

### **Scenario 1: Adding Roman History Papers**
```bash
# You have 50,000 physics papers and are adding 5,000 Roman history papers
# This is a major semantic shift - use reset

python reset_umap_environment.py --sample-size 8000
```

### **Scenario 2: Adding More Physics Papers**
```bash
# You have 50,000 physics papers and are adding 10,000 more physics papers
# This is the same domain - no reset needed, just incremental processing
```

### **Scenario 3: Mixed Domain Addition**
```bash
# You have 30,000 papers across multiple domains and are adding 20,000 papers
# from 5 new domains - this needs a reset

python reset_umap_environment.py --sample-size 10000
```

## Before Running the Reset

### **1. Backup Your Data (Optional)**
```bash
# Backup the current UMAP model
cp umap_model.pkl umap_model.pkl.backup

# Backup database (if you have pg_dump access)
pg_dump -U tgulden -d doctrove -t doctrove_papers > papers_backup.sql
```

### **2. Check Current State**
```bash
# See how many papers have 2D embeddings
psql -U tgulden -d doctrove -h localhost -c "
SELECT 
    COUNT(*) as total_papers,
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_title_2d
FROM doctrove_papers;"
```

### **3. Dry Run First**
```bash
python reset_umap_environment.py --dry-run
```

## After Running the Reset

### **1. Verify the Reset**
```bash
# Check that 2D embeddings were cleared
psql -U tgulden -d doctrove -h localhost -c "
SELECT 
    COUNT(*) FILTER (WHERE doctrove_embedding_2d IS NOT NULL) as with_title_2d
FROM doctrove_papers;"
```

### **2. Monitor Incremental Processing**
```bash
# Check if event listener is running
ps aux | grep event_listener

# Monitor progress
tail -f enrichment.log
```

### **3. Test the Visualization**
- Open the DocScope frontend
- Verify that papers are clustering appropriately
- Check that title-abstract connections make sense

## Troubleshooting

### **Services Won't Stop**
If the script can't stop running services:
```bash
# Manually stop event listener
pkill -f event_listener.py

# Then run the reset
python reset_umap_environment.py
```

### **Not Enough Papers for Sampling**
If you get "No papers found with embeddings":
```bash
# Check how many papers have embeddings
psql -U tgulden -d doctrove -h localhost -c "
SELECT 
    COUNT(*) FILTER (WHERE doctrove_embedding IS NOT NULL) as with_embeddings
FROM doctrove_papers;"
```

### **Memory Issues During Training**
If you get memory errors:
```bash
# Use smaller sample size
python reset_umap_environment.py --sample-size 2000
```

### **Event Listener Won't Start**
If incremental processing fails to start:
```bash
# Start manually
python event_listener.py
```

## Performance Expectations

### **Processing Times**
- **5,000 papers**: ~10-20 minutes total
- **10,000 papers**: ~20-40 minutes total
- **20,000 papers**: ~40-80 minutes total

### **Memory Usage**
- **Sample processing**: ~1-2GB RAM
- **UMAP training**: ~2-4GB RAM
- **Incremental processing**: ~200-500MB RAM

### **Storage Impact**
- **Model file**: ~50-100MB
- **Database**: Minimal (just clearing and updating 2D embeddings)

## Best Practices

### **1. Plan Your Resets**
- Don't reset too frequently (monthly or quarterly is usually sufficient)
- Reset when adding papers from fundamentally different domains
- Consider the computational cost vs. quality improvement

### **2. Monitor Quality**
- After each reset, verify that clustering makes sense
- Check that similar papers are grouped together
- Ensure title-abstract connections are meaningful

### **3. Document Your Resets**
- Keep a log of when and why you performed resets
- Note the sample sizes used and results achieved
- This helps optimize future resets

### **4. Coordinate with Team**
- Resets affect all users of the system
- Coordinate with team members before running resets
- Consider running resets during low-usage periods

## Integration with Workflow

### **Typical Workflow**
1. **Ingest new papers** from different semantic domains
2. **Generate embeddings** (automatic via event listener)
3. **Evaluate clustering quality** in visualization
4. **If quality is poor**, run UMAP reset
5. **Monitor incremental processing** to completion
6. **Verify improved clustering** quality

This reset capability ensures your system can handle diverse academic content while maintaining high-quality semantic clustering. 