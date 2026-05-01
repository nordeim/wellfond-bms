# Wellfond BMS — Corrected Remediation Plan v2

**Date:** 2026-05-01
**Based on:** Systematic re-validation of `code_audit_new_summary.md` against source
**Scope:** 3 Critical + 10 High issues — all re-validated at file:line level
**Status:** READY FOR EXECUTION

---

## Re-Validation Summary

Every issue below was confirmed by reading the actual source code with exact
file:line references. Five corrections to the original remediation plan are
documented in Section 4.

| ID | Severity | File:Line | Root Cause |
|----|----------|-----------|------------|
| C1 | CRITICAL | `nparks.py:272` | `AgreementLineItem` missing `line_total` property |
| C2 | CRITICAL | `nparks.py:340` | `HealthRecord` missing `follow_up_required` field |
| C3 | CRITICAL | `offline-queue.ts` | Root uses localStorage; IndexedDB module unused |
| H1 | HIGH | `middleware.py:73-90` | `get()` then `set()` is non-atomic TOCTOU |
| H2 | HIGH | `agreement.py:588-599` | `agreement.status` read after `.save()` wrote CANCELLED |
| H3 | HIGH | `pdpa.py:109,138` | Placeholder stubs; Customer model with pdpa_consent exists |
| H4 | HIGH | `route.ts:208-211` | `Allow-Origin: *` + `Allow-Credentials: true` |
| H5 | HIGH | `auth.py:18,55` | `SessionManager` uses default `cache`, not `caches["sessions"]` |
| H6 | HIGH | `logs.py:479-558` | 7 queries, per-type limits, Python-side merge |
| H7 | HIGH | `logs.py:109` | `raise HttpError(200, ...)` — API contract violation |
| H8 | HIGH | `agreement.py:625-626` | Same root cause as C1 |
| H9 | HIGH | `operations/models.py:282-286` | Silent `except ImportError: pass` (vaccine.py exists) |
| H10 | HIGH | `finance/models.py:155-177` | Two creates outside `transaction.atomic()` |

---

## Issue C1 + H8: `AgreementLineItem` Missing `line_total` and `gst_amount`

### Root Cause (Confirmed)

`backend/apps/sales/models.py:169-211` — `AgreementLineItem` has `price` and
`gst_component` fields but no `line_total` or `gst_amount` properties.

**Callers that will crash:**
- `backend/apps/compliance/services/nparks.py:272` — `float(item.line_total)`
- `backend/apps/sales/services/agreement.py:625` — `subtotal += item.line_total`
- `backend/apps/sales/services/agreement.py:626` — `gst_amount += item.gst_amount`

The test factory (`backend/apps/sales/tests/factories.py:78-83`) defines these as
`@factory.lazy_attribute`, which only makes them available to factory-created
instances, not real model instances.

### Fix

Add two `@property` methods to `AgreementLineItem`:

```python
# backend/apps/sales/models.py — add to AgreementLineItem class

@property
def line_total(self) -> Decimal:
    """Total amount for this line item (price excluding GST)."""
    return self.price

@property
def gst_amount(self) -> Decimal:
    """GST component for this line item."""
    return self.gst_component
```

### Verification

```python
item = AgreementLineItem.objects.create(
    agreement=agreement, dog=dog, price=Decimal("1000.00"),
    gst_component=Decimal("90.00"),
)
assert item.line_total == Decimal("1000.00")
assert item.gst_amount == Decimal("90.00")
```

**Effort:** 5 min | **Risk:** None (additive)

---

## Issue C2: `HealthRecord` Missing `follow_up_required` Field

### Root Cause (Confirmed)

`backend/apps/compliance/services/nparks.py:340`:
```python
ws.cell(row=row, column=9, value="Yes" if record.follow_up_required else "No")
```

`backend/apps/operations/models.py:159-221` — `HealthRecord` has no
`follow_up_required` field.

### Fix

**Step 1:** Add field to `HealthRecord` model (`operations/models.py` after `vet_name`):

```python
class HealthRecord(models.Model):
    # ... existing fields ...

    vet_name = models.CharField(max_length=100, blank=True)

    # NParks compliance tracking
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up veterinary treatment is required",
    )
    follow_up_date = models.DateField(
        null=True, blank=True,
        help_text="Scheduled follow-up date",
    )
```

**Step 2:** Generate migration:
```bash
cd backend && python manage.py makemigrations operations --name add_follow_up_to_health_record
python manage.py migrate
```

**Effort:** 10 min | **Risk:** None (additive, default=False)

