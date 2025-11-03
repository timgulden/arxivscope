# Virtual Environment Python Binary Fix

## Problem
The venv's Python binary (`venv/bin/python3`) has broken library paths pointing to `@executable_path/../Python3`, which doesn't exist. This causes the error:
```
dyld: Library not loaded: @executable_path/../Python3
  Referenced from: <...> /venv/bin/python3
  Reason: tried: '/venv/Python3' (no such file)
```

## Permanent Fix
Updated `doctrove.sh` to use system Python (`/usr/bin/python3`) with the venv's site-packages in `PYTHONPATH` instead of activating the venv.

### Updated Commands in `doctrove.sh`:

**API:**
```bash
API_CMD="cd ${API_DIR} && PYTHONPATH=${VENV_SITE_PACKAGES}:\$PYTHONPATH /usr/bin/python3 api.py"
```

**Enrichment Workers:**
```bash
EMB_CMD="cd ${ENRICH_DIR} && PYTHONPATH=${VENV_SITE_PACKAGES}:\$PYTHONPATH /usr/bin/python3 event_listener.py"
EMB2D_CMD="cd ${ENRICH_DIR} && PYTHONPATH=${VENV_SITE_PACKAGES}:\$PYTHONPATH /usr/bin/python3 queue_2d_worker.py --batch-size 1000 --sleep 5"
```

Where `VENV_SITE_PACKAGES="${VENV_DIR}/lib/python3.9/site-packages"`

## Manual Startup (if needed)
If you need to start the API manually, use:
```bash
cd arxivscope/doctrove-api
PYTHONPATH=../venv/lib/python3.9/site-packages:$PYTHONPATH /usr/bin/python3 api.py
```

## Future: Recreate Venv (Optional)
If you want to fix the venv itself rather than work around it:
```bash
cd arxivscope
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r doc-ingestor/requirements.txt
pip install -r embedding-enrichment/requirements.txt
pip install -r doctrove-api/requirements.txt
```
Then revert `doctrove.sh` to use `source ${VENV_DIR}/bin/activate && python api.py`

## Status
✅ Fix applied to `doctrove.sh`  
✅ API can be started with `./doctrove.sh start`  
✅ Fix is permanent and will persist across restarts

