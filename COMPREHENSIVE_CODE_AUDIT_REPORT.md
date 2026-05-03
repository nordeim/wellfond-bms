# Wellfond BMS — Comprehensive Code Review & Audit Report

**Date:** 2026-05-03  
**Scope:** Full codebase audit against planning documents (Phases 0–8)  
**Architecture:** Django 6.0.4 + Django Ninja + Next.js 16.2 + PostgreSQL 17 + Celery + SSE + PWA  
**Auditor:** Automated deep-dive code review with re-validation pass

---

## Executive Summary

The Wellfond BMS codebase is a **remarkably well-structured enterprise platform** that closely follows its planning documents across 8 completed phases. The architecture is sound, the BFF security pattern is correctly implemented, and the compliance determinism requirement is strictly enforced.

After a meticulous re-validation pass against the actual code, several initially reported findings were **corrected, downgraded, or removed** because they didn't hold up under scrutiny. The remaining findings represent genuine issues that should be addressed.

**Overall Assessment:** 🟡 **Strong foundation with targeted gaps requiring remediation**

| Category | Status | Score |
|----------|--------|-------|
| Architecture & Design | ✅ Excellent | 9/10 |
| Security (BFF/Auth) | ✅ Good | 8/10 |
| Data Models | ✅ Excellent | 9/10 |
| Compliance Determinism | ✅ Excellent | 9/10 |
| Test Coverage | 🟡 Partial | 6/10 |
| Production Readiness | 🟡 Incomplete infra | 5/10 |
| Documentation Alignment | 🟡 Mostly aligned | 7/10 |
| Frontend Implementation | ✅ Good | 8/10 |

---

## 🔴 CRITICAL FINDINGS (Must Fix Before Production)

### C1: Redis Port Exposed to All Interfaces (Docker Compose)

**Severity:** 🔴 CRITICAL — Security  
**File:** `infra/docker/docker-compose.yml` (line 68)  
**Validated:** ✅ Confirmed by direct code inspection

```yaml
ports:
  - "0.0.0.0:6379:6379"   # ← EXPOSED TO ALL INTERFACES
```

**Evidence:** PostgreSQL is correctly bound to `127.0.0.1:5432:5432` (line 45), but Redis uses `0.0.0.0`. The planning docs specify Redis should be on a private LAN. In production, this exposes Redis to the public internet without authentication.

**Root Cause:** The `.bak` file (hybrid dev compose) had the same issue. The current full-containerized compose inherited it.

**Fix:**
```yaml
ports:
  - "127.0.0.1:6379:6379"
```
Or remove the `ports` mapping entirely and rely on Docker internal networking (the `backend` service connects via `redis:6379` internally).

---

### C2: CSP `unsafe-inline` Carries Into Production for Style Sources

**Severity:** 🔴 CRITICAL — Security (XSS)  
**Files:** `backend/config/settings/base.py` (line 222), `backend/config/settings/production.py`  
**Validated:** ✅ Confirmed by direct code inspection

**Evidence:**
```python
# base.py (line 222)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # Tailwind JIT requires inline

# production.py — overrides CSP_SCRIPT_SRC but NOT CSP_STYLE_SRC
CSP_SCRIPT_SRC = ("'self'",)   # ✅ Hardened
CSP_REPORT_ONLY = False
# CSP_STYLE_SRC is NOT overridden → inherits "'unsafe-inline'" from base.py
```

**Root Cause:** `production.py` hardens `CSP_SCRIPT_SRC` but forgets to harden `CSP_STYLE_SRC`. The `'unsafe-inline'` directive for styles allows injected `<style>` tags to execute, which is an XSS vector.

**Fix in `production.py`:**
```python
CSP_STYLE_SRC = ("'self'",)  # Remove unsafe-inline; use nonce for Tailwind
```
Or implement CSP nonce middleware that generates per-request nonces.

---

