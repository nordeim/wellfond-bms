# Wellfond BMS — Master TODO Checklist

> Track progress by checking off items. Each phase must be 100% complete before the next begins.

---

## Phase 0: Infrastructure & Foundation Scaffold
**Target: 3–5 days | Status: ⬜ Not Started**

### Verified Dependency Versions (installed April 2026)

**Frontend (npm — 377 packages, 0 vulnerabilities):**
`next@16.2.4` · `react@19.2.5` · `tailwindcss@4.2.4` · `@tailwindcss/postcss@4.2.4` · `typescript@6.0.3` · `framer-motion@12.38.0` · `zustand@5.0.12` · `@tanstack/react-query@5.100.1` · `zod@4.3.6` · `lucide-react@1.9.0` · `sonner@2.0.7` · `@radix-ui/react-checkbox@1.3.3` · `@radix-ui/react-dialog@1.1.15` · `@radix-ui/react-dropdown-menu@2.1.16` · `@radix-ui/react-slot@1.2.4` · `class-variance-authority@0.7.1` · `clsx@2.1.1` · `tailwind-merge@3.5.0` · `react-markdown@10.1.0` · `vite@8.0.10` · `vitest@4.1.5` · `@testing-library/react@16.3.2` · `playwright@1.59.1` · `msw@2.13.5`

**Backend base (pip — 24 packages):**
`Django==6.0.4` · `django-ninja==1.6.2` · `pydantic==2.12.5` · `psycopg2-binary==2.9.10` · `redis==6.4.0` · `hiredis==3.3.0` · `django-cors-headers==4.9.0` · `djangorestframework-simplejwt==5.5.1` · `PyJWT==2.12.1` · `stripe==14.4.1` · `python-decouple==3.8` · `pytz==2025.2` · `python-dateutil==2.9.0.post0` · `Pillow==12.2.0` · `asgiref==3.11.0` · `channels==4.3.2` · `channels-redis==4.3.0` · `django-ratelimit==4.1.0`

**Backend dev (pip — 47 packages):**
`pytest==9.0.3` · `pytest-django==4.12.0` · `pytest-asyncio==1.3.0` · `pytest-cov==7.1.0` · `pytest-xdist==3.8.0` · `factory-boy==3.3.3` · `faker==40.5.1` · `black==26.3.1` · `isort==5.12.0` · `flake8==6.1.0` · `mypy==1.20.0` · `django-stubs==6.0.2` · `ipython==9.10.0` · `django-extensions==4.1` · `django-debug-toolbar==6.3.0` · `mkdocs==1.6.1` · `mkdocs-material==9.6.19`

**To add in Phase 0 scaffold:**
`celery==5.4` · `openpyxl` · `httpx` · `opentelemetry-*` · `python-json-logger`

### Files

- [ ] `docker-compose.yml` — PG17, PgBouncer, Redis×3, Django, Celery, Next.js, Gotenberg, Flower, MinIO
- [ ] `docker-compose.dev.yml` — Dev overrides with hot reload
- [ ] `backend/Dockerfile.django` — Multi-stage, non-root, Trivy-ready
- [ ] `frontend/Dockerfile.nextjs` — Multi-stage, pnpm, standalone output
- [ ] `backend/config/settings/base.py` — Django 6.0 core settings
- [ ] `backend/config/settings/development.py` — Debug toolbar, local DB
- [ ] `backend/config/settings/production.py` — Strict CSP, PgBouncer, OTel
- [ ] `backend/config/celery.py` — Celery app with queue routing
- [ ] `backend/config/urls.py` — Root URL conf
- [ ] `backend/config/asgi.py` — ASGI for async SSE
- [ ] `backend/api.py` — NinjaAPI instance, router registry
- [ ] `backend/manage.py` — Django management script
- [ ] `backend/requirements/base.txt` — Production deps (replace CHA YUAN)
- [ ] `backend/requirements/dev.txt` — Dev deps
- [ ] `frontend/next.config.ts` — Standalone output, BFF rewrites
- [ ] `frontend/tailwind.config.ts` — Tangerine Sky palette
- [ ] `frontend/app/layout.tsx` — Root layout
- [ ] `frontend/app/globals.css` — Global styles
- [ ] `frontend/public/manifest.json` — PWA manifest
- [ ] `.github/workflows/ci.yml` — CI pipeline
- [ ] `.env.example` — Replace CHA YUAN with Wellfond vars
- [ ] `.gitignore` — Complete ignore rules
- [ ] `scripts/seed.sh` — Fixture data loader
- [ ] `README.md` — Project readme
- [ ] **VALIDATE:** All containers boot healthy
- [ ] **VALIDATE:** `/health/` returns 200
- [ ] **VALIDATE:** Network isolation verified
- [ ] **VALIDATE:** CI pipeline green
- [ ] **VALIDATE:** `pip install -r base.txt` → 24 packages, no conflicts
- [ ] **VALIDATE:** `pip install -r dev.txt` → 47 packages, no conflicts
- [ ] **VALIDATE:** `npm install` → 377 packages, 0 vulnerabilities
- [ ] **VALIDATE:** `npm run build` → standalone output

