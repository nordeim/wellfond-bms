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
| `docker-compose.dev.yml` | Dev compose (2 services only) | **postgres**: `postgres:17-alpine`, port `5432:5432`. **redis**: `redis:7.4-alpine`, port `6379:6379` (single Redis for all 3 purposes in dev). `DEBUG=True`. Django/Next.js/Celery run natively on localhost. | ☐ |
| `infra/docker/docker-compose.yml` | Infrastructure compose (current) | **postgres**: `postgres:17-trixie`, port `5432`. **redis**: `redis:7.4-alpine`, port `6379`. | ✅ Already running |
| `backend/Dockerfile.django` | Multi-stage Django build | **Builder stage**: `python:3.13-slim`, install uv, `uv pip install -r requirements/base.txt`. **Runtime stage**: `python:3.13-slim`, non-root user, copy installed packages, `gunicorn` + `uvicorn` entrypoint. **Trivy scan stage**: `aquasec/trivy` for SBOM. | ☐ |
| `frontend/Dockerfile.nextjs` | Multi-stage Next.js build | **Deps stage**: `node:22-alpine`, `pnpm install`. **Build stage**: `pnpm build`. **Runtime stage**: `node:22-alpine`, standalone output, non-root user, PWA assets precached. Env: `BACKEND_INTERNAL_URL`, `NEXT_PUBLIC_SENTRY_DSN`. | ☐ |

### Step 3: Backend Skeleton

| File | Purpose | Key Content | Done |
|------|---------|-------------|------|
| `backend/manage.py` | Django management | Standard manage.py. `DJANGO_SETTINGS_MODULE=config.settings.development` | ☐ |
| `backend/config/__init__.py` | Package init | Empty or import celery app | ☐ |
| `backend/config/settings/__init__.py` | Package init | Empty | ☐ |
| `backend/config/settings/base.py` | Core Django settings | `INSTALLED_APPS`: core, operations, breeding, sales, compliance, customers, finance, ai_sandbox + django defaults. `MIDDLEWARE`: CSP, CORS, common, auth, session, csrf, clickjacking, idempotency. `DATABASES`: PG via PgBouncer (`CONN_MAX_AGE=0`). `CACHES`: 3 Redis instances (default, sessions, idempotency). `SESSION_ENGINE=django.contrib.sessions.backends.cache`. `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`. `SECURE_CSP_*` directives. `LOGGING`: JSON structured. `TIME_ZONE='Asia/Singapore'`. `DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'`. | ☐ |
| `backend/config/settings/development.py` | Dev settings | `DEBUG=True`. Import base. **Direct PG connection via `127.0.0.1:5432`** (no PgBouncer). **Single Redis via `127.0.0.1:6379`** (no split instances). `DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'wellfond_db', 'USER': 'wellfond_user', 'PASSWORD': env('DB_PASSWORD'), 'HOST': '127.0.0.1', 'PORT': '5432', 'CONN_MAX_AGE': 0}}`. `CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': 'redis://127.0.0.1:6379/0'}}`. `CELERY_BROKER_URL = 'redis://127.0.0.1:6379/1'`. `SESSION_CACHE_ALIAS = 'default'`. Debug toolbar. Relaxed CSP. | ☐ |
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

## Development Environment Setup (Hybrid: Native + Containerized)

### Architecture
This project uses a **hybrid development environment** where:
- **Containerized**: PostgreSQL 17, Redis 7.4 (via Docker)
- **Native**: Django 6.0, Next.js 16, Celery (run directly on localhost)

### Prerequisites
- Python 3.13+ with `uv` or `pip`
- Node.js 22+ with `pnpm`
- Docker + Docker Compose

### Step-by-Step Dev Setup

#### 1. Start Infrastructure Containers
```bash
# From project root
docker compose -f infra/docker/docker-compose.yml up -d

# Verify
 docker ps
# Should see: wellfond-postgres (5432), wellfond-redis (6379)
```

#### 2. Setup Backend (Native)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run Django development server (native)
python manage.py runserver 127.0.0.1:8000
```

#### 3. Setup Frontend (Native)
```bash
cd frontend

# Install dependencies
npm install  # or pnpm install

# Run Next.js dev server (native)
npm run dev  # Runs on localhost:3000
```

#### 4. Run Celery Worker (Native)
```bash
# In a new terminal, from backend directory
cd backend
source venv/bin/activate

# Run Celery worker
celery -A config worker -l info -Q high,default,low,dlq

# Run Celery beat (scheduler) - in another terminal
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Environment Variables (`.env`)
```
# Database (connects to containerized PG)
DB_PASSWORD=wellfond_dev_password
DATABASE_URL=postgresql://wellfond_user:wellfond_dev_password@127.0.0.1:5432/wellfond_db
DB_NAME=wellfond_db
DB_USER=wellfond_user

# Redis (connects to containerized Redis)
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_SESSIONS_URL=redis://127.0.0.1:6379/1
REDIS_BROKER_URL=redis://127.0.0.1:6379/2

# Django
SECRET_KEY=dev-secret-key-change-in-production-2026-wellfond-singapore
DJANGO_SETTINGS_MODULE=wellfond.settings.development
DEBUG=True

# Frontend BFF proxy (connects to native Django)
BACKEND_INTERNAL_URL=http://127.0.0.1:8000

# Gotenberg (optional for dev - PDF generation)
GOTENBERG_URL=http://localhost:3001  # Or skip for dev

# Testing
TEST_DB_NAME=wellfond_test_db
```

