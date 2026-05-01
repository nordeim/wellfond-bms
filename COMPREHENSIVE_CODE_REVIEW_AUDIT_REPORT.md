# Wellfond BMS — Comprehensive Code Review & Audit Report

**Date:** 2026-05-01
**Auditor:** Independent AI Agent Review
**Scope:** Full-stack audit of backend, frontend, infrastructure, tests, compliance, and security against planning documents (AGENTS.md, draft_plan.md, IMPLEMENTATION_PLAN.md, phases 0-8)
**Classification:** CONFIDENTIAL

---

## 1. Executive Summary

The Wellfond BMS codebase represents a substantial implementation effort across 9 phases (0-8 complete, Phase 9 in backlog). While the project demonstrates strong architectural intent and many correct patterns (BFF proxy, HttpOnly cookies, native Celery, deterministic compliance logic, closure table for COI), the **audit reveals significant gaps between planning documents and actual implementation**.

**Critical concerns** include missing entity scoping in core business routers, broken test auth patterns that will fail in production, session storage using the wrong Redis cache backend, and a BFF proxy CORS preflight that violates the same-origin credential model. **High-priority issues** span PDPA filtering gaps in compliance paths, Pydantic v2 anti-patterns in production code, and an offline queue that still uses `localStorage` instead of the planned `IndexedDB` with background sync.

**Verdict:** The codebase is **NOT production-ready** without remediation of critical and high-priority findings. Phase completion claims (0-8 at 100%) are **overstated** — several foundational security and compliance controls are either incomplete or implemented with deviations from the architectural specification.

---

## 2. Audit Methodology

1. **Document Ground Truth:** Read AGENTS.md, draft_plan.md (MEP v1.1), IMPLEMENTATION_PLAN.md, README.md, and all 9 phase sub-plans.
2. **Static Code Analysis:** Systematic grep and read of all backend Python source (models, routers, services, settings) and frontend TypeScript (components, hooks, lib, API proxy).
3. **Anti-Pattern Detection:** Searched for all patterns listed in AGENTS.md Anti-Patterns table (`from_orm`, `T | None`, `@paginate`, `self.pk`, direct sync ORM in async routes, etc.).
4. **Security Scan:** Reviewed cookie settings, CORS, CSP, BFF proxy path validation, header sanitization, SSRF protection, and credential storage.
5. **Compliance Verification:** Checked for AI imports in compliance/finance/sales paths, GST formula accuracy, PDPA hard filters, audit immutability, and NParks determinism.
6. **Test Quality Review:** Examined test fixtures for `force_login` violations, coverage distribution, and factory usage.
7. **Infrastructure Review:** Analyzed docker-compose, settings split (base/dev/prod), Redis isolation, and PgBouncer configuration.

---

## 3. Critical Findings (Severity: CRITICAL — Block Production)

### C1. Missing Entity Scoping in Core Business Routers
**Files:** `backend/apps/breeding/routers/mating.py`, `backend/apps/breeding/routers/litters.py`, `backend/apps/compliance/routers/nparks.py`, `backend/apps/compliance/routers/gst.py`, `backend/apps/compliance/routers/pdpa.py`, `backend/apps/sales/routers/agreements.py`, `backend/apps/sales/routers/avs.py`, `backend/apps/core/routers/users.py`

**Issue:** These routers do **not** use `scope_entity()` for list/query endpoints. While some implement ad-hoc role checks (`if not user.has_role("management")`), this is inconsistent and error-prone. The `scope_entity()` utility from `apps.core.permissions` is the mandated pattern per AGENTS.md and phase plans.

**Risk:** Cross-entity data leakage. A SALES user from Katong could potentially access Holdings breeding records or NParks submissions by crafting requests with different IDs.

**Ground Truth Violation:** Phase-1 plan states: *"Mandatory: Every data query must respect entity boundaries. Pattern: `queryset = scope_entity(Model.objects.all(), request.user)`"*. Phase-2 checklist: *"Entity scoping prevents cross-entity data leakage"*.