### C3: `isAuthenticated()` Checks HttpOnly Cookie via `document.cookie` — Always Returns False After Page Reload

**Severity:** 🔴 HIGH — Functionality  
**File:** `frontend/lib/auth.ts` (line 92)  
**Validated:** ✅ Confirmed by direct code inspection

```typescript
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  if (cachedUser) return true;
  return document.cookie.includes('sessionid=');  // ← BUG: HttpOnly cookies are invisible to JS
}
```

**Evidence:** The session cookie is set with `httponly=True` (confirmed in `backend/apps/core/auth.py` line 148). JavaScript's `document.cookie` API cannot access HttpOnly cookies. Therefore, this fallback always returns `false`.

**Impact Analysis:**
- **Server-side auth:** ✅ Works correctly — `protected/layout.tsx` calls `getCurrentUser()` server-side with the HttpOnly cookie, and redirects to `/login` if not authenticated. Routes are protected.
- **Client-side auth state:** ❌ After page reload, `cachedUser` is `null` (in-memory only), and the cookie check returns `false`. The `useIsAuthenticated()` hook returns `false` even though the user has a valid session.
- **Practical impact:** Client-side conditional rendering based on auth state (e.g., showing/hiding elements) would be incorrect after page reload until `setSession()` is called again (e.g., after a `getCurrentUser()` or `refreshSession()` call).

**Root Cause:** The `cachedUser` in-memory variable is populated only after `login()`, `refreshSession()`, or `getCurrentUser()` calls. On page reload, it's `null`.

**Fix:** Remove the broken cookie check and rely on `cachedUser` only. Add a client-side initialization that calls `getCurrentUser()` on mount:
```typescript
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!cachedUser;
}
```
And in a top-level client component or layout effect:
```typescript
useEffect(() => {
  getCurrentUser().catch(() => {}); // Populates cachedUser via setSession
}, []);
```

---

## 🟠 HIGH-PRIORITY FINDINGS

### H1: `on_delete=models.CASCADE` on Audit-Critical Foreign Keys in Finance Models

**Severity:** 🟠 HIGH — Data Integrity  
**File:** `backend/apps/finance/models.py`  
**Validated:** ✅ Confirmed by direct code inspection

**Evidence:**
```python
# IntercompanyTransfer (line 62)
created_by = models.ForeignKey("core.User", on_delete=models.CASCADE, ...)

# GSTReport (line 126)
generated_by = models.ForeignKey("core.User", on_delete=models.CASCADE, ...)

# Transaction (line 81) — entity
entity = models.ForeignKey("core.Entity", on_delete=models.CASCADE, ...)
```

**Issue:** Using `CASCADE` for `created_by`/`generated_by` means deleting a user would cascade-delete all their financial records (transactions, GST reports, intercompany transfers). This violates audit requirements and the project's own rule of "immutable audit trails."

**Contrast:** The `compliance` and `sales` apps correctly use `on_delete=models.PROTECT` for similar relationships.

**Fix:** Change all audit-critical FKs in finance models to `on_delete=models.PROTECT`:
```python
created_by = models.ForeignKey("core.User", on_delete=models.PROTECT, ...)
generated_by = models.ForeignKey("core.User", on_delete=models.PROTECT, ...)
```
And for entity FKs, consider `PROTECT` or `RESTRICT` to prevent accidental entity deletion.

---

### H2: AuditLog Immutability Uses `force_insert` Bypass — Inconsistent With Other Immutable Models

**Severity:** 🟠 MEDIUM-HIGH — Data Integrity (downgraded from CRITICAL after re-validation)  
**File:** `backend/apps/core/models.py` (line 178)  
**Validated:** ✅ Confirmed, but practical impact is lower than initially assessed

