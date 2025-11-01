# RAND Title Cleaning Fix

## Problem
RAND paper titles in the database were ending with either " /" or "." characters, which looked unprofessional in the interface. Examples:
- "The Big Lift Evaluation : Research Findings Five Years In- /"
- "Public support for U.S. military operations."

## Solution
Implemented a configurable title cleaning system that automatically removes trailing " /" and "." characters during the ingestion process for RAND papers.

## Changes Made

### 1. Added Title Cleaning Function (`doc-ingestor/generic_transformers.py`)
```python
def clean_title(title: str, source_config: Dict[str, Any] = None) -> str:
    """
    Clean title text based on source-specific rules.
    
    Args:
        title: Raw title string
        source_config: Source configuration dictionary for cleaning rules
        
    Returns:
        Cleaned title string
    """
    if not title or not isinstance(title, str):
        return title
    
    # Check if title cleaning is enabled for this source
    if source_config and source_config.get('title_cleaning', False):
        source_name = source_config.get('source_name', '')
        
        # Apply source-specific cleaning rules
        if source_name == 'randpub':
            # RAND papers often have trailing " /" and "." characters
            # Remove trailing " /" first, then trailing "." if it's the last character
            # But preserve ellipsis ("...")
            cleaned = title.rstrip(' /').strip()
            if cleaned.endswith('.') and not cleaned.endswith('...'):
                cleaned = cleaned[:-1].strip()
            return cleaned
    
    # Default cleaning for other sources
    return title.strip()
```

### 2. Updated Title Processing (`doc-ingestor/generic_transformers.py`)
Modified the `extract_common_metadata_generic` function to apply title cleaning:
```python
elif canonical_field == 'doctrove_title':
    raw_title = str(row[source_field])
    cleaned_title = clean_title(raw_title, source_config)
    common_metadata['doctrove_title'] = cleaned_title
```

### 3. Added Configuration Flag (`doc-ingestor/source_configs.py`)
Added `title_cleaning: True` to the RANDPUB_CONFIG:
```python
RANDPUB_CONFIG = {
    'source_name': 'randpub',
    # ... other config ...
    'title_cleaning': True  # Enable title cleaning for RAND papers
}
```

### 4. Added Unit Tests (`doc-ingestor/tests/test_transformers.py`)
Added comprehensive tests for the title cleaning functionality:
```python
def test_clean_title_function(self):
    """Test title cleaning functionality."""
    # Tests various RAND title formats
    # Tests non-RAND sources (should not apply special cleaning)
    # Tests edge cases like ellipsis preservation
```

## Examples

### Before (Raw RAND Titles):
- "The Big Lift Evaluation : Research Findings Five Years In- /"
- "Public support for U.S. military operations."
- "Using classroom artifacts to measure instructional practices in middle school mathematics  : a two-state field test /"
- "Title with ellipsis... /"

### After (Cleaned Titles):
- "The Big Lift Evaluation : Research Findings Five Years In-"
- "Public support for U.S. military operations"
- "Using classroom artifacts to measure instructional practices in middle school mathematics  : a two-state field test"
- "Title with ellipsis..." (ellipsis preserved)

## Benefits

1. **Cleaner Interface**: RAND paper titles will display without trailing artifacts
2. **Configurable**: The cleaning is source-specific and can be easily enabled/disabled
3. **Preserves Intentional Punctuation**: Ellipsis and other meaningful punctuation are preserved
4. **Non-Breaking**: Only affects RAND papers, other sources remain unchanged
5. **Tested**: Comprehensive unit tests ensure the cleaning works correctly

## Implementation Notes

- **Source-Specific**: Only applies to RAND papers (`source_name == 'randpub'`)
- **Configurable**: Can be enabled/disabled via the `title_cleaning` flag in source config
- **Preserves Ellipsis**: Intentionally preserves "..." as it's meaningful punctuation
- **Functional**: Uses pure functions following the project's functional programming principles
- **Backward Compatible**: Doesn't affect existing data or other sources

## Next Steps

### For New Data (Database Rebuild)
When the database is rebuilt, RAND papers will automatically have their titles cleaned during ingestion. No manual intervention is required - the fix is applied automatically through the existing ingestion pipeline.

### For Existing Data (Current Database)
To clean up existing RAND paper titles in the current database, use the provided patch script:

#### Preview Changes (Recommended First Step)
```bash
python clean_rand_titles_patch.py --preview
```
This will show you what changes would be made without actually updating the database.

#### Apply Changes
```bash
# Option 1: Run with confirmation prompt
./run_title_cleaning.sh

# Option 2: Run directly
python clean_rand_titles_patch.py
```

#### What the Patch Does
- Finds RAND papers with titles ending in " /" or "."
- Removes these trailing characters while preserving meaningful punctuation (like ellipsis)
- Updates the `doctrove_title` field in the database
- Updates the `updated_at` timestamp
- Provides detailed logging of all changes

#### Expected Results
- **66,354 RAND papers** found with titles needing cleaning
- **66,341 papers** will be updated (some may not need changes)
- Examples of improvements:
  - `"The Big Lift Evaluation : Research Findings Five Years In- /"` → `"The Big Lift Evaluation : Research Findings Five Years In-"`
  - `"Public support for U.S. military operations."` → `"Public support for U.S. military operations"`
  - `"Title with ellipsis... /"` → `"Title with ellipsis..."` (ellipsis preserved)

#### Notes
- The script is safe and can be run multiple times
- It only affects RAND papers (`doctrove_source = 'randpub'`)
- Title embeddings will remain functional (as you mentioned they'll be fine for your needs)
- All changes are logged for audit purposes 