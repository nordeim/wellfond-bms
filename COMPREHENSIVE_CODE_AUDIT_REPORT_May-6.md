# Wellfond BMS — Comprehensive Code Audit Report

**Date:** May 6, 2026  
**Auditor:** MiMo AI Assistant  
**Scope:** Full codebase audit against planning documents (Phases 0–8)  
**Codebase Version:** 1.0.0 (8 of 9 phases complete)

---

## Executive Summary

The Wellfond BMS codebase demonstrates **strong architectural foundations** with well-implemented BFF security, entity scoping, and compliance determinism. The project has undergone significant remediation (documented Round 2 audit with 11 fixes). However, several **critical gaps, latent bugs, and incomplete implementations** remain that could impact production readiness, data integrity, and regulatory compliance.

### Severity Distribution

| Severity | Count | Description |
|----------|-------|-------------|
| 🔴 **Critical** | 7 | Security vulnerabilities, data integrity risks, compliance gaps |
| 🟠 **High** | 12 | Functional gaps, missing error handling, performance risks |
| 🟡 **Medium** | 15 | Code quality, incomplete implementations, minor bugs |
| 🔵 **Low** | 8 | Style issues, documentation gaps, minor improvements |
| **Total** | **42** | |

---

## 1. CRITICAL FINDINGS (🔴)

### C-001: Django `SECRET_KEY` Falls Back to Dev Default in Production

**File:** `backend/config/settings/base.py:8`  
**Severity:** 🔴 Critical (Security)

```python
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-in-production")
```

**Issue:** While `production.py` validates the env var at startup, `base.py` still has a hardcoded fallback. If `production.py` import fails or settings are loaded incorrectly, the dev key is used silently. The production validation uses `sys.exit(1)` but only checks `_REQUIRED_ENV_VARS` which includes `DJANGO_SECRET_KEY` — however, the `base.py` default means the variable is always "set" (just to a insecure value).

**Risk:** Session forgery, CSRF bypass, cryptographic weakness.

**Recommendation:** Remove the default entirely in `base.py`:
```python
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # No fallback — fail loud
```

---

### C-002: `Customer.mobile` Unique Constraint Without `null=True` Collides on Empty Strings

**File:** `backend/apps/customers/models.py:42`  
**Severity:** 🔴 Critical (Data Integrity)

```python
mobile = models.CharField(max_length=20, unique=True, db_index=True)
```

**Issue:** The `unique=True` constraint without `null=True` or `blank=True` means multiple customers with empty mobile strings will cause `IntegrityError`. The AGENTS.md documents this as a known gotcha, but the model still has the constraint.

**Impact:** Bulk imports, test fixtures, and partial customer records will fail with database integrity errors.

**Recommendation:** Add `blank=True, null=True` or enforce non-empty at the application layer with a custom validator.

---

### C-003: BFF Proxy Does Not Validate `BACKEND_INTERNAL_URL` at Startup

**File:** `frontend/app/api/proxy/[...path]/route.ts:15`  
**Severity:** 🔴 Critical (Security)

```typescript
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';
```

**Issue:** If `BACKEND_INTERNAL_URL` is not set, it silently falls back to `http://127.0.0.1:8000`. In production, this could cause the proxy to connect to an unintended local service or fail silently. No startup validation exists.

**Risk:** SSRF if the fallback points to an attacker-controlled service, or silent failures in production.

**Recommendation:** Validate at module load time:
```typescript
if (!process.env.BACKEND_INTERNAL_URL) {
  throw new Error('BACKEND_INTERNAL_URL is required');
}
```

---

### C-004: Puppy Model Contains PII Fields Without PDPA Consent Field

**File:** `backend/apps/breeding/models.py:197-198`  
**Severity:** 🔴 Critical (PDPA Compliance)

```python
buyer_name = models.CharField(max_length=100, blank=True, help_text="Buyer's name")
buyer_contact = models.CharField(max_length=100, blank=True, help_text="Buyer's contact")
```

**Issue:** The AGENTS.md explicitly states: *"Puppy buyer fields contain PII but the Puppy model lacks a pdpa_consent field. To ensure compliance, these fields must ONLY be accessed via joins with SalesAgreement."* However, nothing in the code enforces this restriction. Direct queries on `Puppy.buyer_name` and `Puppy.buyer_contact` bypass PDPA filtering.

**Risk:** PII exposure without consent — direct PDPA violation.

