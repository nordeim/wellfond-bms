# Wellfond BMS: Agent Guide

**Purpose:** Authoritative definitive guide to initialize coding agents and engineers with the complete architectural context, implementation standards, and operational mandates required to safely contribute to the Wellfond Breeding Management System.

---

## 1. Core Identity & Purpose
Wellfond BMS is an enterprise-grade platform engineered specifically for Singapore AVS-licensed dog breeding operations. It manages the complete breeding lifecycle: pedigree tracking, health logs, sales agreements, waitlists, and regulatory reporting.

**Core Drivers:**
- **Compliance:** Automates strict AVS/NParks regulatory requirements (NParks submissions, AVS transfer tracking, GST 9/109) with 100% deterministic logic.
- **Security & Multi-Tenancy:** Manages multi-entity operations (Holdings, Katong, Thomson) with robust data isolation, PII/PDPA consent enforcement, and hardened authentication.
- **Operational Efficiency:** Provides a mobile-first, offline-capable PWA for ground staff to log kennel events (heat cycles, whelping, health checks) in real-time.

---

## 2. Technical Stack & Infrastructure
| Layer | Technology | Notes |
|-------|------------|-------|
| **Backend** | Django 6.0 + Django Ninja | Type-safe APIs, Pydantic v2 integration, auto OpenAPI schema |
| **Frontend** | Next.js 16 (App Router) + Tailwind CSS 4 + Radix UI / shadcn/ui | Server Components default, CSS-first Tailwind config, Tangerine Sky design system |
| **Database** | PostgreSQL 17 | Containerized, `wal_level=replica` for PITR, PgBouncer transaction pooling |
| **Cache/Queue** | Redis 7.4 | Triple isolation: Cache (DB 0), Sessions (DB 1), Broker (DB 2) |
| **Async Tasks** | Celery 5.4 | PDF generation, AVS reminders, pedigree closure table rebuilds |
| **PDF Sidecar** | Gotenberg 8 | Chromium-based pixel-perfect rendering for legal agreements |

---

## 3. Architectural Mandates & Security

### 3.1 BFF (Backend-for-Frontend) Security Pattern
- **Zero Direct Backend Access:** The browser never communicates with Django directly. All requests route through the Next.js proxy at `/api/proxy/[...path]`.
- **Header Sanitization:** Proxy strips dangerous headers (`Host`, `X-Forwarded-*`) and enforces a strict API path allowlist.
- **Zero JWT in Browser:** No tokens stored in `localStorage` or `sessionStorage`. Eliminates XSS-based token theft.
- **Session Auth:** Authentication relies exclusively on `HttpOnly, Secure, SameSite=Lax` `sessionid` cookies backed by Redis.

### 3.2 Entity Scoping (Multi-Tenancy)
- **QuerySet Filtering:** Every database query must be scoped using `apps.core.permissions.scope_entity()`.
- **RBAC Enforcement:**
  - `MANAGEMENT`: Sees all data across all entities.
  - `ADMIN`, `SALES`, `GROUND`, `VET`: Hard-scoped to their assigned `entity_id`.
- **Middleware:** `EntityScopingMiddleware` attaches the filter to every request, preventing cross-entity data leakage.

### 3.3 Compliance Determinism & Audit Immutability
- **Pure Logic:** Regulatory calculations (NParks Excel, GST, AVS transfers) must be deterministic Python/SQL.
- **Zero AI in Compliance:** Importing AI libraries (Anthropic, OpenAI, etc.) is strictly forbidden in `apps/compliance/`.
- **Immutability:** `AuditLog` and locked `NParksSubmission` records prohibit `UPDATE` and `DELETE`. Soft-delete (`is_active`) is used elsewhere.

### 3.4 Idempotency & Offline Sync
- **Idempotency Keys:** All state-changing PWA requests (POST/PUT/PATCH) require an `X-Idempotency-Key` (UUIDv4).
- **Redis Caching:** `IdempotencyMiddleware` caches responses for 24 hours. Network flaps triggering retries return the cached response instead of re-executing business logic.

---

## 4. Implementation Standards

### 4.1 Backend (Django + Ninja)
- **Routers:** Each app owns `routers/{feature}.py`. Register in `backend/api/__init__.py`.
- **Pydantic v2:** Use `Model.model_validate(obj, from_attributes=True)` for serialization. Never use `from_orm()`.
- **Error Handling:** Use `ninja.errors.HttpError`. Custom exception handler in `api/__init__.py`. Never expose sensitive data in errors.
- **Code Style:** `black` formatting, `isort` imports, Google-style docstrings, type hints on all public functions, 100-char line limit.

