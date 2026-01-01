#!/bin/bash

# Mirai Knowledge Systems - Frontend Test Setup Script
# フロントエンドテスト環境セットアップスクリプト

set -e

echo "=========================================="
echo "Mirai Knowledge Systems"
echo "Frontend Test Environment Setup"
echo "=========================================="
echo ""

# カレントディレクトリの確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Step 1: Installing Node.js dependencies..."
echo "------------------------------------------"
npm install

echo ""
echo "Step 2: Installing Playwright browsers..."
echo "------------------------------------------"
npx playwright install chromium

echo ""
echo "Step 3: Verifying installation..."
echo "------------------------------------------"

# Jestのバージョン確認
JEST_VERSION=$(npx jest --version 2>/dev/null || echo "not installed")
echo "Jest version: $JEST_VERSION"

# Playwrightのバージョン確認
PLAYWRIGHT_VERSION=$(npx playwright --version 2>/dev/null || echo "not installed")
echo "Playwright version: $PLAYWRIGHT_VERSION"

echo ""
echo "Step 4: Creating test directories..."
echo "------------------------------------------"
mkdir -p tests/coverage
mkdir -p tests/reports

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  npm run test:unit           - Run unit tests"
echo "  npm run test:unit:coverage  - Run unit tests with coverage"
echo "  npm run test:e2e            - Run E2E tests"
echo "  npm test                    - Run all tests"
echo ""
echo "Documentation:"
echo "  See FRONTEND_TESTING.md for detailed usage"
echo ""
