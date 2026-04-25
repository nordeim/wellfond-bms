---
# Wellfond BMS: Instructional Context
# Project Type: django-nextjs-hybrid
# Architecture: BFF Proxy + Django Ninja API
# Security: HttpOnly Session Cookies + CSRF + Entity Scoping
# Last Updated: 2026-04-25
---

## 1. Project Overview
Wellfond BMS is an enterprise-grade platform designed for Singapore AVS-licensed dog breeding operations. It implements a hardened security architecture and deterministic regulatory logic to manage multi-entity kennel operations.

### Tech Stack
- **Backend:** Django 6.0, Django Ninja (API), PostgreSQL 17, Redis 7.4 (Sessions/Broker), Celery 5.4.
- **Frontend:** Next.js 16 (App Router), Tailwind CSS 4, Radix UI / shadcn/ui.
- **Infrastructure:** Gotenberg 8 (PDF Sidecar), PgBouncer (Transaction Pooling).

## 2. Core Identity & Architectural Mandates

### 2.1 BFF Security Pattern (CRITICAL)
- **Zero JWT:** No tokens are stored in the browser's `localStorage` or `sessionStorage`.
- **HttpOnly Cookies:** Authentication is handled exclusively via the `sessionid` cookie, which is inaccessible to client-side JavaScript.
- **Hardened Proxy:** All frontend API calls MUST go through `/api/proxy/[...path]`. This proxy strips dangerous headers and enforces a strict path allowlist.

### 2.2 Compliance & Determinism
- **Deterministic Logic:** All regulatory calculations (NParks Excel sheets, GST 9/109, AVS transfers) must be pure Python/SQL.
- **Zero AI in Compliance:** Importing AI libraries (Anthropic/OpenAI) is **forbidden** within the `apps/compliance/` module to ensure deterministic outcomes.
- **Audit Immutability:** The `AuditLog` model prevents all `UPDATE` and `DELETE` operations.

### 2.3 Entity Scoping (Multi-Tenancy)
- **QuerySet Scoping:** Every database query must be filtered by `entity_id` using the `scope_entity()` helper in `apps.core.permissions`.
- **RBAC:** Management sees all entities; all other roles (Admin, Sales, Ground, Vet) are hard-scoped to their assigned entity.

## 3. Implementation Standards

### 3.1 Backend (Django Ninja)
- **Authentication:** Read session cookies directly from `request.COOKIES`. Ninja decorators do not always preserve `request.user`.
- **Pydantic v2:** Use `model_validate(user, from_attributes=True)` for serialization instead of `from_orm`.
- **Routers:** Organise endpoints in `routers/{feature}.py` and register them in the main `backend/api.py`.
- **Idempotency:** State-changing requests (POST/PUT/PATCH) require an `X-Idempotency-Key` header, managed by `IdempotencyMiddleware`.

### 3.2 Frontend (Next.js)
- **authFetch:** Use the unified wrapper in `lib/api.ts` for all requests. It automatically handles the BFF proxy and idempotency key injection.
- **Design System:** Strictly adhere to the "Tangerine Sky" palette and Radix UI primitives. Avoid generic "AI-slop" aesthetics.
- **Mobile-First:** Ground operations (`/ground/`) target 44px minimum tap targets for kennel environment usage.

## 4. Key Commands

| Command | Purpose |
|---------|---------|
| `docker-compose up -d postgres redis` | Start infrastructure |
| `python manage.py runserver 0.0.0.0:8000` | Start Backend (Django) |
| `npm run dev` | Start Frontend (Next.js port 3000) |
| `python manage.py migrate` | Apply DB migrations |
| `python manage.py test` | Run Backend tests |
| `npx playwright test` | Run E2E tests |
| `celery -A config worker -l info` | Start Celery worker |

## 5. Anti-Patterns to Avoid
- **DO NOT** store sensitive data in `localStorage`.
- **DO NOT** use `request.user` in Ninja API logic; read from cookies/Redis.
- **DO NOT** bypass the BFF proxy for frontend-to-backend calls.
- **DO NOT** write custom components where `shadcn/ui` (Radix) exists.
- **DO NOT** hardcode entity filters; use `scope_entity()`.

---
*Refer to `PROJECT_KNOWLEDGE_BASE.md` for deep-dive technical specifications.*
