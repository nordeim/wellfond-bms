# Phase 3: Ground Operations & Mobile PWA — Sub-Plan

**Target:** 10–14 days | **Dependencies:** Phase 2 | **Status:** ⬜ Not Started

**Success Criteria:** All 7 log types persist. Draminski trends render. SSE delivers <500ms. Offline queue syncs on reconnect. PWA installs.

---

## Execution Order

```
Step 1: Backend models (extend operations/models.py)
Step 2: Backend schemas (extend operations/schemas.py)
Step 3: Backend services (draminski.py, extend alerts.py)
Step 4: Backend routers (logs.py, stream.py)
Step 5: Backend tasks (Celery)
Step 6: Backend tests
Step 7: Frontend ground layout & pages
Step 8: Frontend ground components
Step 9: Frontend PWA (sw.ts, offline-queue.ts, register.ts)
Step 10: Frontend hooks (use-sse.ts, use-offline-queue.ts)
```

---

## File-by-File Specifications

### Step 1: Backend Models (extend)

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/models.py` (add) | **InHeatLog**: `dog` (FK), `draminski_reading` (int), `mating_window` (str: EARLY/RISING/FAST/PEAK/MATE_NOW), `notes`, `staff` (FK User), `created_at`. **MatedLog**: `dog` (FK), `sire` (FK Dog), `method` (NATURAL/ASSISTED), `sire2` (FK Dog, nullable), `notes`, `staff`, `created_at`. **WhelpedLog**: `dog` (FK), `method` (NATURAL/C_SECTION), `alive_count` (int), `stillborn_count` (int), `notes`, `staff`, `created_at`. **WhelpedPup**: `log` (FK WhelpedLog), `gender` (M/F). **HealthObsLog**: `dog` (FK), `category` (LIMPING/SKIN/NOT_EATING/EYE_EAR/INJURY/OTHER), `description`, `temperature` (Decimal), `weight` (Decimal), `photos` (JSON), `staff`, `created_at`. **WeightLog**: `dog` (FK), `weight` (Decimal), `staff`, `created_at`. **NursingFlagLog**: `dog` (FK), `section` (MUM/PUP), `pup_number` (int, nullable), `flag_type` (NO_MILK/REJECTING_PUP/PUP_NOT_FEEDING/OTHER), `photos` (JSON), `severity` (SERIOUS/MONITORING), `staff`, `created_at`. **NotReadyLog**: `dog` (FK), `notes`, `edd` (date, nullable), `staff`, `created_at`. All: auto-capture `staff=request.user`, `created_at=now()`. | ☐ |

### Step 2: Backend Schemas (extend)

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/schemas.py` (add) | `InHeatCreate(draminski: int = Field(..., ge=0, le=999), notes?)`. `MatedCreate(sire_chip: str, method, sire2_chip?)`. `WhelpedCreate(method, alive_count, stillborn_count, pups: list[PupGender])`. `HealthObsCreate(category, description, temperature?, weight?, photos: list[str])`. `WeightCreate(weight: Decimal)`. `NursingFlagCreate(section, pup_number?, flag_type, photos?, severity)`. `NotReadyCreate(notes?, edd?)`. `LogResponse(id, type, dog_id, created_at, staff_name)`. | ☐ |

### Step 3: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/services/draminski.py` | `interpret(dog_id, reading) -> DraminskiResult`. Per-dog baseline: fetch last 30 readings, compute mean. Thresholds: `<baseline*0.5` = early, `0.5-1.0` = rising (daily readings), `1.0-1.5` = fast, `>1.5 or max` = peak, `post-peak drop >10%` = MATE_NOW. `calc_window(history) -> MatingWindow`. 7-day trend array: `[{date, reading, zone}]`. Pure math, no AI. | ☐ |
| `backend/apps/operations/services/alerts.py` (extend) | `get_pending_alerts(user) -> list[AlertEvent]` for SSE. Deduplicates by dog+type. Timestamped. Entity-scoped. Returns: nursing flags, heat cycles, overdue vaccines, rehome overdue. | ☐ |