**Recommendation:** Either:
1. Remove `buyer_name`/`buyer_contact` from `Puppy` model entirely (use joins with `SalesAgreement`)
2. Add a `pdpa_consent` field to `Puppy` and include it in `scope_entity` filtering
3. At minimum, add model-level restrictions or custom managers that block direct PII access

---

### C-005: `NParksSubmission` Lacks Immutable Protection

**File:** `backend/apps/compliance/models.py:26-65`  
**Severity:** 🔴 Critical (Compliance)

**Issue:** `NParksSubmission` does NOT use `ImmutableManager`. The `save()` and `delete()` methods have no immutability guards. While `lock_expired_submissions` task correctly locks submissions, the model itself allows updates and deletes — unlike `AuditLog`, `PDPAConsentLog`, and `CommunicationLog` which have proper `ImmutableManager` protection.

**Risk:** Locked submissions could be modified or deleted at the database level, breaking compliance audit trail.

**Recommendation:** Apply `ImmutableManager` and add `save()`/`delete()` overrides to `NParksSubmission` (at minimum for LOCKED status).

---

### C-006: `cleanup_old_nparks_drafts` Task Uses Hard Delete on Compliance Records

**File:** `backend/apps/compliance/tasks.py:155-180`  
**Severity:** 🔴 Critical (Compliance)

```python
old_drafts.delete()
```

**Issue:** The `cleanup_old_nparks_drafts` task performs hard deletes on NParks submissions. Even though these are DRAFT status, compliance records should never be hard-deleted. This bypasses the "no DELETE" pattern established for `AuditLog` and `PDPAConsentLog`.

**Risk:** Loss of compliance audit trail. Regulators may require proof of what was drafted, not just what was submitted.

**Recommendation:** Soft-delete via `is_active=False` or archive to a separate table instead of hard delete.

---

### C-007: Idempotency Middleware Fails Silently on Non-JSON Responses

**File:** `backend/apps/core/middleware.py:77-87`  
**Severity:** 🔴 Critical (Data Integrity)

```python
except (json.JSONDecodeError, AttributeError):
    # Non-JSON response — clear processing marker so retries work
    idempotency_cache.delete(fingerprint)
```

**Issue:** If a successful response (2xx) is not JSON (e.g., file download, SSE stream, HTML), the idempotency cache entry is deleted. This means retries of the same request will re-execute the action, breaking exactly-once semantics.

**Risk:** Duplicate data creation, double-charging, duplicate file uploads.

**Recommendation:** Store the response status code and content-type alongside the body. For non-JSON responses, store a hash of the body or a sentinel value indicating "completed but not cacheable."

---

## 2. HIGH-SEVERITY FINDINGS (🟠)

### H-001: `GSTLedger` Uses `update_or_create` Which Violates Immutability

**File:** `backend/apps/compliance/services/gst.py:140-148`  
**Severity:** 🟠 High (Compliance)

```python
entry, created = GSTLedger.objects.update_or_create(
    entity=agreement.entity,
    source_agreement=agreement,
    defaults={...},
)
```

**Issue:** `GSTLedger` is documented as "Immutable once created" but uses `update_or_create`, which will UPDATE existing entries. This contradicts the immutability requirement.

**Recommendation:** Use `get_or_create` instead, or add `save()` override to prevent updates.

---

### H-002: Missing `Entity` Scoping on `GSTLedger.create_ledger_entry`

**File:** `backend/apps/compliance/services/gst.py:133-148`  
**Severity:** 🟠 High (Security)

**Issue:** The `create_ledger_entry` method does not validate that the agreement's entity matches the user's entity scope. A user from Entity A could trigger GST ledger creation for Entity B's agreement.

**Recommendation:** Add entity scope validation before creating ledger entries.

---

### H-003: `IntercompanyTransfer.save()` Creates Transactions Without Entity Scoping Check

**File:** `backend/apps/finance/models.py:96-126`  
**Severity:** 🟠 High (Security)

**Issue:** The `save()` override creates two `Transaction` records automatically, but there's no validation that the user has access to both entities. A non-MANAGEMENT user could theoretically create transfers between entities they don't have access to.

**Recommendation:** Add permission validation in the service layer (not model) before allowing intercompany transfers.

---

### H-004: Frontend `api.ts` Exposes `BACKEND_INTERNAL_URL` Check in Browser

**File:** `frontend/lib/api.ts:17-23`  
**Severity:** 🟠 High (Security)

