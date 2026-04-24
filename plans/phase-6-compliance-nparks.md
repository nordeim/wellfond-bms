# Phase 6: Compliance & NParks Reporting — Sub-Plan

**Target:** 7–10 days | **Dependencies:** Phase 2, Phase 4, Phase 5 | **Status:** ⬜ Not Started

**Success Criteria:** Zero AI in compliance. Excel matches NParks template. Month lock immutable. GST exact.

---

## Execution Order

```
Step 1: Backend models → schemas
Step 2: Backend services (nparks.py, gst.py, pdpa.py)
Step 3: Backend routers (nparks.py, gst.py)
Step 4: Backend tasks (Celery: monthly gen, lock)
Step 5: Backend admin & tests
Step 6: Frontend pages (compliance, settings)
```

---

## File-by-File Specifications

### Step 1: Backend Models & Schemas

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/compliance/models.py` | **NParksSubmission**: `entity` (FK), `month` (date, first of month), `status` (DRAFT/SUBMITTED/LOCKED), `generated_at`, `submitted_at`, `locked_at`, `generated_by` (FK User). Unique(entity, month). **GSTLedger**: `entity` (FK), `period` (quarter, e.g. "2026-Q1"), `source_agreement` (FK SalesAgreement), `total_sales` (Decimal), `gst_component` (Decimal), `created_at`. **PDPAConsentLog**: `customer` (FK), `action` (OPT_IN/OPT_OUT), `previous_state` (bool), `new_state` (bool), `actor` (FK User), `ip`, `created_at`. Immutable (no UPDATE/DELETE). | ☐ |
| `backend/apps/compliance/schemas.py` | `NParksGenerateRequest(entity_id, month: date)`. `NParksPreview(doc_type, rows: list[dict], headers: list[str])`. `NParksSubmissionResponse(id, entity, month, status, generated_at, submitted_at)`. `GSTSummary(entity, quarter, total_sales, total_gst, transactions_count)`. `GSTExportRequest(entity_id, quarter)`. `PDPAConsentUpdate(customer_id, action: OPT_IN|OPT_OUT)`. | ☐ |

### Step 2: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/compliance/services/__init__.py` | Empty | ☐ |
| `backend/apps/compliance/services/nparks.py` | `generate_nparks(entity_id, month) -> dict[str, bytes]`. Returns 5 Excel files as dict keys: `mating_sheet`, `puppy_movement`, `vet_treatments`, `puppies_bred`, `dog_movement`. Each: `openpyxl` workbook. Mating sheet: dual-sire columns (Sire 1, Sire 2). Puppy movement: per-pup with chip, breed, buyer. Vet treatments: per-dog vet records. Puppies bred: in-house bred summary. Dog movement: rehomed/deceased. Farm details pre-filled: Wellfond Pets Holdings, Licence DB000065X, address. Deterministic sort: by chip, then date. Zero AI. Zero string interpolation from LLM. `preview_nparks(entity_id, month, doc_type) -> NParksPreview`. `validate_nparks(entity_id, month) -> list[warning]`. | ☐ |
| `backend/apps/compliance/services/gst.py` | `extract_gst(price, entity) -> Decimal`. Formula: `Decimal(str(price)) * Decimal('9') / Decimal('109')`. `quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)`. Thomson entity: return `Decimal('0.00')`. Entity-aware: check entity.gst_rate. `calc_gst_summary(entity, quarter) -> GSTSummary`. Sums all SalesAgreement GST components for period. | ☐ |
| `backend/apps/compliance/services/pdpa.py` | `filter_consent(queryset) -> QuerySet`: hard `WHERE pdpa_consent=True`. Applied to Customer querysets for marketing. `log_consent_change(customer, action, actor, ip)`: creates immutable PDPAConsentLog. `check_blast_eligibility(customer_ids) -> (eligible_ids, excluded_ids)`: splits by consent status. No override path: consent=False always excluded. | ☐ |

