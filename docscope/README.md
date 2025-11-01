# DocScope - Modular Architecture

> **Current Environment (October 2025)**: This system runs on a local laptop environment. The legacy Dash frontend runs on port 8050 (frozen, bug fixes only). The React frontend runs on port 3000 (recommended, active development). See [CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md) for current setup details.
>
> **Note**: This document describes the legacy Dash frontend. For the React frontend, see `docscope-platform/services/docscope/react/` if it exists.

## Overview

DocScope has been refactored from a single monolithic file into a clean, modular architecture. This document explains the new design in plain language.

## What Changed

### Before: Monolithic Design
- **Single file**: Everything was in one large `docscope.py` file
- **Data source**: Read from a local pickle file
- **Hard to maintain**: All functionality mixed together
- **Hard to test**: Difficult to test individual components

### After: Modular Design
- **Multiple files**: Functionality split into logical components
- **API integration**: Fetches data from the DocTrove API
- **Easy to maintain**: Each component has a single responsibility
- **Easy to test**: Components can be tested independently

## Architecture Overview

```
docscope/
├── app.py                    # Main application entry point
├── components/               # Reusable UI components
│   ├── callbacks.py         # All Dash callback logic
│   ├── data_service.py      # Data fetching and processing
│   ├── clustering_service.py # Clustering algorithms
│   ├── graph_component.py   # Plotly graph creation
│   └── ui_components.py     # UI layout components
├── config/
│   └── settings.py          # Configuration and constants
└── utils/                   # Utility functions
```

## Key Components Explained

### 1. `app.py` - The Main Application
**What it does**: Sets up the Dash app and defines the overall layout
**Why it's separate**: Keeps the main app configuration clean and focused

### 2. `components/callbacks.py` - User Interactions
**What it does**: Handles all user interactions (clicks, filters, zooming, clustering)
**Key features**:
- Dynamic data loading when you zoom in/out
- Country filtering
- Clustering computation
- Metadata display when clicking points
- "Show Clusters" toggle functionality

### 3. `components/data_service.py` - Data Management
**What it does**: Fetches and processes data from the DocTrove API
**Key features**:
- Fetches papers based on current view bounds
- Parses coordinate data from embeddings
- Handles country filtering
- Provides clean data to other components

### 4. `components/clustering_service.py` - Clustering Logic
**What it does**: Creates clusters and generates summaries using AI
**Key features**:
- K-means clustering algorithm
- Voronoi polygon generation for cluster regions
- AI-powered cluster summaries using Azure OpenAI
- Handles view-bound filtering for clustering

### 5. `components/ui_components.py` - User Interface
**What it does**: Defines reusable UI components
**Key features**:
- Country filter checkboxes
- Clustering controls
- Status indicators

### 6. `config/settings.py` - Configuration
**What it does**: Centralizes all configuration settings
**Key features**:
- API endpoints
- Default values
- Constants used throughout the app

## How It Works (User Perspective)

### 1. **Initial Load**
- App starts and fetches initial papers from the API (default: 500, configurable)
- Papers are displayed as colored dots on the scatter plot
- Each dot represents a research paper
- Users can adjust the number of papers to load via the "Max Dots" input with real-time updates

### 2. **Interactive Exploration**
- **Zoom**: When you zoom in, the app automatically fetches papers visible in that area
- **Filter**: Use the country checkboxes to show only papers from specific countries
- **Click**: Click any dot to see paper details (title, abstract, date, country)
- **Adjust Load**: Change the "Max Dots" to load more or fewer papers (with 500ms debounce)

### 3. **Clustering**
- Click "Compute Clusters" to group similar papers together
- Clusters appear as colored regions with AI-generated summaries
- Use "Show Clusters" checkbox to toggle cluster visibility

## Key Improvements

### 1. **Dynamic Data Loading**
- **Before**: All data loaded at once from pickle file
- **After**: Data loads dynamically based on what you're viewing, with user-configurable limits
- **Benefit**: Faster initial load, always shows relevant papers, user-controlled data volume with real-time updates

### 2. **Real-time API Integration**
- **Before**: Static data from local file
- **After**: Live data from DocTrove API
- **Benefit**: Always up-to-date with latest papers

### 3. **Modular Design**
- **Before**: Everything in one file
- **After**: Separate files for different concerns
- **Benefit**: Easier to maintain, debug, and extend

### 4. **Better Error Handling**
- **Before**: Limited error handling
- **After**: Graceful handling of API errors, missing data, etc.
- **Benefit**: More robust user experience

### 5. **User-Configurable Data Limits**
- **Before**: Hardcoded 500 record limit
- **After**: User-adjustable "Max Dots" input with environment variable support
- **Benefit**: Users can control data volume based on their needs and system capabilities

### 6. **Smart Callback Architecture**
- **Before**: Complex callback interactions causing infinite loops
- **After**: Clean, debounced callbacks with proper guards
- **Benefit**: Smooth user experience without excessive API calls or UI freezing

## Development Workflow

### Adding New Features
1. **UI changes**: Modify `ui_components.py` or `app.py`
2. **Data processing**: Add functions to `data_service.py`
3. **User interactions**: Add callbacks to `callbacks.py`
4. **Algorithms**: Add logic to appropriate service files

### Testing
- Each component can be tested independently
- Mock data can be used for testing without API calls
- UI components can be tested separately from logic

### Configuration
- All settings centralized in `config/settings.py`
- Easy to change API endpoints, limits, etc.
- Environment-specific configurations possible

#### Environment Variables
Configuration via `.env.local` file (project root):
- `TARGET_RECORDS_PER_VIEW`: Set default number of papers to load (default: 500)
- `NEW_API_BASE_URL`: DocTrove API endpoint (default: `http://localhost:5001`)
- `LEGACY_API_BASE_URL`: Legacy API endpoint (default: `http://localhost:5001`)
- `DEBOUNCE_DELAY_SECONDS`: Debounce delay for zoom operations (default: 0.5)

## Migration Notes

### For Developers
- **No more pickle files**: Data comes from API now
- **Callback patterns**: All user interactions go through callbacks
- **Functional approach**: Services use pure functions for better testing
- **Error handling**: Always check for API errors and missing data

### For Users
- **Same interface**: The app looks and works the same
- **Better performance**: Faster loading and smoother interactions
- **More data**: Access to the full DocTrove database
- **Real-time updates**: Always see the latest papers

## Troubleshooting

### Common Issues
1. **No data loading**: Check API connectivity and endpoints
2. **Clustering not working**: Verify Azure OpenAI API key
3. **Slow performance**: Check network connection to API
4. **Missing coordinates**: Some papers may not have embedding data

### Debug Mode
- Set logging level to DEBUG for detailed information
- Check browser console for JavaScript errors
- Monitor API response times

## Future Enhancements

The modular architecture makes it easy to add:
- New data sources
- Different clustering algorithms
- Additional visualization types
- User authentication
- Data export features
- Advanced filtering options

## Conclusion

The new modular DocScope maintains the same user experience while providing a much more maintainable and extensible codebase. The separation of concerns makes it easier to understand, test, and enhance the application. 