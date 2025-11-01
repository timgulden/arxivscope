# 🚀 ENRICHMENT SCRIPT SELECTION GUIDE

## ✅ USE THIS SCRIPT (Recommended)
**`openalex_country_enrichment.py`**
- **Strategy**: Extract country codes directly from OpenAlex metadata
- **Efficiency**: Zero LLM calls, only processes papers with existing country data
- **Use case**: Production runs of any size, fast and reliable
- **Performance**: ~1000 papers per 1.6 seconds, ~38-42% success rate
- **Table structure**: Simplified `openalex_enrichment_country` with laptop-compatible fields

## 🚨 DEPRECATED SCRIPTS (Moved to DEPRECATED/ directory)
**All previous OpenAlex country enrichment scripts have been deprecated:**
- **`country_enrichment_service.py`** - Had LLM dependencies
- **`openalex_country_enrichment_functional.py`** - Had LLM dependencies  
- **`country_enrichment_main.py`** - Complex interceptor pattern with LLM
- **`run_unique_institution_enrichment.py`** - Had LLM dependencies
- **And others...** - All moved to `DEPRECATED/` directory

## 🎯 Why the Streamlined Approach is Better

### Before (LLM-dependent):
- Required Azure OpenAI API calls
- Complex institution caching logic
- Slow processing due to API dependencies
- Inconsistent results based on LLM responses

### After (Streamlined):
- **Zero LLM calls** - only uses existing OpenAlex data
- **Direct country code extraction** from metadata
- **Fast processing** - no external API dependencies
- **Consistent results** - deterministic country mapping
- **Laptop compatibility** - correct field names and structure

## 🚀 Quick Start
```bash
# Check status
python3 openalex_country_enrichment.py --status

# Test with small batch
python3 openalex_country_enrichment.py --limit 1000

# Full production run
python3 openalex_country_enrichment.py

# Custom batch size
python3 openalex_country_enrichment.py --batch-size 500
```

## 📊 Current Status
- **Total OpenAlex papers**: 17.8M+
- **Papers with country data**: ~38-42% (estimated 6.8M+)
- **Processing speed**: ~1000 papers per 1.6 seconds
- **Expected runtime**: 8-10 hours for full dataset

## 🔧 Table Structure
The script creates a simplified `openalex_enrichment_country` table:
```sql
CREATE TABLE openalex_enrichment_country (
    doctrove_paper_id UUID PRIMARY KEY,
    openalex_country_country TEXT,      -- Full country name (e.g., "United States")
    openalex_country_uschina TEXT       -- US/China/Rest of World coding
);
```

## 📝 Field Values
- **`openalex_country_country`**: Full country names (e.g., "United States", "China", "Germany")
- **`openalex_country_uschina`**: 
  - "United States" for US institutions
  - "China" for Chinese institutions  
  - "Rest of the World" for all other countries
  - "Unknown" for papers without country data

## 🎉 Benefits
- **Fast**: No LLM API calls or complex processing
- **Reliable**: Deterministic results from existing data
- **Compatible**: Correct field names for laptop integration
- **Efficient**: Batch processing with minimal database overhead
- **Clean**: Simple, maintainable code structure
