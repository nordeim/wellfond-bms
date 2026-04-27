please meticulously review and analyze @draft_plan.md , @IMPLEMENTATION_PLAN.md , @README.md , @plans/phase-0-infrastructure.md , @plans/phase-1-auth-bff-rbac.md , @plans/phase-2-domain-foundation.md and @plans/phase-3-ground-operations.md to have a deep understanding of the WHAT, WHY and HOW of the project and its codebase design and architecture, then meticulously do a systematic code review and audit of the current codebase to identify any issues, gaps and bugs. then create a comprehensive assessment analysis report of the current state of the codebase, highlighting any issues, gaps and bugs, and add your observations, conclusions and recommendations based on your deep analysis of the project documents and deep validation of the codebase to establish the ground truth.

---

please meticulously review and analyze @draft_plan.md , @IMPLEMENTATION_PLAN.md , @README.md , @plans/phase-0-infrastructure.md , @plans/phase-1-auth-bff-rbac.md , @plans/phase-2-domain-foundation.md , @plans/phase-3-ground-operations.md and @plans/phase-4-breeding-genetics.md to have a deep understanding of the WHAT, WHY and HOW of the project and its codebase design and architecture, then meticulously do a systematic code review and audit of the current codebase to identify any issues, gaps and bugs. then create a comprehensive assessment analysis report of the current state of the codebase, highlighting any issues, gaps and bugs, and add your observations, conclusions and recommendations based on your deep analysis of the project documents and deep validation of the codebase to establish the ground truth.

---

Awesome meticulous review, analysis and planning. Please keep up the good work. now, please meticulously review @ACCOMPLISHMENTS.md , @CLAUDE.md and @AGENTS.md , then systematically and critically validate them against the current codebase to check for their accurate alignment.

---

awesome meticulous job so far. please keep up the good work. please meticulously plan to validate the following findings against the actual codebase again to confirm them and to identify optimal proper fix without affecting overall application functionality. then meticulously plan to create a remeditation plan to apply the validated optimal fixes identified. review and validate the remediation plan against the codebase to ensure correct alignment before executing it meticulously. use TDD approach to make code changes. 

## High-Severity Findings

### HIGH-001: Empty Stub Apps in INSTALLED_APPS
5 apps (sales, compliance, customers, finance, ai_sandbox) are registered but empty.
- **Fix:** Remove from INSTALLED_APPS until implemented, or add NotImplemented safeguards
### HIGH-002: CHA YUAN Legacy Contamination
- `infra/docker/pg_hba.conf` — chayuan_db entries
- `backend/.env.example` — entirely CHA YUAN branded
- **Fix:** Remove CHA YUAN references; delete backend/.env.example
### HIGH-003: Missing use-auth.ts Hook
Plan specifies hooks/use-auth.ts. Auth logic is in lib/auth.ts (not React-aware).
- **Fix:** Create use-auth.ts wrapper with React hooks (useCurrentUser, useLogin, useLogout)
### HIGH-004: Missing lib/offline-queue.ts Module
Plan specifies dedicated IndexedDB module. Offline queue absorbed into React hook.
- **Fix:** Extract framework-agnostic queueLog/flushQueue into lib/offline-queue.ts
### HIGH-005: Test File Location Split
Tests in both /tests/ (root) and backend/apps/*/tests/. Different configs.
- **Fix:** Consolidate all Django tests into backend/apps/*/tests/ 
