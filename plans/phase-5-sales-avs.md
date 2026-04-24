# Phase 5: Sales Agreements & AVS Tracking — Sub-Plan

**Target:** 10–12 days | **Dependencies:** Phase 2, Phase 1 | **Status:** ⬜ Not Started

**Success Criteria:** PDFs cryptographically hashed. AVS reminders fire at 72h. E-sign captures legally. GST exact to 2 decimals.

---

## Execution Order

```
Step 1: Backend models → schemas
Step 2: Backend services (agreement.py, pdf.py, avs.py)
Step 3: Backend routers (agreements.py, avs.py)
Step 4: Backend tasks (Celery: PDF gen, AVS reminder)
Step 5: Backend admin & tests
Step 6: Frontend components (wizard-steps, agreement-preview, signature-pad)
Step 7: Frontend pages (sales list, wizard)
```

---

## File-by-File Specifications

### Step 1: Backend Models & Schemas

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/sales/models.py` | **SalesAgreement**: `type` (B2C/B2B/REHOME), `entity` (FK), `status` (DRAFT/SIGNED/COMPLETED/CANCELLED), `buyer_name`, `buyer_nric`, `buyer_mobile`, `buyer_email`, `buyer_address`, `buyer_housing_type` (HDB/CONDO/LANDED/OTHER), `pdpa_consent` (bool), `total_amount` (Decimal), `gst_component` (Decimal), `deposit` (Decimal), `balance` (Decimal), `payment_method`, `special_conditions`, `pdf_hash` (SHA-256), `signed_at`, `created_by` (FK User), `created_at`. **AgreementLineItem**: `agreement` (FK), `dog` (FK Dog), `price` (Decimal), `gst_component` (Decimal). **AVSTransfer**: `agreement` (FK), `dog` (FK), `buyer_mobile`, `token` (unique), `status` (PENDING/SENT/COMPLETED/ESCALATED), `reminder_sent_at`, `completed_at`, `created_at`. **Signature**: `agreement` (FK), `signer_type` (SELLER/BUYER), `method` (IN_PERSON/REMOTE/PAPER), `coordinates` (JSON: [{x,y,t}]), `ip`, `timestamp`, `image_url`. **TCTemplate**: `type` (B2C/B2B/REHOME), `content` (text), `version` (int), `updated_by` (FK User), `updated_at`. | ☐ |
| `backend/apps/sales/schemas.py` | `AgreementCreate(type, entity_id, dog_ids[], buyer_info, pricing, tc_acceptance)`. `AgreementUpdate(partial)`. `AgreementResponse(id, type, status, buyer_name, dogs[], total, gst, pdf_hash, created_at)`. `SignatureCreate(method, coordinates?, image_url?)`. `AVSTransferResponse(id, dog_name, buyer_mobile, status, reminder_sent_at, completed_at)`. `TCCTemplateUpdate(content)`. | ☐ |

### Step 2: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/sales/services/__init__.py` | Empty | ☐ |
| `backend/apps/sales/services/agreement.py` | `create_agreement(type, data) -> SalesAgreement`. State machine: DRAFT→SIGNED (on sign), SIGNED→COMPLETED (on send). `extract_gst(price, entity) -> Decimal`: `price * 9 / 109`, `ROUND_HALF_UP`. Thomson entity = 0%. `apply_tc(template_type) -> str`: fetches current TCTemplate version. HDB warning: if housing_type=HDB and breed is large, flag. Deposit non-refundable notice. | ☐ |
| `backend/apps/sales/services/pdf.py` | `render_agreement_pdf(agreement_id) -> bytes`. HTML template (Jinja2) with agreement data, buyer info, dog details, T&Cs, signature image. POST to Gotenberg `/forms/chromium/convert/html`. A4 paper. Returns PDF bytes. `compute_hash(pdf_bytes) -> str`: SHA-256 hex digest. Stores hash on agreement. Watermark "DRAFT" on unsigned. | ☐ |
| `backend/apps/sales/services/avs.py` | `generate_avs_token() -> str`: UUID4. `send_avs_link(agreement)`: creates AVSTransfer, generates unique URL, sends via email/WA. `check_completion(transfer_id)`: checks if transfer done. `escalate_to_staff(transfer)`: if 72h pending, notify management. State: PENDING→SENT (on create)→COMPLETED (on buyer action)→ESCALATED (on 72h timeout). | ☐ |