**Recommendation:** Add `scope_entity()` to **every** queryset in every router. Create a middleware or decorator that auto-scopes if the model has an `entity` FK.

---

### C2. `force_login` Anti-Pattern in Tests (Breaks Ninja Auth)
**Files:** `backend/apps/core/tests/test_dashboard.py` (7 instances), `backend/apps/core/tests/test_dashboard_integration.py` (9 instances), `backend/apps/operations/tests/test_dogs.py` (1 instance)

**Issue:** Tests use `client.force_login(user)` which populates Django's native `request.user` but **does not** create the Redis session cookie that the custom `AuthenticationMiddleware` expects. Per AGENTS.md: *"`force_login` breaks Ninja routers. Use session-based fixtures."*

**Risk:** Tests pass in isolation but would fail against the real Redis-backed auth layer. This creates a false sense of security and means auth integration is untested.

**Recommendation:** Replace all `force_login` with the session fixture pattern from AGENTS.md:
```python
@pytest.fixture
def authenticated_client(test_user):
    key, _ = SessionManager.create_session(test_user, request)
    client.cookies[AuthenticationService.COOKIE_NAME] = key
    return client
```

---

### C3. Session Manager Uses Wrong Redis Cache Backend
**File:** `backend/apps/core/auth.py` lines 55, 62, 72, 80, 88

**Issue:** `SessionManager` uses `cache` (the default Django cache alias) instead of `caches["sessions"]`. The base settings define three separate Redis instances (`default`, `sessions`, `idempotency`), but session data is being written to the default cache, which shares space with general Django caching.

**Risk:** Cache eviction on the general cache could destroy active user sessions. Session data could be read/modified by general cache operations. Violates the isolation principle from Phase 0.

**Ground Truth Violation:** Phase-0 plan: *"Redis instances isolated (sessions ≠ broker ≠ cache)"*.

**Recommendation:** Change all `cache.set()` / `cache.get()` / `cache.delete()` in `SessionManager` to `caches["sessions"].set()` etc.

---

### C4. BFF Proxy CORS Preflight Violates Credentials + Wildcard
**File:** `frontend/app/api/proxy/[...path]/route.ts` lines 204-214

**Issue:** The `OPTIONS` handler returns:
```
'Access-Control-Allow-Origin': '*'
'Access-Control-Allow-Credentials': 'true'
```

Per the Fetch spec and all modern browsers, `Access-Control-Allow-Origin: *` **cannot** be used with `Access-Control-Allow-Credentials: true`. Browsers will reject the response, breaking CORS preflight for authenticated requests.

**Risk:** BFF proxy will fail for cross-origin deployments (e.g., frontend on Vercel, backend on AWS). This is a spec violation that causes silent fetch failures in production.

**Recommendation:** Echo the requesting `Origin` header instead of `*`, or maintain an allowlist of origins and return the matched origin.

---

### C5. `@paginate` Decorator Used with Custom Response Type
**File:** `backend/apps/core/routers/users.py` line 48

**Issue:** `@paginate` is applied to `list_users` which returns `list[UserResponse]`. Per AGENTS.md: *"`@paginate` decorator fails with wrapped/custom response objects. Implement manual pagination for all list endpoints."* The plan_fix_django_router.md document explicitly warns about this causing import-time crashes.

**Risk:** Router registration may crash at import time, or pagination metadata may be missing/broken.

**Recommendation:** Remove `@paginate` and implement manual slice+count pagination (as done correctly in `apps.sales.routers.agreements` and `apps.finance.routers.reports`).

---

### C6. `self.pk` Anti-Pattern in Immutable Models
**Files:** `backend/apps/core/models.py:178`, `backend/apps/compliance/models.py:201`, `backend/apps/customers/models.py:192`

**Issue:** These models use `self.pk` to detect new vs. existing records. AGENTS.md explicitly states: *"New Record Detection: Use `self._state.adding` in `save()`, not `self.pk`."* Using `self.pk` fails for UUID primary keys that are pre-assigned (`default=uuid.uuid4`) before the first save.

