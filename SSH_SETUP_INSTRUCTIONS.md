# SSH Key Setup for GitHub - Step by Step

## Overview

We'll generate an SSH key pair on your Mac, then add the public key to GitHub. This will allow you to push/pull without entering credentials every time.

## Step-by-Step Instructions

### Step 1: Generate SSH Key

Run this command (replace the email with yours):

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

**What to expect:**
1. It will ask: "Enter file in which to save the key"
   - **Just press Enter** to use the default location

2. It will ask: "Enter passphrase"
   - You can enter a passphrase for extra security (recommended)
   - OR just press Enter twice for no passphrase
   - If you use a passphrase, you'll need to enter it when using the key

3. It will generate the key and show something like:
   ```
   Your public key has been saved in /Users/tgulden/.ssh/id_ed25519.pub
   ```

### Step 2: Start SSH Agent (Optional but Recommended)

This lets you enter your passphrase once per session:

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### Step 3: Copy Your Public Key

Run this to display your public key:

```bash
cat ~/.ssh/id_ed25519.pub
```

**Copy the entire output** - it will look like:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...very long string... your_email@example.com
```

### Step 4: Add Key to GitHub

1. Go to: https://github.com/settings/keys
2. Click the green "New SSH key" button
3. Fill in:
   - **Title**: "MacBook - DocTrove" (or any name you like)
   - **Key**: Paste the key you copied in Step 3
   - **Key type**: Should auto-detect as "Authentication Key"
4. Click "Add SSH key"
5. You may be prompted for your GitHub password

### Step 5: Test Connection

Test that it works:

```bash
ssh -T git@github.com
```

**Expected output:**
```
Hi timgulden! You've successfully authenticated, but GitHub does not provide shell access.
```

If you see that, you're all set! ✅

### Step 6: Update Git Remote to Use SSH

Change the remote URL from HTTPS to SSH:

```bash
cd /Users/tgulden/Documents/DocTrove/arxivscope
git remote set-url origin git@github.com:timgulden/arxivscope.git
git remote -v  # Verify it changed
```

### Step 7: Push Your Code

Now you can push without credentials:

```bash
git push -u origin main
```

You should see output like:
```
Enumerating objects: X, done.
Counting objects: X% (X/X), done.
...
To github.com:timgulden/arxivscope.git
 * [new branch]      main -> main
```

## Troubleshooting

### "Permission denied"
- Make sure you added the key to GitHub correctly
- Try `ssh-add ~/.ssh/id_ed25519` again

### "Host key verification failed"
- First time connecting to GitHub, you may need to add it:
  ```bash
  ssh-keyscan github.com >> ~/.ssh/known_hosts
  ```

### "The authenticity of host can't be established"
- Type "yes" when prompted - this is normal the first time

### Forgot your passphrase
- You can't recover it, but you can generate a new key

## What's Next?

Once this works, you'll never need to enter credentials for git operations with this repo!

The SSH key stays on your machine and is automatically used by Git. Much easier than tokens!

