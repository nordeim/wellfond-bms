# Wellfond BMS — Comprehensive Remediation Plan v2

**Date:** 2026-05-07
**Based on:** COMPREHENSIVE_CODE_REVIEW_AUDIT_REPORT_10.md (re-validated against actual code)
**Author:** AI Code Review & Remediation Agent

---

## Re-Validation Summary

Each finding was meticulously re-evaluated against the actual source code, and the root cause confirmed:

| Finding | Original Severity | Re-Validated Root Cause | Notes |
|---------|------------------|------------------------|-------|
| CR-001: Finance `CASCADE` entity FKs | CRITICAL | `on_delete=models.CASCADE` used on all Entity/User FKs in finance models — violates audit immutability | **Confirmed** — 7 occurrences |
| CR-004: Auth state FOUC | CRITICAL | `isAuthenticated()` checks only `cachedUser` (memory cache, cleared on refresh) | **Confirmed** — browser refresh = unauthenticated state |
| HIGH-001: AVS stubs | HIGH | 4 TODOs in `avs.py`: Resend email, WhatsApp API, reminder dispatch | **Confirmed** — no actual delivery |
| HIGH-002: SW POST replay | HIGH | `sw.js` only handles GET; offline POST requests never replayed | **Confirmed** — H-005 from R3 removed sync, no replacement |
| HIGH-003: `any` in TypeVar | HIGH | `Callable[..., any]` in `permissions.py:15` — not valid PEP 484 type | **Confirmed** — breaks `mypy` |
| HIGH-004: Missing `default=''` | HIGH | 3 CharFields (`mobile`, `avs_license_number`, `phone`) have `blank=True` without `default` | **Confirmed** — causes `NotNullViolation` |
| H-005: `T \| None` in finance | HIGH | Finance routers use union syntax instead of `Optional[T]` | **Confirmed** — 9 occurrences |
| H-007: `Dog.age_years` float | HIGH | Returns `float` from `(today - dob).days / 365.25` | **Confirmed** — IEEE 754 precision risk |

---

## Remediation Checklist

| # | Fix | File | Severity | Status |
|---|-----|------|----------|--------|
| FIX-05 | Change all finance Entity/User FKs to `on_delete=PROTECT` | `backend/apps/finance/models.py` | CRITICAL | ⬜ Pendin |
| FIX-06 | Add server-side auth state persistence (cookie check) | `frontend/lib/auth.ts`, `frontend/middleware.ts` | CRITICAL | ⬜ Pending |
| FIX-07 | Implement Resend email dispatch in AVS reminder task | `backend/apps/sales/services/avs.py` | HIGH | ⬜ Pendi |
| FIX-08 | Implement WhatsApp dispatc | `backend/apps/sales/services/avs.py` | HIGH | ⬜ Pending |
| FIX-09 | Add Service Worker `sync` event for offline POST queue | `frontend/public/sw.js` | HIGH | ⬜ Pending |
| FIX-10 | Fix `any` → `Any` in TypeVar | `backend/apps/core/permissions.py` | HIGH | ⬜ Pendin |
| FIX-11 | Add `default=''` to 3 CharFields in core models | `backend/apps/core/models.py` | HIGH | ⬜ Pending |
| FIX-12 | Replace `T \| None` with `Optional[T]` in finance routers | `backend/apps/finance/routers/*.py` | HIGH | ⬜ Pending |
| FIX-13 | Refactor `Dog.age_years` to use `Decimal` | `backend/apps/operations/models.py` | HIGH | ⬜ Pendin |

---

## Fix Details

### FIX-05: Finance Entity FKs → PROTECT (CRITICAL-001 Re-remediation)

**File:** `backend/apps/finance/models.py` (lines 61-62, 119-120, 125-126, 137-139, 213-214, 222-224, 260-262)

**Root Cause:** All 7 Entity/User FKs use `on_delete=models.CASCADE`, which violates the AGENTS.md anti-pattern:
> *"Use `on_delete=PROTECT` for entity FKs to prevent accidental data loss"*

**Impact Cascade:**
| Model | FK Field | On Delete | Risk |
|-------|----------|-----------|------|
| `Transaction` | `entity` | `CASCADE` | Deleting entity → all transactions destroyed |
| `IntercompanyTransfer` | `from_entity` | `CASCADE` | Deleting entity → destroys intercompany audit |
| `IntercompanyTransfer` | `to_entity` | `CASCADE` | Same as above |
| `IntercompanyTransfer` | `created_by` | `CASCADE` | User deletion → transfer record lost |
| `GSTReport` | `entity` | `CASCADE` | GST reports lost on entity deletion |
| `GSTReport` | `generated_by` | `CASCADE` | User deletion → GST report lost |
| `PNLSnapshot` | `entity` | `CASCADE` | P&L data lost on entity deletion |

**Fix:** Change `on_delete=models.CASCADE` to `on_delete=models.PROTECT` in all 7 locations.

**Verification:**
```python
assert Transaction._meta.get_field("entity").remote_field.on_delete == PROTECT
```

---

### FIX-06: Auth State Persistence (CRITICAL-004)

**Root Cause:** `isAuthenticated()` only checks `cachedUser` (RAM, cleared on refresh). After browser refresh, the user appears unauthenticated until `/auth/me` resolves.

