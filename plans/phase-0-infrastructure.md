# Phase 0: Infrastructure & Foundation Scaffold — Sub-Plan

**Target:** 3–5 days | **Dependencies:** None | **Status:** ⬜ Not Started

**Success Criteria:** `docker compose up` boots all 11 services healthy. CI green on push. Base routes return 200.

---

## Execution Order

Files must be created in this order due to dependencies:

```
Step 1: Config files (no code deps)
  .gitignore → .env.example → README.md

Step 2: Docker infrastructure
  docker-compose.yml → docker-compose.dev.yml
  backend/Dockerfile.django → frontend/Dockerfile.nextjs

Step 3: Backend skeleton
  backend/manage.py → backend/config/__init__.py
  → backend/config/settings/base.py
  → backend/config/settings/development.py
  → backend/config/settings/production.py
  → backend/config/urls.py → backend/config/wsgi.py
  → backend/config/asgi.py → backend/config/celery.py
  → backend/api.py

Step 4: Backend dependencies
  backend/requirements/base.txt → backend/requirements/dev.txt

Step 5: Frontend skeleton
  frontend/package.json → frontend/tsconfig.json
  → frontend/next.config.ts → frontend/tailwind.config.ts
  → frontend/postcss.config.ts → frontend/vitest.config.ts
  → frontend/playwright.config.ts
  → frontend/app/globals.css → frontend/app/layout.tsx
  → frontend/app/page.tsx → frontend/public/manifest.json
  → frontend/public/favicon.ico

Step 6: CI/CD
  .github/workflows/ci.yml

Step 7: Scripts
  scripts/seed.sh
```

---

## File-by-File Specifications

### Step 1: Config Files

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `.gitignore` | Git ignore rules | `.env`, `node_modules/`, `__pycache__/`, `.next/`, `venv/`, `*.pyc`, `.pytest_cache/`, `coverage/`, `staticfiles/`, `media/`, `.DS_Store` | ☐ |
| `.env.example` | Environment template | Wellfond-specific vars (NOT CHA YUAN): `DB_PASSWORD`, `POSTGRES_DB=wellfond`, `POSTGRES_USER=wellfond_app`, `DJANGO_SECRET_KEY`, `REDIS_SESSIONS_URL`, `REDIS_BROKER_URL`, `REDIS_CACHE_URL`, `GOTENBERG_URL`, `BACKEND_INTERNAL_URL`, `NEXT_PUBLIC_SENTRY_DSN` (optional) | ☐ |
| `README.md` | Project readme | Quick start (`docker compose up`), architecture diagram, dev setup, deployment, stack versions | ☐ |

### Step 2: Docker Infrastructure

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `docker-compose.yml` | Production compose (11 services) | **postgres**: `postgres:17-alpine`, `wal_level=replica`, `shared_buffers=256MB`, `effective_cache_size=768MB`, healthcheck `pg_isready`. **pgbouncer**: `edoburu/pgbouncer:1.23.0`, `POOL_MODE=transaction`, `MAX_CLIENT_CONN=1000`. **redis_sessions/broker/cache**: `redis:7.4-alpine`, isolated memory limits (128/256/256mb). **django**: builds from `Dockerfile.django`, env vars for DB/Redis/Gotenberg. **celery_worker**: same image, `celery -A config worker -l info -Q high,default,low,dlq`. **celery_beat**: same image, `celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`. **gotenberg**: `gotenberg/gotenberg:8`, healthcheck `/health`. **nextjs**: builds from `Dockerfile.nextjs`, `BACKEND_INTERNAL_URL=http://django:8000`, port 3000. **flower**: `mher/flower:2.0`, port 5555. Networks: `backend_net`, `frontend_net`. Volume: `pg_data`. | ☐ |
| `docker-compose.dev.yml` | Dev overrides | Mount `./backend` and `./frontend` for hot reload. Expose ports: 5432 (PG), 6432 (PgBouncer), 6379 (Redis), 8000 (Django), 3000 (Next.js), 5555 (Flower). `DEBUG=True`. | ☐ |
| `backend/Dockerfile.django` | Multi-stage Django build | **Builder stage**: `python:3.13-slim`, install uv, `uv pip install -r requirements/base.txt`. **Runtime stage**: `python:3.13-slim`, non-root user, copy installed packages, `gunicorn` + `uvicorn` entrypoint. **Trivy scan stage**: `aquasec/trivy` for SBOM. | ☐ |
| `frontend/Dockerfile.nextjs` | Multi-stage Next.js build | **Deps stage**: `node:22-alpine`, `pnpm install`. **Build stage**: `pnpm build`. **Runtime stage**: `node:22-alpine`, standalone output, non-root user, PWA assets precached. Env: `BACKEND_INTERNAL_URL`, `NEXT_PUBLIC_SENTRY_DSN`. | ☐ |

