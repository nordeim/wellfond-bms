# Wellfond BMS — Remediation Plan (Critical & High Findings)

**Date:** 2026-05-07  
**Based on:** COMPREHENSIVE_CODE_REVIEW_AUDIT_REPORT_9.md
**Status:** Ready for implementation

---

## Validation Methodology

Each finding below was re-validated by:
1. Re-reading the exact source file at the exact line
2. Checking `.gitignore` rules vs `git ls-files` to confirm what's actually tracked
3. Cross-referencing dev vs prod compose for consistency
4. Verifying the fix doesn't break other components

---

## 🔴 CRITICAL — C1: TLS Private Key Committed to Repository

### Re-Validation

| Check | Result |
|-------|--------|
| File exists on disk? | ✅ `infra/docker/nginx/certs/server.key` — PEM private key |
| Tracked by git? | ✅ `git ls-files` confirms tracked |
| `.gitignore` covers it? | ⚠️ Rules exist (`*.key`, `*.crt`) but **file was committed before rules were added** — `.gitignore` only prevents *new* untracked files, it does NOT remove already-tracked files |
| When committed? | Commit `3864e9e` ("update docker config") |
| Self-signed or CA? | Self-signed, CN=localhost, valid 2026-04-30 → 2027-04-30 |

### Root Cause

The `.gitignore` was updated to exclude `*.key` and `*.crt` **after** the certs were already committed. Git continues to track files that were committed before a `.gitignore` rule was added. This is a common git footgun.

### Remediation Steps

```bash
# Step 1: Remove from git tracking (keeps file on disk)
cd /root/.openclaw/workspace/wellfond-bms
git rm --cached infra/docker/nginx/certs/server.key
git rm --cached infra/docker/nginx/certs/server.crt

# Step 2: Verify .gitignore already covers these
grep -E '^\*\.(key|crt|pem)' .gitignore
# Should show: *.key, *.crt, *.pem — all present ✅

# Step 3: Commit the removal
git commit -m "security: remove TLS private key and cert from tracking

- git rm --cached removes from index without deleting local files
- .gitignore already has *.key and *.crt rules
- Generate new certs per infra/docker/docker-compose.yml instructions"
```

```bash
# Step 4: For dev, generate fresh self-signed certs locally
mkdir -p infra/docker/nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infra/docker/nginx/certs/server.key \
  -out infra/docker/nginx/certs/server.crt \
  -subj "/C=SG/ST=Singapore/L=Singapore/O=Wellfond/CN=localhost"

# Step 5: For production — use Let's Encrypt or a proper CA
# Option A: certbot with standalone/nginx plugin
# Option B: Docker secret / vault mount
# Option C: Cloud provider managed cert (AWS ACM, Cloudflare, etc.)
```

### Production Cert Strategy (Recommendation)

For production, do NOT use self-signed certs. Two options:

**Option A — Let's Encrypt (recommended for VPS):**
```yaml
# Add to production docker-compose.yml
certbot:
  image: certbot/certbot
  volumes:
    - ./certs:/etc/letsencrypt
    - certbot-webroot:/var/www/certbot
  entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done'"
```

**Option B — Managed cert (recommended for cloud):**
Use AWS ACM, Cloudflare Origin Cert, or GCP managed SSL. Mount the cert/key via Docker secrets:
```yaml
secrets:
  tls_cert:
    file: ./certs/server.crt
  tls_key:
    file: ./certs/server.key
```

### Verification

```bash
# Confirm file is no longer tracked
git ls-files infra/docker/nginx/certs/
# Should return empty

# Confirm .gitignore prevents re-tracking
git status infra/docker/nginx/certs/
# Should show nothing (ignored)
```

---

## 🔴 CRITICAL — C2: Hardcoded Dev Secret Key in Tracked Files

### Re-Validation

