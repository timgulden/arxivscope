# DocScope Functional Specification

> **Purpose**: Comprehensive specification of current DocScope frontend capabilities to ensure complete feature parity during React migration.

> **Audience**: Development team, stakeholders, and anyone implementing or extending DocScope functionality.

> **Status**: Based on analysis of current Dash implementation as of September 18, 2025.

---

## **I. CORE DATA OPERATIONS**

### **A. Data Fetching and Management**

**1. Batch Record Retrieval**
- **Capability**: Fetch configurable batches of paper records from DocTrove API
- **Parameters**: 
  - Limit: 100-50,000 records (default: 5,000)
  - Offset: For pagination support
  - Fields: Configurable field selection via API_FIELDS setting
- **Data Sources**: OpenAlex, RAND Publications, External Publications, ArXiv AI Subset
- **Performance**: Target <2 seconds for initial load, <1 second for subsequent fetches

**2. Dynamic Data Loading**
- **Capability**: Automatically fetch additional data based on user viewport changes
- **Triggers**: Zoom operations, pan operations, filter changes
- **Debouncing**: 500ms debounce on user input changes, 50ms on zoom operations
- **Caching**: Maintains cache of fetched data to avoid redundant API calls
- **Background Loading**: Non-blocking data updates with loading indicators

**3. Data Transformation and Validation**
- **Capability**: Transform API responses into visualization-ready format
- **Coordinate Extraction**: Parse 2D embeddings from `doctrove_embedding_2d` field
- **Data Validation**: Validate paper records for required fields and valid coordinates
- **Error Handling**: Graceful handling of malformed or missing data
- **Field Mapping**: Map internal field names to user-friendly display names

---

## **II. VISUALIZATION AND DISPLAY**

### **A. 2D Scatter Plot Visualization**

**1. Paper Point Display**
- **Capability**: Display papers as colored dots in 2D coordinate space
- **Coordinate System**: UMAP-generated 2D embeddings (X, Y coordinates)
- **Point Styling**:
  - Size: 8px diameter (configurable)
  - Opacity: 70% (configurable)
  - Colors: Source-based color coding (OpenAlex: orange, RAND: purple, etc.)
- **Performance**: Handle up to 50,000 points with smooth rendering

**2. Interactive Navigation**
- **Zoom**: Mouse wheel and zoom controls with smooth transitions
- **Pan**: Click-and-drag navigation across the coordinate space
- **Selection**: Click individual points to view paper details
- **Viewport Management**: Automatic data loading based on current view bounds
- **Extent Management**: Preserve zoom/pan state during filter operations

**3. Visual Feedback and Status**
- **Loading States**: Visual indicators during data fetching and processing
- **Status Indicator**: Real-time display of current data count and system status
- **Error Display**: User-friendly error messages for failed operations
- **Progress Indicators**: Loading spinners and progress feedback

### **B. Clustering Visualization**

**1. On-Demand Clustering**
- **Capability**: Compute and display K-means clusters of visible papers
- **Algorithm**: K-means clustering with configurable cluster count (1-999, default: 30)
- **Trigger**: Manual activation via "Compute Clusters" button
- **Performance**: Target <10 seconds for clustering 10,000 papers

**2. Cluster Region Display**
- **Voronoi Polygons**: Generate and display cluster boundary regions
- **Cluster Labels**: AI-generated cluster summaries using LLM analysis
- **Interactive Control**: Toggle cluster visibility with "Show Clusters" checkbox
- **Color Coding**: Distinct colors for each cluster region
- **Responsive Updates**: Clusters recalculate when data or parameters change

**3. Cluster Intelligence**
- **LLM Integration**: Azure OpenAI integration for cluster summary generation
- **Content Analysis**: Analyze paper titles and abstracts within each cluster
- **Summary Generation**: Generate descriptive labels for each cluster
- **Error Handling**: Graceful fallback when LLM services unavailable

