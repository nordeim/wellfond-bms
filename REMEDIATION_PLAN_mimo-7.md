I've re-evaluated all 7 Critical (C-001–C-007) and 12 High (H-001–H-012) issues to confirm root causes and define optimal fixes. Below is the structured remediation plan, prioritized by severity.
🔴 Critical Issues Remediation
---
C-001: Django SECRET_KEY Insecure Fallback
- Root Cause: base.py has a hardcoded dev fallback ("dev-only-change-in-production") that activates if DJANGO_SECRET_KEY is unset. Even if production.py validates, misconfigurations can silently use the insecure key.
- Optimal Fix: Remove the fallback entirely to fail loudly if the env var is missing.
- Affected Files: backend/config/settings/base.py
- Implementation:
  1. Replace line 13 in base.py:
          # Before:
     SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-in-production")
     # After:
     SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # No fallback — fails if unset
       2. Verify production.py already validates DJANGO_SECRET_KEY at startup (confirmed per AGENTS.md).
- Verification:
  - Run grep -r "dev-only-change-in-production" backend/ → No matches.
  - Unset DJANGO_SECRET_KEY and run python manage.py check → Raises KeyError.
---
C-002: Customer.mobile Unique Constraint Collision
- Root Cause: unique=True without null=True means empty strings ("") are stored as valid unique values, but multiple "" entries violate the unique constraint.
- Optimal Fix: Add null=True (PostgreSQL treats NULL as non-equal, allowing multiple NULL values) and migrate existing "" to NULL.
- Affected Files: backend/apps/customers/models.py, new migration.
- Implementation:
  1. Update line 57 in customers/models.py:
          # Before:
     mobile = models.CharField(max_length=20, unique=True, db_index=True)
     # After:
     mobile = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)
       2. Create a data migration to convert existing "" to NULL:
          python manage.py makemigrations customers --empty
          Edit the empty migration to add:
          def update_mobile(apps, schema_editor):
         Customer = apps.get_model("customers", "Customer")
         Customer.objects.filter(mobile="").update(mobile=None)
     operations = [migrations.RunPython(update_mobile)]
       3. Generate schema migration: python manage.py makemigrations customers
  4. Apply: python manage.py migrate
- Verification:
  - Create two customers with no mobile → Succeeds (both have NULL mobile).
  - Create a customer with a duplicate mobile → Raises IntegrityError.
---
C-003: BFF Proxy No BACKEND_INTERNAL_URL Validation
- Root Cause: route.ts falls back to http://127.0.0.1:8000 if the env var is unset, with no startup validation.
- Optimal Fix: Add module-load validation to throw an error if the env var is missing, and remove the fallback.
- Affected Files: frontend/app/api/proxy/[...path]/route.ts
- Implementation:
  1. Replace lines 17-18 in route.ts:
          // Before:
     const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
     // After:
     const BACKEND_URL = process.env.BACKEND_INTERNAL_URL;
     if (!BACKEND_URL) {
       throw new Error('BACKEND_INTERNAL_URL is required and must be set');
     }
       2. Confirm docker-compose.yml sets BACKEND_INTERNAL_URL: http://django:8000 for the nextjs service (line 247).
- Verification:
  - Start the frontend without BACKEND_INTERNAL_URL → Throws error at module load.
---
C-004 & H-012: Puppy PII Fields Bypass PDPA
- Root Cause: Puppy has buyer_name/buyer_contact (PII) without pdpa_consent, so scope_entity() never filters them. These fields duplicate data already stored in SalesAgreement (which has PDPA checks).
- Optimal Fix: Remove the PII fields from Puppy and access buyer info exclusively via SalesAgreement joins.
- Affected Files: backend/apps/breeding/models.py, any serializers/views using these fields.
- Implementation:
  1. Remove lines 289-290 in breeding/models.py:
          # Delete these lines:
     buyer_name = models.CharField(max_length=100, blank=True, help_text="Buyer's name")
     buyer_contact = models.CharField(max_length=100, blank=True, help_text="Buyer's contact")
       2. Generate migration: python manage.py makemigrations breeding --name remove_puppy_buyer_fields
  3. Search for references: grep -r "buyer_name\|buyer_contact" backend/ → Update serializers/views to fetch buyer info via SalesAgreement:
          # Example replacement in a serializer:
     buyer_name = serializers.CharField(source='sales_agreement.buyer_name', read_only=True)
       4. Apply migration: python manage.py migrate
- Verification:
  - grep -r "buyer_name\|buyer_contact" backend/apps/breeding/ → No matches.
  - Access puppy data → Buyer info only available via SalesAgreement with PDPA filtering.
