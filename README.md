# Wellfond BMS — Enterprise Breeding Management System

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/wellfond/bms)
[![Django](https://img.shields.io/badge/Django-6.0.4-green.svg)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.2.4-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/wellfond/bms/actions)

> **Singapore AVS-compliant dog breeding operations platform** with real-time mobile PWA, genetics engine, and deterministic compliance reporting.

[📖 Documentation](docs/) &nbsp;|&nbsp; [🔌 API Reference](docs/API.md) &nbsp;|&nbsp; [🚀 Deployment Guide](docs/DEPLOYMENT.md) &nbsp;|&nbsp; [🐛 Report Issue](../../issues)

---

## 📋 Overview

**Wellfond BMS** is an enterprise-grade breeding management system designed for Singapore's AVS-licensed dog breeding operations. Built with security-first architecture and compliance determinism at its core, it supports multi-entity operations (Holdings, Katong, Thomson) with strict data isolation.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **BFF Security** | HttpOnly cookies, zero JWT exposure, hardened proxy with path allowlisting |
| 📱 **Mobile-First PWA** | Offline queue with background sync, works in poor connectivity areas |
| 🧬 **Genetics Engine** | COI calculation, farm saturation analysis, dual-sire pedigree tracking |
| 📊 **Real-Time Alerts** | Server-Sent Events (SSE) for nursing flags, heat cycles, vaccine due |
| 📄 **Sales Agreements** | B2C/B2B/Rehoming wizards with e-signatures, GST 9/109, AVS tracking |
| 📈 **NParks Compliance** | 5-document Excel generation with immutable month-lock |
| 🔒 **PDPA Enforcement** | Hard consent filtering at query level, immutable audit trails |
| 🧪 **Zero AI in Compliance** | Pure Python/SQL for regulatory paths — no LLM imports |

---

## 🏗️ Architecture

### Tech Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Backend** | Django + Django Ninja | 6.0.4 / 1.6.2 | API with auto OpenAPI, CSP middleware, async SSE |
| **Frontend** | Next.js (App Router) | 16.2.4 | BFF proxy, server components, PWA |
| **Database** | PostgreSQL | 17 | `wal_level=replica`, PgBouncer pooling |
| **Cache/Broker** | Redis | 7.4 | Sessions, task queue, cache (3 instances in prod) |
| **Task Queue** | Celery | 5.4 | Native `@shared_task`, split queues (high/default/low/dlq) |
| **PDF** | Gotenberg | 8 | Chromium-based PDF generation for legal agreements |
| **Real-Time** | SSE | — | Async Django Ninja generators, auto-reconnect |
| **Styling** | Tailwind CSS | 4.2.4 | Tangerine Sky design system |
| **Testing** | pytest + Vitest | — | ≥85% coverage target |

### Architectural Principles

1. **BFF Security** — Next.js `/api/proxy/` forwards HttpOnly cookies. Server-only `BACKEND_INTERNAL_URL`. Zero token leakage.
2. **Compliance Determinism** — NParks/GST/AVS/PDPA paths are pure Python/SQL. Zero AI imports. Immutable audit trails.
3. **AI Sandbox** — Claude OCR isolated in `backend/apps/ai_sandbox/`. Human-in-the-loop mandatory.
4. **Entity Scoping** — All queries filtered by `entity_id`. Enforced at queryset level (RLS dropped for PgBouncer compatibility).
5. **Idempotent Sync** — UUIDv4 keys on all POST requests. Redis-backed idempotency store (24h TTL).
6. **Async Closure** — Pedigree closure table rebuilt by Celery task (no DB triggers). Incremental for single-dog, full for bulk.

---

## 📁 File Hierarchy

```
wellfond-bms/
├── 📂 backend/                    # Django 6.0 backend
│   ├── 📂 apps/
│   │   ├── 📂 core/              # Auth, users, permissions, audit
│   │   │   ├── models.py         # User, Entity, AuditLog
│   │   │   ├── auth.py           # HttpOnly cookie authentication
│   │   │   ├── permissions.py    # Role decorators, entity scoping
│   │   │   └── middleware.py     # Idempotency, entity middleware
│   │   ├── 📂 operations/       # Dogs, health, ground logs, PWA sync
│   │   │   ├── models.py         # Dog, HealthRecord, Vaccination
│   │   │   ├── services/
│   │   │   │   ├── draminski.py  # DOD2 interpreter for heat detection
│   │   │   │   ├── vaccine.py    # Due date calculation
│   │   │   │   └── importers.py  # CSV dog/litter import
│   │   │   └── routers/
│   │   │       ├── logs.py       # 7 ground log types
│   │   │       └── stream.py     # SSE alert endpoint
│   │   ├── 📂 breeding/          # Mating, litters, COI, saturation
│   │   │   ├── models.py         # BreedingRecord, Litter, DogClosure
│   │   │   └── services/
│   │   │       ├── coi.py        # Wright's formula, closure traversal
│   │   │       └── saturation.py # Farm saturation calculation
│   │   ├── 📂 sales/             # Agreements, AVS, e-signatures
│   │   │   ├── models.py         # SalesAgreement, AVSTransfer
│   │   │   └── services/
│   │   │       ├── pdf.py        # Gotenberg PDF generation
│   │   │       └── avs.py        # AVS link generation, reminders
│   │   ├── 📂 compliance/         # NParks, GST, PDPA (ZERO AI)
│   │   │   ├── services/
│   │   │   │   ├── nparks.py     # 5-doc Excel generation
│   │   │   │   ├── gst.py        # IRAS 9/109 calculation
│   │   │   │   └── pdpa.py       # Hard consent filter
│   │   │   └── routers/
│   │   │       ├── nparks.py     # Generate/submit/lock endpoints
│   │   │       └── gst.py        # GST export endpoints
│   │   ├── 📂 customers/        # CRM, segments, marketing blast
│   │   │   └── services/
│   │   │       ├── segmentation.py
│   │   │       ├── blast.py      # Resend/WA dispatch
│   │   │       └── template_manager.py  # WA approval cache
│   │   └── 📂 finance/          # P&L, GST reports, intercompany
│   ├── 📂 config/               # Django configuration
│   │   ├── settings/
│   │   │   ├── base.py          # Core settings
│   │   │   ├── development.py   # Dev settings (direct PG)
│   │   │   └── production.py    # Prod settings (PgBouncer)
│   │   ├── urls.py              # Root URL conf
│   │   ├── asgi.py              # ASGI for async SSE
│   │   └── celery.py            # Celery app config
│   └── 📄 requirements/
│       ├── base.txt             # Production dependencies
│       └── dev.txt              # Development dependencies
│
├── 📂 frontend/                 # Next.js 16 frontend
│   ├── 📂 app/
│   │   ├── 📂 (auth)/           # Login pages
│   │   ├── 📂 (protected)/      # Protected dashboard pages
│   │   │   ├── dogs/           # Master list, dog profile
│   │   │   ├── breeding/       # Mate checker, litters
│   │   │   ├── sales/          # Agreements, wizard
│   │   │   ├── compliance/     # NParks reporting
│   │   │   ├── customers/      # CRM, blast
│   │   │   ├── finance/        # P&L, GST
│   │   │   └── dashboard/      # Role-aware dashboard
│   │   ├── 📂 ground/          # Mobile PWA (no sidebar)
│   │   │   └── log/[type]/     # 7 log type forms
│   │   └── 📂 api/proxy/        # BFF proxy routes
│   ├── 📂 components/
│   │   ├── 📂 ui/              # Design system primitives
│   │   ├── 📂 layout/          # Sidebar, topbar, bottom-nav
│   │   ├── 📂 dogs/            # Dog table, filters, alerts
│   │   ├── 📂 breeding/          # COI gauge, saturation bar
│   │   ├── 📂 sales/           # Wizard steps, signature pad
│   │   ├── 📂 ground/          # Numpad, Draminski chart, camera
│   │   └── 📂 dashboard/         # Alert feed, revenue chart
│   ├── 📂 lib/
│   │   ├── api.ts              # Unified fetch wrapper with idempotency
│   │   ├── auth.ts             # Session helpers
│   │   └── offline-queue.ts    # IndexedDB offline queue
│   ├── 📂 hooks/
│   │   ├── use-dogs.ts         # Dog data hooks
│   │   ├── use-sse.ts          # SSE hook
│   │   └── use-offline-queue.ts
│   └── 📂 public/
│       └── manifest.json       # PWA manifest
│
├── 📂 infra/                    # Infrastructure
│   └── 📂 docker/
│       └── docker-compose.yml   # PG + Redis only (dev)
│
├── 📂 docs/                     # Documentation
│   ├── RUNBOOK.md              # Operations guide
│   ├── SECURITY.md             # Security documentation
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── API.md                  # API documentation
│
├── 📂 plans/                    # Implementation plans
│   ├── phase-0-infrastructure.md
│   ├── phase-1-auth-bff-rbac.md
│   ├── phase-2-domain-foundation.md
│   ├── phase-3-ground-operations.md
│   ├── phase-4-breeding-genetics.md
│   ├── phase-5-sales-avs.md
│   ├── phase-6-compliance-nparks.md
│   ├── phase-7-customers-marketing.md
│   ├── phase-8-dashboard-finance.md
│   └── phase-9-observability-production.md
│
├── 📂 scripts/                  # Utility scripts
│   └── seed.sh                  # Fixture data loader
│
├── 📂 tests/                    # End-to-end tests
│   └── load/
│       └── k6.js                # Load testing scripts
│
├── 📄 docker-compose.yml          # Production compose (11 services)
├── 📄 docker-compose.dev.yml     # Dev compose (2 services)
├── 📄 IMPLEMENTATION_PLAN.md    # Master implementation plan
├── 📄 TODO.md                     # Master TODO checklist
└── 📄 AGENTS.md                 # AI agent instructions
```

---

## 🔄 User Interaction Flow

```mermaid
flowchart TB
    subgraph "📱 Ground Staff"
        A[Submit Log<br/>PWA Offline Queue]
    end

    subgraph "💼 Sales Staff"
        B[Create Agreement<br/>5-Step Wizard]
    end

    subgraph "🔬 Vet / Admin"
        C[Review Dogs<br/>Dog Profile 7 Tabs]
    end

    subgraph "📊 Management"
        D[Dashboard<br/>Real-time Alerts]
    end

    subgraph "⚡ BFF Proxy"
        E[Next.js API Routes<br/>/api/proxy/*]
        F[Path Allowlist<br/>Header Sanitization]
    end

    subgraph "🛡️ Django API"
        G[Django Ninja<br/>Async Endpoints]
        H[Entity Scoping<br/>PDPA Filtering]
    end

    subgraph "📦 Data Layer"
        I[(PostgreSQL 17)]
        J[Redis Cache]
    end

    subgraph "⚙️ Background Tasks"
        K[Celery Workers]
        L[PDF Generation]
        M[Email/WhatsApp]
    end

    subgraph "🔔 Real-Time"
        N[SSE Stream]
        O[Alert Delivery<br/><500ms]
    end

    A -->|"POST /api/proxy/operations/logs"| E
    B -->|"POST /api/proxy/sales/agreements"| E
    C -->|"GET /api/proxy/dogs/{id}"| E
    D -->|"GET /api/proxy/dashboard/metrics"| E

    E -->|"Forward with Cookies"| F
    F -->|"Validate & Route"| G

    G -->|"Query / Write"| I
    G -->|"Cache"| J
    G -->|"Queue Tasks"| K

    K -->|"Generate"| L
    K -->|"Send"| M

    G -->|"Publish Events"| N
    N -->|"Stream"| O
    O -->|"Update UI"| D
    O -->|"Notify"| A

    style A fill:#DDEEFF,stroke:#0D2030
    style D fill:#FFF0E6,stroke:#F97316
    style G fill:#E8F4FF,stroke:#0891B2
    style I fill:#E8F4FF,stroke:#0891B2
```

---

## 🔄 Application Logic Flow

```mermaid
sequenceDiagram
    actor U as Ground Staff
    participant P as BFF Proxy
    participant A as Django API
    participant R as Redis
    participant C as Celery
    participant D as PostgreSQL
    participant S as SSE Stream

    U->>P: POST /api/proxy/operations/logs/in-heat<br/>with X-Idempotency-Key

    P->>A: Forward with HttpOnly Cookie
    activate A

    A->>R: Check Idempotency Key (24h TTL)
    R-->>A: Not seen (new request)

    A->>D: Begin Transaction<br/>Insert InHeatLog
    activate D

    A->>D: Update Dog Status
    A->>R: Store Idempotency Key
    A->>C: Queue rebuild_closure_table
    activate C

    C-->>A: Task queued (async)
    deactivate C

    D-->>A: Commit OK
    deactivate D

    A->>R: Publish to SSE Channel
    A-->>P: 201 Created + Log ID
    deactivate A

    P-->>U: Return Success + Cache Headers

    R->>S: Broadcast Alert Event
    S-->>U: SSE: New Heat Alert<br/>(real-time, <500ms)

    Note over U,S: Real-time updates via EventSource

    opt Background Processing
        C->>D: Rebuild DogClosure Table
        C->>R: Update Cache
    end

    opt Duplicate Request
        U->>P: Same POST (retry)
        P->>A: Forward
        A->>R: Check Idempotency Key
        R-->>A: Already processed
        A-->>P: 200 Already Processed
        P-->>U: Return cached response
    end
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.13+ with `uv` or `pip`
- **Node.js** 22+ with `pnpm`
- **Docker** + Docker Compose
- **Redis CLI** and **PostgreSQL client** (optional, for debugging)

### Development Setup (Hybrid: Native + Containers)

#### 1. Start Infrastructure Containers

```bash
# Clone repository
git clone https://github.com/wellfond/bms.git
cd wellfond-bms

# Start PostgreSQL and Redis (only containers needed for dev)
docker compose -f infra/docker/docker-compose.yml up -d

# Verify containers are running
docker ps
# Should see: wellfond-postgres (5432), wellfond-redis (6379)
```

#### 2. Setup Backend (Native)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Django development server
python manage.py runserver 127.0.0.1:8000
```

#### 3. Setup Frontend (Native)

```bash
cd frontend

# Install dependencies
npm install  # or pnpm install

# Start Next.js development server
npm run dev  # Runs on http://localhost:3000
```

#### 4. Run Celery Worker (Native)

```bash
# In a new terminal, from backend directory
cd backend
source venv/bin/activate

# Start Celery worker
celery -A config worker -l info -Q high,default,low,dlq

# In another terminal, start Celery beat (scheduler)
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Environment Variables (`.env`)

```bash
# Database (connects to containerized PostgreSQL)
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

# Gotenberg (optional for dev)
GOTENBERG_URL=http://localhost:3001

# Testing
TEST_DB_NAME=wellfond_test_db
```

### Verify Setup

```bash
# Test Django API
curl http://127.0.0.1:8000/health/
# Expected: 200 OK

# Test Next.js frontend
curl http://localhost:3000
# Expected: HTML response

# Test BFF proxy
curl http://localhost:3000/api/proxy/health/
# Expected: Proxies to Django, returns 200
```

---

## 🏭 Deployment

### Architecture (Production)

Production uses full containerization with 11 services:

```
┌─────────────────────────────────────────────────────────────┐
│                         Docker Compose                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Next   │  │ Django  │  │ Celery  │  │ Celery  │       │
│  │   JS    │  │   API   │  │ Worker  │  │  Beat   │       │
│  │  :3000  │  │  :8000  │  │         │  │         │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │             │
│  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐  ┌────┴────┐       │
│  │PgBouncer│  │  Redis  │  │  Redis  │  │  Redis  │       │
│  │  :5432  │  │Sessions │  │ Broker  │  │  Cache  │       │
│  └────┬────┘  │  :6379  │  │  :6380  │  │  :6381  │       │
│       │       └─────────┘  └─────────┘  └─────────┘       │
│  ┌────┴────┐                                              │
│  │PostgreSQL│  ┌─────────┐  ┌─────────┐                   │
│  │   :5432 │  │Gotenberg│  │  Flower │                   │
│  │ (private│  │  :3000  │  │  :5555  │                   │
│  │   LAN)  │  └─────────┘  └─────────┘                   │
│  └─────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Steps

1. **Build Images**
   ```bash
   docker compose build
   ```

2. **Run Migrations**
   ```bash
   docker compose run --rm django python manage.py migrate
   ```

3. **Create Superuser**
   ```bash
   docker compose run --rm django python manage.py createsuperuser
   ```

4. **Start Services**
   ```bash
   docker compose up -d
   ```

5. **Verify Health**
   ```bash
   curl http://localhost:8000/health/
   curl http://localhost:3000
   ```

### Scaling Considerations

- **Celery Workers**: Scale horizontally by adding replicas
- **PostgreSQL**: Use PgBouncer for connection pooling (configured)
- **Redis**: Consider Redis Cluster for high availability
- **Next.js**: Use standalone output for efficient containerization

---

## 🧪 Development

### Code Style & Linting

```bash
# Backend
cd backend
black --check .          # Format checking
isort --check .          # Import sorting
flake8                   # Linting
mypy .                   # Type checking

# Frontend
cd frontend
npm run lint             # ESLint
npm run typecheck        # TypeScript
```

### Testing

```bash
# Backend tests
cd backend
pytest --cov=85          # Run with 85% coverage target

# Frontend tests
cd frontend
npm run test:coverage    # Vitest with coverage

# E2E tests
npx playwright test      # Playwright E2E
```

### CI/CD Pipeline

The project uses GitHub Actions with three jobs:
- **Backend**: lint, typecheck, test (pytest)
- **Frontend**: lint, typecheck, test, build
- **Infrastructure**: Docker build, Trivy security scan

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Master implementation roadmap (178 files, 9 phases) |
| [TODO.md](TODO.md) | Master TODO checklist with validation criteria |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operations guide, troubleshooting, incident response |
| [docs/SECURITY.md](docs/SECURITY.md) | Threat model, CSP policy, OWASP mitigations |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment procedures |
| [docs/API.md](docs/API.md) | Auto-generated API documentation |

---

## 🤝 Contributing

This is a proprietary project. Contributions are by invitation only.

For issues or feature requests, please contact:
- **Architecture Lead**: architecture@wellfond.sg
- **Compliance Officer**: compliance@wellfond.sg

---

## 📝 License

© 2026 Wellfond Pets Holdings Pte. Ltd. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution,
or use is strictly prohibited.

---

## 🙏 Acknowledgments

- **Singapore AVS** (Animal & Veterinary Service) for compliance guidelines
- **NParks** for regulatory reporting requirements
- **Django Community** for the excellent framework
- **Next.js Team** for the App Router and server components
- **Radix UI** for accessible, unstyled components

---

<p align="center">
  <strong>Wellfond BMS</strong> — Built with ❤️ in Singapore 🇸🇬
</p>

<p align="center">
  <a href="#readme-top">⬆️ Back to Top</a>
</p>
