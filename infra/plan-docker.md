**Research & Review Plan**  
I’ve cross‑referenced the current `docker-compose.yml` against:

- the full project brief (especially the BFF security rules, hybrid development strategy, and required environment variables)  
- the corrected Alpine Dockerfiles we already created for the backend and frontend  
- the enterprise‑grade patterns mandated by the Wellfond architecture (no `NEXT_PUBLIC_*` for internal URLs, strict cookie forwarding, etc.)

Below is the meticulous review and the plan for a complete, corrected replacement file.

---

### 1. Findings & Required Changes

| # | Service | Issue | Fix |
|---|---------|-------|-----|
| **1** | **backend** | `DJANGO_SETTINGS_MODULE=wellfond.settings.development` is wrong. The actual module is `config.settings.development`. | Change to `config.settings.development`. |
| **2** | **backend** | `DATABASE_URL` uses the deprecated `postgres://` scheme. Django’s `django-environ` expects `postgresql://`. | Use `postgresql://wellfond_user:...`. |
| **3** | **backend** | Missing `BACKEND_INTERNAL_URL` and proper Redis split‑keys (though for dev a single Redis is fine, the env vars must match the settings). | Add `BACKEND_INTERNAL_URL=http://frontend:3000` (no, the backend doesn’t need that). Actually the backend doesn’t use that; it’s for the frontend’s server‑side fetches. The backend just needs to be reachable. We’ll add the proper Redis URLs that match `config.settings.development`. |
| **4** | **frontend** | Exposes dangerous `NEXT_PUBLIC_BACKEND_URL` and `NEXT_PUBLIC_API_URL` to the browser. The architecture mandates that the Next.js server uses a server‑only `BACKEND_INTERNAL_URL` and the BFF proxy forwards requests with cookies. | Remove all `NEXT_PUBLIC_*` variables. Set `BACKEND_INTERNAL_URL=http://backend:8000` (server‑side only). The frontend container can reach the backend container via Docker DNS name `backend`. |
| **5** | **frontend** | Runs `npm install` on every start. Dependencies should be installed in the Dockerfile. The volume mount overrides `node_modules`; the image already contains the installed modules. | Remove `npm install` from the command. Keep the volume for live‑reload of code, but fence off `node_modules`. |
| **6** | **frontend** | The command `npm run dev` starts the Next.js development server. The BFF proxy (`api/proxy/[...path]`) reads `BACKEND_INTERNAL_URL`. We need to pass that env var. | Add `BACKEND_INTERNAL_URL=http://backend:8000` to the frontend service environment (no `NEXT_PUBLIC_` prefix). |
| **7** | **postgres** | Image `postgres:17-trixie` is not an official tag. It may work but is non‑standard. Because you asked not to change working services, I’ll leave it, but I’ll add a comment advising `postgres:17-alpine` for consistency. | No change, just a warning comment. |
| **8** | **nginx** | Not present. You requested an official `nginx:1-alpine` that terminates SSL on port 443 and forwards to the frontend. | Add a new `nginx` service with a custom config, self‑signed certs, and port mapping `443:443`. The frontend’s port 3000 is no longer published to the host; nginx becomes the only entry point. |
| **9** | **volumes** | Need a volume for nginx SSL certs and a bind mount for the nginx config. | Add `./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro` and `./nginx/certs:/etc/nginx/certs:ro`. |

---

### 2. Updated `docker-compose.yml` – Complete Replacement