**Risk:** `AuditLog` may incorrectly reject legitimate creates because `self.pk` is already populated. `PDPAConsentLog` and `CommunicationLog` have the same flaw.

**Recommendation:** Replace `if self.pk and ...` with `if not self._state.adding and ...`.

---

### C7. `SESSION_COOKIE_SECURE` Tied to `DEBUG` Flag
**File:** `backend/apps/core/auth.py` line 142

**Issue:** `secure=not settings.DEBUG` means in any non-DEBUG environment where `DEBUG` might be accidentally `True` (common in staging misconfigurations), the session cookie is sent over HTTP. The cookie is also never explicitly set with `SESSION_COOKIE_SECURE` in the auth service layer — it relies on Django's global setting, creating dual sources of truth.

**Risk:** Session hijacking via MITM if staging or misconfigured production ever runs with `DEBUG=True`.

**Recommendation:** Always set `secure=True` unconditionally in the auth service. Override with an explicit `INSECURE_COOKIES_FOR_LOCAL_DEV` env var if needed for local testing without HTTPS.

---

## 4. High-Priority Issues (Severity: HIGH)

### H1. Missing PDPA Hard Filter in Compliance & Sales Querysets
**Files:** `backend/apps/compliance/routers/nparks.py`, `backend/apps/compliance/routers/pdpa.py`, `backend/apps/sales/routers/agreements.py`, `backend/apps/customers/routers/customers.py`

**Issue:** The `enforce_pdpa()` function exists in `permissions.py` but is **not used** in any router. SalesAgreement lists customers by mobile/name without filtering `pdpa_consent=True`. The customers router lists all customers regardless of PDPA status.

**Risk:** PDPA violation under Singapore law. PII of opted-out customers is returned in API responses and could be used for marketing blasts.

**Ground Truth Violation:** Phase-6 checklist: *"PDPA filter blocks opted-out at DB query level"*. Phase-7 checklist: *"Blasts respect PDPA hard filter."*

**Recommendation:** Apply `enforce_pdpa()` to every queryset that touches customer/buyer/user data. Make it a middleware or model manager default.

---

### H2. `update_or_create` Used in GST Ledger (Violates Immutability)
**File:** `backend/apps/compliance/services/gst.py` lines 198-206

**Issue:** `GSTLedger.objects.update_or_create(...)` updates existing ledger entries when an agreement changes. The draft plan specifies *"Immutable audit trails"* and *"AuditLog no UPDATE/DELETE"*. GST ledger entries should be append-only for tax audit integrity.

**Risk:** Tax authority audit finds mutable records. Cannot reconstruct historical state.

**Recommendation:** Remove `update_or_create`. Create new ledger entries for amendments and link them with a version chain. Use `created_at` to determine the active version.

---

### H3. `AuthenticationService.get_user_from_request` vs. `get_authenticated_user`
**Files:** Multiple routers across sales, breeding, compliance, customers

**Issue:** Many routers use `AuthenticationService.get_user_from_request(request)` (a method that does not exist in the auth.py file reviewed — it may have been added, but the canonical pattern in AGENTS.md is `get_authenticated_user(request)`). This inconsistency creates multiple auth paths.

**Risk:** If `get_user_from_request` has different semantics than `get_authenticated_user`, some endpoints may bypass the correct Redis session validation.

**Recommendation:** Standardize on `get_authenticated_user(request)` everywhere. Remove or deprecate any duplicate methods.

---

### H4. Celery Version Mismatch (5.6.2 vs. Specified 5.4)
**File:** `backend/requirements/base.txt` line 63

**Issue:** Requirements pin `celery==5.6.2`. AGENTS.md states `Celery 5.4` and the draft plan specifies `celery>=5.4`. While 5.6.2 is newer, it is a major version jump that has not been validated against the project's `django-celery-beat`, `opentelemetry-instrumentation-celery`, or Django 6.0.4 compatibility.

**Risk:** Undiscovered breaking changes in Celery 5.6.x could break beat scheduling, task routing, or DLQ behavior.

**Recommendation:** Pin to a validated minor version. Test all Celery tasks end-to-end before upgrading.

