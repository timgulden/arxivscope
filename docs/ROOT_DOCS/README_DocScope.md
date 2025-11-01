# DocScope - API-Powered Paper Visualization [Legacy]

> This document describes the legacy Dash-based frontend. The UI is migrating to React with logic in TypeScript. See `../DEVELOPMENT/REACT_TS_GUIDE.md` and `../API/README.md`.

DocScope is a refactored version of the original ArXivScope application that uses the DocScope API instead of local pickle files. This provides a more scalable, maintainable, and feature-rich experience.

## Features

- **API-Powered**: Fetches data from the DocScope API instead of local files
- **Real-time Data**: Always shows the latest data from the database
- **Interactive Clustering**: Dynamic clustering with LLM-generated summaries
- **Spatial Filtering**: Zoom and pan to explore different regions
- **Source Filtering**: Filter papers by source/country
- **Paper Details**: Click on points to see detailed paper information

## Architecture

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   DocScope      │◄──────────────►│  DocScope API   │
│   (Frontend)    │                │   (Backend)     │
└─────────────────┘                └─────────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                ┌─────────────────┐
│   Dash/Plotly   │                │   PostgreSQL    │
│   Visualization │                │   Database      │
└─────────────────┘                └─────────────────┘
```

## Prerequisites

1. **Virtual Environment**: Activated Python virtual environment
2. **API Server**: DocScope API running on `http://localhost:5001`
3. **Database**: PostgreSQL with papers and 2D embeddings
4. **Dependencies**: All required Python packages installed

## Quick Start

### 1. Start the API Server

```bash
cd embedding-enrichment
./start_api.sh
```

The API server will be available at `http://localhost:5001`

### 2. Start DocScope

```bash
./start_docscope.sh
```

DocScope will be available at `http://localhost:8050`

### 3. Use the Application

1. **Automatic Loading**: Data loads automatically at startup (500 papers for testing, 5000 for production)
2. **Explore**: Use mouse to zoom and pan around the visualization
3. **Dynamic Loading**: More data loads automatically as you zoom in to maintain target paper count
4. **Filter**: Use the sidebar filters to show specific sources
5. **Cluster**: Click "Compute clusters" to generate dynamic clusters
6. **Details**: Click on any point to see paper details

## Key Differences from Original

### Original (Monolithic docscope.py)
- ❌ Loads data from local pickle file
- ❌ Static data (requires manual updates)
- ❌ Limited to pre-computed embeddings
- ❌ No real-time filtering
- ❌ Single monolithic file
- ❌ Hard to maintain and test

### New (Modular docscope/)
- ✅ Fetches data from API
- ✅ Real-time data from database
- ✅ Dynamic filtering and querying
- ✅ Scalable modular architecture
- ✅ Better error handling
- ✅ Modern API integration
- ✅ Automatic data loading at startup
- ✅ Zoom-based dynamic data fetching
- ✅ Intelligent caching system
- ✅ Component-based design
- ✅ Easy to maintain and test

## API Integration

DocScope uses the following API endpoints:

- `GET /api/papers` - Fetch papers with filters
- `GET /api/stats` - Get database statistics
- `GET /api/health` - Health check

### Query Parameters Used

- `limit`: Maximum number of papers to fetch
- `fields`: Specific fields to return
- `bbox`: Bounding box for spatial filtering
- `sql_filter`: SQL WHERE clauses for filtering

## Features

### View Management Strategy

DocScope uses an intelligent view management system that handles different user interactions:

1. **Initial Load**: Fetches `TARGET_RECORDS_PER_VIEW` papers and establishes coverage area
2. **Zoom-In**: When zooming into a specific area, fetches more papers if density is insufficient
3. **Zoom-Out/Pan**: When the view expands beyond current coverage, fetches new papers to fill the expanded area
4. **Caching**: Avoids redundant API calls by caching results based on bounding box and limit

This ensures users always have a rich, interactive experience regardless of how they navigate the visualization.

