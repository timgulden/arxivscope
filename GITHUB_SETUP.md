# GitHub Setup Instructions

## Option 1: HTTPS with Personal Access Token (Recommended)

### Step 1: Generate Personal Access Token on GitHub

1. Go to GitHub: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "DocTrove CLI"
4. Select scopes:
   - ✅ `repo` (full control of private repositories)
   - ✅ `workflow` (if you want to use GitHub Actions)
5. Click "Generate token"
6. **Copy the token immediately** - you won't see it again!

### Step 2: Configure Git to Use Token

**Method A: Use Token as Password (Easiest)**
When you push, Git will prompt for credentials:
- Username: `timgulden`
- Password: `<paste your token here>`

**Method B: Store Token in Git Credential Helper**
```bash
git config --global credential.helper osxkeychain
# Then on first push, enter your token as password
# macOS will store it securely
```

**Method C: Use Token in URL (Less Secure)**
```bash
cd /Users/tgulden/Documents/DocTrove/arxivscope
git remote set-url origin https://YOUR_TOKEN@github.com/timgulden/arxivscope.git
```

## Option 2: SSH Keys (More Secure, Better for Frequent Use)

### Step 1: Generate SSH Key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location (~/.ssh/id_ed25519)
# Enter a passphrase (recommended) or press Enter for no passphrase
```

### Step 2: Add SSH Key to GitHub

1. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. Go to GitHub: https://github.com/settings/keys
3. Click "New SSH key"
4. Title: "MacBook - DocTrove"
5. Paste the key content
6. Click "Add SSH key"

### Step 3: Test SSH Connection

```bash
ssh -T git@github.com
# Should say: "Hi timgulden! You've successfully authenticated..."
```

### Step 4: Update Git Remote to Use SSH

```bash
cd /Users/tgulden/Documents/DocTrove/arxivscope
git remote set-url origin git@github.com:timgulden/arxivscope.git
```

## Quick Start (Choose One)

### For HTTPS Token:
```bash
cd /Users/tgulden/Documents/DocTrove/arxivscope
git remote set-url origin https://github.com/timgulden/arxivscope.git
git push -u origin main
# When prompted:
# Username: timgulden
# Password: <paste your personal access token>
```

### For SSH:
```bash
# First: Generate key and add to GitHub (see Option 2 above)
cd /Users/tgulden/Documents/DocTrove/arxivscope
git remote set-url origin git@github.com:timgulden/arxivscope.git
git push -u origin main
```

## Which Should You Choose?

- **Personal Access Token (HTTPS)**: Easier to set up, good for occasional use
- **SSH Key**: More secure, better for frequent git operations, no repeated password prompts

Both work equally well! Choose based on your preference.

