# Phase 1: Core Auth, BFF Proxy & RBAC — Sub-Plan

**Target:** 5–7 days | **Dependencies:** Phase 0 | **Status:** ⬜ Not Started

**Success Criteria:** HttpOnly cookie flow verified. Role matrix enforced. Zero token leakage. Design system renders Tangerine Sky theme.

---

## Execution Order

```
Step 1: Backend core app skeleton
  backend/apps/core/__init__.py → models.py → auth.py → permissions.py
  → middleware.py → schemas.py

Step 2: Backend routers & admin
  backend/apps/core/routers/__init__.py → auth.py → users.py
  → backend/apps/core/admin.py

Step 3: Backend tests
  backend/apps/core/tests/__init__.py → factories.py
  → test_auth.py → test_permissions.py

Step 4: Frontend shared utilities
  frontend/lib/types.ts → constants.ts → utils.ts → auth.ts → api.ts

Step 5: Frontend design system (ui/)
  button → input → card → badge → dialog → dropdown-menu → table
  → tabs → select → toast → skeleton → progress

Step 6: Frontend layout components
  layout/sidebar → layout/topbar → layout/bottom-nav → layout/role-bar

Step 7: Frontend auth pages
  app/(auth)/layout.tsx → app/(auth)/login/page.tsx

Step 8: Frontend protected layout
  app/(protected)/layout.tsx

Step 9: Frontend middleware
  frontend/middleware.ts

Step 10: BFF proxy
  app/api/proxy/[...path]/route.ts
```

---

## File-by-File Specifications

### Step 1: Backend Core App

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `backend/apps/core/__init__.py` | App package | Empty or `default_app_config` | ☐ |
| `backend/apps/core/models.py` | Core data models | **User(AbstractUser)**: `role` (enum: MANAGEMENT/ADMIN/SALES/GROUND/VET), `entity` (FK to Entity), `pdpa_consent` (bool), `mobile` (str). **Entity**: `name`, `code` (HOLDINGS/KATONG/THOMSON), `gst_rate` (Decimal), `avs_licence`. **AuditLog**: `uuid` (UUIDField), `actor` (FK to User), `action` (str), `resource_type`, `resource_id`, `payload` (JSON), `ip`, `created_at`. Meta: no UPDATE/DELETE (override `save()` and `delete()`). Indexes on `actor_id`, `created_at`, `action`. | ☐ |
| `backend/apps/core/auth.py` | Authentication logic | `login(request, user)`: sets HttpOnly session cookie, rotates CSRF, stores in Redis. `refresh(request)`: issues new CSRF token. `logout(request)`: clears cookie, deletes Redis session. Session: 15m access, 7d refresh. `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_SAMESITE='Lax'`. | ☐ |
| `backend/apps/core/permissions.py` | Role decorators & entity scoping | `@require_role(*roles)`: decorator that checks `request.user.role`. Fails closed (403) on missing role. `@scope_entity(queryset, user)`: filters queryset by `entity_id` unless user is MANAGEMENT (sees all). `enforce_pdpa(queryset)`: hard filter `WHERE pdpa_consent=True`. Unit tests for each role. | ☐ |
| `backend/apps/core/middleware.py` | Idempotency + entity middleware | **IdempotencyMiddleware**: reads `X-Idempotency-Key` on POST, SHA-256 hashes it, checks Redis (24h TTL), returns cached 200 on duplicate, blocks missing keys on `/api/v1/operations/logs/`. **EntityScopingMiddleware**: attaches `request.entity_filter` based on user role/entity. | ☐ |
| `backend/apps/core/schemas.py` | Pydantic schemas | `LoginRequest(username, password)`, `LoginResponse(user, csrf_token)`, `UserResponse(id, username, role, entity_id, pdpa_consent)`, `UserCreate(username, password, role, entity_id)`, `UserUpdate(role?, entity_id?, pdpa_consent?)`, `AuditLogEntry(uuid, actor, action, resource_type, resource_id, payload, ip, created_at)`. | ☐ |

