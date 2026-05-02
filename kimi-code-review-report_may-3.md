# Wellfond BMS - Comprehensive Code Review & Audit Report

**Project:** Wellfond BMS (Breeding Management System)  
**Date:** 2026-05-03  
**Auditor:** AI Code Review Agent  
**Scope:** Full-stack codebase audit against planning documents  
**Repository:** `https://github.com/nordeim/wellfond-bms.git`

---

## Executive Summary

This report presents a comprehensive audit of the Wellfond BMS codebase, an enterprise-grade dog breeding management system for Singapore AVS-licensed operations. The audit meticulously reviewed the codebase against 9 phases of planning documents and identified **critical issues, significant gaps, and architectural risks** that require immediate attention before production deployment.

**Overall Assessment Grade: C+ (Significant Issues Found)**

| Category | Grade | Summary |
|----------|-------|---------|
| Architecture Design | B | Good separation of concerns, BFF pattern well-conceived |
| Backend Implementation | C+ | Core models solid, but services incomplete/stubbed |
| Frontend Implementation | C | BFF proxy works, but auth state management fragile |
| Security | C | HttpOnly cookies implemented, but multiple exposure risks |
| Compliance (PDPA/GST/AVS) | B- | GST calculation correct, PDPA filtering present, AVS incomplete |
| Test Quality | D+ | Many tests reference non-existent APIs/methods |
| Infrastructure | D | Docker configs missing, no production deployment artifacts |
| Code-Plan Alignment | C | Phases 0-3 claimed complete but significant gaps exist |

---

## 1. Critical Issues (P0 - Must Fix Before Production)

### CRIT-001: Tests Reference Non-Existent Methods (Broken Test Suite)
**File:** `backend/apps/core/tests/test_auth.py`  
**Severity:** CRITICAL  
**Impact:** Test suite is fundamentally broken; CI/CD will fail; TDD claims are invalidated.

The test file references multiple methods that **do not exist** in the actual implementation:

| Test Reference | Actual Implementation | Status |
|----------------|----------------------|--------|
| `SessionManager.update_session_activity()` | **MISSING** | Method does not exist |
| `SessionManager.is_session_valid()` | **MISSING** | Method does not exist |
| `SessionManager.get_session_user()` | **MISSING** | Method does not exist |
| `AuthenticationService.authenticate(request, response, username, password)` | `AuthenticationService.login(request, email, password)` | Signature mismatch |
| `AuthenticationService.logout(response, session_key)` | `AuthenticationService.logout(request)` | Signature mismatch |
| `AuthenticationService.refresh(request, response, session_key)` | `AuthenticationService.refresh(request)` | Signature mismatch |

**Recommendation:** Either implement the missing methods to match test expectations, or rewrite tests to match the actual implementation. The tests appear to have been written for a different API design than what was ultimately implemented.

---

### CRIT-002: Missing Docker & Infrastructure Configuration
**Files:** `docker-compose.yml`, `docker-compose.dev.yml`, `infra/`  
**Severity:** CRITICAL  
**Impact:** Cannot deploy; infrastructure planning documents are unfulfilled.

The `README.md` and planning documents explicitly describe:
- Production `docker-compose.yml` with Django, PgBouncer, PostgreSQL 17, Redis×3, Gotenberg, Celery Worker, Celery Beat
- Development `docker-compose.dev.yml`
- `infra/` directory with Kubernetes manifests, Terraform configs, CloudFormation templates

**Actual State:** None of these files exist in the repository.

**Recommendation:** Create the missing Docker Compose configurations and infrastructure manifests, or update README to reflect actual project state.

---

### CRIT-003: BFF Proxy Falls Back to Insecure Localhost URL
**Files:** `frontend/app/api/proxy/[...path]/route.ts:18`, `frontend/lib/api.ts:18`  
**Severity:** CRITICAL  
**Impact:** SSRF risk, internal URL exposure, potential backend bypass in production.

```typescript
// frontend/app/api/proxy/[...path]/route.ts
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

// frontend/lib/api.ts
const API_BASE_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
```

**Issues:**
1. If `BACKEND_INTERNAL_URL` is unset in production, the proxy falls back to `localhost:8000`, which could leak to the client or cause request failures.
2. The fallback exposes the internal port number in source code.
3. There is **no validation** that `BACKEND_INTERNAL_URL` is actually set before starting the server.

