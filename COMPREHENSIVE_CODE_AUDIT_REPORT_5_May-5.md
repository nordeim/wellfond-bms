# Comprehensive Code Audit Report — Wellfond BMS
**Date:** 2026-05-05 | **Auditor:** Automated Code Review | **Version:** Final

---

## 1. Executive Summary

**Overall Assessment:** The Wellfond BMS codebase is a **well-architected, production-grade system** implementing 8 of 9 planned phases. The code demonstrates strong adherence to the Master Execution Plan (MEP) v1.1 with proper BFF security, compliance determinism, and entity scoping. However, several critical and high-severity issues require attention before production deployment.

### Findings Summary

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 CRITICAL | 5 | Security vulnerabilities, data integrity risks |
| 🟠 HIGH | 12 | Significant bugs, missing features, compliance gaps |
| 🟡 MEDIUM | 18 | Code quality, inconsistencies, incomplete implementations |
| 🟢 LOW | 14 | Style, documentation, minor improvements |
| **Total** | **49** | |

### Key Strengths
- ✅ Zero AI imports in compliance module (verified via grep)
- ✅ HttpOnly cookie auth with zero JWT exposure to client JS
- ✅ Immutable audit logs with save/delete overrides
- ✅ Proper entity scoping across all domain apps
- ✅ Comprehensive idempotency middleware
- ✅ Well-structured Celery task routing with split queues
- ✅ 364 test functions across 33 test files

### Key Risks
- ❌ BFF proxy path allowlist blocks SSE stream endpoints
- ❌ Several placeholder implementations (email, WhatsApp, archival)
- ❌ Phase 9 (Observability) entirely unimplemented
- ❌ Frontend test coverage is minimal

---

## 2. Architecture Validation

The implementation **closely matches** the planned architecture from `IMPLEMENTATION_PLAN.md`:

| Architectural Principle | Status | Evidence |
|------------------------|--------|----------|
| BFF Security (HttpOnly cookies) | ✅ Implemented | `frontend/app/api/proxy/[...path]/route.ts` forwards cookies; `frontend/lib/auth.ts` uses in-memory cache only |
| Compliance Determinism (Zero AI) | ✅ Verified | `grep -r "import anthropic/openai/langchain" backend/apps/compliance/` → 0 matches |
| AI Sandbox Isolation | ⚠️ Partial | `backend/apps/ai_sandbox/` exists but only has `__init__.py` |
| Entity Scoping | ✅ Implemented | `scope_entity()` in `permissions.py`, applied across all routers |
| Idempotent Sync | ✅ Implemented | `IdempotencyMiddleware` with Redis store, UUIDv4 keys |
| Async Closure (No DB Triggers) | ✅ Implemented | `breeding/tasks.py` uses `@shared_task` for closure rebuild |
| Gotenberg PDF | ✅ Implemented | `sales/services/pdf.py` calls Gotenberg sidecar |
| Native Celery | ✅ Implemented | All tasks use `@shared_task`, no `django.tasks` bridge |
| Split Redis Instances | ✅ Implemented | 4 Redis instances: sessions, broker, cache, idempotency |
| SSE Realtime | ✅ Implemented | `operations/routers/stream.py` with async generators |

**Architecture Score: 9/10** — Minor gap in AI sandbox completeness.

---

## 3. Phase Completion Verification

| Phase | Claimed | Verified | Notes |
|-------|---------|----------|-------|
| 0: Infrastructure | ✅ Complete | ✅ Confirmed | Docker, CI/CD, settings, all present |
| 1: Auth, BFF, RBAC | ✅ Complete | ✅ Confirmed | Auth, middleware, permissions, design system |
| 2: Domain Foundation | ✅ Complete | ✅ Confirmed | Dog CRUD, health, vaccines, alerts, importers |
| 3: Ground Operations | ✅ Complete | ✅ Confirmed | 7 log types, Draminski, SSE, PWA, offline queue |
| 4: Breeding & Genetics | ✅ Complete | ✅ Confirmed | COI, saturation, closure table, mate checker |
| 5: Sales & AVS | ✅ Complete | ⚠️ Partial | Models complete, PDF service has fallback, AVS reminders work |
| 6: Compliance & NParks | ✅ Complete | ⚠️ Partial | GST/PDPA solid, NParks Excel gen needs template files |
| 7: Customers & Marketing | ✅ Complete | ⚠️ Partial | Models/segmentation done, email/WA are placeholders |
| 8: Dashboard & Finance | ✅ Complete | ✅ Confirmed | P&L, GST reports, intercompany, dashboard |
| 9: Observability | 📋 Backlog | ❌ Not Started | No OTel, no runbooks, no load tests |

**Completion Score: 8/9 phases substantially complete (89%)**

---

## 4. Critical Issues (Severity: CRITICAL)

### C-001: BFF Proxy Blocks SSE Stream Endpoints
- **Severity:** CRITICAL
- **Category:** Bug
- **Location:** `frontend/app/api/proxy/[...path]/route.ts:57-68`
- **Description:** The path allowlist regex `^\/(auth|users|dogs|breeding|sales|compliance|customers|finance|operations)` does not include `stream`. The SSE alert stream endpoint at `/api/v1/stream/alerts` would be blocked with a 403 Forbidden.
- **Impact:** Real-time alert delivery (nursing flags, heat cycles, overdue alerts) is completely broken through the BFF proxy. Ground staff cannot receive live alerts.
- **Recommended Fix:** Add `stream` to the allowed path regex:
  ```typescript
  const allowedPattern = /^\/(auth|users|dogs|breeding|sales|compliance|customers|finance|operations|stream)(\/.*|$)/;
  ```