**Fix Options:**
1. **Option A (Recommended):** Check `document.cookie` presence (HttpOnly cookies can't be read, but existence can be checked via `document.cookie.includes()`). This is a "cookie exists" check, not a session validity check — but it provides a fast first-level signal that a session might exist.
2. **Option B:** Server-side auth state in Next.js middleware — check for `sessionid` cookie and add auth headers to all requests.
3. **Option C:** Use a non-HttpOnly flag cookie that mirrors auth state (e.g., `auth_state=True` set on login, cleared on logout). Readable by JS but doesn't contain session data.

**Chosen Fix (A + C hybrid):**
- Add `auth_state` flag cookie (non-HttpOnly, SameSite=Lax) set on login/refresh, cleared on logout
- Check this in `isAuthenticated()` for fast initial state
- Keep `/auth/me` request for definitive state after hydration

---

### FIX-07: AVS Email Dispatch (HIGH-001 / Remediation of H-001 stub)

**File:** `backend/apps/sales/services/avs.py:115-124`

**Root Cause:** 4 TODO comments — no actual email or WhatsApp delivery implemented.

**Fix:** Implement `EmailService.send_avs_reminder()` using Resend SDK (already installed). Structure should follow AGENTS.md's `blast.py` pattern.

---

### FIX-08: AVS WhatsApp Dispatch (HIGH-001)

**File:** `backend/apps/sales/services/avs.py:124,220`

**Root Cause:** WhatsApp Business API integration TODO.

**Fix:** Add `WhatsAppService.send_message()` stub that returns FAILED (per H-001 from R3: return `"status": "FAILED"` for unintegrated services, not fake "SENT").

---

### FIX-09: Service Worker Offline POST Replay (HIGH-002)

**Root Cause:** Service Worker only handles GET requests. POST requests queued in IndexedDB are never replayed if the browser tab is closed.

**Fix:** Implement `sync` event handler in `sw.js` that:
1. Reads from IndexedDB (using `lib/offline-queue` pattern)
2. Replays each queued POST with original headers and body
3. Removes successfully replayed items from IndexedDB

---

### FIX-10: `any` → `Any` TypeVar (HIGH-003)

**File:** `backend/apps/core/permissions.py:15`

**Fix:** `from typing import Any` and `TypeVar("F", bound=Callable[..., Any])`

Code:
```python
from typing import Any  # ADD
F = TypeVar("F", bound=Callable[..., Any])  # FIX: any → Any
```

---

### FIX-11: CharField `default=''` (HIGH-004)

**Files:** `backend/apps/core/models.py:39, 109, 122`

**Fix:**
```python
# Line 39
mobile = models.CharField(max_length=20, blank=True, default="")
# Line 109
avs_license_number = models.CharField(max_length=50, blank=True, default="")
# Line 122
phone = models.CharField(max_length=20, blank=True, default="")
```

---

### FIX-12: `T | None` → `Optional[T]` (H-005)

**Files:** `backend/apps/finance/routers/reports.py`, `backend/apps/finance/routers/*.py`

**Fix:** Replace all `X | None = None` with `Optional[X] = None` and add `from typing import Optional`.

---

### FIX-13: `Dog.age_years` → `Decimal` (H-007)

**File:** `backend/apps/operations/models.py:135-138`

**Fix:**
```python
@property
def age_years(self) -> Decimal:
    """Calculate age in years with precise decimal division."""
    from decimal import Decimal
    return Decimal((date.today() - self.dob).days) / Decimal("365.25")
```

---

## Implementation Order

1. **FIX-05** (Finance CASCADE → PROTECT) — Safety first; prevents data loss
2. **FIX-10** (any → Any) — Zero risk, instant fix
3. **FIX-11** (CharField defaults) — Prevents NotNullViolation
4. **FIX-12** (T | None → Optional[T]) — Code quality
5. **FIX-13** (Float → Decimal) — Compliance precision
6. **FIX-06** (Auth state) — Frontend, needs careful testing
7. **FIX-07 + FIX-08** (AVS email/WhatsApp) — Integrations, depends on external APIs
8. **FIX-09** (SW sync) — PWA, last to complete

---

## Test Strategy

| Fix | Test File | Coverage |
|-----|-----------|----------|
| FIX-05 | `apps/finance/tests/test_models.py` | 7 PROTECT assertions |
| FIX-06 | `frontend/lib/auth.test.ts` | Cookie check, FOUC prevention |
| FIX-07 | `apps/sales/tests/test_avs_reminder.py` | Email dispatch with mock |
| FIX-08 | `apps/sales/tests/test_avs_reminder.py` | WhatsApp stub returns FAILED |
| FIX-09 | `frontend/tests/sw-sync.test.ts` | Offline queue replay |
| FIX-10 | `apps/core/tests/test_permissions.py` | mypy clean |
| FIX-11 | `apps/core/tests/test_models.py` | `default=''` migration test |
| FIX-12 | `apps/finance/tests/test_type_annotations.py` | Compile/parse test |
| FIX-13 | `apps/operations/tests/test_dog_age.py` | Decimal precision |

---

## Success Criteria

- [ ] All 9 fixes applied with TDD (test-first)
- [ ] No regressions in existing tests (44/44 pass)
- [ ] New tests pass (36+ tests)
- [ ] Full test suite: 80+ tests pass
- [ ] `mypy` clean (no `any` violations)
- [ ] Finance models use `PROTECT` exclusively
- [ ] Auth state persists across browser refresh