```typescript
if (typeof window !== 'undefined' && process.env.BACKEND_INTERNAL_URL) {
  console.error('[SECURITY] BACKEND_INTERNAL_URL is exposed...');
}
```

**Issue:** This check only logs a warning. If `BACKEND_INTERNAL_URL` is accidentally prefixed with `NEXT_PUBLIC_`, it's already in the bundle. The check should be a build-time validation, not a runtime warning.

**Recommendation:** Add a Next.js build plugin or `next.config.ts` validation that fails the build if `BACKEND_INTERNAL_URL` is in the client bundle.

---

### H-005: Service Worker `syncOfflineQueue` Calls Non-Existent Endpoint

**File:** `frontend/public/sw.js:108`  
**Severity:** 🟠 High (Functional)

```javascript
const response = await fetch("/api/proxy/sync-offline", {
  method: "POST",
  ...
});
```

**Issue:** The `/api/proxy/sync-offline` endpoint does not exist in the backend routers. The BFF proxy allowlist doesn't include `sync-offline`. Background sync will always fail with 403.

**Recommendation:** Either implement the sync endpoint or remove the background sync handler and use the IndexedDB queue's built-in retry mechanism.

---

### H-006: `Vaccination.save()` Catches `ImportError` Instead of `ImportError`

**File:** `backend/apps/operations/models.py:188-196`  
**Severity:** 🟠 High (Functional)

```python
except ImportError:
    logger.warning("Vaccine service import failed...")
```

**Issue:** The `ImportError` catch is overly broad — it will silently swallow import failures in the vaccine service itself (e.g., missing dependencies), not just the module import. This means vaccine due dates will silently not be calculated if there's a bug in the service.

**Recommendation:** Remove the try/except and let import failures propagate. If the service is optional, make it explicit with a feature flag.

---

### H-007: `DogClosure` Entity Cascade Delete Risks Data Loss

**File:** `backend/apps/breeding/models.py:168`  
**Severity:** 🟠 High (Data Integrity)

```python
entity = models.ForeignKey(Entity, on_delete=models.CASCADE, ...)
```

**Issue:** If an Entity is accidentally deleted, ALL closure table entries for that entity are cascade-deleted. This would destroy the entire pedigree tree for that entity, making COI calculations impossible.

**Recommendation:** Use `on_delete=PROTECT` instead of `CASCADE` for the entity FK on `DogClosure`.

---

### H-008: Missing `Entity` Scoping in `NParksService._generate_puppy_movement`

**File:** `backend/apps/compliance/services/nparks.py:158-163`  
**Severity:** 🟠 High (Data Isolation)

**Issue:** The puppy movement query uses `SalesAgreement.objects.filter(entity=entity, ...)` which is correct, but the `item.dog` access doesn't validate that the dog belongs to the same entity. Cross-entity data could leak if line items reference dogs from other entities.

**Recommendation:** Add entity validation on dog access within line items.

---

### H-009: `AuthenticationService.refresh()` Returns UUID Objects, Not Strings

**File:** `backend/apps/core/auth.py:131-146`  
**Severity:** 🟠 High (Serialization)

```python
return {
    "user": {
        "id": user.id,  # UUID object
        "entity_id": user.entity_id,  # UUID object
        ...
    },
}
```

**Issue:** The `refresh()` method returns raw UUID objects, while `login()` returns `str(user.id)`. This inconsistency can cause serialization errors or frontend type mismatches.

**Recommendation:** Consistently serialize UUIDs to strings in all auth responses.

---

### H-010: `Segment.filters_json` Has No Validation

**File:** `backend/apps/customers/models.py:170-173`  
**Severity:** 🟠 High (Data Integrity)

```python
filters_json = models.JSONField(default=dict, help_text="JSON filters: breed, entity, pdpa, date_range, housing_type")
```

**Issue:** No schema validation on the JSON field. Invalid filter structures will cause runtime errors in the segmentation service. No Pydantic schema or JSON Schema validation exists.

**Recommendation:** Add a JSON Schema validator or Pydantic model for the filters structure.

---

### H-011: `WhelpedPup` Has No Entity Scoping

**File:** `backend/apps/operations/models.py:285-305`  
**Severity:** 🟠 High (Multi-tenancy)

**Issue:** `WhelpedPup` is accessed via `WhelpedLog` → `Dog` → `Entity`, but the model itself has no entity FK. This means `scope_entity()` cannot be directly applied to `WhelpedPup` queries, requiring manual joins.

