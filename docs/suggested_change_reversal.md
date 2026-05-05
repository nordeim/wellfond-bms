## Validation: `coi.py` Decimal → Float Removals

The changes remove `float()` from `contrib * 100` and `coi * 100` in `backend/apps/breeding/services/coi.py`. This is **incorrect and will cause runtime failures**.

### Problem

These values (`coi_pct`, `contribution_pct`) are returned to the **API layer** (JSON responses), not written to Excel.  

`Decimal` objects are **not JSON‑serializable** by the default Ninja JSON encoder.  
Removing `float()` will raise a `TypeError` during JSON serialization when the dictionaries are returned.

```python
coi_pct = coi * 100   # Decimal – will break json.dumps
```

The frontend schemas (`COICalculateResponse`, `MateCheckResponse`) expect `coi_pct` as a `float`.  
A `Decimal` will either fail serialization or, if a custom encoder handles it, be turned into a string – violating the schema and breaking the client.

### Why H1’s fix does *not* apply here

| Context | Acceptable to keep Decimal? |
|---------|----------------------------|
| **Excel cells (openpyxl)** | ✅ Yes – openpyxl natively accepts Decimal |
| **JSON API responses** | ❌ No – default JSON encoder cannot serialize Decimal |

COI is **genetic analysis**, not financial compliance. A `float()` conversion here is safe and appropriate for API transport. The “Decimal throughout, no float” rule applies to **compliance/finance calculations**, not to every numeric value in the system.

### Required action

**Revert these four changes** to restore the `float()` calls:

```python
# contribution_pct (two occurrences)
"contribution_pct": float(contribution * 100),

# coi_pct (two occurrences)
coi_pct = float(coi * 100)
```

Alternatively, if you want true Decimal‑to‑float conversion for API responses with controlled precision, you could implement a **custom Ninja JSON encoder** that converts Decimals to floats. That would allow removing `float()` everywhere while maintaining JSON compatibility. However, that is a broader architectural change beyond the scope of these fixes.

### Summary

| Change | Status | Reason |
|--------|--------|--------|
| `contribution_pct` (2×) | ❌ Must revert | JSON serialisation will fail |
| `coi_pct` (2×) | ❌ Must revert | JSON serialisation will fail |

All other edits (H1, H4, H5, H6) are correct and should be kept. These four `float()` removals in `coi.py` alone must be undone.