---

### H5. OpenTelemetry Beta Dependencies in Production Requirements
**File:** `backend/requirements/base.txt` lines 79-83

**Issue:** `opentelemetry-instrumentation-celery==0.60b1` and other OTel packages are **beta** versions (`b1` suffix). These are in `base.txt` (production dependencies) despite Phase 9 (Observability) being in backlog.

**Risk:** Beta packages in production are unsupported and may contain bugs or breaking API changes.

**Recommendation:** Move all OTel packages to `dev.txt` or a separate `observability.txt` extra. Do not install them in production containers until Phase 9 is validated.

---

### H6. Frontend Offline Queue Still Uses `localStorage` (Not IndexedDB)
**File:** `frontend/lib/offline-queue.ts` line 6

**Issue:** The file header explicitly states: *"TODO: Migrate from localStorage to IndexedDB for production."* The README and Phase-3 plan claim a complete IndexedDB offline queue with background sync. The actual implementation uses `localStorage`.

**Risk:** `localStorage` is synchronous, blocks the main thread, has a ~5MB limit, and does not support structured data or background sync. Ground staff in poor connectivity areas will experience UI jank and potential data loss.

**Ground Truth Violation:** Phase-3 checklist: *"Offline logs queue in IndexedDB, sync on reconnect"*.

**Recommendation:** Complete the migration to IndexedDB using the existing `lib/offline-queue/` directory (adapter.idb.ts, db.ts, types.ts) which appears to have partial scaffolding. Remove `localStorage` fallback entirely.

---

### H7. `unique_together` Deprecated in Favor of `UniqueConstraint`
**File:** `backend/apps/breeding/models.py` line 363

**Issue:** `DogClosure.Meta.unique_together = ["ancestor", "descendant"]` uses the deprecated Django API. Django 6.0 still supports it but emits deprecation warnings. Future Django versions may remove it.

**Risk:** Forward compatibility issue. CI builds with `python -W error` would fail.

**Recommendation:** Replace with `constraints = [models.UniqueConstraint(fields=["ancestor", "descendant"], name="unique_ancestor_descendant")]`.

---

### H8. Missing `apps.ai_sandbox` in `INSTALLED_APPS`
**File:** `backend/config/settings/base.py` lines 40-41

**Issue:** `apps.ai_sandbox` is commented out in `INSTALLED_APPS`, yet `backend/apps/apps.py` defines it as `name = "apps.ai_sandbox"`. If any code imports from `ai_sandbox`, Django will raise `AppRegistryNotReady` or `LookupError`.

**Risk:** If future development adds AI sandbox features without uncommenting the app, the project will crash on startup.

**Recommendation:** Either add `apps.ai_sandbox` to `INSTALLED_APPS` (if it contains runnable code) or remove `apps/apps.py` if the app is truly not yet implemented.

---

### H9. Frontend `canAccessRoute` Permissive Default for Unmatched Routes
**File:** `frontend/lib/auth.ts` lines 194-211

**Issue:** `canAccessRoute` returns `true` for any route not explicitly defined in `ROUTE_ACCESS`. This is a "fail-open" security model.

**Risk:** New pages added by developers that are not in the route map become accessible to all roles by default.

**Recommendation:** Change default to `return false` (fail-closed). Add an explicit admin-only wildcard or require explicit registration.

---

## 5. Medium-Priority Issues (Severity: MEDIUM)

### M1. `nparks.py` Missing `from_attributes=True` in `model_validate`
**File:** `backend/apps/compliance/routers/nparks.py` line 66

**Issue:** `NParksSubmissionResponse.model_validate(submission)` does not pass `from_attributes=True`. Pydantic v2 requires this flag to read attributes from ORM objects.

**Risk:** ValidationError at runtime when the endpoint is exercised.

**Recommendation:** Change to `NParksSubmissionResponse.model_validate(submission, from_attributes=True)`.

---

