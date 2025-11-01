#!/usr/bin/env bash

set -euo pipefail

# Simple helper to establish local port forwards to the server.
# Edit SSH_HOST to match your ~/.ssh/config host alias.

SSH_HOST="doctrove-server"

echo "Establishing port forwards to ${SSH_HOST}..."
echo "- Local 127.0.0.1:5001 -> Remote 127.0.0.1:5001 (API)"
echo "- Local 127.0.0.1:8050 -> Remote 127.0.0.1:8050 (Frontend)"
echo "Press Ctrl+C to stop."

exec ssh -N \
  -L 127.0.0.1:5001:127.0.0.1:5001 \
  -L 127.0.0.1:8050:127.0.0.1:8050 \
  "${SSH_HOST}"



