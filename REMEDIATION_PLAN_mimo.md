# Wellfond BMS — Comprehensive Remediation Plan

**Date:** 2026-05-01  
**Based on:** CODE_REVIEW_AUDIT_REPORT.md  
**Scope:** All Critical (3) and High (11) issues — fully re-validated  
**Status:** READY FOR EXECUTION  

---

## Re-Validation Summary

Every issue below was re-read against the actual source code. Root causes are confirmed with exact file:line references. Fixes are designed to be minimal, safe, and non-breaking.

| ID | Severity | Status | Root Cause Confirmed |
|----|----------|--------|---------------------|
| C1 | 🔴 CRITICAL | ✅ Verified | `nparks.py:272` — `item.line_total` does not exist on `AgreementLineItem` model |
| C2 | 🔴 CRITICAL | ✅ Verified | `nparks.py:340` — `record.follow_up_required` does not exist on `HealthRecord` model |
| C3 | 🔴 CRITICAL | ✅ Verified | `offline-queue.ts` uses `localStorage`; SW can't access it; IndexedDB adapter exists but unused |
| H1 | 🟠 HIGH | ✅ Verified | `middleware.py:75-80` — `get()` then `set()` is non-atomic TOCTOU race |
| H2 | 🟠 HIGH | ✅ Verified | `agreement.py:591-593` — `agreement.status` read after `.save()` already wrote CANCELLED |
| H3 | 🟠 HIGH | ✅ Verified | `pdpa.py:109,138` — `check_blast_eligibility` returns all as eligible; `is_consented` returns `True` |
| H4 | 🟠 HIGH | ✅ Verified | `route.ts:208-215` — `Allow-Origin: *` with `Allow-Credentials: true` |
| H5 | 🟠 HIGH | ✅ Verified | `auth.py:55` — `cache.set()` uses default cache, not `caches["sessions"]` |
| H6 | 🟠 HIGH | ✅ Verified | `logs.py:285-370` — 7 separate queries with per-type LIMIT, merged in Python |
| H7 | 🟠 HIGH | ✅ Verified | `logs.py:105` — `raise HttpError(200, ...)` is API contract violation |
| H8 | 🟠 HIGH | ✅ Verified | `agreement.py:625-626` — `item.line_total` and `item.gst_amount` don't exist on model |
| H9 | 🟠 HIGH | ✅ Verified | `models.py:282-286` — `except ImportError: pass` is dead code; service file exists |
| H10 | 🟠 HIGH | ✅ Verified | `finance/models.py:161-191` — `save()` creates 2 Transactions outside `transaction.atomic()` |

---

## Issue C1: NParks `_generate_puppy_movement` References Non-Existent `line_total`

### Root Cause (Confirmed)

**File:** `backend/apps/compliance/services/nparks.py`, line 272  
**Code:**
```python
ws.cell(row=current_row, column=13, value=float(item.line_total))
```

The `AgreementLineItem` model (`backend/apps/sales/models.py`) has:
- `price` — Decimal field
- `gst_component` — Decimal field
- **No `line_total` property or field**

The test factory (`backend/apps/sales/tests/factories.py:78`) defines `line_total` as a `@factory.lazy_attribute`, but this is a test-only mock — it does NOT add the property to the actual Django model.

### Impact
- **Runtime:** `AttributeError: 'AgreementLineItem' object has no attribute 'line_total'`
- **Trigger:** Any call to `NParksService.generate_nparks()` when completed agreements with line items exist
- **Severity:** NParks compliance reporting completely broken for puppy movement document

### Fix

**Option A (Preferred): Add property to model** — minimal change, fixes all callers

**File:** `backend/apps/sales/models.py` — add to `AgreementLineItem` class:
```python
class AgreementLineItem(models.Model):
    # ... existing fields ...

    @property
    def line_total(self) -> Decimal:
        """Total amount for this line item (price only, GST tracked separately)."""
        return self.price

    @property
    def gst_amount(self) -> Decimal:
        """GST component for this line item."""
        return self.gst_component
```

**Option B (Alternative): Fix the caller** — if `line_total` should include GST:
```python
# nparks.py:272
ws.cell(row=current_row, column=13, value=float(item.price + item.gst_component))
```

**Recommendation:** Option A — the test factory already defines `line_total` as `unit_price * quantity`, and `agreement.py:625` also references it. Adding the property to the model fixes all callers at once.

### Verification
```python
# After fix, this should work:
item = AgreementLineItem(price=Decimal("1000.00"), gst_component=Decimal("90.00"))
assert item.line_total == Decimal("1000.00")
assert item.gst_amount == Decimal("90.00")
```

---

## Issue C2: NParks `_generate_vet_treatments` References Non-Existent `follow_up_required`

### Root Cause (Confirmed)

**File:** `backend/apps/compliance/services/nparks.py`, line 340  
**Code:**
```python
ws.cell(row=row, column=9, value="Yes" if record.follow_up_required else "No")
```

The `HealthRecord` model (`backend/apps/operations/models.py`) has these fields:
- `dog`, `date`, `category`, `description`, `temperature`, `weight`, `vet_name`, `photos`, `created_at`, `created_by`
- **No `follow_up_required` field**

