# DocScope Developer Quick Reference

> **Current Environment (October 2025)**: This system runs on a local laptop environment. Legacy Dash frontend on port 8050 (frozen), React frontend on port 3000 (recommended). See [CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md) for current setup details.

## 🚀 Quick Start

### Running the App

#### Legacy Dash Frontend (Frozen, Bug Fixes Only)
```bash
# From project root:
python -m docscope.app
# Runs on http://localhost:8050
```

#### React Frontend (Recommended, Active Development)
```bash
# From docscope-platform/services/docscope/react:
cd docscope-platform/services/docscope/react
npm run dev
# Runs on http://localhost:3000
```

### Key Files to Know
- **`app.py`** - Main entry point, app layout
- **`components/callbacks.py`** - All user interactions
- **`components/data_service.py`** - API calls and data processing
- **`components/clustering_service.py`** - Clustering algorithms
- **`config/settings.py`** - Configuration constants

## 🔄 Data Flow

```
User Action → Callback → Data Service → API → Response → UI Update
```

### Example: Zooming In
1. User zooms → `callbacks.py` detects zoom
2. Callback calls → `data_service.py` with new bounds
3. Data service calls → DocTrove API with bbox parameter
4. API returns → papers in that area
5. Callback updates → scatter plot with new data

## 📝 Common Development Tasks

### Adding a New Filter
1. **UI**: Add checkbox to `ui_components.py`
2. **Callback**: Add input to relevant callback in `callbacks.py`
3. **Data**: Add filtering logic to `data_service.py`
4. **Test**: Verify filter works with existing functionality

### Adding a New API Field
1. **Config**: Add field to `API_FIELDS` in `settings.py`
2. **Data Service**: Update column mapping in `data_service.py`
3. **UI**: Add display logic in relevant callback
4. **Test**: Verify field appears correctly

### Adding a New Visualization
1. **Component**: Create new component in `components/`
2. **Callback**: Add callback to handle interactions
3. **Layout**: Add to main layout in `app.py`
4. **Test**: Verify visualization renders correctly

## 🐛 Debugging Tips

### Data Issues
- Check `data_service.py` for API response parsing
- Verify `API_FIELDS` in `settings.py` matches API
- Look for coordinate parsing errors in logs

### UI Issues
- Check callback inputs/outputs in `callbacks.py`
- Verify component IDs match between layout and callbacks
- Check browser console for JavaScript errors

### Clustering Issues
- Verify Azure OpenAI API key in `clustering_service.py`
- Check Voronoi polygon generation logic
- Look for coordinate data issues

## 🔧 Configuration

### API Settings (`config/settings.py`)
```python
# Configuration via .env.local file (project root)
API_BASE_URL = "http://localhost:5001"  # DocTrove API
TARGET_RECORDS_PER_VIEW = 500
API_FIELDS = "doctrove_paper_id,doctrove_title,..."
```

### Environment Variables (`.env.local`)
```bash
# API Configuration
NEW_API_BASE_URL=http://localhost:5001
LEGACY_API_BASE_URL=http://localhost:5001

# Frontend Configuration
NEW_UI_PORT=3000  # React Frontend
NEW_UI_PUBLIC_URL=http://localhost:3000

# Other settings
TARGET_RECORDS_PER_VIEW=500
DEBOUNCE_DELAY_SECONDS=0.05
```

### Clustering Settings
```python
# In clustering_service.py
KMEANS_RANDOM_STATE = 42
CLUSTER_SUMMARY_MAX_TOKENS = 2000
```

## 📊 State Management

### Dash Stores
- **`data-store`**: Current papers data
- **`cluster-overlay`**: Clustering results
- **`cluster-busy`**: Clustering computation status
- **`clear-selection-store`**: Selection clearing trigger

### Callback Patterns
```python
@app.callback(
    Output('component-id', 'property'),
    [Input('trigger-id', 'property')],
    [State('state-id', 'property')],
    prevent_initial_call=True
)
def callback_function(trigger_value, state_value):
    # Logic here
    return output_value
```

## 🧪 Testing

### Running Tests
```bash
python -m pytest docscope/tests/
```

### Test Structure
- **`test_basic.py`**: Basic functionality tests
- **`test_components.py`**: Component-specific tests
- Mock API responses for testing without network

## 🔄 Migration from Old Code

### Old vs New Patterns

| Old Pattern | New Pattern |
|-------------|-------------|
| Global variables | Dash stores |
| Direct file reading | API calls via data service |
| Monolithic functions | Modular callbacks |
| Hardcoded values | Configuration constants |

### Key Changes
1. **No more pickle files** - everything comes from API
2. **Callback-based interactions** - all user actions go through callbacks
3. **Service separation** - business logic separated from UI
4. **Configuration centralization** - all settings in one place

## 🚨 Common Pitfalls

### ❌ Don't Do This
- Use global variables
- Hardcode API endpoints
- Mix UI and business logic
- Skip error handling

### ✅ Do This Instead
- Use Dash stores for state
- Use configuration constants
- Keep components focused
- Always handle API errors

## 📚 Further Reading

- [Dash Callback Documentation](https://dash.plotly.com/basic-callbacks)
- [Plotly Graph Objects](https://plotly.com/python/reference/)
- [Pandas DataFrame Operations](https://pandas.pydata.org/docs/)
- [Scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html) 