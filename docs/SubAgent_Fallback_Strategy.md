# SubAgent Error Handling and Fallback Implementation

## Overview
This module provides fallback functionality when SubAgent providers are unavailable.

## Available SubAgents
- ✅ general: General-purpose agent for research and multi-step tasks
- ✅ explore: Fast agent specialized for exploring codebases
- ❌ sec-auditor: ProviderModelNotFoundError - using standard security tools
- ❌ arch-reviewer: ProviderModelNotFoundError - using standard analysis
- ❌ test-designer: ProviderModelNotFoundError - using standard test tools
- ❌ code-implementer: ProviderModelNotFoundError - using standard coding
- ❌ ops-runbook: ProviderModelNotFoundError - using standard docs
- ❌ ci-specialist: ProviderModelNotFoundError - using standard CI/CD
- ❌ docs-writer: Disabled

## Fallback Strategy
When SubAgent fails with ProviderModelNotFoundError:
1. Detect the error in task execution
2. Switch to standard functionality using available tools
3. Provide equivalent functionality through bash/read/edit/write/grep/glob
4. Log the fallback action for transparency

## Implementation Details
- Error detection in task tool responses
- Automatic fallback to standard tools
- Equivalent functionality preservation
- Performance monitoring of fallbacks