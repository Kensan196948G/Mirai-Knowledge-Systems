#!/bin/bash

REPO_DIR="/mnt/LinuxHDD/Mirai-Knowledge-Systems"
MAX_ATTEMPTS=15
WAIT_TIME_MINUTES=5

echo "Starting continuous monitor and fix loop..."

while true; do
    echo "$(date): Checking workflow status..."
    
    CI_CD_STATUS=$(gh run list --workflow=221768954 --limit=1 --json conclusion | jq -r '.[0].conclusion')
    FRONTEND_STATUS=$(gh run list --workflow=220002484 --limit=1 --json conclusion | jq -r '.[0].conclusion')
    
    echo "CI/CD: $CI_CD_STATUS, Frontend: $FRONTEND_STATUS"
    
    if [ "$CI_CD_STATUS" = "success" ] && [ "$FRONTEND_STATUS" = "success" ]; then
        echo "$(date): All workflows successful! Exiting..."
        exit 0
    fi
    
    # If any failure, trigger rerun
    if [ "$CI_CD_STATUS" = "failure" ] || [ "$FRONTEND_STATUS" = "failure" ]; then
        echo "$(date): Failures detected. Triggering rerun..."
        gh workflow run ci-cd.yml --ref main || echo "CI/CD trigger failed"
        gh workflow run frontend-tests.yml --ref main || echo "Frontend trigger failed"
    fi
    
    echo "$(date): Waiting 2 minutes for completion..."
    sleep 120
done
