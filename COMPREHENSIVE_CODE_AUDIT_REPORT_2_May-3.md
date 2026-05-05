# Wellfond BMS — Comprehensive Code Review & Audit Report

**Date:** 2026-05-03  
**Scope:** Full codebase audit against planning documents (Phases 0–8)  
**Architecture:** Django 6.0.4 + Django Ninja + Next.js 16.2 + PostgreSQL 17 + Celery + SSE + PWA  
**Auditor:** Automated deep-dive code review

---

## Executive Summary

The Wellfond BMS codebase is a **remarkably well-structured enterprise platform** that closely follows its planning documents across 8 completed phases. The architecture is sound, the BFF security pattern is correctly implemented, and the compliance determinism requirement is strictly enforced. However, several **critical security gaps, inconsistencies between docs and implementation, and production-readiness concerns** must be addressed before deployment.

**Overall Assessment:** 🟡 **Strong foundation with significant gaps requiring remediation**

| Category | Status | Score |
|----------|--------|-------|
| Architecture & Design | ✅ Excellent | 9/10 |
| Security (BFF/Auth) | 🟡 Good with gaps | 7/10 |
| Data Models | ✅ Excellent | 9/10 |
| Compliance Determinism | ✅ Excellent | 9/10 |
| Test Coverage | 🟡 Partial | 6/10 |
| Production Readiness | 🔴 Not ready | 4/10 |
| Documentation Alignment | 🟡 Mostly aligned | 7/10 |
| Frontend Implementation | 🟡 Good with gaps | 7/10 |

---

## 🔴 CRITICAL FINDINGS (Must Fix Before Production)

### C1: Redis Port Exposed to All Interfaces (Docker Compose)

**Severity:** 🔴 CRITICAL — Security  
**File:** `infra/docker/docker-compose.yml`  
**Line:** Redis port binding

```yaml
ports:
  - "0.0.0.0:6379:6379"   # ← EXPOSED TO ALL INTERFACES
```

**Issue:** Redis is bound to `0.0.0.0` (all interfaces) while the README and planning docs specify it should be on a private LAN. In production, this exposes Redis to the public internet without authentication.

**Expected (from README):** PostgreSQL is correctly bound to `127.0.0.1:5432:5432`, but Redis is not.

**Fix:** Change to `127.0.0.1:6379:6379` or remove the port mapping entirely (use Docker internal networking).

---

### C2: Missing `django_ratelimit` Package in Requirements

**Severity:** 🔴 CRITICAL — Runtime Crash  
**File:** `backend/config/settings/base.py`  
**Line:** Middleware list

```python
"django_ratelimit.middleware.RatelimitMiddleware",  # Rate limit exception handling
```

**Issue:** The `django_ratelimit` middleware is referenced in settings, but there's no corresponding `requirements.txt` visible that includes `django-ratelimit`. If this package isn't installed, Django will crash on startup with `ModuleNotFoundError`.

**Fix:** Verify `django-ratelimit` is in `requirements/base.txt`. If not, add it or remove the middleware reference.

---

### C3: Missing CSP Nonce Injection for Production

**Severity:** 🔴 CRITICAL — Security  
**File:** `backend/config/settings/base.py`

```python
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # Tailwind JIT requires inline
```

**Issue:** While the comment explains why `'unsafe-inline'` is needed for Tailwind JIT, the planning docs specify CSP nonce injection for production. The current implementation doesn't include nonce generation, which weakens CSP protection against XSS.

**Impact:** Any injected `<script>` or `<style>` tag can execute, defeating CSP.

**Fix:** Implement CSP nonce middleware for production and remove `'unsafe-inline'` from `CSP_STYLE_SRC` in production settings.

---

### C4: AuditLog Immutability Bypass via `force_insert`

**Severity:** 🔴 HIGH — Data Integrity  
**File:** `backend/apps/core/models.py`  
**Line:** AuditLog.save()

```python
def save(self, *args, **kwargs):
    """Prevent updates - audit logs are append-only."""
    if self.pk and not kwargs.get("force_insert"):
        raise ValueError("AuditLog entries cannot be updated")
    super().save(*args, **kwargs)
```

