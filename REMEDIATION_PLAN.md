# Wellfond BMS - Validated Remediation Plan
## Version: 1.0 | Date: April 30, 2026
## Status: Validated Against Codebase

---

## Executive Summary

This plan addresses **20 validated issues** from the Code Review Audit Report. Each issue has been re-confirmed by direct code inspection. Issues are prioritized by criticality with root causes and optimal fixes specified.

| Category | Count | Status |
|----------|-------|--------|
| Critical | 3 | 🔴 Must fix before deployment |
| High | 7 | 🟠 Should fix before production |
| Medium | 7 | 🟡 Next sprint |
| Low | 3 | 🔵 Backlog/Polish |

---

## Critical Issues (Must Fix Before Deployment)

### 🔴 C1: BFF Proxy Path Traversal Vulnerability

**Validation:**
- **File:** `frontend/app/api/proxy/[...path]/route.ts:52-60`
- **Confirmed:** Uses simple `startsWith()` check
- **Risk:** SSRF via path traversal (e.g., `/dogs/../../admin/` after normalization)

**Root Cause:**
```typescript
// Current (vulnerable):
function isAllowedPath(path: string): boolean {
  return ALLOWED_PREFIXES.some(prefix => path.startsWith(prefix));
}
// Bypass: `/dogs/../../../etc/passwd` starts with `/dogs/`
```

**Optimal Fix:**
1. Add path normalization before validation
2. Use regex anchored at start with strict path segment matching
3. Reject paths containing `..` or null bytes

**Implementation:**
```typescript
function isAllowedPath(path: string): boolean {
  // Normalize path: remove duplicate slashes, resolve . and ..
  const normalized = path.replace(/\/+/g, '/').replace(/\/$/, '');
  
  // Reject paths with traversal attempts
  if (normalized.includes('..') || normalized.includes('\0')) {
    return false;
  }
  
  // Allow health checks
  if (normalized === '/health' || normalized === '/ready') {
    return true;
  }
  
  // Strict regex matching for API paths
  const allowedPattern = /^\/(auth|users|dogs|breeding|sales|compliance|customers|finance|operations)(\/.*)?$/;
  return allowedPattern.test(normalized);
}
```

**Test Strategy:**
```typescript
// Test cases for TDD
const testCases = [
  { path: '/dogs/', expected: true },
  { path: '/dogs/../../admin/', expected: false },
  { path: '/dogs/../../../etc/passwd', expected: false },
  { path: '//dogs/', expected: true },  // After normalization
  { path: '/dogs\x00/../../etc', expected: false },  // Null byte
  { path: '/health/', expected: true },
  { path: '/api/internal', expected: false },
];
```

---

### 🔴 C2: Duplicate AuthenticationMiddleware Conflict

**Validation:**
- **File:** `backend/config/settings/base.py:50-51`
- **Confirmed:** Both middlewares present
- **Risk:** Race condition where Django middleware overwrites custom auth

**Root Cause:**
```python
MIDDLEWARE = [
    # ...
    "apps.core.middleware.AuthenticationMiddleware",  # Custom (line 50)
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Django (line 51)
    # ...
]
```

**Optimal Fix:**
Remove line 51 (Django's middleware). The custom middleware already handles:
- Session retrieval from Redis
- User attachment to request
- Django admin compatibility via ModelBackend

**Implementation:**
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "apps.core.middleware.AuthenticationMiddleware",  # Keep only this
    # REMOVE: "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.IdempotencyMiddleware",
    "apps.core.middleware.EntityScopingMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
]
```

**Note:** Keep `django.contrib.auth` in INSTALLED_APPS for admin support.

---

### 🔴 C3: Idempotency Only Enforced on Log Paths

**Validation:**
- **File:** `backend/apps/core/middleware.py:29-31`
- **Confirmed:** Only `/api/v1/operations/logs/` requires idempotency
- **Risk:** Duplicate records for agreements, litters, transactions, etc.

**Root Cause:**
```python
IDEMPOTENCY_REQUIRED_PATHS = [
    "/api/v1/operations/logs/",  # Only logs!
]
```

**Optimal Fix:**
Per draft_plan v1.1, idempotency should be required for all state-changing operations.

**Implementation:**
```python
# Option A: Require for all POST/PUT/PATCH/DELETE (recommended)
def _is_idempotency_required(self, path: str, method: str) -> bool:
    """Check if idempotency key is required for this request."""
    # All state-changing methods require idempotency
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        # Except auth endpoints
        if path.startswith("/api/v1/auth/"):
            return False
        return True
    return False

