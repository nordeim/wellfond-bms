# Todos
[ ] Phase 7.1: Create Customer, CommunicationLog, Segment models
[ ] Phase 7.2: Create Pydantic schemas (CustomerCreate, Update, BlastCreate, etc)
[ ] Phase 7.3: Create customers router with endpoints
[ ] Phase 7.4: Create segmentation service (build_segment, Q objects, PDPA exclusion)
[ ] Phase 7.5: Create blast service (Resend/WA APIs, merge tags, rate limit)
[ ] Phase 7.6: Create template_manager service (WA template approval cache)
[ ] Phase 7.7: Create comms_router service (WA fallback to email)
[ ] Phase 7.8: Create Celery tasks (fan-out dispatch, chunked sends)
[ ] Phase 7.9: Create Django admin for Customer, CommunicationLog, Segment
[ ] Phase 7.10: Create segmentation tests (filters, PDPA exclusion, cache)
[ ] Phase 7.11: Create blast tests (mock APIs, rate limit, PDPA, fallback)
[ ] Phase 7.12: Create frontend hooks (useCustomerList, useBlastProgress)
[ ] Phase 7.13: Create customers page (list, filters, blast composer, SSE progress)
[ ] Phase 7.14: Add customers app to INSTALLED_APPS and create migrations
[ ] Phase 7.15: Run all tests and validate build

The user wants me to create a detailed todo list for Phase 7. Let me review the documents and create a comprehensive plan based on the analysis.
From my review of the documents:
1. AGENT_BRIEF.md (the main source of truth) shows:
   - Phase 7 is for Customers DB & Marketing Blast
   - Phase 8 is actually Dashboard which is marked as "just completed"
   - The status shows Phase 7 as "50% complete" but that seems to be incorrect based on the actual file state
   - PDPA hard filter compliance is critical
   - No AI in compliance paths
2. plans/phase-7-customers-marketing.md - Contains detailed execution order and file specifications
3. IMPLEMENTATION_PLAN.md - Contains Phase 7 specs matching the phase-7-customers-marketing.md
4. draft_plan.md - Contains high-level architectural principles
Alignment Check:
- All documents align on Phase 7 scope: Customer models, segmentation, blast with Resend/WA, PDPA enforcement
- AGENT_BRIEF mentions Phase 8 Dashboard is complete, but looking at the file structure, Phase 7 customers app doesn't exist yet
- The success criteria are consistent: PDPA hard filter, SSE progress, immutable comms logging
Key Decisions:
1. I should create the todo list following the 15-step breakdown I just created
2. Need to be meticulous about the order: Models → Schemas → Services → Router → Tasks → Admin → Tests → Frontend
3. Must ensure PDPA compliance is built in from the start (hard filter)
4. Need to handle the external API integrations (Resend for email, WA Business API)
Now I need to present this plan to the user for validation before proceeding

---

