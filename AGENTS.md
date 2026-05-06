# AGENTS.md - Wellfond BMS Coding Agent Brief

## 🎯 Project Overview
**Purpose:** Enterprise dog breeding management platform for Singapore AVS-licensed breeders.
**Core Requirements:** Multi-entity operations, strict AVS/NParks compliance, PII/PDPA protection, offline-capable ground operations, and deterministic financial/regulatory logic.
**Tech Stack:** Django 6 + Django Ninja | Next.js 16 + Tailwind CSS 4 + Radix UI | PostgreSQL 17 | Redis 7.4 | Celery 5.4

---

## 🏗 Architecture & Core Patterns

### BFF Security & Authentication
- **Proxy Pattern:** Browser never contacts Django directly. All requests route through Next.js `/api/proxy/[...path]`.
- **Path Allowlist:** The BFF proxy validates all paths against a regex allowlist. Adding new top-level routers (e.g., `stream`, `alerts`) requires updating the regex in `frontend/app/api/proxy/[...path]/route.ts:66`.
- **Session Auth:** HttpOnly, Secure, SameSite=Lax cookies. Zero JWT in client storage.
- **Critical Auth Pattern:** Django Ninja does not reliably preserve `request.user` across decorators/pagination. Always read session directly:
```python
from apps.core.auth import get_authenticated_user
user = get_authenticated_user(request) # Reads cookie & validates Redis session
```
- **Middleware Order (CRITICAL):** Django's `AuthenticationMiddleware` must run BEFORE custom middleware:
```python
MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django first (admin E408)
    "apps.core.middleware.AuthenticationMiddleware",            # Custom second (Redis auth)
    # ...
]
```
Django wraps `request.user` in `SimpleLazyObject`. Custom middleware runs after to re-authenticate from Redis if needed.

### Entity Scoping (Multi-Tenancy)
- **Mandatory:** Every data query must respect entity boundaries.
- **Pattern:** `queryset = scope_entity(Model.objects.all(), request.user)`
- **RBAC:** `MANAGEMENT` sees all entities. All other roles see only their assigned `entity_id`.
- **PDPA:** Centralized PDPA filtering in `scope_entity` based on model attributes. Dogs are farm assets (no PII); consent applies to Customers/Agreements.

### Compliance & Determinism
- **NO AI in Compliance:** `apps/compliance/` and financial calculations must use pure Python/SQL. Deterministic only.
- **Audit Immutability:** `AuditLog` and locked submissions are append-only. No `UPDATE`/`DELETE`. Use `self._state.adding` in `save()`.
- **PDPA Hard Filter:** `WHERE pdpa_consent=true` enforced at QuerySet level (via `scope_entity`). Never expose PII without explicit consent.
- **GST Formula:** `Decimal(price) * 9 / 109`, rounding `ROUND_HALF_UP`. Thomson entity is 0% exempt (case-insensitive check).
- **Fiscal Year:** Singapore FY starts April (month 4). YTD calculations must roll over in April, not January.
- **Puppy PDPA:** Puppy buyer fields (`buyer_name`, `buyer_contact`) contain PII but the `Puppy` model lacks a `pdpa_consent` field. To ensure compliance, these fields must ONLY be accessed via joins with `SalesAgreement` (which enforces consent filtering in `scope_entity`). Direct queries for PII on the `Puppy` model are prohibited.

---

## 📝 Implementation Standards

### Backend (Django + Ninja)
- **Routers:** Each app owns `routers/{feature}.py`. Register in `api/__init__.py`.
- **Pydantic v2:** 
  - Use `Schema.model_validate(obj, from_attributes=True)`. Never use `from_orm()`.
  - Use `Optional[T]` for nullable fields. `T | None` breaks Pydantic v2 compatibility.
- **Security (CSP):** `django-csp` 4.0+ requires removing all legacy `CSP_*` prefixed settings. Use only the `CONTENT_SECURITY_POLICY` dict.
- **Database:** UUID PKs, `created_at`/`updated_at`, soft-delete via `is_active`. Never hard-delete. Ensure `default=''` for CharFields to avoid `NotNullViolation`.
- **Idempotency:** All state-changing POSTs require `X-Idempotency-Key` (UUIDv4). Cache responses in `caches["idempotency"]` with 24h TTL.
- **SSE/Async:** Use `sync_to_async(thread_sensitive=True)` for DB calls inside async generators to prevent thread pool exhaustion.
- **Circular Imports:** Defer service imports inside model methods or use signals. Never import services at module level in `models.py`.