**Evidence:**
```python
# AuditLog (core/models.py) — uses force_insert bypass
def save(self, *args, **kwargs):
    if self.pk and not kwargs.get("force_insert"):
        raise ValueError("AuditLog entries cannot be updated")
    super().save(*args, **kwargs)

# PDPAConsentLog (compliance/models.py) — uses DB existence check (correct)
def save(self, *args, **kwargs):
    if self.pk and PDPAConsentLog.objects.filter(pk=self.pk).exists():
        raise ValueError("PDPAConsentLog is immutable - cannot update")
    super().save(*args, **kwargs)

# CommunicationLog (customers/models.py) — same correct pattern
def save(self, *args, **kwargs):
    if self.pk and CommunicationLog.objects.filter(pk=self.pk).exists():
        raise ValueError("CommunicationLog is immutable - cannot update")
    super().save(*args, **kwargs)
```

**Re-validation Analysis:**
- Calling `save(force_insert=True)` on an existing AuditLog would bypass the check and attempt an `INSERT` with an existing pk.
- PostgreSQL would reject this with an `IntegrityError` (primary key violation), so existing records **cannot actually be overwritten**.
- However, the inconsistency is a code quality issue and the `force_insert` bypass is unnecessary and confusing.
- The `PDPAConsentLog` pattern is strictly better (checks DB existence).

**Fix:** Standardize all immutable models to use the DB existence check:
```python
def save(self, *args, **kwargs):
    if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
        raise ValueError("AuditLog entries cannot be updated")
    super().save(*args, **kwargs)
```

---

### H3: Missing PgBouncer, Celery, Gotenberg in Docker Compose

**Severity:** 🟠 HIGH — Production Readiness  
**File:** `infra/docker/docker-compose.yml`  
**Validated:** ✅ Confirmed — only postgres, redis, backend, frontend, nginx present

**Evidence:** The planning docs specify 11 services for production:
1. ✅ PostgreSQL 17
2. ✅ Redis (but only 1 instance, not 3)
3. ✅ Django backend
4. ✅ Next.js frontend
5. ❌ PgBouncer (not present)
6. ❌ Celery Worker (not present)
7. ❌ Celery Beat (not present)
8. ❌ Gotenberg (not present)
9. ❌ Flower (not present)
10. ❌ Redis Sessions instance (not present)
11. ❌ Redis Broker instance (not present)

The base settings reference `pgbouncer` as default host (`POSTGRES_HOST`, line 89), but the Docker Compose doesn't include it. The development settings override this to `localhost`, so it works in dev but would fail in production.

**Root Cause:** The `.bak` file (hybrid dev compose) was for "Containerized PG + Redis, Native Django/Next.js." The current compose was expanded to full containerization but only added the core services.

**Fix:** Add missing services to Docker Compose (or create a separate `docker-compose.prod.yml`):
```yaml
pgbouncer:
  image: edoburu/pgbouncer
  environment:
    DATABASE_URL: postgres://wellfond_user:${DB_PASSWORD}@postgres:5432/wellfond_db
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 200
    DEFAULT_POOL_SIZE: 20
  ports:
    - "127.0.0.1:5432:5432"
  depends_on:
    postgres:
      condition: service_healthy

celery-worker:
  build: ...
  command: celery -A config worker -l info -Q high,default,low,dlq
  depends_on:
    - redis
    - postgres

celery-beat:
  build: ...
  command: celery -A config beat -l info
  depends_on:
    - redis

gotenberg:
  image: gotenberg/gotenberg:8
  ports:
    - "127.0.0.1:3001:3000"
```

---

### H4: Development Idempotency Cache Shares Redis DB With Default Cache

**Severity:** 🟠 MEDIUM — Data Integrity  
**File:** `backend/config/settings/development.py` (line 35-37)  
**Validated:** ✅ Confirmed by direct code inspection

```python
CACHES["idempotency"]["LOCATION"] = os.environ.get(
    "REDIS_CACHE_URL", "redis://localhost:6379/2"
)
```

