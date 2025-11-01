# OpenAI Account Setup - Billing & Rate Limits

**Date**: 2025-01-22  
**Status**: Waiting for billing setup

## Current Situation

You have a new OpenAI account with a valid API key configured, but:
- Account may not have billing/credit card set up yet
- Rate limits may be effectively zero until billing is authorized
- Getting 429 "Too Many Requests" errors in testing

## What's Working

✅ **API Key Configuration**: Successfully configured in `.env.local`  
✅ **Code Migration**: All hardcoded keys removed, using environment-based config  
✅ **Services Running**: API and frontend running successfully  
✅ **Existing Embeddings**: ~1.53M papers already have embeddings (semantic search works!)

## What's Blocked

❌ **New Embedding Generation**: Will fail with 429 until billing is set up  
❌ **LLM Features**: SQL generation and cluster summaries blocked

## Good News!

**You don't need OpenAI working immediately!** 

- Your existing 1.53M embeddings are already in the database
- Semantic search works with existing embeddings
- Only ~1.39M new papers need embeddings (when you're ready)
- Cost will be ~$83 for the remaining embeddings

## Setting Up OpenAI Billing

The OpenAI website can be confusing. Here's where to go:

### Option 1: Direct Billing Link
Try this direct link: https://platform.openai.com/account/billing/overview

### Option 2: Navigation
1. Go to https://platform.openai.com/
2. Click your profile (top right)
3. Look for "Billing" or "Settings" → "Billing"
4. You should see options to:
   - Add payment method (credit card)
   - Set spending limits
   - View usage

### Option 3: Dashboard
1. Go to https://platform.openai.com/dashboard
2. Look for "Billing" in the left sidebar
3. Click "Payment methods" or "Billing settings"

### What to Look For
- "Payment methods" or "Add payment method" button
- "Usage-based billing" or "Pay as you go" option
- Any "Upgrade" or "Add credits" buttons

### Common Issues
- **Button not visible**: Your account might need email verification first
- **No billing section**: Check if you're on the right plan
- **Always hit OpenAI Support**: They're usually very responsive

## Temporary Workarounds

### Disable OpenAI Features Temporarily

If you want to avoid error messages while setting up billing, you can disable OpenAI features:

Edit `arxivscope/.env.local`:
```bash
USE_OPENAI_EMBEDDINGS=false  # Disables new embedding generation
USE_OPENAI_LLM=false         # Disables LLM features
```

Then restart services:
```bash
cd /Users/tgulden/Documents/DocTrove/arxivscope
./services.sh restart
```

**Impact**: 
- Semantic search still works with existing embeddings ✅
- No new embeddings generated ⚠️
- LLM features disabled ⚠️

### Or Leave It Enabled

The system will just log errors about rate limits, but existing features continue working. Your call!

## Testing After Billing Setup

Once you have billing set up:

1. Wait 5-10 minutes for the rate limits to reset
2. Run the test script:
```bash
cd /Users/tgulden/Documents/DocTrove/arxivscope
source venv/bin/activate
python test_openai_config.py
```

You should see:
```
✅ SUCCESS! Generated embedding with 1536 dimensions
```

## Cost Management

Once billing is set up, you might want to set spending limits:

1. Go to https://platform.openai.com/account/billing/overview
2. Look for "Spending limits" or "Usage limits"
3. Set a monthly limit (e.g., $100 for testing)

This prevents unexpected charges.

## Next Steps

**Immediate**: 
- Set up billing at OpenAI (when convenient)
- For now, semantic search works with existing embeddings

**After billing is ready**:
- Test configuration works
- Run enrichment workers for remaining papers
- Enjoy full DocTrove functionality

## Resources

- OpenAI Billing: https://platform.openai.com/account/billing/overview
- OpenAI Docs: https://platform.openai.com/docs
- OpenAI Support: Check platform.openai.com for contact info

## Questions?

The migration itself is **complete and working**. We're just waiting on OpenAI account activation with billing. Your system will work perfectly once that's set up!

