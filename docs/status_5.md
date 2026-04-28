## Analysis: Phase 5 Plans Alignment
Summary of Alignment Check
| Aspect | Phase 5 Sub-Plan | draft_plan.md (v1.1) | IMPLEMENTATION_PLAN.md | Alignment Status |
|--------|------------------|----------------------|------------------------|------------------|
| Timeline | 10–12 days | Phase 5 section | Phase 5 section | ✅ Aligned |
| Dependencies | Phase 2, Phase 1 | Phase 2, Phase 1, Phase 4 | Phase 2, Phase 1 | ✅ Aligned |
| Success Criteria | PDF hashed, AVS 72h reminder, E-sign, GST exact | Same + cryptographically hashed | Same + SHA-256 hash | ✅ Aligned |
| Backend Models | SalesAgreement, AgreementLineItem, AVSTransfer, Signature, TCTemplate | Same | Same | ✅ Aligned |
| PDF Generation | Gotenberg sidecar | Gotenberg sidecar | Gotenberg sidecar | ✅ Aligned |
| GST Calculation | price * 9 / 109, ROUND_HALF_UP | Same | Same | ✅ Aligned |
| AVS Reminder | Celery Beat, 72h, escalation | Same | Same | ✅ Aligned |
| E-Signature | Canvas pad, coordinates, IP, timestamp | Same | Same | ✅ Aligned |
| Wizard Steps | 5 steps (Dog→Buyer→Health→Pricing→T&C) | Same | Same | ✅ Aligned |
Key Alignment Findings:
1. ✅ Excellent Alignment: All three documents agree on core architecture, models, services, and features.
2. ✅ Dependencies Met: 
   - Phase 1 (Auth, BFF, RBAC) ✅ Complete
   - Phase 2 (Domain Foundation) ✅ Complete
   - Phase 4 (Breeding) ✅ Complete (COI, saturation, breeding records)
3. ✅ Architecture Consistent:
   - HttpOnly cookies via BFF proxy
   - Gotenberg PDF generation (not WeasyPrint)
   - Native Celery @shared_task (no django.tasks bridge)
   - Entity scoping (RLS dropped per v1.1)
4. ✅ Compliance Requirements Covered:
   - GST 9/109 calculation with ROUND_HALF_UP
   - PDPA opt-in checkbox
   - SHA-256 PDF hash for tamper-evidence
   - Immutable audit trail for signatures
5. ⚠️ One Minor Gap: 
   - Phase 5 Sub-Plan mentions "Development mock PDF generation" 
   - IMPLEMENTATION_PLAN.md doesn't explicitly mention mock fallback
   - Recommendation: Add Gotenberg health check with graceful fallback to HTML output in dev
Critical Files Required (from alignment analysis):
Backend (8 files):
1. backend/apps/sales/models.py - 5 models
2. backend/apps/sales/schemas.py - Pydantic schemas
3. backend/apps/sales/services/agreement.py - State machine, GST calc
4. backend/apps/sales/services/pdf.py - Gotenberg integration
5. backend/apps/sales/services/avs.py - AVS link gen, tracking
6. backend/apps/sales/routers/agreements.py - CRUD endpoints
7. backend/apps/sales/routers/avs.py - AVS endpoints
8. backend/apps/sales/tasks.py - Celery tasks (PDF gen, reminders)
Frontend (3 files):
1. frontend/components/sales/wizard-steps.tsx - 5-step wizard
2. frontend/components/sales/agreement-preview.tsx - Live preview
3. frontend/components/ui/signature-pad.tsx - Canvas signature
Frontend Pages (2 files):
1. frontend/app/(protected)/sales/page.tsx - List view
2. frontend/app/(protected)/sales/wizard/page.tsx - Wizard
Tests (2 files):
1. backend/apps/sales/tests/test_agreements.py - 12 test cases
2. backend/apps/sales/tests/test_avs.py - 6 test cases
---
Detailed Phase 5 ToDo List
Based on meticulous alignment analysis, here's the execution plan:
I'll now create the detailed ToDo list based on this analysis.

## ✅ Phase 5 Planning Complete
Planning Documents Analyzed
Document	Key Insights
phase-5-sales-avs.md	Detailed 7-step execution order. 100-line spec with file-by-file requirements. Success criteria: PDF hash, 72h AVS reminders, GST exact.
draft_plan.md (v1.1)	Phase 5 section (lines 139-158). Emphasizes Gotenberg PDF, deterministic GST, e-signature, 3-day reminder. Cross-cutting concerns: compliance determinism, AI sandbox boundary.
IMPLEMENTATION_PLAN.md	Phase 5 section (lines ~1000+). Matches structure. Adds Pydantic schemas, router details, Celery task patterns. Confirms no WeasyPrint (Gotenberg only).
Alignment Verification ✅
Requirement	phase-5-sales-avs.md	draft_plan.md	IMPLEMENTATION_PLAN.md	Status
PDF Generation	Gotenberg	Gotenberg	Gotenberg	✅ Aligned
GST Calculation	price * 9 / 109	price * 9 / 109	price * 9 / 109, ROUND_HALF_UP	✅ Aligned
Thomson GST	0%	0%	0%	✅ Aligned
AVS Reminder	72h Celery Beat	3-day task	72h reminder	✅ Aligned
E-Signature	Coordinates + IP	Legally captured	Coordinates + timestamp	✅ Aligned
No AI in compliance	Explicit	Compliance determinism	Zero AI imports	✅ Aligned
Dependencies Status
Dependency	Phase	Status	Notes
Auth (HttpOnly cookies)	1	✅ Complete	BFF proxy ready
Dog/Entity models	2	✅ Complete	FK references available
Breeding records	4	✅ Complete	Litter/Puppy models ready
Gotenberg	0	✅ Ready	Sidecar in docker-compose
Celery workers	0	✅ Ready	@shared_task pattern
---
📋 PHASE_5_TODO.md Created
Location: /home/project/wellfond-bms/PHASE_5_TODO.md
8 Execution Steps (10–12 days)
Step	Focus	Tasks	Est. Time
1	Backend Models & Schemas	5 models + schemas + migrations	Days 1–2
2	Backend Services	agreement.py, pdf.py, avs.py	Days 3–5
3	Backend Routers	agreements.py, avs.py, API registration	Days 5–6
4	Celery Tasks	PDF gen, AVS reminders, DLQ	Days 6–7
5	Admin & Tests	18 tests (12 + 6), Django admin	Days 7–8
6	Frontend Components	Wizard, preview, signature pad	Days 8–10
7	Frontend Pages	Sales list, wizard page	Days 10–11
8	Hooks & Integration	TanStack Query, API wiring	Days 11–12
Key Success Criteria
- ✅ GST exact: 109→9.00, 218→18.00, 50→4.13, Thomson→0.00
- ✅ PDF via Gotenberg with SHA-256 hash
- ✅ AVS reminder at 72h with escalation
- ✅ HDB warning for large breeds
- ✅ PDPA opt-in enforced
- ✅ 18/18 tests passing

---