---

## **III. FILTERING AND SEARCH CAPABILITIES**

### **A. Source and Metadata Filtering**

**1. Data Source Selection**
- **Capability**: Filter papers by data source
- **Sources**: OpenAlex, RAND Publications (randpub), External Publications (extpub), ArXiv AI Subset (aipickle)
- **Interface**: Multi-select checkboxes with dynamic source discovery
- **Behavior**: Real-time filtering with immediate visualization updates

**2. Temporal Filtering**
- **Capability**: Filter papers by publication year range
- **Interface**: Interactive range slider with year endpoints
- **Range**: 1950-2025 (configurable)
- **Default**: 2000-2025
- **Real-time Updates**: Immediate filtering as slider values change
- **Visual Feedback**: Display current year range values

**3. Record Limit Control**
- **Capability**: User-configurable maximum number of papers to display
- **Interface**: Numeric input field labeled "Fetch"
- **Range**: 100-50,000 records
- **Default**: 5,000 records (configurable via TARGET_RECORDS_PER_VIEW)
- **Debouncing**: 500ms delay to prevent excessive API calls during typing

### **B. Advanced Filtering**

**1. Universe Constraints (SQL Filtering)**
- **Capability**: Apply custom SQL WHERE clauses to constrain the paper universe
- **Interface**: Modal dialog with SQL input textarea
- **Features**:
  - Natural language to SQL conversion using LLM
  - SQL query validation and testing
  - Database schema reference display
  - Example queries and syntax help
- **Validation**: Test queries before application to prevent errors
- **Persistence**: Constraints apply to all subsequent operations

**2. Spatial Filtering (Bounding Box)**
- **Capability**: Automatically filter papers based on current viewport bounds
- **Implementation**: Extract X,Y coordinate ranges from zoom/pan operations
- **Behavior**: Transparent filtering - user doesn't directly control this
- **Performance**: Optimized queries using spatial indexing
- **Integration**: Combines with other filters for compound filtering

### **C. Semantic Search**

**1. Text-Based Similarity Search**
- **Capability**: Find papers semantically similar to input text
- **Interface**: Multi-line textarea for search queries
- **Input Types**: 
  - Short queries ("machine learning", "computer vision")
  - Long text passages (abstracts, descriptions)
  - Technical terms and concepts
- **Threshold Control**: Similarity threshold slider (0.0-1.0, default: 0.5)

**2. Search Processing**
- **Backend Integration**: Uses DocTrove embedding services for similarity calculation
- **Performance**: Target <3 seconds for semantic search queries
- **Result Highlighting**: Visual indication of matching papers in scatter plot
- **Result Persistence**: Maintains search results until cleared or new search performed

**3. Search Management**
- **Clear Function**: Reset search state and return to full dataset view
- **Search History**: Persist last confirmed search text
- **Error Handling**: Graceful handling of search service failures
- **Feedback**: Clear indication of search progress and results count

---

## **IV. ENRICHMENT AND METADATA INTEGRATION**

### **A. Dynamic Enrichment Configuration**

**1. Enrichment Source Selection**
- **Capability**: Select enrichment data source from available options
- **Interface**: Dropdown with dynamic population based on available data
- **Sources**: OpenAlex, RAND Publications, External sources
- **Dependency**: Enrichment tables populate based on selected source

**2. Enrichment Table Selection**
- **Capability**: Choose specific enrichment table for selected source
- **Interface**: Dropdown populated dynamically based on source selection
- **Examples**: `openalex_country_enrichment`, `randpub_metadata`
- **Validation**: Only show tables with available data for current dataset

**3. Enrichment Field Selection**
- **Capability**: Select specific enrichment field for visualization or filtering
- **Interface**: Dropdown populated based on selected table
- **Field Types**: Country data, topic classifications, publication types, etc.
- **Integration**: Selected fields become available for filtering and display

### **B. Enrichment Data Integration**

