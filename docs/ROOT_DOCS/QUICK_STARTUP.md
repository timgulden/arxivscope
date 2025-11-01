# Quick Startup Guide

> **Current Environment (October 2025)**: This system runs on a local laptop environment. API on port 5001, React Frontend on port 3000, PostgreSQL on port 5432. All data is stored on the internal drive. See [CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md) for current setup details.
>
> For detailed guidance, see:
> - `../DEVELOPMENT/QUICK_START.md` - Comprehensive setup guide
> - `../DEVELOPMENT/STARTUP_GUIDE.md` - Detailed startup procedures
> - `../DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md` - Historical multi-environment info (preserved for reference)

## Quick Start (Current Setup)

**Local laptop environment with `.env.local` configuration:**

### Manual Startup (Recommended for Development)
```bash
# Terminal 1 - API Server
cd doctrove-api
source ../venv/bin/activate
python api.py
# API runs on http://localhost:5001

# Terminal 2 - React Frontend
cd docscope-platform/services/docscope/react
npm run dev
# Frontend runs on http://localhost:3000

# Terminal 3 - Enrichment (Optional)
cd embedding-enrichment
source ../venv/bin/activate
python event_listener.py
```

**Configuration**: Uses `.env.local` file (see `env.local.example` for template)

---

## Access Points

- **React Frontend**: http://localhost:3000 (recommended)
- **Legacy Dash Frontend**: http://localhost:8050 (frozen, reference only)
- **API**: http://localhost:5001
- **API Health**: http://localhost:5001/api/health
- **System Health**: http://localhost:5001/api/health/system

## Prerequisites

- PostgreSQL database `doctrove` running on port 5432 (internal drive)
- Python virtual environment activated
- `.env.local` file configured (from `env.local.example` template)
- Node.js installed (for React frontend)

## Stop the System

```bash
./stop_services.sh
```

Or press `Ctrl+C` if you started with `./startup.sh`

## Check System Status

```bash
./check_services.sh
```

This will check the health of all services and show their status.

## Common Issues

- **Wrong port**: API runs on 5001, React Frontend on 3000, Legacy Dash on 8050
- **Database**: Make sure PostgreSQL is running on port 5432 (internal drive) with `doctrove` database
- **Configuration**: Ensure `.env.local` file exists and is properly configured
- **Virtual environment**: Activate virtual environment before starting Python services (`source venv/bin/activate`)
- **React frontend**: Ensure Node.js dependencies are installed (`npm install` in React directory)

## Logs

- API logs: Check terminal where API was started
- React Frontend logs: Check terminal where `npm run dev` was started
- Enrichment logs: Check terminal where event listener was started

---

**For detailed troubleshooting and comprehensive guides, see:**
- **[docs/DEVELOPMENT/STARTUP_GUIDE.md](../DEVELOPMENT/STARTUP_GUIDE.md)** - Detailed startup procedures
- **[docs/DEVELOPMENT/QUICK_START.md](../DEVELOPMENT/QUICK_START.md)** - Comprehensive setup guide
- **[CONTEXT_SUMMARY.md](../../CONTEXT_SUMMARY.md)** - Current environment overview 