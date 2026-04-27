# Wellfond BMS — Codebase Assessment Report v1.0

**Date:** April 28, 2026 | **Health Score: 72/100**

## Executive Summary

Strong implementation of Phases 0-4. 3 Critical, 5 High, 12 Medium, 10 Low findings.
Remediation required before Phase 5.

---

## Critical Findings (Must Fix Before Phase 5)

### CRIT-001: Duplicate NinjaAPI Instances
- `backend/api.py` (89 lines) — orphaned, unused duplicate  
- `backend/api/__init__.py` (66 lines) — master instance, used by url config
- **Fix:** Delete backend/api.py

### CRIT-002: Settings Module Path Mismatch
- `.env.example` says `wellfond.settings.development` (doesn't exist)
- Actual path: `config.settings.development`
- **Fix:** Update DJANGO_SETTINGS_MODULE in .env.example

### CRIT-003: Missing Dashboard Page — 404 on Homepage
- next.config.ts redirects `/` -> `/dashboard`
- `app/(protected)/dashboard/page.tsx` does NOT exist
- **Fix:** Create dashboard page placeholder immediately

---

## High-Severity Findings

### HIGH-001: Empty Stub Apps in INSTALLED_APPS
5 apps (sales, compliance, customers, finance, ai_sandbox) are registered but empty.
- **Fix:** Remove from INSTALLED_APPS until implemented, or add NotImplemented safeguards

### HIGH-002: CHA YUAN Legacy Contamination
- `infra/docker/pg_hba.conf` — chayuan_db entries
- `backend/.env.example` — entirely CHA YUAN branded
- **Fix:** Remove CHA YUAN references; delete backend/.env.example

### HIGH-003: Missing use-auth.ts Hook
Plan specifies hooks/use-auth.ts. Auth logic is in lib/auth.ts (not React-aware).
- **Fix:** Create use-auth.ts wrapper with React hooks (useCurrentUser, useLogin, useLogout)

### HIGH-004: Missing lib/offline-queue.ts Module
Plan specifies dedicated IndexedDB module. Offline queue absorbed into React hook.
- **Fix:** Extract framework-agnostic queueLog/flushQueue into lib/offline-queue.ts

### HIGH-005: Test File Location Split
Tests in both /tests/ (root) and backend/apps/*/tests/. Different configs.
- **Fix:** Consolidate all Django tests into backend/apps/*/tests/

---

## Medium-Severity Findings

| ID | Finding | Fix |
|----|---------|-----|
| MED-001 | HealthObsLog lacks temp/weight validation ranges | Add validators matching HealthRecord |
| MED-002 | Vaccination.save() swallows ImportError silently | Add logger.warning() |
| MED-003 | Draminski DEFAULT_BASELINE=250 vs plan's 300 | Standardize value; make configurable |
| MED-004 | No frontend unit tests | Write vitest tests for critical hooks |
| MED-005 | No Playwright E2E tests | Write login+dog list+log submission E2E |
| MED-006 | log-form.tsx missing — 7 pages duplicate form logic | Extract shared log-form component |
| MED-007 | mate-check-form.tsx at 479 lines (largest component) | Split into 5 sub-components |
| MED-008 | camera-scan.tsx at 375 lines (monolithic) | Split camera/barcode/file modules |
| MED-009 | Production docker-compose.yml (11 services) missing | Create before production deployment |
| MED-010 | docs/RUNBOOK,SECURITY,DEPLOYMENT,API missing | Create minimum versions |
| MED-011 | TODO.md stale (all phases unchecked) | Update or deprecate |
| MED-012 | No .editorconfig or .prettierrc | Add formatting config |

---

## Low-Severity Findings

- SECRET_KEY has hardcoded dev fallback — add assertion for production
- require_admin_debug uses print(sys.stderr) — replace with logger.debug()
- AuditLog.payload lacks Pydantic schema validation
- DogPhoto.customer_visible may be frontend-only filter
- scope_entity_for_list() entity_param missing cross-entity validation
- version: "3.9" deprecated in Docker Compose spec

---

## Gap Analysis: Plan vs Implementation

| Phase | Planned Files | Delivered | Key Gaps |
|-------|--------------|-----------|----------|
| 0 | 24 files, 11-service compose | 5 files, 2-service compose | No prod compose, no PgBouncer/Gotenberg/Flower |
| 1 | 36 files | 30 files | use-auth.ts, progress.tsx, chart.tsx, dropdown-menu missing |
| 2 | 19 files | 18 files | Litters import is placeholder |
| 3 | 21 files | 18 files | log-form.tsx, lib/offline-queue.ts, SW path mismatch |
| 4 | 20 files | 20 files | Complete |
| 5-9 | — | Stubs only | Not started |

---

## Codebase Statistics

- **Backend:** 12,500+ LOC, 20 models, 37+ endpoints, 4 schema files, 5 service files  
- **Frontend:** 6,000+ LOC, 14 UI components, 12 ground components, 3 breeding components  
- **Tests:** 13 test files, ~172+ test methods  
- **Apps Completed:** core, operations, breeding  
- **Apps Stubbed:** sales, compliance, customers, finance, ai_sandbox  

---

## Strengths

1. BFF Proxy is well-implemented (header stripping, path allowlisting, streaming)
2. Entity scoping is thorough (queryset + middleware + permissions)
3. TDD adherence is strong (172+ tests, zone casing fix, idempotency validation)
4. Compliance boundaries respected (zero AI in compliance, deterministic COI/saturation)
5. TypeScript strict mode (0 errors, no any usage)
6. CI/CD comprehensive (backend, frontend, infra, E2E jobs with Trivy scanning)

---

## Weaknesses

1. Documentation drift (TODO stale, 4 planned docs missing, inconsistent metrics)
2. No frontend test coverage (zero vitest/playwright tests)
3. Code duplication (duplicate api.py, 7 repeated log patterns, large components)
4. Legacy brand contamination (CHA YUAN in active config files)
5. Missing production infrastructure (no 11-service compose)

---

## Root Cause Analysis

Most issues stem from:
1. Evolution from CHA YUAN template — legacy residue from original scaffold
2. Rapid sequential phase delivery (4 phases in 7 days) — docs didn't keep pace
3. Pragmatic path choices over plan-specified locations

---

## Phase 5 Readiness Recommendations

1. **BLOCKER:** Fix CRIT-001, CRIT-002, CRIT-003 before any new work
2. **Before Phase 5:** Fix HIGH-001 through HIGH-005
3. **During Phase 5:** Write minimum vitest/playwright tests as acceptance criteria
4. **Continuous:** Standardize test locations, update stale documentation
5. **Defer to Phase 9:** Production compose and ops documentation

---

*Report based on exhaustive codebase exploration cross-referenced against 7 planning documents.*
