# Phase 8: Finance Module Completion — Detailed Execution Plan

**Status:** Dashboard ✅ COMPLETE | Finance ⬜ NOT STARTED  
**Target:** 5–7 days | **Dependencies:** Phase 0-7  
**Success Criteria:** P&L accurate, GST reports match ledger, intercompany nets to zero, Excel exports work, all tests pass.

---

## Current State Assessment

| Component | Status | Evidence |
|-----------|--------|----------|
| **Dashboard Backend** | ✅ Complete | `backend/apps/core/services/dashboard.py`, `routers/dashboard.py` exist |
| **Dashboard Frontend** | ✅ Complete | `frontend/app/(protected)/dashboard/page.tsx`, 8 dashboard components |
| **Finance Backend** | ⬜ Not Started | Only `backend/apps/finance/__init__.py` exists |
| **Finance Frontend** | ⬜ Not Started | No /finance page, no use-finance.ts hook |

**Scope Correction:** Phase 8 = Finance module ONLY. Dashboard already complete.

---

## Execution Order

```
Step 1: Backend models → schemas (Day 1)
Step 2: Backend services — pnl.py, gst_report.py (Day 2)
Step 3: Backend router — reports.py (Day 3)
Step 4: Backend admin & tests (Day 4)
Step 5: Frontend hooks — use-finance.ts (Day 5)
Step 6: Frontend components & page (Day 6)
Step 7: Integration, validation & fixes (Day 7)
```

---

## Step 1: Backend Models & Schemas (Day 1)

### 1.1 Models: `backend/apps/finance/models.py`

```python
# 4 Models: Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot

class TransactionType(models.TextChoices):
    REVENUE = "REVENUE", "Revenue"
    EXPENSE = "EXPENSE", "Expense"
    TRANSFER = "TRANSFER", "Transfer"

class TransactionCategory(models.TextChoices):
    SALE = "SALE", "Sale"
    VET = "VET", "Veterinary"
    MARKETING = "MARKETING", "Marketing"
    OPERATIONS = "OPERATIONS", "Operations"
    OTHER = "OTHER", "Other"

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    entity = models.ForeignKey("core.Entity", on_delete=models.CASCADE)
    gst_component = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    date = models.DateField()
    category = models.CharField(max_length=20, choices=TransactionCategory.choices)
    description = models.TextField(blank=True)
    source_agreement = models.ForeignKey(
        "sales.SalesAgreement", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

class IntercompanyTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    from_entity = models.ForeignKey(
        "core.Entity", on_delete=models.CASCADE, related_name="transfers_out"
    )
    to_entity = models.ForeignKey(
        "core.Entity", on_delete=models.CASCADE, related_name="transfers_in"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    created_by = models.ForeignKey("core.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class GSTReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    entity = models.ForeignKey("core.Entity", on_delete=models.CASCADE)
    quarter = models.CharField(max_length=7)  # "2026-Q1"
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_gst = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey("core.User", on_delete=models.CASCADE)

class PNLSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    entity = models.ForeignKey("core.Entity", on_delete=models.CASCADE)
    month = models.DateField()  # First day of month
    revenue = models.DecimalField(max_digits=12, decimal_places=2)
    cogs = models.DecimalField(max_digits=12, decimal_places=2)
    expenses = models.DecimalField(max_digits=12, decimal_places=2)
    net = models.DecimalField(max_digits=12, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)
```

**Checklist:**
- [ ] All 4 models created with proper fields
- [ ] Foreign keys use string references to avoid circular imports
- [ ] Decimal fields use max_digits=12, decimal_places=2
- [ ] Constraints: IntercompanyTransfer balanced (debit=credit)
- [ ] Migration created: `python manage.py makemigrations finance`
- [ ] Migration applied: `python manage.py migrate`

### 1.2 Schemas: `backend/apps/finance/schemas.py`