**Recommendation:** Either add a denormalized `entity` FK or ensure all access paths go through the parent `WhelpedLog`.

---

### H-012: `Puppy.buyer_name`/`buyer_contact` Fields Create PDPA Shadow

**File:** `backend/apps/breeding/models.py:197-198`  
**Severity:** 🟠 High (PDPA)

**Issue:** These fields duplicate PII from `SalesAgreement` and create a "shadow" PII store that isn't covered by PDPA consent filtering. Any direct query on `Puppy` that returns these fields bypasses consent checks.

**Recommendation:** Remove these fields from `Puppy` and use joins with `SalesAgreement` for buyer information (as documented in AGENTS.md).

---

## 3. MEDIUM-SEVERITY FINDINGS (🟡)

### M-001: `BreedingRecord.save()` Auto-Assigns Entity Without Validation

**File:** `backend/apps/breeding/models.py:85-88`  
**Severity:** 🟡 Medium

```python
if not self.entity_id and self.dam:
    self.entity = self.dam.entity
```

**Issue:** Auto-assigning entity from dam is convenient but bypasses explicit entity assignment. If the dam is later moved to a different entity, historical breeding records will have stale entity references.

---

### M-002: `Litter.save()` Auto-Calculation of `total_count` May Stale

**File:** `backend/apps/breeding/models.py:129-132`  
**Severity:** 🟡 Medium

```python
def save(self, *args, **kwargs):
    self.total_count = self.alive_count + self.stillborn_count
```

**Issue:** If `alive_count` or `stillborn_count` is updated after initial creation, `total_count` is recalculated. However, if `Puppy` records are added/deleted independently, the `total_count` may not reflect actual puppy count.

---

### M-003: `HealthRecord` Model Missing `updated_at` Field

**File:** `backend/apps/operations/models.py:111-159`  
**Severity:** 🟡 Medium

**Issue:** `HealthRecord` has `created_at` but no `updated_at`. If health records are edited (e.g., adding follow-up details), there's no audit trail of when changes occurred.

---

### M-004: `Vaccination` Status Not Auto-Updated When Due Date Passes

**File:** `backend/apps/operations/models.py:200-220`  
**Severity:** 🟡 Medium

**Issue:** `_calculate_status()` is only called in `save()`. If a vaccination's due date passes without an explicit save, the status remains stale. The `check_overdue_vaccines` Celery task should update statuses, but there's no guarantee it runs before status is queried.

---

### M-005: `DogPhoto` Missing Entity Scoping

**File:** `backend/apps/operations/models.py:249-270`  
**Severity:** 🟡 Medium

**Issue:** `DogPhoto` has no `entity` FK and relies on `Dog.entity` for scoping. Direct queries on `DogPhoto` will bypass entity filtering.

---

### M-006: `Signature` Model Stores Raw IP Address Without Anonymization

**File:** `backend/apps/sales/models.py:213`  
**Severity:** 🟡 Medium (PDPA)

```python
ip_address = models.GenericIPAddressField(null=True, blank=True)
```

**Issue:** Storing raw IP addresses may violate PDPA's data minimization principle. IP addresses are considered personal data under Singapore's PDPA.

**Recommendation:** Hash or anonymize IP addresses before storage, or obtain explicit consent for IP logging.

---

### M-007: `TCTemplate` Has No Version Rollback Capability

**File:** `backend/apps/sales/models.py:243-260`  
**Severity:** 🟡 Medium

**Issue:** `TCTemplate` increments version on update but doesn't store historical versions. Previous T&C content is lost on update.

---

### M-008: `PNLSnapshot` Missing `generated_by` Audit Field

**File:** `backend/apps/finance/models.py:151-175`  
**Severity:** 🟡 Medium

**Issue:** Unlike `GSTReport`, `PNLSnapshot` doesn't track who generated it. This breaks audit trail requirements for financial records.

---

### M-009: `Transaction` Model Missing `created_by` Field

**File:** `backend/apps/finance/models.py:24-60`  
**Severity:** 🟡 Medium

**Issue:** Financial transactions have no `created_by` field, making it impossible to audit who created specific transactions.

---

### M-010: Frontend `useAuth` Hook Not Verified for Token Refresh Race Conditions

**File:** `frontend/lib/api.ts:84-100`  
**Severity:** 🟡 Medium

