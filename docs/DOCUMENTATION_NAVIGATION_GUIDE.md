# Documentation Navigation Guide

This guide provides comprehensive navigation through the DocTrove/DocScope documentation structure. Use this when you need detailed navigation paths or want to understand how different documentation sections relate to each other.

## ⚠️ Important Notice: Documentation Currency

**This documentation was developed at different stages of project development and may contain outdated information.**

### **Documentation Status:**
- **🟢 Current**: Recent documentation (2024-2025) - generally up to date
- **🟡 Review Needed**: Older documentation that may need verification
- **🔴 Legacy**: Historical documentation for reference only

### **Before Using Any Documentation:**
1. **Check the date** of the document
2. **Verify against current code** implementation
3. **Test procedures** before following them
4. **Cross-reference** with more recent documentation

### **Most Current Information:**
- **System Status**: Check `CONTEXT_SUMMARY.md` for current state
- **Recent Changes**: Review recent commits and release notes
- **Code Implementation**: Verify against actual codebase
- **Test Results**: Run tests to confirm functionality

---

## 🚀 Quick Start Navigation

### **For New Team Members**
1. **Start Here**: [docs/README.md](./README.md) - Main documentation index
2. **Getting Started**: [docs/DEVELOPMENT/QUICK_START.md](./DEVELOPMENT/QUICK_START.md)
3. **System Overview**: [docs/ARCHITECTURE/README.md](./ARCHITECTURE/README.md)
4. **Development Setup**: [docs/DEVELOPMENT/STARTUP_GUIDE.md](./DEVELOPMENT/STARTUP_GUIDE.md)

### **For System Administrators**
1. **Server Setup**: [docs/DEPLOYMENT/README.md](./DEPLOYMENT/README.md)
2. **Environment Config**: [docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md](./DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md)
3. **Monitoring**: [docs/OPERATIONS/README.md](./OPERATIONS/README.md)

### **For API Users**
1. **API Overview**: [docs/API/README.md](./API/README.md)
2. **Endpoint Reference**: [docs/API/API_DOCUMENTATION.md](./API/API_DOCUMENTATION.md)
3. **Quick Start**: [docs/API/QUICK_START_GUIDE.md](./API/QUICK_START_GUIDE.md)

## 🏗️ Architecture & Design

### **System Design**
- **[docs/ARCHITECTURE/README.md](./ARCHITECTURE/README.md)** - Architecture overview and navigation
- **[docs/ARCHITECTURE/DESIGN_PRINCIPLES_AUDIT_REPORT.md](./ARCHITECTURE/DESIGN_PRINCIPLES_AUDIT_REPORT.md)** - Design principles compliance
- **[docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md](./ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md)** - Functional programming approach
- **[docs/ARCHITECTURE/DocTrove_Technical_Spec.md](./ARCHITECTURE/DocTrove_Technical_Spec.md)** - Technical specifications

### **Design Decisions**
- **[docs/ARCHITECTURE/PreviousDiscussion.md](./ARCHITECTURE/PreviousDiscussion.md)** - Historical design discussions
- **[docs/ARCHITECTURE/PRD%20for%20DocTrove%20Backend.md](./ARCHITECTURE/PRD%20for%20DocTrove%20Backend.md)** - Product requirements
- **[docs/ARCHITECTURE/DocTroveFS.md](./ARCHITECTURE/DocTroveFS.md)** - File system design

### **Functional Refactoring**
- **[docs/ARCHITECTURE/functional-refactor/](./ARCHITECTURE/functional-refactor/)** - Refactoring documentation
  - **CURRENT_STATUS.md** - Current refactoring status
  - **FUNCTIONAL_REFACTOR_PLAN.md** - Refactoring plan
  - **PHASE_0_1_CALLBACK_ANALYSIS.md** - Callback analysis

## 👨‍💻 Development & Testing

### **Quick Start & Setup**
- **[docs/DEVELOPMENT/QUICK_START.md](./DEVELOPMENT/QUICK_START.md)** - Complete setup guide
- **[docs/DEVELOPMENT/STARTUP_GUIDE.md](./DEVELOPMENT/STARTUP_GUIDE.md)** - Service startup procedures
- **[docs/DEVELOPMENT/QUICK_REFERENCE.md](./DEVELOPMENT/QUICK_REFERENCE.md)** - Quick reference commands
- **[docs/DEVELOPMENT/DEVELOPER_QUICK_REFERENCE.md](./DEVELOPMENT/DEVELOPER_QUICK_REFERENCE.md)** - Developer reference

### **Testing Framework**
- **[docs/DEVELOPMENT/COMPREHENSIVE_TESTING_GUIDE.md](./DEVELOPMENT/COMPREHENSIVE_TESTING_GUIDE.md)** - Complete testing guide
- **[docs/DEVELOPMENT/FAST_TESTS.md](./DEVELOPMENT/FAST_TESTS.md)** - Fast test execution
- **[run_comprehensive_tests.sh](../run_comprehensive_tests.sh)** - Test runner script (root level)

### **Code Standards**
- **Functional Programming**: Emphasis on pure functions, immutable data
- **Testing**: Keep tests up to date, write tests for new functionality
- **Documentation**: Update docs with code changes
- **Code Review**: All changes go through review

## 🚀 Deployment & Operations