### M2. Several Models Lack `updated_at`
**Files:** `backend/apps/breeding/models.py` (`DogClosure`, `MateCheckOverride`), `backend/apps/compliance/models.py` (multiple), `backend/apps/operations/models.py` (`InHeatLog`, `MatedLog`, `WhelpedLog`, etc.)

**Issue:** Many log/audit models only have `created_at` without `updated_at`. While some are truly append-only, others (like `BreedingRecord`, `Litter`) do have `updated_at`.

**Recommendation:** Ensure consistency. Either add `updated_at` to all non-immutable models, or document why specific models intentionally omit it.

---

### M3. `Dog` Model `age_years` Property Uses 365.25 (Leap Year Drift)
**File:** `backend/apps/operations/models.py` line 132

**Issue:** `(today - self.dob).days / 365.25` accumulates error over decades. A 6-year rehome threshold could trigger a few days early/late.

**Recommendation:** Use `dateutil.relativedelta` for calendar-accurate age.

---

### M4. Docker Compose Dev Uses Trust Auth and Exposes Redis Globally
**File:** `infra/docker/docker-compose.yml`

**Issue:** `POSTGRES_HOST_AUTH_METHOD: trust` allows any connection without password. Redis port is bound to `0.0.0.0:6379` instead of `127.0.0.1`.

**Risk:** On shared development machines or CI runners, PostgreSQL and Redis are accessible to other users/processes without authentication.

**Recommendation:** Use `scram-sha-256` with the password from env. Bind Redis to `127.0.0.1` only.

---

### M5. `development.py` CORS Allow-All Weakens Security
**File:** `backend/config/settings/development.py` line 23

**Issue:** `CORS_ALLOW_ALL_ORIGINS = True` in development settings. While convenient, it trains developers to ignore CORS issues that will appear in production.

**Recommendation:** Use the same explicit origin list as production, plus `http://localhost:3000`.

---

### M6. PgBouncer Mentioned in Plans but Absent from Docker Compose
**File:** `plans/phase-0-infrastructure.md`

**Issue:** The architecture specification requires PgBouncer for transaction pooling. The development docker-compose connects Django directly to PostgreSQL. The production `docker-compose.yml` does not exist at the repository root — only `infra/docker/docker-compose.yml` (dev) is present.

**Risk:** Connection pool exhaustion under load. Developers never test PgBouncer compatibility locally.

**Recommendation:** Add PgBouncer service to the dev compose (or a dedicated `docker-compose.prod.yml`) and test `CONN_MAX_AGE=0` behavior.

---

### M7. `CSP_STYLE_SRC` Allows `'unsafe-inline'` Unconditionally
**File:** `backend/config/settings/base.py` line 222

**Issue:** CSP allows inline styles globally. While Tailwind JIT may need this, a stricter approach would use CSP nonces or hash-based allowlists.

**Risk:** XSS via inline style injection (though lower severity than script injection).

**Recommendation:** Evaluate if Tailwind v4 still requires this in the build output. If using compiled CSS, remove `'unsafe-inline'`.

---

### M8. `SalesAgreement` Model Lacks `pdf_hash` Field
**Ground Truth:** README.md Phase-5 section claims: *"`pdf_hash` SHA-256"* and *"PDF hash matches stored record; tamper-evident"*.

**Issue:** The `SalesAgreement` model file reviewed does not show a `pdf_hash` field in the first 100 lines. The `pdf_hash` may be stored on a related model, but if absent, the tamper-evident claim is unfulfilled.

**Recommendation:** Verify and add `pdf_hash = models.CharField(max_length=64, blank=True)` to `SalesAgreement` if missing.

---

## 6. Architecture & Design Gaps

### A1. No Unified Entity Scoping Middleware Enforcement
The `EntityScopingMiddleware` attaches `request.entity_filter` but does not automatically scope querysets. Every developer must remember to call `scope_entity()`. This is a human-factor vulnerability.

**Recommendation:** Create a custom `EntityScopedManager` or `EntityScopedQuerySet` that auto-applies the filter based on `request.user` when `.all()` is called inside a request context.

---