**1. Dynamic Field Addition**
- **Capability**: Add enrichment fields to paper data for visualization
- **Process**: Join enrichment tables with main paper data via API
- **Performance**: Optimized queries with proper indexing
- **Error Handling**: Graceful handling when enrichment data unavailable

**2. Enrichment-Based Filtering**
- **Capability**: Filter papers based on enrichment field values
- **Examples**: 
  - Country filtering: "Show only US and China papers"
  - Publication type: "Show only Research Reports (RR)"
  - Topic classification: "Show only AI/ML papers"
- **Interface**: Integrated with universe constraint system

**3. Enrichment State Management**
- **Capability**: Maintain enrichment configuration across user sessions
- **Persistence**: Remember selected source, table, and field choices
- **Reset Function**: Clear enrichment configuration and return to base data
- **Validation**: Ensure enrichment selections remain valid as data changes

---

## **V. USER INTERFACE AND INTERACTION**

### **A. Layout and Navigation**

**1. Responsive Layout Design**
- **Main Area**: Scatter plot visualization (75% width)
- **Sidebar**: Controls and paper details (25% width)
- **Header**: Status indicators and primary controls
- **Responsive**: Adapts to different screen sizes and orientations
- **Theme**: Dark theme with customizable color scheme

**2. Control Organization**
- **Primary Controls**: Status indicator, fetch limit, clustering controls
- **Filter Controls**: Source selection, year range, universe constraints
- **Search Controls**: Semantic search input, similarity threshold, search actions
- **Enrichment Controls**: Modal-based enrichment configuration
- **Visual Hierarchy**: Logical grouping and clear visual separation

**3. Navigation and State Management**
- **View State Persistence**: Maintain zoom/pan state during operations
- **Filter State**: Preserve filter selections across data updates
- **URL State**: Support for bookmarkable application states (basic implementation)
- **Reset Functions**: "Home" button to return to initial view state

### **B. Interactive Features**

**1. Paper Selection and Details**
- **Selection**: Click any paper point to view detailed information
- **Detail Display**: Show title, abstract, authors, publication date, source
- **Metadata Integration**: Display enrichment data when available
- **Link Access**: Provide links to original papers when available
- **Error Handling**: Graceful handling when paper details unavailable

**2. Real-Time Filtering**
- **Immediate Updates**: Filter changes immediately update visualization
- **Combined Filters**: Multiple filter types work together (AND logic)
- **Filter Feedback**: Clear indication of active filters and result counts
- **Filter Reset**: Easy clearing of individual or all filters

**3. Interactive Clustering**
- **Manual Trigger**: User-initiated clustering computation
- **Parameter Control**: Adjustable cluster count with real-time updates
- **Visual Toggle**: Show/hide cluster boundaries and labels
- **Cluster Information**: Display cluster summaries and paper counts
- **Performance Feedback**: Progress indication during cluster computation

---

## **VI. DATA INTEGRATION AND API FEATURES**

### **A. Multi-Source Data Handling**

**1. Unified Data Model**
- **Capability**: Handle papers from multiple sources with unified interface
- **Sources**: OpenAlex (academic papers), RAND (research reports), ArXiv (AI subset), External publications
- **Field Harmonization**: Map source-specific fields to common interface
- **Metadata Preservation**: Maintain source-specific metadata while providing unified access

**2. Dynamic Source Discovery**
- **Capability**: Automatically discover available data sources
- **API Integration**: Query DocTrove API for available sources and counts
- **Real-Time Updates**: Source availability updates as new data ingested
- **Error Handling**: Handle unavailable or temporarily offline sources

**3. Enrichment Data Integration**
- **Capability**: Seamlessly integrate enrichment data with base paper data
- **Join Operations**: Efficient joining of main papers with enrichment tables
- **Field Discovery**: Dynamic discovery of available enrichment fields
- **Performance Optimization**: Optimized queries for large-scale enrichment joins

