# DocTrove/DocScope Documentation

> **Current Environment (October 2025)**: This system has been migrated to a local laptop environment. The system runs with API on port 5001, React Frontend on port 3000, and PostgreSQL on port 5432. All data (database and models) is stored on the internal drive. See [CONTEXT_SUMMARY.md](../CONTEXT_SUMMARY.md) for current setup details.
>
> Migration in progress: UI moving to React, core logic to TypeScript, backend remains Python via API. Documentation entries are being tagged as [Current], [Needs Update], or [Legacy] during this transition. See `migration-planning/` and `docs/DEVELOPMENT/REACT_TS_GUIDE.md`.

Welcome to the comprehensive documentation for the DocTrove/DocScope project. This documentation is organized to help you quickly find the information you need.

## 📚 Documentation Structure

### 📖 [DOCUMENTATION_NAVIGATION_GUIDE.md](./DOCUMENTATION_NAVIGATION_GUIDE.md)
- **Comprehensive Navigation**: Detailed navigation paths and cross-references
- **User-Specific Guidance**: Navigation tailored for different user types
- **Documentation Relationships**: How different sections relate to each other

### 🏗️ [ARCHITECTURE](./ARCHITECTURE/) [Current]
- **System Design**: High-level architecture, design principles, and technical specifications
- **Design Documents**: Original design decisions, architectural patterns, and system overviews
- **Functional Programming**: Design principles and functional programming guidelines

### 🔌 [API](./API/) [Current]
- **API Documentation**: Endpoint specifications, request/response formats, and examples
- **Business Logic**: Core business logic documentation and validation rules
- **Interceptor Pattern**: API interceptor architecture and usage

### 🚀 [DEPLOYMENT](./DEPLOYMENT/) [Current]
- **Server Setup**: AWS, Azure, and local deployment guides
- **Environment Configuration**: Multi-environment setup and configuration
- **Migration Guides**: Database and system migration procedures

### 👨‍💻 [DEVELOPMENT](./DEVELOPMENT/) [Current]
- **Quick Start**: Getting started guides for developers
- **Testing**: Comprehensive testing guide and test suite documentation
- **Code Standards**: Functional programming principles and coding guidelines
- **Git Workflow**: Commit procedures, branching strategy, and repository management
- **TypeScript Docs Generation**: See [DEVELOPMENT/DOCS_GENERATION_GUIDE.md](./DEVELOPMENT/DOCS_GENERATION_GUIDE.md)

### 🔧 [OPERATIONS](./OPERATIONS/) [Current]
- **Performance**: Performance analysis, optimization guides, and monitoring
- **Data Processing**: Ingestion workflows, enrichment processes, and data management
- **Progress Monitoring**: Real-time progress tracking for large-scale embedding generation
- **Troubleshooting**: Common issues, debugging guides, and error resolution

### 🧩 [COMPONENTS](./COMPONENTS/) [Current]
- **Component Documentation**: Links to component-specific documentation co-located with code
- **Integration Guides**: How different components work together
- **Component Architecture**: Detailed component design and implementation

### 📜 [LEGACY](./LEGACY/) [Legacy]
- **Historical Documents**: Outdated or obsolete documentation for reference
- **Migration Artifacts**: Database and system migration artifacts
- **Review Status**: Documents under review for currency and relevance

## 🚀 Quick Navigation

**📖 For detailed navigation paths and comprehensive guidance, see:**
**[DOCUMENTATION_NAVIGATION_GUIDE.md](./DOCUMENTATION_NAVIGATION_GUIDE.md)**

### For New Developers [Current]
1. Start with [DEVELOPMENT/QUICK_START.md](./DEVELOPMENT/QUICK_START.md)
2. Review [ARCHITECTURE/README.md](./ARCHITECTURE/README.md)
3. Check [DEVELOPMENT/COMPREHENSIVE_TESTING_GUIDE.md](./DEVELOPMENT/COMPREHENSIVE_TESTING_GUIDE.md)
4. See [DEVELOPMENT/REACT_TS_GUIDE.md](./DEVELOPMENT/REACT_TS_GUIDE.md)
5. Collaboration workflow: [DEVELOPMENT/COLLABORATION_GUIDE.md](./DEVELOPMENT/COLLABORATION_GUIDE.md)

### For System Administrators [Current]
1. Review [DEPLOYMENT/README.md](./DEPLOYMENT/README.md)
2. Check [OPERATIONS/README.md](./OPERATIONS/README.md)
3. See [DEPLOYMENT/SERVER_DEPLOYMENT_GUIDE.md](./DEPLOYMENT/SERVER_DEPLOYMENT_GUIDE.md)

### For API Users [Current]
1. Start with [API/README.md](./API/README.md)
2. Backend reference: [`doctrove-api/API_DOCUMENTATION.md`](../doctrove-api/API_DOCUMENTATION.md)
3. Quick start: [`doctrove-api/QUICK_START_GUIDE.md`](../doctrove-api/QUICK_START_GUIDE.md)

## 📝 Documentation Maintenance

- **High-level docs**: Centralized in this `docs/` folder
- **Component-specific docs**: Co-located with code in respective folders
- **Cross-references**: Maintained between centralized and co-located docs
- **Regular reviews**: Scheduled to ensure currency and relevance

### Tagging Guidelines
- [Current]: Accurate and aligned with React + TypeScript migration and FP/testing standards
- [Needs Update]: Valuable for the migration; requires targeted edits to be Current
- [Legacy]: Historical/reference only; not part of the active plan

## 🔗 Related Resources

- **GitHub Repository**: [Project Repository]
- **Issue Tracker**: [Issues and Bug Reports]
- **Contributing Guide**: [How to Contribute]

---

*Last updated: October 2025*
*Maintained by: Development Team*
