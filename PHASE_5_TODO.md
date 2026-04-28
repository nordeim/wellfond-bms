# Phase 5: Sales Agreements & AVS Tracking — Detailed ToDo List

**Status:** Ready for Execution | **Timeline:** 10–12 days  
**Dependencies:** Phase 1 ✅, Phase 2 ✅, Phase 4 ✅  
**Alignment Verified:** draft_plan.md v1.1 ✅, IMPLEMENTATION_PLAN.md ✅, phase-5-sales-avs.md ✅

---

## Pre-Execution Validation

### Dependencies Check
| Dependency | Status | Verification |
|------------|--------|--------------|
| Phase 1 (Auth, BFF, RBAC) | ✅ Complete | HttpOnly cookies, role matrix, idempotency middleware |
| Phase 2 (Domain Models) | ✅ Complete | Dog, Entity models, CSV import, entity scoping |
| Phase 4 (Breeding) | ✅ Complete | BreedingRecord, Litter, Puppy models, closure table |
| Gotenberg Container | ✅ Ready | Sidecar configured in docker-compose.yml |
| Celery Workers | ✅ Ready | `@shared_task` pattern established |

### Architecture Principles Verified
- [x] BFF Proxy with path allowlist and header sanitization
- [x] HttpOnly cookies via BFF (zero JWT exposure)
- [x] Entity scoping at queryset level (RLS dropped per v1.1)
- [x] Gotenberg PDF generation (not WeasyPrint)
- [x] Native Celery `@shared_task` (no django.tasks bridge)
- [x] GST calculation: `price * 9 / 109`, `ROUND_HALF_UP`
- [x] Immutable audit trails for signatures

---

## Phase 5 Execution Steps

### 🔧 Step 1: Backend Models & Schemas (Days 1–2)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 1.1 | Create SalesAgreement model | `backend/apps/sales/models.py` | High | 2h | Phase 2 Dog model |
| 1.2 | Create AgreementLineItem model | `backend/apps/sales/models.py` | High | 1h | SalesAgreement |
| 1.3 | Create AVSTransfer model | `backend/apps/sales/models.py` | High | 1.5h | SalesAgreement |
| 1.4 | Create Signature model | `backend/apps/sales/models.py` | High | 1.5h | SalesAgreement |
| 1.5 | Create TCTemplate model | `backend/apps/sales/models.py` | Medium | 1h | - |
| 1.6 | Create Pydantic schemas | `backend/apps/sales/schemas.py` | High | 3h | All models |
| 1.7 | Create Django migrations | `backend/apps/sales/migrations/` | High | 1h | Models complete |
| 1.8 | Apply migrations | Database | High | 0.5h | Migrations created |

**Step 1 Deliverables:**
- [ ] 5 models with proper FKs, indexes, constraints
- [ ] Pydantic schemas for all CRUD operations
- [ ] Database migrations applied successfully
- [ ] Admin panel configuration

---

### 🔧 Step 2: Backend Services (Days 3–5)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 2.1 | Create agreement service | `backend/apps/sales/services/agreement.py` | High | 4h | Step 1 complete |
| 2.2 | Implement state machine (DRAFT→SIGNED→COMPLETED) | `backend/apps/sales/services/agreement.py` | High | 2h | - |
| 2.3 | Implement GST extraction (`price * 9 / 109`) | `backend/apps/sales/services/agreement.py` | High | 2h | - |
| 2.4 | Add HDB warning logic | `backend/apps/sales/services/agreement.py` | Medium | 1.5h | - |
| 2.5 | Create PDF service with Gotenberg | `backend/apps/sales/services/pdf.py` | High | 4h | - |
| 2.6 | Implement SHA-256 hash computation | `backend/apps/sales/services/pdf.py` | High | 1h | - |
| 2.7 | Add dev fallback (HTML output) | `backend/apps/sales/services/pdf.py` | Medium | 2h | - |
| 2.8 | Create AVS service | `backend/apps/sales/services/avs.py` | High | 4h | - |
| 2.9 | Implement token generation (UUID4) | `backend/apps/sales/services/avs.py` | High | 1h | - |
| 2.10 | Implement AVS link sending (email/WA) | `backend/apps/sales/services/avs.py` | High | 2h | - |
| 2.11 | Add escalation logic | `backend/apps/sales/services/avs.py` | Medium | 1.5h | - |

