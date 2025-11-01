# DocScope Configuration

## Configurable Settings

### Number of Dots Displayed

The number of dots (papers) displayed on the screen is configurable through the `TARGET_RECORDS_PER_VIEW` setting.

**Note**: The UI input for this setting includes a 500ms debounce delay to prevent excessive API calls when typing multi-digit numbers. A loading indicator (⏳) will appear while the debounce is active.

#### Default Value
- **Default**: 500 dots per view
- **Location**: `docscope/config/settings.py`

#### Configuration Methods

**1. Environment Variable (Recommended)**
```bash
# Set environment variable before running the app
export TARGET_RECORDS_PER_VIEW=1000
python -m docscope.app
```

**2. Direct Code Modification**
Edit `docscope/config/settings.py`:
```python
TARGET_RECORDS_PER_VIEW = 1000  # Change this value
```

**3. Runtime Configuration**
You can also modify the value programmatically:
```python
from docscope.config.settings import TARGET_RECORDS_PER_VIEW
# TARGET_RECORDS_PER_VIEW = 1000  # Set your desired value
```

#### Performance Considerations

- **Lower values (100-500)**: Faster rendering, less memory usage
- **Higher values (1000-5000)**: More data visible, potentially slower performance
- **Maximum**: The API supports up to 50,000 records per request

#### Usage Examples

```bash
# Development with fewer dots for faster testing
export TARGET_RECORDS_PER_VIEW=200
python -m docscope.app

# Production with more dots for better data coverage
export TARGET_RECORDS_PER_VIEW=2000
python -m docscope.app

# High-performance setup
export TARGET_RECORDS_PER_VIEW=5000
python -m docscope.app
```

### Other Configurable Settings

- **DEBOUNCE_DELAY_SECONDS**: Controls zoom responsiveness (default: 0.05s)
- **MAX_CACHE_SIZE**: Maximum number of cached data sets (default: 10)
- **API_BASE_URL**: Backend API endpoint (default: http://localhost:5001/api)

## Architecture Notes

The limit is applied in multiple places:
1. **Initial Load**: `fetch_papers_for_view()` uses the configured limit
2. **Zoom Operations**: Each zoom level fetches data with the configured limit
3. **Graph Rendering**: The graph component respects the limit for performance

All hardcoded `limit=500` values have been removed in favor of the configurable `TARGET_RECORDS_PER_VIEW` setting. 