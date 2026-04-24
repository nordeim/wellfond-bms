# Phase 7: Customer DB & Marketing Blast — Sub-Plan

**Target:** 7–10 days | **Dependencies:** Phase 5, Phase 6 | **Status:** ⬜ Not Started

**Success Criteria:** Blasts respect PDPA hard filter. Send progress live via SSE. Comms logged per customer.

---

## Execution Order

```
Step 1: Backend models → schemas
Step 2: Backend services (segmentation.py, blast.py, comms_router.py)
Step 3: Backend router (customers.py)
Step 4: Backend tasks (Celery: fan-out)
Step 5: Backend admin & tests
Step 6: Frontend hooks
Step 7: Frontend page (customers)
```

---

## File-by-File Specifications

### Step 1: Backend Models & Schemas

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/customers/models.py` | **Customer**: `name`, `nric` (optional), `mobile` (unique), `email`, `address`, `housing_type` (HDB/CONDO/LANDED/OTHER), `pdpa_consent` (bool, default False), `entity` (FK), `notes`, `created_at`, `updated_at`. **CommunicationLog**: `customer` (FK), `channel` (EMAIL/WA), `campaign_id` (nullable), `status` (SENT/DELIVERED/BOUNCED/FAILED), `message_preview` (first 200 chars), `subject` (for email), `created_at`. Immutable. **Segment**: `name`, `filters_json` (JSON), `created_by` (FK User), `created_at`. | ☐ |
| `backend/apps/customers/schemas.py` | `CustomerCreate(name, mobile, email?, nric?, address?, housing_type?, entity_id, pdpa_consent?)`. `CustomerUpdate(partial)`. `CustomerList(items, total, page, perPage)`. `CustomerDetail(Customer + purchase_history[], comms_log[], notes)`. `SegmentCreate(name, filters: SegmentFilters)`. `SegmentFilters(breed?, entity?, pdpa?, date_from?, date_to?, housing_type?)`. `BlastCreate(segment_id?, customer_ids?, channel: EMAIL|WA|BOTH, subject?, body, merge_tags?)`. `BlastProgress(blast_id, total, sent, delivered, failed, in_progress)`. | ☐ |

### Step 2: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/customers/services/__init__.py` | Empty | ☐ |
| `backend/apps/customers/services/segmentation.py` | `build_segment(filters: SegmentFilters) -> QuerySet`. Composable Q objects: breed, entity, pdpa, date range, housing type. Auto-excludes `pdpa_consent=False`. `preview_segment(filters) -> int` (count without fetching). `get_segment_customers(segment_id) -> QuerySet`. Cached counts (Redis, 5min TTL). | ☐ |
| `backend/apps/customers/services/blast.py` | `send_blast(blast_data) -> BlastResult`. Resend email SDK: `resend.Emails.send({from, to, subject, html})`. WA Business Cloud API: `POST /messages` with template. Merge tag interpolation: `{{name}}`, `{{breed}}`, `{{entity}}`, `{{mobile}}`. Rate limit: 10/sec (token bucket). Bounce handling: update CommunicationLog status. | ☐ |
| `backend/apps/customers/services/comms_router.py` | `route_message(customer, template_name, payload) -> DeliveryResult`. `TemplateManager`: caches WA template approval status in Redis (key: `wa_template:{name}`, TTL: 1h). If WA unapproved or fails → fallback to Resend email. Logs channel switch in CommunicationLog. Returns `{channel, status, reason?}`. | ☐ |

### Step 3: Backend Router

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/customers/routers/__init__.py` | Register customers router | ☐ |
| `backend/apps/customers/routers/customers.py` | `GET /api/v1/customers/` → list with filters (search, breed, entity, pdpa, date range). Pagination. `GET /api/v1/customers/{id}` → detail with purchase history + comms log. `POST /api/v1/customers/` → manual add. `PATCH /api/v1/customers/{id}` → update. `POST /api/v1/customers/import` → CSV upload with column mapping. `POST /api/v1/customers/blast` → send blast (PDPA enforced). `GET /api/v1/customers/blast/{id}/progress` → SSE progress stream. Tags: `["customers"]`. | ☐ |

### Step 4: Backend Tasks

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/customers/tasks.py` | `dispatch_blast(blast_id)`: queue "default". Chunked: 50 customers per chunk. Each chunk: send via email/WA, update CommunicationLog, update progress in Redis. Retry: exponential backoff, max 3. DLQ on 3 failures. `log_delivery(customer_id, channel, status, message_preview)`: per-message logging. Progress: Redis pub/sub → SSE bridge. | ☐ |

### Step 5: Backend Admin & Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/customers/admin.py` | Customer (search by name/mobile/email, filter by entity/pdpa, inline comms log). CommunicationLog (read-only). Segment. | ☐ |
| `backend/apps/customers/tests/__init__.py` | Empty | ☐ |
| `backend/apps/customers/tests/test_segmentation.py` | `test_segment_by_breed`. `test_segment_by_entity`. `test_segment_excludes_pdpa_false`. `test_segment_combines_filters`. `test_preview_returns_count`. `test_cached_count`. | ☐ |
| `backend/apps/customers/tests/test_blast.py` | `test_blast_sends_to_eligible_customers`. `test_blast_excludes_pdpa_false`. `test_blast_email_delivery`. `test_blast_wa_delivery`. `test_blast_fallback_to_email_on_wa_failure`. `test_blast_rate_limit`. `test_blast_logs_communication`. `test_blast_progress_updates`. | ☐ |

### Step 6: Frontend Hooks

| File | Key Content | Done |
|------|-------------|------|
| `frontend/hooks/use-customers.ts` | `useCustomerList(filters?)`: paginated query. `useCustomer(id)`: detail with comms log. `useBlastProgress(blastId)`: SSE stream for live progress. `useCreateCustomer()`, `useUpdateCustomer()`: mutations. `useImportCustomers()`: CSV upload mutation. | ☐ |

### Step 7: Frontend Page

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/(protected)/customers/page.tsx` | **Customer DB & Marketing Page**: List view with sortable columns (name, mobile, breed, entity, last purchase, PDPA badge). Filters: search, breed, entity, PDPA status, date range. Expandable row → full profile (personal details, purchase history, comms log, notes). PDPA badge: inline editable (click → toggle + confirmation dialog). **Blast Composer**: select recipients (all filtered OR manual selection). Recipient summary: total, PDPA opted-in, excluded count with warning. Channel: Email / WhatsApp / Both. Subject line (email). Message body textarea with merge tag buttons ({{name}}, {{breed}}, {{entity}}, {{mobile}}). Send button → confirmation (show excluded count). **Progress**: live progress bar (SSE), success/failure counts. CSV import: upload → column mapping screen → preview → import. | ☐ |

---

## Phase 7 Validation Checklist

- [ ] Customer: create via manual form → persists
- [ ] Customer: CSV import → column mapping → duplicate detection by mobile
- [ ] Segment: filter by breed + entity → correct results
- [ ] Segment: PDPA=false customers automatically excluded
- [ ] Blast: email sends via Resend → CommunicationLog created
- [ ] Blast: WA sends via WA Business API → CommunicationLog created
- [ ] Blast: WA fails → fallback to email → channel switch logged
- [ ] Blast: progress bar updates live via SSE
- [ ] Blast: rate limit 10/sec enforced
- [ ] Blast: PDPA exclusion → warning shows count, opted-out never contacted
- [ ] Comms log: immutable, searchable per customer
- [ ] PDPA toggle: inline edit → confirmation → log recorded
- [ ] `pytest backend/apps/customers/tests/` → all pass
