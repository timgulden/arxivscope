# DocScope Release Notes - Major Update

## Version: 2.0.0
**Date**: July 7, 2025

## 🎉 Major New Features

### ✨ User-Configurable Data Limits
- **New "Max Dots" Input**: Users can now control how many papers to load (100-50,000 range)
- **Real-time Updates**: Graph refreshes immediately when limit changes
- **Debounced Input**: 500ms debounce prevents excessive API calls while typing
- **Environment Variable Support**: `TARGET_RECORDS_PER_VIEW` for default configuration
- **Loading Indicators**: Visual feedback during data fetching

### 🔧 Smart Callback Architecture
- **Eliminated Infinite Loops**: Fixed complex callback interactions that caused repeated API calls
- **Clean Separation**: Each callback has a single, clear responsibility
- **Proper Guards**: Prevents duplicate requests with same parameters
- **Debounced Operations**: Smooth zoom and input handling

### 🏗️ Clean Architecture
- **API Independence**: DocTrove API completely decoupled from DocScope configuration
- **Single Source of Truth**: Data flows cleanly from API → DocScope → UI
- **Modular Design**: Easy to maintain and extend

## 🚀 Performance Improvements

- **Faster Initial Load**: Only loads requested number of papers
- **Reduced API Calls**: Smart debouncing and guards prevent unnecessary requests
- **Smoother Interactions**: No more UI freezing during data updates
- **Memory Efficiency**: User-controlled data volume prevents memory issues

## 🔧 Technical Improvements

### Frontend (DocScope)
- **Configurable Limits**: `TARGET_RECORDS_PER_VIEW` setting with environment variable support
- **Debounced Input**: 500ms debounce on "Max Dots" input
- **Loading States**: Visual feedback during data operations
- **Error Handling**: Graceful handling of API errors and missing data

### Backend (DocTrove API)
- **Limit Validation**: Accepts and validates limit parameters (1-50,000 range)
- **Clean Interface**: No knowledge of frontend configuration
- **Robust Validation**: Comprehensive parameter validation

## 🎯 User Experience

### Before
- Hardcoded 500 record limit
- Infinite loops when changing settings
- UI freezing during updates
- No control over data volume

### After
- User-adjustable limits (100-50,000)
- Smooth, responsive interface
- Real-time graph updates
- Visual feedback for all operations

## 📋 Configuration Options

### Environment Variables
```bash
# Set default number of papers to load
export TARGET_RECORDS_PER_VIEW=1000

# API endpoint
export API_BASE_URL=http://localhost:5001

# Debounce delay for zoom operations
export DEBOUNCE_DELAY_SECONDS=0.5
```

### UI Controls
- **Max Dots Input**: Adjust number of papers to display
- **Country Filters**: Filter by publication country
- **Zoom Controls**: Pan and zoom to explore data
- **Clustering**: Compute and display paper clusters

## 🔍 Testing

The system has been thoroughly tested with:
- ✅ Various limit values (100, 500, 1000, 5000, 10000+)
- ✅ Rapid input changes (debouncing works correctly)
- ✅ Zoom operations (no infinite loops)
- ✅ API error conditions
- ✅ Memory usage with large datasets

## 🚀 Getting Started

1. **Set Environment Variables** (optional):
   ```bash
   export TARGET_RECORDS_PER_VIEW=1000
   ```

2. **Start the API**:
   ```bash
   cd doctrove-api
   python api.py
   ```

3. **Start DocScope**:
   ```bash
   python -m docscope.app
   ```

4. **Use the Interface**:
   - Adjust "Max Dots" to control data volume
   - Zoom and pan to explore papers
   - Use country filters to focus on specific regions
   - Click papers for detailed information

## 🎯 What's Next

This release establishes a solid foundation for future enhancements:
- Advanced filtering options
- Data export capabilities
- User authentication
- Additional visualization types
- Performance optimizations

## 📞 Support

For issues or questions:
- Check the troubleshooting section in README.md
- Review the API documentation
- Monitor console logs for debugging information

---

**This release represents a major step forward in DocScope's usability and performance. The user-configurable limits and clean architecture make it much more flexible and maintainable.** 