**Step 2 Deliverables:**
- [ ] Agreement service with state machine
- [ ] GST calculation exact to 2 decimals (Thomson=0%)
- [ ] PDF service with Gotenberg integration
- [ ] SHA-256 hash stored on agreement
- [ ] AVS service with token generation and tracking
- [ ] HDB warning for large breeds

---

### 🔧 Step 3: Backend Routers (Days 5–6)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 3.1 | Create agreements router | `backend/apps/sales/routers/agreements.py` | High | 4h | Step 2 complete |
| 3.2 | Implement POST /agreements (create draft) | `backend/apps/sales/routers/agreements.py` | High | 2h | - |
| 3.3 | Implement PATCH /agreements/{id} (update) | `backend/apps/sales/routers/agreements.py` | High | 1.5h | - |
| 3.4 | Implement POST /agreements/{id}/sign | `backend/apps/sales/routers/agreements.py` | High | 2h | - |
| 3.5 | Implement POST /agreements/{id}/send | `backend/apps/sales/routers/agreements.py` | High | 2h | - |
| 3.6 | Implement GET /agreements (list with filters) | `backend/apps/sales/routers/agreements.py` | High | 1.5h | - |
| 3.7 | Create AVS router | `backend/apps/sales/routers/avs.py` | High | 3h | - |
| 3.8 | Implement GET /avs/pending | `backend/apps/sales/routers/avs.py` | High | 1h | - |
| 3.9 | Implement POST /avs/{id}/complete | `backend/apps/sales/routers/avs.py` | High | 1h | - |
| 3.10 | Register routers in API | `backend/api/__init__.py` | High | 0.5h | - |

**Step 3 Deliverables:**
- [ ] Agreements router with all CRUD endpoints
- [ ] AVS router with pending/completion endpoints
- [ ] Entity scoping on all queries
- [ ] Routers registered in main API

---

### 🔧 Step 4: Celery Tasks (Days 6–7)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 4.1 | Create tasks module | `backend/apps/sales/tasks.py` | High | 0.5h | Step 3 complete |
| 4.2 | Implement send_agreement_pdf task | `backend/apps/sales/tasks.py` | High | 3h | PDF service |
| 4.3 | Add retry logic (3x exponential) | `backend/apps/sales/tasks.py` | High | 1h | - |
| 4.4 | Implement DLQ routing | `backend/apps/sales/tasks.py` | High | 1h | - |
| 4.5 | Implement avs_reminder_check task | `backend/apps/sales/tasks.py` | High | 3h | AVS service |
| 4.6 | Add Celery Beat schedule | `backend/config/celery.py` | High | 1h | - |
| 4.7 | Test task execution | Celery worker | High | 1h | - |

**Step 4 Deliverables:**
- [ ] PDF generation task with retry
- [ ] AVS reminder task with 72h schedule
- [ ] DLQ configuration
- [ ] Tasks registered in Celery

---

### 🔧 Step 5: Backend Admin & Tests (Days 7–8)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 5.1 | Configure Django admin | `backend/apps/sales/admin.py` | Medium | 2h | Step 1 complete |
| 5.2 | Create test factories | `backend/apps/sales/tests/factories.py` | High | 2h | - |
| 5.3 | Write agreement tests (12 cases) | `backend/apps/sales/tests/test_agreements.py` | High | 6h | - |
| 5.4 | Test GST calculations | `backend/apps/sales/tests/test_agreements.py` | High | 1h | - |
| 5.5 | Test state machine | `backend/apps/sales/tests/test_agreements.py` | High | 1h | - |
| 5.6 | Test PDF hash | `backend/apps/sales/tests/test_agreements.py` | High | 1h | - |
| 5.7 | Write AVS tests (6 cases) | `backend/apps/sales/tests/test_avs.py` | High | 4h | - |
| 5.8 | Test reminder/escalation | `backend/apps/sales/tests/test_avs.py` | High | 1h | - |
| 5.9 | Run all tests | pytest | High | 0.5h | - |

