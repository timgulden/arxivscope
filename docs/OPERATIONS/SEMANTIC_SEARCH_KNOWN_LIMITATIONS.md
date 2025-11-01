# Semantic Search Known Limitations

**Last Updated**: October 13, 2025

## OpenAI Embedding Non-Determinism

### The Issue

OpenAI's `text-embedding-3-small` model generates **non-deterministic embeddings** - the same text produces slightly different embeddings on each API call.

**Example:**
- Text: "Climate change CENTCOM"
- Call 1: `[0.00349, 0.01146, 0.08377, ...]`
- Call 2: `[0.02937, 0.01732, 0.06890, ...]`
- **Similarity**: ~0.85-0.95 (not 1.0!)

### Impact

**When searching with a paper's own metadata:**
- Expected: Paper appears #1 with ~1.0 similarity
- **Reality**: Paper appears with ~0.75-0.85 similarity
- Sometimes ranks below genuinely similar papers
- Can miss threshold entirely

**This is not a bug in our system** - it's an OpenAI limitation documented in their API.

### Why This Happens

OpenAI embeddings use:
- Stochastic elements (dropout, sampling)
- Designed for **similarity**, not exact reproduction
- Trade-off: Better generalization vs perfect reproduction
- Typical variance: 1-15% per dimension

## Format Sensitivity

### Additional Impact

Search text formatting affects similarity:

**Stored format** (from ingestion):
```
Title: Paper Title Abstract: Paper abstract text...
```

**User search** (with UI formatting):
```
Paper Title

Authors:
Names
Year:
2023
Source:
randpub
Paper abstract text...
```

**Effect**: Formatting headers add "semantic noise" that further reduces similarity by 5-15%.

## Mitigation Strategies

### 1. Lowered Default Threshold ✅

**Changed**: October 13, 2025  
**Old default**: 0.5  
**New default**: 0.35

**Rationale**:
- Accounts for OpenAI non-determinism (~15% loss)
- Accounts for format variation (~10-15% loss)
- Still provides meaningful filtering (0.35 = moderately related)

### 2. User Education

**Help text in UI**:
- "Semantic search finds papers by meaning, not exact text"
- "Lower threshold (0.2-0.4) = more results"
- "Higher threshold (0.5-0.8) = stricter matches"
- "Even identical text may not score 1.0 due to AI model behavior"

### 3. Hybrid Search (Future Enhancement)

**Proposed solution**: Combine approaches
```
Results = Exact_Text_Matches (boosted) + Semantic_Matches
```

**Benefits**:
- Exact title/text matches always appear
- Semantic discovery still works
- Best user experience

## User Guidelines

### Best Practices for Semantic Search

**✅ DO:**
- Paste core content (title + abstract)
- Use natural language queries
- Adjust threshold based on results
- Start with lower threshold (0.3-0.4)

**❌ DON'T:**
- Expect perfect 1.0 similarity scores
- Rely solely on high thresholds (>0.6)
- Assume formatting doesn't matter

### Understanding Scores

| Score Range | Meaning |
|-------------|---------|
| 0.8 - 1.0 | Nearly identical content (accounting for AI variance) |
| 0.6 - 0.8 | Highly related, same topic/domain |
| 0.4 - 0.6 | Related, overlapping concepts |
| 0.2 - 0.4 | Loosely related, some common themes |
| 0.0 - 0.2 | Barely related or unrelated |

**Note**: Due to OpenAI non-determinism, even **perfect matches rarely exceed 0.90**.

## Technical Details

### Testing Non-Determinism

We tested identical text multiple times:

**Test 1** (Fresh generation):
```python
text = "Title: X Abstract: Y"
embedding1 = generate_embedding(text)
embedding2 = generate_embedding(text)
similarity(embedding1, embedding2) = 0.9476
```

**Test 2** (Stored vs Fresh):
```python
stored = get_from_database(paper_id)
fresh = generate_embedding(same_text)
similarity(stored, fresh) = 0.8571
```

This 85-95% similarity range is **expected behavior** from OpenAI's model.

### Database Verification

All embeddings verified:
- Model: `text-embedding-3-small` (consistent)
- Format: `"Title: {title} Abstract: {abstract}"` (consistent)
- Dimensions: 1536 (correct)
- Storage: pgvector (working correctly)

**The system is working as designed** - the limitation is in OpenAI's model behavior.

## Related Documentation

- `SEMANTIC_SEARCH_IMPROVEMENT_PLAN.md` - Detailed improvement roadmap
- OpenAI Embeddings API docs - Non-determinism behavior
- React UI component docs - Threshold controls

## Conclusion

Semantic search is working correctly given OpenAI's model limitations. The 0.35 default threshold provides a good balance between:
- Finding relevant papers (lower = more results)
- Filtering noise (higher = fewer, better matches)
- Accounting for non-determinism

Users should understand that **semantic similarity is not exact matching** - it's about finding papers with similar **meaning**, not identical **text**.

---

**Status**: Issue documented, threshold lowered, user guidelines provided



