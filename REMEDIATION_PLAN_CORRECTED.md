### 🔍 Root Cause Diagnosis
The `write` tool failed because the input string was **not valid JSON**. Three specific issues caused the parser to crash:
1. **Unescaped newlines & quotes**: Markdown content was injected directly into a JSON string without escaping `\n`, `\"`, or backticks.
2. **Payload concatenation**: Two separate file writes (`REMEDIATION_PLAN_CORRECTED.md` and `REMEDIATION_PLAN_mimo_v2.md`) were merged into a single string mid-sentence.
3. **Truncation**: The first payload cuts off abruptly at `@class{"filePath":...`, breaking JSON syntax entirely.

---

### 📋 Meticulous Extraction & Recovery Plan

| Phase | Action | Details |
|-------|--------|---------|
| **1. Isolate** | Split concatenated payloads | Cut at the exact injection point: `@class{"filePath": "/home/project/wellfond-bms/REMEDIATION_PLAN_mimo_v2.md"` |
| **2. Clean** | Strip JSON wrapper artifacts | Remove `{"filePath": "...", "content": "` prefix and trailing `}`. Convert escaped sequences (`\n`, `\"`) to raw characters. |
| **3. Validate** | Check markdown integrity | Verify heading hierarchy, code block closure, table alignment, and ensure no truncated lines remain. |
| **4. Reconstruct** | Prepare safe write payload | Use the complete `v2` version as authoritative. Format as raw markdown or properly escaped JSON. |
| **5. Write & Verify** | Save to disk & validate | Write to target path, verify line count, render markdown, and confirm no syntax corruption. |

---

### 📄 Extracted & Cleaned Markdown Content
Below is the **complete, ready-to-write** content for `REMEDIATION_PLAN_mimo_v2.md`. JSON artifacts have been removed, newlines restored, and formatting preserved. *(Note: `REMEDIATION_PLAN_CORRECTED.md` was truncated mid-code-block and is superseded by this v2 version.)*

```markdown
# Wellfond BMS — Corrected Remediation Plan v2

**Date:** 2026-05-01
**Based on:** Systematic re-validation of code_audit_new_summary.md against source
**Scope:** 3 Critical + 10 High issues — all re-validated at file:line level
**Status:** READY FOR EXECUTION

---

## Re-Validation Summary

Every issue below was confirmed by reading the actual source code with exact
file:line references. Root causes are confirmed. Five corrections to the
original remediation plan are documented in Section 4.

| ID | Severity | Re-Validated | Root Cause Confirmed |
|----|----------|-------------|---------------------|
| C1 | CRITICAL | ✅ `nparks.py:272` | `AgreementLineItem` model missing `line_total` property |
| C2 | CRITICAL | ✅ `nparks.py:340` | `HealthRecord` model missing `follow_up_required` field |
| C3 | CRITICAL | ✅ `offline-queue.ts` | Root `offline-queue.ts` uses localStorage; proper IndexedDB implementation exists at `lib/offline-queue/` but is unused |
| H1 | HIGH | ✅ `middleware.py:73-90` | `get()` → `set()` is non-atomic TOCTOU |
| H2 | HIGH | ✅ `agreement.py:588-599` | `agreement.status` read after `.save()` already wrote CANCELLED |
| H3 | HIGH | ✅ `pdpa.py:109,138` | Placeholder stubs; `Customer` model with `pdpa_consent` exists |
| H4 | HIGH | ✅ `route.ts:208-211` | `Allow-Origin: *` + `Allow-Credentials: true` |
| H5 | HIGH | ✅ `auth.py:18,55` | `SessionManager` uses `cache` (default) instead of `caches["sessions"]` |
| H6 | HIGH | ✅ `logs.py:479-558` | 7 queries, per-type limits, Python-side merge + sort |
| H7 | HIGH | ✅ `logs.py:109` | `raise HttpError(200, ...)` — API contract violation; 7 locations |
| H8 | HIGH | ✅ `agreement.py:625-626` | Same root cause as C1 |
| H9 | HIGH | ✅ `operations/models.py:282-286` | `except ImportError: pass` when `vaccine.py` exists |
| H10 | HIGH | ✅ `finance/models.py:155-177` | Two `Transaction.objects.create()` outside `transaction.atomic()` |

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
# backend/apps/sales/models.py — add to AgreementLineItem class (after __str__)

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
# Then: call AgreementService.calculate_totals() — must not raise AttributeError
# And: call NParksService.generate_nparks() — must not raise on line 272
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
`follow_up_required` field. The field was planned (NParks needs it) but
never added to the model.

### Fix

**Step 1:** Add field to `HealthRecord` model (`operations/models.py:198`):

```python
class HealthRecord(models.Model):
    # ... existing fields (dog, date, category, description, temperature,
    #     weight, vet_name, photos, created_at, created_by) ...

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

    # Metadata ... (keep existing)