```yaml
# =============================================================================
# Wellfond BMS - Development Docker Compose (Full Containerized Dev)
# =============================================================================
# All services run in containers. Nginx terminates HTTPS on 443 and proxies to
# the Next.js frontend. The frontend's BFF proxy forwards API calls to the
# Django backend.
#
# IMPORTANT: Generate self‑signed certs before first boot:
#   mkdir -p nginx/certs
#   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#     -keyout nginx/certs/server.key \
#     -out nginx/certs/server.crt \
#     -subj "/C=SG/ST=Singapore/L=Singapore/O=Wellfond/CN=localhost"
# =============================================================================

services:
  # ==========================================================================
  # PostgreSQL 17 – Database (unchanged from working state)
  # ==========================================================================
  postgres:
    image: postgres:17-trixie   # consider switching to postgres:17-alpine for consistency
    container_name: wellfond-postgres
    environment:
      POSTGRES_DB: wellfond_db
      POSTGRES_USER: wellfond_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-wellfond_dev_password}
      POSTGRES_HOST_AUTH_METHOD: trust          # dev‑only trust mode
      TZ: Asia/Singapore
      PGDATA: /var/lib/postgresql/data/pgdata
    command: >
      postgres
      -c timezone=Asia/Singapore
      -c log_destination=stderr
      -c logging_collector=off
      -c log_min_messages=warning
      -c wal_level=replica
      -c shared_buffers=256MB
      -c effective_cache_size=768MB
    ports:
      - "127.0.0.1:5432:5432"   # bind only to loopback for local tooling
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U wellfond_user"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - wellfond-network
    restart: unless-stopped

  # ==========================================================================
  # Redis 7.4 – Cache / Sessions / Broker (unchanged)
  # ==========================================================================
  redis:
    image: redis:7.4-alpine
    container_name: wellfond-redis
    command: >
      redis-server
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --save 60 1000
      --loglevel warning
    ports:
      - "0.0.0.0:6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 5s
    networks:
      - wellfond-network
    restart: unless-stopped

  # ==========================================================================
  # Django 6.0 Backend
  # ==========================================================================
  backend:
    build:
      context: ../../backend
      dockerfile: ../infra/docker/Dockerfile.backend.dev   # your corrected Alpine Dockerfile
    container_name: wellfond-backend
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development   # FIXED
      DATABASE_URL: postgresql://wellfond_user:${DB_PASSWORD:-wellfond_dev_password}@postgres:5432/wellfond_db
      REDIS_CACHE_URL: redis://redis:6379/0
      REDIS_SESSIONS_URL: redis://redis:6379/1
      REDIS_BROKER_URL: redis://redis:6379/2
      DEBUG: "true"
      SECRET_KEY: ${SECRET_KEY:-dev-secret-key-not-for-production}
    ports:
      - "8000:8000"   # exposed for native tooling (e.g., Postman) as well
    volumes:
      - ../../backend:/app
      - backend_static:/app/staticfiles
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - wellfond-network
    restart: unless-stopped
    command: >
      sh -c "python wait_for_db.py &&
             python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"

  # ==========================================================================
  # Next.js 16 Frontend
  # ==========================================================================
  frontend:
    build:
      context: ../../frontend
      dockerfile: ../infra/docker/Dockerfile.frontend.dev   # your corrected Alpine Dockerfile
    container_name: wellfond-frontend
    environment:
      # Server‑side only – never prefixed with NEXT_PUBLIC_
      BACKEND_INTERNAL_URL: http://backend:8000
      NODE_ENV: development
    # Do NOT publish 3000 to the host – nginx will proxy HTTPS
    expose:
      - "3000"
    volumes:
      - ../../frontend:/app
      # fence off dependencies that were installed in the image
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend
    networks:
      - wellfond-network
    restart: unless-stopped
    command: ["npm", "run", "dev"]   # no "npm install" here

  # ==========================================================================
  # Nginx 1.x – SSL Termination, reverse proxy to Next.js
  # ==========================================================================
  nginx:
    image: nginx:1-alpine
    container_name: wellfond-nginx
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
    networks:
      - wellfond-network
    restart: unless-stopped

# =============================================================================
# Named Volumes
# =============================================================================
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  backend_static:
    driver: local

# =============================================================================
# Networks
# =============================================================================
networks:
  wellfond-network:
    driver: bridge
```

---

### 3. Required Supplementary Files

#### a) `nginx/nginx.conf` (create alongside `docker-compose.yml`)

```nginx
server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate     /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;

    # Security headers (CSP, HSTS, etc.)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;

    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Next.js BFF proxy will forward cookies internally
        proxy_pass_header Set-Cookie;
    }
}
```

#### b) Self‑signed certificate (run once before first start)

```bash
mkdir -p nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt \
  -subj "/C=SG/ST=Singapore/L=Singapore/O=Wellfond/CN=localhost"
```

---

### 4. Post‑Update Verification

1. **Start the stack**  
   `docker compose up -d`  
   (ensure the certificates are in place first).

2. **Check nginx**  
   `curl -k https://localhost` should return the Next.js app.

3. **Check BFF proxy**  
   `curl -k https://localhost/api/proxy/health/`  
   should reach Django’s `/health/` endpoint.

4. **Confirm no secrets in browser**  
   Open DevTools → Network → look for `NEXT_PUBLIC_` variables in JS bundles → none should appear.

All previous anti‑patterns (wrong settings module, client‑exposed internal URLs, runtime `npm install`) have been eliminated, and the nginx layer adds TLS termination exactly as requested.

---

Based on the project’s actual implementation (as shown in `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, and the URL configurations), the correct health-check URLs are:

| Service | Current (incorrect) URL | Correct URL | Why |
|---------|--------------------------|-------------|-----|
| **Backend** | `curl -f http://localhost:8000/api/v1/health/` | `curl -f http://localhost:8000/health/` | Django’s health endpoint is registered at the root level: `path('health/', health_check)`. There is no `/api/v1/health/` route. |
| **Frontend** | `curl -f http://localhost:3000/api/health` | `curl -f http://localhost:3000/api/proxy/health/` (or a custom Next.js health route if added) | The Next.js app does **not** have a dedicated `/api/health` endpoint. The BFF proxy forwards `GET /api/proxy/health/` to the Django backend’s `/health/`, giving a reliable health check that validates the full proxy chain. |

---

## Corrected Lines for the Dockerfiles

### In `infra/docker/Dockerfile.backend.dev`

```dockerfile
HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1
```

### In `infra/docker/Dockerfile.frontend.dev`

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/api/proxy/health/ || exit 1
```

---

## Why the correction matters

1. **Backend** – Django serves `/health/` directly; the `/api/v1/` prefix is only applied to Ninja routers.  
2. **Frontend** – Since Next.js doesn’t include a health API by default, using the **BFF proxy** path (`/api/proxy/health/`) is the most faithful check: it ensures the Next.js server is running *and* that it can reach Django. If you prefer a lighter endpoint, you could add a simple Next.js API route (e.g., `app/api/health/route.ts` that returns `200`), but the proxy approach tests end‑to‑end connectivity.

Adjust the health checks in both Dockerfiles accordingly, and the containers will report healthy only when the full stack is functioning.

# https://chat.deepseek.com/share/h5ui9hxxqtz2792cfa 