### Step 2: Backend Routers & Admin

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `backend/apps/core/routers/__init__.py` | Router package | Empty | ☐ |
| `backend/apps/core/routers/auth.py` | Auth endpoints | `POST /api/v1/auth/login` → calls `auth.login()`, returns `LoginResponse`. `POST /api/v1/auth/logout` → calls `auth.logout()`, returns 200. `POST /api/v1/auth/refresh` → rotates CSRF, returns new token. `GET /api/v1/auth/me` → returns current `UserResponse` or 401. Tags: `["auth"]`. | ☐ |
| `backend/apps/core/routers/users.py` | User management (admin) | `GET /api/v1/users/` → list users (admin only). `POST /api/v1/users/` → create user (admin). `PATCH /api/v1/users/{id}` → update user (admin). `DELETE /api/v1/users/{id}` → deactivate (admin). Tags: `["users"]`. | ☐ |
| `backend/apps/core/admin.py` | Django admin | Register User (search by username/mobile, filter by role/entity), Entity (editable), AuditLog (read-only, filter by action/actor). | ☐ |

### Step 3: Backend Tests

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `backend/apps/core/tests/__init__.py` | Test package | Empty | ☐ |
| `backend/apps/core/tests/factories.py` | Test factories | `UserFactory` (role=GROUND, entity=Holdings). `EntityFactory` (name="Holdings", code="HOLDINGS"). `AuditLogFactory`. `ManagementUserFactory`, `AdminUserFactory`, `SalesUserFactory`, `GroundUserFactory`, `VetUserFactory`. | ☐ |
| `backend/apps/core/tests/test_auth.py` | Auth tests | `test_login_sets_httponly_cookie`. `test_login_returns_user`. `test_logout_clears_cookie`. `test_refresh_rotates_csrf`. `test_unauthenticated_returns_401`. `test_session_stored_in_redis`. `test_cookie_properties_httponly_secure_samesite`. | ☐ |
| `backend/apps/core/tests/test_permissions.py` | Permission tests | `test_ground_cannot_access_sales`. `test_sales_cannot_access_finance`. `test_management_sees_all_entities`. `test_ground_sees_own_entity_only`. `test_pdpa_filter_excludes_opted_out`. `test_require_role_fails_closed`. `test_entity_scoping_cross_entity_blocked`. | ☐ |

### Step 4: Frontend Shared Utilities

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/lib/types.ts` | TypeScript types | `User { id, username, role, entityId, pdpaConsent }`. `Role = 'MANAGEMENT' | 'ADMIN' | 'SALES' | 'GROUND' | 'VET'`. `Entity { id, name, code, gstRate }`. `Dog { id, microchip, name, breed, dob, gender, colour, entityId, status, damId?, sireId?, unit, dnaStatus }`. `DogStatus = 'ACTIVE' | 'RETIRED' | 'REHOMED' | 'DECEASED'`. `AuditLog { uuid, actor, action, resourceType, resourceId, payload, ip, createdAt }`. Plus types for BreedingRecord, Litter, Puppy, SalesAgreement, Customer, HealthRecord, Vaccination, etc. | ☐ |
| `frontend/lib/constants.ts` | App constants | `ROLES`, `ENTITIES`, `LOG_TYPES`, `COI_THRESHOLDS { SAFE: 6.25, CAUTION: 12.5 }`, `SATURATION_THRESHOLDS { SAFE: 15, CAUTION: 30 }`, `DESIGN_TOKENS { colors, fonts, spacing }`, `AGREEMENT_TYPES`, `DOG_STATUSES`. | ☐ |
| `frontend/lib/utils.ts` | Utility functions | `cn(...inputs)` (clsx + tailwind-merge). `formatDate(date, format?)`. `formatChip(chip)` (last 4 bold). `calculateAge(dob)` (years + months). `gstExtract(price, entity)` (9/109 formula). `formatCurrency(amount)`. `debounce(fn, ms)`. `truncate(str, len)`. | ☐ |
| `frontend/lib/auth.ts` | Session helpers | `getSession()` (reads cookie, returns User or null). `isAuthenticated()`. `getRole()`. `isServer()` (typeof window). `requireAuth()` (redirect to /login if not). | ☐ |
| `frontend/lib/api.ts` | Unified fetch wrapper | `authFetch<T>(path, opts?)`: server → direct Django URL; client → `/api/proxy/`. Auto-refresh on 401 (one retry). Attaches UUIDv4 `X-Idempotency-Key` on POST. Typed generics. Error → toast via Sonner. `api.get<T>(path)`, `api.post<T>(path, body)`, `api.patch<T>(path, body)`, `api.delete(path)`. | ☐ |

### Step 5: Frontend Design System (ui/)

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/components/ui/button.tsx` | Button | Variants: `primary` (orange bg), `secondary` (teal bg), `ghost` (transparent), `destructive` (red). Sizes: `sm` (32px), `md` (40px), `lg` (48px). Loading state: spinner + disabled. Uses `class-variance-authority`. Forward ref. | ☐ |
| `frontend/components/ui/input.tsx` | Input | Label (Figtree 14px). Error message (red, below). Helper text (muted). Controlled + forward ref. Focus ring (orange). Disabled state. | ☐ |
| `frontend/components/ui/card.tsx` | Card | White bg, border `#C0D8EE`, rounded-lg. Slots: `CardHeader`, `CardContent`, `CardFooter`. Hover: subtle shadow. | ☐ |
| `frontend/components/ui/badge.tsx` | Badge | Variants: `default` (navy), `success` (green), `warning` (amber), `error` (red), `info` (teal). Pill shape. 12px font. | ☐ |
| `frontend/components/ui/dialog.tsx` | Dialog/modal | Radix Dialog. Overlay (black/50%). Close button (X). Title + description. Max-width sm/md/lg. Focus trap. | ☐ |
| `frontend/components/ui/dropdown-menu.tsx` | Dropdown | Radix DropdownMenu. Trigger + content + item. Keyboard navigation. Separators. | ☐ |
| `frontend/components/ui/table.tsx` | Table | `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`. Sortable column headers (click to sort). Responsive: card reflow on mobile (<768px). | ☐ |
| `frontend/components/ui/tabs.tsx` | Tabs | Radix Tabs. `TabsList`, `TabsTrigger`, `TabsContent`. Active: orange underline. Controlled/uncontrolled. | ☐ |
| `frontend/components/ui/select.tsx` | Select | Radix Select. Searchable option list. Placeholder. Disabled. | ☐ |
| `frontend/components/ui/toast.tsx` | Toast | Via Sonner. `toast.success()`, `toast.error()`, `toast.info()`. Auto-dismiss 5s. Position bottom-right. | ☐ |
| `frontend/components/ui/skeleton.tsx` | Skeleton | Pulse animation. Variants: `line` (full width, 16px), `circle` (48px), `rect` (custom w/h). | ☐ |
| `frontend/components/ui/progress.tsx` | Progress bar | Determinate (0-100%). Animated fill. Orange bg. Rounded. | ☐ |

