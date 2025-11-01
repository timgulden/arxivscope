#!/bin/bash

# Fast Tests Runner for DocTrove/DocScope
# Runs all fast tests and provides a summary

echo "🚀 Running Fast Tests for DocTrove/DocScope"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run tests and capture results
run_test_suite() {
    local test_file=$1
    local test_name=$2
    
    echo -e "${YELLOW}Running ${test_name}...${NC}"
    
    if python "$test_file" 2>/dev/null; then
        echo -e "${GREEN}✅ ${test_name} passed${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ ${test_name} failed${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
}

# Run backend tests
if [ -f "doctrove-api/test_business_logic_fast.py" ]; then
    run_test_suite "doctrove-api/test_business_logic_fast.py" "Backend Business Logic Tests"
else
    echo -e "${RED}❌ Backend test file not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Run frontend tests
if [ -f "docscope/test_data_service_fast.py" ]; then
    run_test_suite "docscope/test_data_service_fast.py" "Frontend Data Service Tests"
else
    echo -e "${RED}❌ Frontend test file not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Summary
echo "=============================================="
echo -e "${YELLOW}Test Summary:${NC}"
echo -e "Total test suites: ${TOTAL_TESTS}"
echo -e "Passed: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Failed: ${RED}${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 All fast tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Check the output above.${NC}"
    exit 1
fi 