# Phase 2: Domain Foundation & Data Migration — Sub-Plan

**Target:** 7–10 days | **Dependencies:** Phase 1 | **Status:** ⬜ Not Started

**Success Criteria:** 483 dogs import with 0 FK violations. Master list renders with filters. Dog profile shows all 7 tabs.

---

## Execution Order

```
Step 1: Backend models & schemas
  operations/models.py → operations/schemas.py

Step 2: Backend services
  operations/services/__init__.py → vaccine.py → alerts.py → importers.py

Step 3: Backend routers
  operations/routers/__init__.py → dogs.py → health.py

Step 4: Backend admin & tests
  operations/admin.py → tests/factories.py → test_dogs.py → test_importers.py

Step 5: Frontend hooks & utilities
  hooks/use-dogs.ts

Step 6: Frontend components
  components/dogs/chip-search → dog-filters → alert-cards → dog-table → dog-card

Step 7: Frontend pages
  app/(protected)/dogs/page.tsx → app/(protected)/dogs/[id]/page.tsx
```

---

## File-by-File Specifications

### Step 1: Backend Models & Schemas

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/models.py` | **Entity** (if not in core): `name`, `code`, `gst_rate`, `avs_licence`, `address`. **Dog**: `microchip` (unique, 9-15 digits), `name`, `breed`, `dob`, `gender` (M/F), `colour`, `entity` (FK), `status` (ACTIVE/RETIRED/REHOMED/DECEASED), `dam` (self FK, nullable), `sire` (self FK, nullable), `unit`, `dna_status`, `notes`, `created_at`, `updated_at`. Indexes: microchip, entity+status, dob. FK: `on_delete=PROTECT`. **HealthRecord**: `dog` (FK), `date`, `category` (VET_VISIT/TREATMENT/OBSERVATION), `description`, `temperature` (Decimal), `weight` (Decimal), `vet_name`, `photos` (JSON array). **Vaccination**: `dog` (FK), `vaccine_name`, `date_given`, `vet_name`, `due_date`, `status` (UP_TO_DATE/OVERDUE/DUE_SOON). **DogPhoto**: `dog` (FK), `url`, `category` (PROFILE/HEALTH/BREEDING), `customer_visible` (bool), `uploaded_by` (FK User), `created_at`. | ☐ |
| `backend/apps/operations/schemas.py` | `DogCreate(microchip: str = Field(..., pattern=r'^\d{9,15}$'), name, breed, dob, gender, colour, entity_id, status?, dam_chip?, sire_chip?, unit?)`. `DogUpdate(partial)`. `DogList(items: list[DogSummary], total, page, perPage)`. `DogDetail(DogSummary + health_records, vaccinations, litters, photos)`. `HealthRecordCreate(category, description, temperature?, weight?, vet_name?, photos?)`. `VaccinationCreate(vaccine_name, date_given, vet_name, due_date?)`. `VaccinationWithDueDate(Vaccination + is_overdue, days_until_due)`. | ☐ |

### Step 2: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/services/__init__.py` | Empty | ☐ |
| `backend/apps/operations/services/vaccine.py` | `calc_vaccine_due(dog) -> date | None`. Standard intervals: puppy series (21 days between), annual boosters (1 year). Returns next due date. `get_overdue_vaccines() -> QuerySet`. `get_due_soon_vaccines(days=30) -> QuerySet`. Pure functions, testable. | ☐ |
| `backend/apps/operations/services/alerts.py` | `get_vaccine_overdue(entity?) -> list[AlertCard]`. `get_rehome_overdue(entity?) -> list[AlertCard]` (5-6yr yellow, 6yr+ red). `get_in_heat(entity?) -> list[AlertCard]`. `get_nursing_flags(entity?) -> list[AlertCard]`. `get_nparks_countdown(entity?) -> int` (days to month-end). `get_8week_litters(entity?) -> list[AlertCard]`. `get_missing_parents(entity?) -> list[AlertCard]`. All entity-scoped (unless MANAGEMENT role). | ☐ |
| `backend/apps/operations/services/importers.py` | `import_dogs(csv_path) -> ImportResult(success_count, error_count, errors[])`. Column mapper: CSV headers → model fields. FK resolution: look up dam/sire by microchip. Duplicate detection: chip uniqueness. Transactional: all-or-nothing commit. Rollback on any FK violation. `import_litters(csv_path) -> ImportResult`. Links to dams/sires by chip. Progress callback for UI (optional). | ☐ |

