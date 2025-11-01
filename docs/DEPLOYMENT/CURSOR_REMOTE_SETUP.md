# Cursor Remote Setup: Laptop → Server Environment

This guide documents how to configure Cursor on a laptop to work against the server environment for this repository, and how to fully restore the setup after a local profile reset.

Use this when:
- You need to reconfigure Cursor after cache/profile corruption.
- You are onboarding a new laptop to the existing server environment.

---

## 1) Prerequisites (Laptop)

- Cursor installed and signed in
- Git installed
- OpenSSH client available (`ssh`, `ssh-keygen`)

Recommended: Back up local Cursor profile before changes
- macOS: `~/Library/Application Support/Cursor/`
- Windows: `%APPDATA%\Cursor\` and `%LOCALAPPDATA%\Cursor\User`
- Linux: `~/.config/Cursor/` and `~/.config/Cursor/User`

---

## 1.1) Pre-flight Verification (No Profile Changes)

Use this to confirm you have everything needed before clearing any local caches:

1. Confirm SSH key exists on laptop:
   ```bash
   ls -l ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.pub 2>/dev/null || echo "Create a key with: ssh-keygen -t ed25519 -C 'laptop-cursor'"
   ```

2. Test basic SSH to server (replace host alias or hostname):
   ```bash
   ssh doctrove-server "hostname && whoami && ls -ld /opt/arxivscope"
   ```

3. Test port forwards temporarily from a separate terminal (leave running):
   ```bash
   ssh -N \
     -L 127.0.0.1:5001:127.0.0.1:5001 \
     -L 127.0.0.1:8050:127.0.0.1:8050 \
     doctrove-server
   ```

4. From the laptop, verify API/Frontend via forwarded ports:
   ```bash
   curl -s http://127.0.0.1:5001/api/health | head -c 200 && echo
   # Then open http://127.0.0.1:8050 in a browser
   ```

If these checks pass, you can safely proceed knowing you can reconnect after any local profile reset.

---

## 2) SSH Access to Server

1. Generate an SSH key on the laptop (if you do not already have one):
   ```bash
   ssh-keygen -t ed25519 -C "laptop-cursor"
   # Press enter to accept defaults; set a passphrase if desired
   ```

2. Add the public key to the server user's `~/.ssh/authorized_keys`:
   ```bash
   cat ~/.ssh/id_ed25519.pub | ssh <user>@<server-hostname-or-ip> 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys'
   ```

3. Configure laptop `~/.ssh/config` for easy access and port forwards:
   ```
   Host doctrove-server
       HostName <server-hostname-or-ip>
       User <server-username>
       IdentityFile ~/.ssh/id_ed25519
       ServerAliveInterval 30
       ServerAliveCountMax 6
       ForwardAgent yes
       # API (remote 5001 → local 5001)
       LocalForward 127.0.0.1:5001 127.0.0.1:5001
       # Frontend (remote 8050 → local 8050)
       LocalForward 127.0.0.1:8050 127.0.0.1:8050
       # Optional alternates if using local-style ports remotely
       # LocalForward 127.0.0.1:5002 127.0.0.1:5002
       # LocalForward 127.0.0.1:8051 127.0.0.1:8051
       # Optional DB (only if allowed)
       # LocalForward 127.0.0.1:5432 127.0.0.1:5432
   ```

4. Test SSH connectivity from the laptop:
   ```bash
   ssh doctrove-server "hostname && whoami && ls -ld /opt/arxivscope"
   ```

---

## 3) Open the Remote Workspace in Cursor

Two common approaches; pick one:

- SSH Remote Filesystem (recommended)
  1. In Cursor, open the Command Palette and choose the SSH/Remote option (varies by version) or use the SSH filesystem URI.
  2. Connect to `doctrove-server` and set the workspace folder to `/opt/arxivscope`.
  3. Ensure the integrated terminal opens on the server with shell set to `/bin/bash` and CWD `/opt/arxivscope`.

- Git clone locally + SSH terminal into server (hybrid)
  - Keep a local clone for quick reference, but do all terminal actions inside a Cursor SSH terminal connected to the server and opened at `/opt/arxivscope`.

Confirm you can view files like `CONTEXT_SUMMARY.md` and `docs/README.md` within Cursor.

---

## 4) Environment Configuration (Server)

Use the multi-environment setup to avoid port conflicts and facilitate local vs remote usage. See `docs/DEPLOYMENT/MULTI_ENVIRONMENT_SETUP.md`.

1. Choose your environment file on the server root (`/opt/arxivscope`):
   ```bash
   # For remote/staging (standard ports 5001/8050)
   cp env.remote.example .env.remote
   # Or for local-style ports
   cp env.local.example .env.local
   ```

2. Confirm ports configured as expected in the `.env.*` file you chose:
   - Remote: `DOCTROVE_API_PORT=5001`, `DOCSCOPE_PORT=8050`
   - Local-style: `DOCTROVE_API_PORT=5002`, `DOCSCOPE_PORT=8051`

3. Ensure database is reachable on the server (PostgreSQL + pgvector).

---

## 5) Start/Stop Services (Server)

Preferred automated startup:
```bash
./startup.sh --with-enrichment --background
```

Common alternatives:
```bash
# Restart everything
./startup.sh --with-enrichment --background --restart

