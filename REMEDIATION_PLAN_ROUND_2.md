# Wellfond BMS - Remediation Plan Round 2
## Version: 1.0 | Date: April 30, 2026
## Scope: New Critical & High Issues from Validation Round 2

---

## Executive Summary

Round 2 validation identified **3 NEW Critical** and **3 NEW High** issues that require remediation. These are distinct from Round 1 fixes and focus on environment configuration, runtime settings, and security hardening.

| Priority | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 3 | **Requires immediate fix** |
| 🟠 High | 3 | **Requires attention before production** |
| 🟡 Medium | 5 | Next sprint |
| 🔵 Low | 8 | Backlog |

---

## Critical Issues (Must Fix Before Deployment)

### 🔴 C1: BFF Proxy Edge Runtime Blocks process.env Access

**Status:** NOT FIXED  
**Validation:** ✅ Confirmed in `frontend/app/api/proxy/[...path]/route.ts:232`

**Problem:**
```typescript
export const runtime = 'edge';
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
```

In Edge Runtime, `process.env` is only available at build time. At runtime, `BACKEND_INTERNAL_URL` will be `undefined`, causing the proxy to fail.

**Root Cause:**
- Edge Runtime ≠ Node.js Runtime
- Environment variables compiled at build time
- Only `NEXT_PUBLIC_*` vars are available in Edge at build

**Fix:** Remove Edge Runtime export
```typescript
// REMOVE line 232:
// export const runtime = 'edge';

// The route will default to Node.js runtime which supports process.env
```

**Test:**
```bash
# After fix, verify no Edge runtime
grep -c "export const runtime = 'edge'" frontend/app/api/proxy/\[...path\]/route.ts
# Should return 0
```

---

### 🔴 C2: BACKEND_INTERNAL_URL Leaked to Browser via next.config.ts

**Status:** NOT FIXED  
**Validation:** ✅ Confirmed in `frontend/next.config.ts:89-91`

**Problem:**
```typescript
env: {
  BACKEND_INTERNAL_URL: process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000",
},
```

The `env` key in `next.config.ts` injects variables into the browser bundle, making them accessible to any visitor.

**Root Cause:**
- `env` config makes vars available client-side
- Plan requires: "BACKEND_INTERNAL_URL (server-only env, never NEXT_PUBLIC_)"
- Current implementation violates this

**Fix:** Remove the `env` block entirely
```typescript
// REMOVE lines 88-91:
// // Environment variables exposed to browser (prefix with NEXT_PUBLIC_)
// env: {
//   BACKEND_INTERNAL_URL: process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000",
// },

// The proxy route handler already reads process.env.BACKEND_INTERNAL_URL server-side
// The rewrites() function (line 65-75) runs server-side and can safely use process.env
```

**Verification:**
```bash
# After fix, verify no env block with BACKEND_INTERNAL_URL
grep -c "BACKEND_INTERNAL_URL:" frontend/next.config.ts
# Should return 0 (only the server-side process.env reference should remain)
```

---

### 🔴 C3: DJANGO_SETTINGS_MODULE Points to Nonexistent Path

**Status:** NOT FIXED  
**Validation:** ✅ Confirmed in `.env:23`

**Problem:**
```bash
DJANGO_SETTINGS_MODULE=wellfond.settings.development
```

The actual settings module is at `config.settings.development`, not `wellfond.settings.development`.

**Root Cause:**
- Directory structure: `backend/config/settings/`
- No `backend/wellfond/` package exists
- Causes `ModuleNotFoundError` on startup

**Fix:** Update .env line 23
```bash
# BEFORE:
DJANGO_SETTINGS_MODULE=wellfond.settings.development

# AFTER:
DJANGO_SETTINGS_MODULE=config.settings.development
```

**Verification:**
```bash
# After fix, verify correct path
grep "DJANGO_SETTINGS_MODULE" .env
# Should show: config.settings.development
```

---

## High Issues (Should Fix Before Production)

### 🟠 H1: No Server-Side Role Enforcement

**Status:** NOT FIXED  
**Validation:** ✅ Confirmed in `frontend/middleware.ts:78-83`

**Problem:**
```typescript
// Check for session cookie
const sessionCookie = request.cookies.get('sessionid');

// Note: Full role check happens client-side via useAuth hook
// Middleware only does basic cookie validation
```

Only cookie presence is checked. GROUND users can access `/breeding/`, `/sales/`, `/finance/` by direct URL.

**Root Cause:**
- No role data in cookie/session
- Plan requires server-side middleware role checks
- Current implementation defers to client-side (bypassable)

**Fix Options:**

**Option A: Add role cookie (simpler)**
```typescript
// In login response, set role cookie
response.setCookie('user_role', user.role, { httpOnly: false, secure: true });

// In middleware.ts
const userRole = request.cookies.get('user_role')?.value;

// Enforce role-based routing
const ROLE_ROUTES = {
  GROUND: ['/ground/', '/dogs/'],
  SALES: ['/sales/', '/customers/', '/dogs/'],
  ADMIN: ['/breeding/', '/sales/', '/finance/', '/compliance/', '/customers/', '/dogs/', '/users/'],
  MANAGEMENT: ['/'], // All routes
};

if (pathname.startsWith('/breeding/') && userRole !== 'MANAGEMENT' && userRole !== 'ADMIN') {
  return NextResponse.redirect(new URL('/dashboard', request.url));
}
```

