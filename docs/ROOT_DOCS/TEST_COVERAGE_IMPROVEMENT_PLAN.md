# Test Coverage Improvement Plan

## Current State Analysis

### Existing Test Files:
- `test_basic.py` - Basic component tests (has import errors)
- `test_components.py` - Component integration tests (has import errors)
- `test_data_service.py` - Data service tests (has column name and API format issues)

### Issues Identified:
1. **Import Errors**: Tests reference non-existent modules (`..services.data_service`, `Config` class)
2. **Column Name Mismatches**: Tests expect 'Country of Publication' but actual data uses different column names
3. **API Response Format**: Tests don't match current API response structure
4. **Missing Error Handling Tests**: No tests for the comprehensive error handling we just implemented
5. **Incomplete Coverage**: Missing tests for callbacks, clustering service, and graph components

## Test Coverage Improvement Plan

### Phase 1: Fix Existing Tests

#### 1.1 Fix Import Issues
- Update import statements to match actual module structure
- Remove references to non-existent classes/modules
- Fix relative import paths

#### 1.2 Fix Column Name Issues
- Update test data to match actual column names used in the application
- Align test expectations with current data structure
- Handle column name variations (e.g., 'Country of Publication' vs 'country2')

#### 1.3 Fix API Response Format
- Update mock responses to match current API structure
- Fix parameter expectations in API call tests
- Handle new API parameters (search_text, similarity_threshold)

### Phase 2: Add Missing Test Coverage

#### 2.1 Error Handling Tests
- **Data Service Error Handling**:
  - Test input validation for all parameters
  - Test specific exception types (ConnectionError, Timeout, HTTPError, etc.)
  - Test graceful degradation scenarios
  - Test timeout handling

- **Graph Component Error Handling**:
  - Test invalid DataFrame inputs
  - Test missing coordinate data
  - Test clustering overlay with invalid data
  - Test figure creation with edge cases

- **Callbacks Error Handling**:
  - Test user-facing error messages
  - Test invalid user input handling
  - Test network error scenarios
  - Test data loading failures

- **Clustering Service Error Handling**:
  - Test invalid clustering parameters
  - Test insufficient data scenarios
  - Test LLM API failures
  - Test coordinate validation

#### 2.2 Callback Tests
- **Data Loading Callbacks**:
  - Test `update_data_store_unified`
  - Test `semantic_search_load`
  - Test `handle_zoom`
  - Test debouncing functionality

- **Clustering Callbacks**:
  - Test `handle_clustering`
  - Test cluster parameter validation
  - Test clustering with different data scenarios

- **UI Interaction Callbacks**:
  - Test `display_click_data`
  - Test country filtering
  - Test year range filtering
  - Test search functionality

#### 2.3 Component Integration Tests
- **End-to-End Workflows**:
  - Test complete data loading and visualization workflow
  - Test clustering workflow
  - Test search and filtering workflow
  - Test error recovery workflows

#### 2.4 Performance Tests
- **Data Loading Performance**:
  - Test large dataset handling
  - Test memory usage with large datasets
  - Test response time with different data sizes

- **Clustering Performance**:
  - Test clustering with different cluster counts
  - Test clustering with large datasets
  - Test LLM API response time

### Phase 3: Test Infrastructure Improvements

#### 3.1 Test Utilities
- **Mock Data Generators**:
  - Create realistic test data generators
  - Generate data with various edge cases
  - Create data with different coordinate formats

- **API Mock Utilities**:
  - Create comprehensive API response mocks
  - Mock different error scenarios
  - Mock network timeouts and failures

- **Test Fixtures**:
  - Create reusable test fixtures
  - Set up common test data
  - Create test environment configurations

#### 3.2 Test Organization
- **Test Structure**:
  - Organize tests by component
  - Separate unit tests from integration tests
  - Create test suites for different scenarios

- **Test Documentation**:
  - Document test purposes and scenarios
  - Create test coverage reports
  - Document test data requirements

### Phase 4: Advanced Testing

#### 4.1 Property-Based Testing
- **Data Validation Properties**:
  - Test data transformation properties
  - Test filtering consistency
  - Test coordinate parsing properties

#### 4.2 Stress Testing
- **Load Testing**:
  - Test with maximum data sizes
  - Test concurrent operations
  - Test memory limits

#### 4.3 Edge Case Testing
- **Boundary Conditions**:
  - Test with empty datasets
  - Test with malformed data
  - Test with extreme coordinate values

## Implementation Priority

### High Priority (Phase 1)
1. Fix import errors in existing tests
2. Fix column name mismatches
3. Fix API response format issues
4. Add basic error handling tests

### Medium Priority (Phase 2)
1. Add comprehensive callback tests
2. Add clustering service tests
3. Add graph component tests
4. Add integration tests

### Low Priority (Phase 3-4)
1. Add performance tests
2. Add property-based tests
3. Add stress tests
4. Improve test infrastructure

## Success Metrics

### Coverage Targets
- **Line Coverage**: >90% for all components
- **Branch Coverage**: >85% for critical paths
- **Function Coverage**: 100% for public APIs

### Quality Metrics
- **Test Reliability**: <5% flaky tests
- **Test Performance**: <30 seconds for full test suite
- **Test Maintainability**: Clear test organization and documentation

## Next Steps

1. **Immediate**: Fix existing test import and column name issues
2. **Short-term**: Add error handling tests for all components
3. **Medium-term**: Add comprehensive callback and integration tests
4. **Long-term**: Implement advanced testing strategies

## Files to Create/Update

### New Test Files
- `test_error_handling.py` - Comprehensive error handling tests
- `test_callbacks.py` - Callback function tests
- `test_clustering_service.py` - Clustering service tests
- `test_graph_component.py` - Graph component tests
- `test_integration.py` - End-to-end integration tests

### Updated Test Files
- `test_data_service.py` - Fix existing issues and add error handling tests
- `test_basic.py` - Fix import issues and update test data
- `test_components.py` - Fix import issues and update component tests

### Test Utilities
- `test_utils.py` - Common test utilities and mock generators
- `test_fixtures.py` - Reusable test fixtures
- `conftest.py` - Pytest configuration and fixtures 