**Issue:** The 401 retry logic imports `setSession` and `setCsrfToken` dynamically. If multiple concurrent requests hit 401 simultaneously, multiple refresh attempts will race, potentially invalidating each other's tokens.

**Recommendation:** Implement a token refresh queue or mutex to prevent concurrent refresh attempts.

---

### M-011: `IdempotencyMiddleware` Fingerprint Uses Session Cookie, Not User ID

**File:** `backend/apps/core/middleware.py:102-108`  
**Severity:** 🟡 Medium

```python
session_id = request.COOKIES.get("sessionid", "anon")
```

**Issue:** If a user's session rotates (e.g., after refresh), the same idempotency key with a different session cookie generates a different fingerprint, allowing duplicate execution.

---

### M-012: `scope_entity` PDPA Filter Applies to All Models With `pdpa_consent`

**File:** `backend/apps/core/permissions.py:41-55`  
**Severity:** 🟡 Medium

**Issue:** The PDPA filter `queryset.filter(pdpa_consent=True)` is applied generically to any model with a `pdpa_consent` field. This includes `SalesAgreement` (correct) but could accidentally filter `User` records if `pdpa_consent` is added to User model.

---

### M-013: `NParksService._generate_dog_movement` Only Captures Rehomed Dogs

**File:** `backend/apps/compliance/services/nparks.py:300-340`  
**Severity:** 🟡 Medium

**Issue:** The dog movement report only captures dogs from REHOME-type agreements. Deceased dogs (status=DECEASED) are not included, which may be required by NParks reporting.

---

### M-014: Missing `on_delete=PROTECT` on Several Foreign Keys

**Files:** Various models  
**Severity:** 🟡 Medium

**Issue:** Several FK relationships use `on_delete=CASCADE` where `PROTECT` would be safer:
- `WhelpedLog.pups` → CASCADE (should be PROTECT to prevent orphaned records)
- `AgreementLineItem.agreement` → CASCADE (acceptable, but should be documented)

---

### M-015: `Customer.nric` Field Stores NRIC Without Encryption

**File:** `backend/apps/customers/models.py:38`  
**Severity:** 🟡 Medium (Security/PDPA)

```python
nric = models.CharField(max_length=20, blank=True, db_index=True)
```

**Issue:** NRIC is highly sensitive PII under Singapore's PDPA. Storing it as plaintext in the database without encryption at rest exposes it to database-level breaches.

**Recommendation:** Encrypt NRIC at the application layer before storage, or use PostgreSQL's `pgcrypto` extension.

---

## 4. LOW-SEVERITY FINDINGS (🔵)

### L-001: `Dog.age_years` Property Uses Float Division

**File:** `backend/apps/operations/models.py:85-88`  
**Severity:** 🔵 Low

```python
return (today - self.dob).days / 365.25
```

**Issue:** Float division introduces precision errors. For compliance calculations (e.g., rehome flag at 5/6 years), this could cause off-by-one-day errors.

**Recommendation:** Use integer day comparisons: `(today - self.dob).days >= 5 * 365`

---

### L-002: `Entity.Code` Choices Don't Cover All Possible Entities

**File:** `backend/apps/core/models.py:56-60`  
**Severity:** 🔵 Low

**Issue:** Only Holdings, Katong, and Thomson are defined. If new entities are added, model choices must be updated.

---

### L-003: Frontend `types.ts` Uses `type` for `MatedLog.method` Inconsistently

**File:** `frontend/lib/types.ts:254`  
**Severity:** 🔵 Low

```typescript
method: 'natural' | 'ai' | 'surgical';
```

**Issue:** Backend uses `NATURAL`/`ASSISTED` but frontend uses `natural`/`ai`/`surgical`. Mismatch will cause data binding failures.

---

### L-004: `WhelpedPup` Gender Choices Use `'male'`/`'female'` in Frontend Types

**File:** `frontend/lib/types.ts:265`  
**Severity:** 🔵 Low

```typescript
gender: 'male' | 'female';
```

**Issue:** Backend uses `'M'`/`'F'` but frontend types use `'male'`/`'female'`. This will cause display/data mapping issues.

---

### L-005: `AuditLog` Resource ID is `CharField`, Not UUID

**File:** `backend/apps/core/models.py:104`  
**Severity:** 🔵 Low

```python
resource_id = models.CharField(max_length=100)
```

**Issue:** Resource IDs are UUIDs but stored as strings. This loses type safety and prevents UUID-specific queries.

