# Django AuthenticationMiddleware Fix Summary

## Problem

After adding `django.contrib.auth.middleware.AuthenticationMiddleware` back to `MIDDLEWARE` for Django admin support, Django started successfully but there was a middleware conflict:

1. Django's `AuthenticationMiddleware` unconditionally wraps `request.user` in `SimpleLazyObject`
2. Our custom `AuthenticationMiddleware` sets `request.user` directly from Redis session
3. If custom runs first, Django wraps it; if Django runs first, custom overwrites it

## Solution

**Changed middleware order** so Django's middleware runs first, then custom re-authenticates from Redis:

```python
MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django first
    "apps.core.middleware.AuthenticationMiddleware",             # Custom second
    ...
]
```

**How it works:**
1. Django's middleware wraps `request.user` with `SimpleLazyObject(lambda: get_user(request))`
2. Custom middleware runs after and re-authenticates from Redis session cookie
3. Custom sets `request.user = user` (unwraps the lazy object with actual user)
4. Result: both admin and API authentication work correctly

## Files Changed

1. `backend/config/settings/base.py` - Updated middleware order
2. `backend/apps/core/tests/test_middleware_configuration.py` - Fixed test expectation

## Tests

All 16 middleware tests pass:
- ✅ Django admin can be imported
- ✅ Admin login URL accessible
- ✅ Both middlewares present in correct order
- ✅ CSRF before auth
- ✅ Idempotency after auth
- ✅ No admin.E408 error

## Verification

Django starts successfully:
```bash
✅ Django restarted with PID: 1121407
```

Admin and API authentication both functional.
