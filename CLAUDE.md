---
IMPORTANT: File is read fresh for every conversation. Be brief and practical.
project_type: django-nextjs-hybrid
version: 1.0.0
backend_framework: Django 6.0 + Django Ninja
frontend_framework: Next.js 16 + Tailwind CSS 4 + Radix UI
last_updated: 2026-04-26
---

# Wellfond Breeding Management System (BMS)

Enterprise-grade dog breeding operations platform for Singapore AVS-licensed breeders. Supports multi-entity operations with compliance tracking, PII/PDPA protection, and AVS submission workflows.

**Tech Stack**: Django 6.0 + Django Ninja API, Next.js 16 + Tailwind CSS 4 + Radix UI, PostgreSQL 17, Redis 7.4, Celery

## Core Identity & Purpose

Wellfond BMS manages the complete lifecycle of dog breeding operations:
- Multi-entity business structure (Holdings, Katong, Thomson)
- RBAC with 5 roles (management, admin, sales, ground, vet)
- HttpOnly cookie-based authentication with Redis sessions
- BFF (Backend-for-Frontend) proxy pattern
- AVS compliance tracking and submission workflows
- PII/PDPA consent management for customer data

## Foundational Principles

### Meticulous Approach (Six-Phase Workflow)

Follow this six-phase workflow for all implementation tasks:

1. **ANALYZE** - Deep, multi-dimensional requirement mining
   - Never make surface-level assumptions
   - Identify explicit requirements, implicit needs, and potential ambiguities
   - Explore multiple solution approaches
   - Perform risk assessment

2. **PLAN** - Structured execution roadmap
   - Create detailed plan with sequential phases
   - Present plan for explicit user confirmation
   - Never proceed without validation

3. **VALIDATE** - Explicit confirmation checkpoint
   - Obtain explicit user approval before implementation
   - Address any concerns or modifications

4. **IMPLEMENT** - Modular, tested, documented builds
   - Set up proper environment
   - Implement in logical, testable components
   - Create documentation alongside code

5. **VERIFY** - Rigorous QA against success criteria
   - Execute comprehensive testing
   - Review for best practices, security, performance
   - Consider edge cases and accessibility

6. **DELIVER** - Complete handoff with knowledge transfer
   - Provide complete solution with instructions
   - Document challenges and solutions
   - Suggest improvements and next steps

### Project-Specific Principles

- **Hybrid Environment**: Backend (Django) and frontend (Next.js) run locally while PostgreSQL and Redis run in containers
- **BFF Security Pattern**: All API calls go through Next.js proxy; no direct backend access from browser
- **Entity Scoping**: Every data query must respect entity boundaries (multi-tenancy)
- **PDPA Compliance**: Hard filters for consent; no PII without explicit consent
- **Audit Logging**: All sensitive operations logged immutably for compliance
- **No AI in Compliance**: Deterministic logic only for AVS-related calculations

## Implementation Standards

### Django 6.0 + Django Ninja Specific

- **API Framework**: Django Ninja for type-safe API endpoints
- **Pydantic Schemas**: All request/response models use Pydantic v2
- **Router Organization**: Each app has its own router (`routers/{feature}.py`)
- **Authentication**: Custom HttpOnly cookie-based auth with Redis sessions
- **Session Management**: `apps.core.auth.SessionManager` for Redis-backed sessions
- **RBAC**: `apps.core.permissions.require_role()` decorator pattern
- **Entity Scoping**: `apps.core.permissions.scope_entity()` helper for multi-tenancy

### Authentication Pattern (CRITICAL)

```python
# CORRECT: Read session cookie directly (Ninja doesn't preserve request.user)
def _check_admin_permission(request):
    from apps.core.auth import SessionManager, AuthenticationService
    session_key = request.COOKIES.get(AuthenticationService.COOKIE_NAME)
    session_data = SessionManager.get_session(session_key)
    user = User.objects.get(id=session_data["user_id"])
    # ... validation

# WRONG: Don't rely on request.user with Ninja decorators
@require_admin  # This doesn't work with Ninja's pagination
```

### Pydantic v2 Migration