---

### L-006: Missing Indexes on Frequently Queried Fields

**Severity:** 🔵 Low

**Issue:** Several models lack indexes on commonly filtered fields:
- `HealthRecord.category` (filtered in NParks reports)
- `Vaccination.vaccine_name` (filtered in reports)
- `SalesAgreement.type` (has index but compound with status would help)

---

### L-007: `Dog.notes` Field Has `default=''` But `blank=True` Missing

**File:** `backend/apps/operations/models.py:75`  
**Severity:** 🔵 Low

```python
notes = models.TextField(blank=True, default='')
```

**Issue:** This is actually correct (has both `blank=True` and `default=''`), but the pattern is inconsistent — `dna_notes` at line 73 only has `blank=True` without `default=''`.

---

### L-008: `Breed` Field Not Normalized

**File:** `backend/apps/operations/models.py:44`  
**Severity:** 🔵 Low

```python
breed = models.CharField(max_length=100)
```

**Issue:** Breed is a free-text field. Inconsistent entries (e.g., "Golden Retriever" vs "golden retriever") will cause filtering issues.

**Recommendation:** Create a `Breed` lookup model or normalize to uppercase on save.

---

## 5. ARCHITECTURE & DESIGN OBSERVATIONS

### ✅ Strengths

1. **BFF Security Pattern** — Well-implemented with path allowlisting, header stripping, and `BACKEND_INTERNAL_URL` isolation
2. **Entity Scoping** — `scope_entity()` and `scope_entity_for_list()` provide consistent multi-tenancy
3. **Immutable Audit Trails** — `ImmutableManager` pattern correctly applied to `AuditLog`, `PDPAConsentLog`, `CommunicationLog`
4. **GST Determinism** — Pure Python/SQL calculation with `ROUND_HALF_UP` and Thomson exemption
5. **COI Implementation** — Wright's formula with closure table traversal and Redis caching
6. **Idempotency** — UUIDv4 keys with Redis-backed deduplication
7. **Middleware Order** — Correctly places Django auth before custom auth
8. **Test Infrastructure** — `authenticate_client()` helper properly handles Ninja's auth requirements

### ⚠️ Weaknesses

1. **Inconsistent Immutability** — `GSTLedger` and `NParksSubmission` lack immutable protection
2. **PDPA Shadow PII** — `Puppy.buyer_name`/`buyer_contact` bypass consent filtering
3. **Entity Cascade Deletes** — `DogClosure` uses CASCADE instead of PROTECT
4. **Missing Audit Fields** — `PNLSnapshot` and `Transaction` lack `created_by`
5. **Service Worker Endpoint** — Background sync calls non-existent endpoint
6. **TypeScript Type Mismatches** — Frontend types don't match backend enums

---

## 6. COMPLIANCE VALIDATION

### AVS Compliance
| Requirement | Status | Notes |
|-------------|--------|-------|
| 3-day reminder tasks | ✅ Implemented | `check_avs_reminders` in Celery beat |
| Transfer tracking | ✅ Implemented | `AVSTransfer` model with token |
| Entity scoping | ✅ Implemented | All queries scoped |

### NParks Reporting
| Requirement | Status | Notes |
|-------------|--------|-------|
| 5-document Excel | ✅ Implemented | Mating, movement, vet, bred, movement |
| Month locking | ⚠️ Partial | Lock task exists but model lacks immutability |
| Deterministic | ✅ Implemented | Pure Python/SQL, zero AI |

### GST/IRAS
| Requirement | Status | Notes |
|-------------|--------|-------|
| 9/109 formula | ✅ Implemented | `ROUND_HALF_UP` |
| Thomson 0% | ✅ Implemented | Case-insensitive check |
| Quarterly reports | ✅ Implemented | `GSTReport` model |

### PDPA
| Requirement | Status | Notes |
|-------------|--------|-------|
| Consent filtering | ⚠️ Partial | Works for `SalesAgreement`, bypassed on `Puppy` |
| Audit trail | ✅ Implemented | `PDPAConsentLog` immutable |
| Data minimization | ⚠️ Gap | NRIC stored plaintext, IP addresses stored raw |

---

## 7. TEST COVERAGE ASSESSMENT