### Data Loading
- **Automatic Startup**: Loads 500 papers automatically at startup
- **Smart View Management**: Fetches new data when view expands (zoom-out/pan) or when density is insufficient (zoom-in)
- **Intelligent Caching**: Caches API responses to avoid redundant calls
- **Error Handling**: Graceful handling of API failures
- **Progress Feedback**: Shows loading status, data counts, cache statistics, and fetch reasons

### Visualization
- **2D Embeddings**: Displays papers in 2D space
- **Color Coding**: Different colors for different sources
- **Interactive Plot**: Zoom, pan, and click interactions
- **Responsive Design**: Adapts to different screen sizes

### Clustering
- **Dynamic Clustering**: K-means clustering on visible papers
- **Voronoi Regions**: Visual cluster boundaries
- **LLM Summaries**: AI-generated cluster descriptions
- **Real-time Updates**: Clusters update with zoom/pan

### Filtering
- **Source Filtering**: Filter by paper source/country
- **Spatial Filtering**: Zoom to specific regions
- **Combined Filters**: Mix multiple filter types

### Paper Details
- **Click Interaction**: Click points to see details
- **Rich Information**: Title, abstract, date, source
- **Dismissible Popups**: Easy to close detail views

## Configuration

### Production vs Testing Configuration

The application is currently configured for testing with smaller datasets:

- **Testing**: 500 papers (initial load and per view)
- **Production**: 5000 papers (initial load and per view)

To switch to production configuration, update this value in `docscope/config/settings.py`:

```python
# Configuration
TARGET_RECORDS_PER_VIEW = 5000  # Target records for initial load and per zoom level
```

### API Configuration
```python
API_BASE_URL = "http://localhost:5001/api"
TARGET_RECORDS_PER_VIEW = 500  # Target papers for initial load and per zoom level (5000 for production)
MAX_CACHE_SIZE = 50  # Maximum cached datasets
```

### Color Mapping
```python
country_color_map = {
    'United States': '#1E90FF',
    'China': 'red',
    'aipickle': '#4CAF50',
}
```

### Clustering Settings
- Default clusters: 30
- Minimum papers for clustering: 30
- LLM temperature: 0.3

### Caching Settings
- Cache size: 50 datasets
- Cache key: bbox + limit combination
- Automatic cache management (FIFO)

## Troubleshooting

### Common Issues

1. **API Connection Error**
   ```
   Error: Could not load data from API. Please check if the API server is running.
   ```
   - Solution: Start the API server first

2. **No Data Loaded**
   - Check if database has papers with 2D embeddings
   - Verify API health endpoint

3. **Slow Performance**
   - Reduce the number of papers fetched
   - Use spatial filtering to limit data
   - Check database indexes

4. **Clustering Not Working**
   - Ensure enough papers are visible
   - Check LLM API connectivity
   - Verify clustering parameters

### Debug Mode

Run with debug mode for detailed logs:
```bash
python docscope/app.py
```

## Development

### Adding New Features

1. **New API Endpoints**: Update `fetch_papers_from_api()`
2. **New Filters**: Add to the filter interface
3. **New Visualizations**: Extend the Plotly figure
4. **New Interactions**: Add new callbacks

### Testing

1. **API Testing**: Use the test suite in `embedding-enrichment/`
2. **UI Testing**: Manual testing of interactions
3. **Performance Testing**: Monitor with different data sizes

## Performance Considerations

- **Data Loading**: Limit initial fetch to reasonable size
- **Clustering**: Only cluster visible papers
- **Caching**: Consider caching for frequently accessed data
- **Pagination**: Implement for very large datasets

## Future Enhancements

- [ ] **Real-time Updates**: WebSocket integration
- [ ] **Advanced Filtering**: Date ranges, text search
- [ ] **Export Features**: Save visualizations and data
- [ ] **User Preferences**: Save user settings
- [ ] **Mobile Support**: Responsive mobile interface
- [ ] **Offline Mode**: Cache data for offline use

## Dependencies

- `dash`: Web framework
- `plotly`: Visualization library
- `pandas`: Data manipulation
- `requests`: HTTP client
- `scikit-learn`: Clustering algorithms
- `shapely`: Geometric operations
- `numpy`: Numerical computing

## License

This project follows the same license as the parent ArXivScope project. 