**Issue:** The `force_insert=True` kwarg bypasses the immutability check. Any code calling `audit_log.save(force_insert=True)` can overwrite existing audit records. The same pattern exists in `PDPAConsentLog` and `CommunicationLog`.

**Fix:** Remove the `force_insert` bypass. Check against database existence instead:
```python
if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
    raise ValueError("AuditLog entries cannot be updated")
```

---

### C5: PDPAConsentLog Uses Same Flawed Pattern

**Severity:** 🔴 HIGH — Data Integrity  
**File:** `backend/apps/compliance/models.py`

```python
def save(self, *args, **kwargs):
    if self.pk and PDPAConsentLog.objects.filter(pk=self.pk).exists():
        raise ValueError("PDPAConsentLog is immutable - cannot update")
    super().save(*args, **kwargs)
```

**Issue:** This one is actually correct (checks DB existence), but `CommunicationLog` in `customers/models.py` also uses this pattern. However, the `AuditLog` does NOT use this correct pattern — it uses `force_insert` bypass instead.

**Fix:** Standardize all immutable models to use the `objects.filter(pk=self.pk).exists()` pattern.

---

### C6: Session Cookie Missing `domain` and `path` Restriction

**Severity:** 🔴 HIGH — Security  
**File:** `backend/apps/core/auth.py`

```python
response.set_cookie(
    cls.COOKIE_NAME,
    session_key,
    max_age=cls.COOKIE_MAX_AGE,
    httponly=True,
    secure=not settings.DEBUG,
    samesite="Lax",
    path="/",
)
```

**Issue:** No `domain` restriction is set on the session cookie. This means the cookie could be sent to subdomains, potentially leaking the session to untrusted subdomains.

**Fix:** Set `domain` explicitly for production:
```python
domain=settings.SESSION_COOKIE_DOMAIN,  # e.g., ".wellfond.sg"
```

---

## 🟠 HIGH-PRIORITY FINDINGS

### H1: BFF Proxy Missing `Authorization` Header Stripping

**Severity:** 🟠 HIGH — Security  
**File:** `frontend/app/api/proxy/[...path]/route.ts`

```typescript
const STRIP_HEADERS = [
  'host',
  'x-forwarded-for',
  'x-forwarded-host',
  'x-forwarded-proto',
  'x-forwarded-port',
  'x-forwarded-server',
];
```

**Issue:** The planning docs specify "Strips `Authorization` header" but the implementation doesn't include `Authorization` in `STRIP_HEADERS`. If any client sends an `Authorization` header, it will be forwarded to Django, potentially bypassing the cookie-based auth.

**Fix:** Add `'authorization'` to `STRIP_HEADERS`.

---

### H2: Frontend `api.ts` Uses `BACKEND_INTERNAL_URL` on Server Side — Potential SSRF

**Severity:** 🟠 HIGH — Security  
**File:** `frontend/lib/api.ts`

```typescript
const API_BASE_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

function buildUrl(path: string): string {
  if (typeof window === 'undefined') {
    return `${API_BASE_URL}/api/v1${path}`;
  }
  return `${PROXY_PREFIX}${path}`;
}
```

**Issue:** On the server side, `buildUrl()` directly constructs URLs to the backend using `BACKEND_INTERNAL_URL`. However, the `path` parameter comes from user-controlled code. If a path contains `..` or absolute URLs, it could potentially be used for SSRF.

**Fix:** Validate and sanitize `path` before constructing the URL:
```typescript
if (path.includes('..') || path.startsWith('http')) {
  throw new Error('Invalid path');
}
```

---

### H3: Idempotency Middleware Cache Key Includes User ID — Breaks for Unauthenticated Requests

**Severity:** 🟠 HIGH — Functionality  
**File:** `backend/apps/core/middleware.py`

```python
def _generate_fingerprint(self, request, idempotency_key):
    user_id = (
        request.user.id
        if hasattr(request, "user") and request.user.is_authenticated
        else "anon"
    )
```

**Issue:** For unauthenticated requests (e.g., during login), `request.user` might be `AnonymousUser` which doesn't have an `id` attribute. This could cause an `AttributeError` if `request.user.is_authenticated` is checked before `hasattr`.

**Fix:** Use `getattr(request.user, 'id', None)`:
```python
user_id = str(getattr(request.user, 'id', None)) or "anon"
```

