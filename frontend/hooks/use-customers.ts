/**
 * Customers Hooks
 * ================
 * Phase 7: Customer DB & Marketing Blast
 *
 * TanStack Query hooks for customer operations and blast management.
 */

"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"

// Query keys
const CUSTOMERS_KEY = "customers"
const CUSTOMER_DETAIL_KEY = "customer"
const SEGMENTS_KEY = "segments"
const BLAST_KEY = "blast"

// Types
export interface Customer {
  id: string
  name: string
  nric?: string
  mobile: string
  email?: string
  address?: string
  housing_type?: "HDB" | "CONDO" | "LANDED" | "OTHER"
  pdpa_consent: boolean
  entity_id: string
  entity_name: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface CustomerDetail extends Customer {
  purchase_history: unknown[]
  comms_log: CommunicationLog[]
}

export interface CommunicationLog {
  id: string
  channel: "EMAIL" | "WA"
  status: "SENT" | "DELIVERED" | "BOUNCED" | "FAILED"
  subject?: string
  message_preview: string
  created_at: string
  sent_at?: string
}

export interface Segment {
  id: string
  name: string
  description?: string
  filters_json: Record<string, unknown>
  customer_count: number
  entity_id?: string
  created_at: string
}

export interface BlastProgress {
  blast_id: string
  total: number
  sent: number
  delivered: number
  failed: number
  in_progress: boolean
  percentage: number
}

export interface BlastCreate {
  segment_id?: string
  customer_ids?: string[]
  channel: "EMAIL" | "WA" | "BOTH"
  subject?: string
  body: string
  merge_tags?: Record<string, string>
}

export interface BlastPreview {
  total_customers: number
  eligible_customers: number
  excluded_customers: number
  excluded_reason: string
  channel: string
  sample_message?: string
}

// =============================================================================
// Customer List Hook
// =============================================================================

interface UseCustomerListOptions {
  search?: string
  entity_id?: string
  pdpa_consent?: boolean
  housing_type?: string
  page?: number
  perPage?: number
}

export function useCustomerList(options: UseCustomerListOptions = {}) {
  const { search, entity_id, pdpa_consent, housing_type, page = 1, perPage = 25 } = options

  return useQuery({
    queryKey: [CUSTOMERS_KEY, { search, entity_id, pdpa_consent, housing_type, page, perPage }],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("page", String(page))
      params.append("per_page", String(perPage))
      if (search) params.append("search", search)
      if (entity_id) params.append("entity_id", entity_id)
      if (pdpa_consent !== undefined) params.append("pdpa_consent", String(pdpa_consent))
      if (housing_type) params.append("housing_type", housing_type)

      const response = await api.get<{
        items: Customer[]
        total: number
        page: number
        per_page: number
      }>(`/customers/?${params.toString()}`)
      return response
    },
    staleTime: 30000,
  })
}

// =============================================================================
// Customer Detail Hook
// =============================================================================

export function useCustomer(customer_id: string | null) {
  return useQuery({
    queryKey: [CUSTOMER_DETAIL_KEY, customer_id],
    queryFn: async () => {
      if (!customer_id) return null
      const response = await api.get<CustomerDetail>(`/customers/${customer_id}`)
      return response
    },
    enabled: !!customer_id,
    staleTime: 60000,
  })
}

// =============================================================================
// Create Customer Mutation
// =============================================================================

export function useCreateCustomer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      name: string
      mobile: string
      email?: string
      nric?: string
      address?: string
      housing_type?: string
      entity_id: string
      pdpa_consent?: boolean
      notes?: string
    }) => {
      const response = await api.post<{ id: string; message: string }>("/customers/", data)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_KEY] })
    },
  })
}

// =============================================================================
// Update Customer Mutation
// =============================================================================

export function useUpdateCustomer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      customer_id,
      data,
    }: {
      customer_id: string
      data: Partial<Customer>
    }) => {
      const response = await api.patch<{ id: string; message: string }>(
        `/customers/${customer_id}`,
        data
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_KEY] })
      queryClient.invalidateQueries({ queryKey: [CUSTOMER_DETAIL_KEY, variables.customer_id] })
    },
  })
}

// =============================================================================
// Update PDPA Consent Mutation
// =============================================================================

export function useUpdatePDPAConsent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ customer_id, consent }: { customer_id: string; consent: boolean }) => {
      const response = await api.patch<{ customer_id: string; is_consented: boolean }>(
        `/customers/${customer_id}/consent`,
        { consent }
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_KEY] })
      queryClient.invalidateQueries({ queryKey: [CUSTOMER_DETAIL_KEY, variables.customer_id] })
    },
  })
}

// =============================================================================
// Segments Hooks
// =============================================================================

export function useSegments() {
  return useQuery({
    queryKey: [SEGMENTS_KEY],
    queryFn: async () => {
      const response = await api.get<Segment[]>("/customers/segments/")
      return response
    },
    staleTime: 300000, // 5 minutes - segments don't change often
  })
}

export function useCreateSegment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      name: string
      description?: string
      filters: Record<string, unknown>
      entity_id?: string
    }) => {
      const response = await api.post<{ id: string; count: number; message: string }>(
        "/customers/segments/",
        data
      )
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SEGMENTS_KEY] })
    },
  })
}

export function usePreviewSegment(segmentId: string | null) {
  return useQuery({
    queryKey: [SEGMENTS_KEY, "preview", segmentId],
    queryFn: async () => {
      if (!segmentId) return null
      const response = await api.get<{ count: number; filters_applied: Record<string, unknown> }>(
        `/customers/segments/${segmentId}/preview`
      )
      return response
    },
    enabled: !!segmentId,
  })
}

// =============================================================================
// Blast Hooks
// =============================================================================

export function usePreviewBlast() {
  return useMutation({
    mutationFn: async (data: BlastCreate) => {
      const response = await api.post<BlastPreview>("/customers/blast/preview", data)
      return response
    },
  })
}

export function useSendBlast() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: BlastCreate) => {
      const response = await api.post<{
        blast_id: string
        total_recipients: number
        eligible_recipients: number
        excluded_count: number
        channel: string
        status: string
      }>("/customers/blast", data)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_KEY] })
    },
  })
}

export function useBlastProgress(blastId: string | null) {
  return useQuery<BlastProgress | null>({
    queryKey: [BLAST_KEY, "progress", blastId],
    queryFn: async () => {
      if (!blastId) return null
      const response = await api.get<BlastProgress>(`/customers/blast/${blastId}/progress`)
      return response
    },
    enabled: !!blastId,
    refetchInterval: (query) => {
      // Stop polling when blast is complete
      const data = query.state.data
      return data?.in_progress ? 1000 : false
    },
  })
}

// =============================================================================
// CSV Import Hooks
// =============================================================================

export function usePreviewCSVImport() {
  return useMutation({
    mutationFn: async (data: {
      file_content: string
      column_mapping: Record<string, string>
      entity_id: string
      skip_duplicates?: boolean
    }) => {
      const response = await api.post<{
        total_rows: number
        valid_rows: number
        duplicate_rows: number
        invalid_rows: number
        sample_data: unknown[]
        column_mapping: Record<string, string>
      }>("/customers/import/preview", data)
      return response
    },
  })
}

export function useImportCSV() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: {
      file_content: string
      column_mapping: Record<string, string>
      entity_id: string
      skip_duplicates?: boolean
    }) => {
      const response = await api.post<{
        imported_count: number
        duplicate_count: number
        error_count: number
        errors: unknown[]
      }>("/customers/import", data)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [CUSTOMERS_KEY] })
    },
  })
}
