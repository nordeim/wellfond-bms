Critical Issues (8):
1. Authentication Bypass - require_role decorator relies on request.user instead of reading session cookie directly
2. Missing Entity Scoping - COI service SQL doesn't filter by entity, allowing cross-entity data access
3. Hardcoded GST Logic - Thomson GST exemption uses hardcoded name instead of gst_rate field
4. XSS Vulnerability - PDF template renders user inputs without escaping
5. Missing CSRF Protection - BFF proxy doesn't validate CSRF tokens
6. CORS Misconfiguration - * origin with credentials is a security vulnerability
7. Session Fixation - No session regeneration on login
8. Async/Sync Mismatch - SSE stream uses inconsistent database connection handling
High Priority (14):
- Debug decorator in production code
- Missing rate limiting on auth endpoints
- Insecure token generation (uuid4 vs secrets)
- Missing permission checks in NParks service
- Cache key collisions
- Weight field too small for large breeds
- Race conditions in offline queue
- And more...
Medium Priority (22):
- Various configuration issues, performance concerns, and edge cases
Low Priority (12):
- Code style issues, documentation gaps
The comprehensive audit report has been saved to /home/project/wellfond-bms/CODEBASE_AUDIT_REPORT.md. This report includes detailed findings, remediation steps, and a priority
I've completed a comprehensive code review and audit of the Wellfond BMS codebase. The detailed assessment report has been saved to /home/project/wellfond-bms/CODEBASE_AUDIT_REPORT.md.
Summary of Findings
Severity	Count	Key Issues
🔴 Critical	8	Auth bypass, entity scoping gaps, XSS, CORS misconfig, session fixation
🟠 High	14	Debug code in prod, missing rate limits, insecure tokens, race conditions
🟡 Medium	22	Caching, validation, configuration issues
🟢 Low	12	Code style, documentation
Top Critical Issues
1. Authentication Bypass (permissions.py:30) - require_role decorator relies on request.user instead of reading session cookie directly as required by AGENTS.md
2. Missing Entity Scoping (coi.py:61) - COI calculation SQL doesn't filter by entity, allowing cross-entity data leakage
3. Hardcoded GST Logic (agreement.py:66) - Thomson GST exemption uses hardcoded name instead of gst_rate field on Entity model
4. XSS in PDF Generation (pdf.py:83) - User inputs rendered into HTML without escaping
5. CORS Misconfiguration (route.ts:200) - Access-Control-Allow-Origin: '*' with credentials enabled
6. Async/Sync Mismatch (stream.py:165) - Inconsistent database connection handling in SSE streams
Gaps vs Planning Documents
- ✅ Idempotency cache properly implemented
- ✅ Closure table uses Celery (no triggers)
- ⚠️ SSE async/sync inconsistent
- ❌ GST calculation hardcoded instead of using entity field
- ❌ Missing rate limiting
- ❌ Proxy missing CSRF validation
Recommended Actions
Week 1 (Critical):
- Fix authentication bypass in role decorator
- Add entity scoping to COI service
- Fix GST calculation to use entity.gst_rate
- XSS protection in PDF templates
- Fix async/sync in SSE stream
Week 2 (High):
- Remove debug decorator
- Add rate limiting on auth endpoints
- Secure AVS token generation
- Fix CORS configuration
- Migrate offline queue to IndexedDB
The full report includes code snippets, remediation recommendations, and testing checklists for each finding.

