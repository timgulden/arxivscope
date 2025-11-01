#!/usr/bin/env python3
"""
Test Runner for Event Listener Component
Runs the test suite for the event_listener_functional.py and reports results
"""

import sys
import os
import subprocess
import time

def run_tests():
    """Run the test suite"""
    print("🧪 Running Event Listener Component Test Suite")
    print("=" * 50)
    
    # Change to the embedding-enrichment directory
    os.chdir(os.path.dirname(__file__))
    
    # Run pytest with verbose output
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_event_listener_functional.py", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, timeout=60)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print("=" * 50)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test"""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_event_listener_functional.py", 
            f"::{test_name}",
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, timeout=30)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_tests()
    
    if success:
        print("\n🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test suite failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