**Step 5 Deliverables:**
- [ ] Django admin configured
- [ ] 18 tests (12 agreement + 6 AVS) passing
- [ ] GST tests: 109→9.00, 218→18.00, 50→4.13, Thomson→0
- [ ] 100% test coverage for services

---

### 🔧 Step 6: Frontend Components (Days 8–10)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 6.1 | Create wizard steps component | `frontend/components/sales/wizard-steps.tsx` | High | 6h | - |
| 6.2 | Step 1: Dog Selection UI | `frontend/components/sales/wizard-steps.tsx` | High | 2h | - |
| 6.3 | Step 2: Buyer Details with HDB warning | `frontend/components/sales/wizard-steps.tsx` | High | 2h | - |
| 6.4 | Step 3: Health Disclosure | `frontend/components/sales/wizard-steps.tsx` | Medium | 1.5h | - |
| 6.5 | Step 4: Pricing with GST display | `frontend/components/sales/wizard-steps.tsx` | High | 2h | - |
| 6.6 | Step 5: T&C & Signature | `frontend/components/sales/wizard-steps.tsx` | High | 2h | - |
| 6.7 | Create agreement preview component | `frontend/components/sales/agreement-preview.tsx` | Medium | 3h | - |
| 6.8 | Create signature pad component | `frontend/components/ui/signature-pad.tsx` | High | 4h | - |
| 6.9 | Canvas touch + mouse drawing | `frontend/components/ui/signature-pad.tsx` | High | 2h | - |
| 6.10 | Coordinate capture + export | `frontend/components/ui/signature-pad.tsx` | High | 2h | - |

**Step 6 Deliverables:**
- [ ] 5-step wizard component
- [ ] Live preview panel
- [ ] Signature pad with coordinate capture
- [ ] HDB warning banner
- [ ] GST calculation display
- [ ] Deposit non-refundable notice

---

### 🔧 Step 7: Frontend Pages (Days 10–11)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 7.1 | Create sales list page | `frontend/app/(protected)/sales/page.tsx` | High | 4h | - |
| 7.2 | Agreement table with filters | `frontend/app/(protected)/sales/page.tsx` | High | 2h | - |
| 7.3 | Create new agreement buttons | `frontend/app/(protected)/sales/page.tsx` | High | 1h | - |
| 7.4 | Create wizard page | `frontend/app/(protected)/sales/wizard/page.tsx` | High | 4h | Step 6 |
| 7.5 | Step indicator (1-5) | `frontend/app/(protected)/sales/wizard/page.tsx` | High | 1h | - |
| 7.6 | Back/Next/Submit buttons | `frontend/app/(protected)/sales/wizard/page.tsx` | High | 1h | - |
| 7.7 | Step validation | `frontend/app/(protected)/sales/wizard/page.tsx` | High | 1h | - |
| 7.8 | Success redirect | `frontend/app/(protected)/sales/wizard/page.tsx` | Medium | 0.5h | - |

**Step 7 Deliverables:**
- [ ] Sales agreements list page
- [ ] 5-step wizard page
- [ ] TypeScript types aligned with schemas
- [ ] Responsive layout

---

### 🔧 Step 8: Frontend Hooks & Integration (Days 11–12)