### Step 3: Backend Routers

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/compliance/routers/__init__.py` | Register nparks + gst routers | ☐ |
| `backend/apps/compliance/routers/nparks.py` | `POST /api/v1/compliance/nparks/generate` → generates all 5 docs, creates NParksSubmission(DRAFT). `GET /api/v1/compliance/nparks/preview/{submission_id}` → preview table for each doc. `POST /api/v1/compliance/nparks/submit/{submission_id}` → status→SUBMITTED, records timestamp. `POST /api/v1/compliance/nparks/lock/{submission_id}` → status→LOCKED, prevents all edits. `GET /api/v1/compliance/nparks/download/{submission_id}?doc=mating_sheet` → Excel file download. `GET /api/v1/compliance/nparks/` → list submissions (entity, month, status). Tags: `["compliance"]`. | ☐ |
| `backend/apps/compliance/routers/gst.py` | `GET /api/v1/compliance/gst/summary?entity=&quarter=` → GST summary. `GET /api/v1/compliance/gst/export?entity=&quarter=` → Excel export. Tags: `["gst"]`. | ☐ |

### Step 4: Backend Tasks

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/compliance/tasks.py` | `generate_monthly_nparks(entity_id, month)`: queue "high", scheduled via Celery Beat (1st of month 9am SGT). Generates all 5 docs, creates DRAFT submission. `lock_expired_submissions()`: queue "high", daily. Auto-lock submissions where month has passed and status=SUBMITTED. | ☐ |

### Step 5: Backend Admin & Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/compliance/admin.py` | NParksSubmission (filter by entity/month/status, read-only after LOCKED). GSTLedger (read-only). PDPAConsentLog (read-only, filter by customer/action). | ☐ |
| `backend/apps/compliance/tests/__init__.py` | Empty | ☐ |
| `backend/apps/compliance/tests/test_nparks.py` | `test_generate_holdings_5_docs`. `test_generate_katong_5_docs`. `test_generate_thomson_3_docs` (no mating/bred). `test_dual_sire_columns_present`. `test_farm_details_pre_filled`. `test_lock_prevents_edits`. `test_submit_records_timestamp`. `test_preview_matches_data`. | ☐ |
| `backend/apps/compliance/tests/test_gst.py` | `test_extract_gst_109_equals_9`. `test_extract_gst_218_equals_18`. `test_extract_gst_50_equals_4_13`. `test_extract_gst_thomson_equals_zero`. `test_round_half_up`. `test_gst_summary_sums_correctly`. | ☐ |
| `backend/apps/compliance/tests/test_pdpa.py` | `test_filter_excludes_opted_out`. `test_filter_includes_opted_in`. `test_consent_log_immutable`. `test_log_records_previous_and_new_state`. `test_blast_eligibility_splits_correctly`. `test_no_override_path`. | ☐ |

### Step 6: Frontend Pages

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/(protected)/compliance/page.tsx` | **NParks Page**: Entity selector (Holdings/Katong/Thomson). Month picker. Generate All button (loading state). Preview: tabs for each doc type, table view. Download Excel button per doc. Submit button (confirmation dialog). Lock button (warning: irreversible). Status badges: DRAFT (gray), SUBMITTED (blue), LOCKED (green). Submission history table. | ☐ |
| `frontend/app/(protected)/compliance/settings/page.tsx` | **T&C Settings (admin only)**: Three editable T&C templates (B2C, B2B, Rehoming). Rich text editor or markdown. Version history list (date, author, changes). Preview button. Save button. Applies to all future agreements immediately. | ☐ |

---

## Phase 6 Validation Checklist

- [ ] NParks: Holdings → 5 documents generated
- [ ] NParks: Katong → 5 documents generated
- [ ] NParks: Thomson → 3 documents (no mating/bred)
- [ ] NParks: Excel matches official template (column widths, headers, formatting)
- [ ] NParks: dual-sire columns present in mating sheet
- [ ] NParks: farm details pre-filled (DB000065X)
- [ ] GST: 109→9.00, 218→18.00, 50→4.13 (exact)
- [ ] GST: Thomson = 0.00
- [ ] GST: ROUND_HALF_UP rounding
- [ ] PDPA: opted-out excluded from blast query
- [ ] PDPA: consent log immutable (try UPDATE → error)
- [ ] PDPA: log records previous_state + new_state + actor
- [ ] Month lock: prevents any POST/PATCH to locked period
- [ ] `grep -r "anthropic\|openai\|langchain" backend/apps/compliance/` → 0 matches
- [ ] `pytest backend/apps/compliance/tests/` → all pass
