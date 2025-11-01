# Cursor Cache Cleanup (Targeted) — Keep Working Setup Intact

Purpose: Clear a corrupted chat/tab in Cursor with minimal impact. Start with selective cache removal; escalate only if needed.

---

## 1) Close Cursor Completely

- Quit the app fully (ensure no background processes remain).

---

## 2) Selective Cache Clearing (Recommended First)

Delete only cache directories. This preserves settings, extensions, remotes, and most state.

### macOS
```bash
cd ~/Library/Application\ Support/Cursor
rm -rf User/Cache
rm -rf "Service Worker/CacheStorage"
rm -rf "Service Worker/ScriptCache"
rm -rf "User/Code Cache"
```

### Windows (PowerShell)
```powershell
cd "$env:APPDATA\Cursor"
Remove-Item -Recurse -Force "User/Cache"
Remove-Item -Recurse -Force "Service Worker/CacheStorage"
Remove-Item -Recurse -Force "Service Worker/ScriptCache"
Remove-Item -Recurse -Force "User/Code Cache"
```

### Linux
```bash
cd ~/.config/Cursor
rm -rf User/Cache
rm -rf "Service Worker/CacheStorage"
rm -rf "Service Worker/ScriptCache"
rm -rf "User/Code Cache"
```

Then reopen Cursor and test the problematic chat/tab.

---

## 3) Chat-Specific Reset (If Corruption Persists)

This targets local chat storage while leaving other settings intact.

### macOS
```bash
cd ~/Library/Application\ Support/Cursor
rm -rf "User/IndexedDB"
rm -rf "User/Local Storage"
rm -rf "User/Session Storage"
```

### Windows (PowerShell)
```powershell
cd "$env:APPDATA\Cursor"
Remove-Item -Recurse -Force "User/IndexedDB"
Remove-Item -Recurse -Force "User/Local Storage"
Remove-Item -Recurse -Force "User/Session Storage"
```

### Linux
```bash
cd ~/.config/Cursor
rm -rf "User/IndexedDB"
rm -rf "User/Local Storage"
rm -rf "User/Session Storage"
```

Reopen Cursor and check if the corrupted tab is gone.

---

## 4) Full Profile Reset (Last Resort)

Back up first; this clears all local state. You will need to sign in again and reapply remotes.

### macOS
```bash
cd ~/Library/Application\ Support
mv Cursor Cursor_backup_$(date +%Y%m%d_%H%M%S)
```

### Windows (PowerShell)
```powershell
$ts = Get-Date -Format yyyyMMdd_HHmmss
Rename-Item "$env:APPDATA\Cursor" "Cursor_backup_$ts"
```

### Linux
```bash
cd ~/.config
mv Cursor Cursor_backup_$(date +%Y%m%d_%H%M%S)
```

Launch Cursor; it will create a fresh profile.

---

## 5) Recovery Checklist (After Any Reset)

1. Sign into Cursor
2. Ensure your SSH key exists on the laptop (`~/.ssh/id_ed25519`); add to agent if needed
3. Add SSH config alias (example):
```sshconfig
Host doctrove-vpn
    HostName 10.22.198.120
    User arxivscope
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 6
```
4. Re-establish forwards (choose free local ports):
```bash
ssh -f -N -L 127.0.0.1:5004:127.0.0.1:5001 -L 127.0.0.1:8053:127.0.0.1:8051 doctrove-vpn
```
5. Verify:
```bash
curl http://127.0.0.1:5004/api/health
# Open http://127.0.0.1:8053 in a browser
```
6. In Cursor, connect to the remote workspace at `/opt/arxivscope`

---

## 6) Notes & Tips

- If a forward port is in use locally, pick another (e.g., 5006/8055).
- Keep a copy of your `~/.ssh/config` and private key backed up securely.
- This document lives at `docs/DEPLOYMENT/CURSOR_CACHE_CLEANUP.md` for offline reference.