**Option B: Use JWT in cookie with role claims**
Include role in session cookie payload, decode in middleware.

---

### 🟠 H2: Missing Required Redis URLs in .env

**Status:** NOT FIXED  
**Validation:** ✅ Confirmed in `.env:31-34`

**Problem:**
Only `REDIS_URL` is defined. Settings expect:
- `REDIS_CACHE_URL`
- `REDIS_SESSIONS_URL`
- `REDIS_BROKER_URL`
- `REDIS_IDEMPOTENCY_URL`

**Root Cause:**
- `.env` incomplete
- Settings fall back to production hostnames
- Dev hostnames won't resolve

**Fix:** Add to .env
```bash
# Add after line 34:

# Redis Split Instances (for sessions, broker, cache, idempotency)
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_SESSIONS_URL=redis://localhost:6379/1
REDIS_BROKER_URL=redis://localhost:6379/2
REDIS_IDEMPOTENCY_URL=redis://localhost:6379/3
```

---

### 🟠 H3: PostgreSQL Exposed on All Interfaces

**Status:** NOT FIXED  
**Validation:** ✅ Confirmed in `infra/docker/docker-compose.yml:35`

**Problem:**
```yaml
ports:
  - "0.0.0.0:5432:5432"
environment:
  POSTGRES_HOST_AUTH_METHOD: trust
```

Exposes passwordless PostgreSQL to all network interfaces.

**Fix:** Restrict to localhost
```yaml
# BEFORE:
ports:
  - "0.0.0.0:5432:5432"

# AFTER:
ports:
  - "127.0.0.1:5432:5432"
```

**Alternative:** Remove `POSTGRES_HOST_AUTH_METHOD: trust` for stricter auth

---

## Medium Issues (Next Sprint)

### 🟡 M1: .env Has Branding Remnants
**Fix:** Change line 1 in .env
```bash
# BEFORE:
# CHA YUAN Environment Configuration

# AFTER:
# WELLFOND Environment Configuration
```

### 🟡 M2: Duplicate DB_PASSWORD in .env
**Fix:** Remove duplicate on line 11

### 🟡 M3: CSRF_COOKIE_HTTPONLY=True
**Analysis:** Acceptable - tokens delivered via API body

### 🟡 M4: request.body Consumed in Middleware
**Analysis:** Acceptable - Django caches after first read

### 🟡 M5: Development Settings CONN_MAX_AGE
**Analysis:** Acceptable for development

---

## Implementation Order

### Phase 1: Critical (Immediate)
1. **C1:** Remove Edge Runtime from BFF proxy
2. **C2:** Remove BACKEND_INTERNAL_URL from env block
3. **C3:** Fix DJANGO_SETTINGS_MODULE path

### Phase 2: High (This Sprint)
4. **H1:** Add server-side role enforcement to middleware
5. **H2:** Add Redis URLs to .env
6. **H3:** Restrict PostgreSQL port binding

### Phase 3: Medium (Next Sprint)
7. **M1-M2:** Clean up .env file

---

## Test Strategy

### For Critical Fixes:
```bash
# C1: Verify no Edge runtime
grep -c "runtime = 'edge'" frontend/app/api/proxy/\[...path\]/route.ts
# Expected: 0

# C2: Verify no env block with BACKEND_INTERNAL_URL
grep -c "BACKEND_INTERNAL_URL:" frontend/next.config.ts
# Expected: 0

# C3: Verify correct Django settings path
grep "DJANGO_SETTINGS_MODULE=config.settings" .env
# Expected: 1 match
```

### For High Fixes:
```bash
# H1: Verify role enforcement added
grep -c "user_role" frontend/middleware.ts
# Expected: >0 after fix

# H2: Verify Redis URLs
grep -c "REDIS_SESSIONS_URL\|REDIS_BROKER_URL\|REDIS_IDEMPOTENCY_URL" .env
# Expected: 3 matches

# H3: Verify localhost-only binding
grep "127.0.0.1:5432" infra/docker/docker-compose.yml
# Expected: 1 match
```

---

## Verification Checklist

- [ ] C1: BFF proxy uses Node.js runtime
- [ ] C2: No BACKEND_INTERNAL_URL in browser bundle
- [ ] C3: Django starts with correct settings module
- [ ] H1: Server-side role enforcement active
- [ ] H2: All Redis URLs defined in .env
- [ ] H3: PostgreSQL bound to localhost only
- [ ] All existing tests pass
- [ ] New tests added for role enforcement

---

## Risk Assessment

| Issue | Risk | Mitigation |
|-------|------|------------|
| C1: Edge Runtime | **High** - Proxy fails in production | Fix immediately, test with production build |
| C2: URL Leak | **Medium** - Internal exposure | Fix before any deployment |
| C3: Settings Path | **High** - Django won't start | Fix immediately, verify startup |
| H1: No Role Enforcement | **Medium** - Bypassable access | Add basic enforcement before production |
| H2: Missing Redis URLs | **Low** - Uses defaults | Fix before multi-instance deployment |
| H3: PostgreSQL Exposure | **Low** - Dev only | Fix before any network exposure |

---

## Notes

- All issues are configuration/runtime related (not design flaws)
- Fixes are straightforward and low-risk
- Estimated time: 2-3 hours for all Critical + High fixes
- No code logic changes required, only configuration