| Check | Result |
|-------|--------|
| `.env.example` tracked? | ✅ Yes, explicitly allowed via `!.env.example` in `.gitignore` |
| `.env.bak` tracked? | ✅ Yes, committed before `*.bak` rule was added |
| Secret key value | `dev-secret-key-change-in-production-2026-wellfond-singapore` |
| Same key in both? | ✅ Identical value in both files |
| `.env.bak` commit | `8d4ee66` ("mimo audit 7 remediation review") |
| Production settings use `DJANGO_SECRET_KEY` env var? | ✅ `base.py` line: `SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]` — no fallback |

### Root Cause

Two issues:
1. `.env.example` is **intentionally tracked** (via `!.env.example`) as a template, but it contains a semi-real-looking secret key instead of a placeholder.
2. `.env.bak` was committed before the `*.bak` gitignore rule and is still tracked.

The production Django settings correctly read from `DJANGO_SECRET_KEY` env var (not `SECRET_KEY`), so the `.env.example` key would never be used in production **unless someone mistakenly sets `DJANGO_SECRET_KEY` to the same value**. The risk is primarily social engineering / copy-paste errors.

### Remediation Steps

**Part A — Fix `.env.example` (replace key with clear placeholder):**

```bash
# In .env.example, change:
# SECRET_KEY=dev-secret-key-change-in-production-2026-wellfond-singapore
# To:
# SECRET_KEY=CHANGE_ME_GENERATE_WITH_openssl_rand_base64_50
```

Also update the comment block to be more explicit:
```env
# =============================================================================
# Django Settings
# =============================================================================
# SECURITY WARNING: This is a TEMPLATE. Replace ALL placeholder values.
# Generate SECRET_KEY: openssl rand -base64 50
# The production settings read DJANGO_SECRET_KEY (not SECRET_KEY).
# Set DJANGO_SECRET_KEY in your production .env or secrets manager.
SECRET_KEY=CHANGE_ME_GENERATE_WITH_openssl_rand_base64_50
```

**Part B — Remove `.env.bak` from tracking:**

```bash
git rm --cached .env.bak
git commit -m "security: remove .env.bak from tracking

- .env.bak contained dev secret key
- .gitignore already has *.bak rule but file was committed before rule
- Use .env.example as the only tracked template"
```

**Part C — Add pre-commit hook (optional but recommended):**

Create `.githooks/pre-commit`:
```bash
#!/bin/bash
# Block commits containing known secret patterns
if git diff --cached --diff-filter=A -p | grep -qE '(sk_test|sk_live|sk-proj-|ghp_|gho_|SECRET_KEY=.+[a-zA-Z0-9]{20,})'; then
    echo "ERROR: Potential secret detected in staged files."
    echo "If this is intentional, use: git commit --no-verify"
    exit 1
fi
```

### Verification

```bash
# Confirm .env.bak no longer tracked
git ls-files .env.bak
# Should return empty

# Confirm .env.example has placeholder, not real key
grep SECRET_KEY .env.example
# Should show: SECRET_KEY=CHANGE_ME_GENERATE_WITH_openssl_rand_base64_50
```

---

## 🔴 CRITICAL — C3: Dev Redis Exposed on 0.0.0.0 Without Password

### Re-Validation

| Check | Result |
|-------|--------|
| File | `infra/docker/docker-compose.yml` (full-containerized dev) |
| Port binding | `0.0.0.0:6379:6379` — all interfaces |
| Password? | ❌ No `--requirepass` in command |
| Same in `.bak`? | ✅ Same issue in `infra/docker/docker-compose.yml.bak` |
| Production compose? | ✅ Production has **no ports exposed** for Redis (correct) |
| Dev hybrid compose? | ✅ Uses `127.0.0.1:5432` for PG but Redis not in that compose |

### Root Cause

The dev compose was written for local-only use but binds Redis to `0.0.0.0` (all network interfaces) with no authentication. On a shared network (office WiFi, cloud VPS without firewall), any machine can connect to port 6379 and read/write session data, cached credentials, and Celery task results.

### Remediation Steps

**Fix in `infra/docker/docker-compose.yml`:**

```yaml
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
      --requirepass ${REDIS_PASSWORD:-dev_redis_password}
    ports:
      - "127.0.0.1:6379:6379"   # ← Changed from 0.0.0.0 to 127.0.0.1
    # ... rest unchanged
```