### Step 3: Backend Routers

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/sales/routers/__init__.py` | Register agreements + avs routers | ☐ |
| `backend/apps/sales/routers/agreements.py` | `POST /api/v1/sales/agreements/` → create draft. `PATCH /api/v1/sales/agreements/{id}` → update draft. `POST /api/v1/sales/agreements/{id}/sign` → capture signature (method, coordinates). `POST /api/v1/sales/agreements/{id}/send` → generate PDF, dispatch via email/WA, create AVS transfer. `GET /api/v1/sales/agreements/{id}` → detail with line items, signatures, AVS. `GET /api/v1/sales/agreements/` → list with filters (type, status, entity, date range). Tags: `["sales"]`. | ☐ |
| `backend/apps/sales/routers/avs.py` | `GET /api/v1/sales/avs/pending` → list pending transfers. `POST /api/v1/sales/avs/{id}/complete` → mark complete. `GET /api/v1/sales/avs/{id}/link` → get transfer URL for buyer. Tags: `["avs"]`. | ☐ |

### Step 4: Backend Tasks

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/sales/tasks.py` | `send_agreement_pdf(agreement_id)`: queue "default", retry 3x exponential backoff. Generates PDF via Gotenberg, sends email (Resend) + WhatsApp. Logs to CommunicationLog. DLQ on 3 failures. `avs_reminder_check()`: beat schedule daily 9am SGT. Query all AVSTransfer where status=SENT and created_at < 72h ago. Send reminder, update `reminder_sent_at`. Escalate to staff if needed. | ☐ |

### Step 5: Backend Admin & Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/sales/admin.py` | SalesAgreement (filter by type/status/entity, inline line items). AVSTransfer (filter by status). Signature (read-only). TCTemplate (version history). | ☐ |
| `backend/apps/sales/tests/__init__.py` | Empty | ☐ |
| `backend/apps/sales/tests/test_agreements.py` | `test_create_b2c_agreement`. `test_create_b2b_agreement`. `test_create_rehoming_agreement`. `test_gst_109_equals_9`. `test_gst_218_equals_18`. `test_gst_50_equals_4_13`. `test_gst_thomson_equals_zero`. `test_state_draft_to_signed`. `test_state_signed_to_completed`. `test_signature_captures_coordinates`. `test_pdf_hash_stored`. `test_hdb_warning_for_large_breed`. `test_deposit_non_refundable_notice`. | ☐ |
| `backend/apps/sales/tests/test_avs.py` | `test_generate_unique_token`. `test_send_avs_link_creates_transfer`. `test_reminder_fires_after_72h`. `test_escalation_after_reminder`. `test_completion_updates_status`. `test_idempotent_send`. | ☐ |

### Step 6: Frontend Components

| File | Key Content | Done |
|------|-------------|------|
| `frontend/components/sales/wizard-steps.tsx` | **Step 1 (Dog Selection)**: chip search, entity selector, collection date. **Step 2 (Buyer Details)**: name, NRIC, DOB, mobile, email, address, housing type dropdown. HDB warning banner if applicable. PDPA opt-in checkbox (required). **Step 3 (Health Disclosure)**: editable dog details card. Vaccination rows (add/remove). Health check fields. Seller's remarks. **Step 4 (Pricing)**: sale price input, deposit (non-refundable banner prominent), balance auto-calculated, GST component extracted, payment method. **Step 5 (T&C & Signature)**: T&C read-only display. Special conditions textarea. Signature method: In Person (signature pad) / Remote (link to buyer) / Paper (checklist + mark signed). Each step validates before allowing next. | ☐ |
| `frontend/components/sales/agreement-preview.tsx` | Live preview panel (right side on desktop, collapsible on mobile). Updates as wizard steps complete. Shows: buyer name, dogs, pricing, T&C excerpt, signature status. | ☐ |
| `frontend/components/ui/signature-pad.tsx` | Canvas element. Touch + mouse drawing. Clear button. Undo button. Export as dataURL. Captures coordinates: `[{x, y, timestamp}]`. Responsive: full-width on mobile. | ☐ |

### Step 7: Frontend Pages

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/(protected)/sales/page.tsx` | **Sales Agreements List**: Table (type, buyer, entity, dogs, amount, status badge, created date). Filters: type, status, entity, date range. Create New button → dropdown (B2C/B2B/Rehoming) → wizard. Click → detail view. | ☐ |
| `frontend/app/(protected)/sales/wizard/page.tsx` | **5-Step Wizard**: Step indicator (1-5, current highlighted orange). WizardSteps component. AgreementPreview panel. Back/Next/Submit buttons. Step validation blocks next. Loading state on submit. Success → redirect to agreement detail. | ☐ |

---

## Phase 5 Validation Checklist

- [ ] B2C flow: select dog → buyer → health → pricing → sign → PDF → send → AVS link
- [ ] B2B flow: multiple dogs, line items, subtotal/GST/total auto-calc
- [ ] Rehoming flow: $0 price, transfer form, no invoice
- [ ] GST: 109→9.00, 218→18.00, 50→4.13 (exact to 2 decimals)
- [ ] Thomson entity: GST = 0.00
- [ ] PDF: generated via Gotenberg, SHA-256 hash stored
- [ ] PDF: tamper-evident (hash matches on re-download)
- [ ] Signature: coordinates captured, IP logged, timestamp recorded
- [ ] AVS: unique token per buyer, link sent
- [ ] AVS: reminder fires at 72h (verify via Celery Beat)
- [ ] AVS: escalation after reminder (staff notified)
- [ ] HDB warning: shows for large breeds in HDB housing
- [ ] Deposit: non-refundable banner prominent on pricing step
- [ ] PDPA: opt-in required, enforced on step 2
- [ ] T&C: admin-editable, versioned, applies to future agreements
- [ ] Wizard: step validation blocks forward progress
- [ ] `pytest backend/apps/sales/tests/` → all pass