**Recommendation:** Remove the fallback entirely. Throw a fatal error at startup if `BACKEND_INTERNAL_URL` is not defined. Document the required environment variable in `.env.example`.

---

### CRIT-004: CORS Handler Returns Trusted Origin for Untrusted Requests
**File:** `frontend/app/api/proxy/[...path]/route.ts:223`  
**Severity:** HIGH  
**Impact:** Potential CORS bypass, information leakage.

```typescript
function getCorsHeaders(request: NextRequest): Record<string, string> {
  const origin = request.headers.get('origin') || '';
  const isAllowed =
    ALLOWED_ORIGINS.includes(origin) ||
    (process.env.NODE_ENV === 'development' && origin.startsWith('http://localhost'));
  return {
    'Access-Control-Allow-Origin': isAllowed ? origin : ALLOWED_ORIGINS[0], // <-- ISSUE
    // ...
  };
}
```

For disallowed origins, the code returns `ALLOWED_ORIGINS[0]` (`https://wellfond.sg`) instead of rejecting the origin. This allows any website to make cross-origin requests that appear to come from `wellfond.sg`.

**Recommendation:** Return `''` or omit the header for disallowed origins. Do not reflect any origin for non-matching requests.

---

## 2. High Severity Issues (P1)

### HIGH-001: Development Settings Default in ASGI Entry Point
**File:** `backend/config/asgi.py:7`, `backend/config/wsgi.py`  
**Severity:** HIGH  
**Impact:** Accidental production exposure of debug settings.

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
```

If `DJANGO_SETTINGS_MODULE` is not explicitly set in production, Django will load development settings with `DEBUG=True`, `CORS_ALLOW_ALL_ORIGINS=True`, and the debug toolbar enabled.

**Recommendation:** Default to `config.settings.production` in all entry points. Force explicit override for development.

---

### HIGH-002: Celery Tasks Reference Non-Existent Code
**Files:** `backend/apps/operations/tasks.py`, `backend/apps/sales/tasks.py`  
**Severity:** HIGH  
**Impact:** Runtime crashes when tasks execute.

| Task | Broken Reference |
|------|----------------|
| `archive_old_logs` | `.update(is_active=False)` - Log models have no `is_active` field |
| `cleanup_old_idempotency_keys` | `from django_redis import get_redis_connection` - `django_redis` not in `INSTALLED_APPS` |
| `sync_offline_queue` | `create_in_heat_log()`, `create_mated_log()` - Services don't exist |
| `send_agreement_pdf` | `asyncio.run(PDFService.render_agreement_pdf(...))` - PDFService may block event loop |
| `process_draminski_reading` | `interpret_for_api()` - Not verified to exist |

**Recommendation:** Implement missing service methods or remove broken tasks. Do not deploy Celery workers with broken task references.

---

### HIGH-003: Missing Content Security Policy Middleware
**File:** `backend/config/settings/base.py`  
**Severity:** HIGH  
**Impact:** CSP headers defined but never sent; XSS risk.

The settings define `CSP_*` variables but `django-csp` is **not** in `INSTALLED_APPS` and no CSP middleware is configured. The headers will never be sent to the browser.

**Recommendation:** Add `django-csp` to requirements and `INSTALLED_APPS`, or add the middleware manually.

---

### HIGH-004: Frontend Route Guard Allows Unmatched Routes by Default
**File:** `frontend/lib/auth.ts:211`  
**Severity:** MEDIUM-HIGH  
**Impact:** Potential unauthorized access to undefined routes.

```typescript
export function canAccessRoute(path: string): boolean {
  // ...
  // Allow by default for unmatched routes
  return true;  // <-- ISSUE
}
```

Any route not explicitly defined in `ROUTE_ACCESS` is allowed. This violates the principle of least privilege.

**Recommendation:** Fail closed: `return false` for unmatched routes. Explicitly whitelist all valid routes.

---

### HIGH-005: Duplicate Authentication Middleware with Race Condition Risk
**File:** `backend/config/settings/base.py:44-57`  
**Severity:** MEDIUM-HIGH  
**Impact:** Confusing auth flow, potential race conditions.

```python
MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django auth
    "apps.core.middleware.AuthenticationMiddleware",          # Custom Redis auth
    # ...
]
```

Django's auth middleware sets `request.user` from the session backend. The custom middleware then **overwrites** it by reading from Redis. If they disagree (e.g., session expired in one but not the other), the user could be authenticated with stale data.

**Recommendation:** Remove Django's `AuthenticationMiddleware` when using the custom Redis-based middleware. They serve the same purpose.

---

## 3. Medium Severity Issues (P2)

### MED-001: Idempotency Middleware Body Consumption Risk
**File:** `backend/apps/core/middleware.py:131`  
**Severity:** MEDIUM  
**Impact:** Idempotency fingerprint may fail for multipart/form-data or file uploads.

```python
body = request.body.decode() if request.body else ""
```

The middleware reads `request.body` which is a bytes buffer. For streaming uploads or multipart requests, this may cause issues. The fingerprint also doesn't include query parameters which could differentiate requests.

**Recommendation:** Handle streaming bodies gracefully. Consider including query params in fingerprint.

---

### MED-002: Vaccination Due Date Calculation Ignores Previous Doses
**File:** `backend/apps/operations/models.py:293-306`  
**Severity:** MEDIUM  
**Impact:** Puppy vaccine schedules may be incorrect.

The `Vaccination.save()` method calls `calc_vaccine_due()` but does **not** pass `previous_doses`, which is a required parameter for accurate puppy series scheduling. The function defaults to `previous_doses=0`, causing all puppy vaccines to schedule as if it's the first dose.

**Recommendation:** Pass the actual previous dose count when calculating due dates.

---

### MED-003: Closure Table Rebuild SQL Has Logic Error
**File:** `backend/apps/breeding/tasks.py:51-84`  
**Severity:** MEDIUM  
**Impact:** Incomplete closure table; COI calculations may be wrong.

The recursive CTE uses `COALESCE(parent.dam_id, parent.sire_id)` which will:
1. Return `dam_id` if it exists
2. Return `sire_id` only if `dam_id` is NULL

This means **only one parent path is traversed per generation**, not both. The closure table will miss ancestor paths through the sire if the dam exists.

**Recommendation:** The CTE should generate separate rows for dam and sire paths, not coalesce them.

---

### MED-004: `DogClosure` Unique Constraint Uses Model Objects Not IDs
**File:** `backend/apps/breeding/models.py:363`  
**Severity:** MEDIUM  
**Impact:** Potential database constraint errors.

```python
unique_together = ["ancestor", "descendant"]
```

Django's `unique_together` with ForeignKey fields may not behave as expected in all database backends. Should use explicit `_id` suffixes for clarity: `unique_together = ["ancestor_id", "descendant_id"]`.

---

### MED-005: Sales Agreement GST Split Across Line Items Is Naive
**File:** `backend/apps/sales/services/agreement.py:255-260`  
**Severity:** MEDIUM  
**Impact:** Line-item GST may not sum to agreement GST due to rounding.

```python
price=total_amount / len(dogs),  # Split equally for now
gst_component=gst_component / len(dogs),
```

Dividing GST equally across line items can cause rounding discrepancies where the sum of line GST ≠ agreement GST. IRAS requires consistency.

**Recommendation:** Calculate per-line GST individually with `ROUND_HALF_UP`, or store only total GST at agreement level.

---

### MED-006: `nparks.py` Missing Sire/Dam Microchips in Puppy Movement Sheet
**File:** `backend/apps/compliance/services/nparks.py:246-273`  
**Severity:** MEDIUM  
**Impact:** Incomplete NParks compliance data.

The puppy movement sheet includes columns for "Sire Microchip" and "Dam Microchip" (columns 7 and 8) but they are **never populated** in the code:

```python
ws.cell(row=current_row, column=9, value=agreement.buyer_name)  # Skips cols 7-8
```

**Recommendation:** Populate sire/dam microchip columns from the puppy's litter/breeding record.

---

### MED-007: `get_vaccine_interval()` Partial Match Is Dangerous
**File:** `backend/apps/operations/services/vaccine.py:53-65`  
**Severity:** MEDIUM  
**Impact:** Incorrect vaccine intervals for similarly named vaccines.

```python
for key, interval in VACCINE_INTERVALS.items():
    if key in name_upper:
        return interval