**Issue:** In development, the idempotency cache uses `REDIS_CACHE_URL` (same as default cache, DB 2), while production uses a separate `REDIS_IDEMPOTENCY_URL` (DB 0 on a separate instance). This means:
1. Dev and prod have different Redis DB numbering for idempotency
2. In dev, idempotency keys share space with general cache (potential key collision)
3. The `allkeys-lru` eviction policy could evict idempotency keys under memory pressure

**Fix:** Use a separate Redis DB for idempotency in development:
```python
CACHES["idempotency"]["LOCATION"] = os.environ.get(
    "REDIS_IDEMPOTENCY_URL", "redis://localhost:6379/3"
)
```

---

## 🟡 MEDIUM-PRIORITY FINDINGS

### M1: `Vaccination.save()` Calls Service Layer — Anti-Pattern

**Severity:** 🟡 MEDIUM — Architecture  
**File:** `backend/apps/operations/models.py`  
**Validated:** ✅ Confirmed

```python
def save(self, *args, **kwargs):
    try:
        from .services.vaccine import calc_vaccine_due
        self.due_date = calc_vaccine_due(self.dog, self.vaccine_name, self.date_given)
    except ImportError:
        logger.warning(...)
    self.status = self._calculate_status()
    super().save(*args, **kwargs)
```

**Issue:** The AGENTS.md explicitly warns against this: "Defer service imports inside model methods or use signals. Never import services at module level in `models.py`." While the import IS deferred (inside the method), calling business logic in `save()` has problems:
1. Bulk operations (`bulk_create`, `update`) bypass `save()` — due dates won't be calculated
2. Makes testing harder (need to mock service layer)
3. Violates separation of concerns

**Fix:** Use a Django signal or service layer:
```python
@receiver(pre_save, sender=Vaccination)
def calculate_vaccine_fields(sender, instance, **kwargs):
    from .services.vaccine import calc_vaccine_due
    instance.due_date = calc_vaccine_due(instance.dog, instance.vaccine_name, instance.date_given)
    instance.status = instance._calculate_status()
```

---

### M2: `is_vaccination_current` Returns True for Dogs With Only `DUE_SOON` Vaccines

**Severity:** 🟡 MEDIUM — Logic  
**File:** `backend/apps/operations/services/vaccine.py`  
**Validated:** ✅ Confirmed

```python
def is_vaccination_current(dog):
    has_overdue = dog.vaccinations.filter(status="OVERDUE").exists()
    if has_overdue:
        return False
    if dog.age_years < (8 / 52):
        return True
    return dog.vaccinations.exists()  # ← Returns True even if all are DUE_SOON
```

**Issue:** A dog with only `DUE_SOON` vaccinations would be considered "current" since `exists()` returns `True`. But `DUE_SOON` means the vaccine expires within 30 days — the dog's vaccination status is deteriorating.

**Fix:**
```python
return dog.vaccinations.filter(status="UP_TO_DATE").exists()
```

---

### M3: Hardcoded Farm Details in NParks Service

**Severity:** 🟡 MEDIUM — Maintainability  
**File:** `backend/apps/compliance/services/nparks.py` (line 27-31)  
**Validated:** ✅ Confirmed

```python
FARM_DETAILS = {
    "name": "Wellfond Pets Holdings Pte Ltd",
    "license_number": "DB000065X",
    "address": "123 Pet Avenue, Singapore 123456",
}
```

**Issue:** Farm details are module-level constants. If the entity has different license numbers or addresses, these would be wrong. Should come from the Entity model.

**Fix:** Read from Entity model:
```python
def _get_farm_details(entity: Entity) -> dict:
    return {
        "name": entity.name,
        "license_number": entity.avs_license_number,
        "address": entity.address,
    }
```

---

### M4: `GOTENBERG_URL` Default Mismatch Between Settings and Service

**Severity:** 🟡 LOW-MEDIUM — Configuration  
**Files:** `backend/config/settings/base.py` vs `backend/apps/sales/services/pdf.py`  
**Validated:** ✅ Confirmed

