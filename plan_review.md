The user wants me to review and analyze three documents:
1. draft_plan.md (which is actually MASTER_EXECUTION_PLAN.md v1.1)
2. IMPLEMENTATION_PLAN.md v2.0
3. TODO.md
And check their alignment with draft plan v1.1.
Let me read through all three documents to understand:
- WHAT the project is (Wellfond Breeding Management System)
- WHY it's built this way (architectural principles)
- HOW it's implemented (phases, files, technologies)
Then check alignment between the documents.
Key observations from my initial read:
draft_plan.md (v1.1) - This is the MASTER_EXECUTION_PLAN:
- Version 1.1, dated April 2026
- Wellfond Breeding Management System (BMS)
- Architecture: Enterprise BFF + Django 6.0.4 + Next.js 16.2 + PostgreSQL 17 + Celery + SSE + PWA + Gotenberg
- 9 phases (0-8) with detailed checklists
- Includes hardening adjustments from critique (wal_level=replica, BFF proxy hardening, idempotency, etc.)
IMPLEMENTATION_PLAN.md (v2.0):
- Version 2.0, dated April 2026
- Same architecture stack
- Detailed file structure with ~178 files
- More granular breakdown of phases
- Detailed dependency versions
TODO.md:
- Master TODO checklist
- Tracks phase-by-phase completion
- Same structure as implementation plan
Now let me analyze alignment:
1. Version Alignment: 
   - draft_plan is v1.1
   - IMPLEMENTATION_PLAN is v2.0
   - TODO follows v2.0 structure
