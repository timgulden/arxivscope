# Deployment Documentation

> **Current Environment (October 2025)**: This system has been migrated from a server installation to a local laptop environment. The current setup runs locally with:
> - **API**: Port 5001 (changed from server configuration)
> - **Frontend**: Port 3000 (React, changed from server configuration)
> - **PostgreSQL**: Port 5432 on internal drive (changed from server paths)
> - **Database Location**: `/opt/homebrew/var/postgresql@14` (macOS with Homebrew)
> - **Models**: Stored on internal drive (not external/server paths)
>
> The deployment guides in this section are preserved for reference if server deployment is needed in the future. For current setup information, see [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md).

This section contains deployment guides, server setup instructions, migration procedures, and environment configuration for the DocTrove/DocScope system.

## 🚀 Server Setup

### Platform-Specific Guides
- **[SERVER_DEPLOYMENT_GUIDE.md](./SERVER_DEPLOYMENT_GUIDE.md)** - General server deployment guide
- **[AWS_CLEAN_INSTALL_GUIDE.md](./AWS_CLEAN_INSTALL_GUIDE.md)** - Clean installation on AWS
- **[AWS_MIGRATION_GUIDE.md](./AWS_MIGRATION_GUIDE.md)** - Migration to AWS
- **[AZURE_MIGRATION_SUMMARY.md](./AZURE_MIGRATION_SUMMARY.md)** - Migration to Azure
- **[OPEN_SOURCE_DEPLOYMENT.md](./OPEN_SOURCE_DEPLOYMENT.md)** - Open source deployment guide

### Environment Configuration
- **[MULTI_ENVIRONMENT_SETUP.md](./MULTI_ENVIRONMENT_SETUP.md)** - Multi-environment configuration
- **[COST_OPTIMIZED_DEPLOYMENT.md](./COST_OPTIMIZED_DEPLOYMENT.md)** - Cost-optimized deployment strategies

## 🔄 Migration & Updates

### System Migration
- **[SERVER_MIGRATION_GUIDE.md](./SERVER_MIGRATION_GUIDE.md)** - Server migration procedures
- **[TEAM_DEPLOYMENT_GUIDE.md](./TEAM_DEPLOYMENT_GUIDE.md)** - Team deployment coordination

### Database Migration
- **Database migrations** are handled in the `database/migrations/` folder
- **Backup procedures** are in `database/backup.sh`
- **Recovery procedures** are in `database/recover.sh`

## 🛠️ Deployment Scripts

### Root Level Scripts
- **startup.sh** - Master startup script for all services
- **stop_services.sh** - Stop all running services
- **server-setup.sh** - Server setup automation
- **monitoring-setup.sh** - Monitoring and logging setup

### Component Scripts
- **doctrove-api/start_api.sh** - API server startup
- **docscope/start_docscope.sh** - Frontend startup

## 🔧 Configuration

### Environment Files
- **env.template** - Template for environment configuration
- **env.local.example** - Local development configuration example
- **env.remote.example** - Remote deployment configuration example

### Platform Detection
- **config/linux.sh** - Linux-specific configuration
- **config/macos.sh** - macOS-specific configuration
- **config/windows.ps1** - Windows-specific configuration

## 📋 Deployment Checklist

### Pre-Deployment
1. **Environment Setup**: Configure environment variables
2. **Database Setup**: Ensure PostgreSQL with pgvector is ready
3. **Dependencies**: Install required Python packages
4. **Permissions**: Set correct file ownership and permissions

### Deployment
1. **Code Deployment**: Pull latest code from repository
2. **Service Startup**: Use startup scripts to start services
3. **Health Check**: Verify all services are running
4. **Monitoring**: Ensure monitoring and logging are active

### Post-Deployment
1. **Testing**: Run comprehensive test suite
2. **Performance**: Monitor system performance
3. **Documentation**: Update deployment documentation
4. **Team Communication**: Notify team of deployment status

## 🔗 Related Documentation

- **[Main Documentation Index](../README.md)** - Return to main documentation
- **[Operations Documentation](../OPERATIONS/README.md)** - Operations and monitoring
- **[Component Documentation](../COMPONENTS/README.md)** - Component-specific deployment details

## 🚨 Troubleshooting

### Common Issues
- **Port Conflicts**: Check for port conflicts with `lsof -i :<port>`
- **Permission Issues**: Fix file ownership with `chown` commands
- **Service Failures**: Check service logs and health endpoints
- **Database Issues**: Verify database connectivity and schema

### Recovery Procedures
- **Service Restart**: Use restart scripts for service recovery
- **Database Recovery**: Use database recovery scripts
- **Rollback**: Revert to previous working version if needed

---

*Deployment documentation is maintained by the DevOps team*

