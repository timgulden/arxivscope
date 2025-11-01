# DocScope Quick Reference Guide

> **Current Environment (October 2025)**: This system runs on a local laptop environment. API on port 5001, React Frontend on port 3000, PostgreSQL on port 5432. All data is stored on the internal drive. See [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md) for current setup details.

## 🚀 Essential Commands

### Starting the System
```bash
# Manual startup (recommended for development)
# Terminal 1 - API
cd doctrove-api && source ../venv/bin/activate && python api.py

# Terminal 2 - React Frontend
cd docscope-platform/services/docscope/react && npm run dev

# Terminal 3 - Enrichment (optional)
cd embedding-enrichment && source ../venv/bin/activate && python event_listener.py
```

### Service Management
```bash
# Check all services status
./check_services.sh

# Stop all services
./stop_services.sh

# Check running processes
ps aux | grep -E "(api\.py|event_listener\.py|vite|docscope\.app)"

# Check port usage
lsof -i :5001 -i :3000 -i :8050
```

### Health Checks
```bash
# Check API health
curl http://localhost:5001/api/health

# Check system-wide health
curl http://localhost:5001/api/health/system

# Check React frontend
curl http://localhost:3000

# Check legacy Dash frontend (if running)
curl http://localhost:8050
```

## 🌐 Access Points

- **React Frontend**: http://localhost:3000 (recommended)
- **Legacy Dash Frontend**: http://localhost:8050 (frozen, reference only)
- **API**: http://localhost:5001
- **API Health**: http://localhost:5001/api/health

## 📁 Project Structure
```
./                              # Project root
├── docscope/                   # Dash frontend application
├── doctrove-api/              # Flask API server
├── embedding-enrichment/      # 2D embedding generation
├── doc-ingestor/              # Document ingestion pipeline
├── startup.sh                 # Main startup script
├── stop_services.sh           # Stop all services
└── check_services.sh          # Check service status
```

## 🔧 Common Issues & Solutions

### Database Connection Issues
```bash
# Check database connectivity (local laptop, trust authentication)
psql -d doctrove -c "SELECT COUNT(*) FROM doctrove_papers;"

# Check PostgreSQL is running (macOS with Homebrew)
brew services list | grep postgresql
```

### Services Won't Start
```bash
# Check if ports are in use
lsof -i :5001  # API
lsof -i :3000  # React Frontend
lsof -i :8050  # Legacy Dash Frontend

# Check startup logs
tail -f startup.log

# Force kill processes (emergency)
pkill -f "api\.py|event_listener\.py|vite|docscope\.app"
```

### Configuration Issues
```bash
# Check .env.local file exists
cat .env.local

# Verify environment variables
echo $NEW_API_BASE_URL
echo $NEW_UI_PORT
echo $UMAP_MODEL_PATH

# Check database configuration in .env.local
grep DB_ .env.local
```

## 📊 Database Management

### Connect to Database
```bash
# Local laptop (trust authentication)
psql -d doctrove

# Check database location
psql -d doctrove -c "SHOW data_directory;"
```

### Backup/Restore
```bash
# Backup database
pg_dump doctrove > backup.sql

# Restore database
psql -d doctrove < backup.sql

# Database location (internal drive)
# macOS with Homebrew: /opt/homebrew/var/postgresql@14
```

## 🔍 Troubleshooting

### API Not Responding
1. Check if API is running: `ps aux | grep api.py`
2. Check API logs: `tail -f api.log`
3. Check database connection
4. Restart API: `./startup.sh --background --restart`

### Frontend Not Loading
1. **React Frontend**: Check if running: `ps aux | grep vite` or `lsof -i :3000`
2. **Legacy Dash**: Check if running: `ps aux | grep docscope.app` or `lsof -i :8050`
3. Check frontend logs (terminal where frontend was started)
4. Ensure API is running first (port 5001)
5. Check browser console for errors
6. Verify `.env.local` configuration

### Enrichment System Issues
1. Check enrichment logs: `tail -f enrichment.log`
2. Verify database triggers are installed
3. Check if papers have embeddings: `SELECT COUNT(*) FROM doctrove_papers WHERE doctrove_embedding IS NOT NULL;`

## 📝 Development Workflow

### Standard Workflow
1. **Terminal 1**: Start API: `cd doctrove-api && source ../venv/bin/activate && python api.py`
2. **Terminal 2**: Start React Frontend: `cd docscope-platform/services/docscope/react && npm run dev`
3. **Terminal 3** (optional): Start Enrichment: `cd embedding-enrichment && source ../venv/bin/activate && python event_listener.py`
4. Open browser to http://localhost:3000
5. Make changes to code (React frontend auto-reloads with Vite)
6. Restart API if needed (Ctrl+C and restart)

### Debug Mode
```bash
# Start in foreground for debugging
./startup.sh --with-enrichment

# Check specific service logs
tail -f api.log
tail -f frontend.log
tail -f enrichment.log
```

## 🆘 Emergency Commands

```bash
# Force kill all processes
pkill -f "api\.py|event_listener\.py|vite|docscope\.app"

# Restart PostgreSQL (macOS with Homebrew)
brew services restart postgresql@14

# Clear all logs
rm -f *.log

# Reset database (DANGEROUS - backup first!)
dropdb doctrove
createdb doctrove
psql -d doctrove -f doctrove_schema.sql
``` 