```python
# settings/base.py (line 217)
GOTENBERG_URL = os.environ.get("GOTENBERG_URL", "http://gotenberg:3000")

# services/pdf.py (line 18)
GOTENBERG_URL = getattr(settings, "GOTENBERG_URL", "http://localhost:3000")
```

**Issue:** Different default URLs. The service file should always use `settings.GOTENBERG_URL` without its own fallback.

**Fix in `pdf.py`:**
```python
GOTENBERG_URL = settings.GOTENBERG_URL  # No fallback — always use settings
```

---

### M5: `PNLResult` Dataclass Has Mutable `dict` Field Despite `frozen=True`

**Severity:** 🟡 LOW — Immutability  
**File:** `backend/apps/finance/services/pnl.py`  
**Validated:** ✅ Confirmed

```python
@dataclass(frozen=True)
class PNLResult:
    by_category: dict[str, Decimal]  # ← dict is mutable even in frozen dataclass
```

**Issue:** `frozen=True` prevents reassignment of fields but doesn't prevent mutation of mutable field values. Someone could do `result.by_category["key"] = value`.

**Fix:** Use `types.MappingProxyType` or document that the dict should not be mutated.

---

## 🔵 LOW-PRIORITY / INFORMATIONAL FINDINGS

### L1: `Authorization` Header Not Stripped in BFF Proxy

**Severity:** 🔵 LOW — Defense in Depth  
**File:** `frontend/app/api/proxy/[...path]/route.ts`  
**Validated:** ✅ Confirmed, but no practical impact

**Re-validation:** Grepped the entire backend for `HTTP_AUTHORIZATION`, `Bearer`, `JWT` — **zero matches**. Django's auth is purely cookie-based. The `Authorization` header is never read by any backend code. Not stripping it has no security impact.

**Optional fix:** Add `'authorization'` to `STRIP_HEADERS` for defense-in-depth.

---

### L2: BFF Proxy `buildUrl` in `api.ts` — SSRF Concern

**Severity:** 🔵 LOW — No Practical Attack Vector  
**File:** `frontend/lib/api.ts`  
**Validated:** ✅ Confirmed, but `path` is always hardcoded in application code

**Re-validation:** The `path` parameter in `buildUrl(path)` always comes from hardcoded strings in the codebase (`/auth/login`, `/dogs/`, `/breeding/mate-check`, etc.), never from user input. There is no SSRF vector.

---

### L3: Session Cookie Missing `domain` Attribute

**Severity:** 🔵 INFORMATIONAL — Actually Safer Than Explicit Domain  
**File:** `backend/apps/core/auth.py`  
**Validated:** ✅ Confirmed, but this is correct behavior

**Re-validation:** When no `domain` is set on `set_cookie()`, Django defaults to the current host. Cookies without an explicit `domain` attribute are NOT sent to subdomains — this is actually **more secure** than setting `domain=".wellfond.sg"` which would send the cookie to all subdomains.

---

### L4: Missing `CSRF_TRUSTED_ORIGINS` for Production

**Severity:** 🔵 LOW — Configuration  
**File:** `backend/config/settings/production.py`

**Issue:** Not configured. Needed for HTTPS CSRF validation with Django 4+.

**Fix:**
```python
CSRF_TRUSTED_ORIGINS = ["https://wellfond.sg", "https://www.wellfond.sg"]
```

---

### L5: Demo Credentials Hardcoded in Login Page

**Severity:** 🔵 LOW — Development Artifact  
**File:** `frontend/app/(auth)/login/page.tsx` (line 131-137)

```tsx
<div className="mt-6 rounded-lg bg-[#E8F4FF] p-4 text-center">
  <p className="text-xs text-[#4A7A94]">
    <strong>Demo Credentials:</strong>
  </p>
  <p className="mt-1 text-xs text-[#4A7A94]">
    Email: admin@wellfond.sg
  </p>
  <p className="text-xs text-[#4A7A94]">Password: admin123</p>
</div>
```