### C-002: Immutable CommunicationLog Modified in handle_bounce
- **Severity:** CRITICAL
- **Category:** Data Integrity
- **Location:** `backend/apps/customers/services/blast.py:238-250`
- **Description:** `BlastService.handle_bounce()` calls `log.status = "BOUNCED"` then `log.save()` on a `CommunicationLog` model that overrides `save()` to raise `ValueError` on non-adding saves. This will crash at runtime.
- **Impact:** Bounce handling is broken. Bounced emails/WhatsApp messages cannot be tracked, breaking compliance audit trails.
- **Recommended Fix:** Create a new `CommunicationLog` entry with `BOUNCED` status instead of modifying the existing one, or add a dedicated `BounceLog` model.

### C-003: Celery Beat Schedule Duplicate Definitions
- **Severity:** CRITICAL (config conflict)
- **Category:** Bug
- **Location:** `backend/config/celery.py:17-32` and `backend/config/settings/base.py:107-120`
- **Description:** Beat schedule is defined in both `celery.py` and `settings/base.py` with different task paths (e.g., `apps.sales.tasks.avs_reminder_check` vs `apps.sales.tasks.check_avs_reminders`). The `celery.py` version uses `crontab` while settings use `interval`. The `celery.py` settings may override or conflict with the Django settings version.
- **Impact:** Scheduled tasks may fire at wrong times or not at all. AVS reminders, vaccine checks, and rehome checks could be unreliable.
- **Recommended Fix:** Consolidate beat schedule to a single location (prefer `celery.py` with `crontab` for explicit scheduling).

### C-004: check_rehome_overdue Task is a Stub
- **Severity:** CRITICAL
- **Category:** Bug
- **Location:** `backend/apps/operations/tasks.py:136-139`
- **Description:** The `check_rehome_overdue` task is registered in the Celery beat schedule but only returns `{"status": "success"}` without any actual logic. The comment says "FIX CRIT-006: Define missing task referenced in schedule" but the implementation is empty.
- **Impact:** Dogs approaching or past rehome age (5-6yr yellow, 6yr+ red) are never flagged automatically. This is a compliance/business requirement failure.
- **Recommended Fix:** Implement the actual rehome overdue checking logic using `Dog.rehome_flag` property and the alert service.

### C-005: archive_old_logs Task Doesn't Archive
- **Severity:** CRITICAL
- **Category:** Bug
- **Location:** `backend/apps/operations/tasks.py:152-183`
- **Description:** The `archive_old_logs` task counts old logs but has a TODO comment: "Implement actual archival (e.g. move to archive table)". It only counts but never moves or deletes data.
- **Impact:** Database will grow unboundedly. Log tables will accumulate years of data without cleanup.
- **Recommended Fix:** Implement actual archival: either move to archive tables, export to cold storage, or soft-delete with retention policy.

---

## 5. High-Severity Issues

### H-001: Email/WhatsApp Sending Are Placeholders
- **Severity:** HIGH
- **Category:** Incomplete Feature
- **Location:** `backend/apps/customers/services/blast.py:165-215`
- **Description:** Both `send_email()` and `send_whatsapp()` methods are marked as `PLACEHOLDER` with simulated responses. The actual Resend SDK and WhatsApp Business API integrations are not implemented.
- **Impact:** Marketing blasts, AVS reminders, and agreement PDF delivery cannot actually send messages. All communication is simulated.
- **Recommended Fix:** Integrate Resend SDK for email and WhatsApp Business Cloud API for messaging.

### H-002: No HTTPS Redirect in Nginx Configuration
- **Severity:** HIGH
- **Category:** Security
- **Location:** `infra/docker/nginx/nginx.conf`
- **Description:** Nginx only listens on port 443 with SSL. There's no HTTP→HTTPS redirect on port 80. Users accessing `http://` will get connection refused instead of a redirect.
- **Impact:** Users may not know to use HTTPS. Search engines may index HTTP version.
- **Recommended Fix:** Add a port 80 server block with 301 redirect to HTTPS.

### H-003: Missing ai_sandbox App Implementation
- **Severity:** HIGH
- **Category:** Incomplete Feature
- **Location:** `backend/apps/ai_sandbox/`
- **Description:** The AI sandbox app only contains `__init__.py`. Per the MEP, it should contain OCR, marketing draft generation, and human-in-the-loop workflows. It's also commented out in `INSTALLED_APPS`.
- **Impact:** Claude OCR for document processing and AI-assisted marketing drafts are not available.
- **Recommended Fix:** Implement the AI sandbox with proper isolation, or document that it's intentionally deferred.

### H-004: Dashboard Revenue Uses signed_at Instead of completed_at
- **Severity:** HIGH
- **Category:** Bug
- **Location:** `backend/apps/core/services/dashboard.py:89-95`
- **Description:** `get_revenue_summary()` filters by `signed_at__gte=start_date` but revenue should be recognized when agreements are completed, not just signed. A signed agreement may still be cancelled.
- **Impact:** Revenue figures may be inflated by including agreements that were later cancelled.
- **Recommended Fix:** Filter by `completed_at` instead of `signed_at` for revenue recognition.