---
C-005: NParksSubmission Lacks Immutability
- Root Cause: Unlike AuditLog/PDPAConsentLog/CommunicationLog, NParksSubmission does not use ImmutableManager and has no save()/delete() overrides.
- Optimal Fix: Apply the same ImmutableManager pattern used in other audit models.
- Affected Files: backend/apps/compliance/models.py
- Implementation:
  1. Add ImmutableManager to NParksSubmission (after line 41):
          objects = ImmutableManager()
       2. Add save() and delete() overrides:
          def save(self, *args, **kwargs):
         if not self._state.adding:
             raise ValueError("NParksSubmission is immutable - cannot update")
         super().save(*args, **kwargs)
     def delete(self, *args, **kwargs):
         raise ValueError("NParksSubmission is immutable - cannot delete")
       3. Generate migration: python manage.py makemigrations compliance --name add_nparks_immutable
  4. Apply: python manage.py migrate
- Verification:
  - Try to update an existing NParksSubmission → Raises ValueError.
  - Try to delete → Same.
---
C-006: cleanup_old_nparks_drafts Hard Delete
- Root Cause: The task uses old_drafts.delete(), which permanently removes compliance records.
- Optimal Fix: Add is_active soft-delete flag to NParksSubmission and update the task to set is_active=False.
- Affected Files: backend/apps/compliance/models.py, backend/apps/compliance/tasks.py
- Implementation:
  1. Add is_active to NParksSubmission (after line 61):
          is_active = models.BooleanField(default=True, help_text="Soft delete flag")
       2. Update tasks.py line 254:
          # Before:
     old_drafts.delete()
     # After:
     old_drafts.update(is_active=False)
       3. Update all NParksSubmission queries to filter by is_active=True (e.g., in views/services).
  4. Generate migration: python manage.py makemigrations compliance --name add_nparks_is_active
  5. Apply: python manage.py migrate
- Verification:
  - Run cleanup_old_nparks_drafts → Old drafts have is_active=False instead of being deleted.
---
C-007: Idempotency Middleware Breaks on Non-JSON Responses
- Root Cause: The middleware deletes the cache entry if a 2xx response is non-JSON (e.g., file downloads), breaking exactly-once semantics.
- Optimal Fix: Check Content-Type before attempting to cache; skip caching for non-JSON responses.
- Affected Files: backend/apps/core/middleware.py
- Implementation:
  1. Update lines 105-122 in middleware.py:
          if 200 <= response.status_code < 300:
         content_type = response.get('Content-Type', '')
         if 'application/json' in content_type:
             try:
                 response_content = response.content
                 idempotency_cache.set(...)
             except (json.JSONDecodeError, AttributeError):
                 idempotency_cache.delete(fingerprint)
         else:
             # Non-JSON: delete processing marker, do not cache
             idempotency_cache.delete(fingerprint)
     else:
         idempotency_cache.delete(fingerprint)
     - Verification:
  - Send a POST with an idempotency key that returns a non-JSON response → Cache entry not created, processing marker deleted.
---
🟠 High-Severity Issues Remediation
---
H-001: GSTLedger Uses update_or_create
- Root Cause: update_or_create allows updates to immutable records.
- Optimal Fix: Replace with get_or_create and add save() override to prevent updates.
- Affected Files: backend/apps/compliance/models.py, backend/apps/compliance/services/gst.py
- Implementation:
  1. Add save() override to GSTLedger in models.py:
          def save(self, *args, **kwargs):
         if not self._state.adding:
             raise ValueError("GSTLedger is immutable - cannot update")
         super().save(*args, **kwargs)
       2. Update services/gst.py line 198:
          # Before:
     entry, created = GSTLedger.objects.update_or_create(...)
     # After:
     entry, created = GSTLedger.objects.get_or_create(...)
     - Verification:
  - Try to update an existing GSTLedger → Raises ValueError.
---
H-002: Missing Entity Scoping on GSTLedger.create_ledger_entry
- Root Cause: No validation that the agreement's entity matches the user's scope.
- Optimal Fix: Validate the agreement's entity is active, and add entity checks if called from user context.
- Affected Files: backend/apps/compliance/services/gst.py
- Implementation:
  1. Add to create_ledger_entry:
          if not agreement.entity or not agreement.entity.is_active:
         return None
       2. If called from user-facing views, wrap the agreement query with scope_entity().
- Verification:
  - Call with an agreement from an inactive entity → Returns None.
---
H-003: IntercompanyTransfer No Entity Access Check
- Root Cause: No validation that the user can access both entities in the transfer.
- Optimal Fix: Move validation to a service layer method.
- Affected Files: backend/apps/finance/models.py, new backend/apps/finance/services.py
- Implementation:
  1. Create finance/services.py:
          class IntercompanyTransferService:
         @staticmethod
         def create_transfer(from_entity_id, to_entity_id, amount, date, description, user):
             if user.role != User.Role.MANAGEMENT:
                 if str(user.entity_id) not in [str(from_entity_id), str(to_entity_id)]:
                     raise PermissionError("Insufficient permissions")
             return IntercompanyTransfer.objects.create(...)
       2. Update views to use the service method instead of direct model creation.
- Verification:
  - Non-MANAGEMENT user creates a transfer between unauthorized entities → Permission denied.
