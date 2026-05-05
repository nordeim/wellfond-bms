/**
 * Compliance Hooks
 * ================
 * Phase 6: Compliance & NParks Reporting
 *
 * TanStack Query hooks for NParks, GST, and PDPA operations.
 */

"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"

// Query keys
const NPARKS_KEY = "nparks"
const GST_KEY = "gst"
const PDPA_KEY = "pdpa"

// Types
export interface NParksSubmission {
  id: string
  entity_id: string
  entity_name: string
  document_type: "mating_sheet" | "puppy_movement" | "vet_treatments" | "puppies_bred" | "dog_movement"
  period: string
  status: "DRAFT" | "SUBMITTED" | "LOCKED"
  file_url?: string
  submitted_at?: string
  locked_at?: string
  created_at: string
  updated_at: string
}

export interface NParksGenerateRequest {
  document_type: "mating_sheet" | "puppy_movement" | "vet_treatments" | "puppies_bred" | "dog_movement"
  period: string
  entity_id?: string
}

export interface NParksPreviewData {
  document_type: string
  period: string
  entity_name: string
  row_count: number
  headers: string[]
  sample_data: Record<string, unknown>[][]
  can_submit: boolean
  validation_errors: string[]
}

export interface GSTCalculation {
  price: number
  subtotal: number
  gst_component: number
  entity_gst_rate: number
  entity_name: string
}

export interface GSTSummary {
  period: string
  entity_id: string
  entity_name: string
  total_sales: number
  total_gst: number
  transactions_count: number
}

export interface GSTLedgerEntry {
  id: string
  entity_name: string
  period: string
  source_agreement_id: string
  total_sales: number
  gst_component: number
  created_at: string
}

export interface PDPAConsentLog {
  id: string
  customer_id: string
  action: "OPT_IN" | "OPT_OUT"
  previous_state: boolean
  new_state: boolean
  actor_name: string
  ip_address: string
  user_agent: string
  created_at: string
}

export interface PDPABlastEligibility {
  eligible_ids: string[]
  excluded_ids: string[]
  eligible_count: number
  excluded_count: number
  total_count: number
}

// =============================================================================
// NParks Submission Hooks
// =============================================================================

interface UseNParksSubmissionsOptions {
  status?: string
  document_type?: string
  entity_id?: string
  period?: string
  page?: number
  perPage?: number
}

export function useNParksSubmissions(options: UseNParksSubmissionsOptions = {}) {
  const { status, document_type, entity_id, page = 1, perPage = 25 } = options

  return useQuery({
    queryKey: [NPARKS_KEY, { status, document_type, entity_id, page, perPage }],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("page", String(page))
      params.append("per_page", String(perPage))
      if (status) params.append("status", status)
      if (document_type) params.append("document_type", document_type)
      if (entity_id) params.append("entity_id", entity_id)

      const response = await api.get<{
        items: NParksSubmission[]
        total: number
        page: number
        per_page: number
      }>(`/compliance/nparks?${params.toString()}`)
      return response
    },
    staleTime: 30000,
  })
}

export function useNParksPreview() {
  return useMutation({
    mutationFn: async (data: NParksGenerateRequest) => {
      const response = await api.post<NParksPreviewData>("/compliance/nparks/preview", data)
      return response
    },
  })
}

export function useNParksGenerate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: NParksGenerateRequest) => {
      const response = await api.post<NParksSubmission>("/compliance/nparks/generate", data)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NPARKS_KEY] })
    },
  })
}

export function useNParksSubmit() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (submissionId: string) => {
      const response = await api.post<NParksSubmission>(`/compliance/nparks/${submissionId}/submit`, {})
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NPARKS_KEY] })
    },
  })
}

export function useNParksDownload() {
  return useMutation({
    mutationFn: async ({ submissionId, format }: { submissionId: string; format: "xlsx" | "csv" }) => {
      const response = await api.get<{ download_url: string; file_name: string }>(
        `/compliance/nparks/${submissionId}/download?format=${format}`
      )
      return response
    },
  })
}

export function useNParksValidate() {
  return useMutation({
    mutationFn: async (submissionId: string) => {
      const response = await api.post<{
        is_valid: boolean
        errors: string[]
        warnings: string[]
      }>(`/compliance/nparks/${submissionId}/validate`, {})
      return response
    },
  })
}