### H-005: GOTENBERG_URL Mismatch in Development
- **Severity:** HIGH
- **Category:** Bug
- **Location:** `backend/config/settings/base.py:163` and `backend/apps/sales/services/pdf.py:17`
- **Description:** `base.py` sets `GOTENBERG_URL = "http://gotenberg:3000"` (container hostname), but `pdf.py` defaults to `http://localhost:3000`. In development without Gotenberg, this hits the Next.js dev server instead.
- **Impact:** PDF generation in development may fail silently or produce unexpected results.
- **Recommended Fix:** Use a distinct port for Gotenberg (e.g., 3001) and ensure consistent configuration.

### H-006: No Gotenberg Sidecar in Development Docker Compose
- **Severity:** HIGH
- **Category:** Incomplete Feature
- **Location:** `infra/docker/docker-compose.yml`
- **Description:** The development docker-compose only has PostgreSQL and Redis. Gotenberg is not included, so PDF generation falls back to the mock HTML output.
- **Impact:** PDF generation cannot be tested in development. Agreement PDFs are HTML files, not actual PDFs.
- **Recommended Fix:** Add Gotenberg service to the development docker-compose.

### H-007: Frontend api.ts Evaluates BACKEND_INTERNAL_URL Client-Side
- **Severity:** HIGH
- **Category:** Security
- **Location:** `frontend/lib/api.ts:17`
- **Description:** `const API_BASE_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000'` is evaluated at module load time. While the `typeof window` check in `buildUrl` prevents client-side usage, the variable is still set in the client bundle.
- **Impact:** The internal backend URL may be visible in the client JavaScript bundle, though it's not used for client requests.
- **Recommended Fix:** Move the server-side URL construction entirely into the `buildUrl` function with a dynamic check.

### H-008: Missing Service Worker File
- **Severity:** HIGH
- **Category:** Incomplete Feature
- **Location:** `frontend/lib/pwa/register.ts`
- **Description:** The PWA registration code references a service worker but the actual `sw.js` or service worker file was not found in the expected location (`frontend/public/sw.js`). The `offline-queue` implementation exists but the SW precaching strategy is unclear.
- **Impact:** PWA offline functionality may not work correctly. Background sync on reconnect may fail.
- **Recommended Fix:** Verify and implement the complete service worker with proper precaching and background sync.

### H-009: Idempotency Cache Cleanup Uses Internal Redis API
- **Severity:** HIGH
- **Category:** Bug
- **Location:** `backend/apps/operations/tasks.py:72-90`
- **Description:** `cleanup_old_idempotency_keys` accesses `cache.client.get_client()` which is an internal Django Redis cache API. This is fragile and may break on Django/redis-py version updates.
- **Impact:** Cache cleanup may fail silently or break on dependency updates.
- **Recommended Fix:** Use Django's cache API methods or implement cleanup via Redis TTL (already handled by the 24h TTL on idempotency keys).

### H-010: No CSP Nonce Implementation
- **Severity:** HIGH
- **Category:** Security
- **Location:** `backend/config/settings/base.py:147-157`
- **Description:** CSP is configured with `'unsafe-inline'` for style-src (justified for Tailwind JIT) but there's no nonce-based CSP for script-src. The MEP specified `script-src 'self' 'strict-dynamic'` with nonce injection.
- **Impact:** CSP provides less protection against XSS than planned. Inline scripts could be injected.
- **Recommended Fix:** Implement CSP nonce generation in middleware and inject into HTML responses.

### H-011: No OpenTelemetry Instrumentation
- **Severity:** HIGH
- **Category:** Incomplete Feature
- **Location:** Phase 9 not implemented
- **Description:** Phase 9 (Observability) is entirely unimplemented. No OpenTelemetry setup, no Prometheus metrics, no Grafana dashboards, no structured logging enrichment.
- **Impact:** No observability in production. Cannot trace requests, monitor performance, or detect issues proactively.
- **Recommended Fix:** Implement Phase 9 observability stack.

### H-012: Missing Load Testing and Runbooks
- **Severity:** HIGH
- **Category:** Incomplete Feature
- **Location:** Phase 9 not implemented
- **Description:** No k6 load test scripts, no RUNBOOK.md, no SECURITY.md, no DEPLOYMENT.md. These are critical for production readiness.
- **Impact:** Cannot validate performance budgets. No operational documentation for incident response.
- **Recommended Fix:** Create load tests, runbooks, and security documentation.

---

## 6. Medium-Severity Issues

### M-001: Vaccination.save() Has Circular Import Risk
- **Severity:** MEDIUM
- **Category:** Code Quality
- **Location:** `backend/apps/operations/models.py:156-168`
- **Description:** `Vaccination.save()` imports `calc_vaccine_due` from `services.vaccine` inside the method. While this avoids circular imports at module level, it's a code smell and the `ImportError` catch silently suppresses failures.
- **Impact:** If the vaccine service has import errors, due dates won't be calculated and the error is silently logged.

### M-002: Inconsistent Error Handling Across Routers
- **Severity:** MEDIUM
- **Category:** Code Quality
- **Location:** Multiple router files
- **Description:** Some endpoints use `raise HttpError(status, message)` while others use `return JsonResponse({"error": ...}, status=...)`. The auth router uses `@ratelimit` decorators that may conflict with Ninja's error handling.
- **Impact:** Inconsistent error response formats make frontend error handling more complex.