```

**Step 2:** Generate migration:

```bash
cd backend && python manage.py makemigrations operations \
    --name add_follow_up_to_health_record
python manage.py migrate
```

### Verification

```python
record = HealthRecord.objects.create(
    dog=dog, date=date.today(), category="VET_VISIT",
    description="Checkup", follow_up_required=True,
)
assert record.follow_up_required is True
# Then: call NParksService.generate_nparks() — must not raise on line 340
```

**Effort:** 10 min | **Risk:** None (additive, default=False)

---

## Issue C3: Root `offline-queue.ts` Uses `localStorage`, IndexedDB Impl Exists But Unused

### Root Cause (Confirmed)

**Current state (READ THIS BEFORE FIXING):**

| File | What it does | API |
|------|-------------|-----|
| `lib/offline-queue.ts` (root) | Legacy `localStorage` wrapper | **Sync** functions |
| `lib/offline-queue/index.ts` | Proper adapter with IndexedDB | **Async** functions |
| `lib/offline-queue/db.ts` | IndexedDB connection + migration | (internal) |
| `lib/offline-queue/adapter.idb.ts` | IndexedDB storage adapter | (internal) |
| `lib/offline-queue/adapter.ls.ts` | localStorage fallback adapter | (internal) |
| `lib/offline-queue/adapter.memory.ts` | In-memory fallback adapter | (internal) |
| `lib/offline-queue/types.ts` | Shared types | (internal) |

**The critical mismatch:** The root `lib/offline-queue.ts` exports
**synchronous** functions (`getQueue()`, `addToQueue()`, etc). The proper
`lib/offline-queue/index.ts` exports **asynchronous** functions (all return
`Promise`). Simply re-exporting — as the original plan proposed — **will
break every consumer**:

`frontend/hooks/use-offline-queue.ts:21`:
```typescript
const [queue, setQueue] = useState<OfflineQueueItem[]>(getQueue());
//                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TypeError!
// getQueue() returns Promise<OfflineQueueItem[]>, not OfflineQueueItem[]
```

Seven ground pages import `useOfflineQueue` — all would fail to compile or
crash at runtime with `TypeError: queue is not an array`.

**Note:** The Service Worker (`public/sw.js:154`) calls
`/api/proxy/sync-offline` — it does not access the offline queue directly. The
"SW can't access localStorage" reasoning in the original audit is technically
true but irrelevant to this bug. The real problem is the sync API mismatch.

### Fix (Three Steps)

**Step 1: Update `use-offline-queue.ts` for async API** (primary consumer):

Replace the synchronous `useState(getQueue())` with `useEffect` + loading state:

```typescript
// hooks/use-offline-queue.ts
"use client";

import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/components/ui/use-toast";
import type { OfflineQueueItem } from "@/lib/offline-queue";
import {
  getQueue, addToQueue, removeFromQueue, getQueueCount, incrementRetry,
} from "@/lib/offline-queue";

