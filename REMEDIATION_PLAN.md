# Wellfond BMS Remediation Plan

**Date:** April 29, 2026  
**Status:** Ready for Execution  
**Approach:** Test-Driven Development (TDD)

---

## Executive Summary

This plan addresses **4 confirmed valid issues** from the code audit:

| Issue | File | Severity | TDD Phase |
|-------|------|----------|-----------|
| Hardcoded GST logic | `agreement.py:66` | High | Phase 1 |
| Async/sync mismatch | `stream.py:165` | High | Phase 2 |
| Missing rate limiting | `auth.py` routers | High | Phase 3 |
| Dead code | `permissions.py:236` | Medium | Phase 4 |

---

## Phase 1: GST Calculation Fix

### Issue
Hardcoded `entity.code.upper() == "THOMSON"` instead of using `entity.gst_rate` field.

### TDD Cycle

**Step 1.1: Write Failing Test**
```python
# backend/apps/sales/tests/test_gst_fix.py
import pytest
from decimal import Decimal
from apps.core.models import Entity
from apps.sales.services.agreement import AgreementService

@pytest.mark.django_db
class TestGSTCalculation:
    def test_extract_gst_uses_gst_rate_field(self):
        """Test that GST extraction uses entity.gst_rate, not hardcoded name."""
        # Create entity with 0% GST but different name
        entity = Entity.objects.create(
            name="Test Entity",
            code="TESTZERO",
            gst_rate=Decimal("0.00")  # 0% GST
        )
        
        price = Decimal("109.00")
        gst = AgreementService.extract_gst(price, entity)
        
        # Should return 0.00 because gst_rate=0, not because of hardcoded name
        assert gst == Decimal("0.00"), "Should use gst_rate field, not hardcoded name"
    
    def test_extract_gst_for_9_percent_entity(self):
        """Test normal 9% GST calculation."""
        entity = Entity.objects.create(
            name="Holdings",
            code="HOLDINGS",
            gst_rate=Decimal("0.09")
        )
        
        price = Decimal("109.00")
        gst = AgreementService.extract_gst(price, entity)
        
        # GST = 109 * 9 / 109 = 9.00
        assert gst == Decimal("9.00"), "Should calculate GST correctly for 9% rate"
```

**Step 1.2: Implement Fix**
```python
# backend/apps/sales/services/agreement.py:50-71
@staticmethod
def extract_gst(price: Decimal, entity: Entity) -> Decimal:
    """
    Extract GST component from price using Singapore GST formula.
    Formula: price * 9 / 109, rounded to 2 decimals (HALF_UP)
    Uses entity.gst_rate field (0.00 for exempt entities).
    """
    # Use gst_rate field from entity (0.00 for exempt, 0.09 for standard)
    if entity.gst_rate == Decimal("0.00"):
        return Decimal("0.00")
    
    # Calculate GST using the entity's rate
    # Formula: price * rate / (1 + rate)
    rate = entity.gst_rate
    divisor = Decimal("1") + rate
    gst = price * rate / divisor
    
    return gst.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

**Step 1.3: Verify Fix**
- Run `pytest backend/apps/sales/tests/test_gst_fix.py -v`
- All tests should pass
- Verify Thomson entity still works (gst_rate should be 0.00)

---

## Phase 2: Async/Sync Mismatch Fix

### Issue
`_generate_dog_alert_stream()` uses `asyncio.to_thread()` instead of `sync_to_async(thread_sensitive=True)`.

### TDD Cycle

**Step 2.1: Write Failing Test**
```python
# backend/apps/operations/tests/test_sse_async.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from apps.operations.routers.stream import _generate_dog_alert_stream