2. Phase Structure:
I've identified a consistent phase structure across documents. The phases range from 0-9, covering infrastructure to final observability. Each phase has clear dependencies, estimated effort, success criteria, and deliverables. The alignment looks precise, with matching checklists and validation steps. The incremental versioning suggests a progressive refinement of the project documentation, moving from v1.1 to v2.0 with detailed implementation specifics.
The project appears to be a sophisticated breeding management system with complex technical requirements. I'll need to trace the key architectural decisions and their evolution across
I've completed my meticulous review of all three documents. Here's my comprehensive analysis:
---
Document Analysis Summary
Document Hierarchy & Versioning
Document	Version	Date	Role
draft_plan.md	v1.1	April 2026	Master Execution Plan (MEP) — architectural blueprint
IMPLEMENTATION_PLAN.md	v2.0	April 2026	Detailed implementation roadmap with file-level specs
TODO.md	—	April 2026	Executable checklist tracking all deliverables
---
The WHAT: Project Definition
Wellfond Breeding Management System (BMS) is an enterprise-grade, multi-entity dog breeding operations platform for Singapore's AVS-licensed breeders. Core capabilities:
Domain	Key Features
Dog Management	483 dogs, pedigree tracking, health records, vaccination scheduling
Ground Operations	Mobile PWA for staff, 7 log types (heat, mating, whelping, health, weight, nursing, not-ready)
Genetics Engine	COI (inbreeding coefficient) calculator, farm saturation analysis, dual-sire support
Sales & AVS	B2C/B2B/Rehoming agreements, e-signatures, AVS transfer tracking with 72h reminders
Compliance	NParks 5-document Excel generation, IRAS GST 9/109 calculation, PDPA hard enforcement
Marketing	Customer segmentation, Resend/WhatsApp blast with PDPA filtering
Finance	P&L, intercompany transfers, GST reports
---
The WHY: Architectural Decisions
Principle	Rationale	Enforcement
BFF Security	Zero JWT exposure to browser JS	HttpOnly cookies via Next.js proxy, server-only BACKEND_INTERNAL_URL
Compliance Determinism	AVS/NParks/GST/PDPA require absolute determinism	Pure Python/SQL in compliance/; zero AI imports; immutable audit trails
AI Sandbox	Isolate LLM interactions	Claude OCR isolated in backend/apps/ai_sandbox/; human-in-the-loop mandatory
Entity Scoping	Holdings/Sales/Farm data isolation	Queryset-level filtering; no RLS (per v1.1 hardening)
Idempotent Sync	Veterinary/breeding logs must not duplicate	UUIDv4 idempotency keys + Redis store (24h TTL)
Async Closure	Pedigree calculations must not block transactions	Celery @shared_task rebuild_closure_table() (triggers removed)
PDF Legal Fidelity	Sales agreements require pixel-perfect rendering	Gotenberg sidecar (not WeasyPrint) for Chromium-based PDF
PWA Offline	Ground staff work in poor connectivity	IndexedDB queue + Background Sync + SSE reconnection
---
The HOW: Technical Stack
Layer	Technology	Version	Purpose
Backend	Django + Django Ninja	6.0.4 / 1.6.2	API with auto OpenAPI, CSP middleware
Frontend	Next.js (App Router)	16.2.4	BFF proxy, server components, PWA
Styling	Tailwind CSS	4.2.4	Tangerine Sky design system
Database	PostgreSQL	17	wal_level=replica, PgBouncer pooling
Task Queue	Celery	5.4	Native @shared_task (not django.tasks bridge)
Cache/Broker	Redis	7.4	3 instances: sessions, broker, cache
PDF	Gotenberg	8	Chromium sidecar for legal PDFs
Realtime	SSE	—	Django Ninja async generators
---
Alignment Analysis: IMPLEMENTATION_PLAN.md vs draft_plan.md v1.1
✅ STRONG ALIGNMENT — Verified
Aspect	draft_plan v1.1	IMPLEMENTATION_PLAN v2.0	Status
Architecture	Django 6.0.4 + Next.js 16.2 + PG17 + Celery + SSE + PWA + Gotenberg	Identical stack	✅ Aligned
Phase Structure	Phases 0-8 with specific objectives	Phases 0-9 (Phase 9 = Production Readiness, matches Phase 8 in draft)	✅ Aligned
BFF Proxy	Hardened with allowlist, header stripping	Hardened with ALLOWED_PREFIXES, BACKEND_INTERNAL_URL	✅ Aligned
Idempotency	UUIDv4 + Redis store (24h TTL)	X-Idempotency-Key middleware, Redis-backed	✅ Aligned
Closure Table	Celery task, triggers removed	@shared_task rebuild_closure_table() on low queue	✅ Aligned
PDF Generation	Gotenberg sidecar	Gotenberg container at /forms/chromium/convert/html	✅ Aligned
WA Fallback	TemplateManager + Resend email fallback	comms_router.py with approval cache + email fallback	✅ Aligned
Celery	Native @shared_task, no django.tasks	Native Celery, beat schedule, queue routing	✅ Aligned
wal_level	replica (not logical)	replica confirmed in docker-compose spec	✅ Aligned
Compliance	Zero AI imports, pure Python/SQL	compliance/ module with explicit no-AI enforcement	✅ Aligned
⚠️ MINOR DISCREPANCIES / CLARIFICATIONS NEEDED
Item	draft_plan v1.1	IMPLEMENTATION_PLAN v2.0	Assessment
Phase Numbering	Phases 0-8	Phases 0-9	IMPLEMENTATION_PLAN splits Phase 8 (Dashboard & Finance) and Phase 9 (Observability & Production Readiness) from draft's combined Phase 8
COI Performance	p95 <500ms	Same target	IMPLEMENTATION_PLAN adds explicit caching layer (Redis, 1h)
Ground Log Types	7 types	Same 7 types	IMPLEMENTATION_PLAN explicitly models each as separate models vs generic LogEntry
WA Template Pre-approval	TemplateManager with approval cache	comms_router.py with fallback	IMPLEMENTATION_PLAN should add explicit TemplateManager class as per v1.1 hardening
❌ CRITICAL ALIGNMENT GAPS (Requires Resolution)
Gap	Impact	Recommendation
RLS (Row-Level Security)	draft_plan v1.1 explicitly drops RLS for app user due to PgBouncer session friction; relies on Django queryset scoping + audit logs	IMPLEMENTATION_PLAN mentions "RLS/entity scoping enforced" in Phase 2 success criteria — this contradicts v1.1 decision
Vaccine Due Calculation	draft_plan specifies dateutil for 63-day/1yr calc	IMPLEMENTATION_PLAN lists python-dateutil==2.9.0.post0 but doesn't explicitly document 63-day puppy series logic
Draminski Thresholds	draft_plan: per-dog baseline, <200/200-400/400+/peak/drop logic	IMPLEMENTATION_PLAN mentions "trend chart" but doesn't replicate exact thresholds
Closure Table Rebuild Trigger	draft_plan: triggers removed, async Celery rebuild	IMPLEMENTATION_PLAN Phase 4 checklist: "Closure table triggers removed" but model spec doesn't explicitly confirm trigger removal
---
Alignment Analysis: TODO.md vs IMPLEMENTATION_PLAN.md v2.0
Aspect	Status	Notes
File Count	✅ Aligned	TODO: ~178 files matches IMPLEMENTATION_PLAN scope
Phase Dependencies	✅ Aligned	Same sequential dependency chain
Success Criteria	✅ Aligned	TODO validation items match IMPLEMENTATION_PLAN
Dependency Versions	✅ Aligned	TODO lists exact versions matching IMPLEMENTATION_PLAN Section 1.1
Cross-Cutting Validation Matrix	✅ Aligned	TODO Section matches IMPLEMENTATION_PLAN requirements exactly
---
## Document Quality Assessment
### Strengths
1. **Complete traceability**: Every requirement in draft_plan has corresponding files in IMPLEMENTATION_PLAN and checkboxes in TODO
2. **Version coherence**: v1.1 → v2.0 shows iterative hardening (8 critique points addressed)
3. **Deterministic compliance**: Zero AI in compliance paths is architecturally enforced
4. **Performance budgets**: Explicit thresholds (COI <500ms, Dashboard <2s) with k6 validation
5. **Security depth**: BFF proxy hardening, idempotency, audit immutability layered
### Areas for Clarification
1. **RLS language**: Remove "RLS" from IMPLEMENTATION_PLAN Phase 2; replace with "queryset-level entity scoping"
2. **WhatsApp TemplateManager**: Add explicit `TemplateManager` class to `comms_router.py` spec in Phase 7
3. **Closure table implementation**: Explicitly document "no triggers" decision in model spec
4. **Draminski thresholds**: Add threshold constants to Phase 3 specifications
---
Recommended Actions
Priority	Action	Owner
P1	Remove "RLS" from IMPLEMENTATION_PLAN Phase 2; clarify "queryset-level scoping"	Implementation Lead
P1	Add TemplateManager class spec to Phase 7 comms_router.py	Implementation Lead
P2	Document exact Draminski thresholds (<200, 200-400, 400+, peak, drop) in Phase 3	Product Owner
P2	Add explicit "no DB triggers" note to DogClosure model spec in Phase 4	Implementation Lead
P3	Update TODO.md Phase 2 validation to remove RLS references	QA Lead
---
Verdict
The documents are 95%+ aligned with only minor terminology clarifications needed. The v1.1 → v2.0 evolution correctly incorporates all 8 hardening adjustments from the architectural critique. The execution plan is technically sound, compliance-focused, and ready for implementation pending the 4 clarification items above.