export function useOfflineQueue() {
  // ... existing isOnline, isProcessing, toast ...

  // ✅ FIXED: Use effect for async initial load
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

    const currentQueue = await getQueue(); // ✅ await
    if (currentQueue.length === 0) return;
    // ... rest unchanged but add await to all getQueue() calls ...
  }, [isProcessing, toast]);
  // ... (return queueLoaded in output for loading state) ...
}
```

All 8 calls to `getQueue()`, `addToQueue()` etc. in the hook must add `await`.

**Step 2: Replace `lib/offline-queue.ts` with re-exports:**

Only safe AFTER Step 1 is done (all consumers migrated to async). The
`getQueueSync` / `addToQueueSync` legacy exports from `index.ts` provide
backward compat during transition.

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

**Step 3: Update ground pages to handle loading state:**

```typescript
// In each ground page, destructure queueLoaded:
const { isOnline, queue, queueLoaded, queueLength, queueRequest, processQueue } =
    useOfflineQueue();
// Show loading state while queue initializes
if (!queueLoaded) return <Spinner />;
```

### Verification

1. Open app, verify queue loads (no TypeError on `getQueueSync`)
2. Go offline (DevTools > Network > Offline)
3. Submit a ground log from any page
4. Verify item appears in IndexedDB (`DevTools > Application > IndexedDB > wellfond-offline-queue`)
5. Go back online, verify sync succeeds
6. Verify sync also works via SW background sync endpoint

**Effort:** 30 min | **Risk:** Medium — async migration touches hook + 7 pages

---

## Issue H1: Idempotency Middleware TOCTOU Race
### Root Cause (Confirmed)

`backend/apps/core/middleware.py:73-96` — non-atomic `get()` check, then
`set()` after processing. Two concurrent requests with the same idempotency
key both pass the `get()` check and both execute the handler.

### Fix
Use `cache.add()` (Django equivalent of Redis `SET NX` — returns `False` if
key already exists, atomically):

```python
# middleware.py — in __call__, replace lines 69-96

fingerprint = self._generate_fingerprint(request, idempotency_key)
idempotency_cache = caches["idempotency"]

# Fast path: check for completed response
cached_response = idempotency_cache.get(fingerprint)
if cached_response and cached_response.get("status") != "processing":
    response = JsonResponse(cached_response["data"],
                            status=cached_response["status"])
    response["Idempotency-Replay"] = "true"
    return response

# Atomic lock: cache.add() is SET NX — False if key exists
if not idempotency_cache.add(fingerprint, {"status": "processing"}, timeout=30):
    # Another request is processing — re-check for completed
    cached_response = idempotency_cache.get(fingerprint)
    if cached_response and cached_response.get("status") != "processing":
        response = JsonResponse(cached_response["data"],
                                status=cached_response["status"])
        response["Idempotency-Replay"] = "true"
        return response
    return JsonResponse({"error": "Request already in progress"}, status=409)

# We hold the lock — process
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

`backend/apps/sales/services/agreement.py:588-599` — `agreement.status` is
set to CANCELLED at line 590, saved at line 592, and then READ at line 599
for the audit log. The audit records CANCELLED → CANCELLED
instead of the actual transition (e.g. DRAFT → CANCELLED).

### Fix
Capture before mutation:

```python
def cancel_agreement(agreement_id, cancelled_by, reason=""):
    # ... try/except unchanged ...
    # ✅ Capture state BEFORE mutation
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
                "old_status": old_status,              # ✅ captured
                "new_status": AgreementStatus.CANCELLED,
                "reason": reason,
            },
        )
    # ...
```

**Effort:** 2 min | **Risk:** None

---

## Issue H3: PDPA Placeholder Stubs — Compliance Gap
### Root Cause (Confirmed)

`backend/apps/compliance/services/pdpa.py:109` — `check_blast_eligibility`
returns ALL customers as eligible (comment: "deferred to Phase 7").

`backend/apps/compliance/services/pdpa.py:138` — `is_consented` always
returns `True`.