// =============================================================================
// GST Hooks
// =============================================================================

export function useGSTCalculation(price: number, entityId?: string) {
  return useQuery({
    queryKey: [GST_KEY, "calculate", price, entityId],
    queryFn: async () => {
      if (!price) return null
      const params = new URLSearchParams()
      params.append("price", String(price))
      if (entityId) params.append("entity_id", entityId)

      const response = await api.get<GSTCalculation>(`/compliance/gst/calculate?${params.toString()}`)
      return response
    },
    enabled: price > 0,
    staleTime: 300000, // 5 minutes - GST rates don't change frequently
  })
}

export function useGSTSummary(period: string, entityId?: string) {
  return useQuery({
    queryKey: [GST_KEY, "summary", period, entityId],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("period", period)
      if (entityId) params.append("entity_id", entityId)

      const response = await api.get<GSTSummary>(`/compliance/gst/summary?${params.toString()}`)
      return response
    },
    enabled: !!period,
    staleTime: 60000,
  })
}

export function useGSTLedger(period?: string, entityId?: string) {
  return useQuery({
    queryKey: [GST_KEY, "ledger", period, entityId],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (period) params.append("period", period)
      if (entityId) params.append("entity_id", entityId)

      const response = await api.get<{
        items: GSTLedgerEntry[]
        total: number
      }>(`/compliance/gst/ledger?${params.toString()}`)
      return response
    },
    staleTime: 30000,
  })
}

export function useGSTExport() {
  return useMutation({
    mutationFn: async ({ period, entityId }: { period: string; entityId?: string }) => {
      const params = new URLSearchParams()
      params.append("period", period)
      if (entityId) params.append("entity_id", entityId)

      const response = await api.get<{ download_url: string; file_name: string }>(
        `/compliance/gst/export?${params.toString()}`
      )
      return response
    },
  })
}

export function useGSTQuarters() {
  return useQuery({
    queryKey: [GST_KEY, "quarters"],
    queryFn: async () => {
      const response = await api.get<string[]>("/compliance/gst/quarters")
      return response
    },
    staleTime: 86400000, // 24 hours - quarters don't change
  })
}

// =============================================================================
// PDPA Hooks
// =============================================================================

export function usePDPAConsent(customerId: string | null) {
  return useQuery({
    queryKey: [PDPA_KEY, "consent", customerId],
    queryFn: async () => {
      if (!customerId) return null
      const response = await api.get<{
        customer_id: string
        is_consented: boolean
        last_updated: string
      }>(`/compliance/pdpa/check?customer_id=${customerId}`)
      return response
    },
    enabled: !!customerId,
    staleTime: 60000,
  })
}

export function useUpdatePDPAConsent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      customerId,
      consent,
    }: {
      customerId: string
      consent: boolean
    }) => {
      const response = await api.post<{
        success: boolean
        new_state: boolean
      }>("/compliance/pdpa/consent", {
        customer_id: customerId,
        consent,
      })
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [PDPA_KEY, "consent", variables.customerId] })
      queryClient.invalidateQueries({ queryKey: [PDPA_KEY, "log", variables.customerId] })
    },
  })
}

export function usePDPALog(customer_id: string | null) {
  return useQuery({
    queryKey: [PDPA_KEY, "log", customer_id],
    queryFn: async () => {
      if (!customer_id) return []
      const response = await api.get<{
        items: PDPAConsentLog[]
        total: number
      }>(`/compliance/pdpa/log?customer_id=${customer_id}`)
      return response
    },
    enabled: !!customer_id,
    staleTime: 30000,
  })
}

export function usePDPABlastEligibility(customerIds: string[]) {
  return useMutation({
    mutationFn: async () => {
      const response = await api.post<PDPABlastEligibility>("/compliance/pdpa/blast-check", {
        customer_ids: customerIds,
      })
      return response
    },
  })
}

export function usePDPAStats(entityId?: string) {
  return useQuery({
    queryKey: [PDPA_KEY, "stats", entityId],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (entityId) params.append("entity_id", entityId)

      const response = await api.get<{
        total_customers: number
        opted_in: number
        opted_out: number
        never_responded: number
        opt_in_rate: number
      }>(`/compliance/pdpa/stats?${params.toString()}`)
      return response
    },
    staleTime: 60000,
  })
}