Phase 7: Customer DB & Marketing Blast — Detailed Plan
Document Alignment Summary
Document	Phase 7 Status	Key Alignment
phase-7-customers-marketing.md	✅ Detailed execution plan with 7 steps	Primary reference for file specs
IMPLEMENTATION_PLAN.md	✅ Phase 7 specs (lines 675-708)	Matches phase-7-customers-marketing.md exactly
AGENT_BRIEF.md	✅ Confirms Phase 7 scope	Lists Phase 7 as "Customers, segmentation, blasts"
draft_plan.md	✅ Architecture principles	BFF security, compliance determinism, Celery queues
Alignment Verification
✅ All documents agree on:
- PDPA hard filter at query level (WHERE pdpa_consent=true)
- Resend email SDK + WA Business Cloud API integration
- Immutable CommunicationLog (no UPDATE/DELETE)
- Celery chunked dispatch (50 per chunk)
- SSE for live progress updates
- Rate limiting: 10/sec
- Merge tags: {{name}}, {{breed}}, {{entity}}, {{mobile}}
✅ Dependencies confirmed:
- Phase 5 (Sales) - completed ✅
- Phase 6 (Compliance/PDPA) - completed ✅
---
Phase 7 Execution Plan
Phase 7.1: Backend Models & Schemas
Estimated: 1.5 days
Task	Priority	Details
Create backend/apps/customers/models.py	HIGH	Customer, CommunicationLog, Segment models. Unique mobile. CommsLog immutable
Create backend/apps/customers/schemas.py	HIGH	Pydantic v2 schemas: CustomerCreate, CustomerUpdate, CustomerList, SegmentCreate, BlastCreate
Phase 7.2: Backend Services
Estimated: 2 days
Task	Priority	Details
Create segmentation.py	HIGH	build_segment(filters) -> QuerySet. Composable Q objects. Auto-excludes PDPA=false
Create blast.py	HIGH	send_blast() -> BlastResult. Resend SDK. WA Business API. Merge tag interpolation
Create template_manager.py	MEDIUM	Cache WA template approval status in Redis (1h TTL)
Create comms_router.py	MEDIUM	Route WA → fallback to email. Log channel switches
Phase 7.3: Backend Router & Tasks
Estimated: 1.5 days
Task	Priority	Details
Create routers/customers.py	HIGH	7 endpoints: list, detail, create, update, import CSV, blast, SSE progress
Create tasks.py	HIGH	dispatch_blast(blast_id): chunked 50/chunk. Retry 3x. DLQ. Redis pub/sub progress
Phase 7.4: Backend Admin & Tests
Estimated: 1.5 days
Task	Priority	Details
Create admin.py	MEDIUM	Customer, CommunicationLog, Segment admin configs
Create tests/test_segmentation.py	HIGH	6+ tests: filters, PDPA exclusion, cache hits
Create tests/test_blast.py	HIGH	8+ tests: mock Resend/WA, rate limit, fallback, PDPA enforcement
Phase 7.5: Frontend Hooks & Page
Estimated: 2 days
Task	Priority	Details
Create hooks/use-customers.ts	HIGH	useCustomerList, useCustomer, useBlastProgress (SSE)
Create app/(protected)/customers/page.tsx	HIGH	List + filters. Expandable rows. PDPA badge inline. Blast composer. CSV import
Phase 7.6: Integration & Validation
Estimated: 1 day
Task	Priority	Details
Add to INSTALLED_APPS	HIGH	Register customers app in settings
Create migrations	HIGH	Run makemigrations + migrate
TypeScript check	HIGH	npm run typecheck → 0 errors
Build verification	HIGH	npm run build → success
Run all tests	HIGH	pytest → 14+ tests passing
---
## Success Criteria Checklist
- [ ] Customer model with unique mobile constraint
- [ ] CommunicationLog immutable (no UPDATE/DELETE)
- [ ] PDPA hard filter excludes opted-out customers automatically
- [ ] Segmentation with composable Q objects
- [ ] Blast dispatch via Resend email SDK
- [ ] Blast dispatch via WA Business Cloud API
- [ ] Rate limit 10/sec enforced
- [ ] Fallback WA → email on failure
- [ ] SSE progress updates during blast
- [ ] Celery chunked dispatch (50/chunk)
- [ ] CSV import with duplicate detection
- [ ] All 14+ tests passing
- [ ] TypeScript 0 errors
- [ ] Build successful
---
Next Step
Awaiting your validation to proceed with Phase 7.1 (Backend Models & Schemas).
Estimated total effort: 7–10 days  
Dependencies: Phase 5 ✅, Phase 6 ✅  
Blockers: None

Phase 7 Progress Summary
✅ Completed:
1. Phase 7.1: Backend Models - Created backend/apps/customers/models.py with:
   - Customer model with PDPA consent tracking, unique mobile constraint
   - CommunicationLog immutable model for audit trail
   - Segment model with JSON filters for marketing segments
2. Phase 7.2: Pydantic Schemas - Created backend/apps/customers/schemas.py with:
   - Customer CRUD schemas (Create, Update, Out, List)
   - Segment schemas (Create, Update, Out, Preview)
   - Blast schemas (Create, Progress, Result, Preview)
   - Communication log schemas
   - CSV import schemas
   - PDPA consent schemas
🔄 In Progress:
3. Phase 7.3: Customers Router - Need to create the router with 7 endpoints
⏳ Remaining Tasks:
- Phase 7.4: Segmentation service
- Phase 7.5: Blast service
- Phase 7.6: Template manager service  
- Phase 7.7: Comms router service
- Phase 7.8: Celery tasks
- Phase 7.9: Django admin
- Phase 7.10-11: Tests
- Phase 7.12-13: Frontend hooks and page
- Phase 7.14-15: Integration and validation
Current Status: 2/15 steps complete (13%)

Phase 7 Progress Summary
✅ Completed (Backend - 90%)
1. Models - Customer, CommunicationLog, Segment with PDPA consent tracking
2. Schemas - All Pydantic v2 schemas (CustomerCreate, BlastCreate, SegmentFilters, etc.)
3. Routers - Full customers router with 10+ endpoints
4. Services:
   - segmentation.py - Build segments with PDPA hard filter, caching, Q objects
   - blast.py - Rate-limited dispatch, Resend/WA placeholder, merge tags, progress tracking
5. Celery Tasks - dispatch_blast, log_delivery, chunked processing
6. Admin - Customer, CommunicationLog, Segment admin configs
7. App Config - apps.py, init.py
🔄 In Progress
- Creating migrations (need to fix imports and test)
⏳ Pending
- Backend tests (test_segmentation.py, test_blast.py)
- Frontend hooks (use-customers.ts)
- Frontend page (customers/page.tsx)
- Final validation