BUT: `backend/apps/customers/models.py:44-112` — `Customer` model **exists**
with `pdpa_consent = models.BooleanField(default=False)`. Phase 7 is
marked complete in README. These stubs should have been replaced.

### Fix
Replace all four placeholder methods:

```python
# pdpa.py — replace check_blast_eligibility, is_consented,
#          count_consented_customers, count_opted_out_customers

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

Add origin-aware handling. Also add CORS headers to actual responses (not just
preflight `OPTIONS`):

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

// Replace OPTIONS handler
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(request),
  });
}

// In proxyRequest(), add after building the response:
const corsHeaders = getCorsHeaders(request);
Object.entries(corsHeaders).forEach(([k, v]) => responseHeaders.set(k, v));
```

**Effort:** 10 min | **Risk:** Low — may need CORS allowlist update

---

## Issue H5: Sessions Stored in Default Cache (LRU Eviction Risk)
### Root Cause (Confirmed)

`backend/apps/core/auth.py:18` — `from django.core.cache import cache` uses
the `default` cache (Redis DB 0) which uses `allkeys-lru` eviction. Under
memory pressure, session keys get evicted → random logouts.

`backend/config/settings/base.py:106-110` — a dedicated `"sessions"` cache
backend exists (separate Redis instance) but is unused by the custom
`SessionManager`.

**Secondary instance:** `backend/apps/operations/routers/logs.py:74-87` —
`_check_idempotency` also uses `cache` (default) instead of
`caches["idempotency"]`.

### Fix
**Part A — SessionManager (`auth.py`):**

Replace all `cache.set/get/delete` with `session_cache.X`:

```python
# auth.py — in SessionManager

@classmethod
def _get_session_cache(cls):
    from django.core.cache import caches
    return caches["sessions"]

@classmethod
def create_session(cls, user, request):
    # ... (session_data unchanged) ...
    session_cache = cls._get_session_cache()
    session_cache.set(cls.SESSION_KEY_PREFIX + session_key, session_data,
                      timeout=int(cls.SESSION_DURATION.total_seconds()))
    # Same for refresh key
    refresh_key = f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}"
    session_cache.set(refresh_key, user.id,
                      timeout=int(cls.REFRESH_DURATION.total_seconds()))
    return session_key, csrf_token

# Update get_session, extend_session, delete_session similarly
```

**Part B — `_check_idempotency` (`logs.py:69-88`):** Replace `cache.get/set`
with `caches["idempotency"].get/set`.

**Effort:** 10 min | **Risk:** Low

---

## Issue H6: `list_logs` — 7 Queries, Per-Type Limit Bug
### Root Cause (Confirmed)

`backend/apps/operations/routers/logs.py:479-558` — 7 separate queries,
each `[:limit]` by type, then merged and re-sorted in Python. A dog with
50 heat logs + 50 weight logs returns 100 entries before the final `[:limit]`.

### Fix
**Do NOT use `union()`** (too risky — Django's `union()` requires exact
column alignment across 7 model types, and the original plan's SQL has not
been tested). Instead, fix the limit to be global and keep the simple approach:

```python
@router.get("/{dog_id}", response=LogsListResponse)
def list_logs(request, dog_id: UUID, limit: int = 50):
    # ... user/dog/permission checks unchanged ...

    logs = []

    def _collect(model_related, log_type):
        for log in model_related.select_related('created_by')
                                    .order_by("-created_at")[:limit]:
            logs.append({
                "id": str(log.id),
                "type": log_type,
                "dog_id": str(dog_id),
                "dog_name": dog.name,
                "created_at": log.created_at.isoformat(),
                "created_by_name": log.created_by.username if log.created_by
                                                           else None,
            })

    _collect(dog.heat_logs,          "in_heat")
    _collect(dog.mating_logs,        "mated")
    _collect(dog.whelping_logs,      "whelped")
    _collect(dog.health_obs_logs,    "health_obs")
    _collect(dog.weight_logs,        "weight")
    _collect(dog.nursing_flag_logs,  "nursing_flag")
    _collect(dog.not_ready_logs,     "not_ready")

    # Sort in Python (per-dog log count is typically < 500 = trivial)
    logs.sort(key=lambda x: x["created_at"], reverse=True)
    results = logs[:limit]

    return {"count": len(results), "results": results}
```

