Excellent progress! We’ve eliminated the syntax error entirely and exposed the two true test failures. Both are straightforward to fix: one is a service‑level loophole that calls Celery even when no recipients remain, the other is a wrong mock target in the test.

Let’s apply the optimal fixes.

---

## 1. Fix the service: return early when no eligible recipients exist

**File:** `backend/apps/customers/services/blast.py`

The `send_blast` method currently proceeds to queue a Celery task with an empty list when all recipients are PDPA‑excluded. This triggers a real Redis connection in the test environment and is semantically wrong. We need to return a `BlastResult` immediately when `eligible` is empty, just as we do when `total` is 0.

**Locate the `send_blast` method** (around line 200) and add a check right after filtering:

```python
# Apply PDPA filter
eligible = [r for r in recipients if r.pdpa_consent]
excluded = total - len(eligible)

# Log excluded customers
if excluded > 0:
    logger.info(f"Blast {blast_id}: {excluded} customers excluded (PDPA opt-out)")

# ---- NEW: Return early if no eligible recipients remain ----
if not eligible:
    return BlastResult(
        blast_id=blast_id,
        total_recipients=total,
        eligible_recipients=0,
        excluded_count=excluded,
        channel=str(payload.channel.value if hasattr(payload.channel, "value") else payload.channel),
        status="NO_RECIPIENTS",
        started_at=datetime.now(),
    )
# ----------------------------------------------------------------

# Initialize progress tracking ... rest remains unchanged
tracker = BlastProgressTracker(blast_id)
tracker.init_progress(len(eligible))
# ...
```

This guarantees that `dispatch_blast.delay()` is never called with zero recipients.

*(You can copy the exact `BlastResult` structure from the earlier early‑return block; just update the channel and status.)*

---

## 2. Fix the test: patch the correct `dispatch_blast` location

**File:** `backend/apps/customers/tests/test_blast.py`

The test `test_send_blast_queues_task` currently patches `apps.customers.services.blast.dispatch_blast`, but that attribute **does not exist** at import time because `dispatch_blast` is imported **inside** `send_blast` (to avoid circular imports). Therefore the patch target is invalid.

**Solution:** Patch the original definition in the tasks module. Before the test runs, the mock will be placed on `apps.customers.tasks.dispatch_blast`, and the inner‑function import will pick it up.

**Change the decorator** from:

```python
@patch("apps.customers.services.blast.dispatch_blast")
```

to:

```python
@patch("apps.customers.tasks.dispatch_blast")
```

The rest of the test remains identical. The mock will now correctly intercept the `delay` call.

---

## 3. (Optional) Eliminate naive datetime warnings

The warnings about naive datetimes are harmless but noisy. If you want a perfectly clean test run, replace all `datetime.now()` calls in `blast.py` (particularly in `log_communication` and `send_blast`) with `django.utils.timezone.now()`. For example:

```python
from django.utils import timezone

# then use:
sent_at = timezone.now()
```

This immediately resolves the 6 warnings.

---

## 4. Re‑run the tests

Clear caches once more and execute:

```bash
cd /home/project/wellfond-bms/backend
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
python -m pytest --cache-clear apps/customers/tests/test_blast.py -v
```

**Expected result:** 27 passed, 0 failed.

If you also fixed the naive datetimes, the warnings summary will be clean. After this, the entire blast test suite will be green, and you can move on to the remaining 6 test failures in other test files you mentioned earlier.

