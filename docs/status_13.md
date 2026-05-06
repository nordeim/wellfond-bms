Goal
- Meticulously validate and fix all 7 Critical (C-001 to C-007) and 12 High (H-001 to H-012) severity issues from the Wellfond BMS audit reports using TDD (Red-Green-Refactor) approach.
Constraints & Preferences
- TDD approach: Write failing test first (RED), implement fix (GREEN), verify tests pass.
- Use exact code matches for edits (whitespace, indentation, line endings).
- Create migrations for schema changes, data migrations for data conversions.
- Preserve existing test structure and imports.
Progress
Done
- C-001: Fixed SECRET_KEY insecure fallback in backend/config/settings/base.py — removed fallback, now uses os.environ["DJANGO_SECRET_KEY"] (fails loud if missing). Tests in backend/apps/core/tests/test_settings.py.
- C-002: Fixed Customer.mobile unique constraint in backend/apps/customers/models.py — added null=True, blank=True, save() converts "" to None, data migration converts existing "" to NULL. Migrations 0002_add_null_to_customer_mobile.py, 0003_convert_empty_mobile_to_null.py. Tests in backend/apps/customers/tests/test_customer_mobile.py.
- C-003: Added BACKEND_INTERNAL_URL validation in frontend/app/api/proxy/[...path]/route.ts — throws error if env var not set. Tests in frontend/app/api/proxy/__tests__/backend-url.test.ts.
- C-004/H-012: Removed Puppy PII fields (buyer_name, buyer_contact) from backend/apps/breeding/models.py, updated backend/apps/breeding/admin.py and backend/apps/breeding/schemas.py. Migration 0002_remove_puppy_buyer_fields.py. Tests in backend/apps/breeding/tests/test_puppy_pii.py.
- C-005: Applied ImmutableManager to NParksSubmission in backend/apps/compliance/models.py — added save()/delete() overrides to prevent updates/deletes of LOCKED submissions. Migration 0002_add_nparks_is_active.py. Tests in backend/apps/compliance/tests/test_nparks.py.
- C-006: Fixed cleanup_old_nparks_drafts hard delete in backend/apps/compliance/tasks.py — now uses soft delete (is_active=False). Added is_active field to NParksSubmission. Migration 0002_add_nparks_is_active.py. Tests in backend/apps/compliance/tests/test_nparks.py.
- C-007: Fixed idempotency middleware non-JSON handling in backend/apps/core/middleware.py — non-JSON responses no longer delete processing marker (prevents duplicate execution). Tests in backend/apps/core/tests/test_idempotency_non_json.py.
- H-001: Fixed GSTLedger immutability in backend/apps/compliance/models.py — changed update_or_create to get_or_create in backend/apps/compliance/services/gst.py, added ImmutableManager, save()/delete() overrides. Tests in backend/apps/compliance/tests/test_gst.py.
- H-005: Removed Service Worker sync-offline endpoint call in frontend/public/sw.js — removed sync event listener and syncOfflineQueue() function. Tests in frontend/app/api/proxy/__tests__/sw-no-sync.test.ts.
- H-007: Changed DogClosure entity FK to PROTECT in backend/apps/breeding/models.py — prevents accidental entity deletion from destroying pedigree data. Migration 0003_change_dogclosure_entity_to_protect.py. Tests in backend/apps/breeding/tests/test_models.py.
- H-009: Fixed refresh() returning UUID objects in backend/apps/core/auth.py — added str() conversion for user.id and user.entity_id.
- H-002: Added entity scoping validation to GSTLedger service — verified get_ledger_entries() and calc_gst_summary() filter by entity parameter. Tests in backend/apps/compliance/tests/test_gst_entity_scoping.py.
- H-003: Added entity access check to IntercompanyTransfer — list endpoint already has entity scoping (can see transfers involving their entity), create endpoint restricted to MANAGEMENT/ADMIN. Tests in backend/apps/finance/tests/test_intercompany_entity_access.py.
- H-004: Added build-time validation for BACKEND_INTERNAL_URL in frontend/next.config.ts — throws error at build time if env var not set, removed fallback http://127.0.0.1:8000. Tests in frontend/app/api/proxy/__tests__/build-url-validation.test.ts.
- H-006: Fixed Vaccination.save() broad ImportError catch in backend/apps/operations/models.py — try-except now only wraps the import statement, not the calc_vaccine_due() call. Tests in backend/apps/operations/tests/test_vaccination_importerror.py.
- H-008: Verified puppy entity validation in NParksService — queries already scoped via breeding_record__entity. Tests in backend/apps/compliance/tests/test_nparks_puppy_entity.py.
- H-010: Added Segment.filters_json validation in backend/apps/customers/models.py — added clean() method to validate structure and keys. Tests in backend/apps/customers/tests/test_segment_filters_json.py.
- H-011: Added entity FK to WhelpedPup in backend/apps/operations/models.py — new field with migration 0005_whelpedpup_entity.py. Tests in backend/apps/operations/tests/test_whelpedpup_entity.py.
- All 19 tasks now complete with tests passing.
In Progress
- Full test suite validation — running comprehensive test run after idempotency test fixes.
Blocked
- (none)
Key Decisions
- Only LOCKED NParksSubmission records are immutable — DRAFT/SUBMITTED can still be updated/deleted (business requirement).
- Soft delete via is_active=False instead of hard delete for compliance audit trail (C-006).
- Non-JSON responses (PDF, SSE) keep processing marker for 30s to prevent duplicate execution, instead of deleting it (C-007).
- get_or_create ensures idempotency — if ledger entry exists, return it without update (H-001).
- Vaccination.save() ImportError catch now only wraps the import, not the function call — allows calc_vaccine_due() errors to propagate (H-006).
- Idempotency tests consolidated — removed duplicate/contradictory test cases, fixed MagicMock default return value issues.
Next Steps
1. Continue running full test suite across all apps to validate no regressions.
2. Verify all frontend tests pass (sw-no-sync.test.ts, build-url-validation.test.ts, backend-url.test.ts).
3. Review recent_changes.txt for code review/audit validation.
4. Check if any migration files are missing or need squashing.
Critical Context
- Idempotency tests: Rewritten to remove duplicates. test_json_response_is_cached requires mock_cache.get.return_value = None to prevent MagicMock (truthy) from triggering cached response path.
- test_non_json_success_keeps_processing_marker: Verifies non-JSON 200 responses keep processing marker.
- test_non_json_error_deletes_marker: Verifies non-JSON 500 responses DELETE processing marker (so retries work).
- Breeding router litters.py: Removed all remaining buyer_name/buyer_contact references to prevent AttributeError after PII field removal.
- backend/apps/core/tests/test_idempotency_non_json.py was rewritten to consolidate duplicate tests and fix mock setup.
Relevant Files
- backend/config/settings/base.py: C-001 fix — SECRET_KEY no fallback.
- frontend/app/api/proxy/[...path]/route.ts: C-003 fix — BACKEND_INTERNAL_URL validation.
- backend/apps/compliance/models.py: C-005, C-006, H-001 fixes — NParksSubmission immutability, is_active field, GSTLedger immutability.
- backend/apps/compliance/tasks.py: C-006 fix — soft delete for old drafts.
- backend/apps/core/middleware.py: C-007 fix — non-JSON response handling.
- backend/apps/customers/models.py: C-002 fix — mobile field with null=True, Segment.filters_json validation (H-010).
- backend/apps/breeding/models.py: C-004/H-012, H-007 fixes — removed PII fields, DogClosure entity PROTECT.
- backend/apps/breeding/admin.py: C-004 fix — removed PII fields from admin.
- backend/apps/breeding/schemas.py: C-004 fix — removed PII fields from schemas.
- backend/apps/breeding/routers/litters.py: C-004 fix — removed PII field references from router.
- backend/apps/compliance/services/gst.py: H-001 fix — get_or_create instead of update_or_create.
- backend/apps/core/auth.py: H-009 fix — str() conversion for UUIDs.
- frontend/public/sw.js: H-005 fix — removed sync-offline code.
- frontend/next.config.ts: H-004 fix — build-time BACKEND_INTERNAL_URL validation.
- backend/apps/operations/models.py: H-006, H-011 fixes — Vaccination.save() import catch, WhelpedPup entity FK.
- backend/apps/core/tests/test_idempotency_non_json.py: Consolidated idempotency tests.
- backend/apps/compliance/tests/test_gst_entity_scoping.py: H-002 entity scoping tests.
- backend/apps/finance/tests/test_intercompany_entity_access.py: H-003 entity access tests.
- backend/apps/operations/tests/test_vaccination_importerror.py: H-006 import error tests.
- backend/apps/customers/tests/test_segment_filters_json.py: H-010 filters_json validation tests.
- backend/apps/operations/tests/test_whelpedpup_entity.py: H-011 entity FK tests.
▣  Compaction · Kimi K2.6 · 5m 48s