This field was likely planned but never added to the model.

### Impact
- **Runtime:** `AttributeError: 'HealthRecord' object has no attribute 'follow_up_required'`
- **Trigger:** Any call to `NParksService.generate_nparks()` when health records exist for the reporting month
- **Severity:** NParks vet treatments document generation completely broken

### Fix

**Option A (Preferred): Add field to HealthRecord model**

**File:** `backend/apps/operations/models.py` — add to `HealthRecord`:
```python
class HealthRecord(models.Model):
    # ... existing fields ...
    vet_name = models.CharField(max_length=100, blank=True)
    
    # NEW: Follow-up tracking for NParks reporting
    follow_up_required = models.BooleanField(
        default=False,
        help_text="Whether follow-up veterinary treatment is required",
    )
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled follow-up date",
    )
```

Then generate migration:
```bash
cd backend && python manage.py makemigrations operations --name add_follow_up_to_health_record
python manage.py migrate
```

**Option B (Alternative): Remove the column from Excel output**
```python
# Remove column 9 from headers and data population
# Adjust column indices accordingly
```

**Recommendation:** Option A — `follow_up_required` is a clinically useful field for vet tracking and NParks compliance. Adding it improves the domain model.

### Verification
```python
record = HealthRecord(follow_up_required=True)
assert record.follow_up_required is True
```

---

## Issue C3: Offline Queue Uses `localStorage` — Broken in Service Worker

### Root Cause (Confirmed)

**File:** `frontend/lib/offline-queue.ts` — entire file  
**Code:**
```typescript
function readStorage(): OfflineQueueItem[] {
  const raw = localStorage.getItem(STORAGE_KEY);  // ← localStorage!
  return raw ? JSON.parse(raw) : [];
}
```

The file header explicitly states:
```typescript
// TODO: Migrate from localStorage to IndexedDB for production.
```

**Meanwhile, the proper implementation exists at:**
- `frontend/lib/offline-queue/adapter.idb.ts` — IndexedDB adapter
- `frontend/lib/offline-queue/db.ts` — IndexedDB database
- `frontend/lib/offline-queue/index.ts` — Proper module entry point
- `frontend/lib/offline-queue/types.ts` — Type definitions

The Service Worker (`frontend/public/sw.js`) calls `syncOfflineQueue()` which fetches `/api/proxy/sync-offline`. But the SW cannot access `localStorage` — it runs in a separate worker context. This means:
1. Background sync cannot read queued items
2. Items queued while offline are invisible to the SW
3. Data loss on network reconnect when app is in background

### Impact
- **PWA offline functionality is completely broken** for ground staff
- Ground staff in areas with poor connectivity (common in breeding farms) will lose log data
- The IndexedDB implementation exists but is not wired up

### Fix

**Replace `frontend/lib/offline-queue.ts` content with a re-export from the proper module:**

```typescript
/**
 * Offline Queue - Re-export from proper IndexedDB implementation.
 * 
 * This file previously used localStorage which is inaccessible from
 * Service Workers. Now delegates to the IndexedDB-backed implementation
 * at lib/offline-queue/index.ts.
 */

export {
  addToQueue,
  clearQueue,
  getQueue,
  getQueueCount,
  incrementRetry,
  removeFromQueue,
} from './offline-queue/index';

export type { OfflineQueueItem } from './offline-queue/types';
```

**Ensure `frontend/lib/offline-queue/index.ts` exports the same API:**
```typescript
// If not already present, ensure these exports exist:
export { addToQueue, getQueue, removeFromQueue, getQueueCount, clearQueue, incrementRetry };
export type { OfflineQueueItem };
```

**Update Service Worker to use IndexedDB directly** (optional enhancement):
```javascript
// sw.js — add IndexedDB read for background sync
async function syncOfflineQueue() {
  const db = await openDB('wellfond-offline', 1);
  const items = await db.getAll('queue');
  // ... process items
}
```

### Verification
1. Open app, go offline
2. Submit a ground log
3. Go back online
4. Verify the log syncs (check Network tab for POST to operations/logs)
5. Verify Service Worker can access the queue during background sync

---

## Issue H1: Idempotency Middleware Race Condition (TOCTOU)

### Root Cause (Confirmed)

**File:** `backend/apps/core/middleware.py`, lines 75-80  
**Code:**
```python
cached_response = caches["idempotency"].get(fingerprint)     # CHECK
if cached_response:
    return JsonResponse(cached_response["data"], status=cached_response["status"])

# WINDOW — another request can pass the check here

# Process request and cache response
response = self.get_response(request)
```

Two concurrent requests with the same idempotency key:
1. Request A: `get(fingerprint)` → None (not cached)
2. Request B: `get(fingerprint)` → None (not cached yet)
3. Request A: processes, `set(fingerprint, response)`
4. Request B: processes again (duplicate!)

### Impact
- Duplicate database inserts for concurrent requests with same idempotency key
- Defeats the "exactly-once delivery" guarantee required for PWA offline sync
- Low probability in practice (requires sub-millisecond concurrent requests) but violates the contract

### Fix