### A2. `require_entity_access` Decorator vs. `scope_entity()` Function
Both exist but have overlapping responsibilities. `require_entity_access` is a decorator that mutates `request`, while `scope_entity` is a function that filters querysets. Some routers use one, some use the other, some use neither. This inconsistency is a maintenance burden.

---

### A3. Duplicate `List` Import in `mating.py`
**File:** `backend/apps/breeding/routers/mating.py` lines 13-15

```python
from typing import List
from typing import List  # Duplicate
```

Minor code quality issue but indicates insufficient linting in CI.

---

### A4. Missing `PNLResult` Dataclass with `frozenset` Claim
README Phase-8 claims: *"PNLResult dataclass with frozenset for immutability"*. The actual `finance/services/pnl.py` was not reviewed in depth, but if this pattern is absent, it contradicts the documented architecture.

---

## 7. Security Assessment

| Control | Status | Notes |
|---------|--------|-------|
| **HttpOnly Cookies** | ✅ Partial | `auth.py` sets HttpOnly, but `SESSION_COOKIE_SECURE` is conditional on DEBUG |
| **Zero JWT Exposure** | ✅ Pass | No JWT in localStorage or cookies |
| **BFF Path Allowlist** | ✅ Pass | Regex validation with traversal rejection |
| **Header Sanitization** | ✅ Pass | Strips `X-Forwarded-*` and `Host` |
| **CORS** | ⚠️ Fail | `OPTIONS` returns `*` + `credentials=true` |
| **CSP** | ⚠️ Fail | `'unsafe-inline'` in styles; `'unsafe-eval'` in dev |
| **SSRF Protection** | ✅ Pass | `BACKEND_INTERNAL_URL` is server-only; no client-side exposure |
| **Rate Limiting** | ✅ Pass | `django-ratelimit` on auth endpoints |
| **Entity Isolation** | 🔴 Fail | Missing in multiple routers |
| **PDPA Filtering** | 🔴 Fail | `enforce_pdpa()` exists but is unused |
| **Audit Immutability** | ⚠️ Fail | `AuditLog` uses `self.pk`; `GSTLedger` uses `update_or_create` |
| **Idempotency** | ✅ Pass | Dedicated Redis cache; 24h TTL; required on state-changing paths |
| **CSRF Rotation** | ✅ Pass | Rotated on login and refresh |

---

## 8. Compliance & Regulatory Gaps

| Requirement | Plan Spec | Implementation | Status |
|-------------|-----------|----------------|--------|
| **NParks Excel** | 5-document, deterministic | Present in `nparks.py` | ✅ |
| **GST 9/109** | `Decimal(price) * 9 / 109`, `ROUND_HALF_UP` | Implemented correctly in `gst.py` | ✅ |
| **Thomson=0%** | Case-insensitive check | `entity.code.upper() == "THOMSON"` | ✅ |
| **PDPA Hard Block** | `WHERE consent=true` at queryset | Function exists, not applied | 🔴 |
| **Zero AI in Compliance** | No AI imports | Verified: 0 matches | ✅ |
| **AVS 3-Day Reminder** | Celery Beat daily | Schedule present in `CELERY_BEAT_SCHEDULE` | ✅ |
| **Month Lock** | Immutable lock after submit | Not verified in this audit | ⚠️ |
| **PDF Hash** | SHA-256 tamper-evident | Claimed but field not confirmed | ⚠️ |

---

## 9. Performance & Scalability

| Target | Spec | Assessment |
|--------|------|------------|
| **COI <500ms** | p95, 5-gen | Closure table + raw SQL query is efficient. Async wrapper uses `sync_to_async(thread_sensitive=True)`. Likely meets target for moderate pedigrees. Load testing required. |
| **Dashboard <2s** | SG broadband | Not measured. No OTel instrumentation in place (Phase 9 backlog). |
| **NParks <3s** | Excel generation | Not measured. `openpyxl` template injection is typically fast for 5 sheets. |
| **SSE <500ms** | Alert delivery | Uses 5s poll interval, not true push. Target refers to end-to-end from log creation to SSE emission, which depends on DB write speed. |
| **Closure Table Rebuild** | Async Celery, no triggers | `tasks.py` present. No DB triggers verified in migrations. |

