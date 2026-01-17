#!/bin/bash

set -e

REPO_DIR="/mnt/LinuxHDD/Mirai-Knowledge-Systems"
MAX_ATTEMPTS=15
WAIT_TIME_MINUTES=5

echo "Starting auto-fix CI/CD workflow loop..."

while true; do
    echo "$(date): Starting auto-fix attempt..."
    
    attempt=1
    while [ $attempt -le $MAX_ATTEMPTS ]; do
        echo "$(date): Attempt $attempt/$MAX_ATTEMPTS"
        
        # Check current workflow status
        CI_CD_STATUS=$(gh run list --workflow=221768954 --limit=1 --json conclusion | jq -r '.[0].conclusion')
        FRONTEND_STATUS=$(gh run list --workflow=220002484 --limit=1 --json conclusion | jq -r '.[0].conclusion')
        
        echo "CI/CD status: $CI_CD_STATUS"
        echo "Frontend status: $FRONTEND_STATUS"
        
        if [ "$CI_CD_STATUS" = "success" ] && [ "$FRONTEND_STATUS" = "success" ]; then
            echo "All workflows are successful! Auto-fix complete."
            exit 0
        fi
        
        # Fix CI/CD workflow
        if [ "$CI_CD_STATUS" != "success" ]; then
            echo "Fixing CI/CD workflow..."
            
            # Fix E2E tests job - ensure backend server starts properly
            sed -i 's/working-directory: backend/working-directory: ./g' .github/workflows/ci-cd.yml
            
            # Add backend startup for E2E
            sed -i '/Install Node dependencies/a\
      - name: Start Backend Server for E2E\
        working-directory: backend\
        run: |\
          python app_v2.py &\
          sleep 10\
          curl -s http://localhost:5100/api/v1/health' .github/workflows/ci-cd.yml
            
            # Fix Playwright install path
            sed -i 's|npx playwright install --with-deps chromium|npx playwright install --with-deps|' .github/workflows/ci-cd.yml
        fi
        
        # Fix Frontend Tests workflow
        if [ "$FRONTEND_STATUS" != "success" ]; then
            echo "Fixing Frontend Tests workflow..."
            
            # Add backend server startup for E2E tests
            sed -i '/Install Playwright browsers/a\
      - name: Start Backend Server\
        working-directory: backend\
        env:\
          DATABASE_URL: postgresql://mirai_user:test_password@localhost/mirai_test\
        run: |\
          python app_v2.py &\
          sleep 10\
          curl -s http://localhost:5100/api/v1/health' .github/workflows/frontend-tests.yml
            
            # Fix BASE_URL to match backend port
            sed -i 's|BASE_URL: http://localhost:8000|BASE_URL: http://localhost:5100|' .github/workflows/frontend-tests.yml
        fi
        
        # Commit and push fixes
        git add .github/workflows/ci-cd.yml .github/workflows/frontend-tests.yml
        if git diff --cached --quiet; then
            echo "No changes to commit"
        else
            git commit -m "fix: Auto-correct CI/CD workflows - backend startup and path fixes"
            git push origin main
        fi
        
        # Trigger workflows
        gh workflow run ci-cd.yml --ref main
        gh workflow run frontend-tests.yml --ref main
        
        # Wait for completion
        echo "Waiting 2 minutes for workflow completion..."
        sleep 120
        
        ((attempt++))
    done
    
    echo "$(date): Max attempts reached. Waiting $WAIT_TIME_MINUTES minutes..."
    sleep $((WAIT_TIME_MINUTES * 60))
done