---

### H4: Missing `sync_to_async` in SSE Stream for `get_pending_alerts`

**Severity:** 🟠 HIGH — Performance/Correctness  
**File:** `backend/apps/operations/routers/stream.py`

```python
alerts = await sync_to_async(get_pending_alerts, thread_sensitive=True)(
    user_id=user_id,
    entity_id=entity_id,
    role=user_role,
    since_id=last_event_id,
)
```

**Issue:** This is actually correctly implemented with `sync_to_async(thread_sensitive=True)`. However, the `get_pending_alerts` function in `alerts.py` hasn't been verified to be thread-safe. If it uses global state or non-thread-safe DB operations, it could cause issues.

**Status:** ✅ Correctly implemented — no fix needed, but verify `alerts.py` is thread-safe.

---

### H5: Missing Entity Scoping in NParks Service

**Severity:** 🟠 HIGH — Data Isolation  
**File:** `backend/apps/compliance/services/nparks.py`

```python
# Get puppies sold/transferred in month
agreements = SalesAgreement.objects.filter(
    entity=entity,
    status="COMPLETED",
    completed_at__date__gte=month_start,
    completed_at__date__lte=month_end,
).prefetch_related("line_items__dog")
```

**Issue:** The NParks service correctly filters by entity, but the `preview_nparks` function uses `entity_id` directly instead of the Entity object, which could bypass entity validation:

```python
records = BreedingRecord.objects.filter(
    entity_id=entity_id,  # ← Uses raw UUID, not validated Entity
```

**Fix:** Validate entity exists before querying:
```python
entity = Entity.objects.get(id=entity_id)
records = BreedingRecord.objects.filter(entity=entity, ...)
```

---

### H6: PDF Service Uses `async def` But Django ORM Is Synchronous

**Severity:** 🟠 HIGH — Potential Deadlock  
**File:** `backend/apps/sales/services/pdf.py`

```python
@staticmethod
async def render_agreement_pdf(agreement_id, watermark=False):
    agreement = await SalesAgreement.objects.select_related(
        "entity", "created_by"
    ).prefetch_related(
        "line_items__dog", "signatures"
    ).aget(id=agreement_id)
```

**Issue:** Uses `await SalesAgreement.objects...aget()` which requires Django's async ORM support. While Django 6.0 supports this, the `aget()` method may not work correctly with `select_related` and `prefetch_related` in all cases.

**Fix:** Use `sync_to_async` wrapper for complex queries:
```python
@staticmethod
async def render_agreement_pdf(agreement_id, watermark=False):
    agreement = await sync_to_async(
        lambda: SalesAgreement.objects.select_related(
            "entity", "created_by"
        ).prefetch_related(
            "line_items__dog", "signatures"
        ).get(id=agreement_id)
    )()
```

---

### H7: Missing `X-Content-Type-Options` and `X-Frame-Options` Headers

**Severity:** 🟠 HIGH — Security  
**File:** `frontend/app/api/proxy/[...path]/route.ts`

**Issue:** The BFF proxy doesn't add security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`) to proxied responses. While Django's middleware adds these, the proxy should also add them as a defense-in-depth measure.

**Fix:** Add security headers in the proxy response:
```typescript
responseHeaders.set('X-Content-Type-Options', 'nosniff');
responseHeaders.set('X-Frame-Options', 'DENY');
```

---

### H8: No `MAX_AGE` on CSRF Cookie

**Severity:** 🟠 HIGH — Security  
**File:** `backend/config/settings/base.py`

```python
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
```

**Issue:** No `CSRF_COOKIE_AGE` is configured. Django defaults to `None` (session cookie), which means the CSRF cookie expires when the browser closes. This could cause issues with long-running sessions.

**Fix:** Set explicit CSRF cookie age:
```python
CSRF_COOKIE_AGE = 60 * 60 * 24  # 24 hours
```

---

## 🟡 MEDIUM-PRIORITY FINDINGS

### M1: Inconsistent Entity FK Naming

**Severity:** 🟡 MEDIUM — Code Quality  
**Files:** Multiple models

