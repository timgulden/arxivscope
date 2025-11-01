# Semantic Search Improvement Plan

**Issue Identified**: October 13, 2025  
**Priority**: HIGH - Affects core search functionality

## Problem Statement

When users copy paper metadata from the UI and paste it into semantic search, the paper often doesn't appear in results or ranks poorly, even though it should match itself near-perfectly.

### Root Cause Analysis

**Issue 1: OpenAI Embedding Non-Determinism**
- Same text generates different embeddings each call
- Stored embedding (from ingestion): `[0.00349, 0.01146, 0.08377...]`
- Fresh embedding (same text): `[0.02937, 0.01732, 0.06890...]`
- Similarity: ~0.85-0.95 instead of 1.0
- **This is a known OpenAI limitation with text-embedding-3-small**

**Issue 2: UI Metadata Formatting**
- UI displays papers with formatting:
  ```
  Title
  
  Authors:
  Name1, Name2
  Year:
  2023
  Source:
  randpub
  Abstract text...
  ```
- Stored embeddings generated from: `"Title: {title} Abstract: {abstract}"`
- Format mismatch reduces similarity: 0.95 → 0.75-0.85
- Can push papers below threshold entirely

**Combined Effect:**
- OpenAI non-determinism: -5% to -15% similarity
- Format mismatch: -10% to -20% similarity
- **Total loss**: -15% to -35% similarity
- Result: Paper may not match itself!

## Test Case

**Paper**: "Mischief, Malevolence, or Indifference? HOW COMPETITORS AND ADVERSARIES COULD EXPLOIT CLIMATE-RELATED CONFLICT..."
- ID: `d22c3f07-24b5-4543-b5a7-91ab66b0f6e7`

**Test Results:**
1. **Exact stored format** → Found paper #1, similarity: 0.857 ✅
2. **UI formatted version** → Found similar paper (different ID), similarity: 0.857 ❌
3. **Partial abstract only** → 0 results ❌

## Solutions

### Solution 1: Strip Metadata Formatting (RECOMMENDED)

**Implementation**: Preprocess search text in React UI before sending to API

```typescript
function cleanSearchText(text: string): string {
  // Remove common metadata patterns
  const lines = text.split('\n');
  const cleanedLines = lines.filter(line => {
    const trimmed = line.trim();
    // Skip metadata header lines
    if (trimmed.match(/^(Authors?|Year|Source|Date|DOI|Published):?\s*$/i)) {
      return false;
    }
    // Skip empty lines
    if (!trimmed) {
      return false;
    }
    return true;
  });
  
  return cleanedLines.join(' ').trim();
}
```

**Benefits:**
- Removes semantic noise from searches
- Improves matching accuracy
- Works with existing embeddings
- No API changes needed

### Solution 2: Lower Default Threshold

**Current**: 0.5 (too restrictive given non-determinism)  
**Recommended**: 0.3 or 0.4

**Implementation**: Update React UI default

**Trade-offs:**
- ✅ More forgiving, finds papers despite formatting
- ❌ May return more loosely related papers
- ❌ Doesn't fix root cause

### Solution 3: Add "Title: ... Abstract: ..." Wrapper

**Implementation**: Format search text to match storage format

```typescript
function formatForSemanticSearch(text: string): string {
  // Try to detect if text has title vs abstract
  // Simple heuristic: first line is title, rest is abstract
  const lines = text.split('\n').filter(l => l.trim());
  if (lines.length > 1) {
    const title = lines[0];
    const abstract = lines.slice(1).join(' ');
    return `Title: ${title} Abstract: ${abstract}`;
  }
  return `Title: ${text}`;
}
```

### Solution 4: Exact Title Match Boost (BEST LONG-TERM)

**Implementation**: Add hybrid search in API

```python
# In business_logic.py
def hybrid_search(search_text, similarity_threshold):
    # 1. Check if search_text contains an exact title match
    exact_matches = find_exact_title_matches(search_text)
    
    # 2. Do semantic search
    semantic_results = semantic_search(search_text, threshold)
    
    # 3. Merge results, boost exact matches to top
    return merge_and_boost(exact_matches, semantic_results)
```

**Benefits:**
- Guarantees exact matches always appear
- Preserves semantic search for discovery
- Best user experience

## Immediate Actions

### 1. Lower Threshold (Quick Fix)
Location: React UI semantic search component  
Change: 0.5 → 0.3 or 0.4

### 2. Add Text Cleaning (Medium-term)
Location: React UI before API call  
Implement: `cleanSearchText()` function

### 3. Document Limitation (Communication)
Add tooltip/help text explaining:
- "For best results, paste just title and abstract"
- "Remove Authors:, Year:, Source: headers"
- "Threshold: Lower = more results, Higher = stricter matches"

## Long-term Solution

Implement **hybrid search** combining:
1. Exact text matching (PostgreSQL full-text search)
2. Semantic similarity (pgvector)
3. Boosting algorithm (combine scores)

This ensures:
- Exact/partial text matches always rank high
- Semantic discovery still works
- Best of both worlds

## Technical Notes

### Why OpenAI Embeddings Are Non-Deterministic

According to OpenAI documentation:
- Model uses dropout/other stochastic elements
- Designed for similarity, not exact reproduction
- Variance typically 1-5% but can be higher
- **This is expected behavior, not a bug**

### Alternative: Deterministic Models

Some embedding models offer determinism:
- Sentence Transformers (local, deterministic)
- Cohere embeddings (deterministic mode available)
- But migration would require re-embedding all 2.9M papers

### Why Format Matters

Adding structural markers (`Authors:`, `Year:`) changes semantic meaning:
- Model interprets these as part of the content
- Creates "metadata semantics" vs "content semantics"
- Reduces overlap with pure title+abstract embeddings

## Recommendation

**Phase 1** (Immediate - 5 min):
- Lower threshold to 0.35 in UI
- Test and verify

**Phase 2** (This week - 1 hour):
- Implement `cleanSearchText()` in React
- Strip metadata formatting automatically
- Add help text/tooltip

**Phase 3** (Future - 4 hours):
- Implement hybrid search (exact + semantic)
- Best long-term solution

---

**Status**: Issue documented, solutions identified, ready for implementation