**Use Redis `SET NX` (set-if-not-exists) for atomic check-and-set:**

```python
# backend/apps/core/middleware.py

import hashlib
import json
import logging
from typing import Callable

from django.core.cache import caches
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


class IdempotencyMiddleware:
    """
    Ensures POST/PUT/PATCH/DELETE requests with same idempotency key
    return cached response for 24 hours.

    Uses Redis SET NX for atomic check-and-set to prevent TOCTOU race.
    """

    IDEMPOTENCY_REQUIRED_PATHS = [
        "/api/v1/operations/",
        "/api/v1/breeding/",
        "/api/v1/sales/",
        "/api/v1/finance/",
        "/api/v1/customers/",
        "/api/v1/compliance/",
        "/api/v1/dogs/",
        "/api/v1/users/",
    ]

    IDEMPOTENCY_EXEMPT_PATHS = [
        "/api/v1/auth/",
    ]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return self.get_response(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")

        if self._is_idempotency_required(request.path) and not idempotency_key:
            return JsonResponse(
                {
                    "error": "Idempotency key required",
                    "detail": f"{request.method} to {request.path} requires X-Idempotency-Key header",
                },
                status=400,
            )

        if not idempotency_key:
            return self.get_response(request)

        fingerprint = self._generate_fingerprint(request, idempotency_key)
        
        # ATOMIC: Check if key exists and set "processing" marker in one operation
        # Redis SET NX returns True only if the key did not exist
        idempotency_cache = caches["idempotency"]
        
        # First check for completed response (fast path)
        cached_response = idempotency_cache.get(fingerprint)
        if cached_response and cached_response.get("status") != "processing":
            response = JsonResponse(
                cached_response["data"],
                status=cached_response["status"],
            )
            response["Idempotency-Replay"] = "true"
            return response

        # Atomic lock: try to claim this request
        # Use add() which is SET NX equivalent — returns False if key exists
        if not idempotency_cache.add(fingerprint, {"status": "processing"}, timeout=30):
            # Another request is processing or already completed
            # Re-check for completed response
            cached_response = idempotency_cache.get(fingerprint)
            if cached_response and cached_response.get("status") != "processing":
                response = JsonResponse(
                    cached_response["data"],
                    status=cached_response["status"],
                )
                response["Idempotency-Replay"] = "true"
                return response
            # Still processing — wait briefly and return 409
            return JsonResponse(
                {"error": "Request already in progress"},
                status=409,
            )

        # We claimed the lock — process the request
        response = self.get_response(request)

        if 200 <= response.status_code < 300:
            try:
                idempotency_cache.set(
                    fingerprint,
                    {
                        "data": json.loads(response.content),
                        "status": response.status_code,
                    },
                    timeout=86400,
                )
            except json.JSONDecodeError:
                pass
        else:
            # Remove the processing marker on error
            idempotency_cache.delete(fingerprint)

        return response

    def _generate_fingerprint(self, request: HttpRequest, idempotency_key: str) -> str:
        user_id = (
            request.user.id
            if hasattr(request, "user") and request.user.is_authenticated
            else "anon"
        )
        data = f"{user_id}:{request.path}:{request.body.decode() if request.body else ''}:{idempotency_key}"
        return f"idempotency:{hashlib.sha256(data.encode()).hexdigest()}"

    def _is_idempotency_required(self, path: str) -> bool:
        if any(path.startswith(exempt) for exempt in self.IDEMPOTENCY_EXEMPT_PATHS):
            return False
        return any(path.startswith(p) for p in self.IDEMPOTENCY_REQUIRED_PATHS)
```

**Key change:** `cache.add(key, value, timeout)` is Django's equivalent of Redis `SET NX` — it returns `False` if the key already exists, atomically.

### Verification
```python
# Test: concurrent requests with same key
import threading
results = []

def make_request():
    # Same idempotency key
    response = client.post('/api/v1/operations/logs/in-heat/...', 
                          headers={'X-Idempotency-Key': 'test-key'})
    results.append(response.status_code)

threads = [threading.Thread(target=make_request) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

# Exactly one should succeed (201), others should get 200 (replay) or 409 (in-progress)
assert results.count(201) == 1
```

---

## Issue H2: `cancel_agreement` Audit Log Records Wrong `old_status`

### Root Cause (Confirmed)

**File:** `backend/apps/sales/services/agreement.py`, lines 589-601  
**Code:**
```python
with transaction.atomic():
    agreement.status = AgreementStatus.CANCELLED          # Line 590: set status
    agreement.cancelled_at = timezone.now()                # Line 591: set timestamp
    agreement.save(update_fields=[...])                    # Line 592: SAVE to DB

    AuditLog.objects.create(                               # Line 595: create audit log
        payload={
            "old_status": agreement.status,                # Line 597: READS status — already CANCELLED!
            "new_status": AgreementStatus.CANCELLED,       # Line 598: CANCELLED
        },
    )
```

At line 597, `agreement.status` is already `CANCELLED` because it was set at line 590 and saved at line 592. The audit log records `CANCELLED → CANCELLED` instead of the actual transition (e.g., `DRAFT → CANCELLED` or `SIGNED → CANCELLED`).