---

## Phase 1: Core Auth, BFF Proxy & RBAC
**Target: 5–7 days | Status: ⬜ Not Started**

- [ ] `backend/apps/core/models.py` — User, Role, Entity, AuditLog
- [ ] `backend/apps/core/auth.py` — Login/logout/refresh with HttpOnly cookies
- [ ] `backend/apps/core/permissions.py` — Role decorators, entity scoping, PDPA filter
- [ ] `backend/apps/core/middleware.py` — Idempotency + entity scoping middleware
- [ ] `backend/apps/core/schemas.py` — Auth/user Pydantic schemas
- [ ] `backend/apps/core/routers/auth.py` — Auth endpoints
- [ ] `backend/apps/core/routers/users.py` — User management (admin)
- [ ] `backend/apps/core/admin.py` — Django admin
- [ ] `backend/apps/core/tests/test_auth.py` — Auth tests
- [ ] `backend/apps/core/tests/test_permissions.py` — Permission tests
- [ ] `backend/apps/core/tests/factories.py` — Test factories
- [ ] `frontend/app/api/proxy/[...path]/route.ts` — Hardened BFF proxy
- [ ] `frontend/lib/api.ts` — authFetch wrapper with idempotency
- [ ] `frontend/lib/auth.ts` — Session helpers
- [ ] `frontend/lib/constants.ts` — App constants
- [ ] `frontend/lib/types.ts` — TypeScript types
- [ ] `frontend/lib/utils.ts` — Utility functions
- [ ] `frontend/middleware.ts` — Route protection
- [ ] `frontend/app/(auth)/login/page.tsx` — Login page
- [ ] `frontend/app/(auth)/layout.tsx` — Auth layout
- [ ] `frontend/app/(protected)/layout.tsx` — Protected layout with sidebar
- [ ] `frontend/components/ui/button.tsx` — Button component
- [ ] `frontend/components/ui/input.tsx` — Input component
- [ ] `frontend/components/ui/card.tsx` — Card component
- [ ] `frontend/components/ui/badge.tsx` — Badge component
- [ ] `frontend/components/ui/dialog.tsx` — Dialog/modal
- [ ] `frontend/components/ui/table.tsx` — Table component
- [ ] `frontend/components/ui/tabs.tsx` — Tabs component
- [ ] `frontend/components/ui/toast.tsx` — Toast notifications
- [ ] `frontend/components/ui/skeleton.tsx` — Loading skeleton
- [ ] `frontend/components/ui/select.tsx` — Select component
- [ ] `frontend/components/ui/progress.tsx` — Progress bar
- [ ] `frontend/components/layout/sidebar.tsx` — Desktop sidebar
- [ ] `frontend/components/layout/topbar.tsx` — Top bar
- [ ] `frontend/components/layout/bottom-nav.tsx` — Mobile bottom nav
- [ ] `frontend/components/layout/role-bar.tsx` — Role indicator bar
- [ ] **VALIDATE:** HttpOnly cookie, zero localStorage tokens
- [ ] **VALIDATE:** BFF proxy rejects non-allowlisted paths
- [ ] **VALIDATE:** Role matrix enforced
- [ ] **VALIDATE:** Design system renders Tangerine Sky theme
- [ ] **VALIDATE:** All unit tests pass

---

## Phase 2: Domain Foundation & Data Migration
**Target: 7–10 days | Status: ⬜ Not Started**

