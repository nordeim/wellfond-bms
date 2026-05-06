# Wellfond BMS — Infrastructure & Configuration Audit

**Date:** 2026-05-07  
**Scope:** docker-compose, Dockerfiles, infra/, Django settings, Next.js config, CI/CD, PWA, scripts  
**Remediation:** See [REMEDIATION_PLAN.md](./REMEDIATION_PLAN.md) for detailed fix instructions

---

## Executive Summary

The Wellfond BMS infrastructure is **well-designed overall** with good separation of concerns (split Redis instances, PgBouncer, network isolation, non-root containers). However, several **critical and high-severity issues** need attention before production deployment.

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 CRITICAL | 3 | ✅ All re-validated — root causes confirmed |
| 🟠 HIGH | 6 | ✅ All re-validated — root causes confirmed |
| 🟡 MEDIUM | 8 | Pending re-validation |
| 🔵 LOW | 4 | Pending re-validation |

---

## 🔴 CRITICAL Findings

### C1. TLS Private Key Committed to Repository `✅ RE-VALIDATED`
**File:** `infra/docker/nginx/certs/server.key`  
**Impact:** Private key is in version control. If this repo is public or leaks, all HTTPS traffic can be decrypted.  
**Evidence:** PEM private key file exists alongside `server.crt` in the repo. `git ls-files` confirms both are tracked.  
**Root Cause:** `.gitignore` has `*.key` and `*.crt` rules, but the files were committed (commit `3864e9e`) **before** those rules were added. Git continues tracking already-committed files regardless of `.gitignore`.  
**Fix:** `git rm --cached` both files + generate fresh certs. See [REMEDIATION_PLAN.md C1](./REMEDIATION_PLAN.md#-critical--c1-tls-private-key-committed-to-repository).

### C2. Hardcoded Dev Secret Key in `.env.example` and `.env.bak` `✅ RE-VALIDATED`
**Files:** `.env.example`, `.env.bak`  
**Impact:** Both files contain `SECRET_KEY=dev-secret-key-change-in-production-2026-wellfond-singapore`. `.env.example` is intentionally tracked (via `!.env.example` in `.gitignore`). `.env.bak` was committed (commit `8d4ee66`) before the `*.bak` gitignore rule.  
**Root Cause:** `.env.example` uses a semi-real-looking key instead of an obvious placeholder. `.env.bak` was committed before `.gitignore` was updated.  
**Risk Note:** Production settings read `DJANGO_SECRET_KEY` (not `SECRET_KEY`), so the `.env.example` key wouldn't be used in prod **unless someone copy-pastes it into `DJANGO_SECRET_KEY`**. Risk is primarily social engineering / copy-paste errors.  
**Fix:** Replace key with `CHANGE_ME_GENERATE_WITH_openssl_rand_base64_50` placeholder + `git rm --cached .env.bak`. See [REMEDIATION_PLAN.md C2](./REMEDIATION_PLAN.md#-critical--c2-hardcoded-dev-secret-key-in-tracked-files).

### C3. Docker Compose Dev Exposes Redis on `0.0.0.0:6379` `✅ RE-VALIDATED`
**Files:** `infra/docker/docker-compose.yml`, `infra/docker/docker-compose.yml.bak`  
**Impact:** Redis is bound to all interfaces (`0.0.0.0:6379`) with **no password**. Any machine on the network can connect and read/write data, including session tokens and cached credentials.  
**Evidence:**
```yaml
ports:
  - "0.0.0.0:6379:6379"
# No --requirepass in command
```
**Root Cause:** Written for local-only use but uses `0.0.0.0` binding instead of `127.0.0.1`. The dev compose's Postgres correctly uses `127.0.0.1:5432:5432` but Redis doesn't follow the same pattern.  
**Fix:** Bind to `127.0.0.1:6379:6379` + add `--requirepass`. See [REMEDIATION_PLAN.md C3](./REMEDIATION_PLAN.md#-critical--c3-dev-redis-exposed-on-0000-without-password).

---

## 🟠 HIGH Findings

### H1. PgBouncer Exposed on Host Port 6432 (Production) `✅ RE-VALIDATED`
**File:** `docker-compose.yml` (production)  
**Impact:** PgBouncer port `6432` is published to the host. In production, database connection pooling should only be accessible from within the Docker network.  
**Evidence:**
```yaml
pgbouncer:
  ports:
    - "6432:5432"
```
**Root Cause:** Likely copied from dev/debug setup. All PgBouncer consumers (django, celery_worker, celery_beat) are on `backend_net` and connect via hostname `pgbouncer`. No external access is needed.  
**Fix:** Remove the `ports` mapping entirely. See [REMEDIATION_PLAN.md H1](./REMEDIATION_PLAN.md#-high--h1-pgbouncer-exposed-on-host-port-6432-production).

### H2. Flower Monitoring Dashboard Exposed Without Authentication `✅ RE-VALIDATED`
**File:** `docker-compose.yml` (production)  
**Impact:** Flower (Celery monitoring) is on port `5555` with no authentication configured. Anyone with network access can view task details, retry/cancel tasks, and potentially disrupt operations.  
**Evidence:**
```yaml
flower:
  ports:
    - "5555:5555"
# No FLOWER_BASIC_AUTH or FLOWER_OAUTH2 setting
```
**Root Cause:** Flower was added for monitoring but auth was not configured. The `mher/flower:2.0` image supports `FLOWER_BASIC_AUTH` env var but it's not set.  
**Fix:** Add `FLOWER_BASIC_AUTH` and bind to `127.0.0.1`, or remove port exposure entirely. See [REMEDIATION_PLAN.md H2](./REMEDIATION_PLAN.md#-high--h2-flower-dashboard-without-authentication).

### H3. Django Service Missing Build Context and Dockerfile `✅ RE-VALIDATED`
**File:** `docker-compose.yml` (production)  
**Impact:** The `django` service has no `build:` directive or `image:` — it will fail to start. `docker compose up` will error.  
**Evidence:**
```yaml
django:
    depends_on:
      pgbouncer:
        condition: service_healthy
    # ... no build: or image: key — this is the ONLY service missing it
```
**Root Cause:** Copy-paste error when splitting services. `celery_worker` and `celery_beat` both have `build: context: ./backend, dockerfile: Dockerfile.django`, but the `django` service was missed. Also note: the Dockerfile path `Dockerfile.django` in celery services may need to be `../infra/docker/Dockerfile.django` depending on how the project is structured.  
**Fix:** Add `build:` directive with correct context and dockerfile path. See [REMEDIATION_PLAN.md H3](./REMEDIATION_PLAN.md#-high--h3-django-service-missing-builddockerfile-directive).

### H4. Next.js Exposed on Port 3000 Without Nginx (Production) `✅ RE-VALIDATED`
**File:** `docker-compose.yml` (production)  
**Impact:** Next.js is directly exposed on port 3000. The production compose should use nginx as the TLS-terminating reverse proxy (as the dev compose does). Without nginx, there's no TLS, no rate limiting at the edge, and no proper header management.  
**Evidence:** Production compose has `nextjs: ports: - "3000:3000"` but no nginx service. Dev compose (`infra/docker/docker-compose.yml`) correctly includes nginx on port 443 with TLS.  
**Context:** This may be intentional if deploying behind a managed load balancer (ALB, Cloudflare, etc.). The compose file should document this assumption.  
**Fix:** Add nginx service or document cloud LB assumption. See [REMEDIATION_PLAN.md H4](./REMEDIATION_PLAN.md#-high--h4-nextjs-exposed-on-port-3000-without-nginx-production).

### H5. No Redis Password in Any Environment `✅ RE-VALIDATED`
**Files:** All docker-compose files, `.env.example`  
**Impact:** All Redis instances (sessions, broker, cache, idempotency) run without authentication. In production, a compromised container or network breach gives full access to session data, task queues, and caches.  
**Evidence:** No `--requirepass` in any Redis command. No `REDIS_PASSWORD` in `.env.example`. Redis URLs use format `redis://host:6379/0` (no auth).  
**Mitigating Factor:** Production uses `backend_net` isolated network, which limits attack surface. But defense-in-depth requires auth.  
**Fix:** Add `--requirepass` to all Redis instances + update all Redis URLs. See [REMEDIATION_PLAN.md H5](./REMEDIATION_PLAN.md#-high--h5-no-redis-password-in-any-environment) (also covered in C3).

### H6. Self-Signed Certificate in Repository `✅ RE-VALIDATED`
**File:** `infra/docker/nginx/certs/server.crt`  
**Impact:** Self-signed cert is committed. For production, use Let's Encrypt or a proper CA. The cert is valid until 2027-04-30 for `localhost` only.  
**Evidence:** `git ls-files` confirms `server.crt` is tracked. Same root cause as C1 — committed before `.gitignore` rules.  
**Fix:** `git rm --cached` along with the private key (C1). Use Let's Encrypt or managed cert for production. See [REMEDIATION_PLAN.md H6](./REMEDIATION_PLAN.md#-high--h6-self-signed-certificate-in-repository).

---

## 🟡 MEDIUM Findings

### M1. No Backup Strategy Defined
**Impact:** PostgreSQL has WAL level set to `replica` (good for replication) but no backup commands, cron jobs, or pg_dump scripts are configured.  
**Fix:** Add a scheduled pg_dump or use WAL archiving with a backup tool (pgBackRest, Barman). Document the backup/restore procedure.

### M2. Celery Tasks Missing Retry Policies
**File:** `backend/config/celery.py`, `backend/config/settings/base.py`  
**Impact:** Beat schedule defines 4 periodic tasks but none specify `retry_policy`, `acks_late`, or `reject_on_worker_lost`. If a worker crashes mid-task, the task may be lost.  
**Fix:** Add `acks_late=True` and retry policies to critical tasks (compliance, sales).

### M3. No DLQ (Dead Letter Queue) Consumer
**File:** `docker-compose.yml`  
**Impact:** Celery worker subscribes to `dlq` queue, but no task routing sends failures there, and no consumer/monitor processes DLQ messages.  
**Fix:** Configure Celery task routes to send failed tasks to DLQ after max retries, and add a DLQ consumer or alerting mechanism.

### M4. `CONN_MAX_AGE: 0` May Hurt Performance
**File:** `backend/config/settings/base.py`  
**Impact:** `CONN_MAX_AGE = 0` means every request opens a new database connection. While correct for PgBouncer transaction mode, this adds latency. PgBouncer 1.23+ supports session mode pooling which could be used instead.  
**Fix:** Document why `CONN_MAX_AGE=0` is required. Consider testing session-mode pooling with PgBouncer for better performance.

### M5. Development Compose Runs Migrations in Entrypoint
**File:** `infra/docker/docker-compose.yml`  
**Impact:** Running `python manage.py migrate` in the container command means multiple replicas would race on migrations. Also, `wait_for_db.py` is referenced but may not exist.  
**Fix:** Run migrations as a separate init container or one-shot job, not in the app entrypoint.

### M6. Missing `.gitignore` Entries
**Impact:** `.env.bak`, `infra/docker/nginx/certs/` (private key), and potentially other sensitive files are tracked.  
**Fix:** Add to `.gitignore`:
```
.env
.env.bak
.env.local
infra/docker/nginx/certs/
*.key
```

### M7. Frontend Dev Dockerfile Uses Node 24 (Non-LTS)
**File:** `infra/docker/Dockerfile.frontend.dev`  
**Impact:** Node 24 is "Current" (not LTS). The production Dockerfile uses Node 22 (LTS). This creates environment parity issues.  
**Fix:** Use Node 22-alpine for both dev and prod Dockerfiles.

### M8. CSP Allows `'unsafe-inline'` for Styles
**File:** `backend/config/settings/base.py`, `production.py`  
**Impact:** `'unsafe-inline'` in `style-src` weakens CSP. While Tailwind JIT requires it, consider using nonces or hashes for stricter policy.  
**Fix:** Implement CSP nonces via django-csp middleware for production.

---

## 🔵 LOW Findings

### L1. Service Worker Caches All Navigation Requests
**File:** `frontend/public/sw.js`  
**Impact:** Network-first strategy is good, but caching all 200 responses indefinitely can serve stale data. No cache expiration is set.  
**Fix:** Add `maxAge` or `maxEntries` limits to the cache, or use `Cache-Control` headers from the server.

### L2. PWA Manifest Missing `maskable` Icons
**File:** `frontend/public/manifest.json`  
**Impact:** No `purpose: "maskable"` icon entries. Android will crop standard icons awkwardly in adaptive icon shapes.  
**Fix:** Add at least one icon with `"purpose": "maskable"` (recommended: 512x512).

### L3. Nginx Config Missing Rate Limiting
**File:** `infra/docker/nginx/nginx.conf`  
**Impact:** No `limit_req_zone` or `limit_conn_zone` directives. The edge proxy doesn't protect against DDoS or brute force at the nginx layer.  
**Fix:** Add rate limiting zones for `/api/` endpoints.

### L4. No `STRICT_TRANSPORT_SECURITY` Preload in Nginx
**File:** `infra/docker/nginx/nginx.conf`  
**Impact:** HSTS header is set but missing `preload` directive for HSTS preload list submission.  
**Fix:** Change to: `add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;`

---

## ✅ Positive Findings

1. **Non-root containers** — All Dockerfiles create and switch to non-root users (`wellfond`, `nextjs`). ✅
2. **Multi-stage builds** — Production Dockerfiles use builder → runtime stages, reducing image size and attack surface. ✅
3. **Healthchecks on all services** — Every service in both compose files has healthchecks with appropriate intervals. ✅
4. **Network isolation** — Production uses `backend_net` and `frontend_net` split networks. ✅
5. **PgBouncer transaction pooling** — Correctly configured with `CONN_MAX_AGE=0`. ✅
6. **Split Redis instances** — Sessions, broker, cache, and idempotency are on separate Redis instances with appropriate eviction policies. ✅
7. **Security headers** — Django and Next.js both set X-Frame-Options, X-Content-Type-Options, CSP, HSTS. ✅
8. **CI/CD pipeline** — Comprehensive with linting, type checking, unit tests, Trivy vulnerability scanning, Playwright E2E tests, and Codecov integration. ✅
9. **Environment validation** — Production settings fail loud on missing `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`. ✅
10. **Proper session security** — HttpOnly, SameSite=Lax, Secure (in prod) cookies. ✅
11. **Trivy security scanning** — Both in Dockerfiles (as a stage) and in CI pipeline. ✅
12. **BFF pattern** — Next.js acts as backend-for-frontend, hiding Django from the browser. `BACKEND_INTERNAL_URL` is correctly kept server-side. ✅

---

## Priority Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| 1 | Rotate and remove TLS private key from repo | 1h |
| 2 | Add Redis passwords to all environments | 30min |
| 3 | Fix missing `build:`/`image:` on production Django service | 15min |
| 4 | Add Flower authentication | 15min |
| 5 | Remove PgBouncer host port exposure | 5min |
| 6 | Add nginx to production compose with TLS | 2h |
| 7 | Add `.gitignore` entries for secrets | 5min |
| 8 | Add Celery retry policies and DLQ consumer | 1h |
| 9 | Document backup strategy | 1h |
| 10 | Align Node.js versions across dev/prod | 15min |