### Step 3: Backend Skeleton

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `backend/manage.py` | Django management | Standard manage.py. `DJANGO_SETTINGS_MODULE=config.settings.development` | ☐ |
| `backend/config/__init__.py` | Package init | Empty or import celery app | ☐ |
| `backend/config/settings/__init__.py` | Package init | Empty | ☐ |
| `backend/config/settings/base.py` | Core Django settings | `INSTALLED_APPS`: core, operations, breeding, sales, compliance, customers, finance, ai_sandbox + django defaults. `MIDDLEWARE`: CSP, CORS, common, auth, session, csrf, clickjacking, idempotency. `DATABASES`: PG via PgBouncer (`CONN_MAX_AGE=0`). `CACHES`: 3 Redis instances (default, sessions, idempotency). `SESSION_ENGINE=django.contrib.sessions.backends.cache`. `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`. `SECURE_CSP_*` directives. `LOGGING`: JSON structured. `TIME_ZONE='Asia/Singapore'`. `DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'`. | ☐ |
| `backend/config/settings/development.py` | Dev settings | `DEBUG=True`. Import base. Debug toolbar. Local DB (direct, not PgBouncer). Relaxed CSP. | ☐ |
| `backend/config/settings/production.py` | Prod settings | `DEBUG=False`. Import base. Strict CSP. PgBouncer host. OTel exporters. HTTPS-only cookies. HSTS. | ☐ |
| `backend/config/urls.py` | Root URL conf | `path('api/v1/', api.urls)`. `path('admin/', admin.site.urls)`. `path('health/', health_check)`. `path('api/v1/openapi.json', OpenAPIschema)`. | ☐ |
| `backend/config/wsgi.py` | WSGI config | Standard Django WSGI. | ☐ |
| `backend/config/asgi.py` | ASGI config | Django ASGI application for async/SSE support. | ☐ |
| `backend/config/celery.py` | Celery app config | `app = Celery('wellfond')`. Auto-discovers tasks from all apps. Beat schedule: AVS 3-day reminder (daily 9am SGT). Queue routing: compliance→high, sales→default, breeding→low, marketing→default. | ☐ |
| `backend/api.py` | NinjaAPI instance | `NinjaAPI(title="Wellfond BMS", version="1.0.0", csrf=True, urls_namespace='api')`. Global exception handlers: 500→JSON, 422→validation errors, 401→unauthorized. Router registry pattern. OpenAPI at `/api/v1/openapi.json`. | ☐ |

### Step 4: Backend Dependencies

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `backend/requirements/base.txt` | Production deps | `Django==6.0.4`, `django-ninja==1.6.2`, `pydantic==2.12.5`, `psycopg2-binary==2.9.10`, `redis==6.4.0`, `hiredis==3.3.0`, `django-cors-headers==4.9.0`, `djangorestframework-simplejwt==5.5.1`, `PyJWT==2.12.1`, `stripe==14.4.1`, `python-decouple==3.8`, `pytz==2025.2`, `python-dateutil==2.9.0.post0`, `Pillow==12.2.0`, `asgiref==3.11.0`, `channels==4.3.2`, `channels-redis==4.3.0`, `django-ratelimit==4.1.0`, `celery>=5.4`, `django-celery-beat`, `openpyxl`, `httpx`, `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-django`, `opentelemetry-instrumentation-celery`, `opentelemetry-instrumentation-psycopg2`, `opentelemetry-exporter-prometheus`, `python-json-logger` | ☐ |
| `backend/requirements/dev.txt` | Dev deps | `-r base.txt` + `pytest==9.0.3`, `pytest-django==4.12.0`, `pytest-asyncio==1.3.0`, `pytest-cov==7.1.0`, `pytest-xdist==3.8.0`, `factory-boy==3.3.3`, `faker==40.5.1`, `black==26.3.1`, `isort==5.12.0`, `flake8==6.1.0`, `mypy==1.20.0`, `django-stubs==6.0.2`, `ipython==9.10.0`, `django-extensions==4.1`, `django-debug-toolbar==6.3.0`, `mkdocs==1.6.1`, `mkdocs-material==9.6.19` | ☐ |

