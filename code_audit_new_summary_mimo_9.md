## Summary of Findings

**Overall: Production-ready with minor remediation needed.**

### High-Severity (3):
1. **H-01**: Import ordering bug in `alerts.py` — `models.Q` used before `from django.db import models` import (fragile, works at runtime but violates conventions)
2. **H-02**: Finance router uses unimported `date` name — `date.today()` called in 4 places but only `import datetime` is present → `NameError` at runtime on `/finance/pnl` and `/finance/gst` endpoints when no month/quarter param passed
3. **H-03**: `SESSION_COOKIE_SECURE` not set in base settings (defaults to False, only True in production.py)

### Medium-Severity (4):
- Sales router `require_entity_access` called as bare function instead of decorator
- Django Dockerfile defaults to development settings
- NParksSubmission save has extra DB query
- alerts.py import at bottom of file

### Key Positive Findings:
- **BFF proxy**: Properly hardened with path allowlist, traversal protection, header stripping, edge runtime removed
- **Entity scoping**: Consistently applied across all routers via `scope_entity()`
- **PDPA**: Centralized filtering, immutable consent logs, no PII on non-consent models
- **Compliance determinism**: Zero AI/LLM imports in compliance/finance paths
- **Immutable audit trails**: Properly implemented with `ImmutableManager` and `_state.adding` checks
- **CSP**: Clean django-csp v4 dict format, no legacy `CSP_*` settings
- **Pydantic v2**: Correct `model_validate()` and `from_attributes=True` usage throughout
- **Async patterns**: `sync_to_async(thread_sensitive=True)` correctly used for SSE and COI
- **Test infrastructure**: `authenticate_client()` replaces broken `force_login()` pattern

---

Let me meticulously re-validate each High finding by re-reading the exact code.Now let me verify the sales router issue (M-01) more carefully:Let me also verify the sales entity access issue more precisely:Now I have all the data I need. Let me create the comprehensive remediation plan:Now let me update the main audit report to reflect the re-validated findings:Let me do a final consistency check:Done. Here's the re-validation summary:

## Re-Validation Results

### Confirmed High (2 findings):

**H-01 — Finance Router `NameError` (CRITICAL BUG)**
- **Root cause**: `import datetime` on line 16, but `date.today()` used bare on lines 76, 129, 155, 159
- **Impact**: `GET /finance/pnl` and `GET /finance/gst` crash with 500 when called without explicit params
- **Fix**: One line — add `from datetime import date` to import block

**H-02 — SESSION_COOKIE_SECURE Missing**
- **Root cause**: Only set in `production.py`, base defaults to `False`
- **Fix**: One line — `SESSION_COOKIE_SECURE = not DEBUG` in `base.py`

### Confirmed Medium (2 findings):

**M-01 — Sales Router Entity Access Gap**
- **Root cause**: `require_entity_access(request)` is a decorator called as a bare function — creates and discards a wrapper, does nothing
- **Impact**: Non-management user could create agreement for wrong entity
- **Fix**: Replace with explicit `if user.entity_id != data.entity_id: raise 403`

**M-02 — Alerts Import Ordering (Downgraded from High)**
- **Re-validation**: NOT a runtime error. Module-level import at line 243 is available when function is called. Code quality issue only.

### Files Created:
- `COMPREHENSIVE_CODE_REVIEW_AUDIT_REPORT_8.md` — Updated with re-validated findings
- `REMEDIATION_PLAN_mimo-8.md` — 4 fixes with exact code changes, verification steps, and testing strategy