| # | Task | File | Priority | Est. Time | Dependencies |
|---|------|------|----------|-----------|--------------|
| 8.1 | Create sales hooks | `frontend/hooks/use-sales.ts` | High | 3h | - |
| 8.2 | useAgreements hook | `frontend/hooks/use-sales.ts` | High | 1h | - |
| 8.3 | useCreateAgreement hook | `frontend/hooks/use-sales.ts` | High | 1h | - |
| 8.4 | useSignAgreement hook | `frontend/hooks/use-sales.ts` | High | 1h | - |
| 8.5 | useSendAgreement hook | `frontend/hooks/use-sales.ts` | High | 1h | - |
| 8.6 | Wire up wizard to API | Wizard components | High | 2h | All hooks |
| 8.7 | Wire up list to API | List components | High | 1h | - |
| 8.8 | Error handling + toast | All components | High | 1h | - |
| 8.9 | Loading states | All components | Medium | 1h | - |

**Step 8 Deliverables:**
- [ ] TanStack Query hooks for all operations
- [ ] API integration complete
- [ ] Error handling with toast notifications
- [ ] Loading states on buttons

---

## Phase 5 Validation Checklist

### Functional Requirements
- [ ] B2C flow: select dog → buyer → health → pricing → sign → PDF → send → AVS link
- [ ] B2B flow: multiple dogs, line items, subtotal/GST/total auto-calc
- [ ] Rehoming flow: $0 price, transfer form, no invoice
- [ ] GST: 109→9.00, 218→18.00, 50→4.13 (exact to 2 decimals)
- [ ] Thomson entity: GST = 0.00
- [ ] PDF: generated via Gotenberg, SHA-256 hash stored
- [ ] PDF: tamper-evident (hash matches on re-download)
- [ ] Signature: coordinates captured, IP logged, timestamp recorded
- [ ] AVS: unique token per buyer, link sent
- [ ] AVS: reminder fires at 72h (Celery Beat)
- [ ] AVS: escalation after reminder (staff notified)
- [ ] HDB warning: shows for large breeds in HDB housing
- [ ] Deposit: non-refundable banner prominent on pricing step
- [ ] PDPA: opt-in required, enforced on step 2
- [ ] T&C: admin-editable, versioned, applies to future agreements
- [ ] Wizard: step validation blocks forward progress

### Technical Requirements
- [ ] All backend tests pass (18/18)
- [ ] Frontend TypeScript compiles with 0 errors
- [ ] Frontend build succeeds
- [ ] Entity scoping prevents cross-entity data leakage
- [ ] Idempotency keys prevent duplicate submissions
- [ ] PDF service has dev fallback
- [ ] Celery tasks execute successfully
- [ ] AVS reminders trigger on schedule

### Security & Compliance
- [ ] HttpOnly cookies for authentication
- [ ] BFF proxy with path allowlist
- [ ] Entity scoping on all queries
- [ ] PDPA opt-in enforced at API level
- [ ] SHA-256 hash for PDF integrity
- [ ] Audit log captures all agreement actions
- [ ] Signature coordinates + IP + timestamp recorded
- [ ] No JWT exposure to client JS

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gotenberg unavailable in dev | Dev fallback to HTML output or mock PDF |
| WhatsApp API template rejection | Email fallback with channel switch logging |
| Large PDF generation timeout | Async Celery task with progress polling |
| Mobile signature pad issues | Test on iOS Safari + Android Chrome |
| GST calculation edge cases | Unit tests for all GST scenarios |
| Concurrent agreement edits | Optimistic locking or last-write-wins |

---

## Post-Phase 5 Readiness

### Deliverables
1. **Backend**: 5 models, 3 services, 2 routers, 2 task files, 2 test files
2. **Frontend**: 3 components, 2 pages, 1 hook file
3. **Tests**: 18 backend tests, 100% service coverage
4. **Documentation**: Updated API schema, component docs

### Next Phase Dependencies
- Phase 6 (Compliance & NParks) requires:
  - SalesAgreement model ✅
  - AgreementLineItem model ✅
  - GST calculation service ✅
  - Audit logging ✅

---

**Created:** April 28, 2026  
**Last Updated:** April 28, 2026  
**Phase 5 Status:** Ready to Start Execution 🚀
