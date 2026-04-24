# Phase 8: Dashboard & Finance Exports — Sub-Plan

**Target:** 7–10 days | **Dependencies:** Phase 2–7 | **Status:** ⬜ Not Started

**Success Criteria:** Dashboard loads <2s. Alerts accurate. Finance exports match ledger. Role views correct.

---

## Execution Order

```
Step 1: Backend models → schemas
Step 2: Backend services (pnl.py, gst_report.py)
Step 3: Backend router (reports.py)
Step 4: Backend admin & tests
Step 5: Frontend hooks
Step 6: Frontend components (dashboard/)
Step 7: Frontend pages (dashboard, finance)
```

---

## File-by-File Specifications

### Step 1: Backend Models & Schemas

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/finance/models.py` | **Transaction**: `type` (REVENUE/EXPENSE/TRANSFER), `amount` (Decimal), `entity` (FK), `gst_component` (Decimal), `date`, `category` (SALE/VET/MARKETING/OPERATIONS/OTHER), `description`, `source_agreement` (FK SalesAgreement, nullable), `created_at`. **IntercompanyTransfer**: `from_entity` (FK), `to_entity` (FK), `amount` (Decimal), `date`, `description`, `created_by` (FK User), `created_at`. Constraint: debit=credit (balanced). **GSTReport**: `entity` (FK), `quarter` (str, e.g. "2026-Q1"), `total_sales` (Decimal), `total_gst` (Decimal), `generated_at`, `generated_by` (FK User). **PNLSnapshot**: `entity` (FK), `month` (date), `revenue` (Decimal), `cogs` (Decimal), `expenses` (Decimal), `net` (Decimal), `generated_at`. | ☐ |
| `backend/apps/finance/schemas.py` | `TransactionCreate(type, amount, entity_id, date, category, description?, source_agreement_id?)`. `TransactionList(items, total)`. `PNLResponse(entity, month, revenue, cogs, expenses, net, ytd_revenue, ytd_net)`. `GSTReportResponse(entity, quarter, total_sales, total_gst, transactions[])`. `IntercompanyCreate(from_entity_id, to_entity_id, amount, date, description)`. `FinanceExport(entity, period, format: EXCEL|CSV)`. | ☐ |

### Step 2: Backend Services

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/finance/services/__init__.py` | Empty | ☐ |
| `backend/apps/finance/services/pnl.py` | `calc_pnl(entity_id, month) -> PNLResult`. Revenue: sum SalesAgreement total_amount for entity+month. COGS: sum Transaction(type=EXPENSE, category=SALE). Expenses: sum Transaction(type=EXPENSE, !category=SALE). Net: revenue - COGS - expenses. YTD: rollup from April (SG fiscal year). Intercompany eliminations: net out transfers between entities. Groups by category. Deterministic. | ☐ |
| `backend/apps/finance/services/gst_report.py` | `gen_gst_report(entity_id, quarter) -> bytes`. Sums GST components from SalesAgreement for period. IRAS format: GST9 (standard) / GST109 (simplified). Excel export via openpyxl. Zero AI interpolation. Entity-specific: Thomson = 0 GST. `gen_pnl_excel(entity_id, month) -> bytes`. P&L statement as Excel. | ☐ |

