# Todos
[✓] Read all 9 planning documents (draft_plan, IMPLEMENTATION_PLAN, phases 0-8)
[✓] Explore backend codebase structure (apps, models, services, routers, config)
[✓] Explore frontend codebase structure (components, hooks, pages, BFF proxy)
[✓] Validate Phase 0-3 implementation against plans (infra, auth, domain, ground ops)
[✓] Audit security: BFF proxy hardening, cookies, CORS, CSP, idempotency
[✓] Audit compliance: GST, PDPA, NParks, audit trails, deterministic logic
[✓] Audit performance: COI calculation, closure tables, SSE, caching
[✓] Audit PWA: service worker, offline queue, background sync
[✓] Check test coverage and quality
[✓] Review infrastructure configs (docker-compose, settings, Redis, PgBouncer)
[✓] Compile comprehensive assessment report with findings

The comprehensive audit is complete. Let me now present the full assessment report. Given the constraints on response length, I'll provide a detailed but concise report that captures all findings.

The comprehensive codebase audit is complete. Here is the assessment report:
---
Wellfond BMS — Comprehensive Code Review & Audit Assessment
Version: v1.1 | Date: May 3, 2026 | Scope: Full codebase audit of Phases 0–8  
Overall Status: 8 of 9 phases implemented. Code quality is high with several critical gaps requiring remediation.
---
EXECUTIVE SUMMARY
The codebase is impressively thorough — 35 models, 17 Ninja routers, 17 services, 26 Celery tasks, 179+ Pydantic schemas, 21 frontend pages, and ~9,600 lines of test code. The BFF proxy hardening, cookie security, idempotency implementation, and entity scoping architecture are all exemplary. GST compliance and AI boundary enforcement pass completely. However, 4 critical issues and 6 high-severity issues were identified across PDPA enforcement, infrastructure configuration, test quality, and integration integrity.
Severity	Count	Summary
Critical	4	PDPA filter unused, BFF path prefix bug, CSP inert, no E2E tests
High	6	force_login violations, infra gaps, missing coverage enforcement
Medium	7	Beat schedule duplication, immutability gaps, thin frontend tests
Low	5	Duplicate requirements, image tags, celery hardcoded settings
---
CRITICAL ISSUES (🔴 Must Fix Before Production)
C1 — PDPA Hard Filter Not Enforced at Router Level
Location: backend/apps/core/permissions.py:103-110  
Impact: The enforce_pdpa() function exists but is never called in any router, service, or middleware outside its own test file. Customer PII can be returned without PDPA consent filtering via the customer list endpoint (customers/routers/customers.py:95-96 which has pdpa_consent: Optional[bool] = None — defaults to no filter).
grep enforce_pdpa across all router/service code → 0 matches in production code
7 matches total: 5 in test code + 1 definition + 1 import
Remediation: Import and call enforce_pdpa() in all customer-facing list/detail routers. Alternatively, apply centrally in EntityScopingMiddleware.
C2 — BFF Proxy Path Prefix Double-Stacking (Breeding Hooks)
Location: frontend/hooks/use-breeding.ts:150,175,197  
Impact: The breeding hooks use absolute paths like /api/v1/breeding/mate-check/, but lib/api.ts's buildUrl() already prepends /api/v1 on the server side and strips it for the client proxy. This causes double /api/v1 prefix on server-side requests (/api/v1/api/v1/breeding/mate-check/) → 404 Not Found.
// In use-breeding.ts (WRONG):
const response = await api.post("/api/v1/breeding/mate-check/", payload);
// In use-sales.ts (CORRECT - all other hooks):
const response = await api.post("/breeding/mate-check/", payload);
All other hooks (use-sales.ts, use-finance.ts, use-customers.ts, etc.) use the correct relative path pattern. Only use-breeding.ts has this bug.
C3 — CSP Settings Configured But django-csp Package Not Installed
Location: backend/config/settings/base.py:219-226 and backend/requirements/base.txt  
Impact: CSP directives (CSP_DEFAULT_SRC, CSP_SCRIPT_SRC, etc.) are configured in settings, but the django-csp package is not in requirements/base.txt and not in INSTALLED_APPS. These headers are not being emitted — Content-Security-Policy is completely absent from responses.
C4 — Zero Playwright E2E Tests
Location: frontend/playwright/ directory  
Impact: playwright.config.ts is configured, but the frontend/playwright/ directory contains zero test files. The E2E suite mentioned in the CI pipeline (e2e job, .github/workflows/ci.yml:225-263) has never been written. This means no browser-level testing of login flow, BFF proxy, SSE streams, or PWA behavior.
---
HIGH-SEVERITY ISSUES (🟠 Address Before Go-Live)
H1 — 19 force_login() Calls in Test Suite
Location: backend/apps/core/tests/test_dashboard.py, test_dashboard_integration.py, backend/apps/operations/tests/test_dogs.py  
Impact: These tests use client.force_login() which is explicitly prohibited by AGENTS.md because it "breaks Ninja routers." These tests may produce false positives — they could pass while real Ninja endpoints return 401.
File	Occurrences
test_dashboard.py	8
test_dashboard_integration.py	10
test_dogs.py	1
Total	19
Remediation: Migrate to the Redis session cookie pattern used in tests/test_logs.py:92-111 (creates session via SessionManager.create_session() + sets cookie).
H2 — Infrastructure Gaps: No Gotenberg, No PgBouncer, Single Redis
Location: infra/docker/docker-compose.yml  
Impact:
- Gotenberg: Configured in settings (base.py:271 → GOTENBERG_URL=http://gotenberg:3000) but no service exists in compose. PDF generation for legal agreements will fail.
- PgBouncer: Referenced as default DB host (base.py:89 → HOST=pgbouncer) with CONN_MAX_AGE=0 configured for transaction pooling, but no PgBouncer service exists.
- Redis: Only 1 Redis container instead of 3 separate instances (sessions/broker/cache). DB namespace separation is used instead (DB 0/1/2/3) — acceptable for dev but violates the master execution plan's "split Redis instances to prevent noisy-neighbor contention" requirement.
H3 — No Backend Coverage Threshold Enforcement
Location: backend/pytest.ini  
Impact: The pytest.ini has no --cov flags, no --cov-fail-under=85 threshold. The AGENTS.md mandate of "≥85% backend coverage" is unenforceable in CI because coverage is never measured. The CI pipeline runs pytest without --cov.
H4 — No docker-compose.dev.yml Exists
Impact: The README references docker-compose.dev.yml but this file does not exist. Developers must set up infrastructure containers manually with infra/docker/docker-compose.yml.
H5 — Frontend Test Coverage Thin (<10% of total test code)
Location: frontend/tests/ and frontend/__tests__/  
Impact: Only 7 frontend test files (826 lines) vs ~34 backend test files (7,455 lines). No component tests for ground operations pages, sales wizard, compliance pages, or dog profile. The vitest threshold of 70% is unlikely to be met with current coverage.
H6 — Beat Schedule Defined Twice, Conflicting Configuration
Location: base.py:160-173 (seconds-based) and celery.py:16-33 (crontab-based)  
Impact: The Celery beat schedule is duplicated — base.py uses raw seconds (60*60*24) while celery.py uses precise crontab schedules. celery.py also has an additional lock-expired-submissions task not in base.py. This causes confusion about which schedule is authoritative.
---
MEDIUM-SEVERITY ISSUES (🟡 Remediate Progressively)
M1 — NParksSubmission LOCKED State Not Enforced at Model Level
Location: backend/apps/compliance/models.py:32-94  
The docstring says "immutable once locked" but there is no save() override to reject modifications. Compare with AuditLog and PDPAConsentLog which properly guard with raise ValueError(...).
M2 — GSTLedger Mutable via update_or_create()
Location: backend/apps/compliance/services/gst.py:198  
update_or_create() allows silent overwriting of ledger entries. Use get_or_create instead.
M3 — Shared Test Fixtures Reinvented Across Apps
Location: Every app's tests/factories.py  
Each app creates its own EntityFactory, UserFactory, DogFactory instead of sharing from a common conftest.py. This causes duplication and maintenance burden.
M4 — celery.py Hardcodes config.settings.production
Location: backend/config/celery.py:6  
Sets DJANGO_SETTINGS_MODULE = "config.settings.production" unconditionally, but the container compose uses config.settings.development. Could cause task routing issues in dev.
M5 — django-ratelimit==4.1.0 Listed Twice in base.txt
Location: backend/requirements/base.txt:10 and :58 — duplicate requirement.
M6 — No backup.sh Script for WAL-G PITR
Location: scripts/ directory is missing this file mentioned in the implementation plan.
M7 — Dog Profile Page Structural Tension
Location: frontend/app/(protected)/dogs/[id]/page.tsx  
The page is an async Server Component that imports useDog (a client hook). This works because getSession returns null on the server, but the pattern is fragile and could break with future React changes.
---
LOW-SEVERITY ITEMS
ID	Issue	Location
L1	postgres:17-trixie image — comment suggests postgres:17-alpine for consistency	docker-compose.yml:22
L2	init-scripts/ directory empty — no DB initialization scripts	infra/docker/init-scripts/
L3	Compliance test_gst.py and finance test_gst.py test same formula independently → duplication risk	2 files
L4	test_pdpa.py uses MockQuerySet instead of actual DB queries — may mask real issues	compliance/tests/test_pdpa.py
L5	No SESSION_COOKIE_NAME customization — uses default sessionid	base.py
---
THINGS THAT ARE EXCELLENT (Deserve Recognition)
Area	Assessment
BFF Proxy Hardening	Exemplary — path allowlisting, header stripping, path traversal protection, null byte injection blocking, CORS headers, streaming responses, Edge Runtime removal.
Idempotency Middleware	Exemplary — dedicated caches["idempotency"], SHA-256 fingerprinting, Redis SET NX atomic lock, 24h response caching, Idempotency-Replay header, 30s processing lock.
Cookie/HSTS/CSP Security	Exemplary — HttpOnly, Secure, SameSite=Lax, HSTS preload (1yr), X-Frame-Options DENY, SSL redirect, nosniff/XSS, proxy SSL header.
GST Compliance	Pass — 9/109 formula with ROUND_HALF_UP, Thomson=0% case-insensitive check, Decimal throughout, zero AI involvement.
AI Boundary	Pass — Zero AI/LLM imports anywhere in compliance, finance, or operations. ai_sandbox is properly isolated with no code.
AuditLog Immutability	Pass — save() and delete() properly raise ValueError, force_insert escape hatch for migrations.
COI Implementation	Pass — Wright's formula, closure table traversal, 5-generation depth, Redis cache (1h TTL), 13 tests with manual calculation validation.
PWA Service Worker	Pass — Cache-first for static, network-first for API, background sync registration, push notifications with severity levels, offline fallback page.
Offline Queue	Pass — Three-tier storage adapter (IDB → localStorage → Memory), auto-detection, migration from legacy, quota handling, atomic retry.
Entity Scoping	Pass — Permission-based queryset filtering, MANAGEMENT bypass, cross-entity tests in every domain app.
Middleware Order	Pass — Django's AuthenticationMiddleware at position 6, custom AuthenticationMiddleware at position 7. Matches AGENTS.md critical ordering mandate.
---
PHASE 0-8 COMPLETION VALIDATION MATRIX
Phase	Planned	Implemented	Assessment
0 — Infrastructure	24 files	24 files with gaps	Docker-compose missing Gotenberg/PgBouncer/Flower/3×Redis. CI pipeline exists and runs.
1 — Auth, BFF, RBAC	36 files	All present	BFF proxy exemplary. Middleware correct order. Auth flow via Redis sessions. RBAC tested. CSP inert.
2 — Domain Foundation	19 files	All present	12 models (Dog, Health, Vaccination, etc.). Importers, vaccine calc. Dog profile 7 tabs.
3 — Ground Ops + PWA	21 files	All present	7 log types, Draminski, SSE, PWA SW, offline queue. 30+ ground tests.
4 — Breeding Genetics	15 files	All present	5 models. COI + saturation. Celery closure rebuild (no triggers). Mate checker UI.
5 — Sales + AVS	12 files	All present	6 models. Agreement wizard. Gotenberg PDF configured but Gotenberg service missing.
6 — Compliance	8 files	All present	NParks Excel, GST calc, PDPA ConsentLog mutable properly. enforce_pdpa unused.
7 — Customers	7 files	All present	CRM, segmentation, blast engine, WA template cache, comms router.
8 — Finance	8 files	All present	P&L, GST reports, intercompany transfers, 19 tests all passing.
9 — Observability	6 files	Not started	OTel, k6 load tests, runbooks, Trivy scans marked backlog.
Overall: 89% planned coverage with implementation quality generally high. Gaps are concentrated in infrastructure config and PDPA enforcement.
---
IMMEDIATE ACTION ITEMS (Priority-Ordered)
1. Fix PDPA enforcement — Import enforce_pdpa() into all customer- and user-facing routers.
2. Fix breeding hook paths — Change /api/v1/breeding/mate-check/ → /breeding/mate-check/ in use-breeding.ts.
3. Install django-csp and add to INSTALLED_APPS and requirements/base.txt.
4. Write Playwright E2E tests for: login flow → BFF proxy → cookie validation → role redirect.
5. Replace all 19 force_login calls with session-based auth fixtures.
6. Add --cov=apps --cov-fail-under=85 to pytest.ini.
7. Add Gotenberg, PgBouncer, and split Redis services to production docker-compose.yml.
8. Add NParksSubmission LOCKED immutability guard (model-level save() override).
9. Replace update_or_create with get_or_create in GST ledger service.
10. Consolidate beat schedule into a single source of truth (celery.py via crontab).