---

## Issue C3: Root `offline-queue.ts` Uses `localStorage`, IndexedDB Impl Exists But Unused

### Root Cause (Confirmed)

**Current state (READ BEFORE FIXING):**

| File | API |
|------|-----|
| `lib/offline-queue.ts` (root) | **Sync** functions |
| `lib/offline-queue/index.ts` | **Async** functions (proper impl) |
| `lib/offline-queue/db.ts` | IndexedDB connection + migration |
| `lib/offline-queue/adapter.idb.ts` | IndexedDB storage adapter |
| `lib/offline-queue/adapter.ls.ts` | localStorage fallback |
| `lib/offline-queue/adapter.memory.ts` | In-memory fallback |

**The critical mismatch:** The root `lib/offline-queue.ts` exports
**synchronous** functions (`getQueue()`, `addToQueue()`, etc). The proper
`lib/offline-queue/index.ts` exports **asynchronous** functions (all return
`Promise`). Simply re-exporting — as the original plan proposed — **will
break every consumer**:

`frontend/hooks/use-offline-queue.ts:21`:
```typescript
const [queue, setQueue] = useState<OfflineQueueItem[]>(getQueue());
// TypeError! getQueue() returns Promise<OfflineQueueItem[]>, not array
```

Seven ground pages import `useOfflineQueue` — all would crash.

**Note:** The Service Worker (`public/sw.js:154`) calls
`/api/proxy/sync-offline` — it does not access the offline queue directly. The
"SW can't access localStorage" reasoning is technically true but irrelevant.
The real problem is the sync/async API mismatch.

### Fix (Three Steps)

**Step 1: Update `use-offline-queue.ts` for async API:**

Replace synchronous `useState(getQueue())` with `useEffect` + loading state:

```typescript
"use client";
import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import type { OfflineQueueItem } from "@/lib/offline-queue";
import {
  getQueue, addToQueue, removeFromQueue, getQueueCount, incrementRetry,
} from "@/lib/offline-queue";

export function useOfflineQueue() {
  // ...
  // FIXED: async load
  const [queue, setQueue] = useState<OfflineQueueItem[]>([]);
  const [queueLoaded, setQueueLoaded] = useState(false);

  useEffect(() => {
    getQueue().then((items) => {
      setQueue(items);
      setQueueLoaded(true);
    });
  }, []);

  const processQueue = useCallback(async () => {
    if (isProcessing || !navigator.onLine) return;
    const currentQueue = await getQueue(); // await added
    // ...
  }, [isProcessing, toast]);

  return { isOnline, queue, queueLoaded, queueLength: getQueueCount(),
           isProcessing, queueRequest, processQueue };
}
```

**Step 2: Replace `lib/offline-queue.ts` with re-exports** (only AFTER Step 1):

```typescript
// lib/offline-queue.ts
export {
  getQueue, addToQueue, removeFromQueue, getQueueCount,
  clearQueue, incrementRetry, resetAdapter, getAdapterName,
  getQueueSync, addToQueueSync,
} from './offline-queue/index';

export type { OfflineQueueItem, OfflineQueueItemCreate } from './offline-queue/types';
export { default } from './offline-queue/index';
```

**Step 3: Update 7 ground pages** to destructure `queueLoaded` and show loading state.

**Verification:**
1. Open app — queue loads (no TypeError)
2. Go offline (DevTools > Network > Offline)
3. Submit a ground log
4. Verify item appears in IndexedDB (`wellfond-offline-queue`)
5. Go online — verify sync succeeds

**Effort:** 30 min | **Risk:** Medium — touches hook + 7 pages

---

## Issue H1: Idempotency Middleware TOCTOU Race

### Root Cause (Confirmed)

`backend/apps/core/middleware.py:73-96` — non-atomic `get()` check then `set()`
after processing. Two concurrent requests with the same key both pass `get()`.

### Fix

Use `cache.add()` (Django equivalent of Redis `SET NX`):

