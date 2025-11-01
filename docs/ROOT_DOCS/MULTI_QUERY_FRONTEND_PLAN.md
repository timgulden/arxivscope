# Multi-Query Frontend Development Plan

## Overview

This document outlines the plan for building a multi-query frontend system for DocScope/DocTrove that allows users to create multiple queries, execute them in parallel, and visualize the combined results with different colors and symbols.

## Architecture Decision

**Backend Approach**: Use existing `/api/papers` endpoint instead of building complex multi-query backend
- ✅ Leverages proven, tested API infrastructure
- ✅ Supports all needed features (SQL filtering, semantic search, bounding box, etc.)
- ✅ Simpler maintenance and debugging
- ✅ Better separation of concerns

**Frontend Approach**: Build intelligent frontend that:
- Makes multiple parallel API calls to `/api/papers`
- Combines results with different colors/symbols
- Handles visualization overlay and user interactions

## Phase 1: Core Infrastructure (Week 1)

### 1.1 Query Builder Component
- [ ] Create `MultiQueryBuilder` component
- [ ] Form fields for query configuration:
  - Query name/description
  - SQL filter conditions
  - Color scheme selection
  - Symbol selection (circle, square, triangle, etc.)
  - Data source selection (if applicable)
- [ ] Add/remove query functionality
- [ ] Query validation and error handling

### 1.2 Query State Management
- [ ] Create query state store (using existing state management)
- [ ] Query definition data structure:
  ```typescript
  interface QueryDefinition {
    id: string;
    name: string;
    sqlFilter: string;
    colorScheme: ColorScheme;
    symbol: string;
    isActive: boolean;
  }
  ```
- [ ] Global filters state:
  ```typescript
  interface GlobalFilters {
    yearRange?: [number, number];
    bbox?: [number, number, number, number];
    searchText?: string;
    similarityThreshold?: number;
  }
  ```

### 1.3 API Integration Layer
- [ ] Create `MultiQueryService` class
- [ ] Parallel API execution using `Promise.all()`
- [ ] Error handling and retry logic
- [ ] Loading states management
- [ ] Result caching (optional)

## Phase 2: Visualization Integration (Week 2)

### 2.1 Multi-Dataset Plotly Integration
- [ ] Extend existing Plotly component to handle multiple datasets
- [ ] Color and symbol mapping for each query
- [ ] Legend generation with query names
- [ ] Hover information showing query source

### 2.2 Interactive Features
- [ ] Toggle visibility of individual queries
- [ ] Click to filter by query
- [ ] Legend interaction (click to show/hide datasets)
- [ ] Zoom and pan with all datasets

### 2.3 Performance Optimization
- [ ] Efficient rendering of large datasets
- [ ] Progressive loading for large result sets
- [ ] Memory management for multiple datasets

## Phase 3: Advanced Features (Week 3)

### 3.1 Global Filter Integration
- [ ] Year range slider
- [ ] Bounding box selection tool
- [ ] Semantic search with similarity threshold
- [ ] Real-time filter application to all queries

### 3.2 Query Templates
- [ ] Pre-built query templates (e.g., "Machine Learning Papers", "RAND Reports")
- [ ] Save/load custom query configurations
- [ ] Share query configurations

### 3.3 Advanced Visualization
- [ ] Multiple plot types (scatter, histogram, timeline)
- [ ] Faceted plots for different queries
- [ ] Statistical summaries per query

## Phase 4: User Experience & Polish (Week 4)

### 4.1 User Interface Improvements
- [ ] Drag-and-drop query reordering
- [ ] Query duplication functionality
- [ ] Bulk query operations
- [ ] Keyboard shortcuts

### 4.2 Performance Monitoring
- [ ] Query execution time tracking
- [ ] Result count displays
- [ ] Performance warnings for large queries

### 4.3 Documentation & Help
- [ ] In-app help system
- [ ] Query examples and tutorials
- [ ] Best practices guide

## Technical Implementation Details