# Option B: Expand explicit paths
IDEMPOTENCY_REQUIRED_PATHS = [
    "/api/v1/operations/logs/",
    "/api/v1/breeding/litters",  # POST/PUT/PATCH
    "/api/v1/breeding/records",  # POST/PUT/PATCH
    "/api/v1/sales/agreements",  # POST/PUT/PATCH
    "/api/v1/finance/transactions",  # POST
    "/api/v1/customers/",  # POST/PUT/PATCH
]
```

---

## High Issues (Should Fix Before Production)

### 🟠 H1: Session and Idempotency Share Redis Cache

**Validation:**
- **File:** `backend/config/settings/base.py:112-115`
- **Confirmed:** Uses same `REDIS_CACHE_URL` as default cache

**Root Cause:**
```python
"idempotency": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://redis_cache:6379/0"),  # Same as default!
},
```

**Optimal Fix:**
Add dedicated Redis URL for idempotency with noeviction policy.

**Implementation:**
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://redis_cache:6379/0"),
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_SESSIONS_URL", "redis://redis_sessions:6379/0"),
    },
    "idempotency": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get(
            "REDIS_IDEMPOTENCY_URL", "redis://redis_idempotency:6379/0"  # NEW dedicated instance
        ),
    },
}
```

**Docker Compose Update:**
```yaml
redis_idempotency:
  image: redis:7.4-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy noeviction
```

---

### 🟠 H2: NEXT_PUBLIC_API_URL Exposes Internal URL

**Validation:**
- **Files:** `frontend/lib/api.ts:16`, `frontend/lib/constants.ts:182`
- **Confirmed:** Both use NEXT_PUBLIC_API_URL

**Root Cause:**
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**Optimal Fix:**
Use BACKEND_INTERNAL_URL for server-side calls (not exposed to browser).

**Implementation:**
```typescript
// lib/api.ts
function buildUrl(path: string): string {
  if (typeof window === 'undefined') {
    // Server-side: use internal URL (not exposed to browser)
    const internalUrl = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
    return `${internalUrl}/api/v1${path}`;
  }
  // Client-side: use BFF proxy
  return `${PROXY_PREFIX}${path}`;
}

// lib/constants.ts - remove or use for client-side only
export const API_CONFIG = {
  // Only used for client-side configuration
  baseUrl: '/api/proxy',  // Always proxy
  timeout: 30000,
};
```

---

### 🟠 H3: SESSION_COOKIE_SECURE Verification

**Validation:**
- **File:** `backend/config/settings/production.py:18-19`
- **Status:** ✅ Already correctly set
- **Note:** base.py doesn't set it explicitly but auth.py handles via `secure=not settings.DEBUG`

**Action:** No fix needed. Verified correct in production settings.

---

### 🟠 H4: COI Raw SQL Not Async-Compatible

**Validation:**
- **File:** `backend/apps/breeding/services/coi.py:61-90`
- **Confirmed:** Uses synchronous `connection.cursor()`

**Root Cause:**
```python
def get_shared_ancestors(dam_id: UUID, sire_id: UUID, generations: int = 5) -> List[dict]:
    with connection.cursor() as cursor:  # Synchronous
        cursor.execute("...")  # Blocks event loop
```

**Optimal Fix:**
Add async wrapper using `sync_to_async(thread_sensitive=True)`.

**Implementation:**
```python
from asgiref.sync import sync_to_async

async def get_shared_ancestors_async(
    dam_id: UUID, sire_id: UUID, generations: int = 5
) -> List[dict]:
    """Async wrapper for get_shared_ancestors."""
    return await sync_to_async(get_shared_ancestors, thread_sensitive=True)(
        dam_id, sire_id, generations
    )

async def calc_coi_async(
    dam_id: UUID, sire_id: UUID, generations: int = 5, use_cache: bool = True
) -> dict:
    """Async version of calc_coi."""
    cache_key = get_cache_key(dam_id, sire_id, generations)
    if use_cache:
        cached_result = await sync_to_async(cache.get)(cache_key)
        if cached_result:
            cached_result["cached"] = True
            return cached_result
    
    # Use async version
    ancestors = await get_shared_ancestors_async(dam_id, sire_id, generations)
    # ... rest of calculation
```

---

### 🟠 H5: Service Worker Cache Never Versioned

**Validation:**
- **File:** `frontend/public/sw.js:7`
- **Confirmed:** Hardcoded `const CACHE_NAME = "wellfond-bms-v1"`

**Root Cause:**
No mechanism to bump cache version on deploy.

**Optimal Fix:**
Add build-time version injection via environment variable or build hash.

**Implementation:**
```javascript
// sw.js
// Injected at build time
const CACHE_VERSION = self.__WB_MANIFEST ? self.__WB_MANIFEST.version : 'v1';
const CACHE_NAME = `wellfond-bms-${CACHE_VERSION}`;
const BUILD_TIMESTAMP = '{{BUILD_TIMESTAMP}}';  // Template replaced at build

// Alternative: Use Workbox for proper cache management
// Install: npm install workbox-build workbox-webpack-plugin
// Then use workbox.injectManifest in build process
```

**Build Script Update:**
```json
// package.json
"scripts": {
  "build": "next build && npm run build:sw",
  "build:sw": "workbox injectManifest workbox-config.js"
}
```

---

### 🟠 H6: PDPA Enforcement Missing in Log Routers

**Validation:**
- **File:** `backend/apps/operations/routers/logs.py`
- **Confirmed:** No `enforce_pdpa()` calls
- **Note:** Log models don't have `pdpa_consent` field - this is on User/Customer