### M-003: Entity.gst_rate Field Size May Overflow
- **Severity:** MEDIUM
- **Category:** Data Integrity
- **Location:** `backend/apps/core/models.py:108-112`
- **Description:** `gst_rate` is `max_digits=5, decimal_places=4`. This allows values up to 9.9999 (999.99%). While functional, the field definition is unusual for a percentage field.
- **Impact:** Low risk but could cause confusion. The default `0.09` is correct for 9% GST.

### M-004: BreedingRecord.save() Auto-Sets Entity from Dam
- **Severity:** MEDIUM
- **Category:** Code Quality
- **Location:** `backend/apps/breeding/models.py:79-81`
- **Description:** `save()` automatically sets `self.entity = self.dam.entity` if not set. This could mask entity assignment bugs and makes the entity relationship implicit.
- **Impact:** Entity scoping could be incorrect if dam's entity changes after breeding record creation.

### M-005: Frontend Test Coverage Is Minimal
- **Severity:** MEDIUM
- **Category:** Testing
- **Location:** `frontend/tests/` and `frontend/__tests__/`
- **Description:** Only 4 frontend test files exist: `dashboard.test.tsx`, `use-auth.test.ts`, `use-breeding-path.test.ts`, `offline-queue.test.ts`. No component tests, no hook tests for most hooks, no integration tests.
- **Impact:** Frontend regressions are likely to go undetected. The ≥85% coverage target is not met for frontend.

### M-006: No Database Migrations for Phase 5-8 Schema Changes
- **Severity:** MEDIUM
- **Category:** Data Integrity
- **Location:** `backend/apps/sales/migrations/`, `backend/apps/compliance/migrations/`, etc.
- **Description:** Some apps only have `0001_initial.py` migrations. Schema changes from later phases may not have corresponding migration files, or the initial migration includes all fields.
- **Impact:** Migration conflicts possible when deploying incremental changes.

### M-007: SSE Stream Uses Polling Instead of Push
- **Severity:** MEDIUM
- **Category:** Performance
- **Location:** `backend/apps/operations/routers/stream.py:36-68`
- **Description:** The SSE implementation polls the database every 5 seconds (`asyncio.sleep(POLL_INTERVAL)`) instead of using Redis pub/sub for push-based notifications. This adds latency and database load.
- **Impact:** Alert delivery may be up to 5 seconds delayed. Under load, polling could become a bottleneck.

### M-008: Offline Queue localStorage Fallback
- **Severity:** MEDIUM
- **Category:** Code Quality
- **Location:** `frontend/lib/offline-queue/index.ts:43`
- **Description:** The offline queue has a localStorage fallback path. localStorage is inaccessible from Service Workers, which defeats the purpose of offline queuing.
- **Impact:** If IndexedDB is unavailable, the fallback to localStorage means Service Workers can't access the queue.

### M-009: Missing CSRF Token in BFF Proxy Headers
- **Severity:** MEDIUM
- **Category:** Security
- **Location:** `frontend/app/api/proxy/[...path]/route.ts`
- **Description:** The BFF proxy forwards cookies but doesn't explicitly forward the `X-CSRFToken` header. Django's CSRF middleware requires this for state-changing requests.
- **Impact:** POST/PUT/PATCH/DELETE requests through the proxy may fail CSRF validation if the token isn't in the cookie.

### M-010: No Rate Limiting on SSE Endpoints
- **Severity:** MEDIUM
- **Category:** Security
- **Location:** `backend/apps/operations/routers/stream.py`
- **Description:** SSE endpoints have no connection limits or rate limiting. A malicious client could open thousands of SSE connections, exhausting server resources.
- **Impact:** Potential DoS via SSE connection exhaustion.

### M-011: Duplicate Redis Configuration
- **Severity:** MEDIUM
- **Category:** Code Quality
- **Location:** `backend/config/settings/base.py` and `backend/config/settings/development.py`
- **Description:** Development settings override Redis URLs individually but the base settings already have sensible defaults. The development overrides for idempotency cache point to `redis://localhost:6379/2` which conflicts with the broker URL in the same file.
- **Impact:** In development, idempotency cache and broker may share the same Redis database, causing key collisions.

### M-012: No Input Sanitization on JSON Fields
- **Severity:** MEDIUM
- **Category:** Security
- **Location:** Multiple models with `JSONField` (photos, coordinates, filters_json)
- **Description:** JSON fields like `photos`, `coordinates`, and `filters_json` accept arbitrary JSON without size limits or content validation.
- **Impact:** Malicious users could store excessively large JSON payloads or inject unexpected data structures.

### M-013: Missing `select_related` in Some Query Patterns
- **Severity:** MEDIUM
- **Category:** Performance
- **Location:** Various router files
- **Description:** Some list endpoints don't use `select_related` for foreign key lookups, causing N+1 query problems. For example, listing dogs without prefetching entity, dam, sire.
- **Impact:** Performance degradation with large datasets. The dog list with 483 records could generate 1000+ queries.

### M-014: No Pagination on Log List Endpoint
- **Severity:** MEDIUM
- **Category:** Performance
- **Location:** `backend/apps/operations/routers/logs.py:262-303`
- **Description:** The `list_logs` endpoint collects all 7 log types with Python-side sorting. For dogs with extensive history, this could return unbounded results.
- **Impact:** Large response payloads and memory usage for dogs with long histories.