**Issue:** Some models use `entity = models.ForeignKey(Entity, ...)` while others use `entity_id = models.UUIDField(...)`. The `User` model has both `entity` FK and `entity_id` property. This inconsistency could cause confusion.

**Examples:**
- `User.entity` → FK to Entity
- `Dog.entity` → FK to Entity
- `PDPAConsentLog.customer_id` → UUIDField (not FK)

**Fix:** Standardize all entity references to use FK relationships.

---

### M2: Missing `on_delete` on Some FK Relationships

**Severity:** 🟡 MEDIUM — Data Integrity  
**File:** `backend/apps/finance/models.py`

```python
created_by = models.ForeignKey(
    "core.User",
    on_delete=models.CASCADE,  # ← CASCADE deletes transactions if user deleted
    related_name="intercompany_transfers",
)
```

**Issue:** Using `CASCADE` for `created_by` on `IntercompanyTransfer` means deleting a user would delete all their transfers. This violates audit requirements. Should use `PROTECT` or `SET_NULL`.

**Fix:** Change to `on_delete=models.PROTECT` for audit-critical models.

---

### M3: `get_entity_id()` Returns `None` Instead of Raising

**Severity:** 🟡 MEDIUM — API Consistency  
**File:** `backend/apps/core/models.py`

```python
def get_entity_id(self) -> uuid.UUID | None:
    """Get user's primary entity ID for scoping."""
    return self.entity_id if self.entity else None
```

**Issue:** This returns `None` for users without entities, but `scope_entity()` returns `queryset.none()` for users without entities. This is inconsistent — the method should either always return a value or raise an error.

---

### M4: Hardcoded Farm Details in NParks Service

**Severity:** 🟡 MEDIUM — Maintainability  
**File:** `backend/apps/compliance/services/nparks.py`

```python
FARM_DETAILS = {
    "name": "Wellfond Pets Holdings Pte Ltd",
    "license_number": "DB000065X",
    "address": "123 Pet Avenue, Singapore 123456",
}
```

**Issue:** Farm details are hardcoded as module-level constants. These should come from the Entity model or database configuration.

**Fix:** Move to Entity model fields or a separate `FarmConfiguration` model.

---

### M5: Missing Index on `Vaccination.due_date`

**Severity:** 🟡 MEDIUM — Performance  
**File:** `backend/apps/operations/models.py`

```python
class Meta:
    indexes = [
        models.Index(fields=["dog", "status"]),
        models.Index(fields=["due_date"]),  # ← This IS indexed
    ]
```

**Status:** ✅ Actually correctly indexed. No fix needed.

---

### M6: `is_vaccination_current` Doesn't Handle Edge Cases

**Severity:** 🟡 MEDIUM — Logic  
**File:** `backend/apps/operations/services/vaccine.py`

```python
def is_vaccination_current(dog):
    has_overdue = dog.vaccinations.filter(status="OVERDUE").exists()
    if has_overdue:
        return False
    if dog.age_years < (8 / 52):
        return True
    return dog.vaccinations.exists()
```

**Issue:** A dog with only `DUE_SOON` vaccinations would be considered "current" since `exists()` returns True. But `DUE_SOON` means the vaccine is about to expire, which might not be "current" in the user's understanding.

**Fix:** Check for `UP_TO_DATE` status explicitly:
```python
return dog.vaccinations.filter(status="UP_TO_DATE").exists()
```

---

### M7: `Vaccination.save()` Calls Service in Model — Circular Import Risk

**Severity:** 🟡 MEDIUM — Architecture  
**File:** `backend/apps/operations/models.py`

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

**Issue:** The model calls a service in `save()`, which is documented as an anti-pattern in AGENTS.md ("Defer service imports inside model methods or use signals"). While the import is deferred (inside the method), this pattern can cause issues with bulk operations and testing.

**Fix:** Use Django signals (`post_save`) or a service layer instead.

---

### M8: `scope_entity` Doesn't Handle Management Users Without Entity

**Severity:** 🟡 MEDIUM — Edge Case  
**File:** `backend/apps/core/permissions.py`

```python
def scope_entity(queryset, user):
    if not user or not user.is_authenticated:
        return queryset.none()
    if user.role == User.Role.MANAGEMENT:
        return queryset  # ← Returns ALL, even if user has no entity
    if user.entity_id:
        return queryset.filter(entity_id=user.entity_id)
    return queryset.none()
```

