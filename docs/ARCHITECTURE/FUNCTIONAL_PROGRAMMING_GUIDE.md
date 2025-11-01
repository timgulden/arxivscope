# Functional Programming Guide

## Overview

This guide covers the functional programming improvements made to the DocScope/DocTrove codebase, focusing on replacing `for` loops with functional alternatives like `map`, `filter`, and `reduce`.

## Why Functional Programming?

### **1. Immutability & Purity**
- **Pure functions**: Same input always produces same output
- **No side effects**: Functions don't modify external state
- **Easier testing**: Test the function, not the loop logic

### **2. Composability**
- **Chain operations**: `map(f).filter(g).reduce(h)`
- **Reusable functions**: Small, focused functions that can be combined
- **Declarative code**: Describe what you want, not how to do it

### **3. Performance Benefits**
- **Lazy evaluation**: Operations only execute when needed
- **Parallel processing**: Functional operations can be parallelized
- **Memory efficiency**: No intermediate mutable state

## Key Functional Programming Concepts

### **Map**
Transform each element in a collection:
```python
# Before (imperative)
results = []
for item in items:
    results.append(transform(item))

# After (functional)
results = list(map(transform, items))
```

### **Filter**
Select elements that meet a condition:
```python
# Before (imperative)
valid_items = []
for item in items:
    if is_valid(item):
        valid_items.append(item)

# After (functional)
valid_items = list(filter(is_valid, items))
```

### **Reduce**
Combine elements into a single result:
```python
# Before (imperative)
total = 0
for item in items:
    total += item

# After (functional)
from functools import reduce
total = reduce(lambda x, y: x + y, items, 0)
```

## Refactored Examples

### **1. Paper Transformation (Before)**
```python
def transform_json_to_papers(json_data, source_config):
    common_papers = []
    source_metadata_list = []
    
    for row in json_data:
        paper_id = id_generator()
        common_metadata, source_metadata = map_row_to_papers_generic(row, paper_id, source_config, current_date)
        
        # Validate before adding
        common_error = validate_common_metadata_generic(common_metadata)
        source_error = validate_source_metadata_generic(source_metadata)
        
        if common_error:
            print(f"Warning: Skipping paper due to validation error: {common_error}")
            continue
        
        if source_error:
            print(f"Warning: Skipping paper due to source validation error: {source_error}")
            continue
        
        common_papers.append(common_metadata)
        source_metadata_list.append(source_metadata)
    
    return common_papers, source_metadata_list
```

### **1. Paper Transformation (After)**
```python
def transform_json_to_papers(json_data, source_config):
    # Step 1: Map each row to paper data with validation
    def process_row(row):
        """Process a single row and return paper data if valid, None if invalid"""
        paper_id = id_generator()
        common_metadata, source_metadata = map_row_to_papers_generic(row, paper_id, source_config, current_date)
        
        # Validate before adding
        common_error = validate_common_metadata_generic(common_metadata)
        source_error = validate_source_metadata_generic(source_metadata)
        
        if common_error:
            print(f"Warning: Skipping paper due to validation error: {common_error}")
            return None
        
        if source_error:
            print(f"Warning: Skipping paper due to source validation error: {source_error}")
            return None
        
        return (common_metadata, source_metadata)
    
    # Step 2: Map all rows and filter out None results
    processed_results = list(filter(None, map(process_row, json_data)))
    
    # Step 3: Unzip the results into separate lists
    if processed_results:
        common_papers, source_metadata_list = zip(*processed_results)
        return list(common_papers), list(source_metadata_list)
    else:
        return [], []
```

### **2. Paper Filtering (Before)**
```python
def filter_valid_papers_generic(papers):
    valid_papers = []
    
    for paper in papers:
        error = validate_common_metadata_generic(paper)
        if error is None:
            valid_papers.append(paper)
        else:
            print(f"Warning: Skipping invalid paper: {error}")
    
    return valid_papers
```

### **2. Paper Filtering (After)**
```python
def filter_valid_papers_generic(papers):
    def is_valid_paper(paper):
        """Check if a paper is valid"""
        error = validate_common_metadata_generic(paper)
        if error is not None:
            print(f"Warning: Skipping invalid paper: {error}")
            return False
        return True
    
    return list(filter(is_valid_paper, papers))
```

### **3. Paper Counting (Before)**
```python
def count_papers_by_source_generic(papers):
    counts = {}
    for paper in papers:
        source = paper.get('doctrove_source', 'unknown')
        counts[source] = counts.get(source, 0) + 1
    return counts
```

### **3. Paper Counting (After)**
```python
def count_papers_by_source_generic(papers):
    from collections import Counter
    
    # Extract sources from papers
    sources = map(lambda paper: paper.get('doctrove_source', 'unknown'), papers)
    
    # Count occurrences using Counter
    return dict(Counter(sources))
```