### Step 6: Frontend Layout Components

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/components/layout/sidebar.tsx` | Desktop sidebar | `#E8F4FF` bg. Logo top. Nav items: Dashboard, Dogs, Breeding, Sales, Compliance, Customers, Finance (filtered by role). Active: orange bg + white text. Collapsible (icon-only mode). Entity selector dropdown at bottom. Role badge. | ☐ |
| `frontend/components/layout/topbar.tsx` | Top bar | Breadcrumb (current page). User avatar + name. Notifications bell (badge count). Role badge (orange border). | ☐ |
| `frontend/components/layout/bottom-nav.tsx` | Mobile bottom nav | 5 tabs: Home, Dogs, Sales, Reports, More. Active: orange. 44px tap targets. Fixed bottom. Only visible <768px. | ☐ |
| `frontend/components/layout/role-bar.tsx` | Role indicator | `#FFF0E6` bg, orange left border. Shows: "Logged in as {role} · {entity}". | ☐ |

### Step 7: Frontend Auth Pages

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/app/(auth)/layout.tsx` | Auth layout | Minimal: centered card, no sidebar, no topbar. Full-screen `#DDEEFF` bg. Logo centered. | ☐ |
| `frontend/app/(auth)/login/page.tsx` | Login page | Username input. Password input. Login button (primary, loading state). Submit → `POST /api/proxy/auth/login`. On success → redirect by role: MANAGEMENT/ADMIN→`/dashboard`, SALES→`/dashboard`, GROUND→`/ground`, VET→`/dogs`. Error: toast. Tangerine Sky theme. | ☐ |

### Step 8: Frontend Protected Layout

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/app/(protected)/layout.tsx` | Protected layout | Sidebar (desktop, collapsible) + topbar. Mobile: bottom-nav. Role guard: redirect to `/login` if no session. `RoleBar` at top. Main content area with padding. | ☐ |

### Step 9: Frontend Middleware

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/middleware.ts` | Route protection | Read session cookie. Unauthenticated → redirect to `/login`. Role route map: GROUND→`/ground` only. VET→`/dogs` only. SALES→no `/finance`, no `/compliance`. ADMIN→all except user management. MANAGEMENT→all. Edge-compatible (no Node.js APIs). | ☐ |

