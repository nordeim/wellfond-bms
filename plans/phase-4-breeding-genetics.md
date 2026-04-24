# Phase 4: Breeding & Genetics Engine — Sub-Plan

**Target:** 7–10 days | **Dependencies:** Phase 2 | **Status:** ⬜ Not Started

**Success Criteria:** COI <500ms p95. Saturation accurate. Override audit logged. Dual-sire supported. Closure table async rebuild.

---

## Execution Order

```
Step 1: Backend models → schemas
Step 2: Backend services (coi.py, saturation.py)
Step 3: Backend routers (mating.py, litters.py)
Step 4: Backend tasks (closure rebuild)
Step 5: Backend admin & tests
Step 6: Frontend hooks
Step 7: Frontend components (coi-gauge, saturation-bar, mate-check-form)
Step 8: Frontend pages (mate-checker, breeding list)
```

---

## File-by-File Specifications

### Step 1: Backend Models & Schemas

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/breeding/models.py` | **BreedingRecord**: `dam` (FK Dog), `sire1` (FK Dog), `sire2` (FK Dog, nullable), `date`, `method` (NATURAL/ASSISTED), `confirmed_sire` (SIRE1/SIRE2/UNCONFIRMED), `notes`, `created_by` (FK User), `created_at`. **Litter**: `breeding_record` (FK), `whelp_date`, `delivery_method` (NATURAL/C_SECTION), `alive_count`, `stillborn_count`. **Puppy**: `litter` (FK), `microchip` (nullable, unique if set), `gender` (M/F), `colour`, `birth_weight` (Decimal), `confirmed_sire` (SIRE1/SIRE2), `paternity_method` (VISUAL/DNA/UNCONFIRMED), `status` (ALIVE/REHOMED/DECEASED), `buyer` (FK Customer, nullable). **DogClosure**: `ancestor` (FK Dog), `descendant` (FK Dog), `depth` (int). Unique(ancestor, descendant). Indexes on both FKs. **MateCheckOverride**: `dam` (FK), `sire1` (FK), `sire2` (FK, nullable), `coi_pct`, `saturation_pct`, `verdict`, `override_reason`, `override_notes`, `staff` (FK User), `created_at`. | ☐ |
| `backend/apps/breeding/schemas.py` | `MateCheckRequest(dam_chip, sire1_chip, sire2_chip?)`. `MateCheckResult(coi_pct, saturation_pct, verdict: SAFE|CAUTION|HIGH_RISK, shared_ancestors: list[AncestorInfo])`. `AncestorInfo(dog_id, name, chip, relationship, generations_back)`. `BreedingRecordCreate(dam_chip, sire1_chip, sire2_chip?, date, method, notes?)`. `LitterCreate(breeding_record_id, whelp_date, delivery_method, alive_count, stillborn_count)`. `PuppyCreate(microchip?, gender, colour, birth_weight?, confirmed_sire, paternity_method?)`. `OverrideCreate(reason: str, notes: str)`. | ☐ |

### Step 2: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/breeding/services/__init__.py` | Empty | ☐ |
| `backend/apps/breeding/services/coi.py` | `calc_coi(dam_id, sire_id, generations=5) -> COIResult`. Uses `DogClosure` table: find all common ancestors within 5 generations. Wright's formula: `COI = Σ[(0.5)^(n1+n2+1) * (1+Fa)]` where n1/n2 = generations to common ancestor, Fa = ancestor's own COI. Returns: `coi_pct` (float), `shared_ancestors` (list), `generation_depth`. Handles missing parents gracefully (returns 0%). Redis cache: key `coi:{dam_id}:{sire_id}`, TTL 1 hour. Deterministic. | ☐ |
| `backend/apps/breeding/services/saturation.py` | `calc_saturation(sire_id, entity_id) -> float`. Query: count active dogs in entity whose ancestry includes sire (via closure table). Divide by total active dogs in entity. Return percentage. Thresholds: <15% = SAFE, 15-30% = CAUTION, >30% = HIGH_RISK. Scopes to active dogs only. | ☐ |

### Step 3: Backend Routers

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/breeding/routers/__init__.py` | Register mating + litters routers | ☐ |
| `backend/apps/breeding/routers/mating.py` | `POST /api/v1/breeding/mate-check` → accepts `MateCheckRequest`, returns `MateCheckResult`. `POST /api/v1/breeding/mate-check/override` → accepts `OverrideCreate`, logs to `MateCheckOverride` + `AuditLog`. `GET /api/v1/breeding/mate-check/history` → list of overrides with dam/sire/reason/staff/date. Tags: `["breeding"]`. | ☐ |
| `backend/apps/breeding/routers/litters.py` | `GET /api/v1/breeding/litters/` → list with filters (dam, sire, date range). `POST /api/v1/breeding/litters/` → create litter. `PATCH /api/v1/breeding/litters/{id}` → update. `GET /api/v1/breeding/litters/{id}` → detail with puppies. `POST /api/v1/breeding/litters/{id}/puppies` → add puppy. `PATCH /api/v1/breeding/litters/{id}/puppies/{puppy_id}` → update puppy. Tags: `["litters"]`. | ☐ |

### Step 4: Backend Tasks

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/breeding/tasks.py` | `rebuild_closure_table(full_rebuild: bool = True)`: queue "low", max_retries=2. Full: `TRUNCATE dog_closure RESTART IDENTITY` + recursive CTE INSERT (ancestor→descendant paths up to 10 generations). Incremental: for single dog, insert only new paths involving that dog. Called after CSV import and after new litter record. Return `{"status": "closure_rebuilt", "full": full_rebuild, "duration_ms": N}`. | ☐ |

