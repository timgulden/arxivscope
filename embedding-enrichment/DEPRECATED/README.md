# 🚨 DEPRECATED SCRIPTS

This directory contains scripts that have been **deprecated** and replaced by newer, more efficient implementations.

## ❌ Why These Are Deprecated

All these scripts had one or more of these issues:
- **LLM dependencies** - Required Azure OpenAI API calls
- **Complex logic** - Over-engineered solutions that were hard to maintain
- **Performance issues** - Slow processing due to external API dependencies
- **Inconsistent results** - Results varied based on LLM responses
- **Maintenance burden** - Complex code that was difficult to debug
- **Slow database queries** - Unoptimized queries taking 82+ seconds per batch

## 🔄 What Replaced Them

**Event Listener**: `event_listener_functional.py` - A high-performance functional event listener that:
- ✅ **10x faster processing** - 2,500 papers/minute vs 164 papers/minute
- ✅ **Functional programming** - immutable state, pure functions
- ✅ **Database optimization** - NULL index for fast queries
- ✅ **Batch operations** - efficient database updates
- ✅ **Comprehensive testing** - 21 tests covering all functionality

**Country Enrichment**: `openalex_country_enrichment.py` - A streamlined script that:
- ✅ **Zero LLM calls** - only uses existing OpenAlex data
- ✅ **Fast processing** - ~1000 papers per 1.6 seconds
- ✅ **Deterministic results** - consistent country mapping
- ✅ **Simple structure** - easy to maintain and debug
- ✅ **Laptop compatible** - correct field names and structure

## 📁 Scripts in This Directory

### Event Listener Scripts (Deprecated)
- `event_listener_original.py` - Original slow event listener (82+ seconds per batch)
- `event_listener_fast.py` - Intermediate event listener (still slow)

### Test Scripts (Deprecated)
- `test_simple_country.py` - Old country enrichment tests
- `test_simplified_country.py` - Old country enrichment tests  
- `test_remaining_papers.py` - Old paper processing tests
- `debug_functional.py` - Debug script for functional development

### Core Enrichment Scripts (Deprecated)
- `country_enrichment_service.py` - Had LLM dependencies
- `openalex_country_enrichment.py` - Had LLM fallbacks
- `openalex_country_enrichment_functional.py` - Had LLM dependencies
- `openalex_country_enrichment_pure_functional.py` - Had LLM dependencies
- `openalex_country_enrichment_institution_cache.py` - Had LLM dependencies
- `country_enrichment_main.py` - Complex interceptor pattern with LLM

### Runner Scripts (Deprecated)
- `run_unique_institution_enrichment.py` - Had LLM dependencies
- `run_institution_cached_enrichment.py` - Had LLM dependencies
- `run_openalex_country_enrichment.py` - Had LLM dependencies
- `run_optimized_country_enrichment.py` - Had LLM dependencies

### Test Scripts (Deprecated)
- `test_openalex_country_enrichment.py` - Tests for obsolete scripts
- `test_functional_enrichment.py` - Tests for obsolete functional approach
- `test_batched_llm.py` - Tests for LLM functionality
- `test_real_country_data.py` - Tests for obsolete scripts

## 🚀 Current Recommendation

**Use `openalex_country_enrichment.py`** for all OpenAlex country enrichment needs. It's faster, more reliable, and easier to maintain than any of the deprecated scripts.

## 📚 Documentation

See the main `README_ENRICHMENT_SCRIPTS.md` for current usage instructions and examples.