### M-015: CommunicationLog Immutability Breaks Bounce Handling
- **Severity:** MEDIUM
- **Category:** Data Integrity
- **Location:** `backend/apps/customers/services/blast.py:238-250`
- **Description:** (Related to C-002) The `handle_bounce` method attempts to modify an immutable model. Even if fixed to create new entries, the original "SENT" entry cannot be updated to reflect the bounce.
- **Impact:** Communication audit trail shows messages as "SENT" even when they bounced.

### M-016: Missing Environment Variable Validation
- **Severity:** MEDIUM
- **Category:** Configuration
- **Location:** `backend/config/settings/base.py`
- **Description:** Most environment variables have defaults or are optional. Critical variables like `DJANGO_SECRET_KEY` have a dev-only default but no validation that they're set in production.
- **Impact:** Production deployments could accidentally use the dev secret key.

### M-017: No Database Connection Health Check in Readiness Probe
- **Severity:** MEDIUM
- **Category:** Operations
- **Location:** `backend/config/urls.py:25-34`
- **Description:** The `ready_check` endpoint only tests `SELECT 1`. It doesn't verify Redis connectivity, Celery worker availability, or Gotenberg reachability.
- **Impact:** The readiness probe could return 200 even when critical dependencies are down.

### M-018: Frontend Missing Error Boundary
- **Severity:** MEDIUM
- **Category:** Code Quality
- **Location:** `frontend/app/layout.tsx`
- **Description:** The root layout has no React Error Boundary. Unhandled errors in any component will crash the entire application with a white screen.
- **Impact:** Poor user experience on errors. No graceful degradation.

---

## 7. Low-Severity Issues

### L-001: Inconsistent Naming Conventions
- **Severity:** LOW
- **Category:** Code Quality
- **Description:** Mix of `created_by`, `uploaded_by`, `sent_by`, `generated_by` for audit fields. Some models use `created_at`/`updated_at`, others use `timestamp`.

### L-002: Unused Imports
- **Severity:** LOW
- **Category:** Code Quality
- **Location:** Various files
- **Description:** Several files have unused imports (e.g., `TYPE_CHECKING` imports that are never used, `Decimal` imported but unused).

### L-003: Missing Docstrings on Some Functions
- **Severity:** LOW
- **Category:** Documentation
- **Description:** Some utility functions and helper methods lack docstrings. Test factories could benefit from better documentation.

### L-004: Hardcoded Entity Codes
- **Severity:** LOW
- **Category:** Code Quality
- **Location:** `backend/apps/compliance/services/gst.py:46`
- **Description:** `if entity.code.upper() == "THOMSON"` hardcodes the Thomson entity check. Should use a field like `is_gst_exempt` on the Entity model.

### L-005: No Storybook or Component Documentation
- **Severity:** LOW
- **Category:** Documentation
- **Description:** Frontend UI components have no Storybook stories or visual documentation. Makes design system adoption harder.

### L-006: Missing `.env.example` File
- **Severity:** LOW
- **Category:** Documentation
- **Description:** The `.env.example` file referenced in the plan doesn't exist at the root level (only referenced in README).

### L-007: Tailwind Config Not Found
- **Severity:** LOW
- **Category:** Configuration
- **Location:** `frontend/tailwind.config.ts`
- **Description:** The tailwind config file exists but wasn't reviewed. With Tailwind v4, configuration is primarily in CSS, making the config file potentially redundant.

### L-008: No Linting Configuration for Backend
- **Severity:** LOW
- **Category:** Code Quality
- **Description:** No `.flake8`, `pyproject.toml`, or `setup.cfg` found for consistent Python linting configuration.

### L-009: Frontend Components Mix Styling Approaches
- **Severity:** LOW
- **Category:** Code Quality
- **Description:** Some components use Tailwind utility classes, others use CSS modules or inline styles. Inconsistent styling approach.

### L-010: No API Versioning Strategy
- **Severity:** LOW
- **Category:** Architecture
- **Description:** All endpoints are under `/api/v1/` but there's no versioning strategy documented for future API changes.

### L-011: Missing Database Indexes for Common Queries
- **Severity:** LOW
- **Category:** Performance
- **Description:** Some frequently queried fields (e.g., `Dog.name` for search) lack dedicated indexes.

### L-012: No Graceful Degradation for Gotenberg
- **Severity:** LOW
- **Category:** Code Quality
- **Location:** `backend/apps/sales/services/pdf.py:95-102`
- **Description:** When Gotenberg is unavailable, the service falls back to mock HTML. This is good for dev but should log a warning in production.

### L-013: Frontend manifest.json Not Reviewed
- **Severity:** LOW
- **Category:** PWA
- **Description:** The PWA manifest exists but wasn't verified for completeness (icons, screenshots, etc.).

### L-014: No Automated Security Scanning in CI
- **Severity:** LOW
- **Category:** Security
- **Description:** The CI pipeline references Trivy scanning but the actual `.github/workflows/ci.yml` wasn't verified to include it.

---

## 8. Security Audit

### 8.1 BFF Proxy Security

| Check | Status | Notes |
|-------|--------|-------|
| Server-only BACKEND_INTERNAL_URL | ✅ | No `NEXT_PUBLIC_` prefix |
| Path allowlist | ⚠️ | Missing `stream` endpoint |
| Header stripping | ✅ | Strips host, x-forwarded-* |
| CORS configuration | ✅ | Proper origin validation |
| Cookie forwarding | ✅ | HttpOnly cookies forwarded |
| Edge Runtime removed | ✅ | Uses Node.js runtime |
| Null byte injection prevention | ✅ | Checked in `isAllowedPath` |
| Path traversal prevention | ✅ | `..` detection in path |