### File Structure
```
docscope/
├── components/
│   ├── MultiQueryBuilder/
│   │   ├── index.tsx
│   │   ├── QueryForm.tsx
│   │   ├── QueryList.tsx
│   │   └── GlobalFilters.tsx
│   ├── MultiQueryVisualization/
│   │   ├── index.tsx
│   │   ├── MultiDatasetPlot.tsx
│   │   └── QueryLegend.tsx
│   └── services/
│       ├── MultiQueryService.ts
│       └── QueryStateManager.ts
```

### Key Components

#### MultiQueryBuilder
- Form-based interface for creating queries
- Real-time validation
- Color picker and symbol selector
- Query preview functionality

#### MultiQueryVisualization
- Extends existing Plotly visualization
- Handles multiple datasets with different colors/symbols
- Interactive legend and filtering

#### MultiQueryService
- Manages parallel API calls
- Handles error states and retries
- Provides loading state updates

### State Management
- Use existing state management patterns
- Query definitions stored in component state
- Results cached to avoid unnecessary API calls
- Global filters applied to all queries

### API Integration
```typescript
// Example API call structure
const executeQueries = async (queries: QueryDefinition[], globalFilters: GlobalFilters) => {
  const apiCalls = queries.map(query => 
    fetch(`/api/papers?${buildQueryParams(query, globalFilters)}`)
  );
  
  const results = await Promise.all(apiCalls);
  return results.map((result, index) => ({
    ...result,
    queryId: queries[index].id,
    colorScheme: queries[index].colorScheme,
    symbol: queries[index].symbol
  }));
};
```

## Success Criteria

### Functional Requirements
- [ ] Users can create 3+ different queries simultaneously
- [ ] Queries execute in parallel with loading indicators
- [ ] Results display with different colors and symbols
- [ ] Global filters apply to all active queries
- [ ] Interactive legend allows showing/hiding datasets

### Performance Requirements
- [ ] Query execution completes within 5 seconds for typical queries
- [ ] UI remains responsive during query execution
- [ ] Handles datasets with 10,000+ points efficiently
- [ ] Memory usage stays reasonable with multiple large datasets

### User Experience Requirements
- [ ] Intuitive query builder interface
- [ ] Clear visual feedback for query states
- [ ] Easy error recovery and retry mechanisms
- [ ] Responsive design for different screen sizes

## Risk Mitigation

### Technical Risks
1. **Large dataset performance**: Implement progressive loading and efficient rendering
2. **API rate limiting**: Add retry logic and request queuing
3. **Memory management**: Implement dataset cleanup and pagination

### User Experience Risks
1. **Complex interface**: Start with simple query builder, add complexity gradually
2. **Slow queries**: Provide clear loading states and progress indicators
3. **Error handling**: Comprehensive error messages and recovery options

## Testing Strategy

### Unit Tests
- [ ] Query builder form validation
- [ ] API integration layer
- [ ] State management logic
- [ ] Visualization component rendering

### Integration Tests
- [ ] End-to-end query execution
- [ ] Multi-dataset visualization
- [ ] Global filter application

### User Testing
- [ ] Usability testing with target users
- [ ] Performance testing with large datasets
- [ ] Cross-browser compatibility testing

## Future Enhancements

### Phase 5+ Ideas
- [ ] Query scheduling and automation
- [ ] Advanced analytics and insights
- [ ] Export functionality for combined datasets
- [ ] Collaborative query sharing
- [ ] Machine learning query suggestions

## Development Workflow

1. **Feature branches**: Create `feature/multi-query-{component}` branches
2. **Incremental development**: Build and test each component independently
3. **Integration testing**: Regular integration testing with existing components
4. **User feedback**: Gather feedback early and often
5. **Documentation**: Update documentation as features are completed

## Timeline

- **Week 1**: Core infrastructure and query builder
- **Week 2**: Visualization integration and basic interactions
- **Week 3**: Advanced features and global filters
- **Week 4**: Polish, testing, and documentation

## Notes

- This plan is living document and will be updated as we progress
- Priorities may shift based on user feedback and technical constraints
- Each phase should be completed and tested before moving to the next
- Regular reviews and adjustments to the plan are expected 