**Issue:** Demo credentials visible in the UI. Should be removed or gated behind `DEBUG` mode.

---

### L6: `POSTGRES_HOST_AUTH_METHOD: trust` in Docker Compose

**Severity:** 🔵 LOW — Development Only  
**File:** `infra/docker/docker-compose.yml` (line 33)

**Issue:** `trust` mode allows any connection without authentication. This is acceptable for local development but should not be in any production configuration.

---

## ❌ FINDINGS REMOVED AFTER RE-VALIDATION

The following findings from the initial report were found to be **incorrect or overstated** after careful re-validation against the actual code:

### ~~C2: Missing `django-ratelimit` Package~~ → ❌ REMOVED

**Reason:** `django-ratelimit==4.1.0` IS present in `backend/requirements/base.txt` (listed twice, under "Django Core" and "Security"). The middleware reference is valid.

### ~~C4: AuditLog `force_insert` Bypass~~ → 🟡 DOWNGRADED to H2

**Reason:** While the `force_insert=True` bypass is real, PostgreSQL would reject an INSERT with an existing primary key (IntegrityError). Existing audit records **cannot actually be overwritten**. The issue is now correctly characterized as an inconsistency with other immutable models, not a critical data integrity breach.

### ~~C6: Session Cookie Missing `domain`~~ → ❌ REMOVED

**Reason:** Not setting `domain` is actually the **safer default**. Cookies without explicit `domain` are not sent to subdomains. Setting `domain=".wellfond.sg"` would be less secure.

### ~~H1: `Authorization` Header Not Stripped~~ → 🔵 DOWNGRADED to L1

**Reason:** The backend **never reads** the `Authorization` header. Auth is purely cookie-based. No code in the entire backend references `HTTP_AUTHORIZATION`, `Bearer`, or `JWT`. Not stripping the header has zero practical security impact.

### ~~H2: SSRF in `api.ts` `buildUrl`~~ → 🔵 DOWNGRADED to L2

**Reason:** The `path` parameter is always hardcoded in application code (e.g., `/auth/login`, `/dogs/`). It's never derived from user input. There is no SSRF attack vector.

### ~~H3: IdempotencyMiddleware Fingerprint for Unauthenticated~~ → ❌ REMOVED

**Reason:** The code correctly uses `hasattr(request, "user") and request.user.is_authenticated`. Django's `AuthenticationMiddleware` (which runs first, confirmed at line 50 of `base.py`) always sets `request.user` to either a `User` or `AnonymousUser`. The `AnonymousUser` has `is_authenticated=False`, so the code safely falls back to `"anon"`. No `AttributeError` is possible.

### ~~H7: Missing Security Headers in BFF Proxy~~ → ❌ REMOVED

**Reason:** Django's `SecurityMiddleware` (which runs first in the middleware stack) sets `X-Content-Type-Options`, `X-Frame-Options`, and HSTS headers on all responses. The BFF proxy forwards these headers. Adding them redundantly in the proxy is unnecessary.

---

## 📊 Test Coverage Analysis

### Backend Tests (31 test files found)

| App | Test Files | Key Tests |
|-----|------------|-----------|
| `core` | 10 | Auth, permissions, middleware, dashboard, idempotency, rate limit |
| `operations` | 5 | Dogs, importers, log models, SSE async |
| `breeding` | 3 | COI, saturation, async COI |
| `sales` | 5 | Agreement, AVS, GST, PDF |
| `compliance` | 3 | NParks, GST, PDPA |
| `customers` | 2 | Segmentation, blast |
| `finance` | 3 | PnL, GST, transactions |
| `tests/` (root) | 5 | Draminski, logs, auth refresh, user endpoint, discovery |

### Frontend Tests (6 test files found)

