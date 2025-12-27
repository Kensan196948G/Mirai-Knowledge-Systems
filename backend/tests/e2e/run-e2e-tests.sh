#!/bin/bash

###############################################################################
# E2E Test Execution Script for Mirai Knowledge Systems
#
# This script runs all Playwright E2E scenario tests and generates reports.
#
# Usage:
#   ./tests/e2e/run-e2e-tests.sh [options]
#
# Options:
#   --headed         Run tests in headed mode (visible browser)
#   --debug          Run tests in debug mode
#   --ui             Run tests in UI mode
#   --scenario N     Run specific scenario only (1-5)
#   --report         Show HTML report after tests
#   --no-server      Skip starting the web server (assumes it's already running)
#   --help           Show this help message
#
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
HEADED=""
DEBUG=""
UI=""
SCENARIO=""
SHOW_REPORT=false
SKIP_SERVER=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

###############################################################################
# Functions
###############################################################################

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Mirai Knowledge Systems - E2E Test Suite${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_usage() {
    cat << EOF
Usage: $0 [options]

Options:
  --headed         Run tests in headed mode (visible browser)
  --debug          Run tests in debug mode
  --ui             Run tests in UI mode
  --scenario N     Run specific scenario only (1-5)
  --report         Show HTML report after tests
  --no-server      Skip starting the web server
  --help           Show this help message

Scenarios:
  1 - Knowledge Lifecycle (creation to publication)
  2 - Approval Flow (approve/reject/request changes)
  3 - Search and View (search, filter, view)
  4 - Incident Report (create, update, close)
  5 - Expert Consultation (ask, answer, feedback)

Examples:
  # Run all tests in headless mode
  $0

  # Run with visible browser
  $0 --headed

  # Run only scenario 1
  $0 --scenario 1

  # Debug specific scenario
  $0 --scenario 2 --debug

  # Run all and show report
  $0 --report

EOF
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"

    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js is not installed${NC}"
        exit 1
    fi

    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Error: npm is not installed${NC}"
        exit 1
    fi

    # Check if package.json exists
    if [ ! -f "$PROJECT_ROOT/package.json" ]; then
        echo -e "${RED}Error: package.json not found${NC}"
        exit 1
    fi

    # Check if node_modules exists, if not run npm install
    if [ ! -d "$PROJECT_ROOT/node_modules" ]; then
        echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
        cd "$PROJECT_ROOT"
        npm install
    fi

    # Check if Playwright is installed
    if [ ! -d "$PROJECT_ROOT/node_modules/@playwright" ]; then
        echo -e "${YELLOW}Installing Playwright...${NC}"
        cd "$PROJECT_ROOT"
        npm install @playwright/test
        npx playwright install
    fi

    echo -e "${GREEN}✓ All dependencies are satisfied${NC}"
    echo ""
}

setup_environment() {
    echo -e "${YELLOW}Setting up test environment...${NC}"

    # Create reports directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/tests/reports"

    # Set environment variables
    export NODE_ENV=test
    export BASE_URL="${BASE_URL:-http://localhost:8000}"

    if [ "$SKIP_SERVER" = true ]; then
        export SKIP_WEBSERVER=true
    fi

    echo -e "${GREEN}✓ Environment configured${NC}"
    echo "  - BASE_URL: $BASE_URL"
    echo "  - Reports: $PROJECT_ROOT/tests/reports"
    echo ""
}

run_tests() {
    cd "$PROJECT_ROOT"

    local test_args=""

    # Add headed mode if requested
    if [ -n "$HEADED" ]; then
        test_args="$test_args --headed"
    fi

    # Add debug mode if requested
    if [ -n "$DEBUG" ]; then
        test_args="$test_args --debug"
    fi

    # Add UI mode if requested
    if [ -n "$UI" ]; then
        test_args="$test_args --ui"
    fi

    # Run specific scenario or all scenarios
    if [ -n "$SCENARIO" ]; then
        case $SCENARIO in
            1)
                echo -e "${BLUE}Running Scenario 1: Knowledge Lifecycle${NC}"
                npx playwright test tests/e2e/scenario1_knowledge_lifecycle.spec.js $test_args
                ;;
            2)
                echo -e "${BLUE}Running Scenario 2: Approval Flow${NC}"
                npx playwright test tests/e2e/scenario2_approval_flow.spec.js $test_args
                ;;
            3)
                echo -e "${BLUE}Running Scenario 3: Search and View${NC}"
                npx playwright test tests/e2e/scenario3_search_and_view.spec.js $test_args
                ;;
            4)
                echo -e "${BLUE}Running Scenario 4: Incident Report${NC}"
                npx playwright test tests/e2e/scenario4_incident_report.spec.js $test_args
                ;;
            5)
                echo -e "${BLUE}Running Scenario 5: Expert Consultation${NC}"
                npx playwright test tests/e2e/scenario5_expert_consultation.spec.js $test_args
                ;;
            *)
                echo -e "${RED}Error: Invalid scenario number: $SCENARIO${NC}"
                echo -e "Please specify a scenario number between 1 and 5"
                exit 1
                ;;
        esac
    else
        echo -e "${BLUE}Running all E2E scenarios${NC}"
        echo ""
        npx playwright test $test_args
    fi
}

show_report() {
    if [ "$SHOW_REPORT" = true ]; then
        echo ""
        echo -e "${YELLOW}Opening HTML report...${NC}"
        npx playwright show-report
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}E2E Tests Completed${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Reports generated in: $PROJECT_ROOT/tests/reports/"
    echo ""
    echo "Available reports:"
    echo "  - HTML: tests/reports/e2e-html/index.html"
    echo "  - JSON: tests/reports/e2e-results.json"
    echo "  - JUnit: tests/reports/e2e-junit.xml"
    echo ""
    echo "To view the HTML report, run:"
    echo "  npm run test:e2e:report"
    echo ""
}

###############################################################################
# Main Script
###############################################################################

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --headed)
            HEADED="--headed"
            shift
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        --ui)
            UI="--ui"
            shift
            ;;
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --report)
            SHOW_REPORT=true
            shift
            ;;
        --no-server)
            SKIP_SERVER=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            echo ""
            print_usage
            exit 1
            ;;
    esac
done

# Main execution flow
print_header
check_dependencies
setup_environment
run_tests
show_report
print_summary

exit 0