This is clean, DRY, maintains `select_related` on `created_by`, and the
global limit is correct. 7 queries is acceptable given the per-dog volume.

**Effort:** 15 min | **Risk:** Low

---

## Issue H7: `HttpError(200, ...)` — API Contract Violation
### Root Cause (Confirmed)

`backend/apps/operations/routers/logs.py:109`:
```python
if _check_idempotency(request, str(dog_id), "in_heat"):
    raise HttpError(200, "Already processed")
```

Same pattern at lines 161, 222, 286, 334, 374, 428 — for all 7 log types.
`HttpError` in Django Ninja wraps the response in an error envelope even for
status 200. Plus, the idempotency **middleware** already handles replay at
the middleware level, making these router-level checks redundant AND using
the wrong cache (see H5 Part B).

### Fix
**Remove `_check_idempotency` calls from ALL 7 handler functions.**
The middleware at `middleware.py:49-101` already handles this correctly with
`caches["idempotency"]`.

```python
@router.post("/in-heat/{dog_id}", response=InHeatResponse)
def create_in_heat_log(request, dog_id: UUID, data: InHeatCreate):
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")
    # ❌ REMOVED: _check_idempotency(request, str(dog_id), "in_heat")
    # ... rest unchanged ...
```

Apply to lines: 108-109, 161-162, 222-223, 286-287, 334-335, 374-375, 428-429.

**Effort:** 5 min | **Risk:** None — middleware handles replay

---

## Issue H9: `Vaccination.save()` Silent `ImportError` Catch
### Root Cause (Confirmed)

`backend/apps/operations/models.py:282-286`:
```python
def save(self, *args, **kwargs):
    try:
        from .services.vaccine import calc_vaccine_due
        self.due_date = calc_vaccine_due(self.dog, self.vaccine_name,
                                         self.date_given)
    except ImportError:
        pass  # Service not yet available, skip
```

`backend/apps/operations/services/vaccine.py` **exists** (208 lines,
fully functional). The `ImportError` will never fire under normal operation.

**However, the fix is NOT to simply remove the try/except.** If a
dependency of `vaccine.py` fails to import (e.g., `from django.db.models
import QuerySet` breaks), removing the catch means every
`Vaccination.save()` will crash — taking down the entire vaccination system.

### Fix
Log a warning but allow the save to proceed. This preserves resilience if a
dependency breaks while making the issue visible:

```python
import logging

logger = logging.getLogger(__name__)

def save(self, *args, **kwargs):
    try:
        from .services.vaccine import calc_vaccine_due
        self.due_date = calc_vaccine_due(self.dog, self.vaccine_name,
                                         self.date_given)
    except ImportError:
        # v2: Log with traceback instead of silently swallowing
        logger.warning(
            "Vaccine service import failed for %s. "
            "Due date not auto-calculated.", self.vaccine_name,
            exc_info=True,
        )
    self.status = self._calculate_status()
    super().save(*args, **kwargs)
```

**Effort:** 2 min | **Risk:** None — same behavior, now observable

---

## Issue H10: `IntercompanyTransfer.save()` Missing Atomicity
### Root Cause (Confirmed)

