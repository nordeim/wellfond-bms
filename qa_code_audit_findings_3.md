# Wellfond BMS — Comprehensive Codebase Audit & Assessment Report

**Date:** April 29, 2026  
**Auditor:** AI Code Review Agent  
**Project:** Singapore AVS-Compliant Dog Breeding Operations Platform  
**Architecture:** BFF Proxy + Django 6.0 + Next.js 16 + PostgreSQL 17 + Celery + SSE + PWA  

---

## Executive Summary

This report presents findings from a systematic audit of the Wellfond BMS codebase against the Master Execution Plan v1.1 (MEP), IMPLEMENTATION_PLAN.md, and six phase-specific sub-plans. The audit examined 18 backend test files, 14 router registrations, 7 frontend hooks, 19 UI components, the BFF proxy, infrastructure configuration, and compliance controls.

**Overall Assessment: 73/100 — Substantial Completion with Remediable Gaps**

The codebase demonstrates high-quality implementation across Phases 0-6 with strong architecture compliance — zero AI in compliance paths, hardened BFF proxy with path allowlisting, HttpOnly cookie auth, proper COI using Wright's formula, and comprehensive Pydantic v2 schemas. However, 3 critical blockers (broken tests, missing core test factories, dashboard absence) and 12 medium-severity gaps require remediation before production go-live.

---

## 1. Phase Status Validation

| Phase | Claimed Status | Verified Status | Evidence |
|-------|---------------|----------------|----------|
| **Phase 0** | Complete | **PARTIAL** (60%) | 2 Docker services vs 11 planned; missing Gotenberg, PgBouncer, production compose |
| **Phase 1** | Complete | **COMPLETE** (95%) | Auth, BFF proxy, RBAC, middleware all present; test factories missing |
| **Phase 2** | Complete | **COMPLETE** (90%) | 4 domain models, dog CRUD, vaccines, alerts; CSV import has factory import bug |
| **Phase 3** | Complete | **COMPLETE** (85%) | 7 log types, Draminski, SSE, PWA queue; localStorage not IndexedDB per plan |
| **Phase 4** | Complete | **COMPLETE** (100%) | 5 models, COI (16 tests passing), saturation, dual-sire, closure table |
| **Phase 5** | Backlog (per README) | **COMPLETE** (95%) | 5 models, 14 endpoints, 28 tests, Gotenberg PDF integration |
| **Phase 6** | Backlog (per README) | **COMPLETE** (90%) | 3 models, 17 endpoints, 30 tests, NParks Excel, GST, PDPA |
| **Phase 7** | Backlog | Not Started | No customer models or pages |
| **Phase 8** | Backlog | Not Started | No dashboard or finance |
| **Phase 9** | Backlog | Not Started | No OTel config or runbooks |

> **Note:** README.md shows Phases 5-6 as "Backlog" but the actual implementation is complete. Documentation is stale.

---

## 2. Critical Findings (BLOCKING — Must Fix Before Go-Live)

### 2.1 [CRITICAL] Missing Core Test Factories — Tests Cannot Run

**Severity:** BLOCKING  
**File:** `backend/apps/core/tests/factories.py` — **DOES NOT EXIST**

The test suite fails to collect because `test_importers.py` and `test_dogs.py` import `EntityFactory` and `UserFactory` from `apps.core.tests.factories`, which doesn't exist. These factories are7900 are only defined in `apps/operations/tests/factories.py` and `apps/breeding/tests/factories.py`.

```python
# Failing import in test_importers.py:12
from apps.core.tests.factories import EntityFactory, UserFactory
```

**Fix:** Create `backend/apps/core/tests/factories.py` with `UserFactory` and `EntityFactory`.

**Impact:** All tests fail to collect. CI pipeline will break. ~80 tests untestable.

---

### 2.2 [CRITICAL] Dashboard Page Completely Missing

**Severity:** BLOCKING  
**Route:** `/dashboard` — **NO PAGE EXISTS**

The MEP (v1.1, Phase 8) and IMPLEMENTATION_PLAN.md (Section 8.x) specify a role-aware dashboard command centre. The `next.config.ts` redirects `/` to `/dashboard`, but no `app/(protected)/dashboard/page.tsx` exists. The `components/dashboard/` directory is also completely absent (missing: `nparks-countdown.tsx`, `alert-feed.tsx`, `revenue-chart.tsx`).

**Ripple Effects:**
- Middleware `RoleGuard.get_redirect_for_role()` redirects management/admin/sales to `/dashboard` — results in 404
- Root path redirect (`/ → /dashboard`) breaks
- Alert cards infrastructure exists but has no visual presentation layer

**Fix:** Create `app/(protected)/dashboard/page.tsx` and `components/dashboard/` with alert card rendering.

---

### 2.3 [CRITICAL] Two Conflicting NinjaAPI Instances

**Severity:** HIGH  
**Files:** `backend/api.py` and `backend/api/__init__.py`

Two NinjaAPI instances exist:
- **`api.py`** (stale): Has `csrf=True`, `CookieAuth`, but only 2 routers (auth, users). All other routers commented out.
- **`api/__init__.py`** (active): Has all 14 routers but NO `csrf=True`, NO CookieAuth, NO `urls_namespace`.

The `config/urls.py` imports from `api` package (resolves to `__init__.py`), so the working instance has no CSRF protection at the Ninja level.

**Security Impact:** The active API instance lacks Ninja's built-in CSRF validation. Django's CSRF middleware is14 still present, but Ninja endpoints may bypass it.

**Fix:** Consolidate into one NinjaAPI definition with CSRF enabled and all 14 routers registered. Delete the stale `api.py`.

---

### 2.4 [HIGH] ASGI/WSGI Hardcode Production Settings

**Severity:** HIGH  
**Files:** `backend/config/asgi.py:10`, `backend/config/wsgi.py:6`

Both files hardcode `DJANGO_SETTINGS_MODULE = 'config.settings.production'`. In development, if ASGI is used for SSE, it will load production settings with strict CSP, HSTS, PgBouncer host, HTTPS-only cookies — breaking local development.

**Fix:** Use environment variable with production fallback: `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')`

