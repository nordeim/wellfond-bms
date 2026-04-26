# Phase 3: Ground Operations & Mobile PWA — Alignment Review Report

**Review Date:** April 26, 2026  
**Reviewers:** Technical Lead, Frontend Architect  
**Status:** ✅ ALIGNED — Ready for Execution

---

## 1. Executive Summary

**Phase 3** is **100% aligned** across all master plans:
- ✅ `draft_plan.md` (v1.1) — Phase 3 section
- ✅ `IMPLEMENTATION_PLAN.md` — Phase 3 section (lines 507-550)
- ✅ `plans/phase-3-ground-operations.md` — Sub-plan

All three documents specify:
- 7 ground log types (in_heat, mated, whelped, health_obs, weight, nursing_flag, not_ready)
- Draminski DOD2 interpreter with per-dog thresholds
- SSE streaming for real-time alerts (<500ms)
- PWA offline queue with IndexedDB + Background Sync
- UUIDv4 idempotency keys for exactly-once delivery
- Mobile-first UI with 44px tap targets

**Execution Readiness:** ✅ GREEN — All specifications verified, dependencies ready

---

## 2. Detailed Alignment Matrix

### 2.1 Backend Models

| Component | draft_plan.md (v1.1) | IMPLEMENTATION_PLAN.md | phase-3-sub-plan | Status |
|-----------|---------------------|------------------------|------------------|--------|
| **InHeatLog** | `dog, draminski_reading, mating_window, notes, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |
| **MatedLog** | `dog, sire, method, sire2, notes, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |
| **WhelpedLog** | `dog, method, alive_count, stillborn_count, pups, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |
| **HealthObsLog** | `dog, category, description, temp, weight, photos, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |
| **WeightLog** | `dog, weight, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |
| **NursingFlagLog** | `dog, section, pup_number, flag_type, photos, severity, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |
| **NotReadyLog** | `dog, notes, edd, staff, ts` | ✅ Listed | ✅ Detailed spec | ✅ |

**Alignment Notes:**
- All 7 log types match exactly across all three documents
- Schema requirements aligned (Pydantic v2)
- Auto-capture of `request.user` and timestamp specified everywhere

### 2.2 Draminski Interpreter

| Feature | draft_plan.md (v1.1) | IMPLEMENTATION_PLAN.md | phase-3-sub-plan | Status |
|---------|---------------------|------------------------|------------------|--------|
| **Per-dog baseline** | ✅ "Baseline per dog, not global" | ✅ Listed | ✅ Detailed spec | ✅ |
| **Thresholds** | `<200/200-400/400+/peak/drop` | ✅ Listed | ✅ Listed with logic | ✅ |
| **MATE NOW** | "post-peak drop" trigger | ✅ Listed | ✅ "MATE NOW on post-peak drop" | ✅ |
| **7-day trend** | "7-day trend array" | ✅ Listed | ✅ Detailed spec | ✅ |
| **Pure math** | "Pure math, no AI" | ✅ Listed | ✅ Emphasized | ✅ |

**Alignment Notes:**
- Thresholds: `<200` early, `200-400` rising, `400+` fast, `peak` = highest, `post-peak drop` = MATE NOW
- Per-dog baseline calculation: mean of last 30 readings
- 7-day trend array format: `[{date, reading, zone}]`

### 2.3 SSE (Server-Sent Events)

| Feature | draft_plan.md (v1.1) | IMPLEMENTATION_PLAN.md | phase-3-sub-plan | Status |
|---------|---------------------|------------------------|------------------|--------|
| **Endpoint** | `GET /operations/stream/alerts` | ✅ Listed | ✅ Same | ✅ |
| **Content type** | `text/event-stream` | ✅ Listed | ✅ Same | ✅ |
| **Delivery time** | "<500ms" | ✅ Listed | ✅ "<500ms" | ✅ |
| **Auto-reconnect** | "Reconnect-safe" | ✅ Listed | ✅ "Auto-reconnect" | ✅ |
| **Filtering** | "Filters by user role/entity" | ✅ Listed | ✅ "Filters by role/entity" | ✅ |
| **Backpressure** | "Backpressure handled" | ✅ Listed | ✅ Listed | ✅ |

**Alignment Notes:**
- Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- Format: `data: {json}\n\n`
- Poll interval: 5 seconds

### 2.4 PWA Offline Queue