```python
# Pydantic v2 schemas

class TransactionCreate(Schema):
    type: str  # REVENUE/EXPENSE/TRANSFER
    amount: Decimal
    entity_id: UUID
    date: date
    category: str  # SALE/VET/MARKETING/OPERATIONS/OTHER
    description: str | None = None
    source_agreement_id: UUID | None = None

class TransactionResponse(Schema):
    id: UUID
    type: str
    amount: Decimal
    entity_id: UUID
    gst_component: Decimal
    date: date
    category: str
    description: str | None
    source_agreement_id: UUID | None
    created_at: datetime

class TransactionList(Schema):
    items: list[TransactionResponse]
    total: int

class PNLResponse(Schema):
    entity_id: UUID
    month: date
    revenue: Decimal
    cogs: Decimal
    expenses: Decimal
    net: Decimal
    ytd_revenue: Decimal
    ytd_net: Decimal
    by_category: dict[str, Decimal]

class GSTReportResponse(Schema):
    entity_id: UUID
    quarter: str
    total_sales: Decimal
    total_gst: Decimal
    transactions: list[TransactionResponse]
    generated_at: datetime

class IntercompanyCreate(Schema):
    from_entity_id: UUID
    to_entity_id: UUID
    amount: Decimal
    date: date
    description: str

class IntercompanyResponse(Schema):
    id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    amount: Decimal
    date: date
    description: str
    created_by_id: UUID
    created_at: datetime

class FinanceExportRequest(Schema):
    entity_id: UUID
    period: str  # "2026-04" for P&L, "2026-Q1" for GST
    format: str  # EXCEL or CSV
```

**Checklist:**
- [ ] 7 schemas created with Pydantic v2 syntax
- [ ] All optional fields use `| None` syntax
- [ ] Decimal types preserved (not converted to float)
- [ ] UUID types for all IDs

---

## Step 2: Backend Services (Day 2)

### 2.1 P&L Service: `backend/apps/finance/services/pnl.py`

```python
"""
P&L calculation service.
Formula: Net = Revenue - COGS - Expenses
YTD: Rollup from April (Singapore fiscal year)
"""
from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q
from ..models import Transaction, TransactionType, TransactionCategory

def calc_pnl(entity_id: UUID, month: date) -> PNLResult:
    """
    Calculate P&L for entity and month.
    
    Revenue: SalesAgreement.total_amount for entity+month
    COGS: Transactions where type=EXPENSE, category=SALE
    Expenses: Transactions where type=EXPENSE, category≠SALE
    """
    # Implementation details...
    pass

def calc_ytd(entity_id: UUID, month: date) -> tuple[Decimal, Decimal]:
    """Calculate YTD revenue and net from April to month."""
    # Singapore fiscal year starts April
    pass
```

**Logic Requirements:**
1. Revenue: Sum `SalesAgreement.total_amount` where `entity_id` and month
2. COGS: Sum `Transaction.amount` where `type=EXPENSE`, `category=SALE`, entity, month
3. Expenses: Sum `Transaction.amount` where `type=EXPENSE`, `category≠SALE`, entity, month
4. Net: Revenue - COGS - Expenses
5. YTD: Rollup from April (month 4) to current month
6. Intercompany eliminations: Net out transfers between entities

### 2.2 GST Report Service: `backend/apps/finance/services/gst_report.py`

```python
"""
GST report generation for IRAS filing.
Formats: GST9 (standard), GST109 (simplified)
Thomson entity: 0% GST exempt
Formula: GST = price * 9 / 109, ROUND_HALF_UP
"""
from decimal import Decimal, ROUND_HALF_UP
import openpyxl
from openpyxl import Workbook

def gen_gst_report(entity_id: UUID, quarter: str) -> bytes:
    """Generate GST report Excel for quarter."""
    pass

def gen_pnl_excel(entity_id: UUID, month: date) -> bytes:
    """Generate P&L statement as Excel."""
    pass

def extract_gst_components(entity_id: UUID, quarter: str) -> list[dict]:
    """Extract GST components from SalesAgreement."""
    pass
```

