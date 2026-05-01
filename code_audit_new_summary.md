Here's a summary of findings:

## Key Findings Summary

### 🔴 3 Critical Issues
1. **C1**: NParks `_generate_puppy_movement` references non-existent `line_total` property — will crash at runtime
2. **C2**: NParks `_generate_vet_treatments` references non-existent `follow_up_required` field — will crash at runtime  
3. **C3**: Offline queue uses `localStorage` instead of IndexedDB — Service Workers can't access `localStorage`, breaking PWA background sync

### 🟠 1 High Issues
- **H1**: Idempotency middleware has TOCTOU race condition (not atomic)
- **H2**: `cancel_agreement` audit log records wrong `old_status` (post-save state)
- **H3**: PDPA `check_blast_eligibility` and `is_consented` are placeholder stubs returning `True` — compliance gap
- **H4**: BFF proxy CORS allows `*` origin with credentials
- **H5**: Sessions stored in default cache (LRU eviction risk) instead of dedicated sessions cache
- **H6-H11**: N+1 queries, API contract violations, missing model properties, silent error catches, transaction atomicity issues

### ✅ Positive Findings
- BFF security pattern correctly implemented (HttpOnly cookies, SSRF protection, path allowlist)
- Entity scoping consistently applied across all routers
- Middleware order correct (Django auth before custom auth)
- Audit log immutability properly enforced
- COI calculation with Wright's formula well-implemented
- GST uses `Decimal` with `ROUND_HALF_UP` (IRAS compliant)
- Closure table uses Celery rebuild (no DB triggers per v1.1)

### 📊 Coverage
- **Backend estimated coverage:** ~65% (target: ≥85%)
- **Frontend estimated coverage:** ~30% (needs expansion)
- **Phases 0-8:** Claimed complete, but NParks (Phase 6) has runtime bugs and PDPA (Phase 6) has placeholder stubs

---

Let me re-validate each Critical and High issue against the actual source code with surgical precision before creating the remediation plan.Now let me verify the `Vaccination.save()` issue more carefully — the `except ImportError` pattern:All issues validated with surgical precision. Now creating the comprehensive remediation plan.The comprehensive remediation plan has been created at `REMEDIATION_PLAN_mimo.md`.

Here's a summary of the re-validation and remediation:

## Re-Validation Results

All 14 issues (3 Critical + 1 High) were re-validated against the actual source code with exact file:line references. **Every issue is confirmed as a real bug.**

### Key Re-Validation Discoveries

1. **C1 + H8 are the same root cause** — `AgreementLineItem` model lacks `line_total` and `gst_amount` properties. The test factory defines them as mock attributes, but the actual model doesn't have them. Adding two `@property` methods to the model fixes both issues at once.

2. **H2 is definitively confirmed** — In `cancel_agreement()`, line 590 sets `agreement.status = CANCELLED`, line 592 saves it, then line 597 reads `agreement.status` for the audit log — which is already `CANCELED`. The fix is trivial: capture `old_status` before mutation.

3. **H3 is a compliance gap** — The `Customer` model exists (Phase 7 complete), but `PDPAService.is_consented()` still returns `True` for everyone. This is a 15-minute fix.

4. **C3 has a ready-made solution** — The IndexedDB implementation already exists at `frontend/lib/offline-queue/`. The root `offline-queue.ts` just needs to re-export from it.

## Remediation Plan Structure

| Phase | Issues | Time | Focus |
|-------|--------|------|-------|
| **Phase 1** | C1, C2, C3 | 30 min | Critical — runtime crashes + broken PWA |
| **Phase 2** | H2, H3, H10 | 30 min | Data integrity — audit + compliance + finance |
| **Phase 3** | H1, H4, H5, H7, H9 | 45 min | Security + correctness |
| **Phase 4** | H6 | 30 min | Performance |
| **Phase 5** | Verification | 30 min | End-to-end testing |

**Total estimated fix time: ~2.5 hours**

Each fix includes:
- Root cause with exact file:line reference
- Before/after code comparison
- Migration scripts where needed
- Verification test cases
- Rollback strategy
- Breaking change risk assessment