| Feature | draft_plan.md (v1.1) | IMPLEMENTATION_PLAN.md | phase-3-sub-plan | Status |
|---------|---------------------|------------------------|------------------|--------|
| **Idempotency key** | "UUIDv4 idempotency key" | ✅ Listed | ✅ "UUIDv4" | ✅ |
| **Storage** | "IndexedDB" | ✅ Listed | ✅ "IndexedDB" | ✅ |
| **Conflict resolution** | "Server wins" | ✅ Listed | ✅ "server wins" | ✅ |
| **Retry logic** | "Idempotent retry" | ✅ Listed | ✅ "3 attempts" | ✅ |
| **Background sync** | "Background sync on reconnect" | ✅ Listed | ✅ "flush on reconnect" | ✅ |
| **UI badge** | "UI badge: 3 logs pending" | ✅ Listed | ✅ "Badge shows pending" | ✅ |

**Alignment Notes:**
- Redis store TTL: 24 hours
- Conflict toast: "already recorded"
- Exponential backoff for retries

### 2.5 Frontend Components

| Component | draft_plan.md (v1.1) | IMPLEMENTATION_PLAN.md | phase-3-sub-plan | Status |
|-----------|---------------------|------------------------|------------------|--------|
| **Ground layout** | "Bottom nav (no sidebar)" | ✅ Listed | ✅ Detailed spec | ✅ |
| **44px tap targets** | ✅ Specified | ✅ Listed | ✅ "44px minimum" | ✅ |
| **High contrast** | "#0D2030 on #DDEEFF" | ✅ Listed | ✅ Same colors | ✅ |
| **Numpad** | "Numpad input" | ✅ Listed | ✅ "48px buttons" | ✅ |
| **Draminski chart** | "7-day line chart" | ✅ Listed | ✅ Detailed spec | ✅ |
| **Camera scan** | "Camera API fallback" | ✅ Listed | ✅ "BarcodeDetector API" | ✅ |
| **Service Worker** | "sw.ts" | ✅ Listed | ✅ Detailed spec | ✅ |

---

## 3. Dependency Verification

### 3.1 Pre-requisites (Completed in Phase 2)

| Dependency | Phase 2 Deliverable | Status |
|------------|---------------------|--------|
| **Dog model** | `Dog` with microchip, FKs | ✅ Complete |
| **User model** | `User` with role, entity | ✅ Complete |
| **Entity scoping** | `scope_entity()` helper | ✅ Complete |
| **Idempotency middleware** | `IdempotencyMiddleware` | ✅ Complete |
| **BFF proxy** | `/api/proxy/` working | ✅ Complete |
| **Design system** | Tangerine Sky theme | ✅ Complete |
| **Database** | PostgreSQL + migrations | ✅ Complete |
| **Redis** | 3 instances | ✅ Complete |

### 3.2 New Dependencies (Phase 3 Specific)

| Dependency | Purpose | Installation |
|------------|---------|--------------|
| **IndexedDB** | Offline queue storage | Browser API (no install) |
| **BarcodeDetector API** | Camera barcode scanning | Browser API (Chrome 83+) |
| **EventSource** | SSE client | Browser API (no install) |
| **Service Worker** | PWA offline support | Browser API (no install) |

---

## 4. File Implementation Checklist

### Backend Files

| # | File Path | Line Count | Priority | Status |
|---|-----------|------------|----------|--------|
| 1 | `backend/apps/operations/models.py` (extend) | +200 | HIGH | ⬜ |
| 2 | `backend/apps/operations/schemas.py` (extend) | +150 | HIGH | ⬜ |
| 3 | `backend/apps/operations/services/draminski.py` | ~150 | HIGH | ⬜ |
| 4 | `backend/apps/operations/services/alerts.py` (extend) | +50 | MEDIUM | ⬜ |
| 5 | `backend/apps/operations/routers/logs.py` | ~200 | HIGH | ⬜ |
| 6 | `backend/apps/operations/routers/stream.py` | ~100 | HIGH | ⬜ |
| 7 | `backend/apps/operations/tasks.py` | ~100 | MEDIUM | ⬜ |
| 8 | `backend/apps/operations/tests/test_logs.py` | ~200 | HIGH | ⬜ |
| 9 | `backend/apps/operations/tests/test_draminski.py` | ~150 | HIGH | ⬜ |

**Total Backend:** ~9 files, ~1,300 lines

### Frontend Files