@pytest.mark.asyncio
@pytest.mark.django_db
class TestSSEAsyncHandling:
    @patch('apps.operations.routers.stream.asyncio.to_thread')
    @patch('apps.operations.routers.stream.sync_to_async')
    async def test_dog_alert_stream_uses_sync_to_async(self, mock_sync_to_async, mock_to_thread):
        """Test that _generate_dog_alert_stream uses sync_to_async, not asyncio.to_thread."""
        # Mock sync_to_async to return an async function
        async def mock_async_func(*args, **kwargs):
            return []
        mock_sync_to_async.return_value = mock_async_func
        
        # Start the generator
        gen = _generate_dog_alert_stream(
            dog_id="test-dog-id",
            user_id="test-user-id",
            entity_id="test-entity-id",
            user_role="admin"
        )
        
        # Try to get first result (will timeout or error)
        try:
            await asyncio.wait_for(gen.__anext__(), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        
        # Verify sync_to_async was called (not asyncio.to_thread)
        mock_sync_to_async.assert_called_once()
        mock_to_thread.assert_not_called()
```

**Step 2.2: Implement Fix**
```python
# backend/apps/operations/routers/stream.py:149-172
async def _generate_dog_alert_stream(
    dog_id: str,
    user_id: str,
    entity_id: str,
    user_role: str,
) -> AsyncGenerator[str, None]:
    """Async generator for dog-specific SSE events."""
    import time

    last_event_id = 0

    while True:
        try:
            # Get pending alerts using sync_to_async for proper thread handling
            # CHANGED: sync_to_async instead of asyncio.to_thread
            alerts = await sync_to_async(get_pending_alerts, thread_sensitive=True)(
                user_id=user_id,
                entity_id=entity_id,
                role=user_role,
                since_id=last_event_id,
                dog_id=dog_id,
            )
            # ... rest of function unchanged
```

**Step 2.3: Verify Fix**
- Run `pytest backend/apps/operations/tests/test_sse_async.py -v`
- Verify both `_generate_alert_stream` and `_generate_dog_alert_stream` use same pattern

---

## Phase 3: Rate Limiting Implementation

### Issue
No rate limiting on `/login`, `/refresh`, `/csrf` endpoints.

### TDD Cycle

**Step 3.1: Write Failing Test**
```python
# backend/apps/core/tests/test_rate_limit.py
import pytest
from django.test import Client
from django.core.cache import cache
from apps.core.models import User, Entity

@pytest.mark.django_db
class TestRateLimiting:
    def setup_method(self):
        self.client = Client()
        cache.clear()
        
        self.entity = Entity.objects.create(
            name="Test Entity",
            code="TEST"
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            role="admin",
            entity=self.entity
        )
    
    def test_login_rate_limit_blocks_after_5_attempts(self):
        """Test that login endpoint rate limits after 5 attempts."""
        # Make 5 failed login attempts
        for i in range(5):
            response = self.client.post(
                '/api/v1/auth/login',
                {'email': 'test@example.com', 'password': 'wrong'},
                content_type='application/json'
            )
            # Should get 401 for wrong password
            assert response.status_code == 401
        
        # 6th attempt should be rate limited
        response = self.client.post(
            '/api/v1/auth/login',
            {'email': 'test@example.com', 'password': 'wrong'},
            content_type='application/json'
        )
        # Should get 429 Too Many Requests
        assert response.status_code == 429
        assert 'Rate limit exceeded' in response.content.decode()
```

**Step 3.2: Implement Fix**

First, verify django-ratelimit is installed:
```bash
pip install django-ratelimit
```

Update auth router:
```python
# backend/apps/core/routers/auth.py
from ninja import Router
from django_ratelimit.decorators import ratelimit
from ninja.decorators import decorate

router = Router(tags=["auth"])

def apply_rate_limit(func):
    """Decorator to apply rate limiting to auth endpoints."""
    return decorate(ratelimit(key='ip', rate='5/m', method=['POST']))(func)

@router.post("/login")
@apply_rate_limit
def login(request, data: LoginRequest):
    """Login endpoint with rate limiting: 5 attempts per minute per IP."""
    ...

@router.post("/refresh")
@apply_rate_limit
def refresh(request):
    """Refresh endpoint with rate limiting."""
    ...

@router.get("/csrf")
@decorate(ratelimit(key='ip', rate='10/m', method=['GET']))
def get_csrf(request):
    """CSRF endpoint with rate limiting."""
    ...
```

Add rate limit exception handler to `api.py`:
```python
# backend/api.py
from ninja import NinjaAPI
from django.http import JsonResponse

api = NinjaAPI()

@api.exception_handler(Ratelimited)
def handle_rate_limit(request, exc):
    """Return 429 when rate limit exceeded."""
    return JsonResponse(
        {"error": "Rate limit exceeded", "detail": "Too many requests. Please try again later."},
        status=429
    )
```

**Step 3.3: Verify Fix**
- Run `pytest backend/apps/core/tests/test_rate_limit.py -v`
- Manual test: rapid-fire login requests from same IP should get blocked

---

## Phase 4: Dead Code Removal

### Issue
`require_admin_debug` function exists but is never used.

### TDD Cycle

**Step 4.1: Write Test to Confirm Dead Code**
```python
# backend/apps/core/tests/test_dead_code.py
import subprocess

def test_require_admin_debug_not_referenced():
    """Verify require_admin_debug is not imported or used anywhere."""
    result = subprocess.run(
        ['grep', '-rn', 'require_admin_debug', 'backend/'],
        capture_output=True,
        text=True
    )
    # Should only find the definition, no usages
    lines = [l for l in result.stdout.split('\n') if l.strip()]
    # Should only have 1 line (the definition)
    assert len(lines) == 1, f"require_admin_debug found in {len(lines)} places: {lines}"
```

**Step 4.2: Implement Fix**
```python
# backend/apps/core/permissions.py
# Remove lines 236-255 entirely:
# def require_admin_debug(func: F) -> F:
#     """Debug version of require_admin."""
#     ...
```

**Step 4.3: Verify Fix**
- Run `pytest backend/apps/core/tests/test_dead_code.py -v`
- Run full test suite to ensure nothing breaks

---

## Execution Order

1. **Phase 1** (GST Fix) - ~30 min
   - Write test → Run (fails) → Implement → Run (passes) → Commit

2. **Phase 2** (Async Fix) - ~30 min
   - Write test → Run (fails) → Implement → Run (passes) → Commit

3. **Phase 3** (Rate Limiting) - ~45 min
   - Install package → Write test → Run (fails) → Implement → Run (passes) → Commit

4. **Phase 4** (Dead Code) - ~15 min
   - Write test → Run (passes - confirms dead) → Remove code → Verify → Commit

5. **Final Verification** - ~20 min
   - Run full test suite
   - Run lint/typecheck
   - Manual verification

---

## Rollback Plan

Each phase is independent with its own commit:
```bash
# If issues arise, rollback specific phase
git revert <commit-hash>
```

---

## Verification Checklist

- [ ] All new tests pass
- [ ] Existing tests still pass
- [ ] No lint/type errors
- [ ] Manual testing confirms fixes work
- [ ] Code review complete

---

**Plan Created:** 2026-04-29  
**Estimated Time:** 2.5 hours  
**Ready to Execute:** ✅