## Testing Benefits

### **Before: Testing Loops**
```python
def test_transform_json_to_papers():
    # Need to test the entire loop logic
    json_data = [{"title": "Test", "id": "1"}]
    result = transform_json_to_papers(json_data, config)
    
    # Test the whole transformation
    assert len(result[0]) == 1
    assert result[0][0]['doctrove_title'] == "Test"
```

### **After: Testing Pure Functions**
```python
def test_process_row():
    # Test the pure function in isolation
    row = {"title": "Test", "id": "1"}
    result = process_row(row)
    
    # Test just the transformation logic
    assert result is not None
    assert result[0]['doctrove_title'] == "Test"

def test_transform_json_to_papers():
    # Test the composition of functions
    json_data = [{"title": "Test", "id": "1"}]
    result = transform_json_to_papers(json_data, config)
    
    # Test the overall result
    assert len(result[0]) == 1
```

## Performance Improvements

### **Lazy Evaluation**
```python
# Only processes items when needed
def process_large_dataset(items):
    # This doesn't actually process anything yet
    transformed = map(transform, items)
    filtered = filter(is_valid, transformed)
    
    # Only now does the processing happen
    return list(filtered)
```

### **Memory Efficiency**
```python
# No intermediate lists created
def count_valid_papers(papers):
    # No temporary list of valid papers
    return len(list(filter(is_valid, papers)))
```

## Best Practices

### **1. Use Pure Functions**
```python
# Good: Pure function
def calculate_score(paper):
    return paper.get('citations', 0) * 0.1

# Bad: Function with side effects
def calculate_score(paper):
    global total_score
    score = paper.get('citations', 0) * 0.1
    total_score += score  # Side effect!
    return score
```

### **2. Compose Functions**
```python
# Good: Function composition
def process_papers(papers):
    return list(
        filter(is_valid,
            map(transform,
                filter(has_required_fields, papers)
            )
        )
    )

# Bad: Nested loops
def process_papers(papers):
    results = []
    for paper in papers:
        if has_required_fields(paper):
            transformed = transform(paper)
            if is_valid(transformed):
                results.append(transformed)
    return results
```

### **3. Use Built-in Functions**
```python
# Good: Use built-in functional tools
from collections import Counter
from functools import reduce

# Bad: Reimplement functionality
def count_items(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts
```

## Common Patterns

### **1. Map-Filter-Reduce Pipeline**
```python
def process_data(data):
    # Map: Transform data
    transformed = map(transform, data)
    
    # Filter: Remove invalid items
    valid = filter(is_valid, transformed)
    
    # Reduce: Combine results
    result = reduce(combine, valid, initial_value)
    
    return result
```

### **2. Error Handling with Optional**
```python
def process_with_errors(data):
    def safe_process(item):
        try:
            return process(item)
        except Exception as e:
            logger.error(f"Error processing {item}: {e}")
            return None
    
    # Filter out None results
    return list(filter(None, map(safe_process, data)))
```

### **3. Conditional Processing**
```python
def conditional_process(data, condition):
    def process_if_condition(item):
        if condition(item):
            return process(item)
        return item
    
    return list(map(process_if_condition, data))
```

## Migration Strategy

### **1. Identify Loops**
Look for patterns like:
- `for item in items:`
- `results.append(...)`
- `if condition: continue`

### **2. Extract Pure Functions**
```python
# Before
for item in items:
    if is_valid(item):
        result = transform(item)
        results.append(result)

# After
def process_item(item):
    if is_valid(item):
        return transform(item)
    return None

results = list(filter(None, map(process_item, items)))
```

### **3. Test Incrementally**
- Test the pure function in isolation
- Test the composition of functions
- Ensure the overall behavior is the same

## Tools and Libraries

### **Python Built-ins**
- `map()`: Transform elements
- `filter()`: Select elements
- `reduce()`: Combine elements
- `zip()`: Combine iterables

### **Collections Module**
- `Counter`: Count occurrences
- `defaultdict`: Default values for dicts

### **Functools Module**
- `reduce()`: Functional reduce
- `partial()`: Partial function application

### **Third-party Libraries**
- `itertools`: Advanced iteration tools
- `toolz`: Functional programming utilities
- `fn.py`: Functional programming for Python

## Conclusion

Functional programming makes code:
- **More testable**: Pure functions are easier to test
- **More composable**: Functions can be combined in many ways
- **More readable**: Declarative code is often clearer
- **More maintainable**: Less mutable state means fewer bugs

The refactored codebase now follows functional programming principles while maintaining the same functionality and improving testability. 