- [ ] `backend/apps/operations/models.py` — Dog, Entity, HealthRecord, Vaccination, DogPhoto
- [ ] `backend/apps/operations/schemas.py` — Dog/vaccine Pydantic schemas
- [ ] `backend/apps/operations/routers/dogs.py` — Dog CRUD with filters/search
- [ ] `backend/apps/operations/routers/health.py` — Health & vaccine endpoints
- [ ] `backend/apps/operations/services/importers.py` — CSV import engine
- [ ] `backend/apps/operations/services/vaccine.py` — Vaccine due date calculator
- [ ] `backend/apps/operations/services/alerts.py` — Alert card data providers
- [ ] `backend/apps/operations/admin.py` — Django admin
- [ ] `backend/apps/operations/tests/test_dogs.py` — Dog CRUD tests
- [ ] `backend/apps/operations/tests/test_importers.py` — Import tests
- [ ] `backend/apps/operations/tests/factories.py` — Test factories
- [ ] `frontend/hooks/use-dogs.ts` — Dog data hooks
- [ ] `frontend/components/dogs/dog-table.tsx` — Master list table
- [ ] `frontend/components/dogs/dog-card.tsx` — Dog card (mobile)
- [ ] `frontend/components/dogs/dog-filters.tsx` — Filter bar
- [ ] `frontend/components/dogs/alert-cards.tsx` — Alert cards strip
- [ ] `frontend/components/dogs/chip-search.tsx` — Microchip search
- [ ] `frontend/app/(protected)/dogs/page.tsx` — Master list page
- [ ] `frontend/app/(protected)/dogs/[id]/page.tsx` — Dog profile (7 tabs)
- [ ] **VALIDATE:** 483 dogs import, 0 FK violations
- [ ] **VALIDATE:** Master list loads <2s
- [ ] **VALIDATE:** Partial chip search works
- [ ] **VALIDATE:** Dog profile shows all 7 tabs
- [ ] **VALIDATE:** Entity scoping enforced

---

## Phase 3: Ground Operations & Mobile PWA
**Target: 10–14 days | Status: ⬜ Not Started**

- [ ] `backend/apps/operations/models.py` (extend) — 7 ground log models
- [ ] `backend/apps/operations/schemas.py` (extend) — Log Pydantic schemas
- [ ] `backend/apps/operations/routers/logs.py` — 7 log type endpoints
- [ ] `backend/apps/operations/services/draminski.py` — DOD2 interpreter
- [ ] `backend/apps/operations/routers/stream.py` — SSE alert endpoint
- [ ] `backend/apps/operations/services/alerts.py` (extend) — SSE event generators
- [ ] `backend/apps/operations/tasks.py` — Celery tasks (closure rebuild, alerts)
- [ ] `backend/apps/operations/tests/test_logs.py` — Log tests
- [ ] `backend/apps/operations/tests/test_draminski.py` — Draminski tests
- [ ] `frontend/app/ground/layout.tsx` — Ground staff layout
- [ ] `frontend/app/ground/page.tsx` — Ground staff home
- [ ] `frontend/app/ground/log/[type]/page.tsx` — 7 log type forms
- [ ] `frontend/components/ground/numpad.tsx` — Numpad input
- [ ] `frontend/components/ground/draminski-chart.tsx` — Trend chart
- [ ] `frontend/components/ground/log-form.tsx` — Base log form
- [ ] `frontend/components/ground/camera-scan.tsx` — Camera scanner
- [ ] `frontend/lib/offline-queue.ts` — IndexedDB offline queue
- [ ] `frontend/lib/pwa/sw.ts` — Service worker
- [ ] `frontend/lib/pwa/register.ts` — SW registration
- [ ] `frontend/hooks/use-sse.ts` — SSE hook
- [ ] `frontend/hooks/use-offline-queue.ts` — Offline queue hook
- [ ] **VALIDATE:** All 7 log types persist
- [ ] **VALIDATE:** Draminski interpreter correct
- [ ] **VALIDATE:** SSE <500ms delivery
- [ ] **VALIDATE:** Offline queue syncs on reconnect
- [ ] **VALIDATE:** PWA installs, Lighthouse ≥90

---

## Phase 4: Breeding & Genetics Engine
**Target: 7–10 days | Status: ⬜ Not Started**

