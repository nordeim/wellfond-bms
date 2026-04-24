# Phase 9: Observability, Security & Production Readiness — Sub-Plan

**Target:** 5–7 days | **Dependencies:** Phase 0–8 | **Status:** ⬜ Not Started

**Success Criteria:** Zero critical CVEs. OTel traces flow. Load test passes. Runbooks complete. Sign-off ready.

---

## Execution Order

```
Step 1: Backend observability (otel.py)
Step 2: Frontend observability (instrumentation.ts)
Step 3: Load tests (k6.js)
Step 4: Documentation (RUNBOOK, SECURITY, DEPLOYMENT, API)
Step 5: Scripts (backup.sh)
Step 6: Nginx (optional, nginx.conf)
Step 7: Final QA pass
```

---

## File-by-File Specifications

### Step 1: Backend Observability

| File | Key Content | Done |
|------|-------------|------|
| `backend/config/otel.py` | `init_otel(service_name)`: configure OpenTelemetry SDK. Auto-instrument: Django (`opentelemetry-instrumentation-django`), psycopg2 (`opentelemetry-instrumentation-psycopg2`), Celery (`opentelemetry-instrumentation-celery`). Custom spans: `calc_coi` (attributes: dam_id, sire_id, coi_pct), `generate_nparks` (attributes: entity, month, doc_count), `render_agreement_pdf` (attributes: agreement_id, page_count). Metrics: `http_request_duration_seconds` (histogram), `celery_task_duration_seconds`, `db_query_duration_seconds`, `queue_depth` (gauge). Prometheus exporter endpoint: `/metrics`. Structured JSON logging: `python-json-logger`. | ☐ |

### Step 2: Frontend Observability

| File | Key Content | Done |
|------|-------------|------|
| `frontend/instrumentation.ts` | `register()`: Next.js instrumentation hook. Init OTel with `OTLPTraceExporter`. Trace BFF→Django chain (propagate trace context in headers). `onRequestError(error, request)`: report to OTel + Sentry (if `NEXT_PUBLIC_SENTRY_DSN` set). Web Vitals: LCP, FID, CLS → OTel metrics. CSP violation reporting: `report-uri` handler. | ☐ |

### Step 3: Load Tests

| File | Key Content | Done |
|------|-------------|------|
| `tests/load/k6.js` | **Scenarios**: `auth_flow`: login → fetch /auth/me → logout. `dog_list`: GET /dogs/ with filters (483 records). `mate_check`: POST /breeding/mate-check (known pair). `nparks_gen`: POST /compliance/nparks/generate. `blast_dispatch`: POST /customers/blast (50 recipients). **Config**: 50 VUs, 5min duration, ramp up 0→50 in 1min. **Thresholds**: `http_req_duration{p(95)<2000}` (dashboard), `http_req_duration{p(95)<500}` (COI), `http_req_duration{p(95)<3000}` (NParks), `http_req_failed<0.01` (zero 5xx). Tags per scenario. | ☐ |

### Step 4: Documentation