```

A vaccine named "DHPP_BOOSTER_EXTRA" would match "DHPP" (21 days) instead of "DHPP_BOOSTER" (365 days) because of the order-dependant partial matching.

**Recommendation:** Use exact matching first, then longest-prefix matching, not substring inclusion.

---

## 4. Low Severity Issues (P3)

### LOW-001: Python Type Hint Uses `any` Instead of `Any`
**File:** `backend/apps/core/permissions.py:15`  
**Severity:** LOW

```python
F = TypeVar("F", bound=Callable[..., any])  # Should be typing.Any
```

---

### LOW-002: Frontend `isAuthenticated()` Checks Cookie Name Only
**File:** `frontend/lib/auth.ts:92`  
**Severity:** LOW  
**Impact:** Client-side check is easily bypassed; server validates anyway.

```typescript
return document.cookie.includes('sessionid=');
```

Any cookie named `sessionid` (even empty) passes this check. The server will reject invalid sessions, so this is mostly a UX issue.

---

### LOW-003: Missing `__str__` Methods on Some Models
**Files:** Various models  
**Severity:** LOW  
**Impact:** Poor Django admin UX.

Models like `WhelpedPup`, `WeightLog` have `__str__` methods but some models (e.g., `PNLSnapshot` in finance) use the auto-generated string representation.

---

### LOW-004: `rehome_flag` Calculation Uses Inexact Year Length
**File:** `backend/apps/operations/models.py:132-159`  
**Severity:** LOW

Uses `365.25` days/year which can cause off-by-one-day edge cases on leap years.

---

## 5. Architecture & Design Observations

### Positive Observations

1. **Good Multi-Tenancy Pattern:** The `entity` ForeignKey on nearly all models with `scope_entity()` queryset filtering provides clean data isolation without RLS complexity.

2. **HttpOnly Cookie Auth:** The session management correctly uses HttpOnly cookies with Redis-backed sessions, avoiding JWT exposure entirely.

3. **GST Calculation Is Correct:** Uses `price * 9 / 109` with `ROUND_HALF_UP`, matching IRAS requirements. Thomson entity correctly returns 0%.

4. **PDPA Hard Filter Present:** `PDPAService.filter_consent()` and `enforce_pdpa()` correctly apply `WHERE pdpa_consent=True` at queryset level.

5. **Audit Log Immutability:** Both `AuditLog` and `PDPAConsentLog` override `save()` and `delete()` to enforce append-only semantics.

6. **Closure Table Approach for COI:** Using a materialized closure table with Celery rebuilds is the correct architectural choice for this domain.

### Negative Observations

1. **Stub-Heavy Codebase:** Many "TODO" comments and stub implementations exist in production-facing code:
   - `PDFService.render_agreement_pdf()` - TODO email/WhatsApp sending
   - `AVSService.send_reminder()` - Actual sending not implemented
   - `sync_offline_queue` - Only handles 2 of 7 log types

2. **No Actual SSE Implementation:** The plans mention SSE for real-time alerts, but no SSE endpoint, event generator, or frontend EventSource connection exists.

3. **PWA Is Incomplete:** The service worker exists but:
   - No `manifest.json`
   - No IndexedDB offline queue (only a stub `/api/proxy/sync-offline` endpoint)
   - Background sync handler calls a non-existent endpoint

4. **No Production Hardening:** Missing:
   - `X-Content-Type-Options` header configuration
   - `Referrer-Policy` header
   - `Permissions-Policy` header
   - Request size limits
   - File upload validation/scanning

---

## 6. Phase-by-Phase Ground Truth Validation

### Phase 0: Infrastructure (Claimed: Complete)
| Requirement | Status | Notes |
|-------------|--------|-------|
| Docker Compose production | **MISSING** | `docker-compose.yml` does not exist |
| Docker Compose development | **MISSING** | `docker-compose.dev.yml` does not exist |
| PgBouncer config | **MISSING** | No `pgbouncer.ini` or similar |
| Redis × 3 config | **PARTIAL** | Django settings reference 3 Redis instances but no Docker config |
| Gotenberg sidecar | **PARTIAL** | Settings have URL but no compose/service definition |
| `wal_level=replica` | **UNVERIFIABLE** | No PostgreSQL config file in repo |

**Verdict:** NOT complete. Infrastructure exists only as Django settings, not as deployable artifacts.

---

### Phase 1: Auth, BFF, RBAC (Claimed: Complete)
| Requirement | Status | Notes |
|-------------|--------|-------|
| HttpOnly cookie sessions | **IMPLEMENTED** | Redis-backed, 15min access + 7day refresh |
| BFF Proxy | **IMPLEMENTED** | Path allowlisting works, but fallback URL is insecure |
| RBAC decorators | **IMPLEMENTED** | `require_role`, `scope_entity` functional |
| Idempotency middleware | **IMPLEMENTED** | 24h TTL, works for JSON bodies |
| Rate limiting | **IMPLEMENTED** | `django-ratelimit` on auth endpoints |
| CSRF rotation | **IMPLEMENTED** | Rotates on login and refresh |
| Zero JWT exposure | **VERIFIED** | No JWT tokens found anywhere |

**Verdict:** Core functionality complete but with security gaps (CORS, fallback URL).

---

### Phase 2: Domain Foundation (Claimed: Complete)
| Requirement | Status | Notes |
|-------------|--------|-------|
| Dog model with pedigree | **IMPLEMENTED** | Self-referential FKs for dam/sire |
| CSV import | **MISSING** | No CSV importer service exists |
| Vaccination model | **IMPLEMENTED** | Due date auto-calculation present |
| Entity scoping on dogs | **IMPLEMENTED** | All dog queries scoped by entity |
| Health records | **IMPLEMENTED** | Follow-up tracking present |

**Verdict:** Models complete, but operational features (CSV import) missing.

---

### Phase 3: Ground Operations (Claimed: Complete)
| Requirement | Status | Notes |
|-------------|--------|-------|
| 7 log models | **IMPLEMENTED** | All 7 models exist with proper fields |
| Draminski integration | **STUB** | `process_draminski_reading` task exists but service is incomplete |
| SSE real-time alerts | **MISSING** | No SSE endpoints or EventSource on frontend |
| PWA service worker | **PARTIAL** | SW exists but offline queue is stubbed |
| Background sync | **STUB** | Calls non-existent `/api/proxy/sync-offline` |

**Verdict:** Data models complete, real-time and offline features are stubs.

---

### Phase 4: Breeding & Genetics (In Progress)
| Requirement | Status | Notes |
|-------------|--------|-------|
| COI calculator | **IMPLEMENTED** | Wright's formula with closure table |
| Saturation check | **IMPLEMENTED** | `test_saturation.py` exists |
| Closure table | **IMPLEMENTED** | Celery rebuild task present |
| Async Celery rebuild | **IMPLEMENTED** | `rebuild_closure_table` task |
| Mate check override | **IMPLEMENTED** | `MateCheckOverride` model |

**Verdict:** Core engine functional, but closure table SQL has logic error (see MED-003).

---

### Phase 5: Sales & AVS (In Progress)
| Requirement | Status | Notes |
|-------------|--------|-------|
| Sales agreement model | **IMPLEMENTED** | State machine, signatures, PDF hash |
| AVS transfer tracking | **IMPLEMENTED** | `AVSTransfer` with token and status |
| 3-day reminders | **STUB** | `send_avs_reminder` task exists but actual sending not implemented |
| PDF generation | **STUB** | `PDFService` referenced but actual Gotenberg integration incomplete |
| HDB warning | **IMPLEMENTED** | Large breed check present |

**Verdict:** Data model and workflow complete, external integrations (email/WhatsApp/PDF) are stubs.

---

### Phase 6: Compliance & NParks (In Progress)
| Requirement | Status | Notes |
|-------------|--------|-------|
| 5-document Excel generation | **IMPLEMENTED** | All 5 sheets generated with openpyxl |
| GST ledger | **IMPLEMENTED** | `GSTLedger` with deterministic calculation |
| PDPA hard filter | **IMPLEMENTED** | `WHERE consent=true` at queryset level |
| Immutable audit trail | **IMPLEMENTED** | `PDPAConsentLog` append-only |

**Verdict:** Core compliance logic is the strongest part of the codebase.

---

### Phase 7: Customers & Marketing (In Progress)
| Requirement | Status | Notes |
|-------------|--------|-------|
| Customer model | **IMPLEMENTED** | PDPA consent tracking present |
| Communication log | **IMPLEMENTED** | Immutable, append-only |
| Marketing segments | **IMPLEMENTED** | `Segment` with JSON filters |
| Blast eligibility | **IMPLEMENTED** | PDPA filter enforced |

**Verdict:** Models complete, actual sending integration not present.

---

### Phase 8: Dashboard & Finance (In Progress)
| Requirement | Status | Notes |
|-------------|--------|-------|
| Transaction model | **IMPLEMENTED** | With intercompany transfer auto-balancing |
| GST report | **IMPLEMENTED** | Quarterly summaries |
| P&L snapshot | **IMPLEMENTED** | Monthly snapshots |
| Dashboard page | **IMPLEMENTED** | Next.js page with Suspense boundaries |

**Verdict:** Models and frontend present, data population and chart rendering untested.

---

## 7. Security Risk Register

| Risk ID | Risk | Likelihood | Impact | Mitigation Status |
|---------|------|------------|--------|-------------------|
| SEC-001 | BFF proxy fallback to localhost | High | High | **Unmitigated** |
| SEC-002 | CORS origin reflection for untrusted origins | Medium | High | **Unmitigated** |
| SEC-003 | Development settings default in ASGI | Low | Critical | **Unmitigated** |
| SEC-004 | CSP headers configured but not sent | High | Medium | **Unmitigated** |
| SEC-005 | Debug toolbar enabled in dev settings | N/A | Low (dev only) | **Acceptable** |
| SEC-006 | `sessionid` cookie check is client-side only | High | Low | **Partial** (server validates) |
| SEC-007 | No request body size limits | Medium | Medium | **Unmitigated** |
| SEC-008 | Path traversal check doesn't catch encoded `..` | Low | Medium | **Partial** |

---

## 8. Performance Observations

1. **COI Cache TTL:** 1 hour may be too short for stable pedigree data. Consider 24 hours with explicit invalidation on pedigree edits.

2. **Closure Table Full Rebuild:** `TRUNCATE + INSERT` is acceptable for batch jobs but will briefly leave the table empty. Consider using a staging table and `RENAME` swap for zero-downtime rebuilds.

3. **N+1 Queries in NParks Generation:** The `_generate_puppy_movement()` and `_generate_dog_movement()` methods iterate `agreement.line_items.all()` inside loops. With `prefetch_related`, this is mostly mitigated but `_generate_mating_sheet()` does an additional `Litter.objects.filter(breeding_record=record).first()` per row.

4. **Frontend API Client:** Every request checks `isAuthenticated()` which reads `document.cookie`. This is fast but called on every API call.

---

## 9. Recommendations

### Immediate (Before Any Deployment)
1. **Fix broken test suite** - Rewrite `test_auth.py` to match actual implementation or implement missing methods.
2. **Remove insecure fallbacks** - `BACKEND_INTERNAL_URL` must be required, not optional with localhost fallback.
3. **Fix CORS origin handling** - Reject untrusted origins instead of reflecting `ALLOWED_ORIGINS[0]`.
4. **Add Docker Compose files** - Create the missing `docker-compose.yml` and `docker-compose.dev.yml`.
5. **Fix ASGI default settings** - Default to production settings.
6. **Fix Celery task stubs** - Either implement or remove broken tasks.

### Short-Term (Before Production)
7. **Implement CSP middleware** - Add `django-csp` or custom middleware to actually send CSP headers.
8. **Fix closure table SQL** - Generate separate ancestor paths for dam and sire, not `COALESCE`.
9. **Add request validation** - Body size limits, upload file type validation.
10. **Complete PWA** - Add `manifest.json`, implement IndexedDB offline queue, fix background sync endpoint.
11. **Add security headers** - `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
12. **Fix GST rounding** - Ensure line-item GST sums exactly equal agreement GST.