**Fix in `infra/docker/docker-compose.yml.bak`:** Same change, or delete the `.bak` file entirely (it's redundant).

**Update backend service to use password:**

```yaml
backend:
    environment:
      # Change redis URLs to include password:
      REDIS_CACHE_URL: redis://:${REDIS_PASSWORD:-dev_redis_password}@redis:6379/0
      REDIS_SESSIONS_URL: redis://:${REDIS_PASSWORD:-dev_redis_password}@redis:6379/1
      REDIS_BROKER_URL: redis://:${REDIS_PASSWORD:-dev_redis_password}@redis:6379/2
      REDIS_IDEMPOTENCY_URL: redis://:${REDIS_PASSWORD:-dev_redis_password}@redis:6379/3
```

**Also apply same fix to production compose** (add `--requirepass` to all 4 Redis instances):

```yaml
redis_sessions:
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru --save 60 1 --requirepass ${REDIS_PASSWORD:?required}
redis_broker:
    command: redis-server --maxmemory 256mb --maxmemory-policy noeviction --save 60 1 --requirepass ${REDIS_PASSWORD:?required}
redis_cache:
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru --save 60 1 --requirepass ${REDIS_PASSWORD:?required}
redis_idempotency:
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru --save 60 1 --requirepass ${REDIS_PASSWORD:?required}
```

**Update all Redis URLs in production compose to include password:**

```yaml
# In celery_worker, celery_beat, and django service environment:
REDIS_SESSIONS_URL: redis://:${REDIS_PASSWORD}@redis_sessions:6379/0
REDIS_BROKER_URL: redis://:${REDIS_PASSWORD}@redis_broker:6379/0
REDIS_CACHE_URL: redis://:${REDIS_PASSWORD}@redis_cache:6379/0
REDIS_IDEMPOTENCY_URL: redis://:${REDIS_PASSWORD}@redis_idempotency:6379/0
```

**Update `.env.example`:**

```env
# =============================================================================
# Redis Configuration
# =============================================================================
REDIS_PASSWORD=CHANGE_ME_GENERATE_WITH_openssl_rand_base64_32
```

### Verification

```bash
# From outside the Docker network, attempt connection
redis-cli -h <host-ip> -p 6379 ping
# Should fail with "Connection refused" (127.0.0.1 binding)
# or "NOAUTH Authentication required" (password required)
```

---

## 🟠 HIGH — H1: PgBouncer Exposed on Host Port 6432 (Production)

### Re-Validation

| Check | Result |
|-------|--------|
| File | `docker-compose.yml` (production, root level) |
| Port mapping | `ports: - "6432:5432"` |
| Who connects to PgBouncer? | Django, Celery worker, Celery beat — all on `backend_net` |
| External access needed? | ❌ No — PgBouncer is an internal connection pooler |

### Root Cause

Likely copied from a dev/debug setup where someone wanted to connect a local DB client to PgBouncer. In production, no external service should connect to PgBouncer directly.

### Remediation

```yaml
# In docker-compose.yml (production), change:
pgbouncer:
    # Remove this block entirely:
    # ports:
    #   - "6432:5432"
    # ... rest unchanged
```

If developers need ad-hoc access for debugging, use:
```bash
docker compose exec pgbouncer psql -U wellfond_app wellfond
```

### Verification

```bash
# From host, attempt connection
psql -h localhost -p 6432 -U wellfond_app
# Should fail with "Connection refused"
```

---

## 🟠 HIGH — H2: Flower Dashboard Without Authentication

### Re-Validation

| Check | Result |
|-------|--------|
| File | `docker-compose.yml` (production) |
| Port | `5555:5555` exposed |
| Auth env vars? | ❌ No `FLOWER_BASIC_AUTH`, `FLOWER_OAUTH2`, or `--basic_auth` in command |
| Flower version | `mher/flower:2.0` |
| What's exposed? | Task list, worker status, task retry/cancel, broker stats |

### Root Cause

Flower was added for monitoring but authentication was not configured. Without auth, anyone with network access to port 5555 can view all Celery tasks (which may contain sensitive business data) and retry/cancel tasks.

### Remediation

**Option A — Basic Auth (simplest):**

```yaml
flower:
    image: mher/flower:2.0
    container_name: wellfond-flower
    environment:
      FLOWER_BROKER_API: redis://:${REDIS_PASSWORD}@redis_broker:6379/0
      FLOWER_BASIC_AUTH: ${FLOWER_USER:-admin}:${FLOWER_PASSWORD:?required}
    ports:
      - "127.0.0.1:5555:5555"   # Also bind to localhost only
    networks:
      - backend_net
    depends_on:
      redis_broker:
        condition: service_healthy
    # ... healthcheck unchanged
```

**Option B — Remove port exposure entirely (most secure):**

```yaml
flower:
    image: mher/flower:2.0
    container_name: wellfond-flower
    environment:
      FLOWER_BROKER_API: redis://:${REDIS_PASSWORD}@redis_broker:6379/0
    # No ports: — access via docker compose exec or SSH tunnel
    networks:
      - backend_net
    # ...
```

Access via: `ssh -L 5555:localhost:5555 server` then open `http://localhost:5555`

**Update `.env.example`:**

```env
# Flower Monitoring (Production)
FLOWER_USER=admin
FLOWER_PASSWORD=CHANGE_ME
```

### Verification

```bash
curl -s http://localhost:5555/
# With auth: should return 401
# Without port: should return "Connection refused"
```

---

## 🟠 HIGH — H3: Django Service Missing Build/Image Directive

### Re-Validation

| Check | Result |
|-------|--------|
| File | `docker-compose.yml` (production, root level) |
| Service | `django:` |
| Has `build:`? | ❌ No |
| Has `image:`? | ❌ No |
| Other services? | `celery_worker` and `celery_beat` both have `build: context: ./backend, dockerfile: Dockerfile.django` |
| Dockerfile exists? | ✅ `infra/docker/Dockerfile.django` — multi-stage, non-root, gunicorn+uvicorn |

### Root Cause

The `django` service definition is incomplete. It has `depends_on`, `healthcheck`, `restart`, and `networks` but is missing the `build:` directive that tells Docker how to create the image. This is likely a copy-paste error when splitting the compose file — the build context was included for celery services but missed for django.

Note: The Dockerfile path in celery services is `Dockerfile.django` (relative to `./backend` context), but the actual file is at `infra/docker/Dockerfile.django`. This may also need fixing.

### Remediation

```yaml
django:
    build:
      context: ./backend
      dockerfile: ../infra/docker/Dockerfile.django
    container_name: wellfond-django
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
      POSTGRES_DB: wellfond
      POSTGRES_USER: wellfond_app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_HOST: pgbouncer
      POSTGRES_PORT: "5432"
      REDIS_SESSIONS_URL: redis://:${REDIS_PASSWORD}@redis_sessions:6379/0
      REDIS_BROKER_URL: redis://:${REDIS_PASSWORD}@redis_broker:6379/0
      REDIS_CACHE_URL: redis://:${REDIS_PASSWORD}@redis_cache:6379/0
      REDIS_IDEMPOTENCY_URL: redis://:${REDIS_PASSWORD}@redis_idempotency:6379/0
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
    networks:
      - backend_net
    depends_on:
      pgbouncer:
        condition: service_healthy
      redis_sessions:
        condition: service_healthy
      redis_broker:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\""]
      interval: 15s
      timeout: 10s
      retries: 3
      start_period: 30s
    restart: unless-stopped
```

**Also fix celery_worker and celery_beat Dockerfile paths:**

```yaml
celery_worker:
    build:
      context: ./backend
      dockerfile: ../infra/docker/Dockerfile.django  # ← Fix path
celery_beat:
    build:
      context: ./backend
      dockerfile: ../infra/docker/Dockerfile.django  # ← Fix path
```

### Verification

```bash
cd /root/.openclaw/workspace/wellfond-bms
docker compose config --services | grep django
# Should list 'django' without errors

docker compose build django
# Should build successfully
```

---

## 🟠 HIGH — H4: Next.js Exposed on Port 3000 Without Nginx (Production)

### Re-Validation

| Check | Result |
|-------|--------|
| File | `docker-compose.yml` (production) |
| Next.js ports | `3000:3000` exposed directly |
| Nginx in production compose? | ❌ No nginx service defined |
| Nginx in dev compose? | ✅ `infra/docker/docker-compose.yml` has nginx on port 443 |
| Nginx config exists? | ✅ `infra/docker/nginx/nginx.conf` with TLS termination |
| Next.js security headers? | ✅ X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy set in `next.config.ts` |
| Django HSTS? | ✅ `SECURE_HSTS_SECONDS=31536000` in production.py |

### Root Cause

The production compose was designed for a setup where a cloud load balancer (ALB, Cloudflare, etc.) terminates TLS externally. However, the compose file itself doesn't include nginx, meaning if deployed standalone, there's no TLS and no edge rate limiting.

**Context consideration:** This may be intentional if deploying behind a managed load balancer. But the compose file should document this assumption or include nginx as an option.

### Remediation

**Option A — Add nginx to production compose (for standalone VPS deployment):**

```yaml
nginx:
    image: nginx:1-alpine
    container_name: wellfond-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/docker/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro  # Production certs (Let's Encrypt or managed)
    depends_on:
      - nextjs
    networks:
      - frontend_net
    restart: unless-stopped
```

And change Next.js to not expose ports:
```yaml
nextjs:
    # Remove: ports: - "3000:3000"
    expose:
      - "3000"
    # ... rest unchanged
```

**Option B — Document cloud LB assumption (if using managed TLS):**

Add a comment to the production compose:
```yaml
# NOTE: This compose assumes TLS is terminated by an external load balancer
# (e.g., AWS ALB, Cloudflare, GCP LB). If deploying standalone, add nginx
# service from infra/docker/docker-compose.yml as reference.
nextjs:
    ports:
      - "3000:3000"  # Exposed for LB → Next.js proxy
```

**Recommended:** Option A for VPS deployments, Option B for cloud-managed deployments. Consider making two compose files: `docker-compose.yml` (standalone) and `docker-compose.cloud.yml` (behind LB).

### Verification

```bash
# With nginx: should redirect HTTP → HTTPS
curl -I http://localhost:80
# Should return 301 → https://

# Without nginx (Option B): verify LB handles TLS
curl -I https://wellfond.sg
# Should show valid TLS cert from LB
```

---

## 🟠 HIGH — H5: No Redis Password in Any Environment

### Re-Validation

| Check | Result |
|-------|--------|
| Production compose — Redis commands | No `--requirepass` in any of the 4 Redis services |
| Dev compose — Redis command | No `--requirepass` |
| `.env.example` | No `REDIS_PASSWORD` variable |
| Redis URL format | `redis://redis_sessions:6379/0` — no auth in URL |
| Redis on isolated network? | ✅ Production uses `backend_net` (mitigates risk somewhat) |

### Root Cause

Redis was set up for simplicity without authentication, relying on Docker network isolation as the security boundary. While network isolation helps, it's defense-in-depth insufficient — a compromised container on `backend_net` could connect to any Redis instance.

### Remediation

This is covered in **C3 remediation above** (same fix applies to both dev and prod). Summary:

1. Add `--requirepass ${REDIS_PASSWORD:?required}` to all Redis commands
2. Add `REDIS_PASSWORD` to `.env.example` with placeholder
3. Update all Redis URLs to include password: `redis://:${REDIS_PASSWORD}@host:6379/0`
4. Update Django `CACHES` in `base.py` to use `REDIS_PASSWORD` env var for URL construction

**Django settings update (`base.py`):**

```python
_REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
_REDIS_AUTH = f":{_REDIS_PASSWORD}@" if _REDIS_PASSWORD else ""

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get(
            "REDIS_CACHE_URL",
            f"redis://{_REDIS_AUTH}redis_cache:6379/0"
        ),
    },
    # ... same pattern for sessions, idempotency
}
```

---

## 🟠 HIGH — H6: Self-Signed Certificate in Repository

### Re-Validation

| Check | Result |
|-------|--------|
| `server.crt` tracked? | ✅ `git ls-files` confirms |
| `server.key` tracked? | ✅ (covered in C1) |
| `.gitignore` rules? | `*.crt` and `*.key` present but file committed before rules |
| Cert details | CN=localhost, O=Wellfond, C=SG, valid 2026-04-30 → 2027-04-30 |
| Self-signed? | ✅ Self-signed (not CA-issued) |

### Root Cause

Same as C1 — committed before `.gitignore` rules. The cert itself is less sensitive than the key, but it shouldn't be in the repo as it creates confusion about which cert is "real."

### Remediation

Covered in **C1 remediation** — `git rm --cached` both files together.

```bash
git rm --cached infra/docker/nginx/certs/server.key infra/docker/nginx/certs/server.crt
git commit -m "security: remove TLS key and cert from git tracking"
```

### Production Cert Approach

Document in `infra/docker/README.md`:

```markdown
## TLS Certificates

### Development
Generate self-signed certs (see docker-compose.yml comments):
\`\`\`bash
mkdir -p nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/server.key \
  -out nginx/certs/server.crt \
  -subj "/C=SG/ST=Singapore/L=Singapore/O=Wellfond/CN=localhost"
\`\`\`

### Production
Use one of:
- **Let's Encrypt** (VPS): certbot with auto-renewal
- **Managed cert** (cloud): AWS ACM / Cloudflare Origin / GCP managed SSL
- **Internal CA**: For enterprise deployments

Never commit private keys to version control.
```

---

## Implementation Order

| Step | Finding | Effort | Risk if Skipped |
|------|---------|--------|-----------------|
| 1 | C1 + H6: Remove TLS key/cert from git | 10 min | Private key in repo = total TLS compromise |
| 2 | C3 + H5: Add Redis passwords | 30 min | Unauthenticated Redis = session hijack, data theft |
| 3 | C2: Fix `.env.example` placeholder, remove `.env.bak` | 10 min | Copy-paste secret leakage |
| 4 | H3: Add missing Django build directive | 5 min | Production compose won't start |
| 5 | H1: Remove PgBouncer port exposure | 2 min | Direct DB pooler access |
| 6 | H2: Add Flower auth | 10 min | Unauthenticated task dashboard |
| 7 | H4: Add nginx or document LB assumption | 30 min | No TLS in standalone deployment |

**Total estimated effort: ~1.5 hours**

---

## Files to Modify

| File | Changes |
|------|---------|
| `docker-compose.yml` (prod) | H1: remove PgBouncer ports, H2: add Flower auth, H3: add Django build, H4: add nginx or document, H5/C3: add Redis passwords |
| `infra/docker/docker-compose.yml` (dev) | C3: bind Redis to 127.0.0.1 + add password |
| `infra/docker/docker-compose.yml.bak` | Delete (redundant) |
| `.env.example` | C2: placeholder secret key, add REDIS_PASSWORD, FLOWER_USER/PASSWORD |
| `.env.bak` | C2: `git rm --cached` |
| `infra/docker/nginx/certs/*` | C1/H6: `git rm --cached` |
| `backend/config/settings/base.py` | H5: Redis password in URL construction |

---

## Post-Remediation Checklist

- [ ] `git ls-files infra/docker/nginx/certs/` returns empty
- [ ] `git ls-files .env.bak` returns empty
- [ ] `grep SECRET_KEY .env.example` shows placeholder only
- [ ] `docker compose config` validates without errors (production)
- [ ] Redis requires password: `redis-cli ping` → `NOAUTH`
- [ ] PgBouncer not accessible from host: `psql -h localhost -p 6432` → refused
- [ ] Flower requires auth: `curl localhost:5555` → 401
- [ ] Django service has `build:` directive
- [ ] All Redis URLs include password