| Area | Test Files |
|------|------------|
| BFF Proxy | 2 (route validation, runtime) |
| Offline Queue | 2 (adapter tests) |
| Auth | 1 (useAuth hook) |
| E2E | 1 (dashboard spec) |
| Config | 1 (next-config security) |

### Test Quality Gaps

1. **No integration tests** for full BFF → Django → DB flow
2. **No load tests** for SSE streaming (planning docs mention k6)
3. **Minimal Playwright E2E** — only dashboard spec found
4. **No negative test cases** for cross-entity data access attempts

---

## 🏗 Architecture Validation Matrix

### ✅ Correctly Implemented (Verified)

| Requirement | Implementation | Evidence |
|-------------|----------------|----------|
| BFF Proxy Pattern | `frontend/app/api/proxy/[...path]/route.ts` | Path allowlist, header stripping, cookie forwarding |
| HttpOnly Cookie Auth | `backend/apps/core/auth.py` | `httponly=True`, `samesite="Lax"`, Redis sessions |
| Zero JWT Exposure | No JWT code in frontend | No `localStorage`, no `Bearer` tokens |
| Entity Scoping | `scope_entity()` in permissions.py | MANAGEMENT sees all, others scoped to entity_id |
| Idempotency Keys | `IdempotencyMiddleware` | UUIDv4 keys, Redis cache (24h TTL), atomic lock |
| PDPA Hard Filter | `PDPAService.filter_consent()` | `WHERE pdpa_consent=True` at queryset level |
| GST 9/109 Formula | `GSTService.extract_gst()` | `price * 9 / 109`, `ROUND_HALF_UP` |
| Thomson 0% GST | Entity code check | `entity.code.upper() == "THOMSON"` → `Decimal("0.00")` |
| Audit Log Immutability | `save()`/`delete()` overrides | Append-only enforcement (inconsistent pattern, but functional) |
| Closure Table (No Triggers) | Celery tasks | `rebuild_closure_table()`, `rebuild_closure_incremental()` |
| SSE Streaming | Async generators | `sync_to_async(thread_sensitive=True)`, heartbeat, dedup |
| Draminski Per-Dog Baseline | 30-reading rolling mean | Default 250 for new dogs, UPPERCASE zones |
| 7 Log Types | All in operations/models.py | InHeat, Mated, Whelped, HealthObs, Weight, NursingFlag, NotReady |
| COI Wright's Formula | `calc_coi()` with closure table | 5-generation depth, Redis cache, threshold verdicts |
| Dual-Sire Support | `BreedingRecord.sire2`, `MatedLog.sire2` | Nullable second sire, confirmed_sire enum |
| PWA Offline Queue | IndexedDB with adapter fallback | IndexedDB → localStorage → in-memory |
| NParks 5-Document Excel | `NParksService` | Mating, puppy movement, vet, puppies bred, dog movement |
| Singapore Fiscal Year | `SG_FISCAL_START_MONTH = 4` | YTD from April in `calc_ytd()` |
| Middleware Order | Django auth before custom | Line 50 vs 51 in `base.py` |

### ❌ Not Implemented / Incomplete

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PgBouncer in Docker Compose | ❌ | Not in `docker-compose.yml`; settings reference it as default host |
| 3 Redis Instances (prod) | ❌ | Only 1 Redis in Docker Compose |
| Gotenberg Sidecar | ❌ | Not in Docker Compose; `pdf.py` has mock fallback |
| Celery Worker/Beat in Docker | ❌ | Not in Docker Compose |
| Flower Monitoring | ❌ | Not in Docker Compose |
| WAL-G PITR | ❌ | Not configured |
| OpenTelemetry | 🟡 | Packages in requirements, but no instrumentation code found |
| CI/CD Pipeline | ❌ | No `.github/workflows/` found |
| MkDocs Documentation | ❌ | Package in dev requirements, no `mkdocs.yml` found |
| Load Testing (k6) | ❌ | `tests/load/k6.js` not found |

