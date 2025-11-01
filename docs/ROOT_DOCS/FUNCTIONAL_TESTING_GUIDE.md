# Functional Testing Guide

## Overview

This guide covers how unit tests have been updated to reflect our shift from `for` loops to functional programming patterns using `map`, `filter`, and `reduce`.

## Why Update Tests for Functional Programming?

### **1. Test Pure Functions in Isolation**
- **Before**: Test entire loop logic with side effects
- **After**: Test individual pure functions that can be composed

### **2. Test Functional Composition**
- **Before**: Test imperative step-by-step logic
- **After**: Test how functions compose together

### **3. Test Immutability**
- **Before**: Test that loops modify state correctly
- **After**: Test that functions don't modify input data

### **4. Test Error Handling**
- **Before**: Test exception handling in loops
- **After**: Test error handling with `None` returns and filtering

## Updated Test Patterns

### **1. Testing Pure Functions**

#### **Before: Testing Loop Logic**
```python
def test_transform_dataframe_to_papers():
    # Test the entire loop logic
    df_rows = [{"title": "Test", "id": "1"}]
    result = transform_dataframe_to_papers(df_rows, config)
    
    # Test the whole transformation
    assert len(result[0]) == 1
    assert result[0][0]['doctrove_title'] == "Test"
```

#### **After: Testing Pure Functions**
```python
def test_map_row_to_papers_generic_pure_function():
    # Test the pure function in isolation
    row = {"title": "Test", "id": "1"}
    result = map_row_to_papers_generic(row, paper_id, config, current_date)
    
    # Test just the transformation logic
    assert result[0]['doctrove_title'] == "Test"

def test_transform_json_to_papers_functional_composition():
    # Test the composition of functions
    json_data = [{"title": "Test", "id": "1"}]
    result = transform_json_to_papers(json_data, config)
    
    # Test the overall result
    assert len(result[0]) == 1
```

### **2. Testing Functional Composition**

#### **Before: Testing Nested Logic**
```python
def test_filter_and_count():
    papers = [valid_paper, invalid_paper, valid_paper]
    
    # Test the nested loop logic
    valid_count = 0
    for paper in papers:
        if is_valid(paper):
            valid_count += 1
    
    assert valid_count == 2
```

#### **After: Testing Functional Composition**
```python
def test_functional_composition_chain():
    # Test the functional composition: filter -> map -> count
    papers = [valid_paper, invalid_paper, valid_paper]
    
    # Filter valid papers
    valid_papers = filter_valid_papers_generic(papers)
    
    # Count by source
    counts = count_papers_by_source_generic(valid_papers)
    
    # Verify composition works
    assert len(valid_papers) == 2
    assert counts['arxiv'] == 2
```

### **3. Testing Error Handling**

#### **Before: Testing Exception Handling**
```python
def test_error_handling_in_loop():
    papers = [valid_paper, problematic_paper]
    
    results = []
    for paper in papers:
        try:
            result = process_paper(paper)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {paper}: {e}")
            continue
    
    assert len(results) == 1
```

#### **After: Testing Functional Error Handling**
```python
def test_error_handling_in_functional_pipeline():
    # Test with data that would cause errors
    json_data = [problematic_row]
    
    # Should handle errors gracefully and return None for invalid items
    try:
        common_papers, source_metadata_list = transform_json_to_papers(
            json_data, config, id_generator=mock_id_generator
        )
        assert isinstance(common_papers, list)
        assert isinstance(source_metadata_list, list)
    except Exception as e:
        fail(f"Functional pipeline should handle errors gracefully: {e}")
```

### **4. Testing Immutability**

#### **Before: Testing State Changes**
```python
def test_loop_modifies_state():
    papers = [paper1, paper2]
    original_papers = papers.copy()
    
    # Test that loop modifies state correctly
    for paper in papers:
        paper['processed'] = True
    
    assert all(paper['processed'] for paper in papers)
    assert papers != original_papers  # State was modified
```

#### **After: Testing Immutability**
```python
def test_immutability_property():
    original_paper = paper.copy()
    original_metadata = metadata.copy()
    
    # Call function
    enrichment.calculate_credibility(paper, metadata)
    
    # Verify original data is unchanged
    assert original_paper == paper
    assert original_metadata == metadata
```

### **5. Testing Pure Function Properties**

#### **Before: Testing Side Effects**
```python
def test_loop_side_effects():
    global_counter = 0
    
    def process_with_side_effect(item):
        global global_counter
        global_counter += 1
        return item * 2
    
    items = [1, 2, 3]
    results = []
    for item in items:
        results.append(process_with_side_effect(item))
    
    assert global_counter == 3  # Side effect occurred
```

