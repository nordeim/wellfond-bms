# Wellfond BMS: Project Knowledge Base & Architecture Manifesto

**Version:** 1.0  
**Status:** Live / Reference  
**Classification:** Internal / Confidential  
**Context:** This document provides a deep, validated understanding of the Wellfond Breeding Management System (BMS) codebase, architecture, and engineering mandates. It is designed to initialize any coding agent or engineer with the same context required to safely and effectively contribute to the project.

---

## 1. Core Identity & Purpose (The "WHAT" and "WHY")

### 1.1 The WHAT
Wellfond BMS is an enterprise-grade platform specifically engineered for Singapore AVS-licensed dog breeding operations. It manages the complete lifecycle of breeding—from pedigree tracking and health logs to sales agreements and regulatory reporting.

### 1.2 The WHY
- **Compliance:** Singapore's AVS (Animal & Veterinary Service) has strict regulatory requirements (NParks submissions, AVS transfer tracking). The BMS automates these with 100% deterministic logic.
- **Security:** Managing multi-entity operations requires robust data isolation (Holdings, Katong, Thomson) and protection of PII/PDPA sensitive data.
- **Operational Efficiency:** Ground staff operating in kennels need a mobile-first, offline-capable interface (PWA) to log events like heat cycles and whelping in real-time.

---

## 2. Technical Stack (The "HOW")

### 2.1 Backend: Django 6.0 + Django Ninja
- **Django Ninja:** Chosen for its type-safe API endpoints, Pydantic v2 integration, and automatic OpenAPI schema generation.
- **Models:** Uses UUID primary keys, `created_at`/`updated_at` timestamps, and soft-delete patterns.
- **Celery 5.4:** Handles all background tasks (PDF generation, AVS reminders, Pedigree closure table rebuilds).
- **Redis 7.4:** triple-instance isolation (Sessions, Broker, Cache) to prevent noisy-neighbor contention.

### 2.2 Frontend: Next.js 16 + Tailwind CSS 4 + Radix UI
- **App Router:** Heavily utilizes Route Groups (`(auth)`, `(protected)`) and Server Components by default.
- **Tailwind CSS 4:** CSS-first configuration using `@theme` and `@import`.
- **Radix UI:** Base primitives for accessibility; customized via **shadcn/ui** components.
- **Tangerine Sky Theme:** A distinctive, non-generic design system focusing on high contrast and "Avant-Garde" minimalism.

### 2.3 Infrastructure
- **PostgreSQL 17:** Containerized, running in `wal_level=replica` for PITR (Point-In-Time Recovery) support.
- **Gotenberg 8:** A Chromium-based sidecar used for pixel-perfect PDF rendering of legal agreements.

---

## 3. Architecture Deep Dive

### 3.1 BFF (Backend-for-Frontend) Security Pattern
- **Logic:** The browser never talks to the Django backend directly. All requests pass through a Next.js proxy (`/api/proxy/[...path]`).
- **Authentication:** Uses HttpOnly, Secure, SameSite=Lax cookies (`sessionid`). Access tokens expire in 15m; refresh tokens in 7d.
- **Zero JWT:** No tokens are stored in `localStorage` or `sessionStorage`, eliminating XSS-based token theft.
- **Header Sanitization:** The proxy strips dangerous headers (Host, X-Forwarded-*) and enforces an allowlist of API paths.

### 3.2 Entity Scoping (Multi-Tenancy)
- **The Filter:** Every data query is scoped at the QuerySet level using `apps.core.permissions.scope_entity()`.
- **RBAC:** 
    - `MANAGEMENT`: Sees all data across all entities.
    - `ADMIN`, `SALES`, `GROUND`, `VET`: See only data belonging to their assigned `entity_id`.
- **Enforcement:** `EntityScopingMiddleware` attaches the filter to every request, ensuring no cross-entity data leakage.

### 3.3 Compliance Determinism
- **Mandate:** Regulatory logic (NParks reports, GST 9/109, AVS calculations) must be **deterministic**.
- **No AI:** AI imports (Anthropic/OpenAI) are strictly prohibited in the `apps/compliance/` module.
- **Immutability:** `AuditLog` and `NParksSubmission` (once locked) are immutable. No `UPDATE` or `DELETE` is permitted.

### 3.4 Idempotency & Offline Sync
- **X-Idempotency-Key:** All state-changing requests from the PWA require a UUIDv4 key.
- **Redis Store:** The backend caches responses for 24 hours. Duplicate requests (retried by the PWA on network flap) return the cached response instead of re-executing logic.

---

## 4. Key Implementation Standards

### 4.1 Backend (Python/Django)
- **Ninja Routers:** Each app must have its own router in `routers/{feature}.py`.
- **Pydantic v2:** Use `model_validate(obj, from_attributes=True)` for serialization.
- **Authentication Check:** Always read the session cookie directly from `request.COOKIES` as Ninja does not always preserve `request.user` across decorators.

### 4.2 Frontend (Next.js/React)
- **Server Components:** Default choice. Use `'use client'` only for interactive forms or hooks.
- **authFetch:** Use the unified wrapper in `lib/api.ts` which handles the BFF proxy and idempotency key injection.
- **Mobile-First:** The `ground` route group is designed specifically for 44px tap targets and high-contrast kennel environments.

### 4.3 Testing Strategy
- **Backend:** `pytest` for unit/integration tests. Target: ≥85% coverage.
- **Frontend:** `Vitest` for units, `Playwright` for E2E critical paths (Login, Wizard, NParks Gen).
- **TDD:** Write a failing test for every bug fix or feature.

---

## 5. Anti-Patterns to Avoid

- **NO JWT in Client:** Never store sensitive tokens in browser storage.
- **NO Surface Logic:** Do not use `request.user` with Ninja decorators; use the session cookie.
- **NO Hardcoded IDs:** Always use `entity_id` from the user session for scoping.
- **NO AI in Compliance:** Keep `apps/compliance` pure Python/SQL.
- **NO Generic UI:** Avoid default Tailwind styles; adhere to the Tangerine Sky design system.

---

## 6. Project Directory Hierarchy (Simplified)
```text
wellfond-bms/
├── backend/               # Django 6.0 Core
│   ├── api/               # Ninja API Registry
│   ├── apps/
│   │   ├── core/          # Auth, RBAC, Audit, Entity
│   │   ├── operations/    # Dogs, Logs, PWA Sync
│   │   ├── breeding/      # Genetics, COI, Litters
│   │   ├── compliance/    # NParks, GST (Deterministic)
│   │   └── ai_sandbox/    # Isolated AI Experiments
│   └── config/            # Settings (Base/Dev/Prod)
├── frontend/              # Next.js 16 Core
│   ├── app/               # App Router (BFF Proxy inside)
│   ├── components/        # Radix-based UI (Design System)
│   └── lib/               # authFetch, offline-queue
└── infra/                 # Docker/PostgreSQL/Redis
```

---

*This document is a living artifact. Update it as architectural shifts occur.*
