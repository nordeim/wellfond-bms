/**
 * Finance Hooks
 * =============
 * Phase 8: Finance Module
 *
 * TanStack Query hooks for P&L, GST reports, and transactions.
 */

"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"

// Query keys
const FINANCE_KEY = "finance"
const PNL_KEY = "pnl"
const GST_KEY = "gst"
const TRANSACTIONS_KEY = "transactions"
const INTERCOMPANY_KEY = "intercompany"

// Types
export interface PNLData {
  entity_id: string
  month: string
  revenue: string
  cogs: string
  expenses: string
  net: string
  ytd_revenue: string
  ytd_net: string
  by_category: Record<string, string>
}

export interface GSTData {
  entity_id: string
  entity_name: string
  quarter: string
  total_sales: string
  total_gst: string
  transactions: Transaction[]
  generated_at: string
  generated_by_id: string
}

export interface Transaction {
  id: string
  type: "REVENUE" | "EXPENSE" | "TRANSFER"
  amount: string
  entity_id: string
  gst_component: string
  date: string
  category: "SALE" | "VET" | "MARKETING" | "OPERATIONS" | "OTHER"
  description: string | null
  source_agreement_id: string | null
  created_at: string
}

export interface IntercompanyTransfer {
  id: string
  from_entity_id: string
  from_entity_name: string
  to_entity_id: string
  to_entity_name: string
  amount: string
  date: string
  description: string
  created_by_id: string
  created_by_name: string
  created_at: string
}

export interface TransactionFilters {
  entity_id?: string
  type?: string
  category?: string
  date_from?: string
  date_to?: string
}

export interface TransactionListResponse {
  items: Transaction[]
  total: number
  page: number
  per_page: number
}

export interface IntercompanyListResponse {
  items: IntercompanyTransfer[]
  total: number
  page: number
  per_page: number
}

// ============================================================================
// P&L Queries
// ============================================================================

export function usePNL(entityId: string, month: string) {
  return useQuery<PNLData>({
    queryKey: [FINANCE_KEY, PNL_KEY, entityId, month],
    queryFn: async () => {
      const data = await api.get<PNLData>(`/finance/pnl?entity_id=${entityId}&month=${month}`)
      return data
    },
    enabled: !!entityId && !!month,
  })
}

// ============================================================================
// GST Queries
// ============================================================================

export function useGSTReport(entityId: string, quarter: string) {
  return useQuery<GSTData>({
    queryKey: [FINANCE_KEY, GST_KEY, entityId, quarter],
    queryFn: async () => {
      const data = await api.get<GSTData>(`/finance/gst?entity_id=${entityId}&quarter=${quarter}`)
      return data
    },
    enabled: !!entityId && !!quarter,
  })
}

// ============================================================================
// Transaction Queries
// ============================================================================

export function useTransactions(
  filters: TransactionFilters = {},
  page: number = 1,
  perPage: number = 25
) {
  const params = new URLSearchParams()
  if (filters.entity_id) params.set("entity_id", filters.entity_id)
  if (filters.type) params.set("type", filters.type)
  if (filters.category) params.set("category", filters.category)
  if (filters.date_from) params.set("date_from", filters.date_from)
  if (filters.date_to) params.set("date_to", filters.date_to)
  params.set("page", String(page))
  params.set("per_page", String(perPage))

  return useQuery<TransactionListResponse>({
    queryKey: [FINANCE_KEY, TRANSACTIONS_KEY, filters, page, perPage],
    queryFn: async () => {
      const data = await api.get<TransactionListResponse>(`/finance/transactions?${params.toString()}`)
      return data
    },
  })
}

// ============================================================================
// Intercompany Queries
// ============================================================================

export function useIntercompanyTransfers(
  entityId: string | null = null,
  page: number = 1,
  perPage: number = 25
) {
  const params = new URLSearchParams()
  if (entityId) params.set("entity_id", entityId)
  params.set("page", String(page))
  params.set("per_page", String(perPage))

  return useQuery<IntercompanyListResponse>({
    queryKey: [FINANCE_KEY, INTERCOMPANY_KEY, entityId, page],
    queryFn: async () => {
      const data = await api.get<IntercompanyListResponse>(`/finance/intercompany?${params.toString()}`)
      return data
    },
  })
}

export interface IntercompanyCreatePayload {
  from_entity_id: string
  to_entity_id: string
  amount: string
  date: string
  description: string
}

export interface IntercompanyCreateResponse {
  id: string
  from_entity_id: string
  from_entity_name: string
  to_entity_id: string
  to_entity_name: string
  amount: string
  date: string
  description: string
  created_by_id: string
  created_by_name: string
  created_at: string
}

export function useCreateIntercompanyTransfer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: IntercompanyCreatePayload) => {
      const data = await api.post<IntercompanyCreateResponse>("/finance/intercompany", payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [FINANCE_KEY, INTERCOMPANY_KEY] })
      queryClient.invalidateQueries({ queryKey: [FINANCE_KEY, TRANSACTIONS_KEY] })
    },
  })
}

// ============================================================================
// Export Functions
// ============================================================================

export async function exportPNLExcel(entityId: string, month: string): Promise<void> {
  const response = await fetch(`/api/finance/export/pnl?entity_id=${entityId}&month=${month}`, {
    credentials: 'include',
  })
  
  if (!response.ok) {
    throw new Error('Export failed')
  }
  
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.setAttribute("download", `pnl_${month}.xlsx`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function exportGSTExcel(entityId: string, quarter: string): Promise<void> {
  const response = await fetch(`/api/finance/export/gst?entity_id=${entityId}&quarter=${quarter}`, {
    credentials: 'include',
  })
  
  if (!response.ok) {
    throw new Error('Export failed')
  }
  
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.setAttribute("download", `gst_${quarter}.xlsx`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

// ============================================================================
// Utility Functions
// ============================================================================

export function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: "SGD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-SG", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function getCurrentQuarter(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const quarter = Math.ceil(month / 3)
  return `${year}-Q${quarter}`
}

export function getCurrentMonth(): string {
  const now = new Date()
  return now.toISOString().slice(0, 7) // YYYY-MM
}
