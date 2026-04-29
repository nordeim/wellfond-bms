# AGENT BRIEF - Wellfond BMS
## Single Source of Truth for AI Coding Agents

**Last Updated:** 2026-04-29  
**Project:** Wellfond Breeding Management System (BMS)  
**Version:** 1.0.0 | **Classification:** CONFIDENTIAL  
**Status:** Phases 0-6 COMPLETE, Phase 7-8 IN PROGRESS

---

## 1. Core Identity & Purpose

### 1.1 WHAT
Wellfond BMS is an enterprise-grade dog breeding operations platform for Singapore AVS-licensed breeders. It manages the complete lifecycle of breeding operations from pedigree tracking to AVS regulatory submissions.

### 1.2 WHY
- **Compliance:** Automates AVS/NParks regulatory requirements with 100% deterministic logic
- **Security:** Multi-entity data isolation (Holdings, Katong, Thomson) with PDPA protection
- **Operational Efficiency:** Mobile-first PWA for kennel staff with offline capability

### 1.3 Key Capabilities
| Feature | Description |
|---------|-------------|
| Multi-Entity | Holdings, Katong, Thomson with data scoping |
| RBAC | 5 roles: management, admin, sales, ground, vet |
| Ground Operations | 7 log types (heat, mating, whelping, health, weight, nursing, not-ready) |
| Breeding Engine | COI calculation, saturation analysis, dual-sire support |
| Sales Agreements | B2C/B2B/Rehoming with e-signatures and AVS tracking |
| Compliance | NParks submissions, GST 9/109, PDPA hard filters |

---

## 2. Architecture Overview

### 2.1 Tech Stack
| Layer | Technology | Version |
|-------|------------|---------|
| **Backend** | Django + Ninja | 6.0.4 / 1.6.2 |
| **Frontend** | Next.js | 16.2.4 |
| **Styling** | Tailwind CSS | 4.2.4 |
| **UI Library** | Radix UI + shadcn/ui | Latest |
| **Database** | PostgreSQL | 17 |
| **Cache/Broker** | Redis | 7.4 (×3 instances) |
| **Task Queue** | Celery | 5.4 |
| **PDF** | Gotenberg | 8 (sidecar) |

### 2.2 Architecture Patterns

#### BFF (Backend-for-Frontend) Security
```
Browser → Next.js /api/proxy/[...path] → Django API
```
- **HttpOnly cookies** - No JWT in localStorage/sessionStorage
- **Path allowlist** - Only `/api/v1/{dogs,breeding,sales,compliance,customers,finance,operations,auth,users,dashboard}/`
- **Header sanitization** - Strips Host, X-Forwarded-* headers

#### Entity Scoping (Multi-Tenancy)
```python
# Every query must respect entity boundaries
from apps.core.permissions import scope_entity
queryset = scope_entity(Dog.objects.all(), request.user)
# Management sees all; others see only their entity_id
```

#### Compliance Determinism
- **NO AI in compliance module** - Pure Python/SQL for NParks/GST/AVS
- **Immutable audit logs** - No UPDATE/DELETE on AuditLog
- **GST calculation:** `Decimal(price) * 9 / 109`, `ROUND_HALF_UP`
- **Thomson entity:** 0% GST exempt

---

## 3. Project Structure