| # | File Path | Line Count | Priority | Status |
|---|-----------|------------|----------|--------|
| 10 | `frontend/app/ground/layout.tsx` | ~100 | HIGH | ⬜ |
| 11 | `frontend/app/ground/page.tsx` | ~200 | HIGH | ⬜ |
| 12 | `frontend/app/ground/log/[type]/page.tsx` | ~400 | HIGH | ⬜ |
| 13 | `frontend/components/ground/numpad.tsx` | ~150 | HIGH | ⬜ |
| 14 | `frontend/components/ground/draminski-chart.tsx` | ~200 | HIGH | ⬜ |
| 15 | `frontend/components/ground/log-form.tsx` | ~200 | HIGH | ⬜ |
| 16 | `frontend/components/ground/camera-scan.tsx` | ~200 | MEDIUM | ⬜ |
| 17 | `frontend/lib/pwa/sw.ts` | ~150 | HIGH | ⬜ |
| 18 | `frontend/lib/pwa/register.ts` | ~100 | HIGH | ⬜ |
| 19 | `frontend/lib/offline-queue.ts` | ~250 | HIGH | ⬜ |
| 20 | `frontend/hooks/use-sse.ts` | ~100 | HIGH | ⬜ |
| 21 | `frontend/hooks/use-offline-queue.ts` | ~100 | MEDIUM | ⬜ |

**Total Frontend:** ~12 files, ~2,150 lines

**Phase 3 Total:** ~21 files, ~3,450 lines

---

## 5. Success Criteria Verification

### Phase 3 Checklist Alignment

| Criterion | draft_plan.md | IMPLEMENTATION_PLAN.md | phase-3-sub-plan | Aligned |
|-----------|---------------|------------------------|------------------|---------|
| All 7 log types persist | ✅ | ✅ | ✅ | ✅ |
| Draminski thresholds exact | ✅ "matches PRD" | ✅ "matches PRD" | ✅ Detailed tests | ✅ |
| SSE <500ms delivery | ✅ | ✅ | ✅ | ✅ |
| Offline queue sync | ✅ | ✅ | ✅ | ✅ |
| PWA Lighthouse ≥90 | ✅ | ✅ | ✅ | ✅ |
| 44px tap targets | ✅ | ✅ | ✅ | ✅ |
| High-contrast WCAG AA | ✅ | ✅ | ✅ | ✅ |
| Camera scan + fallback | ✅ | ✅ | ✅ | ✅ |

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Browser API compatibility** | Medium | High | Feature detection + graceful fallbacks |
| **SSE connection stability** | Low | Medium | Auto-reconnect with exponential backoff |
| **IndexedDB quota exceeded** | Low | Medium | LRU eviction, size warnings |
| **Draminski calculation accuracy** | Low | High | Comprehensive unit tests |
| **PWA offline UX** | Medium | Medium | Clear offline indicators, queue counts |

---

## 7. Execution Recommendation

### ✅ PROCEED TO IMPLEMENTATION

**Justification:**
1. All three master plans are **100% aligned**
2. Phase 2 dependencies are **complete**
3. Specifications are **detailed and testable**
4. No architectural conflicts identified
5. Risk profile is **acceptable**

### Recommended Execution Order

```
Step 1: Backend models (extend operations/models.py)        [Day 1-2]
Step 2: Backend schemas (extend operations/schemas.py)      [Day 1-2]
Step 3: Backend services (draminski.py, extend alerts.py)    [Day 2-3]
Step 4: Backend routers (logs.py, stream.py)                 [Day 3-4]
Step 5: Backend tasks (Celery)                               [Day 4]
Step 6: Backend tests                                        [Day 5]
Step 7: Frontend ground layout & pages                       [Day 6-8]
Step 8: Frontend ground components                           [Day 8-10]
Step 9: Frontend PWA (sw.ts, offline-queue.ts)             [Day 11-12]
Step 10: Frontend hooks (use-sse.ts, use-offline-queue.ts) [Day 13]
Step 11: Integration & validation                            [Day 14]
```

**Total Estimated Duration:** 10-14 days

---

## 8. Sign-off

| Role | Name | Status | Date |
|------|------|--------|------|
| **Architecture Lead** | [REDACTED] | ✅ Approved | Apr 26, 2026 |
| **Frontend Architect** | [REDACTED] | ✅ Approved | Apr 26, 2026 |
| **Technical Lead** | [REDACTED] | ✅ Approved | Apr 26, 2026 |

**Next Action:** Proceed to Phase 3 implementation per execution order above.

---

*Document Version: 1.0*  
*Last Updated: April 26, 2026*  
*Classification: Internal*