### 8.2 Authentication Security

| Check | Status | Notes |
|-------|--------|-------|
| HttpOnly cookies | ✅ | Set in `auth.py` |
| Secure flag (production) | ✅ | `secure=not settings.DEBUG` |
| SameSite=Lax | ✅ | Configured in auth |
| CSRF rotation on login | ✅ | `rotate_token()` called |
| Session in Redis | ✅ | 15min access / 7d refresh |
| Rate limiting on login | ✅ | 5 attempts/min per IP |
| No JWT in localStorage | ✅ | Verified via grep |
| Password validation | ✅ | Django validators enabled |

### 8.3 CSP Configuration

| Check | Status | Notes |
|-------|--------|-------|
| Production CSP enforced | ✅ | `REPORT_ONLY = {}` |
| No unsafe-eval (prod) | ✅ | Only in dev settings |
| unsafe-inline for styles | ⚠️ | Required for Tailwind JIT |
| No nonce implementation | ⚠️ | Planned but not implemented |
| Strict-dynamic | ❌ | Not implemented |

### 8.4 PDPA Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Hard consent filter | ✅ | `filter_consent()` in queryset |
| Immutable consent log | ✅ | `save()`/`delete()` overrides |
| Blast exclusion | ✅ | PDPA filter applied before send |
| No override path | ✅ | Consent=false always excluded |

### 8.5 Idempotency

| Check | Status | Notes |
|-------|--------|-------|
| UUIDv4 keys | ✅ | Generated in frontend |
| Redis store (24h TTL) | ✅ | Dedicated Redis instance |
| Atomic lock (SET NX) | ✅ | `cache.add()` in middleware |
| Duplicate detection | ✅ | Returns cached response |
| Required on write endpoints | ✅ | Configurable path list |

---

## 9. Compliance Audit

### 9.1 NParks Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Zero AI in compliance | ✅ | Verified via grep |
| 5-document Excel gen | ⚠️ | Service exists, template files not verified |
| Dual-sire columns | ✅ | Supported in models |
| Month lock (immutable) | ✅ | Status LOCKED prevents edits |
| Entity scoping | ✅ | Per-entity submissions |

### 9.2 GST Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Formula: price × 9 / 109 | ✅ | `extract_gst()` implemented |
| ROUND_HALF_UP | ✅ | Used in both compliance and sales |
| Thomson = 0% | ✅ | Entity code check |
| Decimal throughout | ✅ | No float arithmetic |
| Quarterly reporting | ✅ | IRAS format |

### 9.3 PDPA Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Hard WHERE filter | ✅ | Applied at queryset level |
| Immutable audit trail | ✅ | Append-only model |
| Blast eligibility check | ✅ | Pre-send validation |
| No override path | ✅ | Consent=False blocks all |

### 9.4 AVS Compliance

| Check | Status | Notes |
|-------|--------|-------|
| Transfer tracking | ✅ | AVSTransfer model |
| Unique tokens | ✅ | Per-buyer tokens |
| 3-day reminder | ✅ | Celery beat daily check |
| Escalation logic | ✅ | Auto-escalate after 72h |

### 9.5 Audit Immutability

| Check | Status | Notes |
|-------|--------|-------|
| AuditLog immutable | ✅ | `save()`/`delete()` overrides |
| PDPAConsentLog immutable | ✅ | Same pattern |
| CommunicationLog immutable | ⚠️ | Breaks bounce handling |
| PDF hash (SHA-256) | ✅ | Computed and stored |

---

## 10. Performance Analysis

### 10.1 COI Calculation

| Metric | Target | Status |
|--------|--------|--------|
| Algorithm | Wright's formula | ✅ Implemented |
| Closure table | O(1) lookups | ✅ Used |
| Redis caching | 1h TTL | ✅ Implemented |
| Async support | sync_to_async | ✅ Implemented |
| 5-generation depth | Configurable | ✅ Default 5 |
| p95 < 500ms | Not tested | ⚠️ No load tests |

### 10.2 SSE Delivery

| Metric | Target | Status |
|--------|--------|--------|
| Delivery latency | < 500ms | ⚠️ Polling every 5s |
| Auto-reconnect | 3s delay | ✅ Implemented |
| Entity scoping | Per-user | ✅ Implemented |
| Heartbeat | 5s interval | ✅ Implemented |
| Connection limits | None | ❌ Missing |

### 10.3 Query Optimization

| Area | Status | Notes |
|------|--------|-------|
| select_related | ⚠️ | Used in some endpoints, missing in others |
| Prefetch_related | ⚠️ | Used for dog detail, not for lists |
| Database indexes | ✅ | Comprehensive index coverage |
| Pagination | ✅ | Manual pagination in most endpoints |
| CONN_MAX_AGE=0 | ✅ | Correct for PgBouncer |

---

## 11. Test Coverage Assessment

### Backend Tests: 364 test functions across 33 files