### Frontend (Next.js + TypeScript)
- **Routing:** App Router with route groups: `(auth)`, `(protected)`, `(ground)` (mobile-optimized, no sidebar).
- **Components:** Server Components by default. Add `'use client'` only for hooks/interactivity.
- **UI Library:** Radix primitives + shadcn/ui. Do not rebuild existing components.
- **Tailwind v4:** CSS-first config via `@theme` and `@import`. Adhere to Tangerine Sky design tokens.
- **TypeScript Strict:**
  - `strict: true`. Never use `any` (use `unknown`).
  - Optional props must explicitly allow `undefined`: `entityId?: string | undefined`
  - Use `interface` for objects, `type` for unions.
- **Data Fetching:** Use `authFetch` wrapper (`lib/api.ts`). Injects idempotency keys and handles BFF proxy routing. Avoid double prefixing (`/api/v1` is handled by proxy).
- **Docstrings:** Use JSDoc `/** */` in TS/JS. Never use Python-style `"""`.

---

## 🧪 Testing & QA Strategy
- **Methodology:** TDD mandatory. Red → Green → Refactor → Verify.
- **Frameworks:** `pytest` (backend), `Vitest` (frontend unit), `Playwright` (E2E).
- **Coverage Target:** ≥85% backend. Critical paths covered in E2E.
- **Auth Fixtures:** `force_login` breaks Ninja routers. Use `authenticate_client()` helper from `conftest.py` to set valid session cookies.
- **UUIDs:** `NinjaJSONEncoder` handles UUID objects natively; do not manually cast to string for API responses.
- **Pagination:** `@paginate` decorator fails with wrapped/custom response objects. Implement manual pagination for all list endpoints.
- **Test Data:** Must match model choices exactly (`"F"`/`"M"`, `"ACTIVE"`, `"NATURAL"`). Include `dob` and explicit `slug` for entities.

---

## 📁 Project Structure (Simplified)
```
wellfond-bms/
├── backend/
│   ├── api/                 # NinjaAPI root & router registry
│   ├── apps/
│   │   ├── core/            # Auth, RBAC, entity scoping, audit, dashboard
│   │   ├── operations/      # Dogs, health, ground logs, SSE alerts
│   │   ├── breeding/        # COI, saturation, litters, closure tables
│   │   ├── sales/           # Agreements, AVS tracking, PDF gen
│   │   ├── compliance/      # NParks, GST, PDPA (deterministic only)
│   │   ├── customers/       # CRM, segmentation, blasts
│   │   ├── finance/         # P&L, GST reports, intercompany transfers
│   │   └── ai_sandbox/      # Isolated AI experiments
│   └── config/              # Settings, Celery, ASGI/WSGI
├── frontend/
│   ├── app/                 # (auth), (protected), (ground), api/proxy
│   ├── components/          # Radix/shadcn UI, feature widgets
│   ├── hooks/               # TanStack Query hooks per feature
│   └── lib/                 # authFetch, offline-queue, constants, types
└── tests/                   # Backend pytest suite
```

---

## ⚡ Essential Commands
| Task | Command |
|------|---------|
| Start Infra | `docker-compose up -d postgres redis` |
| Backend Dev | `cd backend && python manage.py runserver 0.0.0.0:8000` |
| Frontend Dev | `cd frontend && npm run dev` |
| Migrations | `python manage.py makemigrations && python manage.py migrate` |
| Backend Tests | `cd backend && python -m pytest apps/ -v` |
| Frontend Typecheck | `cd frontend && npm run typecheck` |
| Frontend Build | `cd frontend && npm run build` |
| E2E Tests | `cd frontend && npx playwright test` |
| Celery Worker | `celery -A config worker -l info` |
| Celery Beat | `celery -A config beat -l info` |

---

