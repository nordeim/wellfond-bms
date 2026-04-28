/**
 * Sales Agreement Hooks
 * ========================
 * Phase 5: Sales Agreements & AVS Tracking
 *
 * TanStack Query hooks for sales agreement operations.
 */

"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"

// Query keys
const SALES_KEY = "sales"
const SALE_DETAIL_KEY = "sale"
const AVS_KEY = "avs"

// Types
export interface Agreement {
  id: string
  agreement_number: string
  type: "B2C" | "B2B" | "REHOME"
  status: "DRAFT" | "SIGNED" | "COMPLETED" | "CANCELLED"
  buyer_name: string
  buyer_mobile: string
  buyer_email: string
  total_amount: number
  deposit: number
  created_at: string
  dog_count: number
}

export interface AgreementDetail extends Agreement {
  buyer_address: string
  buyer_housing_type: string
  buyer_nric?: string
  gst_component: number
  balance: number
  payment_method: string
  special_conditions: string
  pdf_url?: string
  signed_at?: string
  completed_at?: string
  cancelled_at?: string
  line_items: LineItem[]
}

export interface LineItem {
  id: string
  dog_id: string
  dog_name: string
  description: string
  quantity: number
  unit_price: number
  line_total: number
  gst_amount: number
}

export interface AgreementCreate {
  type: "B2C" | "B2B" | "REHOME"
  dog_ids: string[]
  buyer: {
    name: string
    mobile: string
    email: string
    address: string
    housing_type: string
    nric?: string
  }
  pricing: {
    total: number
    deposit: number
    payment_method: string
  }
  special_conditions?: string
  pdpa_consent: boolean
}

export interface AgreementUpdate {
  status?: "SIGNED" | "COMPLETED" | "CANCELLED"
  special_conditions?: string
}

export interface SignatureRequest {
  signature_data: string
  ip_address: string
  user_agent: string
}

export interface AVSTransfer {
  id: string
  agreement_id: string
  dog_id: string
  dog_name: string
  buyer_mobile: string
  status: "PENDING" | "SENT" | "COMPLETED" | "ESCALATED"
  token: string
  reminder_sent_at?: string
  completed_at?: string
  created_at: string
}

// =============================================================================
// Agreement List Hook
// =============================================================================

interface UseAgreementListOptions {
  status?: string
  type?: string
  page?: number
  perPage?: number
}

export function useAgreementList(options: UseAgreementListOptions = {}) {
  const { status, type, page = 1, perPage = 25 } = options

  return useQuery({
    queryKey: [SALES_KEY, { status, type, page, perPage }],
    queryFn: async () => {
      const params = new URLSearchParams()
      params.append("page", String(page))
      params.append("per_page", String(perPage))
      if (status) params.append("status", status)
      if (type) params.append("type", type)

      const response = await api.get<{
        items: Agreement[]
        total: number
        page: number
        per_page: number
      }>(`/sales/agreements/?${params.toString()}`)
      return response
    },
    staleTime: 30000,
  })
}

// =============================================================================
// Agreement Detail Hook
// =============================================================================

export function useAgreementDetail(agreementId: string | null) {
  return useQuery({
    queryKey: [SALE_DETAIL_KEY, agreementId],
    queryFn: async () => {
      if (!agreementId) return null
      const response = await api.get<AgreementDetail>(
        `/sales/agreements/${agreementId}`
      )
      return response
    },
    enabled: !!agreementId,
    staleTime: 60000,
  })
}

// =============================================================================
// Create Agreement Mutation
// =============================================================================

export function useCreateAgreement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: AgreementCreate) => {
      const response = await api.post<Agreement>("/sales/agreements/", data)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [SALES_KEY] })
    },
  })
}

// =============================================================================
// Update Agreement Mutation
// =============================================================================

export function useUpdateAgreement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      agreementId,
      data,
    }: {
      agreementId: string
      data: AgreementUpdate
    }) => {
      const response = await api.patch<Agreement>(
        `/sales/agreements/${agreementId}`,
        data
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [SALES_KEY] })
      queryClient.invalidateQueries({
        queryKey: [SALE_DETAIL_KEY, variables.agreementId],
      })
    },
  })
}

// =============================================================================
// Sign Agreement Mutation
// =============================================================================

export function useSignAgreement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      agreementId,
      data,
    }: {
      agreementId: string
      data: SignatureRequest
    }) => {
      const response = await api.post<Agreement>(
        `/sales/agreements/${agreementId}/sign`,
        data
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [SALES_KEY] })
      queryClient.invalidateQueries({
        queryKey: [SALE_DETAIL_KEY, variables.agreementId],
      })
    },
  })
}

// =============================================================================
// Send Agreement Mutation
// =============================================================================

export function useSendAgreement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      agreementId,
      channel = "both",
    }: {
      agreementId: string
      channel?: "email" | "whatsapp" | "both"
    }) => {
      const response = await api.post<{ success: boolean }>(
        `/sales/agreements/${agreementId}/send`,
        { channel }
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [SALES_KEY] })
      queryClient.invalidateQueries({
        queryKey: [SALE_DETAIL_KEY, variables.agreementId],
      })
    },
  })
}

// =============================================================================
// Cancel Agreement Mutation
// =============================================================================

export function useCancelAgreement() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      agreementId,
      reason,
    }: {
      agreementId: string
      reason: string
    }) => {
      const response = await api.delete<{ success: boolean }>(
        `/sales/agreements/${agreementId}?reason=${encodeURIComponent(reason)}`
      )
      return response
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [SALES_KEY] })
      queryClient.invalidateQueries({
        queryKey: [SALE_DETAIL_KEY, variables.agreementId],
      })
    },
  })
}

// =============================================================================
// AVS Transfer Hooks
// =============================================================================

export function useAVSTransfers(options: { status?: string; entityId?: string } = {}) {
  const { status, entityId } = options

  return useQuery({
    queryKey: [AVS_KEY, { status, entityId }],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (status) params.append("status", status)
      if (entityId) params.append("entity_id", entityId)

      const response = await api.get<AVSTransfer[]>(
        `/avs/pending?${params.toString()}`
      )
      return response
    },
    staleTime: 30000,
    refetchInterval: 60000, // Refetch every minute for pending transfers
  })
}

export function useCompleteAVSTransfer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (transferId: string) => {
      const response = await api.post<AVSTransfer>(
        `/avs/${transferId}/complete`,
        {}
      )
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AVS_KEY] })
      queryClient.invalidateQueries({ queryKey: [SALES_KEY] })
    },
  })
}

export function useSendAVSReminder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (transferId: string) => {
      const response = await api.post<{ success: boolean }>(
        `/avs/${transferId}/reminder`,
        {}
      )
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AVS_KEY] })
    },
  })
}

export function useEscalateAVSTransfer() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (transferId: string) => {
      const response = await api.post<{ success: boolean }>(
        `/avs/${transferId}/escalate`,
        {}
      )
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [AVS_KEY] })
    },
  })
}

// =============================================================================
// PDF Hooks
// =============================================================================

export function useAgreementPDF(agreementId: string | null) {
  return useQuery({
    queryKey: [SALE_DETAIL_KEY, agreementId, "pdf"],
    queryFn: async () => {
      if (!agreementId) return null
      const response = await api.get<{ pdf_url: string; pdf_hash: string }>(
        `/sales/agreements/${agreementId}/pdf`
      )
      return response
    },
    enabled: !!agreementId,
    staleTime: 300000, // 5 minutes
  })
}