```
wellfond-bms/
├── backend/
│   ├── api/                    # NinjaAPI instance
│   ├── apps/
│   │   ├── core/               # Auth, RBAC, Entity, Dashboard (NEW)
│   │   │   ├── auth.py         # SessionManager, AuthenticationService
│   │   │   ├── permissions.py # @require_role, scope_entity
│   │   │   ├── middleware.py  # IdempotencyMiddleware
│   │   │   ├── models.py      # User, Entity, AuditLog
│   │   │   ├── routers/
│   │   │   │   ├── auth.py    # Login/logout/refresh
│   │   │   │   ├── dashboard.py  # NEW: /dashboard/metrics
│   │   │   │   └── users.py
│   │   │   ├── services/
│   │   │   │   └── dashboard.py  # NEW: Dashboard metrics service
│   │   │   └── tests/
│   │   │       ├── test_auth.py
│   │   │       ├── test_permissions.py
│   │   │       ├── test_dashboard.py           # NEW
│   │   │       └── test_dashboard_integration.py # NEW
│   │   ├── operations/         # Dogs, Health, Ground Logs
│   │   ├── breeding/           # Genetics, COI, Litters (Phase 4)
│   │   ├── sales/            # Agreements, AVS (Phase 5)
│   │   ├── compliance/       # NParks, GST, PDPA (Phase 6)
│   │   ├── customers/        # CRM, Blasts (Phase 7)
│   │   └── ai_sandbox/       # Isolated AI experiments
│   └── config/
│       ├── settings/
│       └── celery.py
├── frontend/
│   ├── app/
│   │   ├── (auth)/            # Login (minimal layout)
│   │   ├── (protected)/       # Authenticated routes
│   │   │   ├── dashboard/     # NEW: /dashboard page
│   │   │   │   ├── page.tsx
│   │   │   │   └── layout.tsx
│   │   │   ├── dogs/
│   │   │   ├── breeding/
│   │   │   ├── sales/
│   │   │   └── compliance/
│   │   ├── (ground)/          # Mobile ops (no sidebar)
│   │   └── api/proxy/         # BFF proxy route
│   ├── components/
│   │   ├── ui/               # shadcn components
│   │   ├── dashboard/         # NEW: Dashboard widgets
│   │   │   ├── stat-cards.tsx
│   │   │   ├── nparks-countdown.tsx
│   │   │   ├── activity-feed.tsx
│   │   │   ├── revenue-chart.tsx
│   │   │   ├── quick-actions.tsx
│   │   │   └── dashboard-skeleton.tsx
│   │   ├── dogs/
│   │   ├── breeding/
│   │   ├── sales/
│   │   └── layout/           # Sidebar, Topbar, BottomNav
│   ├── hooks/
│   │   ├── use-dashboard.ts   # NEW: Dashboard TanStack hooks
│   │   ├── use-dogs.ts
│   │   ├── use-breeding.ts
│   │   └── use-sales.ts
│   ├── lib/
│   │   ├── types.ts          # TypeScript types (UPDATED)
│   │   ├── constants.ts
│   │   ├── api.ts            # authFetch wrapper
│   │   └── offline-queue.ts  # PWA offline queue
│   ├── tests/
│   │   └── dashboard.test.tsx # NEW: Component tests
│   └── e2e/
│       └── dashboard.spec.ts # NEW: E2E tests
├── tests/                     # Backend tests
│   └── *.py
└── docker-compose.yml
```

---

## 4. Development Workflow

### 4.1 Environment Setup
```bash
# 1. Start infrastructure
docker-compose up -d postgres redis

# 2. Backend
cd backend
python manage.py migrate
python manage.py shell -c "from apps.core.models import User; User.objects.create_superuser('admin', 'admin@wellfond.sg', 'Wellfond@2024!', role='management')"

# 3. Frontend
cd ../frontend
npm install

# 4. Start services (hybrid mode)
# Terminal 1: Django
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Next.js
npm run dev
```

### 4.2 Key Commands
| Command | Purpose |
|---------|---------|
| `cd backend && python -m pytest apps/core/tests/test_dashboard.py -v` | Run dashboard tests |
| `cd frontend && npm run typecheck` | TypeScript check |
| `cd frontend && npm run build` | Production build |
| `cd frontend && npx playwright test dashboard.spec.ts` | E2E tests |
| `celery -A config worker -l info` | Start Celery worker |

---

## 5. Testing Strategy

### 5.1 Test Organization
| Test Type | Location | Framework | Coverage Target |
|-----------|----------|-----------|-----------------|
| **Backend Unit** | `apps/{app}/tests/` | pytest | ≥85% |
| **Backend Integration** | `apps/core/tests/test_*_integration.py` | pytest | Critical paths |
| **Frontend Unit** | `frontend/tests/*.test.tsx` | Vitest + React Testing Library | Components |
| **E2E** | `frontend/e2e/*.spec.ts` | Playwright | Critical flows |

### 5.2 Dashboard Tests (Just Created)
| File | Tests | Purpose |
|------|-------|---------|
| `backend/apps/core/tests/test_dashboard.py` | 11 | Unit tests for metrics endpoint |
| `backend/apps/core/tests/test_dashboard_integration.py` | 20+ | Integration tests for stats, roles, caching |
| `frontend/tests/dashboard.test.tsx` | 20+ | Component unit tests |
| `frontend/e2e/dashboard.spec.ts` | 30+ | E2E tests for full flows |

### 5.3 TDD Pattern
1. Write failing test (Red)
2. Implement minimal code (Green)
3. Refactor while passing (Refactor)
4. Verify with curl/test client

---

## 6. Implementation Standards

### 6.1 Backend (Python/Django)

#### Pydantic v2 (CRITICAL)
```python
# CORRECT: Use model_validate with from_attributes
user_response = UserResponse.model_validate(user, from_attributes=True)

# WRONG: Don't use from_orm()
user_response = UserResponse.from_orm(user)  # Deprecated
```