### 4.2 Frontend (Next.js + React)
- **Components:** Server Components by default. Use `'use client'` only for interactivity/hooks.
- **API Wrapper:** Always use `authFetch` from `lib/api.ts`. It handles BFF proxy routing and idempotency key injection.
- **Design System:** Strict adherence to "Tangerine Sky" palette and Radix primitives. Avoid generic/default Tailwind aesthetics.
- **Mobile-First:** `/ground/` route group targets 44px minimum tap targets and high-contrast kennel environments.
- **TypeScript:** `strict: true`. Never use `any` (use `unknown`). Explicit parameter types. `interface` for objects, `type` for unions.

### 4.3 Authentication Pattern (CRITICAL)
Django Ninja does not reliably preserve `request.user` across decorators or pagination. **Always read the session cookie directly:**
```python
def _check_admin_permission(request):
    from apps.core.auth import SessionManager, AuthenticationService
    session_key = request.COOKIES.get(AuthenticationService.COOKIE_NAME)
    session_data = SessionManager.get_session(session_key)
    if not session_data:
        raise HttpError(401, "Unauthorized")
    user = User.objects.get(id=session_data["user_id"])
    # ... proceed with validation
```

---

## 5. Development Workflow & Commands

### 5.1 Environment Setup
```bash
# 1. Infrastructure
docker-compose up -d postgres redis

# 2. Backend
cd backend
python manage.py migrate
python manage.py shell -c "from apps.core.models import User; User.objects.create_superuser('admin', 'admin@wellfond.sg', 'Wellfond@2024!', role='management')"

# 3. Frontend
cd ../frontend
npm install

# 4. Run Hybrid Mode
# Terminal 1: python manage.py runserver 0.0.0.0:8000
# Terminal 2: npm run dev
```

### 5.2 Command Reference
| Context | Command | Purpose |
|---------|---------|---------|
| **Backend** | `python manage.py runserver 0.0.0.0:8000` | Start Django dev server |
| | `python manage.py migrate` / `makemigrations` | DB schema management |
| | `python manage.py shell` | Interactive debugging |
| | `pytest tests/` | Run backend test suite |
| | `celery -A config worker -l info` | Start async worker |
| | `celery -A config beat -l info` | Start scheduler |
| **Frontend** | `npm run dev` | Next.js dev server (:3000) |
| | `npm run build` / `lint` / `typecheck` | Build & quality checks |
| | `npx vitest` | Unit tests |
| | `npx playwright test` | E2E critical paths |
| **Docker** | `docker-compose up -d postgres redis` | Start infra containers |
| | `docker-compose logs -f postgres/redis` | Stream container logs |

---

## 6. Testing Strategy & TDD
- **Backend:** `pytest` for unit/integration tests. Target: ≥85% coverage.
- **Frontend:** `Vitest` for units, `Playwright` for E2E (Login, Wizard, NParks Gen).
- **TDD Mandate:** Write a failing test for every bug fix or feature. Follow Red → Green → Refactor.
- **Verification:** Validate endpoints with `curl` or Django test client before merging.

---