### Step 3: Backend Router

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/finance/routers/__init__.py` | Register reports router | ☐ |
| `backend/apps/finance/routers/reports.py` | `GET /api/v1/finance/pnl?entity=&month=` → P&L statement. `GET /api/v1/finance/gst?entity=&quarter=` → GST report summary. `GET /api/v1/finance/transactions?entity=&type=&category=&date_from=&date_to=` → transaction list. `POST /api/v1/finance/intercompany` → create transfer. `GET /api/v1/finance/export/pnl?entity=&month=` → Excel download. `GET /api/v1/finance/export/gst?entity=&quarter=` → Excel download. `GET /api/v1/dashboard/metrics?role=` → role-aware dashboard data (alerts, counts, charts). Tags: `["finance", "dashboard"]`. | ☐ |

### Step 4: Backend Admin & Tests

| File | Key Content | Done |
|------|-------------|------|
| `backend/apps/finance/admin.py` | Transaction (filter by type/entity/category/date). IntercompanyTransfer. GSTReport (read-only). PNLSnapshot (read-only). | ☐ |
| `backend/apps/finance/tests/__init__.py` | Empty | ☐ |
| `backend/apps/finance/tests/__init__.py` | Empty | ☐ |
| `backend/apps/finance/tests/factories.py` | `TransactionFactory`. `IntercompanyTransferFactory`. `GSTReportFactory`. `PNLSnapshotFactory`. | ☐ |
| `backend/apps/finance/tests/test_pnl.py` | `test_pnl_calculates_revenue`. `test_pnl_calculates_cogs`. `test_pnl_calculates_expenses`. `test_pnl_net_correct`. `test_pnl_ytd_rollup`. `test_pnl_intercompany_elimination`. `test_pnl_deterministic`. | ☐ |
| `backend/apps/finance/tests/test_gst.py` | `test_gst_sums_components`. `test_gst_thomson_zero`. `test_gst_iras_format`. `test_gst_excel_export`. | ☐ |

### Step 5: Frontend Hooks

| File | Key Content | Done |
|------|-------------|------|
| `frontend/hooks/use-dashboard.ts` | `useDashboardMetrics(role)`: query, returns role-specific data. `useAlertCards()`: real-time alerts. `useActivityFeed()`: SSE stream for recent logs. `useRevenueChart(entity?, month?)`: bar chart data. | ☐ |
| `frontend/hooks/use-finance.ts` | `usePNL(entity, month)`: query. `useGSTReport(entity, quarter)`: query. `useTransactions(filters)`: paginated query. `useExportPNL()`, `useExportGST()`: mutations triggering download. | ☐ |

### Step 6: Frontend Components

| File | Key Content | Done |
|------|-------------|------|
| `frontend/components/dashboard/nparks-countdown.tsx` | Days to month-end submission. Pending records flagged (count). Blue gradient card. Click → /compliance. | ☐ |
| `frontend/components/dashboard/alert-feed.tsx` | Last 10 ground staff + admin logs. SSE-powered (auto-updates). Each: icon (log type), description, dog name, staff name, timestamp. Scrollable. | ☐ |
| `frontend/components/dashboard/revenue-chart.tsx` | Month-to-date revenue by entity. Bar chart (3 bars: Holdings, Katong, Thomson). Responsive. Colors: Holdings=orange, Katong=teal, Thomson=navy. | ☐ |

### Step 7: Frontend Pages

| File | Key Content | Done |
|------|-------------|------|
| `frontend/app/(protected)/dashboard/page.tsx` | **Role-Aware Dashboard**: **Management/Admin**: NParks countdown, Quick Mate Checker widget, 7 alert cards with trends (vaccines, rehome, in-heat, litters, nursing, unsigned agreements, missing parents), vaccine overdue list with "Log Now" buttons, nursing flags, age alerts (5yr+ yellow, 6yr+ red), activity feed, revenue chart, upcoming collections. **Ground Staff**: nursing flag banner, chip scanner hero, unit stats, quick log buttons, recent logs. **Sales Staff**: unsigned agreements, pending AVS transfers (no revenue, no NParks, no mate checker). | ☐ |
| `frontend/app/(protected)/finance/page.tsx` | **Finance Page**: P&L by entity (monthly selector, revenue/COGS/expenses/net table, YTD rollup). GST report (quarter selector, summary table). Transaction list (filters: type, entity, category, date range). Intercompany transfers (create form + history). Excel download buttons for P&L and GST. | ☐ |

---

## Phase 8 Validation Checklist

- [ ] Dashboard: loads <2s on standard Singapore broadband
- [ ] Dashboard: Management sees all 7 alert cards + revenue + NParks countdown
- [ ] Dashboard: Ground staff sees chip scanner + unit stats (no revenue)
- [ ] Dashboard: Sales sees unsigned agreements (no finance)
- [ ] Alert cards: counts match live DB queries
- [ ] Activity feed: updates via SSE without page refresh
- [ ] Revenue chart: correct amounts per entity
- [ ] P&L: revenue - COGS - expenses = net (correct)
- [ ] P&L: intercompany transfers net to zero
- [ ] P&L: YTD rollup correct from April
- [ ] GST: sums match ledger
- [ ] GST: Thomson = 0
- [ ] Finance Excel: downloads contain correct data
- [ ] Role views: unauthorized metrics hidden
- [ ] `pytest backend/apps/finance/tests/` → all pass