### Impact
- **Audit trail integrity compromised** — immutable audit log records incorrect state transition
- Compliance violation: audit trail should accurately reflect all state changes
- Affects any agreement cancellation in the system

### Fix

**Capture `old_status` before mutation:**

```python
@staticmethod
def cancel_agreement(
    agreement_id: UUID,
    cancelled_by: User,
    reason: str = "",
) -> bool:
    try:
        agreement = SalesAgreement.objects.get(id=agreement_id)
    except SalesAgreement.DoesNotExist:
        return False

    if not AgreementService.can_transition(agreement, AgreementStatus.CANCELLED):
        return False

    from django.utils import timezone

    # Capture state BEFORE mutation
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
                "old_status": old_status,              # ← Captured before mutation
                "new_status": AgreementStatus.CANCELLED,
                "reason": reason,
            },
        )

    logger.info(f"Agreement {agreement_id} cancelled by {cancelled_by.email}: {reason}")
    return True
```

### Verification
```python
# Create agreement in DRAFT status
agreement = SalesAgreementFactory(status=AgreementStatus.DRAFT)
AgreementService.cancel_agreement(agreement.id, user, "test reason")
log = AuditLog.objects.filter(resource_type="SalesAgreement").latest("created_at")
assert log.payload["old_status"] == "DRAFT"
assert log.payload["new_status"] == "CANCELLED"
```

---

## Issue H3: PDPA `check_blast_eligibility` and `is_consented` Are Placeholder Stubs

### Root Cause (Confirmed)

**File:** `backend/apps/compliance/services/pdpa.py`

**`check_blast_eligibility` (line 109):**
```python
return PDPAConsentCheckResponse(
    eligible_ids=customer_ids,  # ALL customers treated as eligible
    excluded_ids=[],
    eligible_count=len(customer_ids),
    excluded_count=0,
    exclusion_reason="PDPA consent check deferred to Phase 7 (Customer model)",
)
```

**`is_consented` (line 138):**
```python
# Placeholder - Phase 7 will implement actual check
return True  # Always returns True!
```

The `Customer` model exists at `backend/apps/customers/models.py` with `pdpa_consent = models.BooleanField(default=False)`. Phase 7 is marked complete in README. These stubs should have been replaced.

### Impact
- **PDPA compliance gap** — marketing blasts could be sent to opted-out customers
- Any code path using `is_consented()` bypasses consent enforcement
- Violates the project's core requirement: "Hard WHERE pdpa_consent=true filter at queryset level"

### Fix

**Replace placeholder stubs with actual implementations:**

```python
# backend/apps/compliance/services/pdpa.py

@staticmethod
def check_blast_eligibility(customer_ids: list[UUID]) -> PDPAConsentCheckResponse:
    """
    Check blast eligibility for customer list.
    Splits customers into eligible and excluded based on PDPA consent.
    """
    from apps.customers.models import Customer

    customers = Customer.objects.filter(id__in=customer_ids)
    
    eligible_ids = []
    excluded_ids = []
    
    for customer in customers:
        if customer.pdpa_consent:
            eligible_ids.append(customer.id)
        else:
            excluded_ids.append(customer.id)
    
    return PDPAConsentCheckResponse(
        eligible_ids=eligible_ids,
        excluded_ids=excluded_ids,
        eligible_count=len(eligible_ids),
        excluded_count=len(excluded_ids),
        exclusion_reason="PDPA consent not given" if excluded_ids else "",
    )

@staticmethod
def is_consented(customer_id: UUID) -> bool:
    """
    Check if customer has PDPA consent.
    Returns False if customer not found or consent not given.
    """
    from apps.customers.models import Customer
    
    try:
        customer = Customer.objects.get(id=customer_id)
        return customer.pdpa_consent
    except Customer.DoesNotExist:
        return False

@staticmethod
def count_consented_customers(entity_id: UUID) -> int:
    """Count customers with PDPA consent for entity."""
    from apps.customers.models import Customer
    return Customer.objects.filter(
        entity_id=entity_id,
        pdpa_consent=True,
    ).count()

@staticmethod
def count_opted_out_customers(entity_id: UUID) -> int:
    """Count customers opted out of PDPA for entity."""
    from apps.customers.models import Customer
    return Customer.objects.filter(
        entity_id=entity_id,
        pdpa_consent=False,
    ).count()
```

### Verification
```python
# Create customer with no consent
customer = CustomerFactory(pdpa_consent=False)
assert PDPAService.is_consented(customer.id) is False

# Create customer with consent
customer2 = CustomerFactory(pdpa_consent=True)
assert PDPAService.is_consented(customer2.id) is True

# Blast eligibility
result = PDPAService.check_blast_eligibility([customer.id, customer2.id])
assert result.eligible_count == 1
assert result.excluded_count == 1
assert customer.id in result.excluded_ids
```

---

## Issue H4: BFF Proxy CORS Allows All Origins with Credentials

### Root Cause (Confirmed)

**File:** `frontend/app/api/proxy/[...path]/route.ts`, lines 207-215  
**Code:**
```typescript
export async function OPTIONS(_request: NextRequest) {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',           // ← ALL origins
      'Access-Control-Allow-Credentials': 'true',   // ← With credentials
    },
  });
}
```