### **B. Advanced Query Capabilities**

**1. SQL Query Generation and Validation**
- **Natural Language Input**: Convert plain English to SQL WHERE clauses
- **LLM Integration**: Azure OpenAI for intelligent query generation
- **Query Validation**: Test SQL queries before application
- **Schema Reference**: Built-in database schema documentation
- **Error Prevention**: Syntax validation and safe query execution

**2. Compound Filtering**
- **Capability**: Combine multiple filter types in single query
- **Filter Types**: Source, year range, spatial bounds, semantic similarity, enrichment fields
- **Logic**: AND combination of all active filters
- **Optimization**: Efficient query planning for compound filters
- **Performance**: Maintain responsiveness with complex filter combinations

**3. Similarity and Embedding Operations**
- **Embedding Search**: Find papers similar to text input using vector similarity
- **Threshold Control**: Adjustable similarity thresholds for precision/recall balance
- **Vector Operations**: Efficient similarity calculations using pgvector database extension
- **Result Ranking**: Papers ranked by similarity score
- **Performance**: Target <3 seconds for similarity searches

---

## **VII. SYSTEM INTEGRATION AND PERFORMANCE**

### **A. API Integration**

**1. DocTrove API Client**
- **Endpoint Coverage**: Full integration with DocTrove v2 API endpoints
- **Authentication**: Support for API authentication when required
- **Error Handling**: Comprehensive error handling for network and API failures
- **Retry Logic**: Automatic retry for transient failures
- **Timeout Management**: Configurable timeouts for different operation types

**2. Real-Time Data Synchronization**
- **Live Updates**: Reflect changes in underlying data without full page refresh
- **Cache Management**: Intelligent caching to balance performance and data freshness
- **Conflict Resolution**: Handle concurrent user operations gracefully
- **State Synchronization**: Maintain UI state consistency with backend data

**3. Performance Optimization**
- **Lazy Loading**: Load data only when needed for current view
- **Efficient Rendering**: Optimized visualization rendering for large datasets
- **Memory Management**: Prevent memory leaks during long user sessions
- **Network Optimization**: Minimize API calls through intelligent caching and batching

### **B. Error Handling and Resilience**

**1. Graceful Degradation**
- **API Failures**: Continue functioning with cached data when API unavailable
- **Partial Data**: Handle incomplete or malformed data gracefully
- **Service Timeouts**: Provide meaningful feedback for slow operations
- **Network Issues**: Retry mechanisms and offline capability indicators

**2. User Feedback**
- **Loading States**: Clear indication of ongoing operations
- **Error Messages**: User-friendly error descriptions with suggested actions
- **Progress Indicators**: Real-time progress for long-running operations
- **Success Confirmation**: Clear feedback when operations complete successfully

**3. System Monitoring**
- **Performance Tracking**: Monitor and log key performance metrics
- **Error Logging**: Comprehensive error logging for debugging
- **Usage Analytics**: Track feature usage and user interaction patterns
- **Health Monitoring**: System health indicators and status reporting

---

## **VIII. USER EXPERIENCE FEATURES**

### **A. Accessibility and Usability**

**1. Keyboard Navigation**
- **Tab Navigation**: Full keyboard navigation support for all interactive elements
- **Keyboard Shortcuts**: Common shortcuts for frequent operations
- **Focus Management**: Clear visual focus indicators
- **Screen Reader Support**: Semantic markup for assistive technologies

**2. Responsive Design**
- **Multi-Device Support**: Functional on desktop, tablet, and mobile devices
- **Adaptive Layout**: Layout adjusts to different screen sizes and orientations
- **Touch Support**: Touch-friendly interactions for mobile devices
- **Performance**: Maintain performance across different device capabilities

**3. Visual Design**
- **Dark Theme**: Consistent dark theme throughout application
- **Color Accessibility**: High contrast colors meeting WCAG guidelines
- **Visual Hierarchy**: Clear information hierarchy and navigation patterns
- **Consistent Styling**: Unified design language across all components