**Checklist:**
- [ ] `gen_gst_report` returns bytes for Excel download
- [ ] GST formula: `price * 9 / 109`, `ROUND_HALF_UP`
- [ ] Thomson entity returns 0 GST
- [ ] IRAS format columns: Description, Value, GST Amount
- [ ] Zero AI interpolation (pure SQL/Python)

---

## Step 3: Backend Router (Day 3)

### 3.1 Reports Router: `backend/apps/finance/routers/reports.py`

```python
"""
Finance router for P&L, GST, transactions, intercompany.
Base: /api/v1/finance/
"""
from ninja import Router
from apps.core.permissions import require_role, scope_entity
from ..models import Transaction, IntercompanyTransfer, GSTReport
from ..schemas import (
    TransactionList, PNLResponse, GSTReportResponse,
    IntercompanyCreate, IntercompanyResponse, FinanceExportRequest
)
from ..services.pnl import calc_pnl
from ..services.gst_report import gen_gst_report, gen_pnl_excel

router = Router(tags=["finance"])

@router.get("/pnl", response=PNLResponse)
def get_pnl(request, entity: UUID, month: date):
    """Get P&L statement for entity and month."""
    pass

@router.get("/gst", response=GSTReportResponse)
def get_gst_report(request, entity: UUID, quarter: str):
    """Get GST report summary for quarter."""
    pass

@router.get("/transactions", response=TransactionList)
def list_transactions(
    request,
    entity: UUID | None = None,
    type: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    per_page: int = 25
):
    """List transactions with filters."""
    pass

@router.post("/intercompany", response=IntercompanyResponse)
@require_role("MANAGEMENT", "ADMIN")
def create_intercompany_transfer(request, payload: IntercompanyCreate):
    """Create intercompany transfer (admin only)."""
    pass

@router.get("/intercompany")
def list_intercompany_transfers(request, entity: UUID | None = None):
    """List intercompany transfers."""
    pass

@router.get("/export/pnl")
def export_pnl_excel(request, entity: UUID, month: date):
    """Download P&L as Excel."""
    pass

@router.get("/export/gst")
def export_gst_excel(request, entity: UUID, quarter: str):
    """Download GST report as Excel."""
    pass
```

**Checklist:**
- [ ] 7 endpoints implemented
- [ ] Entity scoping applied to all list endpoints
- [ ] `@require_role` on intercompany transfer (admin only)
- [ ] Manual pagination for list endpoints (not @paginate)
- [ ] Register in `backend/api/__init__.py`

---

## Step 4: Backend Admin & Tests (Day 4)

### 4.1 Admin: `backend/apps/finance/admin.py`

```python
from django.contrib import admin
from .models import Transaction, IntercompanyTransfer, GSTReport, PNLSnapshot

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_filter = ["type", "entity", "category", "date"]
    list_display = ["type", "amount", "entity", "category", "date"]
    search_fields = ["description"]

@admin.register(IntercompanyTransfer)
class IntercompanyTransferAdmin(admin.ModelAdmin):
    list_display = ["from_entity", "to_entity", "amount", "date"]

@admin.register(GSTReport)
class GSTReportAdmin(admin.ModelAdmin):
    readonly_fields = ["total_sales", "total_gst", "generated_at"]

@admin.register(PNLSnapshot)
class PNLSnapshotAdmin(admin.ModelAdmin):
    readonly_fields = ["revenue", "cogs", "expenses", "net"]
```

### 4.2 Tests: `backend/apps/finance/tests/`

