#!/bin/bash

MAX_ATTEMPTS=15
WAIT_TIME_MINUTES=5
attempt=1

while true; do
    echo "$(date): Starting fix attempt $attempt"
    
    # Check status
    CI_CD_STATUS=$(gh run list --workflow=221768954 --limit=1 --json conclusion | jq -r '.[0].conclusion // "null"')
    FRONTEND_STATUS=$(gh run list --workflow=220002484 --limit=1 --json conclusion | jq -r '.[0].conclusion // "null"')
    
    echo "CI/CD: $CI_CD_STATUS, Frontend: $FRONTEND_STATUS"
    
    # Check if both are successful
    if [ "$CI_CD_STATUS" = "success" ] && [ "$FRONTEND_STATUS" = "success" ]; then
        echo "$(date): All workflows successful! Exiting..."
        exit 0
    fi
    
    # If we reached max attempts, wait and reset
    if [ $attempt -gt $MAX_ATTEMPTS ]; then
        echo "$(date): Max attempts reached. Waiting $WAIT_TIME_MINUTES minutes..."
        sleep $((WAIT_TIME_MINUTES * 60))
        attempt=1
        continue
    fi
    
    # Trigger workflows if they have dispatch
    if [ "$CI_CD_STATUS" != "success" ]; then
        echo "Triggering CI/CD workflow..."
        gh workflow run ci-cd.yml --ref main || echo "CI/CD trigger failed"
    fi
    
    if [ "$FRONTEND_STATUS" != "success" ]; then
        echo "Triggering Frontend Tests workflow..."
        gh workflow run frontend-tests.yml --ref main || echo "Frontend trigger failed"
    fi
    
    # Wait for completion
    echo "$(date): Waiting 3 minutes for workflows to complete..."
    sleep 180
    
    ((attempt++))
done
