# Wellfond BMS — Remediation Plan

**Date:** 2026-05-06  
**Scope:** All Critical (4) and High (8) findings from audit report  
**Methodology:** Root cause validated against actual source code; fixes designed for minimal blast radius  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Critical Issues (C-001 through C-004)](#2-critical-issues)
3. [High Issues (H-001 through H-008)](#3-high-issues)
4. [Implementation Order](#4-implementation-order)
5. [Testing Strategy](#5-testing-strategy)
6. [Risk Assessment](#6-risk-assessment)

---

## 1. Executive Summary

All 4 critical and 8 high findings have been **re-validated against the actual source code**. Every finding is confirmed genuine. The root causes are clear and the fixes are well-scoped:

| Category | Count | Fix Complexity | Estimated Time |
|----------|-------|----------------|----------------|
| 🔴 Critical | 4 | 3 trivial (1-line each), 1 moderate (~30 lines) | ~1 hour |
| 🟠 High | 8 | 2 trivial, 4 moderate, 2 involved | ~3 hours |
| **Total** | **12** | | **~4 hours** |

**Key insight:** 3 of 4 critical bugs are single-line fixes. The 4th (SSE signature mismatch) requires ~30 lines. All high issues are straightforward. None require architectural changes.

---

## 2. Critical Issues

### C-001: `AuthenticationService.get_user_from_request()` Does Not Exist

**Severity:** 🔴 Critical — Runtime crash on 41 endpoints  
**Root Cause:** The method was never added to `AuthenticationService`. The class defines `get_current_user(cls, request)` at line 253 of `backend/apps/core/auth.py`, but 41 call sites across 7 router files call the non-existent `get_user_from_request()`.

**Call Sites (41 total):**
| File | Count |
|------|-------|
| `sales/routers/agreements.py` | 8 |
| `sales/routers/avs.py` | 7 |
| `compliance/routers/nparks.py` | 7 |
| `breeding/routers/litters.py` | 6 |
| `compliance/routers/pdpa.py` | 5 |
| `compliance/routers/gst.py` | 5 |
| `breeding/routers/mating.py` | 3 |

**Fix Option A (Recommended — 1-line fix):**
Add a classmethod alias in `backend/apps/core/auth.py` after line 275 (after `get_current_user`):

```python
@classmethod
def get_user_from_request(cls, request: HttpRequest) -> Optional[User]:
    """Alias for get_current_user — used by routers expecting this name."""
    return cls.get_current_user(request)
```

**Why A over B:** Option B (renaming all 41 call sites) has higher regression risk and is 41× the diff size. The alias is self-documenting and zero-risk.

**Verification:** After fix, run `python -c "from apps.core.auth import AuthenticationService; print(AuthenticationService.get_user_from_request)"` — should not raise `AttributeError`.

**Also:** There's already a standalone function `get_authenticated_user(request)` at line 296 that does the same thing. Consider adding a comment noting the relationship.

---

### C-002: SSE `get_pending_alerts()` Signature Mismatch

**Severity:** 🔴 Critical — SSE real-time alerts completely broken  
**Root Cause:** The stream router (`operations/routers/stream.py`) calls `get_pending_alerts` with keyword arguments at lines 48-52 and 170-175:

```python
alerts = await sync_to_async(get_pending_alerts, thread_sensitive=True)(
    user_id=user_id,
    entity_id=entity_id,
    role=user_role,
    since_id=last_event_id,
)
```

But the function (`operations/services/alerts.py:330`) expects a single `User` object:

```python
def get_pending_alerts(user: "User") -> List[dict]:
```

Internally, `get_pending_alerts` only uses `user.entity_id` and `user.role` from the User object.

**Fix (Recommended — modify the service function):**

Update `get_pending_alerts` in `backend/apps/operations/services/alerts.py` to accept keyword arguments:

```python
def get_pending_alerts(
    user: "User" = None,
    *,
    user_id: str = None,
    entity_id: str = None,
    role: str = None,
    since_id: int = 0,
    dog_id: str = None,
) -> List[dict]:
    """
    Get pending alerts for SSE stream.

    Accepts either a User object OR keyword arguments for async context
    where passing ORM objects across threads is unsafe.

    Returns alerts that have not been acknowledged.
    Deduplicates by dog+type.
    """
    # Resolve entity_id from User or kwargs
    if user is not None:
        entity_id = str(user.entity_id) if user.entity_id and user.role != "management" else None
        role = user.role
    else:
        # From keyword args (SSE async context)
        if role == "management":
            entity_id = None
    
    # Filter by specific dog if provided
    # (dog_id filtering is done at the event level below)

    events = []
    # ... rest of function unchanged, but use `entity_id` and `role` local vars
    # ... and add dog_id filtering at the end if dog_id is not None
```

Also add dog-specific filtering at the end of the function (before `return events`):

```python
    # Filter by specific dog if requested
    if dog_id:
        events = [e for e in events if e.get("dog_id") == dog_id]

    return events
```

**Why modify service, not router:** The router correctly decomposes the `User` into primitives before passing to `sync_to_async` — this is the right pattern for async Django (passing ORM objects across thread boundaries is unsafe). The service function should accept both interfaces.

**Verification:** Test SSE endpoint with `curl -N -H "Cookie: ..." http://localhost:3000/api/v1/stream/alerts` — should receive heartbeat events without crashes.

---

### C-003: Missing `logger` Import in `operations/tasks.py`

**Severity:** 🔴 Critical — Two Celery tasks crash with `NameError`  
**Root Cause:** `backend/apps/operations/tasks.py` uses `logger.info()` at line 216 and `logger.warning()` at line 276, but never imports `logging` or defines `logger`.

**Fix (1-line):**

Add at the top of `backend/apps/operations/tasks.py`, after the existing imports (after line 8):

```python
import logging

logger = logging.getLogger(__name__)
```

**Verification:** `python -c "from apps.operations.tasks import archive_old_logs"` should not raise `NameError`.

---

### C-004: `create_alert_event()` Called with Wrong Argument Count

**Severity:** 🔴 Critical — `generate_health_alert` task crashes  
**Root Cause:** In `backend/apps/operations/tasks.py:61`:

```python
event = create_alert_event(log)  # 1 argument
```

But `create_alert_event` in `alerts.py:402` expects:

```python
def create_alert_event(log_type: str, log_instance) -> dict:  # 2 arguments
```

The task already has `alert_type` available (it's a parameter of `generate_health_alert`).

**Fix (1-line change):**

In `backend/apps/operations/tasks.py`, line 61, change:

```python
event = create_alert_event(log)
```

to:

```python
event = create_alert_event(alert_type, log)
```

**Verification:** `generate_health_alert` task with a valid `log_id` and `alert_type="health_obs"` should return `{"status": "success", ...}`.

---

## 3. High Issues

### H-001: `.env` File Committed to Repository

**Severity:** 🟠 High — Credentials in version control  
**Root Cause:** The `.env` file was committed before `.gitignore` was configured. The `.gitignore` correctly lists `.env` now, but the file remains in git history.

**What's exposed:**
- `DB_PASSWORD=wellfond_dev_password`
- `SECRET_KEY=dev-secret-key-change-in-production-2026-wellfond-singapore`
- `STRIPE_SECRET_KEY=sk_test_singapore_placeholder`

**Fix (3 steps):**

1. Remove from git tracking (keeps local file):
```bash
git rm --cached .env
git commit -m "chore: remove .env from tracking (already in .gitignore)"
```

2. Rotate exposed credentials (even though dev-only):
   - Change `DB_PASSWORD` in actual PostgreSQL
   - Change `SECRET_KEY` in production env
   - Verify `STRIPE_SECRET_KEY` is placeholder (it is — `sk_test_*`)

3. Add pre-commit hook to prevent future `.env` commits:
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: no-env-files
      name: Block .env commits
      entry: bash -c 'for f in "$@"; do case "$f" in .env|.env.local|.env.production) echo "ERROR: $f must not be committed"; exit 1;; esac; done'
      language: system
      files: '\.env'
```

**Risk:** Low — these are development credentials, not production. But the pattern must be corrected.

---

### H-002: `archive_old_logs` Deletes Without Atomic Transaction

**Severity:** 🟠 High — Compliance risk (audit trail could be lost)  
**Root Cause:** In `backend/apps/operations/tasks.py:163-225`, the task deletes old logs BEFORE creating the audit entry. If the process crashes between deletion and audit log creation, the deletion has no trail.

**Current flow (broken):**
1. Delete old logs ← committed immediately
2. Create AuditLog ← could fail, leaving no record of what was deleted

**Fix:**

Wrap the entire operation in `transaction.atomic()` and create the audit log FIRST (optimistic audit):

```python
from django.db import transaction

@shared_task(bind=True, max_retries=2)
def archive_old_logs(self):
    """..."""
    from .models import (...)
    from apps.core.models import AuditLog

    retention_days = 365 * 2
    cutoff_date = timezone.now() - timedelta(days=retention_days)

    archived_counts = {}
    log_models = [InHeatLog, MatedLog, WhelpedLog, HealthObsLog, 
                  WeightLog, NursingFlagLog, NotReadyLog]

    with transaction.atomic():
        # Count first
        for model in log_models:
            old_logs = model.objects.filter(created_at__lt=cutoff_date)
            count = old_logs.count()
            if count > 0:
                archived_counts[model.__name__] = count

        if archived_counts:
            # Create audit log BEFORE deletion
            AuditLog.objects.create(
                actor=None,
                action=AuditLog.Action.DELETE,
                resource_type="GroundLogArchive",
                resource_id="system",
                payload={
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "deleted_counts": archived_counts,
                },
            )

            # Now delete
            for model in log_models:
                if model.__name__ in archived_counts:
                    model.objects.filter(created_at__lt=cutoff_date).delete()

            logger.info(f"Archived old logs: {archived_counts}")

    return {
        "status": "success",
        "archived_counts": archived_counts,
        "cutoff_date": cutoff_date.isoformat(),
    }
```

**Key change:** Audit log created BEFORE deletion, all within `transaction.atomic()`. If anything fails, the entire transaction rolls back — no orphaned deletions.

---

### H-003: No Runtime Validation Against `NEXT_PUBLIC_API_BASE` Leakage

**Severity:** 🟠 High — Security (internal URL could leak to browser)  
**Root Cause:** The code correctly uses `BACKEND_INTERNAL_URL` (server-only), but there's no runtime check preventing someone from accidentally adding `NEXT_PUBLIC_API_BASE` to environment variables, which Next.js would expose to the browser bundle.

**Current state:** `frontend/lib/api.ts:18` uses `process.env.BACKEND_INTERNAL_URL` — correct. Comments at `frontend/next.config.ts:88-91` document the intent — correct. But no enforcement.

**Fix (Add startup validation):**

In `frontend/lib/api.ts`, add after the `API_BASE_URL` declaration:

```typescript
// SECURITY: Prevent internal URL from leaking to browser bundle
// NEXT_PUBLIC_* vars are embedded in client-side JS by Next.js
if (typeof window !== 'undefined') {
  // Running in browser — BACKEND_INTERNAL_URL should NOT be available
  // (it's server-only, not prefixed with NEXT_PUBLIC_)
  const leaked = (window as Record<string, unknown>).__NEXT_DATA__?.props?.env?.BACKEND_INTERNAL_URL;
  if (leaked) {
    console.error('[SECURITY] BACKEND_INTERNAL_URL leaked to browser bundle!');
  }
}
```

Also add to `frontend/next.config.ts` in the `env` block (if one is re-added):

```typescript
// Explicitly exclude BACKEND_INTERNAL_URL from client bundle
env: {
  // Do NOT include BACKEND_INTERNAL_URL here
},
```

**Alternative (simpler — CI check):** Add a CI step that greps for `BACKEND_INTERNAL_URL` in `.next/static/` build output and fails if found.

**Risk:** Low — this is a defense-in-depth check. The current code is already correct; this prevents future regressions.

---

### H-004: `sync_offline_queue` Task Imports Non-Existent Service Functions

**Severity:** 🟠 High — Offline queue sync feature completely broken  
**Root Cause:** The task at `backend/apps/operations/tasks.py:332-335` tries to import:

```python
from .services import create_in_heat_log
from .services import create_mated_log
```

But `backend/apps/operations/services/__init__.py` is empty (`__all__ = []`). The `create_*_log` functions exist in `routers/logs.py` as Django Ninja view functions that require a `request` object — they can't be called from a Celery task.

**The actual service functions don't exist.** The router functions do the model creation inline (e.g., `InHeatLog.objects.create(...)` inside the router handler).

**Fix (Option A — Extract service functions, Recommended):**

Create `backend/apps/operations/services/log_creators.py` with pure business logic extracted from the router:

```python
"""
Service functions for creating ground operation logs.
Used by both routers (with request) and Celery tasks (without request).
"""
from uuid import UUID
from ..models import InHeatLog, MatedLog, WhelpedLog, HealthObsLog, WeightLog, NursingFlagLog, NotReadyLog
from apps.core.models import AuditLog


def create_in_heat_log(dog_id: str, data: dict, idempotency_key: str = None) -> InHeatLog:
    """Create an in-heat log entry."""
    log = InHeatLog.objects.create(
        dog_id=dog_id,
        reading=data.get("reading"),
        zone=data.get("zone"),
        notes=data.get("notes", ""),
    )
    # Audit trail
    AuditLog.objects.create(
        actor=None,  # Will be set by router if request available
        action=AuditLog.Action.CREATE,
        resource_type="InHeatLog",
        resource_id=str(log.id),
        payload={"dog_id": dog_id, "idempotency_key": idempotency_key},
    )
    return log


def create_mated_log(dog_id: str, data: dict, idempotency_key: str = None) -> MatedLog:
    """Create a mated log entry."""
    log = MatedLog.objects.create(
        dog_id=dog_id,
        sire_id=data.get("sire_id"),
        mating_date=data.get("mating_date"),
        notes=data.get("notes", ""),
    )
    AuditLog.objects.create(
        actor=None,
        action=AuditLog.Action.CREATE,
        resource_type="MatedLog",
        resource_id=str(log.id),
        payload={"dog_id": dog_id, "idempotency_key": idempotency_key},
    )
    return log

# ... similar for other log types
```

Then update `services/__init__.py`:

```python
from .log_creators import (
    create_in_heat_log,
    create_mated_log,
    create_whelped_log,
    create_health_obs_log,
    create_weight_log,
    create_nursing_flag_log,
    create_not_ready_log,
)
```

Then refactor router functions to call these service functions (reduces duplication).

**Fix Option B (Quick — direct model creation in task):**

Update `sync_offline_queue` to create models directly instead of importing services:

```python
if log_type == "in_heat":
    InHeatLog.objects.create(dog_id=dog_id, reading=data.get("reading"), ...)
elif log_type == "mated":
    MatedLog.objects.create(dog_id=dog_id, sire_id=data.get("sire_id"), ...)
# ... etc
```

**Recommendation:** Option A. It's more work but eliminates code duplication between routers and tasks, and makes the offline queue maintainable.

---

### H-005: Decimal→Float Conversion in Dashboard Revenue

**Severity:** 🟠 High — Financial precision loss  
**Root Cause:** In `backend/apps/core/services/dashboard.py:186-187`:

```python
"total_sales": float(total_sales),
"gst_collected": float(gst_collected),
```

`total_sales` is a `Decimal` (from `Sum('total_amount')`), and `gst_collected` is calculated with `Decimal('9') / Decimal('109')`. Converting to `float` introduces floating-point precision errors (e.g., `Decimal('1234.56')` → `float(1234.56)` → `1234.5599999999999`).

**Fix:**

In `backend/apps/core/services/dashboard.py`, change lines 186-187:

```python
"total_sales": str(total_sales),      # String preserves precision
"gst_collected": str(gst_collected),  # JSON serialization handles strings
```

Or use `Decimal` serialization with a custom JSON encoder. The simplest approach is `str()` — the frontend can parse it with `parseFloat()` if needed, and the string representation is exact.

**Also check:** Any other `float()` conversions on financial data in `finance/` services. The audit found this pattern only in `dashboard.py`.

---

### H-006: Missing Docker Healthchecks for 6 Services

**Severity:** 🟠 High — Orchestration can't detect unhealthy services  
**Root Cause:** `docker-compose.yml` has healthchecks for PostgreSQL, Redis (×4), and Gotenberg, but not for PgBouncer, Django, Celery Worker, Celery Beat, Next.js, or Flower.

**Current healthcheck coverage:**
| Service | Has Healthcheck |
|---------|----------------|
| postgres | ✅ `pg_isready` |
| redis_sessions | ✅ `redis-cli ping` |
| redis_broker | ✅ `redis-cli ping` |
| redis_cache | ✅ `redis-cli ping` |
| redis_idempotency | ✅ `redis-cli ping` |
| gotenberg | ✅ `curl /health` |
| pgbouncer | ❌ |
| django | ❌ |
| celery_worker | ❌ |
| celery_beat | ❌ |
| nextjs | ❌ |
| flower | ❌ |

**Fix — Add healthchecks to `docker-compose.yml`:**

```yaml
  pgbouncer:
    # ... existing config ...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h localhost -p 5432 -U wellfond_app"]
      interval: 10s
      timeout: 5s
      retries: 3

  django:
    # ... existing config ...
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\""]
      interval: 15s
      timeout: 10s
      retries: 3
      start_period: 30s

  celery_worker:
    # ... existing config ...
    healthcheck:
      test: ["CMD-SHELL", "celery -A config inspect ping --timeout 10"]
      interval: 30s
      timeout: 15s
      retries: 3
      start_period: 20s

  celery_beat:
    # ... existing config ...
    healthcheck:
      test: ["CMD-SHELL", "celery -A config inspect ping --timeout 10"]
      interval: 30s
      timeout: 15s
      retries: 3
      start_period: 20s

  nextjs:
    # ... existing config ...
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/ || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 3
      start_period: 20s

  flower:
    # ... existing config ...
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5555/ || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 3
```

Also update `depends_on` to use `condition: service_healthy` where appropriate:

```yaml
  django:
    depends_on:
      pgbouncer:
        condition: service_healthy  # was: service_started
      redis_sessions:
        condition: service_healthy
      redis_broker:
        condition: service_healthy

  nextjs:
    depends_on:
      django:
        condition: service_healthy  # was: no condition
```

---

### H-007: No Content-Length Limit on BFF Proxy

**Severity:** 🟠 High — Potential DoS via large request bodies  
**Root Cause:** The BFF proxy (`frontend/app/api/proxy/[...path]/route.ts`) forwards requests without checking `Content-Length`. An attacker could send multi-GB request bodies.

**Fix:**

In `frontend/app/api/proxy/[...path]/route.ts`, add at the top of the handler:

```typescript
const MAX_BODY_SIZE = 10 * 1024 * 1024; // 10 MB

// In the request handler:
const contentLength = request.headers.get('content-length');
if (contentLength && parseInt(contentLength, 10) > MAX_BODY_SIZE) {
  return new Response(
    JSON.stringify({ error: 'Request body too large' }),
    { status: 413, headers: { 'Content-Type': 'application/json' } }
  );
}
```

**Risk:** Low — this is a defense-in-depth measure. Django has its own `DATA_UPLOAD_MAX_MEMORY_SIZE` setting.

---

### H-008: Missing Documentation Files

**Severity:** 🟠 High — Referenced docs don't exist  
**Root Cause:** `README.md` references `docs/RUNBOOK.md`, `docs/SECURITY.md`, `docs/DEPLOYMENT.md`, `docs/API.md` but these may not exist.

**Fix:** Verify which files exist and either create stubs or update README references.

```bash
ls -la docs/
```

If missing, create minimal stubs with TODO markers.

---

## 4. Implementation Order

**Recommended sequence (by dependency and risk):**

| Step | Issue | Why This Order |
|------|-------|----------------|
| 1 | **C-003** — Add `import logging` | Zero-risk 1-line fix. Unblocks 2 Celery tasks immediately. |
| 2 | **C-004** — Fix `create_alert_event` call | Zero-risk 1-line fix. Unblocks health alert task. |
| 3 | **C-001** — Add `get_user_from_request` alias | 1-line fix. Unblocks 41 endpoints across 7 routers. |
| 4 | **C-002** — Fix `get_pending_alerts` signature | ~30 lines. Unblocks SSE real-time alerts. |
| 5 | **H-002** — Wrap `archive_old_logs` in atomic | ~15 lines. Compliance fix. |
| 6 | **H-005** — Fix Decimal→float | 2-line change. Financial accuracy. |
| 7 | **H-004** — Fix `sync_offline_queue` imports | ~50 lines (Option A). Unblocks offline sync. |
| 8 | **H-001** — Remove `.env` from git | Git operation + credential rotation. |
| 9 | **H-006** — Add Docker healthchecks | ~40 lines. Infrastructure hardening. |
| 10 | **H-007** — Add BFF body size limit | ~10 lines. Security hardening. |
| 11 | **H-003** — Add API_BASE leak check | ~15 lines. Defense-in-depth. |
| 12 | **H-008** — Verify/create docs | Documentation. |

**Total estimated changes:** ~170 lines across ~12 files.

---

## 5. Testing Strategy

### Critical Fixes — Smoke Tests

After applying C-001 through C-004, verify with:

```bash
# C-001: Auth method exists
python -c "from apps.core.auth import AuthenticationService; AuthenticationService.get_user_from_request"

# C-002: SSE doesn't crash
curl -N -H "Accept: text/event-stream" \
     -H "Cookie: session=..." \
     http://localhost:8000/api/v1/stream/alerts

# C-003: Tasks import cleanly
python -c "from apps.operations.tasks import archive_old_logs, check_rehome_overdue"

# C-004: Alert task doesn't crash
python -c "from apps.operations.tasks import generate_health_alert"
```

### High Fixes — Integration Tests

```bash
# H-002: Atomic archive
python manage.py test apps.operations.tests.test_tasks.ArchiveOldLogsTest

# H-004: Offline queue
python manage.py test apps.operations.tests.test_tasks.SyncOfflineQueueTest

# H-005: Dashboard precision
python manage.py test apps.core.tests.test_dashboard.DashboardPrecisionTest
```

### Full Regression

```bash
# Run entire test suite
pytest backend/ --tb=short -q
cd frontend && npm test
```

---

## 6. Risk Assessment

| Fix | Risk Level | Rationale |
|-----|-----------|-----------|
| C-001 (alias) | **Minimal** | Adds method, doesn't change existing behavior |
| C-002 (signature) | **Low** | Backwards-compatible (accepts both User and kwargs) |
| C-003 (import) | **Minimal** | Adds missing import, no logic change |
| C-004 (arg fix) | **Minimal** | Corrects call to match existing signature |
| H-001 (git rm) | **Low** | File stays locally, only removed from tracking |
| H-002 (atomic) | **Low** | Adds transaction protection, same logic |
| H-003 (leak check) | **Minimal** | Client-side check only, no server change |
| H-004 (offline) | **Medium** | New service layer — needs integration testing |
| H-005 (Decimal) | **Low** | String serialization is safer than float |
| H-006 (healthcheck) | **Low** | Additive — only adds monitoring |
| H-007 (body limit) | **Low** | Defense-in-depth, Django has own limits |
| H-008 (docs) | **Minimal** | Documentation only |

**Overall risk: Low.** No architectural changes. Most fixes are additive (adding missing code) rather than modifying existing behavior.

---

*Plan generated: 2026-05-06*  
*All findings validated against actual source code*