### **Server Setup**
- **[docs/DEPLOYMENT/SERVER_DEPLOYMENT_GUIDE.md](./DEPLOYMENT/SERVER_DEPLOYMENT_GUIDE.md)** - General deployment
- **[docs/DEPLOYMENT/AWS_CLEAN_INSTALL_GUIDE.md](./DEPLOYMENT/AWS_CLEAN_INSTALL_GUIDE.md)** - AWS setup
- **[docs/DEPLOYMENT/AZURE_MIGRATION_SUMMARY.md](./DEPLOYMENT/AZURE_MIGRATION_SUMMARY.md)** - Azure migration
- **[docs/DEPLOYMENT/OPEN_SOURCE_DEPLOYMENT.md](./DEPLOYMENT/OPEN_SOURCE_DEPLOYMENT.md)** - Open source setup

### **Environment Management**
- **[docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md](./DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md)** - Multi-environment setup
- **[docs/DEPLOYMENT/COST_OPTIMIZED_DEPLOYMENT.md](./DEPLOYMENT/COST_OPTIMIZED_DEPLOYMENT.md)** - Cost optimization
- **Environment Files**: `env.local.example`, `env.remote.example`, `env.template`

### **Operations & Monitoring**
- **[docs/OPERATIONS/PERFORMANCE_ANALYSIS_SUMMARY.md](./OPERATIONS/PERFORMANCE_ANALYSIS_SUMMARY.md)** - Performance analysis
- **[docs/OPERATIONS/PERFORMANCE_OPTIMIZATION_GUIDE.md](./OPERATIONS/PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Optimization guide
- **[docs/OPERATIONS/ENRICHMENT_PIPELINE_QUICK_REFERENCE.md](./OPERATIONS/ENRICHMENT_PIPELINE_QUICK_REFERENCE.md)** - Enrichment workflows

## 🧩 Component Documentation

### **Component Index**
- **[docs/COMPONENTS/README.md](./COMPONENTS/README.md)** - Complete component documentation index

### **Core Components**
- **DocScope Frontend**: `docscope/` - Dash application and UI components
- **DocTrove API**: `doctrove-api/` - Flask API server and business logic
- **Data Ingestion**: `doc-ingestor/` - Data processing and transformation
- **Embedding Enrichment**: `embedding-enrichment/` - AI embedding generation
- **OpenAlex Integration**: `openalex/` - OpenAlex data ingestion

### **Component-Specific Docs**
- **Frontend**: `docscope/README.md`, `docscope/DEVELOPER_QUICK_REFERENCE.md`
- **API**: `doctrove-api/README.md`, `doctrove-api/API_DOCUMENTATION.md`
- **Ingestion**: `doc-ingestor/README.md`
- **Enrichment**: `embedding-enrichment/README.md`, `embedding-enrichment/README_ENRICHMENT_SCRIPTS.md`

## 📜 Legacy & Historical

### **Legacy Documentation**
- **[docs/LEGACY/README.md](./LEGACY/README.md)** - Legacy documentation index
- **Deprecated Files**: `docscope_deprecated.py`, `docscope_backup.py`
- **Historical Context**: Development history and previous discussions

### **Migration Artifacts**
- **Database**: `database/migrations/`, `database/backup.sh`, `database/recover.sh`
- **Field Mapping**: `current_field_mapping.txt`, `current_schema_dump.sql`
- **Migration Logs**: `migration_artifacts/DATABASE_MIGRATION_LOG.md`

## 🕒 Documentation Currency Guidelines

### **🟢 Most Likely Current (2024-2025):**
- **`CONTEXT_SUMMARY.md`** - Updated regularly for new chat sessions
- **`docs/DEVELOPMENT/`** - Recent development guides and testing docs
- **`docs/ARCHITECTURE/`** - Recent design principles and audit reports
- **Component READMEs** - Updated with code changes

### **🟡 Review Recommended:**
- **`docs/DEPLOYMENT/`** - Server setup may have changed
- **`docs/OPERATIONS/`** - Performance guides may be outdated
- **`docs/API/`** - API may have evolved since documentation
- **Environment setup scripts** - May need updates for current systems

### **🔴 Likely Outdated:**
- **`Design documents/`** - Historical design decisions
- **`docs/LEGACY/`** - Explicitly marked as legacy
- **Migration artifacts** - Specific to past migrations
- **Old performance reports** - May not reflect current state

### **💡 Currency Check Strategy:**
1. **Start with `CONTEXT_SUMMARY.md`** for current system state
2. **Check document dates** and last modified timestamps
3. **Verify against running system** (test commands, check outputs)
4. **Compare with recent commits** for functionality changes
5. **Run tests** to confirm documented behavior

## 🔗 Cross-References & Integration

### **Documentation Relationships**
- **High-level docs** → **Component docs** → **Implementation details**
- **Architecture docs** → **Development guides** → **Deployment procedures**
- **Component docs** → **API docs** → **Testing guides**

### **Navigation Patterns**
1. **Start with main index** for overview
2. **Navigate to relevant section** for details
3. **Use component docs** for implementation specifics
4. **Reference legacy docs** for historical context

## 📋 Maintenance & Updates

### **Documentation Standards**
- **Keep co-located docs** updated with code changes
- **Update centralized docs** when architecture changes
- **Review legacy docs** quarterly for relevance
- **Cross-reference** between related documents
- **Mark documentation currency** with dates and status indicators
- **Verify accuracy** against current code implementation

### **Update Schedule**
- **Monthly**: Quick review of all documentation
- **Quarterly**: Detailed review and currency verification
- **As needed**: Update when functionality changes

---

*This guide is maintained alongside the main documentation structure*
*For quick navigation, start with [docs/README.md](./README.md)*
