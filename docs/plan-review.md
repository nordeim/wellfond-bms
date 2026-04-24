Both files are loaded. Here's my meticulous review:

---

## 📋 Review: AGENTS.md

**Purpose:** System prompt / operational protocol for a coding agent (likely Qwen-based, given the chat link at the bottom).

**Strengths:**
- The 6-phase workflow (Analyze → Plan → Validate → Implement → Verify → Deliver) is well-structured and enforceable
- "Anti-Generic" design philosophy is a strong differentiator — explicitly rejects AI slop aesthetics
- Transparency pledge and Socratic gate are good guardrails against premature coding
- The library-first approach with bespoke-only-when-needed is pragmatic

**Concerns:**
1. **Over-engineered for a coding agent** — The Design Thinking Protocol, Multi-Dimensional Analysis, and Anti-Generic philosophy are excellent for a designer but add significant token overhead on every request. A simpler "apply design principles when building UI" directive would achieve the same with less context burn.
2. **Contradictory directives** — It says "never write code without completing ANALYZE and PLAN phases" but also says to be efficient and avoid filler. Real-world tasks often need quick iteration, not a 6-phase ceremony for every CSS fix.
3. **No mention of testing infrastructure** — References TDD and testing but doesn't specify which test frameworks or how to run them in this project's context.
4. **Missing project-specific context** — This is a generic agent prompt. It doesn't reference the Wellfond BMS stack (Django 6, Next.js 16, Celery, etc.) or domain (breeding management). The agent would need to rediscover this every session.

---

## 📋 Review: draft_plan.md

**Purpose:** Master Execution Plan (MEP) v1.0 → v1.1 with hardening critique integration for the Wellfond Breeding Management System.

**Strengths:**
- Extremely thorough — 10 phases (0-9) with explicit file-level specs, interfaces, and checklists
- The 8 hardening adjustments from the critique are all valid and well-evidenced:
  - `wal_level=replica` over `logical` (saves 10-20% WAL I/O) ✅
  - BFF proxy SSRF hardening with path allowlist ✅
  - RLS dropped in favor of Django queryset scoping (PgBouncer compatibility) ✅
  - UUIDv4 idempotency keys for offline sync ✅
  - Async closure table rebuild (avoids lock contention during CSV import) ✅
  - Gotenberg over WeasyPrint (pixel-perfect legal PDFs) ✅
  - WA template manager + email fallback ✅
  - Native Celery over `django.tasks` bridge ✅
- Cross-cutting validation matrix is excellent for QA
- Code snippets (BFF proxy, idempotency middleware, docker-compose) are production-ready starting points

**Concerns:**
1. **Version mismatch** — The file says v1.1 but the header still says v1.0 in places. The v1.1 updates are appended as bullet-point deltas to phases 2-9 rather than integrated inline, which makes the document harder to follow as a single source of truth.
2. **Django 6.0 doesn't exist yet** — As of April 2026, Django's latest LTS is 5.2. Django 6.0 is speculative. Same for Next.js 16.2 and PostgreSQL 17 — these should be verified against actual release timelines or labeled as target versions.
3. **Missing cost/infra sizing** — 10 containers (PG, PgBouncer, 3× Redis, Django, Celery worker, Celery beat, Gotenberg, Next.js, Flower) plus MinIO is a non-trivial deployment. No mention of resource limits, cloud provider, or estimated monthly cost.
4. **No migration strategy** — 483 dogs + 5 years of litters is mentioned as import data, but there's no plan for the legacy system migration (what's the current system? CSV exports? Direct DB access?).
5. **Singapore-specific compliance gaps** — NParks, GST (IRAS), AVS, PDPA are all referenced correctly for Singapore, but the actual NParks Excel template format isn't described. The `openpyxl` approach assumes template injection, but what if the template changes?
6. **Gotenberg Chromium memory** — Gotenberg with Chromium can consume 500MB+ under load. The docker-compose has no memory limits defined.
7. **The "CONFIDENTIAL" classification** — This is on a public GitHub repo. Either remove the classification or make the repo private.

---

## 🔑 Key Takeaways

The plan is **architecturally sound and impressively detailed** — clearly written by someone who understands Django, Next.js, and Singapore's pet breeding regulatory landscape. The hardening critique is legitimate and the v1.1 adjustments are well-reasoned.

The main risks are:
- **Speculative framework versions** (Django 6, Next.js 16, PG17)
- **Public repo with "CONFIDENTIAL" label**
- **No infrastructure cost/resource planning**
- **v1.1 is a patch, not a rewrite** — would benefit from a clean merged document

Want me to dig deeper into any specific phase, merge the v1.0/v1.1 into a clean single document, or start working on any of the implementation pieces?