While modern browsers block `*` + `credentials` combination, this is still a security misconfiguration that:
1. May work in older browsers or non-browser HTTP clients
2. Signals incorrect CORS configuration
3. Could be exploited if the proxy is accessed programmatically

### Impact
- Potential credential theft via CORS bypass in edge cases
- Security audit finding

### Fix

**Use origin-aware CORS with allowlist:**

```typescript
// frontend/app/api/proxy/[...path]/route.ts

const ALLOWED_ORIGINS = [
  'https://wellfond.sg',
  'https://www.wellfond.sg',
  'http://localhost:3000',  // Dev only
];

function getCorsHeaders(request: NextRequest): Record<string, string> {
  const origin = request.headers.get('origin') || '';
  const isAllowed = ALLOWED_ORIGINS.includes(origin) || 
                    (process.env.NODE_ENV === 'development' && origin.startsWith('http://localhost'));

  return {
    'Access-Control-Allow-Origin': isAllowed ? origin : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-CSRFToken, X-Idempotency-Key',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '86400', // 24h preflight cache
  };
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(request),
  });
}
```

**Also add CORS headers to actual responses** (not just preflight):
```typescript
async function proxyRequest(request: NextRequest, method: string): Promise<NextResponse> {
  // ... existing code ...
  const response = new NextResponse(responseBody, { ... });
  
  // Add CORS headers to response
  const corsHeaders = getCorsHeaders(request);
  Object.entries(corsHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });
  
  return response;
}
```

### Verification
```bash
# Should work
curl -H "Origin: http://localhost:3000" -X OPTIONS http://localhost:3000/api/proxy/health
# Should return Access-Control-Allow-Origin: http://localhost:3000

# Should be rejected
curl -H "Origin: https://evil.com" -X OPTIONS http://localhost:3000/api/proxy/health
# Should NOT return Access-Control-Allow-Origin: https://evil.com
```

---

## Issue H5: Sessions Stored in Default Cache Instead of Dedicated Sessions Cache

### Root Cause (Confirmed)

**File:** `backend/apps/core/auth.py`, line 55  
**Code:**
```python
cache.set(
    cls.SESSION_KEY_PREFIX + session_key,
    session_data,
    timeout=int(cls.SESSION_DURATION.total_seconds()),
)
```

`cache.set()` uses Django's **default** cache backend. The configuration in `base.py`:
```python
CACHES = {
    "default": {"LOCATION": "redis://redis_cache:6379/0"},      # LRU eviction
    "sessions": {"LOCATION": "redis://redis_sessions:6379/0"},   # Dedicated
    "idempotency": {"LOCATION": "redis://redis_idempotency:6379/0"},
}
```

The `default` cache uses `allkeys-lru` eviction. Under memory pressure, session keys get evicted, causing unexpected logouts.

### Impact
- Random logouts for ground staff during high-usage periods
- Session data loss when cache is under memory pressure
- Particularly problematic for PWA users who may have long-lived sessions

### Fix

**Use `caches["sessions"]` for all session operations:**

```python
# backend/apps/core/auth.py

class SessionManager:
    SESSION_KEY_PREFIX = "session:"
    SESSION_DURATION = timedelta(minutes=15)
    REFRESH_DURATION = timedelta(days=7)

    @classmethod
    def _get_session_cache(cls):
        """Get the dedicated sessions cache backend."""
        from django.core.cache import caches
        return caches["sessions"]

    @classmethod
    def create_session(cls, user: User, request: HttpRequest) -> tuple[str, str]:
        session_key = str(uuid.uuid4())
        csrf_token = get_token(request)

        session_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "entity_id": str(user.entity_id) if user.entity_id else None,
            "csrf_token": csrf_token,
        }

        session_cache = cls._get_session_cache()
        session_cache.set(
            cls.SESSION_KEY_PREFIX + session_key,
            session_data,
            timeout=int(cls.SESSION_DURATION.total_seconds()),
        )

        refresh_key = f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}"
        session_cache.set(
            refresh_key, user.id, timeout=int(cls.REFRESH_DURATION.total_seconds())
        )

        return session_key, csrf_token

    @classmethod
    def get_session(cls, session_key: str) -> Optional[dict]:
        return cls._get_session_cache().get(cls.SESSION_KEY_PREFIX + session_key)

    @classmethod
    def extend_session(cls, session_key: str, user: User) -> None:
        session_data = cls.get_session(session_key)
        if session_data:
            cls._get_session_cache().set(
                cls.SESSION_KEY_PREFIX + session_key,
                session_data,
                timeout=int(cls.SESSION_DURATION.total_seconds()),
            )

    @classmethod
    def delete_session(cls, session_key: str) -> None:
        session_cache = cls._get_session_cache()
        session_cache.delete(cls.SESSION_KEY_PREFIX + session_key)
        session_cache.delete(f"{cls.SESSION_KEY_PREFIX}refresh:{session_key}")
```

### Verification
```python
# Verify sessions use the correct cache
from django.core.cache import caches
session_cache = caches["sessions"]
# Create session, verify it's in session_cache, not default cache
```