## 7. Git, Version Control & Documentation
- **Branching:** `feature/{id}-{desc}`, `fix/{id}-{desc}`, `refactor/{desc}`. Short-lived (1-3 days).
- **Commits:** Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`). Atomic, one logical change per commit. Reference ticket IDs.
- **Documentation:** Explain "why", not just "what". Update guides when conventions shift. Use Mermaid for complex flows. API docs auto-generated at `/api/v1/docs/`.

---

## 8. Project Structure & API Design
**API Conventions:**
- Base: `/api/v1/` | Auth: `/api/v1/auth/*` | Resources: `/api/v1/{resource}/`
- Responses: Consistent Pydantic models. Never hardcode entity IDs; rely on session scoping.

**Directory Hierarchy:**
```
wellfond-bms/
├── backend/
│   ├── api/               # Ninja API registry & exception handler
│   ├── apps/
│   │   ├── core/          # Auth, RBAC, Audit, Entity, SessionManager
│   │   ├── operations/    # Dogs, Logs, PWA Sync
│   │   ├── breeding/      # Genetics, COI, Litters
│   │   ├── sales/         # Sales, waitlist, invoices
│   │   ├── compliance/    # NParks, GST (Deterministic)
│   │   ├── customers/     # Customers, PDPA consent
│   │   ├── finance/       # Invoicing, payments
│   │   └── ai_sandbox/    # Isolated AI experiments
│   └── config/            # Settings (Base/Dev/Prod)
├── frontend/
│   ├── app/               # App Router (BFF Proxy inside)
│   ├── components/        # Radix-based UI (Tangerine Sky)
│   └── lib/               # authFetch, offline-queue, types
├── tests/                 # Backend pytest suite
└── infra/                 # Docker/PostgreSQL/Redis configs
```

**Database Patterns:**
- UUID primary keys, `created_at`/`updated_at` timestamps.
- Soft-delete via `is_active` flag (never hard delete).
- Immutable `AuditLog`. Migrations only; never modify DB directly.

**Environment Variables:**
`DATABASE_URL`, `REDIS_CACHE_URL` (DB 0), `REDIS_SESSIONS_URL` (DB 1), `SECRET_KEY`, `JWT_SECRET`

---

## 9. Anti-Patterns & Troubleshooting

### 🚫 Strict Anti-Patterns
- NO JWT/tokens in browser storage.
- NO `request.user` reliance in Ninja endpoints.
- NO bypassing the BFF proxy.
- NO custom UI components when shadcn/Radix exists.
- NO hardcoded entity filters; use `scope_entity()`.
- NO PII access without explicit PDPA consent.
- NO magic numbers; use `lib/constants.ts`.
- NO synchronous AVS/compliance calls; delegate to Celery.
- NO AI imports in `apps/compliance/`.

### 🔍 Common Troubleshooting
| Symptom | Resolution |
|---------|------------|
| Session not persisting | Verify Redis connection (`redis-cli ping`), check `SESSION_ENGINE`, validate cookie domain/SameSite settings |
| Ninja router 404 | Ensure `api.add_router()` in `api/__init__.py`, check import errors, clear `__pycache__` |
| Frontend proxy 404 | Verify Django running on `:8000`, check `app/api/proxy/[...path]/route.ts`, test backend directly via `curl` |
| Type/Schema mismatch | Run `npm run typecheck`, ensure Pydantic schema fields exactly match ORM model, verify `from_attributes=True` |
| Celery tasks stuck | Check broker URL, verify worker/beat are running, inspect Redis queue depth |

---

## 10. Agent Workflow Protocol (Six-Phase)
All implementation tasks must follow this structured approach:
1. **ANALYZE:** Deep requirement mining. Identify explicit/implicit needs, edge cases, and risks. No surface assumptions.
2. **PLAN:** Create a sequential, modular execution roadmap. Present for explicit confirmation.
3. **VALIDATE:** Checkpoint for user approval. Address concerns before coding.
4. **IMPLEMENT:** Build in logical, testable components. Co-locate docs. Adhere strictly to standards.
5. **VERIFY:** Rigorous QA against success criteria. Test security, performance, accessibility, and entity scoping.
6. **DELIVER:** Complete handoff with run instructions, documented challenges, and next-step recommendations.

---

## ⚠️ Appendix: Identified Conflicts & Clarifications
*The following inconsistencies were detected across the source documents and require architectural clarification or standardization:*

| Conflict Area | Details | Recommended Resolution |
|---------------|---------|------------------------|
| **Token Expiry vs. Zero JWT** | Docs state `Access tokens expire in 15m; refresh tokens in 7d` alongside a strict `Zero JWT` & `HttpOnly sessionid` mandate. | Clarify if short-lived tokens are used internally (service-to-service) or if this is legacy text. Browser auth should remain purely Redis-session based. |
| **JWT_SECRET Env Var** | `JWT_SECRET` is listed in environment variables despite the `Zero JWT` architecture mandate. | Remove `JWT_SECRET` if unused, or document its exact internal purpose (e.g., signing internal service payloads). |
| **Test Execution Command** | Some docs suggest running tests via `python test_auth_refresh_endpoint.py`, which bypasses `pytest` discovery/fixtures. | Standardize exclusively on `pytest tests/` or `python -m pytest tests/` for proper fixture/plugin loading. |
| **App Directory Variance** | Core manifest omits `sales/`, `customers/`, `finance/` apps, while agent docs include them. | Merged into the definitive structure above. Ensure all routers are registered and entity-scoped. |
| **Hardcoded Paths** | Setup instructions reference `/home/project/wellfond-bms`. | Replaced with relative/project-root references to ensure environment agnosticism. |
| **Redis Isolation** | Manifest mentions "triple-instance isolation", while env vars show logical DB separation (0, 1). | Logical DB separation is acceptable for dev/staging. Production should use separate Redis instances or ACLs to enforce true isolation. |

*This document is a living artifact. Update it as architectural shifts occur or conflicts are resolved.*