**Root Cause:**
The `enforce_pdpa()` function filters querysets by `pdpa_consent` field, but log operations check user permissions, not customer data.

**Optimal Fix:**
Add PDPA consent check at user level for operations that handle customer data. For pure operational logs (heat, whelping), PDPA may not apply.

**Implementation:**
```python
# In log routers, check user's entity access and PDPA compliance
def _check_permission(request, dog: Dog):
    """Check if user has access to the dog with PDPA compliance."""
    user = _get_current_user(request)
    
    if not user or not user.is_authenticated:
        raise HttpError(401, "Authentication required")
    
    # Check PDPA consent for user
    if hasattr(user, 'pdpa_consent') and not user.pdpa_consent:
        raise HttpError(403, "PDPA consent required")
    
    # Entity scoping
    if user.role != "management" and str(dog.entity_id) != str(user.entity_id):
        raise HttpError(403, "Access denied")
    
    return user
```

---

### 🟠 H7: Rate Limiting on Auth Endpoints

**Validation:**
- **File:** `backend/apps/core/routers/auth.py:39,65,101`
- **Confirmed:** `@ratelimit` decorators present
- **Status:** ✅ Already implemented

**Note:** RATELIMIT_VIEW in settings needs handler implementation.

**Action:** Add ratelimit handler view if not present.

---

## Medium Issues (Next Sprint)

### 🟡 M1: COI SQL Parameter Documentation

**Status:** Low priority - queries are properly parameterized with `%s`
**Action:** Add comment documenting parameter order for maintainability.

---

### 🟡 M2: Closure Table Auto-Rebuild

**Status:** Celery tasks exist but no automatic triggers
**Action:** Document manual rebuild process; consider adding post_save signal for critical paths.

---

### 🟡 M3: Gotenberg Missing in Dev Compose

**Implementation:**
```yaml
gotenberg:
  image: gotenberg/gotenberg:8
  ports:
    - "3001:3000"
  command: gotenberg --api-port=3000
```

---

### 🟡 M4: api.ts Server Detection Fragile

**Current:** `typeof window === 'undefined'`
**Better:** Use Next.js headers() availability

```typescript
function isServer(): boolean {
  try {
    // Server-only import
    const { headers } = require('next/headers');
    return true;
  } catch {
    return false;
  }
}
```

---

### 🟡 M5: Rate Limit Handler

**Add to:** `backend/apps/core/routers/auth.py`
```python
from django.http import JsonResponse

def ratelimit_handler(request, exception):
    """Handle rate limit exceeded."""
    return JsonResponse(
        {"error": "Rate limit exceeded", "retry_after": 60},
        status=429
    )
```

---

### 🟡 M6: SSE Connection Cleanup

**Current:** `while True` loop never terminates
**Fix:** Add client disconnect detection via request signals.

```python
async def _generate_alert_stream(...):
    cancelled = False
    
    def on_disconnect():
        nonlocal cancelled
        cancelled = True
    
    # Register disconnect handler
    request.add_done_callback(on_disconnect)
    
    while not cancelled:
        # ... existing logic
```

---

### 🟡 M7: scope_entity Hasattr Check

```python
def scope_entity(queryset: QuerySet, user: User) -> QuerySet:
    if not user or not user.is_authenticated:
        return queryset.none()
    
    if user.role == User.Role.MANAGEMENT:
        return queryset
    
    # Add hasattr check
    if not hasattr(queryset.model, 'entity_id'):
        return queryset  # Pass through for non-entity models
    
    if user.entity_id:
        return queryset.filter(entity_id=user.entity_id)
    
    return queryset.none()
```

---

## Low Issues (Backlog)

### 🔵 L1: Remove api.py.bak
```bash
rm /home/project/wellfond-bms/backend/api.py.bak
```

### 🔵 L2: Fix GOTENBERG_URL Port
```python
# sales/services/pdf.py:24
GOTENBERG_URL = getattr(settings, "GOTENBERG_URL", "http://localhost:3001")
```

### 🔵 L3: Update README Docker References
Update to reference actual `infra/docker/docker-compose.yml`

---

## Execution Order

### Phase 1: Critical (Immediate)
1. C2: Remove duplicate AuthenticationMiddleware
2. C1: Fix BFF proxy path traversal
3. C3: Expand idempotency enforcement

### Phase 2: High (This Sprint)
4. H1: Isolate idempotency cache
5. H2: Remove NEXT_PUBLIC_API_URL
6. H4: Add COI async wrapper
7. H5: SW cache versioning
8. H6: PDPA enforcement (if applicable)

### Phase 3: Medium (Next Sprint)
9. M3: Add Gotenberg to compose
10. M6: SSE connection cleanup
11. M7: scope_entity hasattr check
12. M4: api.ts server detection

### Phase 4: Low (Backlog)
13. L1: Remove api.py.bak
14. L2: Fix GOTENBERG_URL port
15. L3: Update README

---

## Validation Checklist

- [ ] Each fix has corresponding test
- [ ] TDD approach: test first, then implementation
- [ ] Security fixes tested with attack scenarios
- [ ] No regression in existing functionality
- [ ] Documentation updated