```python
# test_pnl.py - 7 tests
class TestPNLCalculation:
    def test_pnl_calculates_revenue(self): pass
    def test_pnl_calculates_cogs(self): pass
    def test_pnl_calculates_expenses(self): pass
    def test_pnl_net_correct(self): pass
    def test_pnl_ytd_rollup(self): pass
    def test_pnl_intercompany_elimination(self): pass
    def test_pnl_deterministic(self): pass

# test_gst.py - 4 tests
class TestGSTReport:
    def test_gst_sums_components(self): pass
    def test_gst_thomson_zero(self): pass
    def test_gst_iras_format(self): pass
    def test_gst_excel_export(self): pass

# test_transactions.py - 5 tests
class TestTransactionCRUD:
    def test_create_transaction(self): pass
    def test_list_transactions_filtered(self): pass
    def test_entity_scoping(self): pass
    def test_intercompany_transfer(self): pass
    def test_intercompany_balanced(self): pass
```

**Checklist:**
- [ ] 16 total tests (7 P&L + 4 GST + 5 transactions)
- [ ] Test factories created
- [ ] All tests pass: `pytest backend/apps/finance/tests/ -v`

---

## Step 5: Frontend Hooks (Day 5)

### 5.1 use-finance.ts: `frontend/hooks/use-finance.ts`

```typescript
"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { authFetch } from "@/lib/api";
import type { PNLResponse, GSTReportResponse, TransactionList } from "@/lib/types";

// Query hooks
export function usePNL(entityId: string, month: string) {
  return useQuery<PNLResponse>({
    queryKey: ["finance", "pnl", entityId, month],
    queryFn: () => authFetch(`/finance/pnl?entity=${entityId}&month=${month}`),
  });
}

export function useGSTReport(entityId: string, quarter: string) {
  return useQuery<GSTReportResponse>({
    queryKey: ["finance", "gst", entityId, quarter],
    queryFn: () => authFetch(`/finance/gst?entity=${entityId}&quarter=${quarter}`),
  });
}

export function useTransactions(filters: TransactionFilters) {
  return useQuery<TransactionList>({
    queryKey: ["finance", "transactions", filters],
    queryFn: () => authFetch(`/finance/transactions?${new URLSearchParams(filters)}`),
  });
}

// Export mutations
export function useExportPNL() {
  return useMutation({
    mutationFn: async ({ entityId, month }: { entityId: string; month: string }) => {
      const response = await authFetch(`/finance/export/pnl?entity=${entityId}&month=${month}`);
      downloadBlob(response, `pnl-${month}.xlsx`);
    },
  });
}

export function useExportGST() {
  return useMutation({
    mutationFn: async ({ entityId, quarter }: { entityId: string; quarter: string }) => {
      const response = await authFetch(`/finance/export/gst?entity=${entityId}&quarter=${quarter}`);
      downloadBlob(response, `gst-${quarter}.xlsx`);
    },
  });
}
```

**Checklist:**
- [ ] 5 hooks: usePNL, useGSTReport, useTransactions, useExportPNL, useExportGST
- [ ] All hooks typed with Pydantic-generated types
- [ ] Query keys follow TanStack Query best practices
- [ ] Export mutations trigger file download

---

## Step 6: Frontend Components & Page (Day 6)

### 6.1 Finance Page: `frontend/app/(protected)/finance/page.tsx`

**Layout:**
- Tab 1: P&L Statement (monthly selector, table, YTD rollup)
- Tab 2: GST Report (quarter selector, summary table)
- Tab 3: Transaction List (filters, table, pagination)
- Tab 4: Intercompany Transfers (create form + history)

**Components needed:**
- PNLTable
- GSTSummaryTable
- TransactionTable
- IntercompanyForm
- MonthSelector
- QuarterSelector
- ExportButtons

### 6.2 Key TypeScript Types: Update `frontend/lib/types.ts`