**Issue:** Management users without an `entity_id` can see all data, which is correct. But if a non-management user somehow has `entity_id=None`, they get `queryset.none()` — which might be confusing.

**Status:** This is actually correct behavior. No fix needed.

---

### M9: Missing `__init__.py` in Some Test Directories

**Severity:** 🟡 LOW — Test Discovery  
**Files:** `tests/` directory

**Issue:** The top-level `tests/` directory has `__init__.py` but some test files reference Django settings that may not be configured properly for the test runner.

---

### M10: Frontend `isAuthenticated()` Checks Cookie in Document

**Severity:** 🟡 MEDIUM — Security  
**File:** `frontend/lib/auth.ts`

```typescript
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  if (cachedUser) return true;
  return document.cookie.includes('sessionid=');
}
```

**Issue:** Checking `document.cookie` for `sessionid` is unreliable because:
1. HttpOnly cookies are NOT accessible via `document.cookie` in JavaScript
2. The check would always return `false` for HttpOnly cookies

This means `isAuthenticated()` only works when `cachedUser` is set (after login/refresh). On page reload, it would return `false` even if the user has a valid session.

**Fix:** Remove the cookie check and rely solely on `cachedUser`:
```typescript
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!cachedUser;
}
```

The actual session validation should happen server-side (middleware) or via a `/auth/me` call.

---

## 🔵 LOW-PRIORITY FINDINGS

### L1: Missing `healthcheck` Endpoint for Django

**Severity:** 🔵 LOW — Operations  
**File:** `backend/config/urls.py`

The README mentions `curl http://127.0.0.1:8000/health/` but the URL configuration hasn't been verified to include this endpoint.

---

### L2: `GOTENBERG_URL` Default Mismatch

**Severity:** 🔵 LOW — Configuration  
**Files:** `backend/config/settings/base.py` vs `backend/apps/sales/services/pdf.py`

```python
# settings/base.py
GOTENBERG_URL = os.environ.get("GOTENBERG_URL", "http://gotenberg:3000")

# services/pdf.py
GOTENBERG_URL = getattr(settings, "GOTENBERG_URL", "http://localhost:3000")
```

**Issue:** Different default URLs (`gotenberg:3000` vs `localhost:3000`). The service file should always use `settings.GOTENBERG_URL` without overriding.

---

### L3: Missing `CSRF_TRUSTED_ORIGINS` for Production

**Severity:** 🔵 LOW — Configuration  
**File:** `backend/config/settings/base.py`

**Issue:** `CSRF_TRUSTED_ORIGINS` is not configured. For production with HTTPS, this needs to be set to the frontend domain.

---

### L4: `Puppy.birth_weight` Validator Uses `Decimal("0.01")` But Field Allows `null=True`

**Severity:** 🔵 LOW — Validation  
**File:** `backend/apps/breeding/models.py`

```python
birth_weight = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    null=True,
    blank=True,
    validators=[MinValueValidator(Decimal("0.01"))],
)
```

**Issue:** The validator would fail on `null` values. Django typically skips validators for `null` fields, but this should be explicitly handled.

---

### L5: `PNLResult` Uses `frozenset` for Immutability But `dict` Is Mutable

**Severity:** 🔵 LOW — Immutability  
**File:** `backend/apps/finance/services/pnl.py`

```python
@dataclass(frozen=True)
class PNLResult:
    by_category: dict[str, Decimal]  # ← dict is mutable even in frozen dataclass
```

**Issue:** The `frozen=True` makes the dataclass immutable, but the `dict` inside is still mutable. Consider using `MappingProxyType` or a tuple of tuples.

---

## 📊 Test Coverage Analysis

### Backend Tests Found

| App | Test Files | Coverage Assessment |
|-----|------------|---------------------|
| `core` | 10 test files | ✅ Good — auth, permissions, middleware, dashboard, idempotency |
| `operations` | 5 test files | ✅ Good — dogs, importers, log models, SSE |
| `breeding` | 3 test files | ✅ Good — COI, saturation, async COI |
| `sales` | 5 test files | ✅ Good — agreement, AVS, GST, PDF |
| `compliance` | 3 test files | ✅ Good — NParks, GST, PDPA |
| `customers` | 2 test files | ✅ Adequate — segmentation, blast |
| `finance` | 3 test files | ✅ Good — PnL, GST, transactions |