### **B. Advanced User Features**

**1. Configuration and Preferences**
- **Persistent Settings**: Remember user preferences across sessions
- **Customizable Defaults**: User-configurable default values for common operations
- **Theme Options**: Customizable color schemes and visual preferences
- **Performance Settings**: User-adjustable performance vs quality trade-offs

**2. Data Export and Sharing**
- **Current Capability**: Basic data access through paper detail views
- **Future Enhancement**: Export filtered datasets in various formats
- **Sharing**: Shareable URLs for specific views and filter combinations
- **Integration**: Potential integration with external tools and workflows

---

## **IX. TECHNICAL CAPABILITIES**

### **A. State Management**

**1. Application State**
- **Current View State**: Bounding box, zoom level, pan position
- **Filter State**: All active filters (source, year, search, enrichment, universe constraints)
- **UI State**: Loading states, error states, modal visibility, selected papers
- **Performance State**: Cache status, background operation status

**2. State Persistence**
- **Session Persistence**: Maintain state during user session
- **URL State**: Basic URL-based state sharing
- **Local Storage**: Persist user preferences and recent operations
- **State Recovery**: Restore application state after errors or refreshes

**3. State Synchronization**
- **Real-Time Updates**: Keep UI state synchronized with backend data
- **Optimistic Updates**: Immediate UI feedback for user actions
- **Conflict Resolution**: Handle state conflicts gracefully
- **Rollback Capability**: Undo operations when they fail

### **B. Integration Architecture**

**1. API Contract Compliance**
- **DocTrove Integration**: Full compliance with DocTrove API specifications
- **Version Compatibility**: Support for API versioning and backward compatibility
- **Contract Validation**: Runtime validation of API responses
- **Type Safety**: TypeScript integration for compile-time API validation

**2. Extensibility**
- **Plugin Architecture**: Support for additional visualization types
- **Custom Filters**: Framework for adding new filter types
- **Enrichment Extensions**: Support for new enrichment data sources
- **Integration Points**: Well-defined interfaces for external integrations

---

## **X. CURRENT IMPLEMENTATION DETAILS**

### **A. Key Components (Current Dash Implementation)**

**1. Main Application Components**
- **app.py**: Main application layout and configuration (1,191 lines)
- **callbacks_orchestrated.py**: User interaction handling (2,288 lines)
- **data_service.py**: API integration and data processing (918 lines)
- **clustering_service.py**: Clustering algorithms and LLM integration (274 lines)
- **ui_components.py**: Reusable UI component definitions

**2. Configuration and Settings**
- **settings.py**: Application configuration and constants
- **callback_config.py**: Callback behavior configuration
- **Environment Variables**: Configurable API endpoints, ports, and behavior settings

**3. State Stores (Dash-Specific)**
- **Data Stores**: `data-store`, `data-metadata`, `available-sources`, `selected-sources`
- **View Stores**: `view-ranges-store`, `current-view-state`, `force-autorange`
- **Filter Stores**: `filter-trigger`, `source-filter-trigger`, `zoom-trigger`
- **Enrichment Stores**: `enrichment-state`, `enrichment-tables`, `enrichment-fields`
- **UI Stores**: `cluster-busy`, `cluster-overlay`, `app-ready`

### **B. Performance Characteristics (Current Baseline)**

**1. Response Times**
- **Initial Load**: ~5 seconds for 5,000 papers
- **Filter Updates**: 1-2 seconds for most filter operations
- **Clustering**: 5-15 seconds depending on paper count and cluster number
- **Semantic Search**: 2-5 seconds for typical queries
- **Paper Selection**: <100ms for individual paper detail display

**2. Resource Usage**
- **Memory**: ~800MB for 10,000 papers loaded
- **Network**: Efficient API usage with caching and debouncing
- **CPU**: Optimized for smooth user interactions
- **Storage**: Minimal local storage for state persistence