`backend/apps/finance/models.py:155-177` — two `Transaction.objects.create()`
calls outside `transaction.atomic()`. If the second fails, the transfer
exists with only a single (unbalanced) transaction.

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
            from_entity = self.from_entity
            to_entity = self.to_entity
            from_name = getattr(from_entity, 'name', str(from_entity.id))[:50]
            to_name = getattr(to_entity, 'name', str(to_entity.id))[:50]

            Transaction.objects.create(
                type=TransactionType.EXPENSE, amount=self.amount,
                entity=from_entity, gst_component=Decimal("0.00"),
                date=self.date, category=TransactionCategory.OTHER,
                description=f"Transfer to {to_name}: {self.description}"[:200],
            )
            Transaction.objects.create(
                type=TransactionType.REVENUE, amount=self.amount,
                entity=to_entity, gst_component=Decimal("0.00"),
                date=self.date, category=TransactionCategory.OTHER,
                description=f"Transfer from {from_name}: {self.description}"[:200],
            )
```

**Effort:** 3 min | **Risk:** None — adds safety

---

## Section 4: Corrections to Original Remediation Plan

| # | Original Plan Claim | Correction |
|---|--------------------|------------|
| 1 | C3 fix: "Replace content with re-exports" | **Will break:** API mismatch (sync vs async). Must update `use-offline-queue.ts` hook first. See C3 fix above. |
| 2 | H7 fix: "Remove all `_check_idempotency` calls" | Correct, but must ALSO fix the wrong cache (`logs.py:74` uses `cache` not `caches["idempotency"]`). If `_check_idempotency` is kept (even unused), it has a secondary bug. |
| 3 | H6 fix: "Use `union()` query" | **Too risky.** 7-model union via `.values()` is untested and fragile. Simpler global limit fix is safer. See H6 fix above. |
| 4 | H9 fix: "Remove the try/except" | **Dangerous.** Removes resilience. Should log warning with `exc_info=True` instead. See H9 fix above. |
| 5 | H5 fix: "Use `caches['sessions']` in SessionManager" | Correct, but also missed the secondary instance in `_check_idempotency` (`logs.py:74` which uses wrong cache too). See H5 fix (Part B). |

---

## Execution Priority Matrix (Corrected)

| Priority | Issue | Time | Risk | Impact if Deferred |
|----------|-------|------|------|-------------------|
| **P0-1** | C1 + H8 | 5 min | None | NParks + P&L crash at runtime |
| **P0-2** | C2 | 10 min | None | NParks vet doc crash at runtime |
| **P0-3** | H2 | 2 min | None | Audit trail permanently wrong |
| **P0-4** | H3 | 10 min | Low | PDPA violation |
| **P0-5** | H10 | 3 min | None | Financial data integrity |
| **P0-6** | H7 | 5 min | None | API contract + double idempotency bug |
| **P1-1** | H5 | 10 min | Low | Random logouts + wrong cache in logs |
| **P1-2** | H9 | 2 min | None | Silent vaccine mis-calc |
| **P1-3** | H1 | 15 min | Low | Duplicate DB records (low probability) |
| **P1-4** | H4 | 10 min | Low | Security finding |
| **P1-5** | H6 | 15 min | Low | Performance (7 queries) |
| **P1-6** | C3 | 30 min | **Medium** | PWA offline broken for ground staff |

**Total: ~2 hours**

---

## Implementation Order

```
Phase 1: Critical + Data Integrity (C1+H8, C2, H2, H3, H10, H7) — 35 min
  🌳 C1+H8: Add @property line_total, gst_amount to AgreementLineItem
  🌳 C2: Add follow_up_required field + migration
  🌳 H2: Capture old_status before mutation in cancel_agreement
  🌳 H3: Wire Customer.pdpa_consent into PDPAService
  🌳 H10: Wrap IntercompanyTransfer.save() in transaction.atomic()
  🌳 H7: Remove 7x _check_idempotency calls; fix cache in remaining fn

Phase 2: Security + Correctness (H5, H9, H1, H4) — 37 min
  🌳 H5: SessionManager → caches["sessions"] + _check_idempotency
           → caches["idempotency"]
  🌳 H9: Replace silent ImportError with logged warning
  🌳 H1: Atomic idempotency with cache.add() (SET NX)
  🌳 H4: Origin-aware CORS in BFF proxy OPTIONS + responses