| Module | Test Files | Coverage Assessment |
|--------|-----------|---------------------|
| core | 12 files | ✅ Good - auth, permissions, middleware, idempotency, dashboard |
| operations | 4 files | ✅ Good - dogs, importers, logs, SSE |
| breeding | 3 files | ✅ Good - COI, saturation, async COI |
| sales | 5 files | ✅ Good - agreements, AVS, GST, PDF |
| compliance | 3 files | ✅ Good - NParks, GST, PDPA |
| customers | 2 files | ⚠️ Moderate - blast, segmentation |
| finance | 3 files | ⚠️ Moderate - P&L, GST, transactions |

### Frontend Tests: ~4 test files

| Area | Status |
|------|--------|
| Unit tests | ❌ Minimal - only 4 test files |
| Component tests | ❌ None |
| Hook tests | ❌ Minimal (1 file) |
| E2E tests | ⚠️ 1 Playwright spec |
| Coverage target (85%) | ❌ Not met |

### Missing Test Areas
- No integration tests for BFF proxy → Django flow
- No load tests (k6 scripts)
- No security tests (OWASP ZAP)
- No visual regression tests
- No accessibility tests

---

## 12. Frontend Audit

### 12.1 Component Quality

| Aspect | Assessment |
|--------|------------|
| Design system | ✅ Comprehensive UI primitives (button, input, card, badge, dialog, table, tabs, select, toast, skeleton, progress) |
| Theming | ✅ Tangerine Sky palette with CSS custom properties |
| Responsiveness | ✅ Mobile-first with breakpoints |
| Accessibility | ⚠️ Radix UI provides base a11y, but no explicit ARIA testing |
| Animation | ✅ Framer Motion for transitions |

### 12.2 TypeScript Strictness

| Aspect | Assessment |
|--------|------------|
| Type definitions | ✅ Comprehensive types in `lib/types.ts` |
| API types | ✅ Typed fetch wrapper with generics |
| No `any` usage | ⚠️ Some `any` in error handling |
| Strict mode | ✅ Enabled in tsconfig |

### 12.3 PWA Implementation

| Aspect | Assessment |
|--------|------------|
| Manifest | ✅ Present at `public/manifest.json` |
| Service Worker | ⚠️ Registration code exists, SW file unclear |
| Offline queue | ✅ IndexedDB-backed with adapter pattern |
| Background sync | ⚠️ Code exists but SW integration unclear |
| Install prompt | ❌ Not implemented |

### 12.4 State Management

| Aspect | Assessment |
|--------|------------|
| Server state | ✅ TanStack Query for caching |
| Client state | ✅ Zustand (referenced in package.json) |
| Auth state | ✅ In-memory cache (no localStorage) |
| Offline state | ✅ IndexedDB queue |

---

## 13. Backend Audit

### 13.1 Django Models

| Aspect | Assessment |
|--------|------------|
| UUID primary keys | ✅ All models use UUID |
| Entity scoping | ✅ ForeignKey to Entity on all domain models |
| Immutability | ✅ AuditLog, PDPAConsentLog, CommunicationLog |
| Indexes | ✅ Comprehensive index coverage |
| Constraints | ✅ Unique constraints, validators |
| on_delete | ✅ PROTECT for important FKs, CASCADE for children |

### 13.2 Service Layer

| Aspect | Assessment |
|--------|------------|
| Separation of concerns | ✅ Clear service/routers/models split |
| Pure functions | ✅ GST, COI, Draminski are deterministic |
| Error handling | ⚠️ Inconsistent across services |
| Logging | ✅ Structured logging with python-json-logger |
| Transaction management | ✅ `transaction.atomic()` used correctly |

### 13.3 Middleware Stack

| Middleware | Order | Status |
|------------|-------|--------|
| SecurityMiddleware | 1 | ✅ |
| CSPMiddleware | 2 | ✅ |
| CorsMiddleware | 3 | ✅ |
| SessionMiddleware | 4 | ✅ |
| CommonMiddleware | 5 | ✅ |
| CsrfViewMiddleware | 6 | ✅ |
| AuthenticationMiddleware (Django) | 7 | ✅ |
| AuthenticationMiddleware (Custom) | 8 | ✅ |
| MessageMiddleware | 9 | ✅ |
| XFrameOptionsMiddleware | 10 | ✅ |
| IdempotencyMiddleware | 11 | ✅ |
| EntityScopingMiddleware | 12 | ✅ |
| RatelimitMiddleware | 13 | ✅ |

### 13.4 Celery Configuration

| Aspect | Assessment |
|--------|------------|
| Split queues | ✅ high, default, low, dlq |
| Beat schedule | ⚠️ Duplicate definitions |
| Task routing | ✅ Compliance→high, marketing→default |
| Retry policy | ✅ Configured per task |
| DLQ support | ✅ Queue defined |

---

## 14. Infrastructure Audit

### 14.1 Docker Configuration

| Aspect | Production | Development |
|--------|-----------|-------------|
| PostgreSQL 17 | ✅ wal_level=replica | ✅ wal_level=replica |
| PgBouncer | ✅ Transaction pooling | ❌ Not included |
| Redis instances | ✅ 4 separate (sessions, broker, cache, idempotency) | ⚠️ Single instance |
| Gotenberg | ✅ Included | ❌ Not included |
| Nginx | ❌ Not in prod compose | ✅ SSL termination |
| Network isolation | ✅ backend_net / frontend_net | ✅ Single network |
| Healthchecks | ✅ All services | ✅ PG + Redis |
| Non-root user | ✅ Dockerfile | ✅ Dockerfile |

### 14.2 Nginx Configuration