### Step 4: Backend Routers

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/routers/logs.py` | `POST /api/v1/operations/logs/in-heat/{dog_id}`. `POST /api/v1/operations/logs/mated/{dog_id}`. `POST /api/v1/operations/logs/whelped/{dog_id}`. `POST /api/v1/operations/logs/health-obs/{dog_id}`. `POST /api/v1/operations/logs/weight/{dog_id}`. `POST /api/v1/operations/logs/nursing-flag/{dog_id}`. `POST /api/v1/operations/logs/not-ready/{dog_id}`. `GET /api/v1/operations/logs/{dog_id}` → chronological all types. All POST require `X-Idempotency-Key`. Auto-capture `request.user`. Tags: `["ground-logs"]`. | ☐ |
| `backend/apps/operations/routers/stream.py` | `GET /api/v1/operations/stream/alerts` → `StreamingHttpResponse(content_type='text/event-stream')`. Async generator: poll `get_pending_alerts(user)` every 5s. Format: `data: {json}\n\n`. Reconnect-safe (client handles). Filters by user role/entity. SSE headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`. | ☐ |

### Step 5: Backend Tasks

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/tasks.py` | `rebuild_closure_table(full_rebuild=False)` → queue: low, max_retries=2. Full: TRUNCATE + recursive CTE. Incremental: insert new ancestor-descendant pairs for single dog. `check_overdue_vaccines()` → daily 8am SGT, creates alerts. `check_rehome_overdue()` → daily 8am SGT. `notify_management(log_type, dog_id)` → sends SSE event. | ☐ |

### Step 6: Backend Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/operations/tests/test_logs.py` | `test_create_in_heat_log`. `test_create_mated_log_with_sire2`. `test_create_whelped_log_with_pups`. `test_create_health_obs_with_photo`. `test_create_weight_log`. `test_create_nursing_flag_serious_notifies`. `test_create_not_ready_with_edd`. `test_log_auto_captures_user`. `test_log_auto_captures_timestamp`. `test_idempotency_prevents_duplicate`. `test_missing_idempotency_key_returns_400`. | ☐ |
| `backend/apps/operations/tests/test_draminski.py` | `test_interpret_below_200_early`. `test_interpret_200_400_rising`. `test_interpret_above_400_fast`. `test_interpret_peak_highest_recorded`. `test_interpret_post_peak_drop_mate_now`. `test_per_dog_baseline_not_global`. `test_trend_array_7_days`. `test_calc_window_returns_correct_range`. | ☐ |

### Step 7: Frontend Ground Layout & Pages

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/ground/layout.tsx` | Bottom nav (no sidebar). High-contrast mode: `#0D2030` text on `#DDEEFF` bg. 44px minimum tap targets. No horizontal scroll. Status bar safe area. | ☐ |
| `frontend/app/ground/page.tsx` | **Ground Staff Home**: Chip scanner hero (large input, auto-focus). Camera scan button (BarcodeDetector → file input fallback). Dog search results: name, breed, unit badge, in-heat status. Quick stats: in-heat count, nursing flags, active litters, vaccine due. Recent logs (last 5). | ☐ |
| `frontend/app/ground/log/[type]/page.tsx` | **Dynamic log form by type**: `in-heat`: large numpad for Draminski reading, 7-day trend chart (line), mating window slider (auto-adjusts), notes textarea, auto-timestamp. `mated`: sire chip search, method toggle (Natural/Assisted), optional Sire #2 search, auto-timestamp. `whelped`: method toggle, alive/stillborn counters (+/- buttons), per-pup gender M/F taps, auto-timestamp. `health-obs`: category selector (6 buttons), description textarea, temp/weight inputs, photo upload (required), auto-timestamp. `weight`: numpad for kg, history bar chart, auto-timestamp. `nursing-flag`: Mum Problems / Pup Problems tabs, pup number selector, flag type buttons, photo (required for serious), auto-timestamp. `not-ready`: one-tap button, optional notes, EDD date picker, auto-timestamp. All: dog info header (name, chip, breed), submit button with loading, offline queue integration. | ☐ |

### Step 8: Frontend Ground Components