---

## **XI. MIGRATION REQUIREMENTS**

### **A. Feature Parity Requirements**

**Must Preserve (100% Compatibility):**
- All data fetching and filtering capabilities
- Complete scatter plot visualization functionality
- On-demand clustering with LLM-generated summaries
- Semantic search with similarity thresholds
- Enrichment data integration and filtering
- Universe constraint SQL filtering
- Multi-source data handling
- Real-time user interaction responsiveness

**Should Improve:**
- Performance (target 50% improvement in response times)
- User experience (better loading states, error handling)
- Code maintainability (functional programming principles)
- Testing coverage (comprehensive test suite)

**Could Enhance (Future Iterations):**
- Additional visualization types
- Advanced analytics and insights
- Collaborative features
- Data export capabilities
- Mobile optimization

### **B. Technical Requirements**

**1. Architecture Compliance**
- **Functional Programming**: All business logic implemented as pure functions
- **Service Separation**: Clear boundaries between UI and business logic
- **Type Safety**: Full TypeScript implementation with strict mode
- **Testing**: >90% test coverage for business logic, >80% for UI components

**2. Performance Requirements**
- **Initial Load**: <3 seconds (vs current 5 seconds)
- **Filter Response**: <500ms (vs current 1-2 seconds)
- **Memory Usage**: <500MB for 50,000 papers
- **Bundle Size**: <2MB gzipped for initial load

**3. Quality Requirements**
- **Accessibility**: WCAG 2.1 AA compliance
- **Browser Support**: Chrome, Firefox, Safari, Edge
- **Responsive Design**: Functional on mobile, tablet, desktop
- **Error Recovery**: Graceful handling of all error scenarios

---

## **XII. USER WORKFLOWS**

### **A. Primary User Journeys**

**1. Exploratory Analysis Workflow**
```
User opens application
→ Views initial scatter plot of papers (5,000 default)
→ Zooms into area of interest
→ Additional papers load automatically for zoomed region
→ Applies source filter (e.g., "OpenAlex only")
→ Applies year filter (e.g., "2020-2023")
→ Clicks on interesting paper point
→ Reviews paper details in sidebar
→ Continues exploration with different filters
```

**2. Focused Search Workflow**
```
User has specific research interest
→ Enters semantic search query (e.g., "machine learning healthcare")
→ Adjusts similarity threshold for precision/recall balance
→ Reviews semantically similar papers in visualization
→ Applies additional filters to refine results
→ Computes clusters to identify research themes
→ Reviews LLM-generated cluster summaries
→ Selects papers of interest for detailed review
```

**3. Data Discovery Workflow**
```
User explores unfamiliar dataset
→ Reviews available data sources and counts
→ Applies universe constraints to focus on relevant subset
→ Uses enrichment data to understand data characteristics
→ Computes clusters to identify major themes
→ Uses cluster summaries to understand dataset structure
→ Drills down into specific clusters or themes of interest
```

### **B. Advanced User Workflows**

**1. Comparative Analysis Workflow**
```
User compares different data sources
→ Selects multiple sources for comparison
→ Uses clustering to identify source-specific patterns
→ Applies temporal filters to analyze trends over time
→ Uses enrichment data to understand source characteristics
→ Exports or documents findings for further analysis
```

**2. Targeted Research Workflow**
```
User has specific research requirements
→ Uses natural language to generate universe constraint SQL
→ Tests and refines SQL query for accuracy
→ Applies semantic search within constrained universe
→ Uses enrichment filtering for additional precision
→ Analyzes results with clustering and manual review
→ Iterates on filters and constraints to refine results
```

---

*Document created: September 18, 2025*
*Based on: Current DocScope Dash implementation analysis*
*Version: 1.0*
*Status: Complete functional specification for migration reference*
