# Mirai Knowledge Systems - Copilot Agent Instructions

## Project Overview

**Name**: Mirai Knowledge Systems
**Domain**: Construction/Civil Engineering Industry Knowledge Management
**Version**: 1.4.0

## Tech Stack

- **Backend**: Flask 3.1.2 (Python 3.12+), SQLAlchemy 2.0, JWT auth
- **Frontend**: Vanilla JavaScript (ES6+), no framework
- **Database**: PostgreSQL 16 (production), JSON (development)
- **Testing**: pytest + Jest 29.7 + Playwright 1.57
- **Linting**: ruff (mandatory), flake8 (advisory)

## Project Structure

```
backend/
  app_v2.py          # Main Flask app (46+ endpoints)
  models.py          # SQLAlchemy models (14+ tables)
  schemas.py         # Validation schemas
  auth/              # Authentication (JWT + 2FA/TOTP)
  services/          # Business logic services
  integrations/      # External API clients (MS365)
  tests/             # pytest tests (unit/integration/e2e/security)
webui/
  app.js             # Main frontend logic
  *.html             # HTML pages
  *.js               # Feature modules
docs/                # Documentation
```

## Coding Standards

### Python
- Follow PEP 8
- Use `ruff` for linting (CI enforced)
- Max line length: 100 characters
- Use type hints where practical
- All new functions must have docstrings

### JavaScript
- ES6+ syntax (const/let, arrow functions, template literals)
- **NEVER use innerHTML** - always use DOM API (textContent, createElement, etc.)
- No console.log in production code
- Follow ESLint configuration

### Security Requirements
- Sanitize all user input
- Use parameterized queries (SQLAlchemy ORM)
- CSRF protection on state-changing endpoints
- Rate limiting on authentication endpoints
- Audit logging for sensitive operations

## Forbidden Actions

- DO NOT read or modify `.env` files
- DO NOT directly edit `backend/data/*.json` files
- DO NOT leave `console.log` statements in code
- DO NOT use `innerHTML` (XSS risk)
- DO NOT commit secrets or credentials
- DO NOT modify `backend/data/users.json`

## Testing Requirements

- **Python coverage**: minimum 80% (`pytest --cov-fail-under=80`)
- **JavaScript coverage**: minimum 70% (Jest)
- Write tests for all new endpoints and functions
- Include both happy path and error cases
- Use existing test fixtures from `tests/conftest.py`

## Round-trip Development Loop

When working on refinement tasks:

1. **Branch naming**: `refinement/{iteration}/pr-{source_pr_number}`
2. **Commit messages**: Include `[round-trip:N]` tag (N = iteration number)
3. **PR titles**: Include `[round-trip:N]` tag
4. **Max iterations**: 3 (system enforced)

### Example
```
Branch: refinement/1/pr-2605
Commit: feat: improve test coverage [round-trip:1]
PR Title: [refinement] Add user validation [round-trip:1]
```

## Environment Variables

Required for testing:
```
MKS_ENV=test
MKS_SECRET_KEY=test-secret-key-for-ci
MKS_JWT_SECRET_KEY=test-jwt-secret-key-for-ci
MKS_CORS_ORIGINS=http://localhost:5100
```

## Common Commands

```bash
# Lint
ruff check .

# Python tests
pytest tests/ -v --tb=short -x --maxfail=5

# Jest tests
cd backend && npm run test:unit:coverage

# E2E tests
cd backend && npm run test:e2e
```