- Use `model_validate(user, from_attributes=True)` not `from_orm()`
- Use `UserResponse.model_validate()` for serialization
- All schema fields must match ORM model fields exactly

### Next.js 16 + Tailwind CSS 4 + Radix UI

- **App Router**: Use `app/` directory with route groups
- **Server Components**: Default; add `'use client'` only for interactivity
- **Tailwind v4**: CSS-first configuration via `@import` and `@theme`
- **Radix UI**: Base components for accessibility
- **shadcn/ui**: Use installed components, don't rebuild
- **BFF Proxy**: All API calls through `/api/proxy/[...path]`

### TypeScript Strict Mode

- `strict: true` in `tsconfig.json`
- Never use `any` - use `unknown` instead
- Explicit types on all function parameters
- Use `interface` for object shapes, `type` for unions

## Development Workflow

### Environment Setup

```bash
# 1. Start infrastructure containers
cd /home/project/wellfond-bms
docker-compose up -d postgres redis

# 2. Backend setup
cd backend
python manage.py migrate
python manage.py shell -c "from apps.core.models import User; User.objects.create_superuser('admin', 'admin@wellfond.sg', 'Wellfond@2024!', role='management')"

# 3. Frontend setup
cd ../frontend
npm install

# 4. Start services (hybrid mode)
# Terminal 1: Django
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Next.js
npm run dev
```

### Backend Commands

| Command | Purpose |
|---------|---------|
| `python manage.py runserver 0.0.0.0:8000` | Start Django dev server |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py shell` | Django shell for debugging |
| `python manage.py test` | Run Django tests |
| `python -m pytest tests/` | Run pytest tests |
| `celery -A config worker -l info` | Start Celery worker |
| `celery -A config beat -l info` | Start Celery beat scheduler |

### Frontend Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start Next.js dev server (port 3000) |
| `npm run build` | Production build |
| `npm run lint` | ESLint check |
| `npm run typecheck` | TypeScript type checking |
| `npx playwright test` | Run E2E tests |
| `npx vitest` | Run unit tests |

### Docker Commands

| Command | Purpose |
|---------|---------|
| `docker-compose up -d postgres redis` | Start DB and cache |
| `docker-compose logs -f postgres` | Watch PostgreSQL logs |
| `docker-compose logs -f redis` | Watch Redis logs |

## Testing Strategy

### Test Organization

- **Backend**: `tests/` directory at project root
  - `test_auth_refresh_endpoint.py` - Authentication tests
  - `test_users_endpoint.py` - User management tests
- **Frontend**: `frontend/tests/` for Playwright E2E tests

### Running Tests

```bash
# Backend tests
cd /home/project/wellfond-bms/tests
python test_auth_refresh_endpoint.py
python test_users_endpoint.py

# Frontend E2E tests
cd frontend
npx playwright test

# Frontend unit tests
npx vitest
```

### TDD Pattern

1. Write failing test (Red)
2. Implement minimal code to pass (Green)
3. Refactor while keeping tests passing (Refactor)
4. Verify with curl or test client

## Code Quality Standards

### Backend (Python/Django)

- **Imports**: Sort with `isort` (configuration in pyproject.toml)
- **Formatting**: Use `black` for code formatting
- **Typing**: Type hints on all public functions
- **Docstrings**: Google-style docstrings for modules and functions
- **Line Length**: 100 characters max

### Frontend (TypeScript)

- **Linting**: ESLint with flat config (`eslint.config.mjs`)
- **Formatting**: Prettier (via ESLint)
- **Import Order**: Absolute imports first, then relative
- **Component Structure**: Co-locate component, styles, and tests

## Git & Version Control

### Branch Naming

- `feature/{ticket-id}-{description}` - New features
- `fix/{ticket-id}-{description}` - Bug fixes
- `refactor/{description}` - Code refactoring
- Short-lived branches (merge within 1-3 days)

### Commit Standards

- Follow Conventional Commits format
- Atomic commits (one logical change per commit)
- Reference ticket IDs in commit messages

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## Error Handling & Debugging

### Backend Error Handling

- Use `ninja.errors.HttpError` for API errors
- Custom exception handler in `api/__init__.py`
- Log all errors with structured logging
- Sensitive data never in error messages

### Debugging Tools

```python
# Django shell
python manage.py shell

