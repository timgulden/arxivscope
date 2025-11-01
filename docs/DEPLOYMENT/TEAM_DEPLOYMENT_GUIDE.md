# DocScope Team Deployment Guide

## Overview

This guide describes how to deploy DocScope in a team-friendly environment where multiple team members can manage and maintain the system.

## Key Benefits of Team Deployment

1. **Shared Installation**: Installed in `/opt/arxivscope/` - accessible to all team members
2. **Dedicated Service User**: Runs as `arxivscope` user, not tied to any individual
3. **Standard Startup Script**: Uses the existing `startup.sh` script for service management
4. **Team Permissions**: Any team member can start/stop/check services
5. **Standard Location**: Follows Linux filesystem hierarchy standards

## Installation

### Prerequisites
- Root/sudo access on the server
- Git access to the repository
- At least 10GB free disk space

### Installation Steps

1. **Clone the repository** (as any user):
   ```bash
   git clone <repository-url> arxivscope-back-end
   cd arxivscope-back-end
   ```

2. **Run the team setup script** (requires sudo):
   ```bash
   sudo ./scripts/server_setup_team.sh
   ```

3. **Add team members** to the arxivscope group:
   ```bash
   sudo usermod -a -G arxivscope <username>
   ```

## Team Management Commands

Once installed, any team member can use these commands:

### Service Management (Using Existing Startup Script)
```bash
# Navigate to installation directory
cd /opt/arxivscope

# Start all services in background mode
./startup.sh --with-enrichment --background

# Restart all services (stops existing, starts new)
./startup.sh --with-enrichment --background --restart

# Stop all services
./stop_services.sh

# Check service status
./check_services.sh

# Start only API and frontend (no enrichment)
./startup.sh --background

# Start in foreground mode (for debugging)
./startup.sh --with-enrichment
```

### Logs and Monitoring
```bash
# View startup script logs
tail -f /opt/arxivscope/startup.log

# Check running processes
ps aux | grep -E "(api\.py|event_listener\.py|docscope\.app)"

# Check system resources
htop
df -h

# Check port usage
lsof -i :5001  # API port
lsof -i :8050  # Frontend port
```

### Database Management
```bash
# Connect to database
sudo -u postgres psql -d doctrove

# Backup database
sudo -u postgres pg_dump doctrove > backup.sql

# Restore database
sudo -u postgres psql -d doctrove < backup.sql
```

## File Locations

- **Installation**: `/opt/arxivscope/`
- **Logs**: `/opt/arxivscope/startup.log` and individual service logs
- **Configuration**: `/opt/arxivscope/config/`
- **Database**: PostgreSQL data directory
- **Python Environment**: `/opt/arxivscope/arxivscope/`

## Adding New Team Members

1. **Add user to arxivscope group**:
   ```bash
   sudo usermod -a -G arxivscope <new-username>
   ```

2. **User must log out and back in** for group changes to take effect

3. **Test access**:
   ```bash
   cd /opt/arxivscope
   ./check_services.sh
   ```

## Updating the Installation

### Code Updates
```bash
# Navigate to installation directory
cd /opt/arxivscope

# Pull latest changes
git pull origin main

# Restart services to apply changes
./startup.sh --with-enrichment --background --restart
```

### Database Schema Updates
```bash
cd /opt/arxivscope
sudo -u postgres psql -d doctrove -f new_schema.sql
```

### Performance Index Updates
```bash
cd /opt/arxivscope
./scripts/apply_performance_indexes.sh
```

## Troubleshooting

### Service Won't Start
```bash
# Check service status
./check_services.sh

# Check logs
tail -f /opt/arxivscope/startup.log

# Check permissions
ls -la /opt/arxivscope/
```

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep doctrove
```

### Permission Issues
```bash
# Check group membership
groups <username>

# Re-add user to group
sudo usermod -a -G arxivscope <username>
```

## Security Considerations

1. **Service User**: The `arxivscope` user has minimal permissions
2. **File Permissions**: Sensitive files are protected
3. **Database Access**: Only postgres user has direct database access
4. **Network**: Services bind to localhost by default

## Backup and Recovery

### Regular Backups
```bash
# Create backup script
sudo crontab -e

# Add daily backup (example)
0 2 * * * sudo -u postgres pg_dump doctrove > /backups/doctrove_$(date +\%Y\%m\%d).sql
```

### Disaster Recovery
1. **Restore from backup**:
   ```bash
   sudo -u postgres dropdb doctrove
   sudo -u postgres createdb doctrove
   sudo -u postgres psql -d doctrove < backup.sql
   ```

2. **Reinstall if needed**:
   ```bash
   sudo ./scripts/server_setup_team.sh
   ```

## Performance Monitoring

### Key Metrics to Monitor
- **Database size**: `sudo -u postgres psql -d doctrove -c "SELECT pg_size_pretty(pg_database_size('doctrove'));"`
- **Service memory usage**: `ps aux | grep arxivscope`
- **Disk space**: `df -h /opt/arxivscope/`
- **Database connections**: `sudo -u postgres psql -d doctrove -c "SELECT count(*) FROM pg_stat_activity;"`

### Performance Tuning
- **Database indexes**: Run performance index script after major data loads
- **Memory**: Adjust PostgreSQL shared_buffers in postgresql.conf
- **Disk I/O**: Monitor with `iostat` and `iotop`

## Support and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check service status and logs
2. **Monthly**: Review disk usage and database size
3. **Quarterly**: Update system packages and review security

### Getting Help
- Check logs: `tail -f /opt/arxivscope/startup.log`
- Review this guide
- Check the main project documentation
- Contact the development team

## Migration from User-Specific Installation

If you have an existing installation in a user's home directory:

1. **Backup current data**:
   ```bash
   sudo -u postgres pg_dump doctrove > migration_backup.sql
   ```

2. **Run team setup**:
   ```bash
   sudo ./scripts/server_setup_team.sh
   ```

3. **Restore data**:
   ```bash
   sudo -u postgres psql -d doctrove < migration_backup.sql
   ```

4. **Update any configuration files** to point to new locations

5. **Test the new installation** before removing the old one

## Quick Reference

### Most Common Commands
```bash
# Start everything
cd /opt/arxivscope && ./startup.sh --with-enrichment --background

# Restart everything  
cd /opt/arxivscope && ./startup.sh --with-enrichment --background --restart

# Stop everything
cd /opt/arxivscope && ./stop_services.sh

# Check status
cd /opt/arxivscope && ./check_services.sh
```

### Emergency Commands
```bash
# Force kill all processes
pkill -f "api\.py|event_listener\.py|docscope\.app"

# Check what's using ports
lsof -i :5001
lsof -i :8050

# Restart PostgreSQL
sudo systemctl restart postgresql
``` 