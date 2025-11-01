# Server Git Pull Guide

## Overview

This guide explains how to properly pull updates from the Git repository on the DocScope server, addressing the permission issues that arise due to the shared installation directory and service user setup.

## The Problem

The DocScope installation is set up with:
- **Installation directory**: `/opt/arxivscope/`
- **Service user**: `arxivscope` (owns the files)
- **Git operations**: Require `tgulden` user (has SSH access to repository)

This creates a permission conflict when trying to pull updates, as Git needs to modify files owned by `arxivscope` but can only be run by `tgulden`.

**⚠️ CRITICAL**: After any Git operation, the files are owned by `tgulden`, but the services need to run as `arxivscope`. Without fixing permissions, the entire system will fail.

## Solution: Proper Pull Process

### Method 1: Temporary Ownership Change (Recommended)

```bash
# 1. SSH to server as tgulden
ssh tgulden@10.22.198.120

# 2. Navigate to installation directory
cd /opt/arxivscope

# 3. Temporarily change ownership to tgulden for Git operations
sudo chown -R tgulden:tgulden .

# 4. Pull the latest changes
git pull

# 5. Restore ownership to arxivscope
sudo chown -R arxivscope:arxivscope .

# 6. Verify permissions are correct
ls -la /opt/arxivscope/
```

### Method 2: Force Reset and Pull (Use when there are conflicts)

```bash
# 1. SSH to server as tgulden
ssh tgulden@10.22.198.120

# 2. Navigate to installation directory
cd /opt/arxivscope

# 3. Temporarily change ownership
sudo chown -R tgulden:tgulden .

# 4. Force reset any local changes and clean untracked files
git reset --hard HEAD
git clean -fd

# 5. Pull the latest changes
git pull

# 6. Restore ownership to arxivscope
sudo chown -R arxivscope:arxivscope .
```

### Method 3: Using the Update Script (Future)

Once the `scripts/update_server.sh` script is properly set up on the server:

```bash
# SSH to server and run the update script
ssh tgulden@10.22.198.120 "cd /opt/arxivscope && ./scripts/update_server.sh"
```

## Verification Steps

After pulling, verify that:

1. **Ownership is correct**:
   ```bash
   ls -la /opt/arxivscope/ | head -5
   # Should show: arxivscope arxivscope
   ```

2. **Key files are accessible**:
   ```bash
   sudo -u arxivscope test -w /opt/arxivscope && echo "Permissions OK"
   ```

3. **Services can start**:
   ```bash
   cd /opt/arxivscope
   ./startup.sh --background
   ```

## Common Issues and Solutions

### Issue: "dubious ownership in repository"
```bash
# Solution: Add safe directory
git config --global --add safe.directory /opt/arxivscope
```

### Issue: "Permission denied" during pull
```bash
# Solution: Ensure tgulden owns the directory temporarily
sudo chown -R tgulden:tgulden /opt/arxivscope
git pull
sudo chown -R arxivscope:arxivscope /opt/arxivscope
```

### Issue: "Your local changes would be overwritten"
```bash
# Solution: Stash or reset local changes
git stash  # or
git reset --hard HEAD
git clean -fd
```

### Issue: "Host key verification failed" (when running as arxivscope)
```bash
# Solution: Use tgulden user for Git operations
# The arxivscope user doesn't have SSH access to the repository
```

## Best Practices

1. **ALWAYS restore ownership** after Git operations - this is CRITICAL
2. **Test service startup** after pulling updates
3. **Check logs** for any issues after updates
4. **Use Method 1** for routine updates
5. **Use Method 2** when there are conflicts or issues
6. **Never skip the permission fix** - services will fail without it

## One-Liner Commands

### Quick Pull (Method 1)
```bash
ssh tgulden@10.22.198.120 "cd /opt/arxivscope && sudo chown -R tgulden:tgulden . && git pull && sudo chown -R arxivscope:arxivscope ."
```

### Force Pull (Method 2)
```bash
ssh tgulden@10.22.198.120 "cd /opt/arxivscope && sudo chown -R tgulden:tgulden . && git reset --hard HEAD && git clean -fd && git pull && sudo chown -R arxivscope:arxivscope ."
```

### ⚠️ IMPORTANT: Always Fix Permissions After Pull

**Every Git pull operation MUST include permission restoration:**
```bash
sudo chown -R arxivscope:arxivscope .
```

Without this step, the arxivscope user won't be able to:
- Start services (`./startup.sh`)
- Write to log files
- Access configuration files
- Run any scripts

## Future Improvements

1. **Automated update script**: Enhance `scripts/update_server.sh` to handle permissions properly
2. **Git hooks**: Set up post-merge hooks to automatically fix permissions
3. **Deployment pipeline**: Integrate with CI/CD for automated deployments
4. **Permission management**: Consider using ACLs or different ownership strategies

## Related Documentation

- `TEAM_DEPLOYMENT_GUIDE.md` - Overall server setup and management
- `QUICK_REFERENCE.md` - Common commands and troubleshooting
- `scripts/update_server.sh` - Automated update script (when available) 