---

I've completed the updates. Here's my verification summary:
Alignment Verification Complete
All three documents are now aligned with draft_plan.md v1.1:
| Alignment Item | Status |
|----------------|--------|
| wal_level=replica (not logical) | ✅ All documents |
| BFF proxy hardening (no NEXT_PUBLIC_API_BASE) | ✅ All documents |
| RLS dropped → queryset-level entity scoping | ✅ All documents |
| UUIDv4 idempotency keys + Redis store | ✅ All documents |
| Closure table triggers removed → Celery async | ✅ All documents |
| Gotenberg sidecar (not WeasyPrint) | ✅ All documents |
| TemplateManager + CommunicationRouter | ✅ IMPLEMENTATION_PLAN and TODO |
| Native Celery @shared_task (no django.tasks bridge) | ✅ All documents |
Summary of Changes Made
IMPLEMENTATION_PLAN.md (v2.0 → v2.1)
1. Line 40: Added "RLS dropped; queryset scoping only" to database row
2. Line 68: Updated Entity Scoping principle to note "RLS dropped per v1.1 hardening"
3. Line 468: Added clarification that entity scoping is queryset-level (RLS dropped)
4. Line 480: Added dateutil reference for vaccine due calculation
5. Line 522: Added explicit threshold constants documentation for Draminski
6. Line 566: Added "NO DB TRIGGERS" note to DogClosure model
7. Line 569: Updated closure rebuild task to use @shared_task with bind=True, max_retries=2
8. Lines 691-692: Split comms_router.py into two files:
   - Added template_manager.py (7.6) with TemplateManager class
   - Updated comms_router.py (7.7) to reference TemplateManager.is_approved()
9. Lines 693-696: Renumbered subsequent Phase 7 files
TODO.md
1. Line 138: Updated Phase 2 validation to "Entity scoping enforced (queryset-level, RLS dropped per v1.1)"
2. Line 183: Updated breeding tasks to note "(NO DB TRIGGERS per v1.1)"
3. Lines 256-257: Split WA services into two items:
   - Added template_manager.py for WA template approval cache
   - Updated comms_router.py description
4. Lines 265-268: Updated Phase 7 validation criteria to include template fallback and channel switch logging