## 🚫 Anti-Patterns & Critical Gotchas
| Category | ❌ Avoid | ✅ Do Instead |
|----------|----------|---------------|
| **Auth** | Relying on `request.user` with Ninja | Read session cookie via `get_authenticated_user(request)` |
| **Financial** | `float()` in Excel exports | Pass `Decimal` directly to `openpyxl` |
| **Pydantic** | `from_orm()` or `T \| None` | `model_validate(..., from_attributes=True)` & `Optional[T]` |
| **Pagination** | `@paginate` with wrapped responses | Manual slice & count pagination |
| **Entity Scope** | Hardcoding IDs or unscoped queries | `scope_entity(qs, user)` on every query |
| **Compliance** | AI/LLM calls in regulatory logic | Pure Python/SQL deterministic calculations |
| **GST Rounding** | `ROUND_HALF_EVEN` or standard float | `Decimal` with `ROUND_HALF_UP` |
| **Model Save** | Checking `self.pk` for new records | Check `self._state.adding` |
| **TS Props** | `prop?: string` with strict mode | `prop?: string \| undefined` |
| **Components** | Rebuilding UI from scratch | Use installed shadcn/Radix components |
| **Docstrings** | Python `"""` in TypeScript | JSDoc `/** */` |
| **Idempotency** | Using default `cache` backend | Use isolated `caches["idempotency"]` |
| **SSE/Async** | Direct sync ORM in async routes | Wrap with `sync_to_async(thread_sensitive=True)` |
| **BFF Proxy Runtime** | `export const runtime = 'edge'` | Remove - use default Node.js runtime |
| **Internal URLs** | `NEXT_PUBLIC_*` for backend URLs | `BACKEND_INTERNAL_URL` server-side only |
| **Middleware Order** | Custom auth before Django auth | Django first, then custom (E408 requirement) |
| **CSP** | Keeping legacy `CSP_*` settings | Delete all `CSP_*` vars; use `CONTENT_SECURITY_POLICY` dict |
| **BFF Proxy** | Double prefixing `/api/v1` in client | Let `authFetch` and proxy handle the base path |
| **Serialization** | `float()` in calculations | Use `Decimal` throughout; convert to `float` only at API edge |
| **Audit Immutability** | Model-level `save()`/`delete()` only | Also use `ImmutableQuerySet` to block bulk deletes |
| **Celery Beat** | Duplicate schedules in settings + celery.py | Single source in `celery.py` with `crontab`; remove `CELERY_BEAT_SCHEDULE` |
| **Decimal Defaults** | `DecimalField(default=0.09)` (float literal) | `DecimalField(default=Decimal("0.09"))` |
| **Revenue Filters** | `signed_at__gte` in dashboard/finance | `completed_at__date__gte` for revenue recognition |
| **Immutable Bounce** | Mutating `CommunicationLog.status` in `handle_bounce` | Create new BOUNCED entry (append-only) |

django-csp 4.0 requires the OLD CSP_* settings to be removed — their mere presence causes csp.E001.
The CSP error is clear — django-csp 4.0 requires removal of old CSP_* prefix settings.
Fix the CSP settings per the migration guide (remove old CSP_* settings, keep only dict format)
- In base.py: Remove all CSP_* lines, keep only CONTENT_SECURITY_POLICY dict
- In development.py: Remove CSP_SCRIPT_SRC and CSP_REPORT_ONLY, replace with self-contained dicts
- Centralized PDPA in scope_entity/scope_entity_for_list rather than per-router — ensures no endpoint accidentally skips the filter. MANAGEMENT role still sees all entities but PDPA still applies.
- authenticate_client() helper exported from conftest.py — allows both function-style and fixture-style use, since some test classes create users dynamically and need per-test auth.
- CSP report-only in dev (CONTENT_SECURITY_POLICY={}, CONTENT_SECURITY_POLICY_REPORT_ONLY={...}) to avoid breaking HMR/inline scripts during development.
- django-csp v4 error: csp.E001 fires if ANY old CSP_* settings remain — even if new dict config exists. All old prefix vars must be fully deleted, not just supplemented.
- force_login breaks Ninja: Django Ninja 1.6.2 uses its own auth extraction that differs from Django's stock AuthenticationMiddleware. force_login sets request.user on the Django session but Ninja bypasses this — hence 401 responses in tests.
- BFF double prefix: api.ts:buildUrl() prepends /api/v1 (server) or /api/proxy (client). Hooks using /api/v1/breeding/... become /api/v1/api/v1/breeding/... → 404. Also, the BFF proxy allowlist expects /breeding (not /api/v1/breeding) → 403.
- UUID serialization is NOT a problem: NinjaJSONEncoder extends DjangoJSONEncoder which handles UUID objects natively.
- the 500 is NotNullViolation on colour (NOT a UUID issue). The NinjaJSONEncoder handles UUIDs natively.
- backend/apps/operations/models.py - add default='' to colour, unit, and notes
  colour = models.CharField(max_length=50, blank=True, default='')
- Parallel test execution (pytest-xdist) causes deadlock detected and database does not exist errors — always use -p no:xdist for sequential runs

---

