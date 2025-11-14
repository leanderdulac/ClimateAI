#!/bin/bash

###############################################################################
# Test Suite Runner for ClimateAI
# Runs pytest with various configurations for comprehensive testing
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
TEST_DIR="server/tests"
COVERAGE_DIR="coverage_html"
TEST_LOG="test_results.log"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest not found! Install with:"
        echo "pip install -r server/requirements-test.txt"
        exit 1
    fi
    print_success "pytest found: $(pytest --version)"
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    if pytest \
        "${TEST_DIR}/unit" \
        -v \
        -m unit \
        --tb=short \
        --cov=server \
        --cov-report=html:${COVERAGE_DIR} \
        --cov-report=term-missing \
        2>&1 | tee -a "${TEST_LOG}"; then
        print_success "Unit tests passed"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    if pytest \
        "${TEST_DIR}/integration" \
        -v \
        -m integration \
        --tb=short \
        2>&1 | tee -a "${TEST_LOG}"; then
        print_success "Integration tests passed"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    print_header "Running Performance Tests (Slow)"
    
    if pytest \
        "${TEST_DIR}/performance" \
        -v \
        -m "performance or slow" \
        --tb=short \
        2>&1 | tee -a "${TEST_LOG}"; then
        print_success "Performance tests passed"
        return 0
    else
        print_error "Performance tests failed"
        return 1
    fi
}

# Run specific test file
run_specific_test() {
    local test_file="$1"
    
    print_header "Running: $test_file"
    
    if pytest "${test_file}" -v --tb=short; then
        print_success "Test passed: $test_file"
        return 0
    else
        print_error "Test failed: $test_file"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    print_header "Running All Tests"
    
    if pytest \
        "${TEST_DIR}" \
        -v \
        --tb=short \
        --cov=server \
        --cov-report=html:${COVERAGE_DIR} \
        --cov-report=term-missing \
        --cov-report=json:coverage.json \
        --cov-fail-under=80 \
        2>&1 | tee "${TEST_LOG}"; then
        print_success "All tests passed"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Run tests without coverage
run_fast_tests() {
    print_header "Running Fast Tests (No Coverage)"
    
    if pytest \
        "${TEST_DIR}" \
        -v \
        --tb=short \
        -m "not slow" \
        2>&1 | tee -a "${TEST_LOG}"; then
        print_success "Fast tests passed"
        return 0
    else
        print_error "Fast tests failed"
        return 1
    fi
}

# Run tests matching pattern
run_tests_matching() {
    local pattern="$1"
    
    print_header "Running tests matching: $pattern"
    
    if pytest \
        "${TEST_DIR}" \
        -v \
        -k "$pattern" \
        --tb=short \
        2>&1 | tee -a "${TEST_LOG}"; then
        print_success "Tests matched: $pattern"
        return 0
    else
        print_error "Tests failed for: $pattern"
        return 1
    fi
}

# Generate coverage report
generate_coverage_report() {
    print_header "Generating Coverage Report"
    
    if [ -d "${COVERAGE_DIR}" ]; then
        print_success "Coverage report generated in ${COVERAGE_DIR}/"
        print_info "Open with: open ${COVERAGE_DIR}/index.html"
        return 0
    else
        print_error "Coverage report not found"
        return 1
    fi
}

# Display test statistics
show_statistics() {
    print_header "Test Statistics"
    
    if [ -f "${TEST_LOG}" ]; then
        local total=$(grep -c "PASSED\|FAILED" "${TEST_LOG}" || echo "0")
        local passed=$(grep -c "PASSED" "${TEST_LOG}" || echo "0")
        local failed=$(grep -c "FAILED" "${TEST_LOG}" || echo "0")
        
        echo "Total Tests: ${total}"
        echo "Passed: ${GREEN}${passed}${NC}"
        echo "Failed: ${RED}${failed}${NC}"
        
        if [ "$failed" -eq 0 ]; then
            print_success "All tests passed!"
        fi
    fi
}

# Display help
show_help() {
    cat << EOF
${BLUE}ClimateAI Test Suite Runner${NC}

Usage: $0 [command] [options]

Commands:
    all              Run all tests with coverage (default)
    unit             Run unit tests only
    integration      Run integration tests only
    performance      Run performance tests (slow)
    fast             Run tests without slow tests or coverage
    specific FILE    Run specific test file
    match PATTERN    Run tests matching pattern (e.g., test_health)
    coverage         Generate coverage report
    stats            Show test statistics
    help             Show this help message

Options:
    --verbose        Show verbose output
    --quiet          Minimal output
    --no-cov         Skip coverage reporting
    --pdb            Drop into debugger on failures

Examples:
    $0                           # Run all tests
    $0 unit                      # Run unit tests
    $0 specific server/tests/unit/test_health.py
    $0 match "test_health"
    $0 fast                      # Quick test run
    $0 coverage                  # Generate coverage report

EOF
}

# Main script
main() {
    # Clear log
    > "${TEST_LOG}"
    
    # Check prerequisites
    check_pytest
    
    print_info "ClimateAI Test Suite"
    print_info "Workspace: $(pwd)"
    print_info "Python: $(python --version)"
    
    # Parse command
    local command="${1:-all}"
    
    case "$command" in
        all)
            run_all_tests
            generate_coverage_report
            show_statistics
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        performance)
            run_performance_tests
            ;;
        fast)
            run_fast_tests
            ;;
        specific)
            if [ -z "$2" ]; then
                print_error "Please specify test file"
                exit 1
            fi
            run_specific_test "$2"
            ;;
        match)
            if [ -z "$2" ]; then
                print_error "Please specify test pattern"
                exit 1
            fi
            run_tests_matching "$2"
            ;;
        coverage)
            generate_coverage_report
            ;;
        stats)
            show_statistics
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