### Step 10: BFF Proxy

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/app/api/proxy/[...path]/route.ts` | Hardened BFF proxy | `BACKEND_INTERNAL_URL` (server-only env, never NEXT_PUBLIC_). **Development**: `http://127.0.0.1:8000`. **Production**: `http://django:8000`. `ALLOWED_PREFIXES` regex: `/api/v1/(dogs|breeding|sales|compliance|customers|finance|operations|auth|users)/`. Strip headers: `host`, `x-forwarded-for`, `x-forwarded-host`, `x-forwarded-proto`. Set `x-forwarded-proto: https`. Stream response body. 403 on non-allowlisted paths. 503 on upstream failure. Export GET/POST/PATCH/DELETE handlers. | ☐ |
| `frontend/next.config.ts` (dev section) | Dev proxy config | `rewrites(): [{ source: '/api/proxy/:path*', destination: 'http://127.0.0.1:8000/api/v1/:path*' }]` for development fallback. Environment detection: `process.env.NODE_ENV`. | ☐ |

---

## Phase 1 Validation Checklist

### Authentication
- [ ] Login → sets HttpOnly cookie, Secure, SameSite=Lax
- [ ] `window.localStorage` and `window.sessionStorage` are empty after login
- [ ] Logout → clears cookie, redirects to /login
- [ ] Refresh → rotates CSRF token
- [ ] Unauthenticated → redirects to /login (not 500)
- [ ] Session stored in Redis (verify via `redis-cli GET session:*`)

### BFF Proxy (Development Environment)
- [ ] `POST /api/proxy/auth/login` → forwards to Django at `127.0.0.1:8000`, returns user
- [ ] Next.js dev server (`localhost:3000`) → proxies to Django (`127.0.0.1:8000`)
- [ ] `BACKEND_INTERNAL_URL=http://127.0.0.1:8000` in `.env.local`
- [ ] Django receives cookies from Next.js proxy correctly
- [ ] CORS configured for `localhost:3000` in Django dev settings

### BFF Proxy (Production Environment)
- [ ] `POST /api/proxy/auth/login` → forwards to Django container, returns user
- [ ] `BACKEND_INTERNAL_URL=http://django:8000` in production env
- [ ] Container-to-container networking works
- [ ] `POST /api/proxy/admin/login` → 403 Forbidden (path not allowlisted)
- [ ] `POST /api/proxy/dogs/` → forwards with cookies, Django validates
- [ ] `GET /api/proxy/dogs/` → streams response
- [ ] Upstream down → 503 Service Unavailable
- [ ] No `NEXT_PUBLIC_API_BASE` or `NEXT_PUBLIC_` env vars in proxy code

### RBAC
- [ ] GROUND role → can access `/ground/`, blocked from `/sales/`, `/breeding/`, `/finance/`
- [ ] SALES role → can access `/dogs/`, `/sales/`, blocked from `/finance/`, `/compliance/`
- [ ] VET role → can access `/dogs/`, blocked from `/sales/`, `/breeding/`
- [ ] ADMIN role → all except user management
- [ ] MANAGEMENT role → all
- [ ] Cross-entity query → returns empty (not other entity's data)

### Design System
- [ ] Button: all 4 variants render with correct colors
- [ ] Input: label, error, helper text display correctly
- [ ] Card: white bg, border, rounded
- [ ] Badge: 5 variants with correct colors
- [ ] Dialog: opens/closes, focus trap works
- [ ] Table: sortable columns, card reflow on mobile
- [ ] Tabs: active state (orange underline)
- [ ] Toast: appears, auto-dismisses after 5s
- [ ] Skeleton: pulse animation during loading
- [ ] Progress: animated fill bar

### Layout
- [ ] Sidebar: role-aware nav items, collapsible
- [ ] Topbar: breadcrumb, user info, role badge
- [ ] Bottom nav: 5 tabs, 44px targets, visible <768px only
- [ ] Role bar: shows role + entity

### Idempotency
- [ ] POST with `X-Idempotency-Key` → first returns 201, second returns 200 (cached)
- [ ] POST to `/operations/logs/` without key → 400
- [ ] POST to other endpoints without key → allowed (not enforced)