```python
# middleware.py — in __call__, replace lines 69-96

fingerprint = self._generate_fingerprint(request, idempotency_key)
idempotency_cache = caches["idempotency"]

# Fast path: completed response
cached = idempotency_cache.get(fingerprint)
if cached and cached.get("status") != "processing":
    resp = JsonResponse(cached["data"], status=cached["status"])
    resp["Idempotency-Replay"] = "true"
    return resp

# Atomic lock: cache.add() = SET NX — False if key exists
if not idempotency_cache.add(fingerprint, {"status": "processing"}, timeout=30):
    cached = idempotency_cache.get(fingerprint)
    if cached and cached.get("status") != "processing":
        resp = JsonResponse(cached["data"], status=cached["status"])
        resp["Idempotency-Replay"] = "true"
        return resp
    return JsonResponse({"error": "Request already in progress"}, status=409)

# Hold lock — process
response = self.get_response(request)

if 200 <= response.status_code < 300:
    try:
        idempotency_cache.set(
            fingerprint,
            {"data": json.loads(response.content), "status": response.status_code},
            timeout=86400,
        )
    except json.JSONDecodeError:
        pass
else:
    idempotency_cache.delete(fingerprint)

return response
```

**Effort:** 15 min | **Risk:** Low

---

## Issue H2: `cancel_agreement` Audit Log Records Wrong `old_status`

### Root Cause (Confirmed)

`backend/apps/sales/services/agreement.py:588-599` — `agreement.status` set to
CANCELLED at line 590, saved at line 592, then READ at line 599 for audit log.
The audit records CANCELLED -> CANCELLED instead of DRAFT -> CANCELLED.

### Fix

Capture before mutation:

```python
def cancel_agreement(agreement_id, cancelled_by, reason=""):
    # ...
    # CAPTURE state before mutation
    old_status = agreement.status

    with transaction.atomic():
        agreement.status = AgreementStatus.CANCELLED
        agreement.cancelled_at = timezone.now()
        agreement.save(update_fields=["status", "cancelled_at", "updated_at"])

        AuditLog.objects.create(
            actor=cancelled_by,
            action=AuditLog.Action.UPDATE,
            resource_type="SalesAgreement",
            resource_id=str(agreement_id),
            payload={
                "old_status": old_status,              # captured before save
                "new_status": AgreementStatus.CANCELLED,
                "reason": reason,
            },
        )
```

**Effort:** 2 min | **Risk:** None

---

## Issue H3: PDPA Placeholder Stubs — Compliance Gap

### Root Cause (Confirmed)

`backend/apps/compliance/services/pdpa.py:109` — `check_blast_eligibility`
returns ALL customers as eligible. `pdpa.py:138` — `is_consented` returns `True`.

BUT: `backend/apps/customers/models.py:69` — `Customer` model EXISTS with
`pdpa_consent = models.BooleanField(default=False)`. Phase 7 is complete.

### Fix

Replace all four placeholder methods:

```python
@staticmethod
def check_blast_eligibility(customer_ids: list[UUID]) -> PDPAConsentCheckResponse:
    from apps.customers.models import Customer
    customers = Customer.objects.filter(id__in=customer_ids)
    eligible_ids = [c.id for c in customers if c.pdpa_consent]
    excluded_ids = [c.id for c in customers if not c.pdpa_consent]
    return PDPAConsentCheckResponse(
        eligible_ids=eligible_ids, excluded_ids=excluded_ids,
        eligible_count=len(eligible_ids), excluded_count=len(excluded_ids),
        exclusion_reason="PDPA consent not given" if excluded_ids else "",
    )

@staticmethod
def is_consented(customer_id: UUID) -> bool:
    from apps.customers.models import Customer
    try:
        return Customer.objects.get(id=customer_id).pdpa_consent
    except Customer.DoesNotExist:
        return False

@staticmethod
def count_consented_customers(entity_id: UUID) -> int:
    from apps.customers.models import Customer
    return Customer.objects.filter(entity_id=entity_id, pdpa_consent=True).count()

@staticmethod
def count_opted_out_customers(entity_id: UUID) -> int:
    from apps.customers.models import Customer
    return Customer.objects.filter(entity_id=entity_id, pdpa_consent=False).count()
```

**Effort:** 10 min | **Risk:** Low — blast eligibility behavior changes

---

## Issue H4: BFF Proxy CORS Allows All Origins with Credentials

### Root Cause (Confirmed)

`frontend/app/api/proxy/[...path]/route.ts:208-211`:
```typescript
'Access-Control-Allow-Origin': '*',
'Access-Control-Allow-Credentials': 'true',
```

### Fix

Add origin-aware handling. Also add CORS headers to actual responses:

```typescript
const ALLOWED_ORIGINS = [
  'https://wellfond.sg',
  'https://www.wellfond.sg',
  'http://localhost:3000',
];

function getCorsHeaders(request: NextRequest): Record<string, string> {
  const origin = request.headers.get('origin') || '';
  const isAllowed = ALLOWED_ORIGINS.includes(origin) ||
                    (process.env.NODE_ENV === 'development' &&
                     origin.startsWith('http://localhost'));
  return {
    'Access-Control-Allow-Origin': isAllowed ? origin : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers':
      'Content-Type, Authorization, X-CSRFToken, X-Idempotency-Key',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '86400',
  };
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(request),
  });
}
```

