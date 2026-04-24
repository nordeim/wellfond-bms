# Wellfond BMS — Implementation Plan v2.0
**Architecture:** Django 6.0 + Django Ninja + Next.js 16 + PostgreSQL 17 + Celery + SSE + PWA  
**Date:** April 2026 | **Status:** Ready for Execution

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Codebase Structure](#2-codebase-structure)
3. [Phase 0: Infrastructure & Scaffold](#phase-0)
4. [Phase 1: Auth, BFF & RBAC](#phase-1)
5. [Phase 2: Domain Foundation & Data Migration](#phase-2)
6. [Phase 3: Ground Operations & Mobile PWA](#phase-3)
7. [Phase 4: Breeding & Genetics Engine](#phase-4)
8. [Phase 5: Sales Agreements & AVS](#phase-5)
9. [Phase 6: Compliance & NParks](#phase-6)
10. [Phase 7: Customer DB & Marketing](#phase-7)
11. [Phase 8: Dashboard & Finance](#phase-8)
12. [Phase 9: Observability & Production Readiness](#phase-9)
13. [Cross-Cutting Concerns](#13-cross-cutting-concerns)
14. [Dependency Graph](#14-dependency-graph)

---

## 1. Architecture Overview

### 1.1 Stack Decisions (Verified — all versions install cleanly as of April 2026)

| Layer | Choice | Installed Version | Rationale |
|-------|--------|-------------------|-----------|
| Backend | Django + Django Ninja | 6.0.4 / 1.6.2 | Native CSP middleware, async support, auto OpenAPI |
| Frontend | Next.js (App Router) + React | 16.2.4 / 19.2.5 | BFF proxy pattern, server components, PWA |
| Styling | Tailwind CSS + PostCSS | 4.2.4 / 8.5.10 | v4 utility-first, JIT, design tokens |
| UI Primitives | Radix UI (checkbox, dialog, dropdown, slot) | 1.3.3 / 1.1.15 / 2.1.16 / 1.2.4 | Accessible, unstyled, composable |
| Animation | Framer Motion | 12.38.0 | Page transitions, micro-interactions |
| State | Zustand + TanStack Query | 5.0.12 / 5.100.1 | Client state + server cache |
| Validation | Zod + Pydantic | 4.3.6 / 2.12.5 | Frontend + backend schema validation |
| Icons | Lucide React | 1.9.0 | Tree-shakeable icon library |
| Database | PostgreSQL 17 (containerized, private LAN) | 17 (Docker) | `wal_level=replica`, PgBouncer transaction pooling. RLS dropped; queryset scoping only |
| Task Queue | Celery (native `@shared_task`) | 5.4 (Docker) | Battle-tested; skip `django.tasks` bridge (early-stage) |
| Cache/Broker | Redis (3 instances: sessions, broker, cache) | 7.4 (Docker) / 6.4.0 (client) | Isolation prevents noisy-neighbor contention |
| DB Driver | psycopg2-binary | 2.9.10 | PostgreSQL adapter |
| HTTP Client | httpx (for Gotenberg) | (Docker) | Async HTTP for PDF sidecar |
| PDF | Gotenberg sidecar (Chromium-based) | 8 (Docker) | Pixel-perfect legal agreements, e-signature fidelity |
| Realtime | SSE via Django Ninja async generators | — | Simpler than WebSockets, HTTP/2 native, auto-reconnect |
| Offline | PWA Service Worker + IndexedDB + Background Sync | — | Queue ground logs in dead zones, sync on reconnect |
| Auth | HttpOnly cookies via BFF proxy | — | Zero JWT exposure to client JS |
| Type Safety | TypeScript | 6.0.3 | Strict mode, no `any` |
| Testing (BE) | pytest + pytest-django + pytest-asyncio | 9.0.3 / 4.12.0 / 1.3.0 | Unit, integration, async tests |
| Testing (FE) | Vitest + Testing Library + Playwright | 4.1.5 / 16.3.2 / 1.59.1 | Unit, component, E2E |
| Mocking | MSW (Mock Service Worker) | 2.13.5 | API mocking for frontend tests |
| Coverage | pytest-cov + Vitest coverage-v8 | 7.1.0 / 4.1.5 | ≥85% target |
| Factories | factory-boy + Faker | 3.3.3 / 40.5.1 | Test data generation |
| Linting | Black + isort + flake8 + mypy | 26.3.1 / 5.12.0 / 6.1.0 / 1.20.0 | Format, sort, lint, type-check |
| Django Types | django-stubs + django-stubs-ext | 6.0.2 / 6.0.3 | Type hints for Django |
| Dev Tools | IPython + django-extensions + django-debug-toolbar | 9.10.0 / 4.1 / 6.3.0 | REPL, management commands, SQL profiling |
| Docs | MkDocs + mkdocs-material | 1.6.1 / 9.6.19 | Project documentation site |
| Observability | OpenTelemetry → Prometheus/Grafana | (Docker) | Structured JSON logging, distributed tracing |

> **Verification:** `npm install` → 377 packages, 0 vulnerabilities. `pip install -r base.txt` → 24 packages installed. `pip install -r dev.txt` → 47 packages installed. All resolved successfully.

### 1.2 Key Architectural Principles

1. **BFF Security** — Next.js `/api/proxy/` forwards HttpOnly cookies. Server-only `BACKEND_INTERNAL_URL`. Path allowlist. Zero token leakage.
2. **Compliance Determinism** — NParks/GST/AVS/PDPA paths are pure Python/SQL. Zero AI imports. Immutable audit trails.
3. **AI Sandbox** — Claude OCR isolated in `backend/apps/ai_sandbox/`. Human-in-the-loop mandatory.
4. **Entity Scoping** — All queries filtered by `entity_id`. No cross-entity data leakage. Enforced at queryset level (RLS dropped per v1.1 hardening).
5. **Idempotent Sync** — UUIDv4 keys on all POST requests. Redis-backed idempotency store. Exactly-once delivery.
6. **Async Closure** — Pedigree closure table rebuilt by Celery task (no DB triggers). Incremental for single-dog, full for bulk import.

---

## 2. Codebase Structure

### 2.1 Repository Layout

```
wellfond-bms/
├── .github/workflows/
│   └── ci.yml                          # Lint, test, build, Trivy, SBOM
├── backend/
│   ├── Dockerfile.django               # Multi-stage Python 3.13-slim
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Django 6.0 defaults, CSP, logging
│   │   │   ├── development.py          # Debug toolbar, local DB
│   │   │   └── production.py           # PgBouncer, OTel, CSP strict
│   │   ├── urls.py                     # Root URL conf
│   │   ├── wsgi.py
│   │   ├── asgi.py                     # ASGI for async SSE
│   │   └── celery.py                   # Celery app config
│   ├── api.py                          # NinjaAPI instance, router registry
│   ├── apps/
│   │   ├── core/                       # Auth, users, permissions, audit
│   │   │   ├── models.py
│   │   │   ├── auth.py
│   │   │   ├── permissions.py
│   │   │   ├── middleware.py           # Idempotency, entity scoping
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   └── users.py
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   │   ├── test_auth.py
│   │   │   │   ├── test_permissions.py
│   │   │   │   └── factories.py
│   │   │   └── migrations/
│   │   ├── operations/                 # Dogs, health, ground logs, PWA sync
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dogs.py
│   │   │   │   ├── health.py
│   │   │   │   ├── logs.py            # 7 ground log types
│   │   │   │   └── stream.py          # SSE alert endpoint
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── importers.py       # CSV dog/litter import
│   │   │   │   ├── vaccine.py         # Due date calculation
│   │   │   │   ├── draminski.py       # DOD2 interpreter
│   │   │   │   └── alerts.py          # Nursing/heat/age flags
│   │   │   ├── tasks.py               # Celery: closure rebuild, alerts
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   ├── breeding/                   # Mating, litters, COI, saturation
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mating.py          # Mate checker endpoint
│   │   │   │   └── litters.py         # Litter CRUD
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── coi.py             # Wright's formula, closure traversal
│   │   │   │   └── saturation.py      # Farm saturation calculation
│   │   │   ├── tasks.py               # Celery: closure table rebuild
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   ├── sales/                      # Agreements, AVS, e-sign
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agreements.py
│   │   │   │   └── avs.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agreement.py       # Wizard state machine
│   │   │   │   ├── pdf.py             # Gotenberg PDF render
│   │   │   │   └── avs.py             # AVS link gen, state tracking
│   │   │   ├── tasks.py               # Celery: PDF gen, AVS reminder
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   ├── compliance/                 # NParks, GST, PDPA (ZERO AI)
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── nparks.py
│   │   │   │   └── gst.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── nparks.py          # 5-doc Excel gen via openpyxl
│   │   │   │   ├── gst.py             # IRAS 9/109, ROUND_HALF_UP
│   │   │   │   └── pdpa.py            # Hard queryset filter, consent log
│   │   │   ├── tasks.py               # Celery: monthly gen, reminders
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   ├── customers/                  # CRM, segments, marketing blast
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── customers.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── segmentation.py    # Dynamic Q-object filters
│   │   │   │   ├── blast.py           # Resend/WA dispatch
│   │   │   │   └── comms_router.py    # WA template + email fallback
│   │   │   ├── tasks.py               # Celery: fan-out, DLQ
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   ├── finance/                    # P&L, GST reports, intercompany
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── reports.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pnl.py
│   │   │   │   └── gst_report.py
│   │   │   ├── admin.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   └── ai_sandbox/                # Isolated AI (OCR, drafts)
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── routers/
│   │       ├── services/
│   │       ├── tests/
│   │       └── migrations/
│   ├── requirements/
│   │   ├── base.txt
│   │   └── dev.txt
│   ├── manage.py
│   └── .env.example
├── frontend/
│   ├── Dockerfile.nextjs               # Node 22-alpine, pnpm, standalone
│   ├── app/
│   │   ├── layout.tsx                  # Root: Tailwind, fonts, CSP nonce
│   │   ├── page.tsx                    # Landing → redirect to /dashboard
│   │   ├── globals.css
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── layout.tsx             # Minimal layout for auth pages
│   │   ├── (protected)/
│   │   │   ├── layout.tsx             # Sidebar + topbar + role guard
│   │   │   ├── dashboard/page.tsx     # Role-aware command centre
│   │   │   ├── dogs/
│   │   │   │   ├── page.tsx           # Master list
│   │   │   │   └── [id]/page.tsx      # Dog profile (7 tabs)
│   │   │   ├── breeding/
│   │   │   │   ├── page.tsx           # Breeding records list
│   │   │   │   └── mate-checker/page.tsx
│   │   │   ├── sales/
│   │   │   │   ├── page.tsx           # Agreements list
│   │   │   │   └── wizard/page.tsx    # 5-step wizard
│   │   │   ├── compliance/
│   │   │   │   ├── page.tsx           # NParks gen + GST
│   │   │   │   └── settings/page.tsx  # T&C templates (admin)
│   │   │   ├── customers/
│   │   │   │   └── page.tsx           # Customer DB + blast
│   │   │   └── finance/
│   │   │       └── page.tsx           # P&L, GST export
│   │   ├── ground/                     # Mobile-first (no sidebar)
│   │   │   ├── layout.tsx             # Bottom nav, high-contrast
│   │   │   ├── page.tsx               # Chip search + quick stats
│   │   │   └── log/[type]/page.tsx    # 7 log type forms
│   │   └── api/
│   │       └── proxy/[...path]/route.ts  # BFF proxy
│   ├── components/
│   │   ├── ui/                         # Design system primitives
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   ├── table.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── select.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── skeleton.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── signature-pad.tsx
│   │   │   └── chart.tsx
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── topbar.tsx
│   │   │   ├── bottom-nav.tsx
│   │   │   └── role-bar.tsx
│   │   ├── dogs/
│   │   │   ├── dog-table.tsx
│   │   │   ├── dog-card.tsx
│   │   │   ├── dog-filters.tsx
│   │   │   ├── alert-cards.tsx
│   │   │   └── chip-search.tsx
│   │   ├── breeding/
│   │   │   ├── coi-gauge.tsx
│   │   │   ├── saturation-bar.tsx
│   │   │   └── mate-check-form.tsx
│   │   ├── sales/
│   │   │   ├── wizard-steps.tsx
│   │   │   └── agreement-preview.tsx
│   │   ├── ground/
│   │   │   ├── numpad.tsx
│   │   │   ├── draminski-chart.tsx
│   │   │   ├── log-form.tsx
│   │   │   └── camera-scan.tsx
│   │   └── dashboard/
│   │       ├── nparks-countdown.tsx
│   │       ├── alert-feed.tsx
│   │       └── revenue-chart.tsx
│   ├── hooks/
│   │   ├── use-dogs.ts
│   │   ├── use-auth.ts
│   │   ├── use-sse.ts
│   │   ├── use-offline-queue.ts
│   │   └── use-idempotency.ts
│   ├── lib/
│   │   ├── api.ts                      # authFetch wrapper
│   │   ├── auth.ts                     # Session helpers
│   │   ├── utils.ts                    # cn(), formatDate(), etc.
│   │   ├── constants.ts                # Roles, entities, thresholds
│   │   ├── types.ts                    # Shared TypeScript types
│   │   ├── offline-queue.ts            # IndexedDB wrapper
│   │   └── pwa/
│   │       ├── sw.ts                   # Service worker
│   │       └── register.ts             # SW registration
│   ├── middleware.ts                    # Route protection, role redirect
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   ├── package.json
│   └── public/
│       ├── manifest.json
│       ├── icons/
│       └── favicon.ico
├── docker-compose.yml
├── docker-compose.dev.yml              # Dev overrides (hot reload, debug)
├── nginx/                              # Optional: reverse proxy for prod
│   └── nginx.conf
├── docs/
│   ├── RUNBOOK.md
│   ├── SECURITY.md
│   ├── DEPLOYMENT.md
│   └── API.md
├── scripts/
│   ├── seed.sh                         # Load fixture data
│   ├── import-dogs.sh                  # CSV import runner
│   └── backup.sh                       # WAL-G backup wrapper
├── AGENTS.md
├── IMPLEMENTATION_PLAN.md              # This file
├── requirements.md                     # PRD
├── .gitignore
├── .env.example
└── README.md
```

---

<a id="phase-0"></a>
## Phase 0: Infrastructure & Foundation Scaffold

**Objective:** Containerized infrastructure, base Django/Next.js projects, CI/CD pipeline, dependency pinning.  
**Dependencies:** None  
**Estimated Effort:** 3–5 days  
**Success Criteria:** `docker compose up` boots all services healthy. CI green on push. Base routes return 200.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 0.1 | `docker-compose.yml` | Production compose: PG17, PgBouncer, Redis×3, Django, Celery worker + beat, Next.js, Gotenberg, Flower (11 services) | Services on `backend_net`/`frontend_net`. Healthchecks on all. `wal_level=replica`. Resource limits. Named volumes for NVMe. | ☐ All 11 containers boot healthy ☐ Networks isolated ☐ Volumes persist data |
| 0.2 | `docker-compose.dev.yml` | Dev overrides: hot reload, debug ports | Mounts `./backend` and `./frontend` for live reload. Exposes 5432 (PG), 6379 (Redis), 8000 (Django), 3000 (Next.js). | ☐ `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` works |
| 0.3 | `backend/Dockerfile.django` | Multi-stage: builder (uv/pip-tools) → runtime (slim) | Non-root user. Trivy scan stage. SBOM generation. `psycopg[c]`, `celery`, `uvicorn` pinned. | ☐ Image <200MB ☐ No root process ☐ Trivy passes |
| 0.4 | `frontend/Dockerfile.nextjs` | Multi-stage: deps → build → standalone | Node 22-alpine. pnpm. `output: standalone`. Non-root. PWA assets precached. Env: `BACKEND_INTERNAL_URL` (server-only), `NEXT_PUBLIC_SENTRY_DSN` (optional). No `NEXT_PUBLIC_API_BASE`. | ☐ Image <150MB ☐ Standalone output works ☐ SW precache loads |
| 0.5 | `backend/config/settings/base.py` | Django 6.0 core settings | `INSTALLED_APPS` (all 7 domain apps). CSP middleware. `CONN_MAX_AGE=0`. Split Redis configs. Celery config. Logging (JSON). Timezone `Asia/Singapore`. | ☐ `python manage.py check` passes ☐ All apps registered |
| 0.6 | `backend/config/settings/development.py` | Dev settings | `DEBUG=True`. Debug toolbar. Local DB. Relaxed CSP. | ☐ Debug toolbar loads |
| 0.7 | `backend/config/settings/production.py` | Prod settings | `DEBUG=False`. Strict CSP. PgBouncer host. OTel exporters. HTTPS-only cookies. | ☐ CSP headers present in response |
| 0.8 | `backend/config/celery.py` | Celery app initialization | `app = Celery('wellfond')`. Auto-discovers tasks from all apps. Beat schedule for AVS reminders. Queue routing: compliance→high, marketing→default, breeding→low. | ☐ `celery -A config inspect registered` lists tasks |
| 0.9 | `backend/config/urls.py` | Root URL configuration | Includes `api.urls` at `/api/v1/`. Admin at `/admin/`. Health check at `/health/`. | ☐ `/health/` returns 200 |
| 0.10 | `backend/config/asgi.py` | ASGI config for async | Uvicorn-compatible. Supports SSE streaming. | ☐ Async views work |
| 0.11 | `backend/api.py` | NinjaAPI instance | `NinjaAPI(title="Wellfond BMS", version="1.0.0", csrf=True)`. Global exception handlers (500/422/401). Router registry. OpenAPI at `/api/v1/openapi.json`. | ☐ Schema exports without runtime ☐ Custom error responses |
| 0.12 | `backend/manage.py` | Django management script | Standard. `DJANGO_SETTINGS_MODULE=config.settings.development`. | ☐ `python manage.py runserver` works |
| 0.13 | `backend/requirements/base.txt` | Production dependencies | `Django==6.0.4`, `django-ninja==1.6.2`, `pydantic==2.12.5`, `psycopg2-binary==2.9.10`, `redis==6.4.0`, `hiredis==3.3.0`, `django-cors-headers==4.9.0`, `djangorestframework-simplejwt==5.5.1`, `PyJWT==2.12.1`, `stripe==14.4.1`, `python-decouple==3.8`, `pytz==2025.2`, `python-dateutil==2.9.0.post0`, `Pillow==12.2.0`, `asgiref==3.11.0`, `channels==4.3.2`, `channels-redis==4.3.0`, `django-ratelimit==4.1.0` + `celery`, `django-celery-beat`, `openpyxl`, `httpx`, `opentelemetry-*`, `python-json-logger` (to add) | ☐ `pip install -r base.txt` succeeds ☐ No version conflicts |
| 0.14 | `backend/requirements/dev.txt` | Dev dependencies | `pytest==9.0.3`, `pytest-django==4.12.0`, `pytest-asyncio==1.3.0`, `pytest-cov==7.1.0`, `pytest-xdist==3.8.0`, `factory-boy==3.3.3`, `faker==40.5.1`, `black==26.3.1`, `isort==5.12.0`, `flake8==6.1.0`, `mypy==1.20.0`, `django-stubs==6.0.2`, `ipython==9.10.0`, `django-extensions==4.1`, `django-debug-toolbar==6.3.0`, `mkdocs==1.6.1`, `mkdocs-material==9.6.19` | ☐ `pytest` runs and discovers tests |
| 0.15 | `frontend/next.config.ts` | Next.js 16.2.4 configuration | `output: 'standalone'`. Rewrites for BFF proxy. Image domains. PWA headers. | ☐ Build succeeds |
| 0.16 | `frontend/tailwind.config.ts` | Tailwind v4.2.4 config | Tangerine Sky palette: `#DDEEFF`, `#0D2030`, `#F97316`, `#0891B2`, `#4EAD72`, `#D4920A`, `#D94040`. Font: Figtree. Breakpoints. | ☐ Custom colors render |
| 0.17 | `frontend/app/layout.tsx` | Root layout | Tailwind import. Figtree font. CSP nonce. Theme color. Manifest link. Strict mode. | ☐ Page renders with correct font |
| 0.18 | `frontend/app/globals.css` | Global styles | Tailwind v4 `@import`. CSS custom properties for theme. | ☐ Styles apply |
| 0.19 | `frontend/public/manifest.json` | PWA manifest | Name, icons, theme_color, display: standalone, start_url. | ☐ Lighthouse PWA passes |
| 0.20 | `.github/workflows/ci.yml` | CI pipeline | Matrix: backend (lint, typecheck, test), frontend (lint, typecheck, test, build), infra (docker build, Trivy). Coverage ≥85%. Schema diff check. No `latest` tags. | ☐ Pipeline green on push |
| 0.21 | `.env.example` | Environment template | **Replace "CHA YUAN" with Wellfond-specific vars.** DB, Redis×3, Gotenberg, Django secret, CSP, OTel. | ☐ Matches docker-compose env vars |
| 0.22 | `.gitignore` | Git ignore rules | `.env`, `node_modules/`, `__pycache__/`, `.next/`, `venv/`, `*.pyc`, `.pytest_cache/`, `coverage/`, `staticfiles/`, `media/`. | ☐ Sensitive files excluded |
| 0.23 | `scripts/seed.sh` | Fixture data loader | Runs migrations, creates superuser, loads entity fixtures. | ☐ Fresh DB has 3 entities + admin user |
| 0.24 | `README.md` | Project readme | Quick start, architecture overview, dev setup, deployment. | ☐ New dev can boot project in <10 min |

### Phase 0 Validation

- [ ] `docker compose up -d` → all 11 containers healthy within 60s
- [ ] `curl http://localhost:8000/health/` → 200 OK
- [ ] `curl http://localhost:3000` → Next.js renders
- [ ] `docker exec wellfond-nextjs curl http://postgres:5432` → connection refused (network isolation)
- [ ] PgBouncer routes Django connections successfully
- [ ] Redis instances isolated: sessions ≠ broker ≠ cache
- [ ] Gotenberg responds: `curl http://localhost:3000/health` → 200 (Gotenberg's own healthcheck)
- [ ] OpenAPI schema exports at `/api/v1/openapi.json` without server runtime
- [ ] CI pipeline green on push to `main`
- [ ] `pip install -r backend/requirements/base.txt` → 24 packages, no conflicts
- [ ] `pip install -r backend/requirements/dev.txt` → 47 packages, no conflicts
- [ ] `cd frontend && npm install` → 377 packages, 0 vulnerabilities
- [ ] `cd frontend && npm run build` → standalone output in `.next/standalone/`

---

<a id="phase-1"></a>
## Phase 1: Core Auth, BFF Proxy & RBAC

**Objective:** Secure authentication, BFF proxy, role-based access, idempotency middleware, shared UI design system.  
**Dependencies:** Phase 0  
**Estimated Effort:** 5–7 days  
**Success Criteria:** HttpOnly cookie flow verified. Role matrix enforced. Zero token leakage in DevTools. Design system components render.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 1.1 | `backend/apps/core/models.py` | User, Role, Entity, AuditLog models | `User(AbstractUser)` with `role`, `entity`, `pdpa_consent` fields. `Role` enum: MANAGEMENT, ADMIN, SALES, GROUND, VET. `AuditLog(uuid, actor, action, resource_type, resource_id, payload, ip, ts)` — immutable (no UPDATE/DELETE). Indexes on `actor_id`, `created_at`, `action`. | ☐ Migrations run ☐ AuditLog blocks UPDATE/DELETE via DB trigger or model override |
| 1.2 | `backend/apps/core/auth.py` | Authentication logic | `login(request, user)` → sets HttpOnly session cookie. `refresh(request)` → rotates CSRF. `logout(request)` → clears cookie. Session stored in Redis. 15m access / 7d refresh. | ☐ Cookie visible in DevTools with HttpOnly✓ Secure✓ SameSite=Lax |
| 1.3 | `backend/apps/core/permissions.py` | Role decorators & entity scoping | `@require_role("ADMIN")` — fails closed on missing role. `@scope_entity(queryset, user)` — filters by `entity_id`. `enforce_pdpa(queryset)` — hard `WHERE pdpa_consent=true`. | ☐ Ground staff blocked from /sales/ ☐ Cross-entity query returns empty |
| 1.4 | `backend/apps/core/middleware.py` | Idempotency + entity scoping middleware | `IdempotencyMiddleware`: reads `X-Idempotency-Key` header, Redis store (24h TTL), returns cached response on duplicate, blocks missing keys on POST to `/operations/logs/`. `EntityScopingMiddleware`: attaches `request.entity_filter` based on user role. | ☐ Duplicate POST returns 200 (cached) ☐ Missing key returns 400 on log endpoints |
| 1.5 | `backend/apps/core/schemas.py` | Pydantic schemas for auth/user | `LoginRequest(username, password)`, `UserResponse(id, username, role, entity)`, `AuditLogEntry(...)`. | ☐ OpenAPI schema shows auth endpoints |
| 1.6 | `backend/apps/core/routers/auth.py` | Auth endpoints | `POST /auth/login` → sets cookie, returns user. `POST /auth/logout` → clears cookie. `POST /auth/refresh` → rotates CSRF. `GET /auth/me` → current user. | ☐ Login sets cookie ☐ Logout clears it ☐ /auth/me returns user or 401 |
| 1.7 | `backend/apps/core/routers/users.py` | User management (admin) | `GET /users/` (admin only). `PATCH /users/{id}` (role change). `POST /users/` (create). | ☐ Non-admin gets 403 |
| 1.8 | `backend/apps/core/admin.py` | Django admin registration | User, AuditLog in admin. AuditLog read-only. | ☐ Admin panel accessible |
| 1.9 | `backend/apps/core/tests/test_auth.py` | Auth tests | Login/logout/refresh. Cookie properties. Role enforcement. CSRF rotation. | ☐ All pass |
| 1.10 | `backend/apps/core/tests/test_permissions.py` | Permission tests | Each role blocked from unauthorized endpoints. Entity scoping. PDPA filter. | ☐ All pass |
| 1.11 | `backend/apps/core/tests/factories.py` | Test factories | `UserFactory`, `EntityFactory`, `AuditLogFactory`. | ☐ Factories produce valid instances |
| 1.12 | `frontend/app/api/proxy/[...path]/route.ts` | BFF proxy (hardened) | `BACKEND_INTERNAL_URL` (server-only env). Path allowlist regex: `/api/v1/(dogs|breeding|sales|compliance|customers|finance|operations|auth|users)/`. Strips `host`, `x-forwarded-for`, `x-forwarded-host`. Streams response. 403 on non-allowlisted paths. 503 on upstream failure. | ☐ Proxy to /admin/ returns 403 ☐ Cookies forwarded ☐ No NEXT_PUBLIC_ vars used |
| 1.13 | `frontend/lib/api.ts` | Unified fetch wrapper | `authFetch<T>(path, opts)` — server: direct Django URL; client: `/api/proxy/`. Auto-refresh on 401. Attaches UUIDv4 `X-Idempotency-Key` on POST. Typed response generics. Error handling with toast. | ☐ 401 triggers refresh then retry ☐ POST includes idempotency key |
| 1.14 | `frontend/lib/auth.ts` | Session helpers | `getSession()`, `isAuthenticated()`, `getRole()`, `isServer()`. | ☐ Works in both server and client components |
| 1.15 | `frontend/lib/constants.ts` | App constants | `ROLES`, `ENTITIES`, `LOG_TYPES`, `COI_THRESHOLDS`, `SATURATION_THRESHOLDS`, `DESIGN_TOKENS`. | ☐ Constants match backend enums |
| 1.16 | `frontend/lib/types.ts` | TypeScript type definitions | `User`, `Dog`, `Entity`, `Role`, `BreedingRecord`, `Litter`, `SalesAgreement`, `Customer`, `AuditLog`, etc. | ☐ Types match Pydantic schemas |
| 1.17 | `frontend/lib/utils.ts` | Utility functions | `cn()` (clsx + twMerge), `formatDate()`, `formatChip()`, `calculateAge()`, `gstExtract()`. | ☐ Utilities work correctly |
| 1.18 | `frontend/middleware.ts` | Route protection | Reads session cookie. Redirects unauthenticated to `/login`. Role-aware route map (Ground→/ground, Sales→/dashboard, etc.). Edge-compatible. | ☐ Unauthenticated → /login ☐ Ground staff → /ground |
| 1.19 | `frontend/app/(auth)/login/page.tsx` | Login page | Username/password form. Submit to `/api/proxy/auth/login`. Redirect by role. Error handling. Tangerine Sky theme. | ☐ Login works ☐ Role redirect works |
| 1.20 | `frontend/app/(auth)/layout.tsx` | Auth layout | Minimal: centered card, no sidebar. | ☐ Renders cleanly |
| 1.21 | `frontend/app/(protected)/layout.tsx` | Protected layout | Sidebar (desktop) + bottom nav (mobile). Role bar. User menu. Logout. | ☐ Sidebar renders ☐ Mobile bottom nav shows |
| 1.22 | `frontend/components/ui/button.tsx` | Button component | Variants: primary, secondary, ghost, destructive. Sizes: sm, md, lg. Loading state with spinner. Disabled during async. | ☐ All variants render |
| 1.23 | `frontend/components/ui/input.tsx` | Input component | Label, error message, helper text. Controlled. Forward ref. | ☐ Validation states display |
| 1.24 | `frontend/components/ui/card.tsx` | Card component | Header, content, footer slots. Hover state. | ☐ Composable |
| 1.25 | `frontend/components/ui/badge.tsx` | Badge component | Variants: default, success, warning, error, info. | ☐ Color-coded correctly |
| 1.26 | `frontend/components/ui/dialog.tsx` | Dialog/modal component | Radix Dialog. Overlay, close button, title, description. | ☐ Opens/closes, focus trap |
| 1.27 | `frontend/components/ui/table.tsx` | Table component | Header, body, row, cell. Sortable columns. Responsive (card reflow on mobile). | ☐ Renders data correctly |
| 1.28 | `frontend/components/ui/tabs.tsx` | Tabs component | Radix Tabs. Controlled/uncontrolled. | ☐ Tab switching works |
| 1.29 | `frontend/components/ui/toast.tsx` | Toast notifications | Via Sonner. Variants: success, error, info. Auto-dismiss. | ☐ Toasts appear and dismiss |
| 1.30 | `frontend/components/ui/skeleton.tsx` | Loading skeleton | Pulse animation. Configurable shape (line, circle, rect). | ☐ Renders during loading |
| 1.31 | `frontend/components/ui/select.tsx` | Select component | Radix Select. Searchable option. | ☐ Selection works |
| 1.32 | `frontend/components/ui/progress.tsx` | Progress bar | Determinate/indeterminate. Animated. | ☐ Percentage displays |
| 1.33 | `frontend/components/layout/sidebar.tsx` | Desktop sidebar | Nav items by role. Active state (orange). Collapsible. Entity selector. | ☐ Role-aware nav items |
| 1.34 | `frontend/components/layout/topbar.tsx` | Top bar | Breadcrumb, user avatar, notifications bell, role badge. | ☐ Displays user info |
| 1.35 | `frontend/components/layout/bottom-nav.tsx` | Mobile bottom nav | 5 tabs: Home, Dogs, Sales, Reports, More. Active state. 44px tap targets. | ☐ Navigates correctly |
| 1.36 | `frontend/components/layout/role-bar.tsx` | Role indicator bar | Orange-bordered strip showing current role and entity. | ☐ Displays correctly |

### Phase 1 Validation

- [ ] Login sets HttpOnly cookie; `window.localStorage` and `window.sessionStorage` are empty
- [ ] BFF proxy rejects non-allowlisted paths (403)
- [ ] `auth-fetch` attaches idempotency key to POST requests
- [ ] Role matrix: Ground staff can't access `/breeding/`, Sales can't access `/finance/`
- [ ] Design system components render with Tangerine Sky theme
- [ ] All unit tests pass (`pytest` + `vitest`)
- [ ] Mobile bottom nav renders on <768px viewport

---

<a id="phase-2"></a>
## Phase 2: Domain Foundation & Data Migration

**Objective:** Core domain models, Pydantic contracts, CSV importers, dog list & profile UI.  
**Dependencies:** Phase 1  
**Estimated Effort:** 7–10 days  
**Success Criteria:** 483 dogs import with 0 FK violations. Master list renders with filters. Dog profile shows all 7 tabs. Queryset-level entity scoping enforced (RLS dropped per v1.1 hardening).

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 2.1 | `backend/apps/operations/models.py` | Dog, Entity, HealthRecord, Vaccination, DogPhoto models | `Dog(microchip, name, breed, dob, gender, colour, entity, status, dam, sire, unit, dna_status, notes)`. Status enum: ACTIVE, RETIRED, REHOMED, DECEASED. Unique microchip. FK constraints + `on_delete=PROTECT`. Indexes on chip, entity, status, dob. `HealthRecord(dog, date, category, description, temperature, weight, vet_name, photos)`. `Vaccination(dog, vaccine_name, date_given, vet_name, due_date, status)`. `DogPhoto(dog, url, category, customer_visible, uploaded_by, ts)`. | ☐ Migrations run ☐ Unique constraint on microchip ☐ FK integrity |
| 2.2 | `backend/apps/operations/schemas.py` | Pydantic v2 schemas | `DogCreate(microchip: str = Field(..., pattern=r'^\d{9,15}$'), ...)`. `DogUpdate(partial)`. `DogList(paginated)`. `DogDetail(with_health, vaccines, litters)`. `HealthRecordCreate`. `VaccinationCreate`. `VaccinationWithDueDate`. | ☐ Schema validates chip format ☐ Pagination works |
| 2.3 | `backend/apps/operations/routers/dogs.py` | Dog CRUD endpoints | `GET /dogs/` — list with filters: `?status=active&entity=holdings&breed=poodle&search=1234`. Sorting: `?sort=-dob,name`. Pagination: `?page=1&per_page=25`. `GET /dogs/{id}` — full detail with nested health/vaccines/litters. `POST /dogs/` — create. `PATCH /dogs/{id}` — update. `DELETE /dogs/{id}` — soft delete. | ☐ Filters combine correctly ☐ Partial chip search works ☐ Entity scoping enforced |
| 2.4 | `backend/apps/operations/routers/health.py` | Health & vaccine endpoints | `GET /dogs/{id}/health/` — list health records. `POST /dogs/{id}/health/` — add record. `GET /dogs/{id}/vaccinations/` — list vaccines with due dates. `POST /dogs/{id}/vaccinations/` — add vaccine. | ☐ Due dates auto-calculated |
| 2.5 | `backend/apps/operations/services/importers.py` | CSV import engine | `import_dogs(csv_path) -> ImportResult`. Column mapper (CSV→model). FK resolution by microchip. Duplicate detection (chip uniqueness). Transactional commit (all-or-nothing). Progress callback for UI. `import_litters(csv_path)` — links to dams/sires by chip. | ☐ 483 dogs import with 0 errors ☐ FK violations caught and reported ☐ Rollback on malformed CSV |
| 2.6 | `backend/apps/operations/services/vaccine.py` | Vaccine due date calculator | `calc_vaccine_due(dog) -> date`. Standard intervals: 21 days (puppy series), 1 year (annual boosters). Overdue detection. Returns next due date + status. Uses `dateutil` for 63-day/1yr calc per PRD. | ☐ Correct for standard vaccine schedules |
| 2.7 | `backend/apps/operations/services/alerts.py` | Alert card data providers | `get_vaccine_overdue() -> QuerySet`. `get_rehome_overdue() -> QuerySet` (5yr yellow, 6yr+ red). `get_in_heat() -> QuerySet`. `get_nursing_flags() -> QuerySet`. `get_nparks_countdown() -> int`. All entity-scoped. | ☐ Alerts match business rules ☐ Entity scoping enforced |
| 2.8 | `backend/apps/operations/admin.py` | Django admin | Dog, HealthRecord, Vaccination, DogPhoto. Search by chip/name. Filters by entity/status. | ☐ Admin panel shows dogs |
| 2.9 | `backend/apps/operations/tests/test_dogs.py` | Dog CRUD tests | Create, read, update, delete. Filter combinations. Entity scoping. Chip uniqueness. | ☐ All pass |
| 2.10 | `backend/apps/operations/tests/test_importers.py` | Import tests | Valid CSV. Malformed CSV (rollback). Duplicate chips. Missing FK references. | ☐ All pass |
| 2.11 | `backend/apps/operations/tests/factories.py` | Test factories | `DogFactory`, `HealthRecordFactory`, `VaccinationFactory`. | ☐ Factories produce valid instances |
| 2.12 | `frontend/hooks/use-dogs.ts` | Dog data hooks | `useDogList(filters)` — paginated list with TanStack Query. `useDog(id)` — detail with health/vaccines/litters. `useAlertCards()` — dashboard alerts. | ☐ Hooks return typed data ☐ Caching works |
| 2.13 | `frontend/components/dogs/dog-table.tsx` | Dog master list table | Columns: chip, name/breed, gender, age dot, unit, last event, dam/sire, DNA badge, vaccine due. Sort by any column. Row click → dog profile. WhatsApp copy button per row. Card reflow on mobile. | ☐ Sort works ☐ WhatsApp copy generates formatted message |
| 2.14 | `frontend/components/dogs/dog-card.tsx` | Dog card (mobile) | Compact card for mobile list view. Name, chip, breed, status badge, age dot. Tap → profile. | ☐ Renders on mobile |
| 2.15 | `frontend/components/dogs/dog-filters.tsx` | Filter bar | Status chips (active/retired/rehomed). Gender toggle. Breed dropdown. Entity dropdown. Search input. All combinable. | ☐ Filters apply simultaneously |
| 2.16 | `frontend/components/dogs/alert-cards.tsx` | Alert cards strip | 6 cards: vaccines overdue, rehome overdue, in heat, 8-week litters, nursing flags, NParks countdown. Each with count, trend indicator, color. | ☐ Counts match backend ☐ Trends show vs prior period |
| 2.17 | `frontend/components/dogs/chip-search.tsx` | Microchip search | Partial chip input (last 4–6 digits). Live dropdown. Name search fallback. Debounced. | ☐ Results appear on partial input |
| 2.18 | `frontend/app/(protected)/dogs/page.tsx` | Master list page | Alert cards strip at top. Filter bar. Dog table. CSV export button. Pagination. | ☐ Full page renders with data |
| 2.19 | `frontend/app/(protected)/dogs/[id]/page.tsx` | Dog profile page | Hero strip (name, chip, age dot, status). 7 tabs: Overview, Health, Breeding, Litters, Media, Genetics, Activity. Role-locked tabs (Breeding/Litters/Genetics locked for Sales/Ground). | ☐ Tabs render ☐ Locked tabs show lock icon |

### Phase 2 Validation

- [ ] `import_dogs('dogs.csv')` → 483 records, 0 FK violations
- [ ] `import_litters('litters.csv')` → 5yr history linked to dams/sires
- [ ] Master list loads <2s with 483 records
- [ ] Partial chip search returns results within 300ms
- [ ] Filter combinations work correctly
- [ ] Dog profile shows all 7 tabs with correct data
- [ ] Role-locked tabs hidden/locked for Sales and Ground staff
- [ ] Entity scoping: Holdings user sees only Holdings dogs

---

<a id="phase-3"></a>
## Phase 3: Ground Operations & Mobile PWA

**Objective:** Mobile-first ground staff interface, 7 log types, Draminski interpreter, SSE alerts, offline PWA.  
**Dependencies:** Phase 2  
**Estimated Effort:** 10–14 days  
**Success Criteria:** All 7 log types persist. Draminski trends render. SSE delivers <500ms. Offline queue syncs on reconnect. PWA installs.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 3.1 | `backend/apps/operations/models.py` (extend) | Ground log models | `InHeatLog(dog, draminski_reading, mating_window, notes, staff, ts)`. `MatedLog(dog, sire, method, sire2, notes, staff, ts)`. `WhelpedLog(dog, method, alive_count, stillborn_count, pups, staff, ts)`. `HealthObsLog(dog, category, description, temperature, weight, photos, staff, ts)`. `WeightLog(dog, weight, staff, ts)`. `NursingFlagLog(dog, section, pup_number, flag_type, photos, severity, staff, ts)`. `NotReadyLog(dog, notes, edd, staff, ts)`. All capture `request.user` and `timestamp` automatically. | ☐ 7 log types defined ☐ FK to Dog ☐ Auto-capture user/ts |
| 3.2 | `backend/apps/operations/schemas.py` (extend) | Log schemas | `InHeatCreate(draminski, notes)`. `MatedCreate(sire_chip, method, sire2_chip?)`. `WhelpedCreate(method, alive, stillborn, pups[])`. `HealthObsCreate(category, description, temp?, weight?, photos[])`. `WeightCreate(weight)`. `NursingFlagCreate(section, pup?, type, photos[], severity)`. `NotReadyCreate(notes?, edd?)`. `LogResponse(id, type, dog, ts)`. | ☐ Schemas validate required fields per type |
| 3.3 | `backend/apps/operations/routers/logs.py` | Log endpoints | `POST /operations/logs/in-heat/{dog_id}`. `POST /operations/logs/mated/{dog_id}`. `POST /operations/logs/whelped/{dog_id}`. `POST /operations/logs/health-obs/{dog_id}`. `POST /operations/logs/weight/{dog_id}`. `POST /operations/logs/nursing-flag/{dog_id}`. `POST /operations/logs/not-ready/{dog_id}`. `GET /operations/logs/{dog_id}` — chronological. All require `X-Idempotency-Key`. | ☐ Each endpoint creates correct log type ☐ Idempotency enforced |
| 3.4 | `backend/apps/operations/services/draminski.py` | Draminski DOD2 interpreter | `interpret(dog_id, reading) -> DraminskiResult`. Per-dog baseline (not global). **Threshold constants:** `<200` early, `200-400` rising (daily readings), `400+` fast, `peak` = highest for this dog, `post-peak drop` = MATE NOW. `calc_window(history) -> MatingWindow`. 7-day trend array. Pure math, no AI. | ☐ Interpretation per-dog ☐ MATE NOW on post-peak drop ☐ Trend array correct ☐ Thresholds match PRD |
| 3.5 | `backend/apps/operations/routers/stream.py` | SSE alert endpoint | `GET /operations/stream/alerts` — async generator. `text/event-stream`. Reconnect-safe. Filters by user role/entity. Events: nursing_flags, heat_cycles, overdue_alerts. Backpressure handled. | ☐ SSE stream delivers events ☐ Auto-reconnect works ☐ <500ms delivery |
| 3.6 | `backend/apps/operations/services/alerts.py` (extend) | SSE event generators | `get_pending_alerts(user) -> list[AlertEvent]`. Entity-scoped. Deduplicates. Timestamped. | ☐ Alerts filtered by entity |
| 3.7 | `backend/apps/operations/tasks.py` | Celery tasks | `rebuild_closure_table(full_rebuild)` — async closure rebuild. `check_overdue_vaccines()` — daily. `check_rehome_overdue()` — daily. `notify_management(log_type, dog)` — push notification. | ☐ Tasks execute via Celery |
| 3.8 | `backend/apps/operations/tests/test_logs.py` | Log tests | All 7 log types create correctly. Idempotency. User capture. Timestamp. Validation. | ☐ All pass |
| 3.9 | `backend/apps/operations/tests/test_draminski.py` | Draminski tests | Per-dog baseline. Peak detection. MATE NOW trigger. Trend calculation. | ☐ All pass |
| 3.10 | `frontend/app/ground/layout.tsx` | Ground staff layout | Bottom nav (no sidebar). High-contrast mode. Large tap targets. 44px minimum. | ☐ Layout renders on mobile |
| 3.11 | `frontend/app/ground/page.tsx` | Ground staff home | Chip scanner hero. Dog search (partial chip/name). Camera scan button. Quick stats (in heat, nursing, litters, vaccine due). Recent logs (last 5). | ☐ Search works ☐ Camera fallback to file input |
| 3.12 | `frontend/app/ground/log/[type]/page.tsx` | Log form pages | Dynamic form per type. `in-heat`: numpad for Draminski, trend chart, mating window slider. `mated`: sire search, method toggle, sire2 option. `whelped`: method toggle, alive/stillborn counters, pup gender M/F taps. `health-obs`: category selector, text, temp/weight, photo required. `weight`: numpad, history chart. `nursing-flag`: mum/pup sections, pup selector, photo, severity. `not-ready`: one tap, notes, EDD picker. All auto-capture timestamp. | ☐ Each form renders correctly ☐ 44px tap targets ☐ Photo upload works |
| 3.13 | `frontend/components/ground/numpad.tsx` | Numpad input | Large buttons. Decimal point. Clear. Submit. Display shows current value. | ☐ Touch-friendly |
| 3.14 | `frontend/components/ground/draminski-chart.tsx` | Draminski trend chart | 7-day line chart. Today's reading highlighted. Color zones (green/yellow/red). Responsive. | ☐ Chart renders with data |
| 3.15 | `frontend/components/ground/log-form.tsx` | Base log form wrapper | Auto-timestamp display. Dog info header. Submit with idempotency key. Loading/error states. Offline queue integration. | ☐ Submits correctly |
| 3.16 | `frontend/components/ground/camera-scan.tsx` | Camera barcode scanner | Camera API. BarcodeDetector API fallback. File input fallback. Returns chip number. | ☐ Camera opens ☐ Fallback works |
| 3.17 | `frontend/lib/offline-queue.ts` | IndexedDB offline queue | `queueLog(type, payload, dogId)`. UUIDv4 per entry. `flushQueue()` on reconnect. Conflict resolution (server wins). `getQueueCount()`. Retry logic (3 attempts). | ☐ Queue persists offline ☐ Flush on reconnect ☐ Badge shows pending count |
| 3.18 | `frontend/lib/pwa/sw.ts` | Service worker | Cache-first for app shell. Network-first for API. Background sync for queued logs. Cache versioning. Offline fallback page. | ☐ App works offline for shell ☐ Logs queue then sync |
| 3.19 | `frontend/lib/pwa/register.ts` | SW registration | Registers service worker. Handles update prompts. Checks for connectivity. Triggers flush on reconnect. | ☐ SW installs |
| 3.20 | `frontend/hooks/use-sse.ts` | SSE hook | `useAlertStream()` — connects to `/operations/stream/alerts`. Auto-reconnect. Event parsing. TypeScript typed events. | ☐ Events arrive in real-time |
| 3.21 | `frontend/hooks/use-offline-queue.ts` | Offline queue hook | `useOfflineQueue()` — queue count, flush trigger, status. Integrates with `authFetch`. | ☐ Badge updates |

### Phase 3 Validation

- [ ] All 7 log types persist with correct metadata
- [ ] Draminski interpreter matches PRD thresholds for test readings
- [ ] SSE stream delivers nursing flags <500ms
- [ ] Offline logs queue in IndexedDB, sync on reconnect
- [ ] PWA installs on iOS/Android, Lighthouse ≥90
- [ ] Camera scan works or gracefully falls back to file input
- [ ] 44px tap targets verified on mobile viewport
- [ ] High-contrast colors pass WCAG AA

---

<a id="phase-4"></a>
## Phase 4: Breeding & Genetics Engine

**Objective:** Mate checker, COI calculation, farm saturation, breeding records, litter management, closure table.  
**Dependencies:** Phase 2  
**Estimated Effort:** 7–10 days  
**Success Criteria:** COI <500ms p95. Saturation accurate. Override audit logged. Dual-sire supported.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 4.1 | `backend/apps/breeding/models.py` | BreedingRecord, Litter, Puppy, DogClosure models | `BreedingRecord(dam, sire1, sire2?, date, method, confirmed_sire, notes)`. `Litter(breeding_record, whelp_date, delivery_method, alive_count, stillborn_count)`. `Puppy(litter, microchip?, gender, colour, birth_weight, confirmed_sire, paternity_method, status, buyer?)`. `DogClosure(ancestor, descendant, depth)` — closure table for pedigree. Indexes on (ancestor, descendant) unique pair. **NO DB TRIGGERS** (rebuild via Celery per v1.1 hardening). | ☐ Migrations run ☐ Dual-sire fields nullable ☐ Closure table indexed ☐ No triggers |
| 4.2 | `backend/apps/breeding/schemas.py` | Pydantic schemas | `MateCheckRequest(dam_chip, sire1_chip, sire2_chip?)`. `MateCheckResult(coi_pct, saturation_pct, verdict, shared_ancestors[])`. `BreedingRecordCreate`. `LitterCreate`. `PuppyCreate`. `OverrideCreate(reason, notes)`. | ☐ Schemas validate chip formats |
| 4.3 | `backend/apps/breeding/routers/mating.py` | Mate checker endpoint | `POST /breeding/mate-check` — accepts dam + sire1 + optional sire2. Returns COI, saturation, verdict, shared ancestors. `POST /breeding/mate-check/override` — requires reason + notes, logs to audit. `GET /breeding/mate-check/history` — override log. | ☐ COI calculates correctly ☐ Override requires reason+notes ☐ Audit logged |
| 4.4 | `backend/apps/breeding/routers/litters.py` | Litter CRUD | `GET /breeding/litters/` — list with filters. `POST /breeding/litters/` — create. `PATCH /breeding/litters/{id}` — update. `GET /breeding/litters/{id}` — detail with puppies. `POST /breeding/litters/{id}/puppies` — add puppy. | ☐ Litter CRUD works ☐ Puppy FK to litter |
| 4.5 | `backend/apps/breeding/services/coi.py` | COI calculator | `calc_coi(dam_id, sire_id, generations=5) -> COIResult`. Uses closure table traversal. Wright's formula. Returns coefficient + shared ancestor list. Handles missing parents gracefully. Deterministic. Cached (Redis, 1h). | ☐ COI matches manual calculation for 10 test pairs ☐ <500ms p95 |
| 4.6 | `backend/apps/breeding/services/saturation.py` | Farm saturation calculator | `calc_saturation(sire_id, entity_id) -> float`. % of active dogs in entity sharing sire ancestry. Uses closure table. Thresholds: <15 green, 15-30 yellow, >30 red. Scopes to active dogs only. | ☐ Saturation correct for test sire ☐ Entity-scoped |
| 4.7 | `backend/apps/breeding/tasks.py` | Celery closure rebuild | `@shared_task(queue="low", bind=True, max_retries=2) def rebuild_closure_table(self, full_rebuild: bool = False)`. Full: TRUNCATE + recursive CTE insert. Incremental: single-dog path update. **No DB triggers** (async Celery only per v1.1 hardening). | ☐ Full rebuild <8s for 483 dogs ☐ Incremental <1s ☐ No triggers |
| 4.8 | `backend/apps/breeding/admin.py` | Django admin | BreedingRecord, Litter, Puppy, DogClosure. | ☐ Admin panel shows data |
| 4.9 | `backend/apps/breeding/tests/test_coi.py` | COI tests | Known pedigree → expected COI. Missing parents. 5-generation depth. Cache hit. | ☐ All pass |
| 4.10 | `backend/apps/breeding/tests/test_saturation.py` | Saturation tests | Known sire → expected %. Entity scoping. Active-only filter. | ☐ All pass |
| 4.11 | `backend/apps/breeding/tests/factories.py` | Test factories | `BreedingRecordFactory`, `LitterFactory`, `PuppyFactory`, `DogClosureFactory`. | ☐ Factories produce valid instances |
| 4.12 | `frontend/app/(protected)/breeding/mate-checker/page.tsx` | Mate checker UI | Dam search (chip/name). Sire #1 search. Optional Sire #2. Submit → COI gauge + saturation bar + verdict card. Shared ancestors list. Override modal (reason + notes). History table. | ☐ Search works ☐ COI gauge animates ☐ Override logs to audit |
| 4.13 | `frontend/app/(protected)/breeding/page.tsx` | Breeding records list | Table of breeding records. Filters by dam/sire/date. Create new. Click → detail. | ☐ List renders |
| 4.14 | `frontend/components/breeding/coi-gauge.tsx` | COI gauge component | Circular gauge. Color: green (<6.25%), yellow (6.25-12.5%), red (>12.5%). Percentage in center. Animated fill. | ☐ Gauge renders with correct color |
| 4.15 | `frontend/components/breeding/saturation-bar.tsx` | Saturation bar | Horizontal bar. Color: green (<15%), yellow (15-30%), red (>30%). Percentage label. | ☐ Bar renders correctly |
| 4.16 | `frontend/components/breeding/mate-check-form.tsx` | Mate check form | Dam + sire chip searches. Submit button. Loading state. Results panel. | ☐ Form submits and displays results |

### Phase 4 Validation

- [ ] COI matches manual calculation for 10 test pairs
- [ ] Farm saturation scopes to entity correctly
- [ ] Dual-sire records flow to NParks mating sheet
- [ ] Override requires reason + notes, logged immutably
- [ ] Closure table rebuilds on new litter import
- [ ] COI <500ms at p95 under k6 load
- [ ] Mate checker UI is responsive on mobile

---

<a id="phase-5"></a>
## Phase 5: Sales Agreements & AVS Tracking

**Objective:** B2C/B2B/Rehoming wizards, PDF generation via Gotenberg, e-signature, AVS state machine, 3-day reminder.  
**Dependencies:** Phase 2, Phase 1  
**Estimated Effort:** 10–12 days  
**Success Criteria:** PDFs cryptographically hashed. AVS reminders fire at 72h. E-sign captures legally.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 5.1 | `backend/apps/sales/models.py` | SalesAgreement, AgreementLineItem, AVSTransfer, Signature, TCTemplate models | `SalesAgreement(type: B2C|B2B|REHOME, buyer_info, entity, status: DRAFT|SIGNED|COMPLETED|CANCELLED, pdf_hash, created_by, ts)`. `AgreementLineItem(agreement, dog, price, gst_component)`. `AVSTransfer(agreement, dog, buyer, token, status, reminder_sent, completed_at)`. `Signature(agreement, signer_type, method, coordinates, ip, timestamp, image_url)`. `TCTemplate(type, content, version, updated_by, ts)`. | ☐ Migrations run ☐ SHA-256 hash stored ☐ AVS token unique |
| 5.2 | `backend/apps/sales/schemas.py` | Pydantic schemas | `AgreementCreate(type, buyer, dogs[], pricing, tc_acceptance)`. `AgreementResponse`. `SignatureCreate(method, coordinates?)`. `AVSStatusUpdate`. | ☐ Schemas validate all 3 agreement types |
| 5.3 | `backend/apps/sales/routers/agreements.py` | Agreement endpoints | `POST /sales/agreements/` — create draft. `PATCH /sales/agreements/{id}` — update. `POST /sales/agreements/{id}/sign` — capture signature. `POST /sales/agreements/{id}/send` — generate PDF + dispatch. `GET /sales/agreements/{id}` — detail. `GET /sales/agreements/` — list with filters. | ☐ CRUD works ☐ Sign captures coordinates ☐ Send generates PDF |
| 5.4 | `backend/apps/sales/routers/avs.py` | AVS endpoints | `GET /sales/avs/pending` — pending transfers. `POST /sales/avs/{id}/complete` — mark complete. `GET /sales/avs/{id}/link` — get transfer link. | ☐ AVS tracking works |
| 5.5 | `backend/apps/sales/services/agreement.py` | Agreement state machine | `create_agreement(type, data) -> SalesAgreement`. State transitions: DRAFT→SIGNED→COMPLETED. GST extraction: `Decimal(price) * 9 / 109`, `ROUND_HALF_UP`. Thomson = 0%. T&C injection from template. HDB warning logic. | ☐ State transitions enforced ☐ GST exact to 2 decimals |
| 5.6 | `backend/apps/sales/services/pdf.py` | PDF generation via Gotenberg | `render_agreement_pdf(agreement_id) -> bytes`. HTML template → Gotenberg `/forms/chromium/convert/html`. Pixel-perfect. E-signature coordinates rendered. Watermark on draft. SHA-256 hash computed and stored. | ☐ PDF matches on-screen preview ☐ Hash stored |
| 5.7 | `backend/apps/sales/services/avs.py` | AVS transfer management | `send_avs_link(agreement)` — generates unique token, sends to buyer. `check_completion()` — checks if transfer done. `escalate_to_staff(transfer)` — if 72h pending. State tracking: PENDING→SENT→COMPLETED/ESCALATED. | ☐ Unique token per buyer ☐ 72h escalation |
| 5.8 | `backend/apps/sales/tasks.py` | Celery tasks | `send_agreement_pdf(agreement_id)` — PDF gen + email/WA dispatch. Retry 3x exponential. `avs_reminder_check()` — beat schedule, daily. Dispatches reminders for 72h pending. DLQ on failure. | ☐ Tasks execute ☐ Retry works ☐ DLQ captures failures |
| 5.9 | `backend/apps/sales/admin.py` | Django admin | SalesAgreement, AVSTransfer, Signature, TCTemplate. | ☐ Admin shows agreements |
| 5.10 | `backend/apps/sales/tests/test_agreements.py` | Agreement tests | B2C/B2B/Rehoming flows. GST calculation. State transitions. Signature capture. PDF hash. | ☐ All pass |
| 5.11 | `backend/apps/sales/tests/test_avs.py` | AVS tests | Token generation. Reminder firing. Escalation. | ☐ All pass |
| 5.12 | `frontend/app/(protected)/sales/page.tsx` | Agreements list | Table of agreements. Filters by type/status/entity. Create new button. | ☐ List renders |
| 5.13 | `frontend/app/(protected)/sales/wizard/page.tsx` | 5-step wizard | Step 1: Dog selection (chip search, entity). Step 2: Buyer details (name, NRIC, mobile, email, address, HDB warning, PDPA checkbox). Step 3: Health disclosure (editable dog details, vaccination rows, health check). Step 4: Pricing (price, deposit non-refundable banner, balance calc, GST extraction, payment method). Step 5: T&C (read-only, special conditions, signature: In Person/Remote/Paper). Step validation blocks next. | ☐ All 5 steps render ☐ HDB warning shows ☐ Deposit non-refundable prominent |
| 5.14 | `frontend/components/sales/wizard-steps.tsx` | Individual step components | `DogSelectionStep`, `BuyerDetailsStep`, `HealthDisclosureStep`, `PricingStep`, `SignatureStep`. Each validates before allowing next. | ☐ Step validation works |
| 5.15 | `frontend/components/sales/agreement-preview.tsx` | Agreement preview panel | Live preview of agreement content. Updates as steps complete. Responsive. | ☐ Preview matches final PDF |
| 5.16 | `frontend/components/ui/signature-pad.tsx` | Signature pad | Canvas-based. Touch + mouse. Clear. Undo. Export as data URL. Coordinates captured. | ☐ Signature captures on touch |

### Phase 5 Validation

- [ ] B2C/B2B/Rehoming flows complete without errors
- [ ] PDF hash matches stored record (tamper-evident)
- [ ] AVS reminder fires at 72h; escalation logs
- [ ] PDPA opt-in captured at step 2; enforced downstream
- [ ] E-sign captures coordinates, IP, timestamp
- [ ] GST: 109→9.00, 218→18.00, 50→4.13 (exact)
- [ ] Thomson entity: GST = 0

---

<a id="phase-6"></a>
## Phase 6: Compliance & NParks Reporting

**Objective:** Deterministic NParks Excel generation, GST engine, PDPA hard filters, submission lock, audit immutability.  
**Dependencies:** Phase 2, Phase 4, Phase 5  
**Estimated Effort:** 7–10 days  
**Success Criteria:** Zero AI in compliance. Excel matches NParks template. Month lock immutable.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 6.1 | `backend/apps/compliance/models.py` | NParksSubmission, GSTLedger, PDPAConsentLog models | `NParksSubmission(entity, month, status: DRAFT|SUBMITTED|LOCKED, generated_at, submitted_at, locked_at)`. Unique(entity, month). `GSTLedger(entity, period, total_sales, gst_component, source_agreement)`. `PDPAConsentLog(customer, action: OPT_IN|OPT_OUT, previous_state, new_state, actor, ts)` — immutable. | ☐ Migrations run ☐ Unique constraint on (entity, month) ☐ PDPA log immutable |
| 6.2 | `backend/apps/compliance/schemas.py` | Pydantic schemas | `NParksGenerateRequest(entity, month)`. `NParksPreview(doc_type, rows[])`. `GSTExport(entity, quarter)`. `PDPAConsentUpdate(customer_id, action)`. | ☐ Schemas validate entity/month |
| 6.3 | `backend/apps/compliance/routers/nparks.py` | NParks endpoints | `POST /compliance/nparks/generate` — generate all 5 docs for entity+month. `GET /compliance/nparks/preview/{id}` — preview table. `POST /compliance/nparks/submit/{id}` — mark submitted. `POST /compliance/nparks/lock/{id}` — lock month. `GET /compliance/nparks/download/{id}` — Excel file. | ☐ Generate produces 5 docs ☐ Lock prevents edits ☐ 403 if unauthorized |
| 6.4 | `backend/apps/compliance/routers/gst.py` | GST endpoints | `GET /compliance/gst/summary?entity=&quarter=` — GST summary. `GET /compliance/gst/export?entity=&quarter=` — Excel export. | ☐ GST sums match ledger |
| 6.5 | `backend/apps/compliance/services/nparks.py` | NParks Excel generator | `generate_nparks(entity_id, month) -> dict[doc_type, bytes]`. 5 documents: mating_sheet, puppy_movement, vet_treatments, puppies_bred, dog_movement. Uses `openpyxl` with template injection. Dual-sire columns. Deterministic sort. Zero string interpolation from AI. Farm details pre-filled (DB000065X). | ☐ Excel matches NParks template ☐ Zero AI imports ☐ Dual-sire columns present |
| 6.6 | `backend/apps/compliance/services/gst.py` | GST engine | `extract_gst(price, entity) -> Decimal`. Formula: `Decimal(price) * Decimal('9') / Decimal('109')`. `quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)`. Thomson = 0%. Entity-aware. | ☐ 109→9.00 ☐ 218→18.00 ☐ 50→4.13 ☐ Thomson=0 |
| 6.7 | `backend/apps/compliance/services/pdpa.py` | PDPA enforcement | `filter_consent(queryset) -> QuerySet` — hard `WHERE pdpa_consent=true`. `log_consent_change(customer, action, actor)` — immutable audit. `check_blast_eligibility(customer_ids) -> (eligible, excluded)`. No override path. | ☐ Blast excludes opted-out at query level ☐ Consent log immutable |
| 6.8 | `backend/apps/compliance/tasks.py` | Celery tasks | `generate_monthly_nparks(entity_id, month)` — scheduled monthly. `lock_expired_submissions()` — auto-lock past months. | ☐ Tasks execute on schedule |
| 6.9 | `backend/apps/compliance/admin.py` | Django admin | NParksSubmission, GSTLedger, PDPAConsentLog. All read-only after creation. | ☐ Admin shows compliance data |
| 6.10 | `backend/apps/compliance/tests/test_nparks.py` | NParks tests | Generate for each entity. Dual-sire columns. Lock prevents edits. Template match. | ☐ All pass |
| 6.11 | `backend/apps/compliance/tests/test_gst.py` | GST tests | 10 test cases with known values. Thomson=0. ROUND_HALF_UP. | ☐ All pass |
| 6.12 | `backend/apps/compliance/tests/test_pdpa.py` | PDPA tests | Filter excludes opted-out. Consent log immutable. Blast eligibility check. | ☐ All pass |
| 6.13 | `frontend/app/(protected)/compliance/page.tsx` | NParks page | Entity selector. Month picker. Generate All button. Preview table per doc. Download Excel. Submit/lock buttons. Status badges. | ☐ Generate works ☐ Download produces Excel |
| 6.14 | `frontend/app/(protected)/compliance/settings/page.tsx` | T&C settings (admin) | Three editable T&C templates (B2C, B2B, Rehoming). Version history. Preview. Save. | ☐ Templates editable ☐ Changes apply to future agreements |

### Phase 6 Validation

- [ ] NParks Excel matches official template pixel/column
- [ ] GST calculation exact to 2 decimals; Thomson=0
- [ ] PDPA filter blocks opted-out at DB query level
- [ ] Month lock prevents any POST/PATCH to that period
- [ ] Zero `import anthropic/openai/langchain` in compliance module (`grep` verified)
- [ ] `PDPAConsentLog` is append-only (no UPDATE/DELETE)

---

<a id="phase-7"></a>
## Phase 7: Customer DB & Marketing Blast

**Objective:** Customer records, segmentation, Resend/WA API integration, PDPA-enforced blasts, comms logging.  
**Dependencies:** Phase 5, Phase 6  
**Estimated Effort:** 7–10 days  
**Success Criteria:** Blasts respect PDPA hard filter. Send progress live. Comms logged per customer.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 7.1 | `backend/apps/customers/models.py` | Customer, CommunicationLog, Segment models | `Customer(name, nric, mobile, email, address, housing_type, pdpa_consent, entity, notes)`. Unique mobile. `CommunicationLog(customer, channel: EMAIL|WA, campaign_id, status: SENT|DELIVERED|BOUNCED|FAILED, message_preview, ts)`. `Segment(name, filters_json, created_by, ts)`. | ☐ Migrations run ☐ Unique mobile ☐ CommsLog immutable |
| 7.2 | `backend/apps/customers/schemas.py` | Pydantic schemas | `CustomerCreate`. `CustomerUpdate`. `CustomerList(paginated)`. `SegmentCreate(filters)`. `BlastCreate(segment_id, channel, subject?, body, merge_tags)`. | ☐ Schemas validate |
| 7.3 | `backend/apps/customers/routers/customers.py` | Customer endpoints | `GET /customers/` — list with filters (search, breed, entity, pdpa, date range). `GET /customers/{id}` — detail with comms history. `POST /customers/` — manual add. `PATCH /customers/{id}` — update. `POST /customers/import` — CSV upload with column mapping. `POST /customers/blast` — send blast. `GET /customers/blast/{id}/progress` — SSE progress. | ☐ Filters combine ☐ CSV import works ☐ Blast excludes PDPA=false |
| 7.4 | `backend/apps/customers/services/segmentation.py` | Segment builder | `build_segment(filters) -> QuerySet`. Composable Q objects. Auto-excludes PDPA=false. Cached counts. Preview mode (count without fetching). | ☐ Segment matches filters ☐ PDPA exclusion automatic |
| 7.5 | `backend/apps/customers/services/blast.py` | Blast dispatch | `send_blast(segment_id, channel, template) -> BlastResult`. Resend email SDK. WA Business Cloud API. Merge tag interpolation: `{{name}}`, `{{breed}}`, `{{entity}}`, `{{mobile}}`. Rate limit: 10/sec. Bounce handling. | ☐ Emails deliver ☐ WA messages deliver ☐ Rate limit enforced |
| 7.6 | `backend/apps/customers/services/template_manager.py` | WA template approval cache | `TemplateManager` — caches Meta template approval status. `is_approved(template_name)` — checks cache or fetches from Meta API. `refresh_status(template_name)` — updates cache. | ☐ Template status cached ☐ Auto-refresh on expiry |
| 7.7 | `backend/apps/customers/services/comms_router.py` | WA template + email fallback router | `CommunicationRouter.route(customer, template, payload)` — checks `TemplateManager.is_approved()`. Falls back to Resend email on unapproved/rejected templates or WA API failure. Logs channel switch in CommunicationLog. | ☐ Email fallback <500ms on WA failure ☐ Channel switch logged |
| 7.8 | `backend/apps/customers/tasks.py` | Celery fan-out | `@shared_task(queue="default") dispatch_blast(blast_id)` — chunked dispatch (50 per chunk). Exponential retry. DLQ on 3 failures. Updates progress via Redis pub/sub. `@shared_task(queue="low") log_delivery(customer_id, channel, status)` — per-message logging. | ☐ Fan-out works ☐ Progress updates live ☐ DLQ captures failures |
| 7.9 | `backend/apps/customers/admin.py` | Django admin | Customer, CommunicationLog, Segment. | ☐ Admin shows customers |
| 7.10 | `backend/apps/customers/tests/test_segmentation.py` | Segmentation tests | Filter combinations. PDPA exclusion. Cached counts. | ☐ All pass |
| 7.11 | `backend/apps/customers/tests/test_blast.py` | Blast tests | Mock Resend/WA APIs. Rate limiting. Bounce handling. PDPA enforcement. Template fallback. | ☐ All pass |
| 7.11 | `frontend/app/(protected)/customers/page.tsx` | Customer DB page | List view with filters. Expandable row → profile. PDPA badge inline editable. Blast composer. Progress bar (SSE). Comms history tab. CSV import with column mapping. | ☐ Filters work ☐ Blast sends ☐ Progress live |
| 7.12 | `frontend/hooks/use-customers.ts` | Customer data hooks | `useCustomerList(filters)`. `useCustomer(id)`. `useBlastProgress(blastId)`. | ☐ Hooks return typed data |

### Phase 7 Validation

- [ ] Segment builder matches filters exactly
- [ ] Blast excludes PDPA=false; warning shows excluded count
- [ ] Resend/WA APIs deliver; bounces logged
- [ ] Progress bar updates via SSE
- [ ] CommunicationLog immutable; searchable per customer
- [ ] CSV import detects duplicates by mobile number

---

<a id="phase-8"></a>
## Phase 8: Dashboard & Finance Exports

**Objective:** Role-aware dashboard, alert cards, activity feed, P&L, GST reports, intercompany transfers, Excel export.  
**Dependencies:** Phase 2–7  
**Estimated Effort:** 7–10 days  
**Success Criteria:** Dashboard loads <2s. Alerts accurate. Finance exports match ledger. Role views correct.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 8.1 | `backend/apps/finance/models.py` | Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot models | `Transaction(type: REVENUE|EXPENSE|TRANSFER, amount, entity, gst_component, date, category, description, source_agreement?)`. `IntercompanyTransfer(from_entity, to_entity, amount, date, description)`. `GSTReport(entity, quarter, total_sales, total_gst, generated_at)`. `PNLSnapshot(entity, month, revenue, cogs, expenses, net)`. | ☐ Migrations run ☐ Intercompany balanced (debit=credit) |
| 8.2 | `backend/apps/finance/schemas.py` | Pydantic schemas | `TransactionCreate`. `PNLResponse(entity, month, revenue, cogs, expenses, net)`. `GSTReportResponse`. `IntercompanyCreate`. | ☐ Schemas validate |
| 8.3 | `backend/apps/finance/routers/reports.py` | Finance endpoints | `GET /finance/pnl?entity=&month=` — P&L statement. `GET /finance/gst?entity=&quarter=` — GST report. `GET /finance/transactions?entity=&type=&date_range=` — transaction list. `POST /finance/intercompany` — create transfer. `GET /finance/export/pnl?entity=&month=` — Excel download. `GET /finance/export/gst?entity=&quarter=` — Excel download. | ☐ P&L balances ☐ GST matches ledger ☐ Excel exports work |
| 8.4 | `backend/apps/finance/services/pnl.py` | P&L calculator | `calc_pnl(entity, month) -> PNLResult`. Groups by category. YTD rollup. Handles intercompany eliminations. Deterministic. | ☐ P&L balances |
| 8.5 | `backend/apps/finance/services/gst_report.py` | GST report generator | `gen_gst_report(entity, quarter) -> bytes`. Sums GST components. IRAS format. Excel export via openpyxl. Zero AI interpolation. | ☐ GST report matches IRAS requirements |
| 8.6 | `backend/apps/finance/admin.py` | Django admin | Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot. | ☐ Admin shows finance data |
| 8.7 | `backend/apps/finance/tests/test_pnl.py` | P&L tests | Known transactions → expected P&L. Intercompany elimination. YTD rollup. | ☐ All pass |
| 8.8 | `backend/apps/finance/tests/test_gst.py` | GST report tests | Known data → expected GST report. Entity-specific (Thomson=0). | ☐ All pass |
| 8.9 | `backend/apps/finance/tests/factories.py` | Test factories | `TransactionFactory`, `IntercompanyTransferFactory`. | ☐ Factories produce valid instances |
| 8.10 | `frontend/app/(protected)/dashboard/page.tsx` | Dashboard page | Role-aware rendering. Management: NParks countdown, quick mate checker, 7 alert cards with trends, vaccine overdue list, nursing flags, age alerts, activity feed (SSE), revenue chart, upcoming collections. Ground: nursing banner, chip scanner hero, unit stats, quick logs, recent logs. Sales: unsigned agreements, pending AVS. | ☐ Role-specific views render ☐ Dashboard <2s load |
| 8.11 | `frontend/app/(protected)/finance/page.tsx` | Finance page | P&L by entity (monthly/YTD). GST report. Transaction list. Intercompany transfers. Excel download buttons. | ☐ Exports work ☐ P&L displays |
| 8.12 | `frontend/components/dashboard/nparks-countdown.tsx` | NParks countdown card | Days to month-end. Pending records flagged. Blue gradient. | ☐ Countdown accurate |
| 8.13 | `frontend/components/dashboard/alert-feed.tsx` | Activity feed | Last 10 ground staff + admin logs. SSE-powered. Timestamped. | ☐ Feed updates live |
| 8.14 | `frontend/components/dashboard/revenue-chart.tsx` | Revenue chart | Month-to-date by entity. Bar chart. Responsive. | ☐ Chart renders |

### Phase 8 Validation

- [ ] Dashboard loads <2s on standard Singapore broadband
- [ ] Alert cards match live DB counts
- [ ] P&L balances; intercompany nets to zero
- [ ] GST report matches IRAS requirements
- [ ] Role views hide unauthorized metrics
- [ ] Finance Excel exports contain correct data

---

<a id="phase-9"></a>
## Phase 9: Observability, Security & Production Readiness

**Objective:** OpenTelemetry, CSP hardening, Trivy/Snyk scans, load testing, runbooks, disaster recovery, final QA.  
**Dependencies:** Phase 0–8  
**Estimated Effort:** 5–7 days  
**Success Criteria:** Zero critical CVEs. OTel traces flow. Load test passes. Runbooks complete. Sign-off ready.

### Files to Create

| # | File | Description | Features & Interfaces | Checklist |
|---|------|-------------|----------------------|-----------|
| 9.1 | `backend/config/otel.py` | OpenTelemetry setup | `init_otel()`. Auto-instruments Django, psycopg, Celery. Custom spans: COI calc, NParks gen, PDF render. Metrics: queue depth, request latency, error rate. Prometheus exporter. | ☐ Traces flow to collector ☐ Custom spans appear |
| 9.2 | `frontend/instrumentation.ts` | Next.js OTel | `register()`. Traces BFF→Django chain. Web Vitals to OTel. CSP violation reporting. Error boundary. | ☐ Frontend traces appear |
| 9.3 | `tests/load/k6.js` | Load test scripts | Auth flow. Dog list (483 records). Mate checker. NParks gen. Blast dispatch. 50 VUs. Thresholds: p95 <2s, COI <500ms, NParks <3s, SSE <500ms, zero 5xx. | ☐ All thresholds pass |
| 9.4 | `docs/RUNBOOK.md` | Operations runbook | Deploy procedure. Scale Celery workers. PgBouncer tuning. Celery DLQ recovery. WAL-G PITR restore. SSE reconnect handling. PWA cache clear. Incident response. | ☐ Runbook complete |
| 9.5 | `docs/SECURITY.md` | Security documentation | Threat model. CSP policy. PDPA compliance proof. OWASP Top 10 mitigations. Audit log access policy. Penetration test results. | ☐ Security doc complete |
| 9.6 | `docs/DEPLOYMENT.md` | Deployment guide | Docker Compose production setup. Environment variables. SSL/TLS. Domain config. Backup schedule. Monitoring setup. | ☐ Deployment guide complete |
| 9.7 | `docs/API.md` | API documentation | Auto-generated from OpenAPI. Authentication. Rate limits. Error codes. Examples for each endpoint. | ☐ API docs match actual endpoints |
| 9.8 | `scripts/backup.sh` | WAL-G backup script | Full backup. WAL archiving. PITR procedure. R2 destination. Cron schedule. | ☐ Backup runs successfully |
| 9.9 | `nginx/nginx.conf` | Nginx reverse proxy (optional) | TLS termination. Proxy to Next.js. Static file serving. Rate limiting. CSP headers. | ☐ Nginx proxies correctly |

### Phase 9 Validation

- [ ] Trivy/Snyk: 0 critical/high CVEs
- [ ] CSP blocks inline eval; report-only disabled
- [ ] OTel traces flow to Grafana; dashboards live
- [ ] k6 load test passes all thresholds
- [ ] WAL-G PITR restore verified (test restore to separate instance)
- [ ] Runbooks complete and tested
- [ ] All sign-off checkboxes from Phase 0–8 verified

---

## 13. Cross-Cutting Concerns

### 13.1 Testing Strategy

| Layer | Framework | Coverage Target | Scope |
|-------|-----------|-----------------|-------|
| Backend unit | pytest + pytest-django | ≥85% | Models, services, serializers |
| Backend integration | pytest + httpx | ≥70% | API endpoints, auth flows |
| Frontend unit | Vitest + Testing Library | ≥85% | Components, hooks, utilities |
| Frontend E2E | Playwright | Critical paths | Login, dog CRUD, sales wizard, NParks gen |
| Load | k6 | Thresholds pass | Auth, dog list, mate checker, NParks, blast |
| Security | Trivy + Snyk + OWASP ZAP | 0 critical CVEs | Images, dependencies, BFF proxy |

### 13.2 Security Checklist (All Phases)

- [ ] BFF proxy: server-only `BACKEND_INTERNAL_URL`, path allowlist, header sanitization
- [ ] Auth: HttpOnly, Secure, SameSite=Lax cookies. CSRF rotation. Redis sessions.
- [ ] RBAC: Role decorators on every endpoint. Entity scoping. Fails closed.
- [ ] PDPA: Hard `WHERE pdpa_consent=true`. No override. Immutable consent log.
- [ ] Compliance: Zero AI imports in `compliance/` module. Deterministic outputs.
- [ ] Audit: `AuditLog` immutable. SHA-256 PDF hash. Override logging.
- [ ] CSP: `script-src 'self' 'strict-dynamic'`. No `'unsafe-eval'`. Report-only disabled.
- [ ] Idempotency: UUIDv4 keys on POST. Redis store (24h TTL). Duplicate detection.
- [ ] Input validation: Pydantic schemas on all inputs. Regex for microchip. Decimal for money.
- [ ] SQL injection: Django ORM only. No raw SQL except closure table (parameterized).

### 13.3 Performance Budgets

| Endpoint | Target | Measurement |
|----------|--------|-------------|
| Dashboard | <2s | k6 p95 |
| Dog list (483 records) | <500ms | k6 p95 |
| Mate checker (COI) | <500ms | k6 p95 |
| NParks generate (5 docs) | <3s | k6 p95 |
| SSE alert delivery | <500ms | k6 |
| PWA install | <3s | Lighthouse |
| PDF generation | <5s | Gotenberg benchmark |

### 13.4 Cross-Cutting Validation Matrix (from draft_plan v1.1)

| Requirement | Implementation | Verification Method |
|-------------|----------------|---------------------|
| **BFF HttpOnly** | Next.js proxy forwards cookies; Django validates session | Playwright: `window.*` token scan → empty |
| **Compliance Determinism** | Pure Python/SQL in `compliance/`; zero AI imports | `grep -r "anthropic\|openai\|langchain" backend/apps/compliance/` → 0 matches |
| **GST 9/109** | `Decimal(price) * 9 / 109`, `ROUND_HALF_UP` | Unit tests: 109→9.00, 218→18.00, 50→4.13 |
| **PDPA Hard Block** | `WHERE pdpa_consent=true` at queryset + DB constraint | Pen test: blast to opted-out → 0 delivered |
| **COI Performance** | Closure table + recursive CTE + Redis cache | k6: p95 <500ms on 5-gen pedigree |
| **NParks Excel** | `openpyxl` template injection, zero AI | Diff vs official template → 0 deviation |
| **AVS 3-Day Reminder** | Celery Beat schedule, idempotent send, escalation | Mock time → task fires → comms logged |
| **PWA Offline** | Service worker + IndexedDB queue + background sync | DevTools offline → queue → reconnect → sync |
| **SSE Realtime** | Async generator + `text/event-stream` + EventSource | k6: alert delivery <500ms, auto-reconnect <3s |
| **Audit Immutability** | `AuditLog` no UPDATE/DELETE, SHA-256 PDF hash | DB trigger blocks modification; hash verifies |

### 13.5 Execution Protocol & Sign-Off

1. **Phase Gating:** Each phase requires checklist completion + lead review before merging to `main`.
2. **Compliance Freeze:** Phase 6 locks NParks/GST/PDPA logic. Changes require architecture review + regression suite.
3. **AI Boundary Enforcement:** `backend/apps/ai_sandbox/` is the only directory permitted LLM imports. CI fails on violation.
4. **Performance Budget:** Dashboard <2s, COI <500ms, NParks <3s, SSE <500ms. k6 enforces in CI.
5. **Security Baseline:** CSP enforced, Trivy blocks CVEs, PDPA hard filter, HttpOnly BFF, audit immutability.
6. **Handoff:** Phase 9 delivers runbooks, OTel dashboards, PITR procedure, load test reports, and sign-off matrix.

**Approval Signatures:**
`[ ] Architecture Lead` | `[ ] Compliance Officer` | `[ ] DevOps Lead` | `[ ] Product Owner`
**Date:** _______________ | **Version:** 2.0 | **Status:** READY FOR EXECUTION

---

## 14. Dependency Graph

```
Phase 0 (Infrastructure)
    │
    ▼
Phase 1 (Auth, BFF, RBAC, Design System)
    │
    ├──────────────────┐
    ▼                  ▼
Phase 2 (Domain      Phase 2 enables all subsequent phases
Foundation)
    │
    ├──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼
Phase 3     Phase 4     Phase 5     Phase 6
(Ground)    (Breeding)  (Sales)     (Compliance)
    │          │          │           │
    │          │          └─────┬─────┘
    │          │                │
    │          │                ▼
    │          │           Phase 7 (Customers)
    │          │                │
    └──────────┴────────────────┘
                    │
                    ▼
              Phase 8 (Dashboard & Finance)
                    │
                    ▼
              Phase 9 (Observability & Production)
```

**Parallel execution:** Phases 3, 4, 5 can proceed in parallel after Phase 2. Phase 6 needs Phase 2 + 4 + 5. Phase 7 needs Phase 5 + 6. Phase 8 needs all prior. Phase 9 is final.

---

## Summary: File Count by Phase

| Phase | Backend Files | Frontend Files | Total | Est. Days |
|-------|--------------|----------------|-------|-----------|
| 0 | 12 | 8 | 20 | 3–5 |
| 1 | 11 | 25 | 36 | 5–7 |
| 2 | 11 | 8 | 19 | 7–10 |
| 3 | 10 | 12 | 22 | 10–14 |
| 4 | 11 | 5 | 16 | 7–10 |
| 5 | 9 | 7 | 16 | 10–12 |
| 6 | 12 | 2 | 14 | 7–10 |
| 7 | 10 | 2 | 12 | 7–10 |
| 8 | 9 | 5 | 14 | 7–10 |
| 9 | 4 | 5 | 9 | 5–7 |
| **Total** | **99** | **79** | **178** | **~70–95** |

---

*This plan enforces enterprise-grade determinism, security, and performance from day one. No phase proceeds without explicit validation. Compliance paths are mathematically exact. AI is strictly sandboxed. Infrastructure is production-hardened.*