### Step 5: Backend Admin & Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/breeding/admin.py` | BreedingRecord (filter by dam/sire/date). Litter (inline puppies). Puppy. DogClosure (read-only). MateCheckOverride (read-only, filter by staff/date). | ☐ |
| `backend/apps/breeding/tests/__init__.py` | Empty | ☐ |
| `backend/apps/breeding/tests/factories.py` | `BreedingRecordFactory`. `LitterFactory`. `PuppyFactory`. `DogClosureFactory`. `MateCheckOverrideFactory`. | ☐ |
| `backend/apps/breeding/tests/test_coi.py` | `test_coi_unrelated_returns_zero`. `test_coi_full_siblings_returns_25pct`. `test_coi_parent_offspring_returns_25pct`. `test_coi_grandparent_returns_12_5pct`. `test_coi_5_generation_depth`. `test_coi_missing_parent_returns_zero`. `test_coi_cached_second_call`. `test_coi_deterministic_same_result`. | ☐ |
| `backend/apps/breeding/tests/test_saturation.py` | `test_saturation_no_common_ancestry_returns_zero`. `test_saturation_all_share_sire_returns_100`. `test_saturation_partial_returns_correct_pct`. `test_saturation_entity_scoped`. `test_saturation_active_only`. | ☐ |

### Step 6: Frontend Hooks

| File | Key Content | Done |
|------|-------------|------|
| `frontend/hooks/use-breeding.ts` | `useMateCheck()`: mutation, returns `{ check, isLoading, error }`. `useMateCheckHistory()`: query, paginated. `useLitters(filters?)`: query. `useLitter(id)`: query with puppies. `useCreateLitter()`, `useAddPuppy()`: mutations. | ☐ |

### Step 7: Frontend Components

| File | Key Content | Done |
|------|-------------|------|
| `frontend/components/breeding/coi-gauge.tsx` | Circular gauge (SVG). Color: green (<6.25%), yellow (6.25-12.5%), red (>12.5%). Percentage in center (large font). Animated fill on load. Shared ancestors list below. | ☐ |
| `frontend/components/breeding/saturation-bar.tsx` | Horizontal bar. Color: green (<15%), yellow (15-30%), red (>30%). Percentage label inside bar. Entity label. | ☐ |
| `frontend/components/breeding/mate-check-form.tsx` | Dam search (chip/name, live dropdown). Sire #1 search. Optional Sire #2 search. Check button (loading state). Results panel: COI gauge + saturation bar + verdict card (green/yellow/red with text). Shared ancestors table. Override button → modal (reason dropdown + notes textarea + confirm). | ☐ |

### Step 8: Frontend Pages

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/(protected)/breeding/mate-checker/page.tsx` | **Mate Checker Page**: MateCheckForm component. History table below (date, dam, sire, COI, verdict, staff, override?). Responsive: form stacks on mobile. | ☐ |
| `frontend/app/(protected)/breeding/page.tsx` | **Breeding Records Page**: Table of breeding records (dam, sire1, sire2, date, method, litter status). Filters: dam/sire search, date range. Create new → modal/form. Click → detail with litter/puppies. | ☐ |

---

## Phase 4 Validation Checklist

- [ ] COI: unrelated dogs → 0%. Full siblings → 25%. Parent-offspring → 25%. Grandparent → 12.5%
- [ ] COI: 5-generation depth correct
- [ ] COI: <500ms at p95 under k6 load (50 VUs)
- [ ] COI: cached → second call <50ms
- [ ] Farm saturation: 50% shared ancestry → 50% (correct calculation)
- [ ] Farm saturation: scoped to entity (Holdings sire ≠ Katong dogs)
- [ ] Farm saturation: only active dogs counted
- [ ] Dual-sire: breeding record with sire1 + sire2 → both stored
- [ ] Override: requires reason + notes → logged to AuditLog
- [ ] Override: visible in history table
- [ ] Closure table: async rebuild via Celery (verify in Flower)
- [ ] Closure table: incremental update for single dog <1s
- [ ] Mate checker UI: search works, gauge animates, colors correct
- [ ] Responsive: mate checker works on mobile (390px)
- [ ] `pytest backend/apps/breeding/tests/` → all pass