# Check Redis session
cd backend && python manage.py shell -c "
from django.core.cache import cache
print(cache.keys('session:*'))
"

# View logs
tail -f backend/nohup.out
```

### Frontend Error Handling

- Always implement `onError` handler for async operations
- Show loading indicator on buttons during async operations
- Disable buttons during mutations

## Communication & Documentation

### Documentation Standards

- Explain "why", not just "what"
- Document assumptions and constraints
- Update AGENTS.md when conventions change
- Use Mermaid diagrams for complex flows

### API Documentation

- Auto-generated from Ninja schemas
- Access at `/api/v1/docs/` when server running
- Keep schemas in sync with models

## Project-Specific Standards

### Architecture

```
wellfond-bms/
├── backend/               # Django backend
│   ├── api/              # Ninja API root
│   ├── apps/
│   │   ├── core/         # Auth, RBAC, entities, audit
│   │   ├── operations/   # Dogs, breeding, health records
│   │   ├── breeding/     # Matings, litters, genetics
│   │   ├── sales/        # Sales, waitlist, invoices
│   │   ├── compliance/   # AVS submissions, NParks
│   │   ├── customers/    # Customers, PDPA consent
│   │   ├── finance/      # Invoicing, payments
│   │   └── ai_sandbox/   # Safe AI experiments
│   └── config/           # Django settings
├── frontend/             # Next.js frontend
│   ├── app/              # App Router
│   ├── components/       # React components
│   └── lib/              # Utilities, types
└── tests/                # Backend test files
```

### API Design

- **Base Path**: `/api/v1/`
- **Auth Endpoints**: `/api/v1/auth/*`
- **Resource Endpoints**: `/api/v1/{resource}/`
- **Response Format**: Pydantic models with consistent structure

### Database Patterns

- **Models**: UUID primary keys, `created_at`, `updated_at`
- **Soft Delete**: `is_active` flag (never hard delete)
- **Audit Logs**: Immutable `AuditLog` model
- **Migrations**: Always create, never modify DB directly

### Entity Scoping

Every data query must respect entity boundaries:

```python
# CORRECT: Scope by entity
from apps.core.permissions import scope_entity
queryset = scope_entity(Dog.objects.all(), request.user)

# Management sees all; others see only their entity
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@localhost:5432/wellfond_db` |
| `REDIS_CACHE_URL` | Redis cache | `redis://localhost:6379/0` |
| `REDIS_SESSIONS_URL` | Redis sessions | `redis://localhost:6379/1` |
| `SECRET_KEY` | Django secret | Django-generated |
| `JWT_SECRET` | Token signing | Secure random string |

## Success Metrics

You are successful when:
- API endpoints return consistent responses
- Authentication flows work end-to-end
- Entity scoping prevents data leakage
- Tests pass before commits
- Code follows established patterns

---

## Phase 2-3 Lessons Learned (April 26, 2026)

### Technical Insights

1. **Django Ninja Pagination**: `@paginate` decorator requires `list[Schema]` response type, not wrapped objects. Manual pagination gives more control and works with custom response structures.

2. **Circular Imports in Django**: Services imported in model `save()` methods should use deferred imports (`try/except ImportError`) or move logic to signals. This prevents import cycles during app initialization.

3. **Self-Referential FKs**: Using `on_delete=PROTECT` on dam/sire FKs prevents accidental deletion of dogs with offspring, maintaining pedigree integrity.

4. **CSV Import Patterns**: Pre-flight validation before database transaction is essential for good UX with detailed error messages. Use `transaction.atomic()` for rollback safety.

5. **Frontend State Management**: TanStack Query with proper invalidation keys eliminates manual cache management. Use `queryClient.invalidateQueries()` after mutations.

6. **Draminski Per-Dog Baseline**: Rolling mean of last 30 readings per dog provides accurate fertility thresholds, avoiding global calibration issues.

7. **SSE with Django Ninja**: Async generators work seamlessly with Ninja. Event deduplication (dog+type composite key) prevents alert spam.

8. **PWA Service Worker Strategy**: Cache-first for static assets, network-first for API calls. Background sync requires explicit permission in manifest.

9. **Idempotency Pattern**: UUIDv4 keys on all POST requests with 24h Redis TTL ensures safe retries without duplicate processing.

10. **Mobile-First Route Groups**: `(ground)/` route group with no sidebar reduces bundle size and improves kennel usability with 44px touch targets.

### Process Insights

1. **Test-First Approach**: Writing tests before implementation catches architectural issues early and ensures entity scoping works correctly.

2. **Phase Gate Reviews**: Explicit validation checkpoints prevent scope creep and ensure quality before moving to next phase.

3. **Documentation Parity**: Updating AGENTS.md and README alongside code reduces knowledge debt and keeps team aligned.

4. **Migration Strategy**: Always use Django migrations, never modify DB directly. This saved us from data loss during iterative development.

5. **TypeScript Strict Mode**: Fixing 87 type errors revealed underlying API contract mismatches. Early type discipline prevents runtime errors.

6. **Client Component Boundaries**: `'use client'` needed for hooks (useState, useEffect) but not for data fetching in Server Components.

7. **Deleted File Recovery**: Systematic restoration approach (inventory → categorize → restore → verify) proved effective for large-scale recovery.

---

## Phase 2-3 Blockers Encountered

### Resolved Blockers

| Blocker | Impact | Solution | Date Resolved |
|---------|--------|----------|---------------|
| `@paginate` with wrapped response | Pagination failed with custom response objects | Removed decorator, implemented manual pagination | Apr 26 |
| Circular import (vaccine service) | Model save() couldn't import service | Deferred import with try/except | Apr 26 |
| Missing `DogPhotoListResponse` | Router import error | Added missing schema to schemas.py | Apr 26 |
| Import error `UserSummary` | Schema import failed | Removed non-existent import | Apr 26 |
| Test discovery failure | pytest couldn't find tests | Added `__init__.py` to test directories | Apr 26 |
| Python-style docstrings | TypeScript syntax errors | Converted to JSDoc comments | Apr 26 |
| Duplicate AlertCards import | ESLint warning | Removed duplicate import | Apr 26 |
| SSE connection drops | Async generators failed to stream | Verified ASGI running, added proper MIME type | Apr 26 |
| Draminski baseline calc | Missing readings caused errors | Default to 300 if <30 readings available | Apr 26 |
| TrendIndicator type error | Expected number, got string | Changed to `'up' \| 'down' \| 'flat' \| undefined` | Apr 26 |
| SortField type mismatch | 'created_at' not in union | Extended local SortField type in dog-table.tsx | Apr 26 |

### Persistent Blockers

| Blocker | Status | Notes |
|---------|--------|-------|
| PgBouncer in dev | Not required | Using direct PG connection for simplicity |
| Gotenberg in dev | Optional | PDF generation not critical for Phase 2-3 |
| Celery workers | In Progress | Needs worker/beat startup in dev |
| Test coverage < 85% | In Progress | Need more edge case tests (Phase 4+) |

---

## Recommended Next Steps

### Immediate (Next 2-3 Days)

1. **Configure Celery Workers**
   - Start worker: `celery -A config worker -l info`
   - Start beat: `celery -A config beat -l info`
   - Test background tasks (closure table rebuilds)

2. **Backend Test Execution**
   - Fix Django environment for pytest
   - Run: `pytest backend/apps/operations/tests/`
   - Target: ≥85% coverage

3. **E2E Testing with Playwright**
   - Critical paths: Login → Ground Log → Offline Sync
   - PWA installation flow
   - SSE real-time alert verification

### Short-term (Next 1-2 Weeks)

4. **Phase 4: Breeding & Genetics Engine**
   - Mate checker with COI calculation
   - Farm saturation analysis
   - Dual-sire pedigree support
   - Closure table implementation

5. **Phase 5: Sales Agreements & AVS**
   - 5-step wizard (B2C/B2B/Rehoming)
   - Gotenberg PDF generation
   - AVS link tracking
   - 3-day reminder tasks

### Phase Milestones

| Phase | Target Date | Status |
|-------|-------------|--------|
| Phase 0 | Apr 22 | ✅ Complete |
| Phase 1 | Apr 25 | ✅ Complete |
| Phase 2 | Apr 26 | ✅ Complete |
| Phase 3 | Apr 26 | ✅ Complete |
| Phase 4 | May 7 | 🔄 Next |
| Phase 5 | May 14 | 📋 Planned |

## System Integration

### Available Tools

- **bash**: Execute terminal operations
- **read**: Read files and directories
- **glob**: Find files by pattern
- **edit**: Make exact string replacements
- **write**: Write files to filesystem

### Hybrid Development Mode

- Django runs on localhost:8000
- Next.js runs on localhost:3000
- PostgreSQL in Docker (port 5432)
- Redis in Docker (port 6379)

## Anti-Patterns to Avoid

- **Relying on request.user with Ninja**: Always read session cookie directly
- **Using from_orm()**: Use model_validate() for Pydantic v2
- **Custom components when shadcn exists**: Use library components
- **Hardcoding entity IDs**: Always use entity scoping
- **Storing PII without consent**: Check PDPA consent first
- **Magic numbers**: Use constants from `lib/constants.ts`
- **Synchronous AVS calls**: Use Celery for compliance tasks
- **Using @paginate with wrapped responses**: Manual pagination for custom responses
- **Python-style docstrings in TypeScript**: Use JSDoc `/** */` not `"""`
- **Duplicate imports**: Check imports before committing
- **Importing services at module level in models**: Use deferred imports to avoid circular deps

## Troubleshooting

### Common Issues

**Session not persisting**
```bash
# Check Redis connection
redis-cli ping

# Verify session engine
python -c "from django.conf import settings; print(settings.SESSION_ENGINE)"
# Should be: django.contrib.sessions.backends.cache

# Check cookie in browser DevTools
# Look for 'sessionid' cookie with HttpOnly, Secure, SameSite=Lax
```

**Ninja router not registering**
```bash
# Ensure router added in api/__init__.py
# Check for import errors
python -c "from api import api; print(api.urls)"

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

**Migration errors**
```bash
# Check migration status
python manage.py showmigrations

# Reset if needed (CAUTION: data loss)
python manage.py migrate operations zero
python manage.py migrate operations
```

**Frontend proxy 404**
```bash
# Verify Django running
curl http://localhost:8000/health/

# Test proxy route
curl http://localhost:3000/api/proxy/health/

# Check proxy logs in browser Network tab
```

**Type errors after changes**
```bash
cd frontend
npm run typecheck

# Common fixes:
# - Check Pydantic schema matches ORM model
# - Verify all required fields present
# - Ensure no 'any' types with strict: true
```

### Phase 2 Specific Issues

**Circular import in vaccine service**
```python
# Problem: Importing service in model save() causes circular import
# Solution: Defer import inside method
def save(self, *args, **kwargs):
    try:
        from .services.vaccine import calc_vaccine_due
        self.due_date = calc_vaccine_due(self.dog, self.vaccine_name, self.date_given)
    except ImportError:
        # Service not yet available, skip auto-calculation
        pass
    super().save(*args, **kwargs)
```

**@paginate decorator issues**
```python
# Problem: @paginate doesn't work well with wrapped response objects
# Solution: Use manual pagination
@router.get("/", response=DogListResponse)
def list_dogs(request, page: int = 1, per_page: int = 25):
    qs = Dog.objects.all()
    total = qs.count()
    paginated = qs[(page-1)*per_page : page*per_page]
    return {"count": total, "results": list(paginated), "page": page, "per_page": per_page}
```

**Test discovery failure**
```bash
# Ensure __init__.py exists in test directories
touch apps/operations/tests/__init__.py

# Run with verbose output
python -m pytest apps/operations/tests/ -v --tb=short
```

**Python-style docstrings in TypeScript**
```typescript
// WRONG - Python triple quotes:
"""
Component description
"""

// CORRECT - JSDoc comments:
/**
 * Component description
 * =====================
 * Detailed explanation here.
 */
```
