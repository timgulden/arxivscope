#!/usr/bin/env python3
"""
Query Performance Test Runner
Runs the query performance optimization test suite and generates reports.
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def run_performance_tests():
    """Run the query performance optimization tests."""
    print("🚀 DocTrove Query Performance Test Runner")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Change to project root
    project_root = "/opt/arxivscope"
    os.chdir(project_root)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{project_root}/doctrove-api:{env.get('PYTHONPATH', '')}"
    
    # Run the performance tests
    test_file = "tests/performance/test_query_performance_optimization.py"
    
    print(f"Running tests from: {test_file}")
    print()
    
    try:
        # Run tests with verbose output
        result = subprocess.run([
            sys.executable, "-m", "unittest", 
            test_file, "-v"
        ], env=env, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        print("Test Output:")
        print("-" * 30)
        print(result.stdout)
        
        if result.stderr:
            print("Test Errors:")
            print("-" * 30)
            print(result.stderr)
        
        print("Test Summary:")
        print("-" * 30)
        print(f"Return code: {result.returncode}")
        print(f"Success: {'✅' if result.returncode == 0 else '❌'}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def check_prerequisites():
    """Check if prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check if API is running
    try:
        import requests
        api_url = os.getenv('DOCTROVE_API_URL', 'http://localhost:5001/api')
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False
    
    # Check if database is accessible
    try:
        import psycopg2
        from doctrove_api.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASSWORD
        )
        conn.close()
        print("✅ Database is accessible")
    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")
        return False
    
    # Check if query analyzer modules are available
    try:
        sys.path.append('/opt/arxivscope/doctrove-api')
        from query_analyzer import QueryAnalyzer
        from enhanced_business_logic import execute_enhanced_query
        print("✅ Query analyzer modules are available")
    except ImportError as e:
        print(f"⚠️  Query analyzer modules not available: {e}")
        print("   Some tests may be skipped")
    
    print()
    return True

def generate_performance_report():
    """Generate a performance report after tests."""
    print("📊 Generating performance report...")
    
    # Check if query analysis logs exist
    log_files = [
        "/tmp/doctrove_performance.log",
        "/tmp/query_analysis_summary.csv",
        "/tmp/vector_query_performance.csv"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"✅ Found log file: {log_file}")
        else:
            print(f"⚠️  Log file not found: {log_file}")
    
    # Run query analysis if available
    analysis_script = "/opt/arxivscope/scripts/analyze_query_logs.py"
    if os.path.exists(analysis_script):
        try:
            print("\nRunning query analysis...")
            result = subprocess.run([
                sys.executable, analysis_script, "--hours", "1", "--recommendations"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("Query Analysis Results:")
                print("-" * 30)
                print(result.stdout)
            else:
                print(f"Query analysis failed: {result.stderr}")
        except Exception as e:
            print(f"Error running query analysis: {e}")
    else:
        print("⚠️  Query analysis script not found")

def main():
    """Main function."""
    print("Starting query performance test suite...")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please check the issues above.")
        return False
    
    # Run tests
    success = run_performance_tests()
    
    # Generate report
    generate_performance_report()
    
    # Final summary
    print("\n" + "=" * 50)
    if success:
        print("✅ Query performance tests completed successfully!")
        print("📊 Check the logs above for detailed performance metrics")
        print("🔍 Use ./scripts/analyze_query_logs.py for ongoing monitoring")
    else:
        print("❌ Query performance tests failed!")
        print("🔍 Check the test output above for details")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)