---

## 🔐 Security Assessment

### OWASP Top 10 (Re-validated)

| Category | Status | Notes |
|----------|--------|-------|
| A01: Broken Access Control | ✅ | Entity scoping + RBAC + PDPA filter |
| A02: Cryptographic Failures | 🟡 | No encryption at rest; SHA-256 for PDF hash |
| A03: Injection | ✅ | Django ORM parameterized queries |
| A04: Insecure Design | ✅ | BFF pattern, compliance isolation, AI sandbox |
| A05: Security Misconfiguration | 🔴 | Redis exposed, CSP weak in prod |
| A06: Vulnerable Dependencies | 🟡 | `safety` and `bandit` in dev deps, not in CI |
| A07: Auth Failures | ✅ | HttpOnly cookies, session rotation, CSRF |
| A08: Data Integrity | 🟡 | Immutable models inconsistent (H2) |
| A09: Logging & Monitoring | ✅ | Structured JSON logging configured |
| A10: SSRF | ✅ | BFF path allowlist regex, no user-controlled URLs |

---

## 📋 Prioritized Remediation Plan

### P0 — Fix Before Any Production Deployment

| # | Finding | Fix Effort | Impact |
|---|---------|------------|--------|
| C1 | Redis port binding | 1 line change | Prevents public Redis exposure |
| C2 | CSP `unsafe-inline` in prod | 1 line + nonce middleware | Prevents XSS via style injection |
| C3 | `isAuthenticated()` broken | ~10 lines | Fixes client-side auth state |
| H1 | Finance `on_delete=CASCADE` | 3 line changes | Prevents audit data loss |

### P1 — Fix Before Phase 9 (Observability)

| # | Finding | Fix Effort | Impact |
|---|---------|------------|--------|
| H2 | AuditLog immutability pattern | 3 lines | Consistency with other immutable models |
| H3 | Missing Docker services | Docker Compose additions | Production parity |
| H4 | Dev idempotency cache DB | 1 line | Prevents dev/prod drift |
| M1 | Vaccination.save() anti-pattern | ~20 lines (signal) | Bulk operation correctness |
| M2 | is_vaccination_current logic | 1 line | Accurate vaccination status |
| M3 | Hardcoded farm details | ~15 lines | Entity-specific NParks reports |

### P2 — Nice to Have

| # | Finding | Fix Effort | Impact |
|---|---------|------------|--------|
| M4 | GOTENBERG_URL mismatch | 1 line | Config consistency |
| L1 | Authorization header strip | 1 line | Defense in depth |
| L4 | CSRF_TRUSTED_ORIGINS | 1 line | Production HTTPS |
| L5 | Demo credentials in UI | Conditional render | Production hygiene |
| L6 | POSTGRES_HOST_AUTH_METHOD | Docker env | Production hygiene |

---

## 🎯 Conclusion

After meticulous re-validation against the actual codebase, the Wellfond BMS demonstrates **strong architectural discipline** with **faithful implementation** of planning documents. The initial audit contained several findings that didn't survive scrutiny — they were either incorrect (C2, H3), overstated (C4, H1), or had mitigating factors (H2, H7).

The **4 genuine critical/high findings** are:
1. **Redis exposed** in Docker Compose (C1)
2. **CSP `unsafe-inline`** in production (C2)
3. **`isAuthenticated()` broken** after page reload (C3)
4. **`on_delete=CASCADE`** on finance audit FKs (H1)

These are all **low-effort fixes** (1-3 lines each) with **high security/integrity impact**.

The codebase is suitable for continued development and is impressively complete for 8 phases of work. With the P0 fixes applied, it would be ready for staging deployment.

---

*Report generated from systematic review of 150+ files. Initial findings re-validated through direct code inspection, grep analysis, and architectural tracing. 7 findings corrected or removed in the re-validation pass.*