---

## 10. Test Coverage & Quality

| Module | Tests Present | Quality Notes |
|--------|---------------|---------------|
| `core/auth` | ✅ `test_auth.py` | Uses proper session fixtures (correct) |
| `core/permissions` | ✅ `test_permissions.py` | Correct pattern |
| `core/middleware` | ✅ Multiple test files | Tests idempotency, rate limiting, middleware order |
| `operations/dogs` | ✅ `test_dogs.py` | Uses `force_login` (critical anti-pattern) |
| `operations/logs` | ✅ `test_log_models.py` | Model validation tests |
| `operations/importers` | ✅ `test_importers.py` | CSV import tests |
| `operations/draminski` | ✅ `test_draminski.py` | 20 tests including zone casing |
| `operations/sse` | ✅ `test_sse_async.py` | Async stream tests |
| `breeding/coi` | ✅ `test_coi.py`, `test_coi_async.py` | 8 + async tests |
| `breeding/saturation` | ✅ `test_saturation.py` | 5 tests |
| `sales/agreements` | ✅ `test_agreement.py` | Present |
| `sales/avs` | ✅ `test_avs.py` | Present |
| `sales/pdf` | ✅ `test_pdf.py` | Present |
| `sales/gst` | ✅ `test_gst.py`, `test_gst_fix.py` | Present |
| `compliance/gst` | ✅ `test_gst.py` | Present |
| `compliance/nparks` | ✅ `test_nparks.py` | Present |
| `compliance/pdpa` | ✅ `test_pdpa.py` | Present |
| `customers/blast` | ✅ `test_blast.py` | Present |
| `customers/segmentation` | ✅ `test_segmentation.py` | Present |
| `finance/pnl` | ✅ `test_pnl.py` | 7 tests |
| `finance/gst` | ✅ `test_gst.py` | 4 tests |
| `finance/transactions` | ✅ `test_transactions.py` | 8 tests |

**Coverage Estimate:** Backend test count appears strong (70+ tests across modules). However, the `force_login` issue in `test_dashboard.py`, `test_dashboard_integration.py`, and `test_dogs.py` means those tests are **not testing the actual auth path**. If corrected, some may fail due to missing `scope_entity` or other integration issues.

**Frontend Tests:** Present but minimal. `dashboard.test.tsx`, `use-auth.test.ts`, `offline-queue.test.ts`, and Playwright E2E specs exist. Coverage likely below 50% for frontend business logic.

---

## 11. Frontend Assessment

| Component | Status | Issues |
|-----------|--------|--------|
| **BFF Proxy** | ✅ Implemented | CORS preflight bug (C4) |
| **Auth (lib/auth.ts)** | ✅ Implemented | `canAccessRoute` fail-open (H9) |
| **API Client (lib/api.ts)** | ✅ Implemented | Uses `BACKEND_INTERNAL_URL` correctly; idempotency keys injected |
| **Offline Queue** | ⚠️ Partial | Still `localStorage`; IndexedDB scaffold exists but unused (H6) |
| **PWA SW** | ✅ Implemented | `public/sw.js` exists |
| **Manifest** | ✅ Implemented | `public/manifest.json` exists |
| **Ground Components** | ✅ Implemented | 12 components present |
| **Dashboard Components** | ✅ Implemented | 7 components present |
| **Sales Wizard** | ✅ Implemented | Agreement wizard, signature pad, preview panel |
| **TypeScript Strict** | ✅ Pass | `tsconfig.json` has `strict: true` |

---

## 12. Infrastructure & DevOps

