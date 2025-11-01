#!/usr/bin/env python3
"""
Production workflow for embedding enrichment service.
Demonstrates daily incremental processing, annual full rebuild, and system monitoring.
"""

import sys
import os
import subprocess
import logging
from datetime import datetime
from config import get_adaptive_batch_sizes, get_batch_sizing_rationale

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Run a command and log the result."""
    logger.debug(f"Running: {description}")
    logger.debug(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.debug(f"✅ {description} completed successfully")
            if result.stdout:
                logger.debug(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"❌ {description} failed")
            logger.error(f"Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        logger.error(f"❌ {description} failed with exception: {e}")
        return False
    
    return True

def check_system_health():
    """Check system health and dependencies."""
    logger.debug("🔍 Checking system health...")
    
    # Check if main script exists
    if not os.path.exists("main.py"):
        logger.error("❌ main.py not found")
        return False
    
    # Check if UMAP model exists and get its size
    model_path = "umap_model.pkl"
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        logger.debug(f"✅ UMAP model found: {size_mb:.1f} MB")
    else:
        logger.warning("⚠️  No UMAP model found (will be created on first run)")
    
    # Check database connectivity
    logger.debug("🔍 Testing database connectivity...")
    if not run_command("python main.py --mode status", "Database connectivity test"):
        logger.error("❌ Database connectivity failed")
        return False
    
    logger.debug("✅ System health check passed")
    return True

def get_dataset_info():
    """Get information about the dataset and recommended batch sizes."""
    logger.debug("📊 Getting dataset information...")
    
    # Run status to get dataset size
    result = subprocess.run("python main.py --mode status", shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        output = result.stdout
        logger.debug("Dataset information:")
        for line in output.split('\n'):
            if any(keyword in line for keyword in ['papers', 'batch', 'rationale']):
                logger.debug(f"  {line.strip()}")
    
    return True

def run_daily_incremental():
    """Run daily incremental processing."""
    logger.debug("🔄 Starting daily incremental processing...")
    
    # Get dataset info first
    get_dataset_info()
    
    # Run incremental processing
    if run_command("python main.py --mode incremental", "Daily incremental processing"):
        logger.debug("✅ Daily processing completed successfully")
        return True
    else:
        logger.error("❌ Daily processing failed")
        return False

def run_annual_rebuild():
    """Run annual full rebuild."""
    logger.debug("🔄 Starting annual full rebuild...")
    
    # Get dataset info first
    get_dataset_info()
    
    # Run full rebuild
    if run_command("python main.py --mode full-rebuild", "Annual full rebuild"):
        logger.debug("✅ Annual rebuild completed successfully")
        return True
    else:
        logger.error("❌ Annual rebuild failed")
        return False

def run_tests():
    """Run all tests."""
    logger.debug("🧪 Running tests...")
    
    # Run unit tests
    if run_command("python test_enrichment.py", "Unit tests"):
        logger.debug("✅ Unit tests passed")
    else:
        logger.error("❌ Unit tests failed")
        return False
    
    # Run integration tests (with mocked database)
    logger.debug("⚠️  Integration tests require mocked database - skipping in production")
    
    return True

def show_adaptive_batch_sizing():
    """Show adaptive batch sizing recommendations for different dataset sizes."""
    logger.debug("📊 Adaptive Batch Sizing Recommendations:")
    
    test_sizes = [1000, 5000, 10000, 50000, 100000, 500000, 1000000]
    
    for size in test_sizes:
        first_batch, subsequent_batch = get_adaptive_batch_sizes(size)
        rationale = get_batch_sizing_rationale(size)
        
        logger.debug(f"  {size:,} papers:")
        logger.debug(f"    First batch: {first_batch:,}")
        logger.debug(f"    Subsequent batches: {subsequent_batch:,}")
        logger.debug(f"    Rationale: {rationale}")
        logger.debug("")

def main():
    if len(sys.argv) != 2:
        print("Usage: python production_workflow.py <command>")
        print("Commands:")
        print("  monitor    - Check system health and status")
        print("  daily      - Run daily incremental processing")
        print("  annual     - Run annual full rebuild")
        print("  test       - Run all tests")
        print("  batch-info - Show adaptive batch sizing recommendations")
        sys.exit(1)
    
    command = sys.argv[1]
    
    print(f"🚀 Production Workflow: {command}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    if command == "monitor":
        success = check_system_health()
        if success:
            get_dataset_info()
        sys.exit(0 if success else 1)
        
    elif command == "daily":
        success = run_daily_incremental()
        sys.exit(0 if success else 1)
        
    elif command == "annual":
        success = run_annual_rebuild()
        sys.exit(0 if success else 1)
        
    elif command == "test":
        success = run_tests()
        sys.exit(0 if success else 1)
        
    elif command == "batch-info":
        show_adaptive_batch_sizing()
        sys.exit(0)
        
    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 