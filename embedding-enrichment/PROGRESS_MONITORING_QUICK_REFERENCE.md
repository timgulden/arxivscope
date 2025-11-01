# Progress Monitoring Quick Reference

## Overview

This document provides quick reference for monitoring the progress of large-scale embedding generation in the DocScope/DocTrove system.

## Quick Commands

### Monitor 1D Embedding Progress
```bash
# Real-time progress monitoring (recommended)
cd embedding-enrichment && python monitor_event_listener.py

# Check event listener logs directly
screen -S embedding_1d -X hardcopy /tmp/event_listener_log.txt
tail -20 /tmp/event_listener_log.txt

# Check if event listener is running
ps aux | grep event_listener_functional
```

### Monitor 2D Embedding Progress
```bash
# Check 2D embedding service status
cd embedding-enrichment && python functional_2d_processor.py --status

# Check if 2D service is running
ps aux | grep functional_2d_processor
```

### Cost Analysis
```bash
# Analyze real token counts and costs
cd embedding-enrichment && python analyze_real_token_counts.py

# Quick cost estimate for 20M embeddings
# Result: ~$95 for 20 million embeddings
```

## Progress Monitoring Solution

### Why This Approach?
- **Database timeouts**: Direct COUNT queries on 17M+ row table are too slow
- **Sampling unreliability**: Sample-based estimates give wildly inaccurate rates
- **Real-time data**: Event listener logs provide actual processing progress
- **Cost accuracy**: Real token analysis vs test case estimates

### Key Files
- `monitor_event_listener.py` - Main progress monitoring script
- `analyze_real_token_counts.py` - Token count and cost analysis
- `event_listener_functional.py` - Database-driven 1D embedding service
- `functional_2d_processor.py` - 2D embedding generation service

### Current Status (as of latest run)
- **1D Embeddings**: Processing at ~95K papers/hour
- **Completion Time**: ~6 days for 13M remaining papers
- **Cost**: ~$95 for 20 million embeddings total
- **Success Rate**: 100% (250 successful, 0 failed per batch)

## Sample Output

### Progress Monitor Output
```
📊 Event Listener Progress Monitor
===================================

📈 Current Status (2025-09-02T00:07:10.216191)
------------------------------
Total Papers: 17,870,457
Full Embeddings: 4,537,998 (25.4%)
Papers Needing Full: 13,332,459
Processed So Far: 51,250
Percentage Complete: 0.4%
Method: event_listener_logs

⚡ Processing Rate
------------------------------
Rate: 94736.8 papers/hour
Time to completion: 5.8 days
```

### Cost Analysis Output
```
📊 Real Token Count Analysis
============================================================
Average title tokens: 30.7
Average abstract tokens: 206.3
Average total tokens per paper: 237.0
Cost per paper: $0.000005
Cost for 20M papers: $94.81
```

## Troubleshooting

### Event Listener Not Running
```bash
# Start the event listener
cd embedding-enrichment
screen -dmS embedding_1d bash -c "python event_listener_functional.py"
```

### No Progress Data
```bash
# Check if event listener is processing
screen -S embedding_1d -X hardcopy /tmp/event_listener_log.txt
grep "Processed.*%" /tmp/event_listener_log.txt | tail -5
```

### Database Connection Issues
```bash
# Test database connection
PGPASSWORD=doctrove_admin psql -h localhost -p 5434 -U doctrove_admin -d doctrove -c "SELECT 1;"
```

## Cost Breakdown

### Token Analysis Results
- **Average tokens per paper**: 237 (title + abstract)
- **Cost per 1K tokens**: $0.00002
- **Cost per paper**: $0.000005
- **Cost for 1M papers**: $4.74
- **Cost for 10M papers**: $47.41
- **Cost for 20M papers**: $94.81

### Comparison with Estimates
- **Test case estimate**: 68 tokens = $27.20 for 20M
- **Real database analysis**: 237 tokens = $94.81 for 20M
- **Difference**: 3.5x higher than estimated
- **Still very reasonable**: Under $100 for 20M embeddings

## Integration with Context Summary

This progress monitoring solution is documented in:
- `CONTEXT_SUMMARY.md` - Main context summary
- `docs/OPERATIONS/EMBEDDING_GENERATION_PERFORMANCE.md` - Performance documentation
- `docs/OPERATIONS/DATABASE_DRIVEN_EVENT_LISTENER_GUIDE.md` - Event listener guide

## Future Improvements

- **Web dashboard**: Real-time web interface for progress monitoring
- **Email alerts**: Notifications when processing completes
- **Historical tracking**: Long-term progress history and trends
- **Performance optimization**: Further rate improvements


