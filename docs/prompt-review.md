Please meticulously conduct a comprehensive code review and audit of the Wellfond BMS (Breeding Management System) codebase to identify issues, gaps, and bugs, then create a detailed assessment report. The project is a Singapore AVS-compliant dog breeding operations platform built with Django 6.0 + Next.js 16 + PostgreSQL 17.

## Instructions
- Meticulously review and analyze the planning documents to understand the WHAT, WHY, and HOW of the project
- Do a systematic code review and audit of the current codebase to identify any issues, gaps and bugs
- Create a comprehensive assessment analysis report of the current state of the codebase
- Highlight issues, gaps, bugs, and provide observations, conclusions, and recommendations
- Establish ground truth by validating implementation against the project documents

## Project Structure:
- Wellfond BMS is an enterprise-grade breeding management system for Singapore's AVS-licensed dog breeding operations
- Architecture: BFF (Backend-for-Frontend) pattern with Django 6.0.4 + Django Ninja + Next.js 16.2 + PostgreSQL 17 + Celery + SSE + PWA
- Multi-entity support: Holdings, Katong, Thomson with strict entity scoping
- Security: HttpOnly cookies via BFF proxy, zero JWT exposure, hardened path allowlisting

## Key Architectural Decisions from Planning Docs:
- wal_level=replica (not logical) to reduce WAL I/O overhead by ~15%
- RLS dropped for Django app user - using queryset scoping + audit logs instead (PgBouncer compatibility)
- Gotenberg sidecar for PDF generation (replaced WeasyPrint for legal-grade fidelity)
- Native Celery @shared_task - django.tasks bridge deferred (early-stage adapter risk)
- Idempotency: UUIDv4 keys + Redis store (24h TTL) for exactly-once delivery
- Closure table: Async Celery rebuild (no DB triggers) to prevent lock contention during bulk imports
- BFF Proxy: Server-only BACKEND_INTERNAL_URL, path allowlist regex, header sanitization (SSRF protection)

## PWA Features:
- Service Worker with cache-first/static assets, network-first/API
- IndexedDB offline queue with background sync
- 44px touch targets, high contrast (#0D2030 on #DDEEFF)
- Idempotency keys for conflict resolution (server wins)

## Compliance Requirements:
- NParks reporting: 5-document Excel generation (mating, movement, vet, bred, movement)
- GST: IRAS 9/109 calculation with ROUND_HALF_UP, Thomson=0%
- PDPA: Hard WHERE consent=true filter at queryset level, immutable audit trails
- AVS: 3-day reminder tasks for transfers

## TODO List:
- Read and analyzed all 8 planning documents:
  - @draft_plan.md (Master Execution Plan v1.1 with hardening)
  - @IMPLEMENTATION_PLAN.md (178 files across 9 phases)
  - @README.md (project status showing Phases 0-3 complete)
  - @plans/phase-0-infrastructure.md (Docker, PgBouncer, Redis×3, Gotenberg)
  - @plans/phase-1-auth-bff-rbac.md (HttpOnly cookies, RBAC, idempotency)
  - @plans/phase-2-domain-foundation.md (Dog models, CSV import, vaccines)
  - @plans/phase-3-ground-operations.md (7 logs, Draminski, SSE, PWA)
  - @plans/phase-4-breeding-genetics.md (COI, saturation, closure table)
  - @plans/phase-5-sales-avs.md 
  - @plans/phase-6-compliance-nparks.md
  - @plans/plans/phase-7-customers-marketing.md 
  - @plans/phase-8-dashboard-finance.md 
- Setting up systematic code review structure with todo items
- Preparing to audit actual codebase implementation against plans
- Remaining:
  - Explore actual backend code structure (models, services, routers)
  - Explore actual frontend code structure (components, hooks, pages)
  - Validate implemented features against Phase 0-3 completion claims
  - Check for gaps between planned architecture and actual implementation
  - Review test coverage and quality
  - Check infrastructure configuration (docker-compose, settings)
  - Identify security issues, performance bottlenecks, or compliance risks
  - Create comprehensive assessment report with findings and recommendations

## Relevant files / directories

### Planning Documents to read:
- /home/project/wellfond-bms/draft_plan.md - Master Execution Plan v1.1
- /home/project/wellfond-bms/IMPLEMENTATION_PLAN.md - Detailed implementation roadmap
- /home/project/wellfond-bms/README.md - Project status and overview
- /home/project/wellfond-bms/plans/phase-0-infrastructure.md - Infrastructure scaffold
- /home/project/wellfond-bms/plans/phase-1-auth-bff-rbac.md - Auth, BFF, RBAC
- /home/project/wellfond-bms/plans/phase-2-domain-foundation.md - Domain models
- /home/project/wellfond-bms/plans/phase-3-ground-operations.md - Ground ops, PWA
- /home/project/wellfond-bms/plans/phase-4-breeding-genetics.md - Genetics engine
- /home/project/wellfond-bms/plans/phase-5-sales-avs.md 
- /home/project/wellfond-bms/plans/phase-6-compliance-nparks.md
- /home/project/wellfond-bms/plans/phase-7-customers-marketing.md 
- /home/project/wellfond-bms/plans/phase-8-dashboard-finance.md 

### Codebase Structure (to be audited):
- /home/project/wellfond-bms/backend/ - Django backend (models, services, routers, config)
- /home/project/wellfond-bms/frontend/ - Next.js frontend (app, components, hooks, lib)
- /home/project/wellfond-bms/infra/ - Infrastructure configs
- /home/project/wellfond-bms/tests/ - Test suites
- /home/project/wellfond-bms/docker-compose.yml - Production compose
- /home/project/wellfond-bms/docker-compose.dev.yml - Development compose

### Key Areas to Audit:
- Backend apps: core, operations, breeding, sales, compliance, customers, finance, ai_sandbox
- Frontend: BFF proxy implementation, PWA service worker, offline queue
- Security: Cookie settings, CORS, CSP, BFF proxy hardening
- Compliance: Zero AI in compliance paths, GST calculation, PDPA filtering
- Performance: COI calculation <500ms, closure table rebuilds, SSE delivery
- Data integrity: Closure table triggers removed (should use Celery), idempotency keys