Also add `getCorsHeaders(request)` to `proxyRequest()` response headers.

**Effort:** 10 min | **Risk:** Low

---

## Issue H5: Sessions Stored in Default Cache (LRU Eviction Risk)

### Root Cause (Confirmed)

`backend/apps/core/auth.py:18` — `from django.core.cache import cache` uses
default cache. `backend/config/settings/base.py:106-110` — a dedicated
`"sessions"` cache exists but is unused by `SessionManager`.

**Secondary:** `backend/apps/operations/routers/logs.py:74-87` —
`_check_idempotency` also uses `cache` (default) instead of
`caches["idempotency"]`.

### Fix

**Part A — SessionManager (`auth.py`):**

Replace `from django.core.cache import cache` with `from django.core.cache import caches` and add helper:

```python
class SessionManager:
    @classmethod
    def _get_session_cache(cls):
        from django.core.cache import caches
        return caches["sessions"]

    @classmethod
    def create_session(cls, user, request):
        # ... session_data unchanged ...
        session_cache = cls._get_session_cache()
        session_cache.set(
            cls.SESSION_KEY_PREFIX + session_key, session_data,
            timeout=int(cls.SESSION_DURATION.total_seconds()),
        )
        refresh_key = f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}"
        session_cache.set(refresh_key, user.id,
                          timeout=int(cls.REFRESH_DURATION.total_seconds()))
        return session_key, csrf_token

    @classmethod
    def get_session(cls, session_key):
        return cls._get_session_cache().get(cls.SESSION_KEY_PREFIX + session_key)

    @classmethod
    def delete_session(cls, session_key):
        session_cache = cls._get_session_cache()
        session_cache.delete(cls.SESSION_KEY_PREFIX + session_key)
        session_cache.delete(f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}")

    @classmethod
    def extend_session(cls, session_key, user):
        session_data = cls.get_session(session_key)
        if session_data:
            cls._get_session_cache().set(
                cls.SESSION_KEY_PREFIX + session_key, session_data,
                timeout=int(cls.SESSION_DURATION.total_seconds()),
            )
```

**Part B — `_check_idempotency` (`logs.py:69-88`):**
Change `cache.get/set` to `caches["idempotency"].get/set`.
(Moot after H7 fix removes the function entirely.)

**Effort:** 10 min | **Risk:** Low

---

## Issue H6: `list_logs` — 7 Queries, Per-Type Limit Bug

### Root Cause (Confirmed)

`backend/apps/operations/routers/logs.py:479-558` — 7 separate queries,
each `[:limit]` by type, then merged and re-sorted in Python. A dog with
50 heat logs + 50 weight logs returns 100 entries before final `[:limit]`.

### Fix

**Do NOT use `union()`** (too risky — 7-model union via `.values()` is untested).
Keep simple approach with DRY helper and correct global limit:

```python
@router.get("/{dog_id}", response=LogsListResponse)
def list_logs(request, dog_id: UUID, limit: int = 50):
    # ... user/dog/permission checks unchanged ...

    logs = []

    def _collect(related, log_type):
        for log in related.select_related('created_by').order_by("-created_at")[:limit]:
            logs.append({
                "id": str(log.id), "type": log_type,
                "dog_id": str(dog_id), "dog_name": dog.name,
                "created_at": log.created_at.isoformat(),
                "created_by_name": log.created_by.username if log.created_by else None,
            })

    _collect(dog.heat_logs,          "in_heat")
    _collect(dog.mating_logs,        "mated")
    _collect(dog.whelping_logs,      "whelped")
    _collect(dog.health_obs_logs,    "health_obs")
    _collect(dog.weight_logs,        "weight")
    _collect(dog.nursing_flag_logs,  "nursing_flag")
    _collect(dog.not_ready_logs,     "not_ready")

    logs.sort(key=lambda x: x["created_at"], reverse=True)
    results = logs[:limit]
    return {"count": len(results), "results": results}
```

This is DRY, maintains `select_related` on `created_by`, and the global
limit is now correct. 7 queries is acceptable for per-dog volumes (<500 rows).

**Effort:** 15 min | **Risk:** Low

---

## Issue H7: `HttpError(200, ...)` — API Contract Violation