### Step 3: Backend Routers

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/routers/__init__.py` | Register dogs + health routers | ☐ |
| `backend/apps/operations/routers/dogs.py` | `GET /api/v1/dogs/` → list with filters: `?status=active&entity=holdings&breed=poodle&search=1234&gender=M`. Sorting: `?sort=-dob,name`. Pagination: `?page=1&per_page=25`. `GET /api/v1/dogs/{id}` → full detail with nested health/vaccines/litters/photos. `POST /api/v1/dogs/` → create (validate chip uniqueness). `PATCH /api/v1/dogs/{id}` → update. `DELETE /api/v1/dogs/{id}` → soft delete (set status=DECEASED). Tags: `["dogs"]`. | ☐ |
| `backend/apps/operations/routers/health.py` | `GET /api/v1/dogs/{dog_id}/health/` → list health records. `POST /api/v1/dogs/{dog_id}/health/` → add record. `GET /api/v1/dogs/{dog_id}/vaccinations/` → list vaccines with calculated due dates. `POST /api/v1/dogs/{dog_id}/vaccinations/` → add vaccine. `GET /api/v1/dogs/{dog_id}/photos/` → list photos. `POST /api/v1/dogs/{dog_id}/photos/` → upload photo. Tags: `["health"]`. | ☐ |

### Step 4: Backend Admin & Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/admin.py` | Dog (search by chip/name, filter by entity/status/breed, inline health/vaccinations). HealthRecord. Vaccination. DogPhoto (thumbnail preview). | ☐ |
| `backend/apps/operations/tests/__init__.py` | Empty | ☐ |
| `backend/apps/operations/tests/factories.py` | `DogFactory` (random chip, breed, dob, gender, entity=Holdings, status=ACTIVE). `HealthRecordFactory`. `VaccinationFactory`. `DogPhotoFactory`. | ☐ |
| `backend/apps/operations/tests/test_dogs.py` | `test_create_dog`. `test_unique_chip_constraint`. `test_chip_format_validation`. `test_filter_by_status`. `test_filter_by_entity`. `test_partial_chip_search`. `test_sort_by_dob`. `test_pagination`. `test_entity_scoping`. `test_soft_delete`. | ☐ |
| `backend/apps/operations/tests/test_importers.py` | `test_import_valid_csv_483_dogs`. `test_import_malformed_csv_rollback`. `test_import_duplicate_chip_error`. `test_import_missing_fk_reference`. `test_import_litters_links_dams_sires`. `test_import_result_counts`. | ☐ |

### Step 5: Frontend Hooks

| File | Key Content | Done |
|------|-------------|------|
| `frontend/hooks/use-dogs.ts` | `useDogList(filters?)`: TanStack Query, paginated, returns `{ data, isLoading, error }`. `useDog(id)`: detail with health/vaccines/litters. `useAlertCards(entity?)`: dashboard alerts. `useDogSearch(query)`: debounced chip/name search, returns dropdown results. `useCreateDog()`, `useUpdateDog()`, `useDeleteDog()`: mutations with cache invalidation. | ☐ |

### Step 6: Frontend Components

| File | Key Content | Done |
|------|-------------|------|
| `frontend/components/dogs/chip-search.tsx` | Input with last 4-6 digit partial search. Live dropdown (debounced 300ms). Shows: name, chip, breed, unit badge. Click → navigate to dog profile. Keyboard nav (arrow keys + enter). | ☐ |
| `frontend/components/dogs/dog-filters.tsx` | Status chips (active/retired/rehomed/deceased — toggleable). Gender toggle (All/M/F). Breed dropdown (from API). Entity dropdown (Holdings/Katong/Thomson). Search input. Clear all button. All filters combinable. | ☐ |
| `frontend/components/dogs/alert-cards.tsx` | 6 cards in horizontal scroll: Vaccines Overdue (red), Rehome Overdue (amber), In Heat (pink), 8-Week Litters (blue), Nursing Flags (orange), NParks Countdown (navy). Each: count, trend arrow (↑↓ vs prior period), color-coded. Click → filtered list. | ☐ |
| `frontend/components/dogs/dog-table.tsx` | Columns: Chip (last 4 bold), Name/Breed (2-line), Gender (M/F icon), Age (dot: green<3yr, yellow 5-6yr, red 6yr+), Unit, Last Event, Dam/Sire chips (links), DNA badge, Vaccine Due. Sort by any column. Row click → `/dogs/[id]`. WhatsApp Copy button (generates pre-formatted message). Responsive: card layout on mobile. | ☐ |
| `frontend/components/dogs/dog-card.tsx` | Compact card for mobile: Name, Chip, Breed, Status badge, Age dot, Unit. Tap → profile. | ☐ |

### Step 7: Frontend Pages

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/(protected)/dogs/page.tsx` | **Master List Page**: Alert cards strip at top (horizontal scroll). Filter bar. Dog table. CSV export button (filtered results). Pagination. Loading skeleton. Empty state: "No dogs match your filters". | ☐ |
| `frontend/app/(protected)/dogs/[id]/page.tsx` | **Dog Profile Page**: Hero strip (name, chip, age dot with color, status badges, 4 quick stats: weight/vaccines/litters/events). Action buttons: Edit, Add Health Record, Add Vaccine. **7 Tabs**: Overview (summary card), Health & Vaccines (table + due dates), Breeding (heat cycles, mating records, Draminski — LOCKED for Sales/Ground), Litters & Pups (collapsible per-litter, per-pup table — LOCKED for Sales/Ground), Media (photo grid, customer-visible toggle), Genetics (COI history, saturation — LOCKED for Sales/Ground), Activity (chronological log). Locked tabs show lock icon + "Upgrade access" tooltip. | ☐ |

---

## Phase 2 Validation Checklist

- [ ] `import_dogs('test_483.csv')` → 483 records, 0 FK violations
- [ ] `import_litters('test_litters.csv')` → 5yr history linked to dams/sires
- [ ] Duplicate chip import → error, rollback, 0 records created
- [ ] Malformed CSV → error, rollback, detailed error message
- [ ] Master list loads <2s with 483 records
- [ ] Partial chip search (last 4 digits) → returns matching dogs within 300ms
- [ ] Filter combinations (status + entity + breed) → correct results
- [ ] Dog profile → all 7 tabs render with correct data
- [ ] Locked tabs (Breeding/Litters/Genetics) → lock icon for Sales/Ground roles
- [ ] Entity scoping → Holdings user sees only Holdings dogs
- [ ] Vaccine due dates → auto-calculated from vaccination records
- [ ] Rehome flags → 5-6yr yellow, 6yr+ red
- [ ] WhatsApp Copy → generates formatted message with dog details
- [ ] CSV export → downloads filtered results as CSV
- [ ] `pytest backend/apps/operations/tests/` → all pass