Phase 3: Performance (H6) — 15 min
  🌳 H6: Refactor list_logs with global limit + DRY _collect helper

Phase 4: PWA Offline (C3) — 30 min ⚠️ HIGH RISK
  🌳 C3: Migrate use-offline-queue.ts to async API
  🌳     Re-export proper IndexedDB module from root offline-queue.ts
  🌳     Update 7 ground pages for async queue loading state

Phase 5: Verification — 25 min
  1️⃣ python -m pytest apps/ -v  (target: 0 failures)
  2️⃣ cd frontend && npm run typecheck  (target: 0 errors)
  3️⃣ Manual: NParks Excel generation works (C1+C2 fix)
  4️⃣ Manual: Offline queue sync works (C3 fix)
  5️⃣ Manual: PDPA consent filtering (H3 fix)
  6️⃣ curl -H "Origin: https://evil.com" localhost:3000/api/proxy/health
           (verify not allowed — H4 fix)
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

| Fix | Breaking Change | Rollback |
|-----|----------------|----------|
| C1+H8 | None | Remove @property |
| C2 | None | Remove field + revert migration |
| C3 | **Medium** — 7 ground pages + hook | Revert to localStorage root, revert hook |
| H1 | Low — changes locking | Revert to non-atomic |
| H2 | None | No rollback needed |
| H3 | Low — blast eligibility changes | Revert to placeholders |
| H4 | Low — origin checking | Revert to `*` |
| H5 | Low — cache backend | Revert to default cache |
| H6 | Low — SQL generation | Revert to 7 loops |
| H7 | None — removes redundant code | Add back |
| H9 | None — same behavior, visible | Add back `pass` |
| H10 | None — adds safety | Remove atomic wrapper |

**No breaking changes. No data loss risk. All migrations are additive.**

---

*End of Corrected Remediation Plan v2 — 2026-05-01*
```

---

### 🛠️ Corrected Tool Input Format (JSON-Safe)
If you must pass this through a JSON-based tool, use this structure. Note the proper escaping and single-payload focus:

```json
{
  "filePath": "/home/project/wellfond-bms/REMEDIATION_PLAN_mimo_v2.md",
  "content": "# Wellfond BMS — Corrected Remediation Plan v2\n\n**Date:** 2026-05-01\n**Based on:** Systematic re-validation of code_audit_new_summary.md against source\n**Scope:** 3 Critical + 10 High issues — all re-validated at file:line level\n**Status:** READY FOR EXECUTION\n\n---\n\n## Re-Validation Summary\n\nEvery issue below was confirmed by reading the actual source code with exact\nfile:line references. Root causes are confirmed. Five corrections to the\noriginal remediation plan are documented in Section 4.\n\n| ID | Severity | Re-Validated | Root Cause Confirmed |\n|----|----------|-------------|---------------------|\n| C1 | CRITICAL | ✅ `nparks.py:272` | `AgreementLineItem` model missing `line_total` property |\n| C2 | CRITICAL | ✅ `nparks.py:340` | `HealthRecord` model missing `follow_up_required` field |\n...(rest of content properly escaped)..."
}
```
💡 **Pro Tip**: For large markdown files, avoid JSON string escaping entirely. Write the content directly via standard file I/O or base64-encode the payload before passing it to the tool.

---

### ✅ Prevention Checklist for Future Tool Calls
- [ ] Never concatenate multiple `write` payloads into one string
- [ ] Use a JSON linter/validator before submitting tool input
- [ ] Escape newlines (`\n`), quotes (`\"`), and backslashes (`\\`) in JSON strings
- [ ] Split files >50KB into chunked writes or use raw file streams
- [ ] Verify tool schema matches exactly (`filePath` + `content` only, no extra keys)

# https://chat.qwen.ai/s/6975b0fd-d1aa-4c2a-b67e-83b4cc098dfe?fev=0.2.45 