### Root Cause (Confirmed)

`backend/apps/operations/routers/logs.py:109` and lines 161, 222, 286, 334,
374, 428 — all 7 log types:
```python
if _check_idempotency(request, str(dog_id), "in_heat"):
    raise HttpError(200, "Already processed")
```

`HttpError` wraps response in error envelope even for 200. Plus, the
idempotency **middleware** already handles replay with `caches["idempotency"]`.
These router-level checks are redundant AND use the wrong cache (H5 Part B).

### Fix

**Remove `_check_idempotency` calls from ALL 7 handler functions.**
The middleware at `middleware.py:49-101` handles this correctly.

Delete these 7 lines:
- Line 108-109 (in_heat)
- Line 161-162 (mated)
- Line 222-223 (whelped)
- Line 286-287 (health_obs)
- Line 334-335 (weight)
- Line 374-375 (nursing_flag)
- Line 428-429 (not_ready)

Also delete the `_check_idempotency` function itself (lines 69-88).

**Effort:** 5 min | **Risk:** None — middleware handles replay

---

## Issue H9: `Vaccination.save()` Silent `ImportError` Catch

### Root Cause (Confirmed)

`backend/apps/operations/models.py:282-286`:
```python
try:
    from .services.vaccine import calc_vaccine_due
    self.due_date = calc_vaccine_due(...)
except ImportError:
    pass  # Service not yet available
```

`backend/apps/operations/services/vaccine.py` **exists** (208 lines).
`ImportError` never fires under normal operation.

**However, removing the try/except is dangerous.** If any dependency of
`vaccine.py` fails to import, every `Vaccination.save()` would crash —
taking down the entire vaccination system.

### Fix

Log a warning with full traceback instead of silently swallowing:

```python
import logging
logger = logging.getLogger(__name__)

def save(self, *args, **kwargs):
    try:
        from .services.vaccine import calc_vaccine_due
        self.due_date = calc_vaccine_due(self.dog, self.vaccine_name,
                                         self.date_given)
    except ImportError:
        logger.warning(
            "Vaccine service import failed for %s. "
            "Due date not auto-calculated.", self.vaccine_name,
            exc_info=True,
        )
    self.status = self._calculate_status()
    super().save(*args, **kwargs)
```

**Effort:** 2 min | **Risk:** None — same resilience, now observable

---

## Issue H10: `IntercompanyTransfer.save()` Missing Atomicity

### Root Cause (Confirmed)

`backend/apps/finance/models.py:155-177` — two `Transaction.objects.create()`
calls outside `transaction.atomic()`. If the second create fails, transfer
exists with only one balancing transaction.

### Fix

Wrap in `transaction.atomic()`:

```python
def save(self, *args, **kwargs):
    from django.db import transaction as db_transaction
    from decimal import Decimal

    is_new = self._state.adding

    with db_transaction.atomic():
        super().save(*args, **kwargs)

        if is_new:
            from_name = getattr(self.from_entity, 'name',
                                str(self.from_entity.id))[:50]
            to_name = getattr(self.to_entity, 'name',
                              str(self.to_entity.id))[:50]

            Transaction.objects.create(
                type=TransactionType.EXPENSE, amount=self.amount,
                entity=self.from_entity, gst_component=Decimal("0.00"),
                date=self.date, category=TransactionCategory.OTHER,
                description=f"Transfer to {to_name}: {self.description}"[:200],
            )
            Transaction.objects.create(
                type=TransactionType.REVENUE, amount=self.amount,
                entity=self.to_entity, gst_component=Decimal("0.00"),
                date=self.date, category=TransactionCategory.OTHER,
                description=f"Transfer from {from_name}: {self.description}"[:200],
            )
```

**Effort:** 3 min | **Risk:** None — adds safety

---

## Section 4: Corrections to Original Remediation Plan

| # | Original Claim | Correction |
|---|---------------|------------|
| 1 | C3: "Replace content with re-exports" | **Will break:** sync/async API mismatch. Must update `use-offline-queue.ts` hook first. |
| 2 | H7: "Remove all `_check_idempotency` calls" | Correct, but `_check_idempotency` also uses wrong cache (`logs.py:74` — `cache` not `caches["idempotency"]`). |
| 3 | H6: "Use `union()` query" | **Too risky.** 7-model union via `.values()` untested. DRY global limit fix is safer. |
| 4 | H9: "Remove the try/except" | **Dangerous.** Removes resilience. Log warning with `exc_info=True` instead. |
| 5 | H5: "Use `caches['sessions']` in SessionManager" | Correct, but missed secondary instance in `_check_idempotency` (wrong cache). |