#### Authentication Pattern
```python
# CORRECT: Read session cookie directly (Ninja doesn't preserve request.user)
def _get_current_user(request):
    from apps.core.auth import get_authenticated_user
    return get_authenticated_user(request)

# WRONG: Don't rely on request.user with Ninja decorators
@require_admin  # This doesn't work with Ninja's pagination
```

#### Entity Scoping
```python
from apps.core.permissions import scope_entity

# In router:
user = _get_current_user(request)
queryset = scope_entity(Dog.objects.all(), user)
```

### 6.2 Frontend (TypeScript/React)

#### TypeScript Strict Mode
- `strict: true` in `tsconfig.json`
- Never use `any` - use `unknown` instead
- Explicit types on all function parameters
- Use `interface` for object shapes, `type` for unions

#### Client Component Boundaries
```typescript
// Server Component by default
export default async function DashboardPage() {
  const user = await getCurrentUser();
  return <div>{user.name}</div>;
}

// 'use client' only when needed
'use client';
export function StatCards() {
  const { data } = useQuickStats(); // Hook requires client
  return <div>{data.total_dogs}</div>;
}
```

#### Optional Props (TypeScript Strict)
```typescript
// CORRECT: explicit | undefined
interface Props {
  entityId?: string | undefined;
}

// WRONG: missing undefined
interface Props {
  entityId?: string;  // Fails with exactOptionalPropertyTypes
}
```

### 6.3 Design System (Tangerine Sky)
```typescript
// Colors
const COLORS = {
  background: '#DDEEFF',
  sidebar: '#E8F4FF',
  primary: '#F97316',    // Orange
  secondary: '#0891B2',  // Teal
  success: '#4EAD72',
  warning: '#D4920A',
  error: '#D94040',
  text: '#0D2030',
  muted: '#4A7A94',
  border: '#C0D8EE',
};

// Usage in Tailwind
<div className="bg-[#F97316] text-white hover:bg-[#EA580C]">
```

---

## 7. Security & Compliance (Singapore-Specific)

### 7.1 PDPA Compliance
- **Hard filter:** `WHERE pdpa_consent=true` at query level
- **No PII without consent:** Check consent before displaying customer data
- **Audit logging:** All consent changes logged to immutable AuditLog

### 7.2 AVS Compliance
- **NParks submissions:** Monthly Excel generation via `openpyxl`
- **AVS transfer tracking:** Token-based links with 72h reminders
- **Dual-sire records:** Proper pedigree documentation

### 7.3 GST (Singapore)
```python
# Formula: price * 9 / 109, ROUND_HALF_UP
from decimal import Decimal, ROUND_HALF_UP

def extract_gst(price: Decimal, entity) -> Decimal:
    if entity.code == 'THOMSON':
        return Decimal('0.00')  # GST exempt
    gst = (price * Decimal('9') / Decimal('109')).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    return gst
```

---

## 8. Common Issues & Solutions

### 8.1 Import Errors
```python
# Issue: django_ratelimit.exceptions not ratelimit.exceptions
from django_ratelimit.exceptions import Ratelimited  # CORRECT
from ratelimit.exceptions import Ratelimited          # WRONG
```

### 8.2 NinjaAPI Configuration
```python
# Issue: csrf parameter not valid
api = NinjaAPI(
    title="Wellfond BMS",
    version="1.0.0",
    # csrf=True,  # WRONG - not a valid parameter
)
```

### 8.3 TypeScript Optional Props
```typescript
// Error: Type 'string | undefined' not assignable
interface Props {
  entityId?: string | undefined;  // CORRECT - explicit undefined
}
```

### 8.4 Dashboard Router URL
```python
# URL pattern for dashboard
/api/v1/dashboard/metrics  # GET - Returns role-aware dashboard data
```

### 8.5 SalesAgreement Status Access
```python
# Issue: SalesAgreement.Status doesn't exist
# CORRECT: Use AgreementStatus
from apps.sales.models import AgreementStatus
statuses = [AgreementStatus.DRAFT, AgreementStatus.SIGNED]
```

---

## 9. Phase Status

### COMPLETED PHASES

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| **0** | ✅ Complete | Infrastructure, Docker, CI/CD |
| **1** | ✅ Complete | Auth, BFF proxy, RBAC, design system |
| **2** | ✅ Complete | Dogs, Health, Vaccinations |
| **3** | ✅ Complete | Ground ops, PWA, Draminski, SSE |
| **4** | ✅ Complete | Breeding engine, COI, saturation |
| **5** | ✅ Complete | Sales agreements, AVS, PDF |
| **6** | ✅ Complete | Compliance, NParks, GST, PDPA |

### IN PROGRESS

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| **7** | 🔄 50% | Customers, segmentation, blasts |
| **8** | 🔄 80% | Dashboard (just completed!) |