---

## Issue H6: `list_logs` Endpoint Has N+1 Query Problem

### Root Cause (Confirmed)

**File:** `backend/apps/operations/routers/logs.py`, lines 285-370  
**Code:** 7 separate queries, each with `order_by("-created_at")[:limit]`:

```python
for log in dog.heat_logs.order_by("-created_at")[:limit]:       # Query 1
for log in dog.mating_logs.order_by("-created_at")[:limit]:     # Query 2
for log in dog.whelping_logs.order_by("-created_at")[:limit]:   # Query 3
for log in dog.health_obs_logs.order_by("-created_at")[:limit]: # Query 4
for log in dog.weight_logs.order_by("-created_at")[:limit]:     # Query 5
for log in dog.nursing_flag_logs.order_by("-created_at")[:limit]: # Query 6
for log in dog.not_ready_logs.order_by("-created_at")[:limit]:  # Query 7
```

Then all logs are merged in Python and re-sorted. The `limit` applies per-type, not globally — a dog with 50 heat logs and 50 weight logs returns 100 entries.

### Impact
- 7 database queries per API call
- Python-side sorting of potentially large lists
- Limit applies incorrectly (per-type, not global)

### Fix

**Use `union()` for efficient single-query approach:**

```python
from django.db.models import Value, CharField, UUIDField, DateTimeField
from django.db.models.functions import Cast

@router.get("/{dog_id}", response=LogsListResponse)
def list_logs(request, dog_id: UUID, limit: int = 50):
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")

    _check_permission(request, dog)

    # Single query using union of all log types
    heat_logs = InHeatLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('in_heat', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    mating_logs = MatedLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('mated', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    whelped_logs = WhelpedLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('whelped', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    health_logs = HealthObsLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('health_obs', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    weight_logs = WeightLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('weight', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    nursing_logs = NursingFlagLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('nursing_flag', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    not_ready_logs = NotReadyLog.objects.filter(dog_id=dog_id).values(
        'id', 'created_at'
    ).annotate(
        log_type=Value('not_ready', output_field=CharField()),
        dog_name=Value(dog.name, output_field=CharField()),
    )

    # Union all and sort in DB
    all_logs = heat_logs.union(
        mating_logs, whelped_logs, health_logs,
        weight_logs, nursing_logs, not_ready_logs
    ).order_by('-created_at')[:limit]

    results = [
        {
            "id": str(log['id']),
            "type": log['log_type'],
            "dog_id": str(dog_id),
            "dog_name": log['dog_name'],
            "created_at": log['created_at'].isoformat(),
            "created_by_name": None,  # Would need join for this
        }
        for log in all_logs
    ]

    return {"count": len(results), "results": results}
```

**Alternative (simpler, keeps created_by):** Just fix the limit to be global:
```python
# Collect all, then apply global limit
logs = []
for log in dog.heat_logs.select_related('created_by').all():
    logs.append({...})
# ... same for other types ...
logs.sort(key=lambda x: x["created_at"], reverse=True)
return {"count": len(logs[:limit]), "results": logs[:limit]}
```

### Verification
```bash
# Check query count with django-debug-toolbar or connection.queries
# Should be 1-2 queries instead of 7
```

---

## Issue H7: `create_in_heat_log` Returns HTTP 200 via `HttpError`

### Root Cause (Confirmed)

**File:** `backend/apps/operations/routers/logs.py`, line 105  
**Code:**
```python
if _check_idempotency(request, str(dog_id), "in_heat"):
    raise HttpError(200, "Already processed")
```

`HttpError` is Django Ninja's error class. Raising it with status 200 is semantically incorrect — it's not an error. Additionally, the idempotency **middleware** already handles replay at the middleware level, making this router-level check redundant and conflicting.

### Impact
- Django Ninja wraps the response in its error format even for 200
- Double idempotency check (middleware + router) causes confusion
- API contract violation: clients expect 200 to be a success response, not an error

### Fix

**Option A (Preferred): Remove router-level idempotency check** — middleware handles it:
```python
@router.post("/in-heat/{dog_id}", response=InHeatResponse)
def create_in_heat_log(request, dog_id: UUID, data: InHeatCreate):
    """Create an in-heat log with Draminski reading."""
    user = _get_current_user(request)
    if not user:
        raise HttpError(401, "Authentication required")

    # REMOVED: _check_idempotency call — middleware handles this
    
    try:
        dog = Dog.objects.get(id=dog_id)
    except Dog.DoesNotExist:
        raise HttpError(404, "Dog not found")
    # ... rest of handler
```

**Option B (If keeping router-level check):** Return proper response:
```python
if already_processed:
    from django.http import JsonResponse
    return JsonResponse({"status": "already_processed"}, status=200)
```

**Recommendation:** Option A — remove all `_check_idempotency` calls from router handlers. The middleware handles it correctly at the right layer.

### Verification
```bash
# Send same request twice with same idempotency key
# First: 201 Created
# Second: 200 with Idempotency-Replay header (from middleware)
```

---

## Issue H8: `AgreementLineItem` Missing `line_total` and `gst_amount` Properties

