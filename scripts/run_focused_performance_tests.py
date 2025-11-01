#!/usr/bin/env python3
"""
Focused Performance Test Runner
Runs the most critical query performance tests for optimization.
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    """Run focused performance tests."""
    print("🎯 DocTrove Focused Performance Test Runner")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print("Testing the most critical query performance scenarios")
    print()
    
    # Change to project root
    project_root = "/opt/arxivscope"
    os.chdir(project_root)
    
    # Run the focused performance tests
    test_file = "tests/performance/test_query_performance_focused.py"
    
    print(f"Running focused tests from: {test_file}")
    print()
    
    try:
        # Run tests with verbose output
        result = subprocess.run([
            sys.executable, test_file
        ], timeout=300)  # 5 minute timeout
        
        print("\nTest Summary:")
        print("-" * 30)
        print(f"Return code: {result.returncode}")
        print(f"Success: {'✅' if result.returncode == 0 else '❌'}")
        
        if result.returncode == 0:
            print("\n🎉 All focused performance tests passed!")
            print("📊 Check the output above for performance metrics")
            print("🔍 Use ./scripts/analyze_query_logs.py for detailed analysis")
        else:
            print("\n❌ Some focused performance tests failed!")
            print("🔍 Check the test output above for details")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)