### Port Configuration
| Service | Dev Port | Container/Process | Notes |
|---------|----------|-------------------|-------|
| PostgreSQL | `5432` | Docker container `wellfond-postgres` | Direct connection |
| Redis | `6379` | Docker container `wellfond-redis` | Single instance |
| Django | `8000` | Native `python manage.py runserver` | No container |
| Next.js | `3000` | Native `npm run dev` | No container |
| Celery | N/A | Native `celery worker` | No container |
| Gotenberg | `3001` | Optional Docker or skip | Dev mock available |

### Dev vs Production Differences
| Aspect | Development | Production |
|--------|-------------|------------|
| Database | Direct PG on `:5432` | Via PgBouncer pool |
| Redis | Single instance | 3 split instances (sessions/broker/cache) |
| Django | Native `runserver` | Gunicorn + Uvicorn in container |
| Next.js | Native dev server | Standalone build in container |
| Celery | Native execution | Containerized worker/beat |
| Gotenberg | Optional / mock | Required sidecar |
| PgBouncer | Not used | Required connection pooler |

---

## Phase 0 Validation Checklist

### Development Environment (Hybrid Setup)

#### Infrastructure Containers (Docker)
- [ ] `docker compose -f infra/docker/docker-compose.yml up -d` → postgres + redis containers healthy
- [ ] `docker exec wellfond-postgres pg_isready -U wellfond_user` → accepting connections
- [ ] `docker exec wellfond-redis redis-cli ping` → PONG
- [ ] `psql postgresql://wellfond_user:wellfond_dev_password@127.0.0.1:5432/wellfond_db -c '\dt'` → connects (no tables yet)
- [ ] `redis-cli -h 127.0.0.1 -p 6379 ping` → PONG

#### Backend (Native)
- [ ] `cd backend && python -m venv venv && source venv/bin/activate` → venv created
- [ ] `pip install -r requirements/dev.txt` → 70+ packages, no conflicts
- [ ] `python manage.py check` → System check identified no issues
- [ ] `python manage.py migrate` → All migrations applied
- [ ] `python manage.py runserver 127.0.0.1:8000` → Development server running
- [ ] `curl http://127.0.0.1:8000/health/` → 200 OK
- [ ] `curl http://127.0.0.1:8000/api/v1/openapi.json` → valid OpenAPI schema

#### Frontend (Native)
- [ ] `cd frontend && npm install` → 377 packages, 0 vulnerabilities
- [ ] `npm run dev` → Next.js dev server running on localhost:3000
- [ ] `curl http://localhost:3000` → Next.js renders
- [ ] `npm run lint` → no errors
- [ ] `npm run typecheck` → no errors

#### Celery (Native)
- [ ] `celery -A config worker -l info` → Worker starts, connects to Redis at 127.0.0.1:6379
- [ ] `celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler` → Beat starts

#### BFF Proxy (Native → Native)
- [ ] `curl http://localhost:3000/api/proxy/health/` → proxies to Django, returns 200
- [ ] Frontend login form → submits to `/api/proxy/auth/login` → Django receives, sets cookie
- [ ] Cookie visible in DevTools → HttpOnly, Secure (if HTTPS), SameSite=Lax

#### Environment Verification
- [ ] `grep DB_PASSWORD .env` → matches `docker-compose.yml`
- [ ] `grep DATABASE_URL .env` → points to `127.0.0.1:5432`
- [ ] `grep BACKEND_INTERNAL_URL .env` → `http://127.0.0.1:8000`
- [ ] Django settings → `DATABASES['default']['HOST']` = `'127.0.0.1'`
- [ ] Django settings → `CELERY_BROKER_URL` = `'redis://127.0.0.1:6379/1'`

### Production Environment (Full Containerization)
**Note:** Production uses 11 containers including PgBouncer, Gotenberg, and containerized Django/Next.js.
See `docker-compose.yml` (production) for details. Dev environment skips these.

- [ ] Production: `docker compose up -d` → all 11 containers healthy within 60s
- [ ] Production: `docker exec wellfond-pgbouncer psql -h 127.0.0.1 -p 5432 -U wellfond_app -d pgbouncer -c 'SHOW POOLS'` → pool active
- [ ] Production: Redis isolation: sessions ≠ broker ≠ cache (3 separate Redis instances)
- [ ] Production: Gotenberg: `curl http://localhost:3000/health` → 200

### CI Pipeline
- [ ] Push to branch → CI pipeline triggers
- [ ] Backend job: lint + typecheck + test → green
- [ ] Frontend job: lint + typecheck + test + build → green
- [ ] Infra job: docker build + trivy → green, 0 critical/high CVEs