### Root Cause (Confirmed)

**File:** `backend/apps/sales/models.py` — `AgreementLineItem` class  
**Referenced by:**
- `backend/apps/compliance/services/nparks.py:272` — `item.line_total`
- `backend/apps/sales/services/agreement.py:625` — `item.line_total`
- `backend/apps/sales/services/agreement.py:626` — `item.gst_amount`
- `backend/apps/sales/tests/factories.py:78` — factory defines it (test-only)

The model has `price` and `gst_component` but no computed properties.

### Impact
- `calculate_totals()` in agreement service will crash
- NParks puppy movement will crash
- Any code accessing line item totals will fail

### Fix

**Add properties to `AgreementLineItem`:**

```python
# backend/apps/sales/models.py — add to AgreementLineItem class

class AgreementLineItem(models.Model):
    # ... existing fields ...

    @property
    def line_total(self) -> Decimal:
        """Total amount for this line item (price only)."""
        return self.price

    @property
    def gst_amount(self) -> Decimal:
        """GST component for this line item."""
        return self.gst_component

    def __str__(self) -> str:
        return f"{self.dog.name} - ${self.price}"
```

**Note:** This is the same fix as C1. One property addition fixes both C1 and H8.

### Verification
```python
item = AgreementLineItem(price=Decimal("1000.00"), gst_component=Decimal("90.00"))
assert item.line_total == Decimal("1000.00")
assert item.gst_amount == Decimal("90.00")
```

---

## Issue H9: `Vaccination.save()` Uses Silent `ImportError` Catch

### Root Cause (Confirmed)

**File:** `backend/apps/operations/models.py`, lines 282-286  
**Code:**
```python
def save(self, *args, **kwargs):
    try:
        from .services.vaccine import calc_vaccine_due
        self.due_date = calc_vaccine_due(self.dog, self.vaccine_name, self.date_given)
    except ImportError:
        pass  # Service not yet available, skip auto-calculation
```

The service file exists at `backend/apps/operations/services/vaccine.py` and the `__init__.py` is present. The `ImportError` will never be raised in the current codebase. However, this pattern:
1. Silently swallows any `ImportError` in the dependency chain
2. Could mask a broken import (e.g., missing dependency)
3. Leaves `due_date` as `None` without any indication

### Impact
- If any dependency of `vaccine.py` fails to import, the error is silently swallowed
- `due_date` will be `None`, causing `_calculate_status()` to return `UP_TO_DATE` incorrectly
- Vaccines could appear up-to-date when they're actually overdue

### Fix

**Remove the try/except — let import errors propagate:**

```python
def save(self, *args, **kwargs):
    """Auto-calculate due date based on vaccine type."""
    from .services.vaccine import calc_vaccine_due
    self.due_date = calc_vaccine_due(self.dog, self.vaccine_name, self.date_given)
    self.status = self._calculate_status()
    super().save(*args, **kwargs)
```