---

## Execution Priority Matrix (Corrected)

| Priority | Issue | Time | Risk | Impact if Deferred |
|----------|-------|------|------|--------------------|
| **P0** | C1 + H8 | 5 min | None | NParks + P&L runtime crash |
| **P0** | C2 | 10 min | None | NParks vet doc runtime crash |
| **P0** | H2 | 2 min | None | Audit trail permanently wrong |
| **P0** | H3 | 10 min | Low | PDPA compliance violation |
| **P0** | H10 | 3 min | None | Financial data integrity |
| **P0** | H7 | 5 min | None | API contract + double idempotency |
| **P1** | H5 | 10 min | Low | Random logouts |
| **P1** | H9 | 2 min | None | Silent vaccine mis-calc |
| **P1** | H1 | 15 min | Low | Duplicate records (low prob) |
| **P1** | H4 | 10 min | Low | Security finding |
| **P1** | H6 | 15 min | Low | Performance (7 queries) |
| **P1** | C3 | 30 min | **Medium** | PWA offline broken |

**Total: ~2 hours**

---

## Implementation Order

```
Phase 1: Critical + Data Integrity (C1+H8, C2, H2, H3, H10, H7) — 35 min
  C1+H8: Add @property line_total, gst_amount to AgreementLineItem
  C2:    Add follow_up_required field + migration
  H2:    Capture old_status before mutation in cancel_agreement
  H3:    Wire Customer.pdpa_consent into PDPAService
  H10:   Wrap IntercompanyTransfer.save() in transaction.atomic()
  H7:    Remove 7x _check_idempotency calls + function

Phase 2: Security + Correctness (H5, H9, H1, H4) — 37 min
  H5:    SessionManager -> caches["sessions"]
         _check_idempotency -> caches["idempotency"]
  H9:    Replace silent ImportError with logged warning
  H1:    Atomic idempotency with cache.add() (SET NX)
  H4:    Origin-aware CORS in BFF proxy

Phase 3: Performance (H6) — 15 min
  H6:    Refactor list_logs with DRY _collect helper + global limit

Phase 4: PWA Offline (C3) — 30 min (HIGH RISK)
  C3:    Migrate use-offline-queue.ts to async API
         Re-export proper IndexedDB module from root offline-queue.ts
         Update 7 ground pages for async queue loading state

Phase 5: Verification — 25 min
  1. cd backend && python -m pytest apps/ -v  (target: 0 failures)
  2. cd frontend && npm run typecheck  (target: 0 errors)
  3. Manual: NParks.generate_nparks() succeeds (C1+C2 fix)
  4. Manual: Offline queue sync works end-to-end (C3 fix)
  5. Manual: PDPA consent filters blast eligibility (H3 fix)
  6. curl -H "Origin: https://evil.com" -X OPTIONS localhost:3000/api/proxy/health
     (verify rejected — H4 fix)
```

---

## Migration Requirements

**One new migration:** `operations/0003_add_follow_up_to_health_record.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('operations', '0002_alter_healthrecord_options')]
    operations = [
        migrations.AddField(
            model_name='healthrecord', name='follow_up_required',
            field=models.BooleanField(
                default=False,
                help_text='Whether follow-up veterinary treatment is required'
            ),
        ),
        migrations.AddField(
            model_name='healthrecord', name='follow_up_date',
            field=models.DateField(
                blank=True, null=True,
                help_text='Scheduled follow-up date'
            ),
        ),
    ]
```

Run: `cd backend && python manage.py makemigrations && python manage.py migrate`

---

## Risk Assessment

| Fix | Breaking | Rollback |
|-----|----------|----------|
| C1+H8 | None | Remove @property |
| C2 | None | Remove field, revert migration |
| C3 | **Medium** — 7 pages + hook | Revert to localStorage, revert hook |
| H1 | Low — locking | Revert to non-atomic |
| H2 | None | No rollback needed |
| H3 | Low — blast eligibility | Revert to placeholders |
| H4 | Low — origin checking | Revert to `*` |
| H5 | Low — cache backend | Revert to default cache |
| H6 | Low — SQL | Revert to 7 loops |
| H7 | None — removes dead code | Add back |
| H9 | None — same, now visible | Add back `pass` |
| H10 | None — adds safety | Remove atomic wrapper |

**No data loss risk. All migrations additive. All fixes reversible.**

---

*End of Corrected Remediation Plan v2 — 2026-05-01*
