#!/bin/bash

# Comprehensive Test Runner for DocTrove/DocScope
# Runs all test suites from their proper locations
# 
# USAGE: Run from the project root directory (arxivscope-back-end/)
# ./run_comprehensive_tests.sh

echo "🧪 Running Comprehensive Test Suite for DocTrove/DocScope"
echo "=========================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
TOTAL_TEST_SUITES=0
PASSED_TEST_SUITES=0
FAILED_TEST_SUITES=0
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test suite and capture results
run_test_suite() {
    local test_dir=$1
    local test_name=$2
    local test_command=$3
    
    echo -e "${BLUE}🔍 Running ${test_name}...${NC}"
    echo -e "${YELLOW}   Directory: ${test_dir}${NC}"
    echo -e "${YELLOW}   Command: ${test_command}${NC}"
    
    # Change to the test directory
    cd "$test_dir" || {
        echo -e "${RED}❌ Failed to change to directory: ${test_dir}${NC}"
        FAILED_TEST_SUITES=$((FAILED_TEST_SUITES + 1))
        return 1
    }
    
    # Run the tests and capture output
    if eval "$test_command" 2>&1; then
        echo -e "${GREEN}✅ ${test_name} completed successfully${NC}"
        PASSED_TEST_SUITES=$((PASSED_TEST_SUITES + 1))
        
        # Try to extract test counts from pytest output
        if [[ "$test_command" == *"pytest"* ]]; then
            # Look for pytest summary line - capture output more carefully
            local test_output
            test_output=$(eval "$test_command" 2>&1)
            local exit_code=$?
            
            # Only try to parse if the command succeeded
            if [[ $exit_code -eq 0 ]]; then
                # Look for the summary line in the last few lines
                local summary_line=$(echo "$test_output" | tail -5 | grep -E "[0-9]+ (passed|failed)")
                if [[ -n "$summary_line" ]]; then
                    echo -e "${GREEN}   Test output: ${summary_line}${NC}"
                fi
            fi
        fi
    else
        echo -e "${RED}❌ ${test_name} failed${NC}"
        FAILED_TEST_SUITES=$((FAILED_TEST_SUITES + 1))
    fi
    
    echo ""
    
    # Return to project root
    cd - > /dev/null
}

# Ensure we're in the project root
if [[ ! -f "README.md" ]] || [[ ! -d "docscope" ]] || [[ ! -d "doctrove-api" ]]; then
    echo -e "${RED}❌ Error: This script must be run from the project root directory (arxivscope-back-end/)${NC}"
    echo -e "${YELLOW}   Current directory: $(pwd)${NC}"
    echo -e "${YELLOW}   Expected files: README.md, docscope/, doctrove-api/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running from project root: $(pwd)${NC}"
echo ""

# 1. Run main DocScope test suite
if [[ -d "docscope/tests" ]]; then
    run_test_suite "docscope/tests" "Main DocScope Test Suite" "python -m pytest -v --tb=short"
    TOTAL_TEST_SUITES=$((TOTAL_TEST_SUITES + 1))
else
    echo -e "${RED}❌ Main test suite directory not found: docscope/tests${NC}"
    FAILED_TEST_SUITES=$((FAILED_TEST_SUITES + 1))
fi

# 2. Run functional programming component tests
if [[ -d "docscope/components" ]]; then
    # Run the new functional programming tests we created
    run_test_suite "." "Functional Programming Component Tests" "python -m pytest docscope/components/ -v --tb=short"
    TOTAL_TEST_SUITES=$((TOTAL_TEST_SUITES + 1))
else
    echo -e "${RED}❌ Components directory not found: docscope/components${NC}"
    FAILED_TEST_SUITES=$((FAILED_TEST_SUITES + 1))
fi

# 3. Run backend API tests
if [[ -d "doctrove-api" ]]; then
    # Run backend tests
    run_test_suite "." "Backend API Tests" "python -m pytest doctrove-api/ -v --tb=short"
    TOTAL_TEST_SUITES=$((TOTAL_TEST_SUITES + 1))
else
    echo -e "${RED}❌ Backend directory not found: doctrove-api${NC}"
    FAILED_TEST_SUITES=$((FAILED_TEST_SUITES + 1))
fi

# 4. Run performance tests
if [[ -f "tests/performance/test_embedding_performance.py" ]]; then
    run_test_suite "." "Performance Tests" "python tests/performance/test_embedding_performance.py"
    TOTAL_TEST_SUITES=$((TOTAL_TEST_SUITES + 1))
fi

if [[ -f "tests/performance/test_performance.py" ]]; then
    run_test_suite "." "Performance Tests" "python tests/performance/test_performance.py"
    TOTAL_TEST_SUITES=$((TOTAL_TEST_SUITES + 1))
fi

# 5. Run root-level tests (if any remain)
# Note: Most tests have been moved to organized subdirectories

# Summary
echo "=========================================================="
echo -e "${YELLOW}📊 Test Summary:${NC}"
echo -e "Test suites run: ${TOTAL_TEST_SUITES}"
echo -e "Test suites passed: ${GREEN}${PASSED_TEST_SUITES}${NC}"
echo -e "Test suites failed: ${RED}${FAILED_TEST_SUITES}${NC}"

if [[ $TOTAL_TESTS -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}📈 Individual Test Results:${NC}"
    echo -e "Total tests: ${TOTAL_TESTS}"
    echo -e "Tests passed: ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "Tests failed: ${RED}${FAILED_TESTS}${NC}"
fi

echo ""

if [[ $FAILED_TEST_SUITES -eq 0 ]]; then
    echo -e "${GREEN}🎉 All test suites completed successfully!${NC}"
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}🎉 All individual tests passed!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Some individual tests failed, but all suites completed${NC}"
        exit 1
    fi
else
    echo -e "${RED}💥 Some test suites failed. Check the output above.${NC}"
    exit 1
fi
