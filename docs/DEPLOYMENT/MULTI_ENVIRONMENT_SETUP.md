# Multi-Environment Development Setup

> **Note**: This document reflects the previous multi-environment setup (local development vs remote server). 
> The system is currently running on a single local laptop environment (migrated from AWS server to local laptop in October 2025).
> This guide is preserved for potential future use if multi-environment setup is needed again.
> 
> For current setup information, see [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md)

This guide explains how to set up and use different development environments for DocScope/DocTrove without breaking repo syncs.

## **Overview**

The system now supports multiple development environments using environment variables:
- **Local Development**: Ports 5002/8051 (avoiding conflicts with remote)
- **Remote Development**: Ports 5001/8050 (standard ports)
- **Environment-specific configuration** that doesn't get committed to the repo

## **Quick Setup**

### **1. Local Development (Ports 5002/8051)**
```bash
# Copy the example file
cp env.local.example .env.local

# Start the system (will use ports 5002/8051)
./startup.sh --restart --background
```

### **2. Remote Development (Ports 5001/8050)**
```bash
# Copy the example file
cp env.remote.example .env.remote

# Start the system (will use ports 5001/8050)
./startup.sh --restart --background
```

## **Environment Files**

### **`.env.local` (Local Development)**
```bash
# Use different ports for local development
DOCTROVE_API_PORT=5002
DOCSCOPE_PORT=8051
DOCTROVE_API_URL=http://localhost:5002/api
```

### **`.env.remote` (Remote Development)**
```bash
# Use standard ports for remote development
DOCTROVE_API_PORT=5001
DOCSCOPE_PORT=8050
DOCTROVE_API_URL=http://localhost:5001/api
```

## **How It Works**

### **1. Configuration Files**
- **`docscope/config/settings.py`**: Reads from environment variables
- **`doctrove-api/api.py`**: Uses `DOCTROVE_API_PORT` environment variable
- **`docscope/app.py`**: Uses `DOCSCOPE_PORT` environment variable

### **2. Startup Scripts**
- **`startup.sh`**: Loads environment variables and uses them for port checking
- **Port availability checks**: Use environment variables instead of hardcoded values
- **Service URLs**: Display the actual ports being used

### **3. Environment Loading**
- **`.env` files**: Loaded automatically by startup scripts
- **Fallback values**: Default to standard ports (5001/8050) if not specified
- **Command line override**: Still supported for manual port specification

## **Benefits**

✅ **No Port Conflicts**: Local and remote can run simultaneously  
✅ **Repo Safe**: Environment files are in .gitignore  
✅ **Easy Switching**: Just change .env file and restart  
✅ **Clear Separation**: Local vs remote environments are distinct  
✅ **No Code Changes**: Same codebase works in both environments  

## **Usage Examples**

### **Local Development Workflow**
```bash
# 1. Set up local environment
cp env.local.example .env.local

# 2. Start local services
./startup.sh --restart --background

# 3. Access local services
# API: http://localhost:5002
# Frontend: http://localhost:8051

# 4. Test your changes locally
# 5. Commit and push to repo
```

### **Remote Development Workflow**
```bash
# 1. Set up remote environment
cp env.remote.example .env.remote

# 2. Start remote services
./startup.sh --restart --background

# 3. Access remote services
# API: http://localhost:5001
# Frontend: http://localhost:8050

# 4. Test production-like environment
```

## **Troubleshooting**

### **Port Already in Use**
```bash
# Check what's using the port
lsof -i :5001
lsof -i :8050

# Use different ports in your .env file
DOCTROVE_API_PORT=5003
DOCSCOPE_PORT=8052
```

### **Environment Not Loading**
```bash
# Check if .env file exists
ls -la .env*

# Verify environment variables are set
echo $DOCTROVE_API_PORT
echo $DOCSCOPE_PORT
```

### **Services Not Starting**
```bash
# Check logs for port conflicts
tail -f api.log
tail -f frontend.log

# Verify port availability
./startup.sh --restart --background
```

## **Advanced Configuration**

### **Custom Ports**
```bash
# Use any available ports
DOCTROVE_API_PORT=8001
DOCSCOPE_PORT=9001
```

### **Multiple Local Environments**
```bash
# Development
cp env.local.example .env.dev
# Modify ports in .env.dev

# Testing
cp env.local.example .env.test
# Modify ports in .env.test
```

### **Environment-Specific Settings**
```bash
# Add other environment-specific configurations
TARGET_RECORDS_PER_VIEW=1000  # Smaller dataset for testing
DEBOUNCE_DELAY_SECONDS=0.1    # Slower response for debugging
```

## **Best Practices**

1. **Always use environment files** for port configuration
2. **Never commit .env files** to the repo
3. **Use descriptive names** for different environments
4. **Test in both environments** before committing
5. **Document any environment-specific requirements**

## **Migration from Old Setup**

If you were previously using hardcoded ports:

1. **Create appropriate .env file** for your current environment
2. **Restart services** to pick up new configuration
3. **Verify ports are working** as expected
4. **Update any hardcoded URLs** in your browser bookmarks

This setup ensures you can develop locally and remotely without conflicts while keeping your repo clean and syncable! 🚀