| File | Key Content | Done |
|------|-------------|------|
| `docs/RUNBOOK.md` | **Operations Guide**: Deploy procedure (docker compose pull → up). Scale Celery workers (add replicas). PgBouncer tuning (pool_size, max_client_conn). Celery DLQ recovery (inspect → retry → purge). WAL-G PITR restore (wal-g backup-fetch → pg_ctl start). SSE reconnect handling. PWA cache clear (bump version in sw.ts). Incident response (who to page, escalation). Common errors + fixes. | ☐ |
| `docs/SECURITY.md` | **Security Documentation**: Threat model (external: XSS/SSRF/CSRF, internal: privilege escalation/data leakage). CSP policy (directives listed). PDPA compliance proof (consent flow, hard filter, audit log). OWASP Top 10 mitigations (each mapped to implementation). Audit log access policy (who can read, retention). BFF proxy security (allowlist, header stripping). Penetration test results (if available). | ☐ |
| `docs/DEPLOYMENT.md` | **Deployment Guide**: Prerequisites (Docker, domain, SSL cert). Environment variables (all listed with descriptions). Docker Compose production setup. SSL/TLS configuration (Let's Encrypt / Cloudflare). Domain config (DNS records). Backup schedule (WAL-G daily, full weekly). Monitoring setup (Prometheus + Grafana). Scaling guide (horizontal: Celery replicas, vertical: PG memory). | ☐ |
| `docs/API.md` | **API Documentation**: Auto-generated from OpenAPI schema. Authentication (cookie flow, CSRF). Rate limits (10/sec for blast, 100/sec general). Error codes (400/401/403/404/422/500/503). Examples for each endpoint group (dogs, breeding, sales, compliance, customers, finance). Webhook formats (if any). | ☐ |

### Step 5: Scripts

| File | Key Content | Done |
|------|-------------|------|
| `scripts/backup.sh` | WAL-G backup wrapper. `wal-g backup-push` (full backup). `wal-g wal-push` (WAL archiving). Cron: daily 2am SGT. Destination: S3/R2 bucket. PITR procedure: `wal-g backup-fetch LATEST` → `pg_ctl start -t recovery`. Verification: `wal-g backup-list`. | ☐ |

### Step 6: Nginx (Optional)

| File | Key Content | Done |
|------|-------------|------|
| `nginx/nginx.conf` | TLS termination (port 443 → Next.js 3000). Proxy pass to Next.js. Static file serving (cached 30d). Rate limiting (100 req/sec per IP). CSP headers (inherited from Django). Gzip compression. Access logging. | ☐ |

### Step 7: Final QA Pass

| Check | Procedure | Done |
|-------|-----------|------|
| Trivy scan | `trivy image wellfond-django:latest --severity HIGH,CRITICAL` → 0 findings | ☐ |
| Trivy scan FE | `trivy image wellfond-nextjs:latest --severity HIGH,CRITICAL` → 0 findings | ☐ |
| CSP test | Inject `<script>alert(1)</script>` → browser blocks, console reports violation | ☐ |
| OTel traces | Send request → check Grafana for trace waterfall (BFF→Django→PG) | ☐ |
| OTel metrics | Check Prometheus for `http_request_duration_seconds`, `celery_task_*` | ☐ |
| k6 load test | `k6 run tests/load/k6.js` → all thresholds pass | ☐ |
| WAL-G PITR | Restore to test instance → verify data integrity | ☐ |
| PWA Lighthouse | `lighthouse http://localhost:3000 --preset=pwa` → score ≥90 | ☐ |
| Full E2E | Playwright: login → create dog → mate check → sales agreement → NParks gen | ☐ |
| All tests | `pytest` → all pass. `vitest run` → all pass. | ☐ |

---

## Phase 9 Validation Checklist

### Security
- [ ] Trivy: 0 critical/high CVEs on both Docker images
- [ ] CSP: blocks `eval()`, inline scripts, unauthorized origins
- [ ] CSP: `report-only=false` (enforced, not just monitored)
- [ ] BFF: non-allowlisted paths return 403
- [ ] BFF: `NEXT_PUBLIC_API_BASE` not in any env file
- [ ] PDPA: blast to opted-out customer → 0 delivered
- [ ] AuditLog: try UPDATE → error (immutable)
- [ ] PDF hash: re-download → hash matches (tamper-evident)

### Observability
- [ ] OTel: traces flow to collector (verify in Grafana)
- [ ] OTel: custom spans (COI, NParks, PDF) appear
- [ ] OTel: metrics (request duration, task duration, queue depth) export
- [ ] Logging: structured JSON to stdout (parseable)
- [ ] Sentry: frontend errors captured (if DSN configured)

### Performance
- [ ] k6: dashboard p95 <2s
- [ ] k6: COI p95 <500ms
- [ ] k6: NParks p95 <3s
- [ ] k6: SSE delivery <500ms
- [ ] k6: zero 5xx errors
- [ ] PWA: Lighthouse score ≥90

### Disaster Recovery
- [ ] WAL-G: backup runs successfully
- [ ] WAL-G: PITR restore to test instance → data intact
- [ ] Runbook: procedures tested and accurate

### Sign-Off
- [ ] Architecture Lead: approved
- [ ] Compliance Officer: approved
- [ ] DevOps Lead: approved
- [ ] Product Owner: approved