| File | Key Content | Done |
|------|-------------|------|
| `frontend/components/ground/numpad.tsx` | Large numeric buttons (48px). Decimal point. Clear (C). Backspace (⌫). Display shows current value (large font). Submit button. Touch-friendly, no tiny buttons. | ☐ |
| `frontend/components/ground/draminski-chart.tsx` | 7-day line chart (Canvas or SVG). Today's reading highlighted (orange dot). Color zones: green (<baseline*0.5), yellow (0.5-1.0), orange (1.0-1.5), red (>1.5). X-axis: dates. Y-axis: readings. Responsive. | ☐ |
| `frontend/components/ground/log-form.tsx` | Base wrapper for all log forms. Dog info header (name, chip, breed, unit). Auto-timestamp display (live clock). Submit button with idempotency key generation. Loading state. Error state with retry. Offline queue integration (queue if offline). | ☐ |
| `frontend/components/ground/camera-scan.tsx` | Camera API: `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })`. BarcodeDetector API for microchip barcodes. Fallback: file input with image upload. Returns chip number string. Close button. | ☐ |

### Step 9: Frontend PWA

| File | Key Content | Done |
|------|-------------|------|
| `frontend/lib/pwa/sw.ts` | Service worker. `install`: precache app shell (HTML, CSS, JS, icons). `fetch`: cache-first for static assets, network-first for API calls, cache fallback for offline. `sync`: background sync for queued POSTs. Cache versioning: `v1`, `v2` on update. Offline fallback page. | ☐ |
| `frontend/lib/pwa/register.ts` | `navigator.serviceWorker.register('/sw.ts')`. Handle update prompt (toast: "Update available, refresh?"). Check connectivity on mount. Trigger `flushQueue()` on reconnect. | ☐ |
| `frontend/lib/offline-queue.ts` | IndexedDB wrapper (DB: `wellfond-offline`, store: `log-queue`). `queueLog(type, payload, dogId)`: generates UUIDv4, stores with timestamp. `flushQueue()`: iterate queue, POST each, remove on 200/201. `getQueueCount()`: returns pending count. Conflict: server wins (show toast "This log was already recorded"). Retry: 3 attempts with exponential backoff. | ☐ |

### Step 10: Frontend Hooks

| File | Key Content | Done |
|------|-------------|------|
| `frontend/hooks/use-sse.ts` | `useAlertStream()`: connects to `/api/proxy/operations/stream/alerts` via `EventSource`. Auto-reconnect on drop (3s delay). Parses `data:` events as typed `AlertEvent[]`. Returns `{ alerts, isConnected, error }`. Cleanup on unmount. | ☐ |
| `frontend/hooks/use-offline-queue.ts` | `useOfflineQueue()`: returns `{ queueCount, isOnline, flushQueue }`. Listens to `online`/`offline` events. Auto-flush on reconnect. Badge: "3 logs pending" when count > 0. | ☐ |

---

## Phase 3 Validation Checklist

- [ ] All 7 log types persist with correct metadata (staff, timestamp)
- [ ] Draminski: reading 150 → "Early" (green). Reading 350 → "Rising" (yellow). Reading 450 → "Fast" (orange). Highest ever → "Peak" (red). Drop after peak → "MATE NOW" (red pulse)
- [ ] Draminski per-dog: same reading = different zone for different dogs
- [ ] 7-day trend chart renders with correct data points
- [ ] SSE: nursing flag created → alert delivered <500ms
- [ ] SSE: auto-reconnect on connection drop (verify in Network tab)
- [ ] Offline: go offline → submit 3 logs → go online → all 3 sync
- [ ] Offline: badge shows "3 logs pending"
- [ ] Conflict: log already on server → toast "already recorded", no duplicate
- [ ] PWA: install on iOS/Android → home screen icon, standalone mode
- [ ] PWA: Lighthouse score ≥90
- [ ] Camera: opens camera → scans barcode → returns chip number
- [ ] Camera fallback: no camera → file input → upload image → extract chip
- [ ] 44px tap targets verified on 390px viewport
- [ ] High-contrast: `#0D2030` on `#DDEEFF` passes WCAG AA
- [ ] `pytest backend/apps/operations/tests/test_logs.py` → all pass
- [ ] `pytest backend/apps/operations/tests/test_draminski.py` → all pass