### Backend Tests (Documented)
| App | Test Files | Coverage Assessment |
|-----|------------|-------------------|
| core | 12 test files | ✅ Good — auth, middleware, CSP, idempotency |
| operations | 5 test files | ✅ Good — dogs, importers, logs, SSE, tasks |
| breeding | 4 test files | ✅ Good — COI, saturation, async COI |
| sales | 6 test files | ✅ Good — agreements, AVS, GST, PDF |
| compliance | 3 test files | ✅ Good — GST, NParks, PDPA |
| customers | 2 test files | ⚠️ Adequate — blast, segmentation |
| finance | 3 test files | ✅ Good — P&L, GST, transactions |

### Frontend Tests
| Area | Status | Notes |
|------|--------|-------|
| Unit tests | ⚠️ Limited | `use-auth`, `offline-queue`, `next-config-security` |
| E2E tests | ⚠️ Minimal | Only `dashboard.spec.ts` |
| Component tests | ❌ Missing | No component-level tests |

### Test Gaps
1. No integration tests for BFF proxy → Django flow
2. No tests for concurrent idempotency key handling
3. No tests for entity scoping edge cases (cross-entity access)
4. No tests for PDPA filtering on `Puppy` model
5. No load tests for COI calculation performance (<500ms target)

---

## 8. INFRASTRUCTURE OBSERVATIONS

### Docker Compose (Production)
| Component | Status | Notes |
|-----------|--------|-------|
| PostgreSQL 17 | ✅ Correct | `wal_level=replica`, SCRAM auth |
| PgBouncer | ✅ Correct | Transaction pooling mode |
| Redis ×4 | ✅ Correct | Sessions, broker, cache, idempotency |
| Gotenberg | ✅ Correct | Chromium PDF generation |
| Celery Worker | ✅ Correct | 2 replicas, split queues |
| Celery Beat | ✅ Correct | DatabaseScheduler |
| Next.js | ✅ Correct | BFF proxy, SSR |

### Issues
1. **Django service missing `build` context** — The `django` service in `docker-compose.yml` doesn't have a `build` section, relying on pre-built images
2. **No health check for Gotenberg** — Gotenberg has a healthcheck but Django doesn't wait for it
3. **Flower exposed without auth** — Port 5555 is exposed without authentication
4. **No rate limiting on BFF proxy** — Only backend has rate limiting, proxy doesn't

---

## 9. RECOMMENDATIONS

### Immediate (Before Production)

1. **Fix C-004 (Puppy PII):** Remove `buyer_name`/`buyer_contact` from `Puppy` model or add PDPA filtering
2. **Fix C-005 (NParks immutability):** Apply `ImmutableManager` to `NParksSubmission`
3. **Fix C-007 (Idempotency non-JSON):** Handle non-JSON responses in idempotency middleware
4. **Fix H-001 (GSTLedger immutability):** Use `get_or_create` instead of `update_or_create`
5. **Fix H-005 (Service Worker sync):** Implement or remove the sync endpoint
6. **Fix H-007 (DogClosure cascade):** Change to `on_delete=PROTECT`

### Short-Term (Next Sprint)

7. **Add `created_by` to `Transaction` and `PNLSnapshot`** for audit completeness
8. **Normalize breed field** or add a lookup table
9. **Encrypt NRIC** at application layer
10. **Add frontend component tests** for critical paths
11. **Validate TypeScript types** against backend enums
12. **Add Flower authentication** or restrict port

### Medium-Term (Next Phase)

13. **Implement IP address anonymization** for PDPA compliance
14. **Add load testing** for COI calculation performance
15. **Add integration tests** for BFF → Django flow
16. **Implement T&C version history** for legal compliance
17. **Add deceased dogs to NParks movement report**
18. **Consider PostgreSQL `pgcrypto`** for sensitive fields

---

## 10. CONCLUSION

The Wellfond BMS codebase is **architecturally sound** with strong foundations in security (BFF pattern), multi-tenancy (entity scoping), and compliance (deterministic calculations). The Round 2 remediation addressed many critical issues.

However, **7 critical and 12 high-severity issues remain** that must be addressed before production deployment. The most pressing concerns are:

1. **PDPA compliance gap** on `Puppy` model PII fields
2. **Inconsistent immutability** across compliance models
3. **Idempotency middleware** not handling non-JSON responses
4. **Service Worker** calling non-existent endpoints

The codebase demonstrates good engineering practices (TDD, immutable audit trails, deterministic compliance logic) but needs focused remediation on the identified gaps before it can be safely deployed for production use handling real regulatory data.

---

*Report generated by comprehensive code audit on May 6, 2026.*
