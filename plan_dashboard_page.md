# Dashboard Implementation Plan

## Goal
Create a role-aware dashboard page (`/dashboard`) with 7 alert cards, NParks countdown widget, mate checker widget, revenue chart, and activity feed SSE — aligning with Phase 8 of draft_plan.md.

## Current State
- Middleware redirects to `/dashboard` but page doesn't exist → 404
- Ground dashboard exists at `/app/(ground)/page.tsx` as mobile reference
- AlertCards component exists at `/components/dogs/alert-cards.tsx`
- Backend has `/alerts/` endpoints including `nparks_countdown`
- No `finance` app yet, so revenue data will come from existing SalesAgreement model

## Implementation Plan

### Phase 1: Backend Dashboard Router

**Files to create:**
1. `backend/apps/core/routers/dashboard.py` — Dashboard metrics endpoint
2. `backend/apps/core/services/dashboard.py` — Dashboard metrics service

**Key features:**
- GET `/dashboard/metrics` — Returns role-aware dashboard data
- Caches for 60s (Redis)
- Metrics include:
  - Alert counts (vaccine_overdue, rehome_overdue, in_heat, nursing_flags, etc.)
  - NParks countdown (days until submission deadline)
  - Recent activity (last 10 audit logs)
  - Entity stats (dog count, active breeding, pending sales)
  - Role-specific sections:
    - Management/Admin: Full view + revenue summary
    - Sales: Sales pipeline + agreements pending
    - Vet: Health alerts + vaccinations

**TDD approach:**
1. Write `test_dashboard.py` with failing tests for metrics endpoint
2. Implement service + router
3. Verify tests pass

### Phase 2: Frontend Dashboard Page

**Files to create:**
1. `frontend/app/(protected)/dashboard/page.tsx` — Main dashboard page
2. `frontend/app/(protected)/dashboard/layout.tsx` — Dashboard layout (no sidebar on mobile)
3. `frontend/hooks/use-dashboard.ts` — TanStack Query hooks for dashboard data
4. `frontend/components/dashboard/`:
   - `npars-countdown.tsx` — NParks deadline countdown card
   - `mate-checker-widget.tsx` — Quick COI check widget
   - `revenue-chart.tsx` — Revenue bar chart (using Recharts)
   - `activity-feed.tsx` — SSE-powered activity stream
   - `stat-cards.tsx` — Summary stat cards (dogs, litters, agreements)
   - `quick-actions.tsx` — Role-based quick action buttons

**Key features:**
- Server Component for initial data fetch
- Client Components for interactivity
- SSE EventSource for real-time activity feed
- Responsive grid layout (1 col mobile, 2 col tablet, 3 col desktop)
- Load time target: <2s on Singapore broadband

**TDD approach:**
1. Write dashboard page tests using Vitest + React Testing Library
2. Implement components with Suspense + Skeleton loading states
3. Run `npm run typecheck` — must pass
4. Run `npm run build` — must succeed

### Phase 3: Dashboard Components Detail

**1. Alert Cards Strip (existing component)**
- Reuse `AlertCards` from `/components/dogs/alert-cards.tsx`
- Shows horizontal scrollable alert cards

**2. NParks Countdown Widget**
```typescript
// Shows days until NParks submission deadline
interface NParksCountdownProps {
  daysRemaining: number;
  deadlineDate: string;
  status: 'upcoming' | 'due_soon' | 'overdue';
}
```

**3. Mate Checker Widget**
- Quick COI check input
- Shows last 5 mate checks
- Link to full breeding page

**4. Revenue Chart**
- Monthly revenue bar chart (last 6 months)
- Uses Recharts library
- Data from SalesAgreement model
- Shows: month, total sales, GST collected

**5. Activity Feed**
- SSE-powered real-time feed
- Shows last 20 audit log entries
- Auto-scroll with pause on hover
- Entries: user, action, timestamp, entity

**6. Stat Cards**
- Total dogs (by status: active, breeding, retired)
- Active litters (puppies < 8 weeks)
- Pending agreements (sales)
- Overdue vaccinations

**7. Quick Actions**
- Role-aware buttons:
  - Management: Add Dog, Create Agreement, Run Report
  - Sales: Create Agreement, View Pipeline
  - Vet: Health Check, Vaccination Round

### Phase 4: Testing & Validation

**Backend tests:**
- `test_dashboard.py` — Test metrics endpoint with different roles
- Verify entity scoping
- Verify caching

**Frontend tests:**
- `dashboard.test.tsx` — Component rendering tests
- `use-dashboard.test.ts` — Hook tests with MSW
- Run `npm run test` — must pass

**Integration tests:**
- E2E with Playwright: Dashboard loads, alerts display, SSE connects

**Performance:**
- Lighthouse score ≥90
- Load time <2s (k6 test)

## Files to Modify

### Backend
- `backend/apps/core/routers/__init__.py` — Export dashboard router
- `backend/api/__init__.py` — Register dashboard router

### Frontend
- `frontend/middleware.ts` — Ensure `/dashboard` redirect works
- `frontend/lib/constants.ts` — Add dashboard to NAV_ITEMS if not present

## Success Criteria
- [ ] `/dashboard` page loads without 404
- [ ] 7 alert cards display with trends
- [ ] NParks countdown shows days remaining
- [ ] Mate checker widget functional
- [ ] Revenue chart renders with data
- [ ] Activity feed SSE connects and receives events
- [ ] Role-aware: Management sees all, Sales sees sales-only, Vet sees health-only
- [ ] Page loads <2s (verified with k6)
- [ ] TypeScript typecheck passes
- [ ] Build succeeds
- [ ] All tests pass

## Dependencies to Check
- Recharts (for revenue chart) — may need to install
- Existing: @tanstack/react-query, lucide-react, framer-motion

## Open Questions
1. Should we create a separate `finance` app for revenue data, or use SalesAgreement model?
2. What exact alert types should be shown? (Current plan: vaccine_overdue, rehome_overdue, in_heat, nursing_flags, 8week_litters, nparks_countdown, health_flags)
3. Should the mate checker widget perform actual COI calculation or just link to breeding page?

## Notes
- The dashboard is in `(protected)` group — requires authentication
- Mobile view should prioritize alert cards and quick actions
- Use existing color palette from constants.ts
- Follow existing patterns: TanStack Query for data, SSE for real-time