### Phase 8 Dashboard Completion
| Component | Status | Files |
|-----------|--------|-------|
| Backend Service | ✅ | `apps/core/services/dashboard.py` |
| Backend Router | ✅ | `apps/core/routers/dashboard.py` |
| Backend Tests | ✅ | `test_dashboard.py`, `test_dashboard_integration.py` |
| Frontend Hooks | ✅ | `hooks/use-dashboard.ts` |
| Frontend Components | ✅ | `components/dashboard/*.tsx` (7 widgets) |
| Frontend Page | ✅ | `app/(protected)/dashboard/page.tsx` |
| Frontend Tests | ✅ | `tests/dashboard.test.tsx`, `e2e/dashboard.spec.ts` |
| TypeScript | ✅ | 0 errors |

---

## 10. Key API Endpoints

### Dashboard
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard/metrics` | GET | Role-aware dashboard data (caches 60s) |
| `/api/v1/dashboard/activity/stream` | GET | SSE for real-time activity |

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Login with HttpOnly cookie |
| `/api/v1/auth/logout` | POST | Clear session |
| `/api/v1/auth/refresh` | POST | Rotate CSRF token |
| `/api/v1/auth/me` | GET | Current user |

### Operations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dogs/` | GET/POST | Dog CRUD |
| `/api/v1/alerts/` | GET | Dashboard alert cards |
| `/api/v1/ground-logs/` | POST | 7 log types |
| `/api/v1/stream/` | GET | SSE alert stream |

### Breeding
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/breeding/mate-check` | POST | COI calculation |
| `/api/v1/breeding/` | GET/POST | Litter CRUD |

---

## 11. Documentation References

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Original project guidelines |
| `AGENT_BRIEF.md` | This document - single source of truth |
| `IMPLEMENTATION_PLAN.md` | Phase-by-phase roadmap |
| `draft_plan.md` | Technical architecture v1.1 |
| `PHASE_5_TODO.md` | Sales agreements checklist |

---

## 12. Success Criteria

You are successful when:
- [ ] Dashboard loads at `/dashboard` without 404
- [ ] 7 alert cards display with trends
- [ ] NParks countdown shows days remaining
- [ ] Stat cards show correct data per role
- [ ] Activity feed SSE connects and receives events
- [ ] Quick actions are role-aware
- [ ] Page loads <2s (verified with k6)
- [ ] TypeScript typecheck passes (0 errors)
- [ ] Build succeeds
- [ ] All tests pass (pytest + vitest + playwright)

---

## 13. Anti-Patterns to Avoid

### Backend
- ❌ Relying on `request.user` with Ninja decorators
- ❌ Using `from_orm()` instead of `model_validate()`
- ❌ Custom components when shadcn exists
- ❌ Hardcoding entity IDs
- ❌ Storing PII without PDPA consent check
- ❌ Magic numbers (use `lib/constants.ts`)
- ❌ Synchronous AVS calls (use Celery)
- ❌ Using `@paginate` with custom response shapes (manual pagination)
- ❌ Direct model imports in services (circular deps)

### Frontend
- ❌ JWT in localStorage/sessionStorage
- ❌ `any` types (use `unknown`)
- ❌ Python-style docstrings in TypeScript
- ❌ Missing `| undefined` on optional props
- ❌ `'use client'` on data-fetching components

---

## 14. Next Steps

### Immediate (Next 2-3 Days)
1. **Run full test suite:**
   ```bash
   cd backend && python -m pytest apps/core/tests/test_dashboard.py -v
   cd frontend && npm run typecheck && npm run build
   ```

2. **E2E verification:**
   ```bash
   cd frontend && npx playwright test dashboard.spec.ts
   ```

3. **Performance testing:**
   - k6 load test for dashboard <2s load time

### Short-term (Next 1-2 Weeks)
4. **Phase 7 completion:** Customers DB & Marketing Blast
   - Segmentation service
   - Resend/WA blast integration
   - PDPA-enforced sends

5. **Phase 9:** Observability & Production Readiness
   - OpenTelemetry
   - CSP hardening
   - k6 load testing
   - Runbooks

---

## 15. Contact & Support

For questions or clarifications:
1. Check `AGENTS.md` for detailed conventions
2. Review existing code patterns in similar files
3. Follow the Meticulous Approach (ANALYZE → PLAN → VALIDATE → IMPLEMENT → VERIFY → DELIVER)

---

**Document Maintenance:** Update this document when:
- New phases are completed
- Architecture decisions change
- New anti-patterns are discovered
- Testing strategies evolve

**Last Updated By:** AI Agent  
**Version:** 1.0.0