### Step 5: Frontend Skeleton

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `frontend/package.json` | Dependencies (pinned) | All 37 deps with exact versions (already created and verified) | ☐ |
| `frontend/tsconfig.json` | TypeScript config | `strict: true`, `paths: { "@/*": ["./*"] }`, target ES2022, module ESNext | ☐ |
| `frontend/next.config.ts` | Next.js config | `output: 'standalone'`, `reactStrictMode: true`, image domains for R2, headers for PWA | ☐ |
| `frontend/tailwind.config.ts` | Tailwind v4 config | Tangerine Sky palette: `#DDEEFF` (bg), `#0D2030` (text), `#F97316` (primary), `#0891B2` (secondary), `#4EAD72` (success), `#D4920A` (warning), `#D94040` (error), `#E8F4FF` (sidebar), `#C0D8EE` (border), `#4A7A94` (muted). Font: Figtree | ☐ |
| `frontend/postcss.config.ts` | PostCSS config | `@tailwindcss/postcss` plugin | ☐ |
| `frontend/vitest.config.ts` | Vitest config | React plugin, jsdom environment, setup files, coverage v8 | ☐ |
| `frontend/playwright.config.ts` | Playwright config | Chromium, baseURL localhost:3000, screenshot on failure | ☐ |
| `frontend/app/globals.css` | Global styles | Tailwind v4 `@import "tailwindcss"`. CSS custom properties for theme. Figtree font import | ☐ |
| `frontend/app/layout.tsx` | Root layout | Figtree font. Metadata: title, description, viewport, theme-color. Manifest link. Strict mode. Body with `className="bg-[#DDEEFF] text-[#0D2030] font-figtree"` | ☐ |
| `frontend/app/page.tsx` | Landing page | Redirect to `/dashboard` if authenticated, `/login` if not | ☐ |
| `frontend/public/manifest.json` | PWA manifest | `name: "Wellfond BMS"`, `short_name: "Wellfond"`, `start_url: "/"`, `display: "standalone"`, `theme_color: "#F97316"`, `background_color: "#DDEEFF"`, icons 192/512 | ☐ |
| `frontend/public/favicon.ico` | Favicon | Tangerine paw icon (generate SVG → ICO) | ☐ |

### Step 6: CI/CD

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `.github/workflows/ci.yml` | CI pipeline | **Matrix:** `backend` (lint, typecheck, test), `frontend` (lint, typecheck, test, build), `infra` (docker build, trivy scan). **Backend job:** `pip install -r requirements/dev.txt`, `black --check`, `isort --check`, `flake8`, `mypy`, `pytest --cov=85`. **Frontend job:** `pnpm install`, `pnpm lint`, `pnpm typecheck`, `pnpm test:coverage`, `pnpm build`. **Infra job:** `docker build` both images, `trivy image --severity HIGH,CRITICAL`. Fail on CVE high/critical. No `latest` tags. SBOM generation. Artifact upload. | ☐ |

### Step 7: Scripts

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `scripts/seed.sh` | Fixture data loader | `python manage.py migrate`. `python manage.py createsuperuser` (from env vars). Load entity fixtures (Holdings, Katong, Thomson). | ☐ |

---

## Phase 0 Validation Checklist

### Infrastructure
- [ ] `docker compose up -d` → all 11 containers healthy within 60s
- [ ] `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` → dev mode works
- [ ] `docker exec wellfond-postgres pg_isready` → accepting connections
- [ ] `docker exec wellfond-pgbouncer psql -h 127.0.0.1 -p 5432 -U wellfond_app -d pgbouncer -c 'SHOW POOLS'` → pool active
- [ ] Redis isolation: sessions ≠ broker ≠ cache (verify via `docker exec wellfond-redis-sessions redis-cli DBSIZE`)
- [ ] Gotenberg: `curl http://localhost:3000/health` → 200

### Backend
- [ ] `curl http://localhost:8000/health/` → 200 OK
- [ ] `curl http://localhost:8000/api/v1/openapi.json` → valid OpenAPI schema
- [ ] `python manage.py check` → no errors
- [ ] `python manage.py migrate` → all migrations apply
- [ ] `pip install -r requirements/base.txt` → 24+ packages, no conflicts
- [ ] `pip install -r requirements/dev.txt` → 47+ packages, no conflicts

### Frontend
- [ ] `curl http://localhost:3000` → Next.js renders
- [ ] `npm install` → 377 packages, 0 vulnerabilities
- [ ] `npm run build` → standalone output in `.next/standalone/`
- [ ] `npm run lint` → no errors
- [ ] `npm run typecheck` → no errors

### Network
- [ ] `docker exec wellfond-nextjs curl http://postgres:5432` → connection refused (isolation)
- [ ] `docker exec wellfond-nextjs curl http://django:8000/health/` → 200 (BFF can reach backend)
- [ ] `docker exec wellfond-django curl http://pgbouncer:5432` → connection works

### CI
- [ ] Push to branch → CI pipeline triggers
- [ ] Backend job: lint + typecheck + test → green
- [ ] Frontend job: lint + typecheck + test + build → green
- [ ] Infra job: docker build + trivy → green, 0 critical/high CVEs
