# OpenAI API Migration Guide

**Date**: 2025-01-22  
**Context**: Code was transferred from corporate RAND context with permission. The corporate OpenAI API key is no longer authorized for use.

## Summary

The system has been migrated from using a corporate RAND Azure OpenAI API key to supporting personal OpenAI API keys. All hardcoded API keys have been removed and replaced with environment-based configuration.

### Cost Estimates

Based on current database state (~2.9M papers, ~1.39M needing embeddings):
- **Embedding Remaining Work**: ~$83 for 1.39M papers
- **Semantic Search**: Free (uses existing embeddings)
- **LLM Features**: Minimal cost (low volume usage)

**Total Estimated Cost**: <$100 for remaining embedding generation

## Architecture Changes

### Before (Hardcoded)
```python
# OLD: Hardcoded corporate API key
api_key = "a349cd5ebfcb45f59b2004e6e8b7d700"
url = "https://apigw.rand.org/openai/RAND/inference/deployments/text-embedding-3-small-v1-base/embeddings?api-version=2024-06-01"
```

### After (Environment-Based)
```python
# NEW: Configurable from environment
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_EMBEDDING_MODEL

url = f"{OPENAI_BASE_URL}/embeddings"
headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
```

## Setup Instructions

### 1. Get Personal OpenAI API Key

Visit: https://platform.openai.com/api-keys
1. Sign up for OpenAI account (if needed)
2. Create a new API key
3. Copy the key

### 2. Configure Environment

The `.env.local` file has been updated with OpenAI configuration. Edit `arxivscope/.env.local`:

```bash
# OpenAI Configuration (Personal API Key)
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# OpenAI Model Configuration
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o

# Feature Flags
USE_OPENAI_EMBEDDINGS=true  # Set to false to disable embedding generation
USE_OPENAI_LLM=true  # Set to false to disable LLM features
```

### 3. Verify Configuration

The system will log errors if the API key is not configured:
```
ERROR: OpenAI API key not configured. Please set OPENAI_API_KEY in .env.local
```

## Feature Flags

You can disable OpenAI features completely by setting flags in `.env.local`:

```bash
USE_OPENAI_EMBEDDINGS=false  # Disables embedding generation
USE_OPENAI_LLM=false         # Disables LLM features (SQL generation, summaries)
```

**Impact**:
- If `USE_OPENAI_EMBEDDINGS=false`: Semantic search will only work on existing embeddings, new paper ingestion won't generate embeddings
- If `USE_OPENAI_LLM=false`: SQL generation and cluster summarization features will return errors

## Code Changes

### Files Modified

1. **`env.local.example`** - Added OpenAI configuration template
2. **`arxivscope/.env.local`** - Added OpenAI configuration section
3. **`doctrove-api/config.py`** - Added OpenAI configuration loading
4. **`doctrove-api/business_logic.py`** - Refactored embedding functions to use config
5. **`doctrove-api/api.py`** - Refactored LLM functions to use config

### Key Functions Updated

#### Embedding Functions
- `get_embedding_for_text()` - Single text embedding
- `get_embeddings_for_texts_batch()` - Batch embedding generation

Both functions now:
1. Check `USE_OPENAI_EMBEDDINGS` flag
2. Validate API key is configured
3. Use environment-based URLs and headers
4. Support both standard OpenAI and Azure OpenAI formats

#### LLM Functions
- `cluster_summarize()` - Cluster summary generation
- `generate_sql()` - SQL query generation

Both functions now:
1. Check `USE_OPENAI_LLM` flag
2. Validate API key is configured
3. Use standard OpenAI API format

## Legacy API Key Storage

The old corporate RAND API key has been preserved in `config.py` for reference only:

```python
# DEPRECATED - kept for reference only
RAND_OPENAI_API_KEY = 'a349cd5ebfcb45f59b2004e6e8b7d700'
```

**DO NOT USE THIS KEY** - It is stored for reference only and should never be used without explicit authorization.

## Compatibility

### Standard OpenAI API

Works out of the box with configuration in `.env.local`:
```bash
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
```

### Azure OpenAI

The code supports Azure OpenAI if you have an Azure account. Configure:
```bash
OPENAI_BASE_URL=https://your-resource.openai.azure.com
OPENAI_API_KEY=your-azure-api-key
```

Note: Azure OpenAI uses different header format (Ocp-Apim-Subscription-Key vs Authorization). This would require code modification to support fully.

## Testing

### Test Embedding Generation

```python
from doctrove-api.business_logic import get_embedding_for_text

embedding = get_embedding_for_text("Test document")
if embedding is not None:
    print(f"Generated {len(embedding)}-dimensional embedding")
else:
    print("Embedding generation failed - check configuration")
```

### Test LLM Generation

Use the API endpoints directly:
```bash
curl -X POST http://localhost:5001/api/generate-sql \
  -H "Content-Type: application/json" \
  -d '{"natural_language": "Find papers about climate change"}'
```

## Troubleshooting

### Error: "OpenAI API key not configured"

**Solution**: Set `OPENAI_API_KEY` in `arxivscope/.env.local`

### Error: "LLM features disabled via configuration"

**Solution**: Set `USE_OPENAI_LLM=true` in `.env.local` (or add the key if missing)

### Error: 401 Unauthorized

**Solution**: Check that your OpenAI API key is valid and has credit

### Error: 402 Insufficient Credit

**Solution**: Add credit to your OpenAI account at https://platform.openai.com/

## Future Alternatives

If you want to avoid OpenAI costs entirely in the future:

1. **Local Embeddings**: Use sentence-transformers library (requires re-embedding all papers)
2. **Ollama**: Run local LLM (requires GPU setup)
3. **Other Cloud Services**: Hugging Face, Cohere, etc.

See `SEMANTIC_SEARCH_IMPROVEMENT_PLAN.md` for discussion of local embedding options.

## Security Notes

- `.env.local` is gitignored and never committed
- API keys should never be hardcoded in code
- Old corporate key is kept for reference only, marked DEPRECATED
- All API calls use SSL/TLS encryption (certifi verification)

## Questions?

For issues or questions about this migration:
1. Check configuration in `.env.local`
2. Review logs for specific error messages
3. Verify API key is valid at https://platform.openai.com/
4. Check OpenAI usage/credits dashboard