```typescript
export interface PNLResponse {
  entity_id: string;
  month: string;
  revenue: string;  // Decimal as string
  cogs: string;
  expenses: string;
  net: string;
  ytd_revenue: string;
  ytd_net: string;
  by_category: Record<string, string>;
}

export interface GSTReportResponse {
  entity_id: string;
  quarter: string;
  total_sales: string;
  total_gst: string;
  transactions: TransactionResponse[];
  generated_at: string;
}

export interface TransactionResponse {
  id: string;
  type: "REVENUE" | "EXPENSE" | "TRANSFER";
  amount: string;
  entity_id: string;
  gst_component: string;
  date: string;
  category: string;
  description: string | null;
  source_agreement_id: string | null;
  created_at: string;
}
```

**Checklist:**
- [ ] /finance page renders without errors
- [ ] All 4 tabs functional
- [ ] P&L table shows correct calculations
- [ ] GST report shows Thomson = 0
- [ ] Transaction filters work
- [ ] Excel export buttons trigger download
- [ ] TypeScript typecheck passes: `npm run typecheck`

---

## Step 7: Integration, Validation & Fixes (Day 7)

### 7.1 Integration Checklist

- [ ] Finance app registered in `backend/config/settings/base.py` INSTALLED_APPS
- [ ] Finance router registered in `backend/api/__init__.py`
- [ ] Frontend /finance link added to sidebar
- [ ] Role-based access: Ground staff cannot access /finance

### 7.2 Validation Checklist

| Test | Method | Expected |
|------|--------|----------|
| P&L calculation | Unit test | revenue - cogs - expenses = net |
| YTD rollup | Unit test | Correct from April fiscal year start |
| Intercompany balance | Unit test | From entity debit = To entity credit |
| Thomson GST | Unit test | 0.00 regardless of sales |
| GST formula | Unit test | 109 → 9.00, 218 → 18.00, 50 → 4.13 |
| Excel export | Manual | File downloads, opens in Excel |
| Role access | E2E | Ground staff 403 on /finance |
| Entity scoping | Unit test | User only sees their entity data |

### 7.3 Final Verification Commands

```bash
# Backend tests
cd /home/project/wellfond-bms/backend
python -m pytest apps/finance/tests/ -v

# Frontend build
cd /home/project/wellfond-bms/frontend
npm run typecheck
npm run build

# Full test suite
cd /home/project/wellfond-bms
pytest backend/ -v --tb=short
```

---

## Phase 8 Success Criteria

| Criterion | Verification | Status |
|-----------|--------------|--------|
| P&L: revenue - COGS - expenses = net | Unit test | ☐ |
| P&L: intercompany nets to zero | Unit test | ☐ |
| P&L: YTD rollup from April | Unit test | ☐ |
| GST: sums match ledger | Unit test | ☐ |
| GST: Thomson = 0 | Unit test | ☐ |
| GST: formula price * 9 / 109 | Unit test | ☐ |
| Finance Excel: downloads work | Manual test | ☐ |
| Role views: unauthorized hidden | E2E test | ☐ |
| TypeScript: 0 errors | npm run typecheck | ☐ |
| Build: succeeds | npm run build | ☐ |
| Tests: all pass | pytest | ☐ |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why | Solution |
|--------------|-----|----------|
| Float for money | Precision loss | Use Decimal throughout |
| Missing entity scoping | Data leakage | Apply scope_entity() to all queries |
| @paginate decorator | Ninja pagination conflict | Manual pagination |
| AI in GST calc | Compliance violation | Pure Python/SQL only |
| Hardcoded fiscal year | Maintainability | Constant SG_FISCAL_START_MONTH = 4 |
| Synchronous Excel gen | Request blocking | Use Celery for large exports |

---

## Daily Progress Tracking

| Day | Task | Status | Blockers |
|-----|------|--------|----------|
| 1 | Models & Schemas | ☐ | |
| 2 | Services (PNL, GST) | ☐ | |
| 3 | Router | ☐ | |
| 4 | Admin & Tests | ☐ | |
| 5 | Frontend Hooks | ☐ | |
| 6 | Frontend Page | ☐ | |
| 7 | Integration & Validation | ☐ | |

---

**Next Action:** Confirm Phase 8 Finance plan and begin Day 1 implementation.