If circular import protection is truly needed (it's not in this case), use lazy import:
```python
def save(self, *args, **kwargs):
    """Auto-calculate due date based on vaccine type."""
    import importlib
    vaccine_service = importlib.import_module('.services.vaccine', package='apps.operations')
    self.due_date = vaccine_service.calc_vaccine_due(self.dog, self.vaccine_name, self.date_given)
    self.status = self._calculate_status()
    super().save(*args, **kwargs)
```

### Verification
```python
# Create vaccination — due_date should be calculated
vacc = Vaccination(dog=dog, vaccine_name="DHPP", date_given=date(2026, 1, 1))
vacc.save()
assert vacc.due_date is not None  # Should be 2026-01-22 (21 days)
assert vacc.status == "UP_TO_DATE"  # or DUE_SOON/OVERDUE based on current date
```

---

## Issue H10: `IntercompanyTransfer.save()` Missing Atomicity

### Root Cause (Confirmed)

**File:** `backend/apps/finance/models.py`, lines 161-191  
**Code:**
```python
def save(self, *args, **kwargs):
    is_new = self._state.adding
    super().save(*args, **kwargs)      # Save transfer record

    if is_new:
        Transaction.objects.create(    # First transaction — succeeds
            type=TransactionType.EXPENSE,
            ...
        )
        Transaction.objects.create(    # Second transaction — CAN FAIL
            type=TransactionType.REVENUE,
            ...
        )
```

If the second `Transaction.objects.create()` fails (validation error, DB constraint, network issue), the transfer exists with only one balancing transaction — violating the debit=credit invariant.

### Impact
- Unbalanced intercompany transfers in financial records
- P&L reports will show mismatched amounts
- GST reports could be incorrect

### Fix

**Wrap in `transaction.atomic()`:**

```python
def save(self, *args, **kwargs):
    """Override save to create balanced transaction records."""
    from django.db import transaction as db_transaction

    is_new = self._state.adding

    with db_transaction.atomic():
        super().save(*args, **kwargs)

        if is_new:
            from_entity = self.from_entity
            to_entity = self.to_entity
            from_entity_name = getattr(from_entity, 'name', str(from_entity.id))[:50]
            to_entity_name = getattr(to_entity, 'name', str(to_entity.id))[:50]

            Transaction.objects.create(
                type=TransactionType.EXPENSE,
                amount=self.amount,
                entity=from_entity,
                gst_component=Decimal("0.00"),
                date=self.date,
                category=TransactionCategory.OTHER,
                description=f"Intercompany transfer to {to_entity_name}: {self.description}"[:200],
            )
            Transaction.objects.create(
                type=TransactionType.REVENUE,
                amount=self.amount,
                entity=to_entity,
                gst_component=Decimal("0.00"),
                date=self.date,
                category=TransactionCategory.OTHER,
                description=f"Intercompany transfer from {from_entity_name}: {self.description}"[:200],
            )
```

### Verification
```python
# Create transfer — both transactions should exist
transfer = IntercompanyTransfer.objects.create(
    from_entity=entity_a, to_entity=entity_b,
    amount=Decimal("1000.00"), date=date.today(),
    description="Test", created_by=user,
)
txns = Transaction.objects.filter(date=date.today())
assert txns.count() == 2
assert txns.filter(type="EXPENSE").first().amount == Decimal("1000.00")
assert txns.filter(type="REVENUE").first().amount == Decimal("1000.00")
```

---

## Execution Priority Matrix

| Priority | Issue | Fix Effort | Risk if Deferred |
|----------|-------|-----------|-----------------|
| **P0** | C1 + H8 (line_total) | 5 min | NParks + P&L crashes |
| **P0** | C2 (follow_up_required) | 15 min | NParks vet doc crashes |
| **P0** | C3 (offline queue) | 30 min | PWA offline completely broken |
| **P0** | H2 (audit log old_status) | 5 min | Audit trail integrity |
| **P0** | H3 (PDPA stubs) | 15 min | Compliance violation |
| **P0** | H10 (atomicity) | 5 min | Financial data integrity |
| **P1** | H5 (session cache) | 10 min | Random logouts |
| **P1** | H1 (idempotency race) | 20 min | Duplicate records |
| **P1** | H4 (CORS) | 10 min | Security finding |
| **P1** | H7 (HttpError 200) | 5 min | API contract violation |
| **P1** | H9 (silent ImportError) | 2 min | Silent vaccine miscalc |
| **P1** | H6 (N+1 queries) | 30 min | Performance |

**Total estimated fix time: ~2.5 hours**

---

## Implementation Order

```
Phase 1: Critical Fixes (C1, C2, C3) — 30 min
  ├─ C1+H8: Add line_total/gst_amount properties to AgreementLineItem
  ├─ C2: Add follow_up_required field to HealthRecord + migration
  └─ C3: Replace offline-queue.ts with IndexedDB re-export

Phase 2: High Data Integrity (H2, H3, H10) — 30 min
  ├─ H2: Capture old_status before mutation in cancel_agreement
  ├─ H3: Implement actual PDPA consent checking
  └─ H10: Wrap IntercompanyTransfer.save() in atomic block

Phase 3: High Security & Correctness (H1, H4, H5, H7, H9) — 45 min
  ├─ H1: Atomic idempotency with cache.add()
  ├─ H4: Origin-aware CORS in BFF proxy
  ├─ H5: Use caches["sessions"] for session storage
  ├─ H7: Remove router-level idempotency checks
  └─ H9: Remove silent ImportError catch

Phase 4: High Performance (H6) — 30 min
  └─ H6: Consolidate list_logs to union query

Phase 5: Verification — 30 min
  ├─ Run full test suite
  ├─ Verify NParks generation works end-to-end
  ├─ Verify offline queue syncs correctly
  └─ Verify PDPA consent enforcement
```

---

## Migration Requirements

### New Migration: `operations/0003_add_follow_up_to_health_record.py`
```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('operations', '0002_alter_healthrecord_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='healthrecord',
            name='follow_up_required',
            field=models.BooleanField(default=False, help_text='Whether follow-up veterinary treatment is required'),
        ),
        migrations.AddField(
            model_name='healthrecord',
            name='follow_up_date',
            field=models.DateField(blank=True, null=True, help_text='Scheduled follow-up date'),
        ),
    ]
```

---

## Risk Assessment

| Fix | Breaking Change Risk | Rollback Strategy |
|-----|---------------------|-------------------|
| C1+H8 (properties) | None — additive | Remove properties |
| C2 (new field) | None — additive, default=False | Remove field |
| C3 (offline queue) | Medium — changes PWA behavior | Revert to localStorage version |
| H2 (audit log) | None — fixes incorrect data | No rollback needed |
| H3 (PDPA) | Low — changes blast eligibility | Revert to placeholder |
| H1 (idempotency) | Low — changes locking behavior | Revert to non-atomic |
| H4 (CORS) | Low — may break non-browser clients | Revert to * origin |
| H5 (session cache) | Low — changes cache backend | Revert to default cache |
| H6 (queries) | Low — changes SQL generation | Revert to N+1 queries |
| H7 (HttpError) | None — removes redundant code | Add back |
| H9 (ImportError) | None — removes dead code | Add back try/except |
| H10 (atomicity) | None — adds safety | Remove atomic wrapper |

---

*End of Remediation Plan*