## 🔍 Troubleshooting & Lessons Learnt
- **csp.E001 Error:** Triggered by any remaining `CSP_*` prefixed settings in Django configuration after upgrading to `django-csp` 4.0.
- **401 Unauthorized in Tests:** Usually caused by using `force_login` instead of session-based cookies which Ninja requires.
- **Property Missing Errors:** Ensure `frontend/lib/types.ts` is updated when backend models change (e.g., adding `notes` to `Dog`).
- **NotNullViolation:** Ensure `blank=True` CharFields have `default=''` to satisfy DB constraints during model instantiation.
- **Double Prefixing:** `api.ts:buildUrl()` and BFF proxy configuration can conflict if both try to append API version prefixes.
- **BFF SSE Blocked:** The proxy path allowlist regex in `route.ts:66` must include every top-level router path. Adding `stream` or `alerts` routers requires updating the regex. Tests for new paths must be added to `__tests__/route.test.ts`.
- **Celery Beat Duplicates:** Beat schedules defined in both `celery.py` and `settings/base.py` cause silent configuration conflicts. Use `celery.py` as the single source of truth with `crontab` for explicit SGT scheduling. Remove `CELERY_BEAT_SCHEDULE` from settings entirely.
- **Celery Task Names:** Task name strings in beat schedules must match the actual `@shared_task` function name exactly. A typo like `avs_reminder_check` vs `check_avs_reminders` causes silent `TaskNotFoundError` — Celery beat skips the task without alerting.
- **ImmutableQuerySet Pattern:** Model-level `save()`/`delete()` overrides do NOT protect against `QuerySet.delete()` (bulk deletes). Use `ImmutableManager` with `ImmutableQuerySet` for audit log models:
```python
class ImmutableQuerySet(models.QuerySet):
    def delete(self):
        raise ValueError("Immutable records cannot be deleted")

class ImmutableManager(models.Manager):
    def get_queryset(self):
        return ImmutableQuerySet(self.model, using=self._db)

class AuditLog(models.Model):
    objects = ImmutableManager()
```
Apply to all immutable models: `AuditLog`, `PDPAConsentLog`, `CommunicationLog`.
- **CommunicationLog Bounce Handling:** `handle_bounce()` in `blast.py` creates a new `CommunicationLog` entry with `BOUNCED` status (append-only) instead of mutating the original. The original `SENT` entry is preserved for audit trail integrity.
- **GST Decimal Default:** `DecimalField(default=0.09)` stores the default as a Python `float`, causing `Decimal + float` TypeErrors and silent precision loss (`Decimal(0.09)` = `0.089999...`). Always use `default=Decimal("0.09")`.
- **Dashboard Revenue Recognition:** Revenue filtering must use `completed_at__date__gte/lte`, not `signed_at__gte/lte`. A signed agreement may complete months later or be cancelled. Revenue recognition depends on completion, not signing date.
- **NParks lock_expired_submissions:** `save(update_fields=...)` must only reference fields that exist on the model. `NParksSubmission` has no `updated_at` field — using it in `update_fields` causes `FieldError`.
- **Environment Variable Validation:** Production settings must validate critical environment variables at startup. A missing `DJANGO_SECRET_KEY` silently falls back to the dev-only default `"dev-only-change-in-production"`.
- **WhatsApp Placeholder:** Return `"status": "FAILED"` instead of fake `"SENT"` for unintegrated services. False-positive success responses mask operational gaps.
- **pytest-xdist Database Contention:** Parallel test processes share the same PostgreSQL test database, causing deadlocks, missing-table errors, and `IntegrityError: duplicate key`. Use `-p no:xdist` for reliable sequential execution in development.
- **Customer Unique Constraints:** `Customer.mobile` has `unique=True` without `null=True` or `blank=True`. Multiple test-created `Customer` objects with default empty-string mobile collide. Always assign unique mobile values in tests.

---

## 🤖 Agent Operating Workflow
Execute all tasks using this strict sequence. Never skip validation.

1. **ANALYZE** - Mine explicit/implicit requirements. Identify ambiguities, edge cases, and compliance constraints.
2. **PLAN** - Draft a sequential, modular implementation roadmap. Present for explicit user confirmation.
3. **VALIDATE** - Halt until user approves plan. Adjust based on feedback.
4. **IMPLEMENT** - Build in testable components. Write tests first (TDD). Document alongside code.
5. **VERIFY** - Run full test suite, typecheck, and lint. Validate against success criteria, security rules, and entity scoping.
6. **DELIVER** - Provide complete code, run instructions, and note architectural decisions or trade-offs.

**Success Criteria:**
- [ ] All queries entity-scoped & PDPA-filtered
- [ ] Auth flows use HttpOnly cookies & direct session reads
- [ ] Pydantic v2 & TS strict mode compliant (0 errors)
- [ ] Tests pass before commit (≥85% backend coverage)
- [ ] Compliance/Finance logic is fully deterministic
- [ ] No anti-patterns present in diff

---
*This document is the single source of truth for code generation. Update only when architectural standards or core patterns change.*