- [ ] `backend/apps/breeding/models.py` — BreedingRecord, Litter, Puppy, DogClosure
- [ ] `backend/apps/breeding/schemas.py` — Mate check/breeding schemas
- [ ] `backend/apps/breeding/routers/mating.py` — Mate checker endpoint
- [ ] `backend/apps/breeding/routers/litters.py` — Litter CRUD
- [ ] `backend/apps/breeding/services/coi.py` — COI calculator (closure table)
- [ ] `backend/apps/breeding/services/saturation.py` — Farm saturation
- [ ] `backend/apps/breeding/tasks.py` — Celery closure rebuild
- [ ] `backend/apps/breeding/admin.py` — Django admin
- [ ] `backend/apps/breeding/tests/test_coi.py` — COI tests
- [ ] `backend/apps/breeding/tests/test_saturation.py` — Saturation tests
- [ ] `backend/apps/breeding/tests/factories.py` — Test factories
- [ ] `frontend/app/(protected)/breeding/mate-checker/page.tsx` — Mate checker UI
- [ ] `frontend/app/(protected)/breeding/page.tsx` — Breeding records list
- [ ] `frontend/components/breeding/coi-gauge.tsx` — COI gauge
- [ ] `frontend/components/breeding/saturation-bar.tsx` — Saturation bar
- [ ] `frontend/components/breeding/mate-check-form.tsx` — Mate check form
- [ ] **VALIDATE:** COI matches manual calculation
- [ ] **VALIDATE:** COI <500ms p95
- [ ] **VALIDATE:** Farm saturation entity-scoped
- [ ] **VALIDATE:** Override audit logged

---

## Phase 5: Sales Agreements & AVS Tracking
**Target: 10–12 days | Status: ⬜ Not Started**

- [ ] `backend/apps/sales/models.py` — SalesAgreement, AVSTransfer, Signature, TCTemplate
- [ ] `backend/apps/sales/schemas.py` — Agreement Pydantic schemas
- [ ] `backend/apps/sales/routers/agreements.py` — Agreement CRUD + sign + send
- [ ] `backend/apps/sales/routers/avs.py` — AVS tracking endpoints
- [ ] `backend/apps/sales/services/agreement.py` — State machine, GST extraction
- [ ] `backend/apps/sales/services/pdf.py` — Gotenberg PDF generation
- [ ] `backend/apps/sales/services/avs.py` — AVS link gen, state tracking
- [ ] `backend/apps/sales/tasks.py` — Celery: PDF gen, AVS reminder
- [ ] `backend/apps/sales/admin.py` — Django admin
- [ ] `backend/apps/sales/tests/test_agreements.py` — Agreement tests
- [ ] `backend/apps/sales/tests/test_avs.py` — AVS tests
- [ ] `frontend/app/(protected)/sales/page.tsx` — Agreements list
- [ ] `frontend/app/(protected)/sales/wizard/page.tsx` — 5-step wizard
- [ ] `frontend/components/sales/wizard-steps.tsx` — Step components
- [ ] `frontend/components/sales/agreement-preview.tsx` — Preview panel
- [ ] `frontend/components/ui/signature-pad.tsx` — Signature pad
- [ ] **VALIDATE:** B2C/B2B/Rehoming flows complete
- [ ] **VALIDATE:** PDF hash tamper-evident
- [ ] **VALIDATE:** AVS 72h reminder fires
- [ ] **VALIDATE:** GST exact (109→9.00, Thomson=0)

---

## Phase 6: Compliance & NParks Reporting
**Target: 7–10 days | Status: ⬜ Not Started**

- [ ] `backend/apps/compliance/models.py` — NParksSubmission, GSTLedger, PDPAConsentLog
- [ ] `backend/apps/compliance/schemas.py` — Compliance schemas
- [ ] `backend/apps/compliance/routers/nparks.py` — NParks gen/submit/lock
- [ ] `backend/apps/compliance/routers/gst.py` — GST summary/export
- [ ] `backend/apps/compliance/services/nparks.py` — 5-doc Excel generator
- [ ] `backend/apps/compliance/services/gst.py` — IRAS GST engine
- [ ] `backend/apps/compliance/services/pdpa.py` — PDPA hard filter
- [ ] `backend/apps/compliance/tasks.py` — Celery: monthly gen, lock
- [ ] `backend/apps/compliance/admin.py` — Django admin
- [ ] `backend/apps/compliance/tests/test_nparks.py` — NParks tests
- [ ] `backend/apps/compliance/tests/test_gst.py` — GST tests
- [ ] `backend/apps/compliance/tests/test_pdpa.py` — PDPA tests
- [ ] `frontend/app/(protected)/compliance/page.tsx` — NParks page
- [ ] `frontend/app/(protected)/compliance/settings/page.tsx` — T&C settings
- [ ] **VALIDATE:** Excel matches NParks template
- [ ] **VALIDATE:** Zero AI imports in compliance/ (grep verified)
- [ ] **VALIDATE:** Month lock prevents edits
- [ ] **VALIDATE:** PDPA blocks opted-out at query level

