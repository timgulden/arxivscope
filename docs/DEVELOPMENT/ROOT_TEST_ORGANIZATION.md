# Root Test Organization

## 📁 Tests Have Been Moved!

**All test files that were previously in the root directory have been organized into the `tests/` subdirectory.**

## 🎯 What This Means

- **The comprehensive test suite** (`run_comprehensive_tests.sh`) continues to work from the root
- **Individual test files** are now organized by category in `tests/`
- **Root directory is cleaner** and more professional

## 🔍 Where to Find Tests

### **Main Test Suite** (Run from root)
```bash
./run_comprehensive_tests.sh
```

### **Individual Tests** (Organized by category)
- **`tests/performance/`** - Performance and benchmark tests
- **`tests/integration/`** - Integration and end-to-end tests  
- **`tests/ingestion/`** - Data ingestion and processing tests
- **`tests/enrichment/`** - Data enrichment and analysis tests
- **`tests/utilities/`** - Utility and functional tests
- **`tests/scripts/`** - Test scripts and SQL files

## 📖 Full Documentation

See `tests/README.md` for complete details on:
- Test organization
- How to run different test categories
- Test requirements and setup
- Adding new tests

## ⚠️ Important Notes

- **These tests are NOT part of the main comprehensive test suite**
- **Many require specific setup** (database, services, data)
- **Some are designed to be run from specific directories**
- **Check individual test files for requirements**

---

*This organization makes the project more maintainable while preserving all test functionality.*