---
H-004: api.ts Exposes BACKEND_INTERNAL_URL Check
- Root Cause: Runtime browser check only logs an error; NEXT_PUBLIC_ prefix leaks the URL to the bundle.
- Optimal Fix: Add build-time validation in next.config.ts to fail if the env var is misprefixed.
- Affected Files: frontend/next.config.ts, frontend/lib/api.ts
- Implementation:
  1. Add to next.config.ts:
          if (process.env.NEXT_PUBLIC_BACKEND_INTERNAL_URL) {
       throw new Error('BACKEND_INTERNAL_URL must not use NEXT_PUBLIC_ prefix');
     }
       2. Remove the runtime check from api.ts lines 25-29.
- Verification:
  - Build with NEXT_PUBLIC_BACKEND_INTERNAL_URL set → Build fails.
---
H-005: Service Worker Calls Non-Existent Endpoint
- Root Cause: sw.js calls /api/proxy/sync-offline, which is not implemented and not in the BFF allowlist.
- Optimal Fix: Remove the background sync handler (the IndexedDB queue already handles retries) to reduce scope.
- Affected Files: frontend/public/sw.js
- Implementation:
  1. Remove lines 98-103 (sync event listener) and the syncOfflineQueue function (lines 153-177).
  2. Update the app to handle queue retries on reconnect instead of relying on background sync.
- Verification:
  - grep "sync-offline" frontend/public/sw.js → No matches.
---
H-006: Vaccination.save() Broad ImportError Catch
- Root Cause: Swallows all import errors, including bugs in the vaccine service.
- Optimal Fix: Remove the try/except to let errors propagate.
- Affected Files: backend/apps/operations/models.py
- Implementation:
  1. Remove lines 296-308 (try/except block) and import calc_vaccine_due at the top of the file.
  2. If the service is optional, add a feature flag in settings.
- Verification:
  - Introduce a bug in vaccine.py → save() raises an error.
---
H-007: DogClosure Entity Uses CASCADE
- Root Cause: Deleting an Entity cascade-deletes all pedigree data.
- Optimal Fix: Change to PROTECT to prevent accidental entity deletion.
- Affected Files: backend/apps/breeding/models.py
- Implementation:
  1. Update lines 351-353 in breeding/models.py:
          # Before:
     on_delete=models.CASCADE
     # After:
     on_delete=models.PROTECT
       2. Generate migration: python manage.py makemigrations breeding --name change_dogclosure_entity_on_delete
  3. Apply: python manage.py migrate
- Verification:
  - Try to delete an Entity with closure entries → Raises ProtectedError.
---
H-008: NParksService Missing Puppy Entity Validation
- Root Cause: No check that puppies in line items belong to the same entity as the agreement.
- Optimal Fix: Validate dog.entity == entity when processing line items.
- Affected Files: backend/apps/compliance/services/nparks.py
- Implementation:
  1. Add .select_related('dog') to the puppy query and validate:
          item.dog.entity == entity or raise ValidationError("Puppy entity mismatch")
     - Verification:
  - Generate a report with a cross-entity puppy → Excluded from results.
---
H-009: refresh() Returns UUID Objects
- Root Cause: Inconsistent serialization between login() and refresh().
- Optimal Fix: Convert UUIDs to strings in refresh() to match login().
- Affected Files: backend/apps/core/auth.py
- Implementation:
  1. Update the refresh() response:
          "id": str(user.id),
     "entity_id": str(user.entity_id) if user.entity_id else None,
     - Verification:
  - Call POST /api/v1/auth/refresh → id and entity_id are strings.
---
H-010: Segment.filters_json No Validation
- Root Cause: No schema validation on the JSON field.
- Optimal Fix: Add a clean() method with JSON Schema validation.
- Affected Files: backend/apps/customers/models.py
- Implementation:
  1. Add clean() to Segment:
          def clean(self):
         import jsonschema
         schema = {"type": "object", "properties": {"breed": {"type": "string"}, ...}, "additionalProperties": False}
         jsonschema.validate(instance=self.filters_json, schema=schema)
       2. Install jsonschema: pip install jsonschema
- Verification:
  - Create a Segment with invalid filters → Raises ValidationError.
---
H-011: WhelpedPup No Entity FK
- Root Cause: No direct entity FK, so scope_entity() cannot be applied.
- Optimal Fix: Add a denormalized entity FK from the parent WhelpedLog.
- Affected Files: backend/apps/operations/models.py
- Implementation:
  1. Add entity FK to WhelpedPup:
          entity = models.ForeignKey(Entity, on_delete=models.PROTECT, related_name="whelped_pups")
       2. Update save() to auto-set entity from whelped_log.
  3. Generate migration and apply.
- Verification:
  - scope_entity(WhelpedPup.objects.all(), user) filters correctly.
---
🗓️ Execution Timeline
Phase	Tasks	Priority
1	C-001, C-003, C-005, C-006	Critical (security/compliance)
2	C-002, C-004/H-012, C-007	Critical (data integrity/PDPA)
3	H-001, H-007, H-009	High (consistency/security)
4	H-002, H-003, H-005, H-008, H-010, H-011	High (functionality)
5	H-004, H-006	High (code quality)
All fixes include migrations where necessary and should be paired with unit tests to validate the changes.