#### **After: Testing Pure Function Properties**
```python
def test_pure_function_properties():
    # Test same input always produces same output
    paper = sample_paper.copy()
    metadata = sample_metadata.copy()
    
    # Call function multiple times with same input
    result1 = enrichment.calculate_credibility(paper, metadata)
    result2 = enrichment.calculate_credibility(paper, metadata)
    result3 = enrichment.calculate_credibility(paper, metadata)
    
    # Should always return the same result
    assert result1 == result2
    assert result2 == result3
```

## Updated Test Files

### **1. doc-ingestor/tests/test_transformers.py**

**Key Changes:**
- Renamed class to `TestTransformersFunctional`
- Updated imports to use `generic_transformers` module
- Added tests for functional composition
- Added tests for error handling in functional pipelines
- Added tests for pure function properties

**New Test Methods:**
- `test_map_row_to_papers_generic_pure_function()`
- `test_transform_json_to_papers_functional_composition()`
- `test_filter_valid_papers_generic_functional()`
- `test_count_papers_by_source_generic_functional()`
- `test_functional_composition_chain()`
- `test_error_handling_in_functional_pipeline()`

### **2. embedding-enrichment/test_enrichment_framework_simple.py**

**Key Changes:**
- Renamed class to `TestEnrichmentFrameworkFunctional`
- Updated to test functional validation patterns
- Added tests for functional composition
- Added tests for pure function properties
- Added tests for immutability

**New Test Methods:**
- `test_process_papers_functional_pattern()`
- `test_process_papers_with_errors_functional()`
- `test_validation_functional_pattern()`
- `test_functional_composition_chain()`
- `test_pure_function_properties()`
- `test_immutability_property()`

## Testing Best Practices

### **1. Test Pure Functions in Isolation**
```python
def test_single_transformation():
    # Test one transformation function
    result = transform_single_item(input_data)
    assert result == expected_output
```

### **2. Test Function Composition**
```python
def test_functional_pipeline():
    # Test how functions compose
    pipeline = compose(filter_valid, map(transform), filter(None))
    result = pipeline(input_data)
    assert len(result) == expected_count
```

### **3. Test Error Handling with Optional**
```python
def test_error_handling():
    # Test that errors return None and are filtered out
    results = list(filter(None, map(safe_process, items)))
    assert len(results) == expected_valid_count
```

### **4. Test Immutability**
```python
def test_immutability():
    original = data.copy()
    result = process_function(data)
    assert data == original  # Input unchanged
```

### **5. Test Pure Function Properties**
```python
def test_pure_function():
    # Same input should always produce same output
    result1 = pure_function(input_data)
    result2 = pure_function(input_data)
    assert result1 == result2
```

## Running the Updated Tests

### **Run All Tests**
```bash
# Run all functional tests
pytest

# Run specific test files
pytest doc-ingestor/tests/test_transformers.py
pytest embedding-enrichment/test_enrichment_framework_simple.py
```

### **Run with Coverage**
```bash
# Run tests with coverage
pytest --cov=doc-ingestor --cov=embedding-enrichment

# Generate coverage report
pytest --cov=doc-ingestor --cov=embedding-enrichment --cov-report=html
```

### **Run Specific Test Classes**
```bash
# Run functional transformer tests
pytest doc-ingestor/tests/test_transformers.py::TestTransformersFunctional

# Run functional enrichment tests
pytest embedding-enrichment/test_enrichment_framework_simple.py::TestEnrichmentFrameworkFunctional
```

## Benefits of Updated Tests

### **1. Better Testability**
- **Isolated testing**: Test individual functions, not entire loops
- **Easier mocking**: Mock pure functions instead of complex state
- **Faster tests**: No need to test loop iterations

### **2. Better Coverage**
- **Edge cases**: Easier to test error conditions
- **Composition**: Test how functions work together
- **Properties**: Test functional programming properties

### **3. Better Maintainability**
- **Clear intent**: Tests show what functions do, not how they do it
- **Refactoring safety**: Changes to implementation don't break tests
- **Documentation**: Tests serve as documentation of function behavior

### **4. Better Debugging**
- **Isolated failures**: Failures point to specific functions
- **Clear inputs/outputs**: Easy to see what each function expects/returns
- **Reproducible**: Pure functions are easier to debug

## Conclusion

The updated tests now properly reflect our functional programming approach:

1. **Test pure functions in isolation** instead of testing loop logic
2. **Test functional composition** instead of testing nested logic
3. **Test immutability** instead of testing state changes
4. **Test error handling with Optional** instead of testing exception handling
5. **Test pure function properties** instead of testing side effects

This makes the tests more maintainable, easier to understand, and better at catching real issues in the functional code. 