# Stop services
./stop_services.sh
```

Manual control (when troubleshooting):
```bash
# API
cd doctrove-api && python api.py

# Frontend (from project root)
python -m docscope.app
```

Health checks:
```bash
./check_services.sh
curl http://localhost:5001/api/health
curl http://localhost:5001/api/stats
```

If port-forwarding is configured in SSH, you can reach the server’s API/UI via the same localhost ports on the laptop.

---

## 5.1) Helper: Port-Forwarding Script (Laptop)

We include a helper script you can run on the laptop to establish the forwards in one command. Adjust the `SSH_HOST` to your alias.

Path: `scripts/ssh_forward_doctrove.sh`

Usage:
```bash
chmod +x scripts/ssh_forward_doctrove.sh
./scripts/ssh_forward_doctrove.sh
```

This runs `ssh -N -L 5001:5001 -L 8050:8050 doctrove-server` so you can test `http://localhost:5001` and `http://localhost:8050` from the laptop.

---

## 6) Verifying the Remote Session in Cursor

- Integrated terminal shows prompt on the server and `pwd` is `/opt/arxivscope`.
- `python -V` is the server’s interpreter; virtualenv active if applicable.
- Running `ls` shows repo files on the server, not the laptop.
- API/Frontend accessible on laptop via forwarded `http://localhost:5001` and `http://localhost:8050`.

Optional: smoke tests
```bash
./run_comprehensive_tests.sh
curl "http://localhost:5001/api/papers?fields=doctrove_title&limit=1"
```

---

## 7) Recovery After Cursor Profile Reset (Laptop)

If you must clear/rename your Cursor profile on the laptop, use this to fully restore access:

1. Back up the old profile folder, then launch Cursor (it will create a new one) and sign in.
2. Recreate `~/.ssh/config` entries (or copy from backup) for `doctrove-server`.
3. Re-add your SSH private key to `~/.ssh/` (and `ssh-add` if using an agent).
4. Reconnect in Cursor to the SSH target and open `/opt/arxivscope`.
5. Open a terminal in Cursor; verify you are on the server and in the correct directory.
6. If needed, re-establish port forwards by connecting via `ssh doctrove-server` in a side terminal; or rely on SSH config when Cursor connects.
7. Start services as needed with `./startup.sh --with-enrichment --background`.
8. Verify API and frontend via forwarded ports.

Tip: Keep a one-file checklist in the repo that you can reference even if local profile data is gone. We maintain `session_logs/session_latest.md` as an independent note.

---

## 8) Optional Hardening & Convenience

- Add multiple `Host` entries in `~/.ssh/config` for dev vs prod with different forwards.
- Use separate `.env.*` files on the server for local-style vs standard ports.
- Create small helper scripts on the laptop to open SSH with required forwards.
- Keep a minimal local copy of this repo for documentation reference, while doing all execution on the server.

---

## 9) Common Pitfalls

- Frontend started by running `docscope/app.py` directly instead of module: always use `python -m docscope.app` from the project root.
- API assumed to be on port 5000: use 5001 (or 5002 if using local-style env).
- Missing `.env.*` file: startup scripts won’t pick correct ports.
- Port-forwarding not active: endpoints unreachable from the laptop; reconnect SSH or verify `~/.ssh/config` forwards.

---

## 10) Quick Restore Checklist

On the laptop after a Cursor reset:
1. Restore or recreate SSH keys and `~/.ssh/config` (Host `doctrove-server`).
2. Connect from Cursor to `doctrove-server` and open `/opt/arxivscope`.
3. Confirm terminal is on server and `pwd` is `/opt/arxivscope`.
4. Ensure port forwards (5001, 8050) are active.
5. Start services: `./startup.sh --with-enrichment --background`.
6. Verify: `curl http://localhost:5001/api/health` and open `http://localhost:8050`.

You are now fully restored to the working environment.