| Component | Plan Spec | Actual | Status |
|-----------|-----------|--------|--------|
| **PostgreSQL 17** | `postgres:17-alpine`, `wal_level=replica` | `postgres:17-trixie` used in dev; `wal_level=replica` confirmed | ⚠️ |
| **PgBouncer** | Transaction pooling | **Absent** from docker-compose | 🔴 |
| **Redis Split** | Sessions/Broker/Cache isolated | Dev uses single Redis with DB numbers (0/1/2). Acceptable for dev. | ⚠️ |
| **Gotenberg** | Sidecar for PDF | Present in requirements, PDF service checks health | ✅ |
| **Celery Worker/Beat** | Native `@shared_task` | Configured in `celery.py`, beat schedule present | ✅ |
| **Docker Multi-stage** | Builder + Runtime + Trivy | Dockerfiles present but not validated in this audit | ✅ |
| **CI/CD** | GitHub Actions | `.github/workflows/ci.yml` present | ✅ |
| **Nginx/SSL** | Terminates HTTPS, proxies to Next.js | Config in `infra/docker/nginx/` | ✅ |

---

## 13. Remediation Recommendations (Prioritized)

### Immediate (Block Release)
1. **Fix C4:** Update BFF proxy `OPTIONS` to echo origin instead of `*`.
2. **Fix C1:** Add `scope_entity()` to **all** routers lacking it (breeding, compliance, sales, users).
3. **Fix C3:** Change `SessionManager` to use `caches["sessions"]` exclusively.
4. **Fix C2:** Replace all `force_login` in tests with Redis session fixtures.
5. **Fix C5:** Remove `@paginate` from `users.py` and implement manual pagination.
6. **Fix C6:** Replace `self.pk` with `self._state.adding` in `AuditLog`, `PDPAConsentLog`, `CommunicationLog`.
7. **Fix C7:** Force `secure=True` unconditionally for session cookies.

### High Priority (Fix Before UAT)
8. **Fix H1:** Apply `enforce_pdpa()` to all customer/buyer/user querysets.
9. **Fix H2:** Make `GSTLedger` append-only; remove `update_or_create`.
10. **Fix H3:** Standardize auth to `get_authenticated_user()` everywhere.
11. **Fix H6:** Complete IndexedDB offline queue; remove `localStorage` implementation.
12. **Fix H4/H5:** Validate Celery 5.6.2 compatibility or downgrade to 5.4. Remove beta OTel packages from `base.txt`.
13. **Fix H7:** Replace `unique_together` with `UniqueConstraint`.
14. **Fix H9:** Change `canAccessRoute` default to `false`.

### Medium Priority (Fix Before GA)
15. **Fix M1:** Add `from_attributes=True` to all `model_validate()` calls with ORM objects.
16. **Fix M4/M6:** Harden dev docker-compose (trust auth → scram-sha-256; Redis bind to 127.0.0.1; add PgBouncer).
17. **Fix M3:** Use `dateutil.relativedelta` for accurate age calculation.
18. **Fix M8:** Add `pdf_hash` to `SalesAgreement` if missing.
19. **Add M7:** Implement CSP nonces for inline styles if possible.
20. **Add A1:** Create auto-scoping model manager to eliminate human error.

---

## 14. Conclusion

The Wellfond BMS codebase demonstrates **strong architectural vision** and **correct technology choices** for a Singapore AVS-compliant breeding management platform. The BFF pattern, native Celery tasks, deterministic compliance logic, and closure-table genetics engine are all well-conceived.

However, **execution gaps between planning and implementation** create material risks in three areas:

1. **Security:** Entity scoping is inconsistently applied. The BFF CORS preflight is spec-violating. Session cookies have conditional security.
2. **Compliance:** PDPA hard filtering exists as a function but is not wired into routers. GST ledger mutability violates audit immutability principles.
3. **Test Integrity:** `force_login` usage means the primary authentication and authorization paths are **not actually tested**.

**Phase completion claims (0-8 at 100%) should be revised.** Phases 1 (Auth/BFF), 5 (Sales), 6 (Compliance), and 7 (Customers) require remediation before they can be considered complete against their own success criteria.

**Estimated Remediation Effort:** 2-3 developer weeks for critical/high issues, plus 1 week for medium issues and regression testing.

---

*Report compiled through systematic static analysis, document cross-reference, and architectural pattern validation against the Wellfond BMS Master Execution Plan v1.1 and AGENTS.md.*