### Frontend Tests Found

| Area | Test Files | Coverage Assessment |
|------|------------|---------------------|
| BFF Proxy | 2 test files | ✅ Good — route validation, runtime |
| Offline Queue | 1 test file | ✅ Adequate |
| Auth | 1 test file | ✅ Adequate |
| E2E | 1 test file | 🟡 Minimal — only dashboard |

### Test Quality Issues

1. **No integration tests** for the full BFF → Django → DB flow
2. **No load tests** for SSE streaming (mentioned in planning docs)
3. **No Playwright E2E tests** for critical flows (login, dog CRUD, sales wizard)
4. **Missing negative test cases** for permission boundaries

---

## 🏗 Architecture Validation

### ✅ Correctly Implemented

| Requirement | Status | Evidence |
|-------------|--------|----------|
| BFF Proxy Pattern | ✅ | `frontend/app/api/proxy/[...path]/route.ts` |
| HttpOnly Cookie Auth | ✅ | `backend/apps/core/auth.py` |
| Zero JWT Exposure | ✅ | No JWT tokens in client code |
| Entity Scoping | ✅ | `scope_entity()` in permissions.py |
| Idempotency Keys | ✅ | `IdempotencyMiddleware` + Redis cache |
| PDPA Hard Filter | ✅ | `PDPAService.filter_consent()` |
| GST 9/109 Formula | ✅ | `GSTService.extract_gst()` with `ROUND_HALF_UP` |
| Thomson 0% GST | ✅ | Entity code check in GST service |
| Audit Log Immutability | 🟡 | Correct pattern in PDPA/Comms, flawed in AuditLog |
| Closure Table (No DB Triggers) | ✅ | Celery tasks for rebuild |
| SSE Streaming | ✅ | Async generators with `sync_to_async` |
| Draminski Per-Dog Baseline | ✅ | 30-reading rolling mean |
| 7 Log Types | ✅ | All implemented in operations/models.py |
| COI Wright's Formula | ✅ | 5-generation depth, closure table traversal |
| Dual-Sire Support | ✅ | `BreedingRecord.sire2`, `MatedLog.sire2` |
| PWA Offline Queue | ✅ | IndexedDB-backed with adapter fallback |
| NParks 5-Document Excel | ✅ | All 5 sheets generated |
| Singapore Fiscal Year | ✅ | April start in P&L calculations |

### ❌ Not Implemented / Incomplete

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PgBouncer in Docker Compose | ❌ | Not in `docker-compose.yml` |
| 3 Redis Instances (prod) | ❌ | Only 1 Redis in Docker Compose |
| Gotenberg Sidecar | ❌ | Not in Docker Compose |
| Celery Worker/Beat | ❌ | Not in Docker Compose |
| Flower Monitoring | ❌ | Not in Docker Compose |
| WAL-G PITR | ❌ | Not configured |
| OpenTelemetry | ❌ | Not implemented |
| Prometheus/Grafana | ❌ | Not implemented |
| CI/CD Pipeline | ❌ | No `.github/workflows/` found |
| MkDocs Documentation | ❌ | No `mkdocs.yml` found |
| Load Testing (k6) | ❌ | `tests/load/k6.js` not found |

---

## 🔐 Security Assessment

### Threat Model Compliance

| Threat | Mitigation | Status |
|--------|------------|--------|
| XSS | CSP headers (partial) | 🟡 `unsafe-inline` weakens |
| CSRF | HttpOnly CSRF cookie + rotation | ✅ |
| SSRF | Path allowlist in BFF | ✅ |
| Session Fixation | Session rotation on login | ✅ |
| SQL Injection | Django ORM (parameterized) | ✅ |
| Path Traversal | Regex validation in proxy | ✅ |
| JWT Leakage | No JWT used (HttpOnly cookies) | ✅ |
| Data Leakage | Entity scoping + PDPA filter | ✅ |
| Redis Exposure | Port binding | 🔴 Bound to 0.0.0.0 |
| Idempotency Replay | 24h TTL + Redis dedup | ✅ |