### Medium-Term (Post-Production)
13. **Implement actual integrations** - Resend email, WhatsApp Business API, Gotenberg PDF rendering.
14. **Add SSE for real-time alerts** - Implement server-sent events endpoint and frontend EventSource.
15. **Add CSV importer** - Implement the missing bulk dog import service.
16. **Add production monitoring** - Health checks, structured logging, error tracking (Sentry).
17. **Database hardening** - Add `wal_level=replica` config, connection pooling validation.

---

## 10. Conclusion

The Wellfond BMS codebase demonstrates **strong architectural planning** and a solid understanding of the domain requirements. The multi-tenancy model, compliance engine (GST/PDPA/NParks), and breeding genetics calculations are well-conceived.

However, there is a **significant gap between planning and implementation**:
- Infrastructure artifacts are almost entirely missing
- Many features exist as data models but lack operational services
- External integrations (email, WhatsApp, PDF, SSE) are stubbed
- The test suite is broken due to API drift
- Security hardening has gaps that could expose the system in production

**The codebase is approximately 60-70% complete** relative to the planning documents. With focused effort on the critical issues identified in this report, the system could reach production readiness within 4-6 weeks of dedicated development.

**Priority order:** Fix security gaps → Fix broken tests → Add infrastructure → Implement stubs → Harden for production.

---

*End of Report*
