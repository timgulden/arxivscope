# Development Documentation

This section contains development guides, quick start instructions, testing documentation, and coding standards for developers working on the DocTrove/DocScope project.

## 🚀 Getting Started

### Quick Start Guides
- **[QUICK_START.md](./QUICK_START.md)** - Quick start guide for new developers
- **[STARTUP_GUIDE.md](./STARTUP_GUIDE.md)** - Comprehensive startup and development environment setup
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick reference for common development tasks

### Developer References
- **[DEVELOPER_QUICK_REFERENCE.md](./DEVELOPER_QUICK_REFERENCE.md)** - Developer quick reference guide
- **[CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md)** - Context summary for new chat sessions (root level)

## 🧪 Testing

### Testing Framework
- **[COMPREHENSIVE_TESTING_GUIDE.md](./COMPREHENSIVE_TESTING_GUIDE.md)** - Comprehensive testing guide and test suite documentation
- **[FAST_TESTS.md](./FAST_TESTS.md)** - Fast test execution guide
- **[run_comprehensive_tests.sh](../run_comprehensive_tests.sh)** - Comprehensive test runner script (root level)

### Testing Philosophy
- **Unit Tests**: Fast execution, pure functions, no external dependencies
- **Integration Tests**: Marked with `@pytest.mark.skip` for external dependencies
- **Performance Tests**: 5s baseline threshold with realistic variance tolerance
- **Test Organization**: Tests organized by component with clear `RUNNING INSTRUCTIONS`

## 📚 Code Standards

### Functional Programming
- **Pure Functions**: Emphasis on pure functions, immutable data, and side-effect-free operations
- **No Classes**: Avoid classes altogether in favor of functional approaches
- **Testing**: Keep tests up to date when writing or refactoring code
- **Interceptors**: Use interceptor pattern for cross-cutting concerns

### Development Practices
- **Planning**: Plan before writing any code
- **Testing**: Write tests for new functionality
- **Documentation**: Update documentation with code changes
- **Code Review**: All changes go through code review

## 🔀 Git Workflow & Commit Procedures

### Branching Strategy
- **Main Branch**: `main` - production-ready code only
- **Feature Branches**: `feat/<area>-<short-desc>` - new features
- **Hotfix Branches**: `hotfix/<description>` - critical bug fixes
- **No direct commits to main**: All changes via feature branches and PRs

### Commit Guidelines
```bash
# Standard commit workflow
git checkout main
git pull origin main                           # Always start from latest
git checkout -b feat/your-feature-name         # Create feature branch
# ... make changes ...
git add .
git commit -m "feat: brief description"       # Use conventional commits
git push origin feat/your-feature-name
# Create Pull Request on GitHub
```

### Commit Message Format
Use conventional commit messages:
- **`feat:`** - New feature
- **`fix:`** - Bug fix
- **`docs:`** - Documentation changes
- **`refactor:`** - Code refactoring
- **`test:`** - Test additions/changes
- **`chore:`** - Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add semantic search filter modal"
git commit -m "fix: resolve clustering performance issue"
git commit -m "docs: update API endpoint documentation"
```

### Before Committing

**⚠️ CRITICAL CHECKS:**
1. **Never commit sensitive data**: `.env.local`, API keys, credentials
2. **Never commit large files**: `.gitignore` should exclude data files, node_modules, etc.
3. **Check repository size**: If repository exceeds 100MB, investigate large files
4. **Verify .gitignore**: Ensure data directories and environment files are excluded

**Pre-Commit Checklist:**
```bash
# Check what will be committed
git status
git diff --staged

# Check for large files
git ls-files | xargs du -h | sort -hr | head -20

# Verify .env.local is NOT committed
git ls-files | grep -E "^\.env$|^\.env\.local$"
# Should return nothing!

# Run tests before committing
python -m pytest tests/
npm test  # For frontend changes
```

### Repository Size Issues

**If push is slow or fails due to size:**
```bash
# Check repository size
git count-objects -vH

# If repository is too large, create fresh repo
cd /path/to/project
rm -rf .git
git init
git add .
git commit -m "feat: initial commit with current codebase"
git remote add origin git@github.com:username/repo.git
git push -u origin main
```

**Prevent future size issues:**
- Use `.gitignore` to exclude large data files
- Use Git LFS for binary assets if necessary
- Keep data separate from code repository
- Regular cleanup of build artifacts

### GitHub Setup
For authentication setup instructions, see: **[GITHUB_SETUP.md](../../GITHUB_SETUP.md)**

### Code Review Process
1. Create Pull Request from feature branch
2. Ensure all tests pass
3. Request review from appropriate team members
4. Address review comments
5. Merge to main when approved
6. Delete feature branch after merge

## 🔧 Development Environment

### Setup Requirements
- Python 3.8+
- PostgreSQL with pgvector extension
- Environment configuration files
- Required Python packages (see requirements.txt files)

### Running the Application
- **DocScope Frontend**: `python -m docscope.app` (from project root)
- **DocTrove API**: `python doctrove-api/api.py`
- **All Services**: `./startup.sh --restart --background`

### Development Workflow
1. **Setup**: Follow startup guide for environment setup
2. **Development**: Make changes in appropriate component
3. **Testing**: Run relevant test suites
4. **Documentation**: Update component-specific documentation
5. **Review**: Submit for code review

## 🔗 Related Documentation

- **[Main Documentation Index](../README.md)** - Return to main documentation
- **[Architecture Documentation](../ARCHITECTURE/README.md)** - System design and principles
- **[Component Documentation](../COMPONENTS/README.md)** - Component-specific implementation details
- **[Testing Guide](./COMPREHENSIVE_TESTING_GUIDE.md)** - Comprehensive testing documentation

## 📋 Development Standards

### Code Quality
- **Linting**: Use project linting rules
- **Formatting**: Follow project formatting standards
- **Documentation**: Include docstrings and comments
- **Error Handling**: Proper error handling and logging

### Testing Requirements
- **Coverage**: Maintain good test coverage
- **Performance**: Include performance tests for critical paths
- **Integration**: Test component integration points
- **Regression**: Ensure no regressions in existing functionality

---

*Development documentation is maintained by the development team*