---

## Phase 7: Customer DB & Marketing Blast
**Target: 7–10 days | Status: ⬜ Not Started**

- [ ] `backend/apps/customers/models.py` — Customer, CommunicationLog, Segment
- [ ] `backend/apps/customers/schemas.py` — Customer/blast schemas
- [ ] `backend/apps/customers/routers/customers.py` — Customer CRUD + blast
- [ ] `backend/apps/customers/services/segmentation.py` — Dynamic Q-object filters
- [ ] `backend/apps/customers/services/blast.py` — Resend/WA dispatch
- [ ] `backend/apps/customers/services/comms_router.py` — WA fallback to email
- [ ] `backend/apps/customers/tasks.py` — Celery fan-out
- [ ] `backend/apps/customers/admin.py` — Django admin
- [ ] `backend/apps/customers/tests/test_segmentation.py` — Segmentation tests
- [ ] `backend/apps/customers/tests/test_blast.py` — Blast tests
- [ ] `frontend/app/(protected)/customers/page.tsx` — Customer DB + blast
- [ ] `frontend/hooks/use-customers.ts` — Customer data hooks
- [ ] **VALIDATE:** Blast excludes PDPA=false
- [ ] **VALIDATE:** Progress bar live via SSE
- [ ] **VALIDATE:** Comms logged per customer

---

## Phase 8: Dashboard & Finance Exports
**Target: 7–10 days | Status: ⬜ Not Started**

- [ ] `backend/apps/finance/models.py` — Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot
- [ ] `backend/apps/finance/schemas.py` — Finance schemas
- [ ] `backend/apps/finance/routers/reports.py` — Finance endpoints
- [ ] `backend/apps/finance/services/pnl.py` — P&L calculator
- [ ] `backend/apps/finance/services/gst_report.py` — GST report generator
- [ ] `backend/apps/finance/admin.py` — Django admin
- [ ] `backend/apps/finance/tests/test_pnl.py` — P&L tests
- [ ] `backend/apps/finance/tests/test_gst.py` — GST report tests
- [ ] `backend/apps/finance/tests/factories.py` — Test factories
- [ ] `frontend/app/(protected)/dashboard/page.tsx` — Role-aware dashboard
- [ ] `frontend/app/(protected)/finance/page.tsx` — Finance page
- [ ] `frontend/components/dashboard/nparks-countdown.tsx` — Countdown card
- [ ] `frontend/components/dashboard/alert-feed.tsx` — Activity feed
- [ ] `frontend/components/dashboard/revenue-chart.tsx` — Revenue chart
- [ ] **VALIDATE:** Dashboard <2s load
- [ ] **VALIDATE:** Role-specific views correct
- [ ] **VALIDATE:** P&L balances, intercompany nets zero

---

## Phase 9: Observability & Production Readiness
**Target: 5–7 days | Status: ⬜ Not Started**

- [ ] `backend/config/otel.py` — OpenTelemetry setup
- [ ] `frontend/instrumentation.ts` — Next.js OTel
- [ ] `tests/load/k6.js` — Load test scripts
- [ ] `docs/RUNBOOK.md` — Operations runbook
- [ ] `docs/SECURITY.md` — Security documentation
- [ ] `docs/DEPLOYMENT.md` — Deployment guide
- [ ] `docs/API.md` — API documentation
- [ ] `scripts/backup.sh` — WAL-G backup script
- [ ] `nginx/nginx.conf` — Nginx reverse proxy
- [ ] **VALIDATE:** 0 critical/high CVEs
- [ ] **VALIDATE:** OTel traces flow to Grafana
- [ ] **VALIDATE:** k6 load test passes thresholds
- [ ] **VALIDATE:** WAL-G PITR restore verified
- [ ] **VALIDATE:** Runbooks complete
- [ ] **SIGN-OFF:** Architecture Lead
- [ ] **SIGN-OFF:** Compliance Officer
- [ ] **SIGN-OFF:** DevOps Lead
- [ ] **SIGN-OFF:** Product Owner

---

**Total Files: ~178 | Estimated Effort: ~70–95 days**
**Verified Stack: npm 377 pkgs (0 vulns) + pip 71 pkgs (all resolved) | April 2026**
