# DocScope Documentation Index

## 🎯 Choose Your Path [Current]

### **I'm new to DocScope - where do I start?** [Current]
- **[README.md](README.md)** - Main entry point with quick start commands
- **[QUICK_START.md](QUICK_START.md)** - Complete setup guide for individual development

### **I need to deploy this on a server for my team** [Current]
- **[TEAM_DEPLOYMENT_GUIDE.md](TEAM_DEPLOYMENT_GUIDE.md)** - Server deployment and team management

### **I need to manage running services** [Current]
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Essential commands and troubleshooting
- **[STARTUP_GUIDE.md](STARTUP_GUIDE.md)** - Detailed startup procedures and options
- **[SERVER_GIT_PULL_GUIDE.md](SERVER_GIT_PULL_GUIDE.md)** - Repository updates and permission management

### **I need to set up multiple development environments** [Current]
- **[MULTI_ENVIRONMENT_SETUP.md](MULTI_ENVIRONMENT_SETUP.md)** - Multi-environment development setup and port management
- **[QUICK_STARTUP.md](QUICK_STARTUP.md)** - Quick startup with multi-environment options

### **I need to ingest data or optimize performance** [Current]
- **[OPENALEX_INGESTION_GUIDE.md](OPENALEX_INGESTION_GUIDE.md)** - Data ingestion from various sources
- **[PERFORMANCE_OPTIMIZATION_GUIDE.md](PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Database optimization and indexes
- **[EMBEDDING_GENERATION_PERFORMANCE.md](OPERATIONS/EMBEDDING_GENERATION_PERFORMANCE.md)** - Embedding generation optimization

### **I'm a developer working on the code** [Current]
- **[docscope/DEVELOPER_QUICK_REFERENCE.md](docscope/DEVELOPER_QUICK_REFERENCE.md)** - Development workflow
- **[doctrove-api/API_DOCUMENTATION.md](doctrove-api/API_DOCUMENTATION.md)** - Complete API reference

## 📋 Documentation Categories [Current]

### **Getting Started** [Current]
| Document | Purpose | Audience |
|----------|---------|----------|
| [README.md](README.md) | Main entry point and overview | Everyone |
| [QUICK_START.md](QUICK_START.md) | Complete setup guide | Individual developers |
| [TEAM_DEPLOYMENT_GUIDE.md](TEAM_DEPLOYMENT_GUIDE.md) | Server deployment | System administrators |

### **Service Management** [Current]
| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Essential commands and troubleshooting | All users |
| [STARTUP_GUIDE.md](STARTUP_GUIDE.md) | Detailed startup procedures | Advanced users |
| [SERVER_GIT_PULL_GUIDE.md](SERVER_GIT_PULL_GUIDE.md) | Repository updates and permission management | System administrators |

### **Development Environment** [Current]
| Document | Purpose | Audience |
|----------|---------|----------|
| [MULTI_ENVIRONMENT_SETUP.md](MULTI_ENVIRONMENT_SETUP.md) | Multi-environment development setup | Developers working locally and remotely |
| [QUICK_STARTUP.md](QUICK_STARTUP.md) | Quick startup with multi-environment options | Developers needing fast setup |

### **Data & Performance** [Current]
| Document | Purpose | Audience |
|----------|---------|----------|
| [OPENALEX_INGESTION_GUIDE.md](OPENALEX_INGESTION_GUIDE.md) | Data ingestion workflows | Data engineers |
| [PERFORMANCE_OPTIMIZATION_GUIDE.md](PERFORMANCE_OPTIMIZATION_GUIDE.md) | Database optimization | System administrators |
| [EMBEDDING_GENERATION_PERFORMANCE.md](OPERATIONS/EMBEDDING_GENERATION_PERFORMANCE.md) | Embedding generation optimization | Data engineers |

### **Development** [Current]
| Document | Purpose | Audience |
|----------|---------|----------|
| [docscope/DEVELOPER_QUICK_REFERENCE.md](docscope/DEVELOPER_QUICK_REFERENCE.md) | Development workflow | Developers |
| [docscope/CALLBACK_ARCHITECTURE_DESIGN.md](docscope/CALLBACK_ARCHITECTURE_DESIGN.md) | Callback architecture and data fetching | Developers working on UI |
| [doctrove-api/API_DOCUMENTATION.md](doctrove-api/API_DOCUMENTATION.md) | API reference | API users |

## 🚀 Quick Decision Tree

```
Are you setting up DocScope for the first time?
├─ Yes, for individual development → QUICK_START.md
├─ Yes, for team/server deployment → TEAM_DEPLOYMENT_GUIDE.md
└─ No, I need to manage services → QUICK_REFERENCE.md

Are you having trouble with services?
├─ Services won't start → QUICK_REFERENCE.md (Troubleshooting section)
├─ Need to restart/stop services → QUICK_REFERENCE.md (Service Management)
├─ Need to update code from repository → SERVER_GIT_PULL_GUIDE.md
└─ Need detailed startup options → STARTUP_GUIDE.md

Are you working with data?
├─ Need to ingest papers → OPENALEX_INGESTION_GUIDE.md
├─ Need to optimize performance → PERFORMANCE_OPTIMIZATION_GUIDE.md
└─ Need API documentation → doctrove-api/API_DOCUMENTATION.md

Are you working on the UI/callbacks?
├─ Need to understand callback architecture → docscope/CALLBACK_ARCHITECTURE_DESIGN.md
├─ Need to understand data flow → docscope/CALLBACK_ARCHITECTURE_DESIGN.md
└─ Need to debug callback issues → docscope/CALLBACK_ARCHITECTURE_DESIGN.md
```

## 📝 Documentation Standards

- **README.md** - Always start here
- **QUICK_REFERENCE.md** - Keep this open while working
- **TEAM_DEPLOYMENT_GUIDE.md** - For server deployments only
- **STARTUP_GUIDE.md** - For advanced startup scenarios
- **Specialized guides** - Only when needed for specific tasks

## 🔄 Keeping Documentation Updated

- All guides reference the same startup script (`startup.sh`)
- Commands are tested and verified
- Team deployment uses the same commands as individual setup
- Troubleshooting sections are regularly updated based on common issues 