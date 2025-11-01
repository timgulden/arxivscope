# Running OpenAlex Enrichment via SOCKS Proxy

## Overview

Run the enrichment script on AWS, but route all OpenAlex API traffic through your local machine using an SSH SOCKS proxy.

**Benefits:**
- Script runs on AWS (close to database, no SSH tunnel needed)
- API traffic goes through your local machine (bypasses AWS firewall)
- Simple setup with SSH

---

## Setup (One-time)

### Step 1: Create SSH SOCKS Proxy from Local Machine

On your **local machine**, create an SSH connection with dynamic port forwarding:

```bash
# From your local machine:
ssh -D 9050 -C -N arxivscope@your-aws-server-ip

# -D 9050: Create SOCKS proxy on port 9050
# -C: Compress data
# -N: No remote command (just tunnel)
```

**Keep this terminal open** - it creates the proxy tunnel.

To run in background:
```bash
ssh -D 9050 -C -f -N arxivscope@your-aws-server-ip
# -f: Run in background
```

To check if it's running:
```bash
ps aux | grep "ssh -D 9050"
```

---

### Step 2: Install PySocks on AWS

On the **AWS server**, install the PySocks library:

```bash
cd /opt/arxivscope
source arxivscope/bin/activate  # If using venv
pip install PySocks
```

---

### Step 3: Configure Script to Use SOCKS Proxy

The script will automatically detect and use the SOCKS proxy if you set environment variables.

---

## Running the Enrichment

### Test First (100 papers)

```bash
# On AWS server:
cd /opt/arxivscope/embedding-enrichment

# Set proxy environment variables
export SOCKS_PROXY=socks5://localhost:9050

# Run test
python3 openalex_country_enrichment_batch.py --test --email tgulden@rand.org --use-proxy
```

### Full Run (~1 hour)

```bash
# On AWS server:
cd /opt/arxivscope/embedding-enrichment

export SOCKS_PROXY=socks5://localhost:9050

python3 openalex_country_enrichment_batch.py --email tgulden@rand.org --use-proxy
```

---

## How It Works

1. **Local machine** runs SSH with `-D 9050` → creates SOCKS proxy
2. **AWS script** sends API requests to `localhost:9050`
3. **SOCKS proxy** forwards traffic through SSH tunnel to your local machine
4. **Local machine** makes actual API call to OpenAlex
5. **Response** travels back through tunnel to AWS script

```
AWS Server          SSH Tunnel           Local Machine        Internet
┌─────────┐        ┌──────────┐         ┌──────────┐        ┌─────────┐
│ Script  │───────>│  SOCKS   │────────>│ SSH      │───────>│OpenAlex │
│         │<───────│  Proxy   │<────────│ Client   │<───────│   API   │
└─────────┘        └──────────┘         └──────────┘        └─────────┘
                   localhost:9050
```

---

## Troubleshooting

### Test Proxy Connection

```bash
# On AWS, test if proxy works:
curl --socks5 localhost:9050 https://api.openalex.org/works/W2741809807

# Should return JSON instead of 403 error
```

### Proxy Not Working

1. **Check SSH tunnel is running on local machine:**
   ```bash
   # On local machine:
   ps aux | grep "ssh -D 9050"
   ```

2. **Check port 9050 is listening on AWS:**
   ```bash
   # On AWS:
   netstat -ln | grep 9050
   # Should show: tcp 0 0 127.0.0.1:9050 0.0.0.0:* LISTEN
   ```

3. **Test with curl first before running Python script**

### Connection Drops

The SSH tunnel might disconnect. Monitor with:
```bash
# On local machine, keep tunnel alive with:
ssh -D 9050 -C -N -o ServerAliveInterval=60 arxivscope@your-aws-server
```

---

## Alternative: HTTP Proxy (If SOCKS Doesn't Work)

If SOCKS proxy has issues, you can run a simple HTTP proxy on your local machine:

### On Local Machine:

```bash
# Install tinyproxy or squid, or use Python:
python3 -m http.server 8888 --bind 0.0.0.0

# Then create SSH reverse tunnel:
ssh -R 8888:localhost:8888 arxivscope@your-aws-server
```

### On AWS:

```bash
export HTTP_PROXY=http://localhost:8888
export HTTPS_PROXY=http://localhost:8888
python3 openalex_country_enrichment_batch.py --email tgulden@rand.org
```

---

## Clean Up

When done, kill the SSH tunnel:

```bash
# On local machine:
# If running in foreground: Ctrl+C

# If running in background:
pkill -f "ssh -D 9050"
```