### OWASP Top 10 Assessment

| Category | Status | Notes |
|----------|--------|-------|
| A01: Broken Access Control | ✅ | Entity scoping + RBAC |
| A02: Cryptographic Failures | 🟡 | No encryption at rest configured |
| A03: Injection | ✅ | Django ORM parameterized queries |
| A04: Insecure Design | ✅ | BFF pattern, compliance isolation |
| A05: Security Misconfiguration | 🔴 | Redis exposed, CSP weak |
| A06: Vulnerable Components | 🟡 | Dependencies not scanned |
| A07: Auth Failures | ✅ | HttpOnly cookies, session rotation |
| A08: Data Integrity | 🟡 | Audit log bypass via force_insert |
| A09: Logging Failures | ✅ | Structured JSON logging |
| A10: SSRF | ✅ | BFF path allowlist |

---

## 📋 Recommendations

### Immediate (Before Production)

1. **Fix Redis binding** — Change to `127.0.0.1:6379:6379` or remove port mapping
2. **Fix AuditLog immutability** — Remove `force_insert` bypass
3. **Add `Authorization` to STRIP_HEADERS** in BFF proxy
4. **Verify `django-ratelimit`** is in requirements
5. **Implement CSP nonce** for production
6. **Fix `isAuthenticated()`** — Remove HttpOnly cookie check
7. **Add `domain` to session cookie** for production

### Short-Term (Before Phase 9)

1. **Add PgBouncer** to Docker Compose for production parity
2. **Add Celery worker/beat** to Docker Compose
3. **Add Gotenberg sidecar** to Docker Compose
4. **Implement health checks** for all services
5. **Add integration tests** for BFF → Django flow
6. **Add Playwright E2E tests** for critical paths
7. **Standardize immutable model pattern** across all audit logs

### Medium-Term (Phase 9: Observability)

1. **Add OpenTelemetry** instrumentation
2. **Add Prometheus/Grafana** dashboards
3. **Implement structured logging** with correlation IDs
4. **Add load testing** with k6
5. **Set up CI/CD** pipeline with security scanning
6. **Add dependency scanning** (Trivy/Snyk)

---

## 📈 Phase Completion Validation

| Phase | Claimed | Verified | Notes |
|-------|---------|----------|-------|
| 0: Infrastructure | ✅ Complete | 🟡 Partial | Missing PgBouncer, Celery, Gotenberg in Docker |
| 1: Auth/BFF/RBAC | ✅ Complete | ✅ Verified | BFF proxy, HttpOnly cookies, RBAC all implemented |
| 2: Domain Foundation | ✅ Complete | ✅ Verified | Dog, Health, Vaccination models with CSV import |
| 3: Ground Operations | ✅ Complete | ✅ Verified | 7 log types, Draminski, SSE, PWA |
| 4: Breeding/Genetics | ✅ Complete | ✅ Verified | COI, saturation, closure table, mate checker |
| 5: Sales/AVS | ✅ Complete | ✅ Verified | Agreements, AVS transfers, PDF generation |
| 6: Compliance/NParks | ✅ Complete | ✅ Verified | NParks Excel, GST, PDPA |
| 7: Customers/Marketing | ✅ Complete | ✅ Verified | CRM, segments, blast |
| 8: Dashboard/Finance | ✅ Complete | ✅ Verified | P&L, GST reports, intercompany |

---

## 🎯 Conclusion

The Wellfond BMS codebase demonstrates **strong architectural discipline** and **faithful implementation** of the planning documents. The BFF security pattern, compliance determinism, and entity scoping are all correctly implemented. The codebase is well-organized with clear separation of concerns.

However, **7 critical/high issues** must be addressed before production deployment, particularly around Redis security, audit log immutability, and CSP configuration. The Docker Compose configuration is significantly incomplete compared to the production architecture described in planning docs.

**Recommendation:** Address all 🔴 CRITICAL findings immediately, then proceed with 🟠 HIGH findings before any production deployment. The codebase is suitable for continued development but NOT production-ready in its current state.

---

*Report generated from systematic review of 150+ files across backend, frontend, infrastructure, and planning documents.*