| Aspect | Assessment |
|--------|------------|
| SSL termination | ✅ Certificate configured |
| HTTP→HTTPS redirect | ❌ Missing |
| Security headers | ✅ HSTS, X-Content-Type-Options, X-Frame-Options |
| Proxy to Next.js | ✅ Configured |
| SSE support | ✅ Upgrade headers |

### 14.3 Dockerfile Quality

| Aspect | Assessment |
|--------|------------|
| Multi-stage build | ✅ Builder → Runtime → Security scan |
| Non-root user | ✅ `wellfond` user |
| Health check | ✅ curl to /health/ |
| Base image | ✅ python:3.13-slim |
| Dependency pinning | ✅ Requirements files |

---

## 15. Gap Analysis: Planned vs Implemented

| Planned Feature | Implemented | Gap |
|----------------|-------------|-----|
| BFF Proxy with path allowlist | ✅ | Missing `stream` endpoint |
| HttpOnly cookie auth | ✅ | Complete |
| RBAC with role decorators | ✅ | Complete |
| Entity scoping | ✅ | Complete |
| Idempotency middleware | ✅ | Complete |
| Dog CRUD with filters | ✅ | Complete |
| CSV import | ✅ | Complete |
| 7 ground log types | ✅ | Complete |
| Draminski interpreter | ✅ | Complete |
| SSE alert stream | ⚠️ | Implemented but blocked by BFF proxy |
| PWA offline queue | ✅ | IndexedDB implementation |
| Service Worker | ⚠️ | Registration code exists, SW unclear |
| COI calculator | ✅ | Wright's formula with closure table |
| Farm saturation | ✅ | Entity-scoped calculation |
| Sales agreements (B2C/B2B/REHOME) | ✅ | Complete model and service |
| PDF generation | ✅ | Gotenberg with HTML fallback |
| E-signature capture | ✅ | Signature model with coordinates |
| AVS tracking | ✅ | State machine with reminders |
| NParks Excel generation | ⚠️ | Service exists, templates not verified |
| GST engine (9/109) | ✅ | Deterministic with ROUND_HALF_UP |
| PDPA hard filter | ✅ | Queryset-level enforcement |
| Customer CRM | ✅ | Complete model |
| Segmentation | ✅ | Dynamic Q-object filters |
| Marketing blast | ⚠️ | Placeholder email/WA implementations |
| P&L statement | ✅ | With YTD and intercompany |
| GST reports | ✅ | IRAS format |
| Dashboard | ✅ | Role-aware with caching |
| OpenTelemetry | ❌ | Not implemented |
| CSP nonce | ❌ | Not implemented |
| Load testing (k6) | ❌ | Not implemented |
| Runbooks | ❌ | Not implemented |
| Security documentation | ❌ | Not implemented |

**Implementation Completeness: ~85%** (core features complete, Phase 9 and some integrations pending)

---

## 16. Recommendations (Prioritized)

### Immediate (Before Production)

1. **🔴 Fix BFF proxy path allowlist** — Add `stream` to allowed paths (C-001)
2. **🔴 Fix CommunicationLog immutability in bounce handling** (C-002)
3. **🔴 Consolidate Celery beat schedule** (C-003)
4. **🔴 Implement check_rehome_overdue task** (C-004)
5. **🔴 Implement archive_old_logs task** (C-005)
6. **🟠 Integrate Resend SDK for email** (H-001)
7. **🟠 Add HTTP→HTTPS redirect in Nginx** (H-002)
8. **🟠 Fix dashboard revenue filter** (H-004)
9. **🟠 Implement CSP nonce** (H-010)
10. **🟠 Add environment variable validation** (M-016)

### Short-Term (Before Scale)

11. **🟠 Implement OpenTelemetry** (H-011)
12. **🟠 Create runbooks and security docs** (H-012)
13. **🟠 Add frontend test coverage** (M-005)
14. **🟡 Implement Redis pub/sub for SSE** (M-007)
15. **🟡 Add SSE connection limits** (M-010)
16. **🟡 Add React Error Boundary** (M-018)
17. **🟡 Fix Redis config conflicts in dev** (M-011)

### Long-Term (Post-Launch)

18. **🟡 Implement AI sandbox** (H-003)
19. **🟡 Add load testing** (H-012)
20. **🟢 Add Storybook for components** (L-005)
21. **🟢 Standardize naming conventions** (L-001)
22. **🟢 Add API versioning strategy** (L-010)

---

## 17. Conclusion

The Wellfond BMS codebase demonstrates **strong engineering practices** with a well-thought-out architecture that closely follows the Master Execution Plan. The core domain logic (dogs, breeding, sales, compliance, finance) is solid and production-ready. The security architecture (BFF proxy, HttpOnly cookies, entity scoping, idempotency, PDPA enforcement) is exemplary.

However, **5 critical issues** and **12 high-severity issues** must be addressed before production deployment. The most impactful are:

1. The BFF proxy blocking SSE endpoints (breaks real-time alerts)
2. Placeholder email/WhatsApp integrations (breaks communication)
3. Missing Phase 9 observability (no production monitoring)
4. Stub tasks that silently do nothing (check_rehome_overdue, archive_old_logs)

The codebase is **85% complete** for production readiness. With the critical and high issues resolved, this system is well-positioned to serve as a reliable, compliant breeding management platform for Singapore's AVS-licensed operations.

---

*Report generated: 2026-05-05 | Total files analyzed: 150+ | Test functions found: 364*
