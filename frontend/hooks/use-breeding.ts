"use client";

/**
 * Breeding & Genetics Hooks
 * ========================
 * Phase 4: Breeding & Genetics Engine
 *
 * TanStack Query hooks for:
 * - Mate checker (COI + saturation)
 * - Litters CRUD
 * - Puppies CRUD
 * - Breeding records
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";

// =============================================================================
// Types
// =============================================================================

interface ApiError {
  message?: string;
}

interface AncestorInfo {
  dog_id: string;
  name: string;
  microchip: string;
  relationship: string;
  generations_back: number;
}

export interface MateCheckResult {
  dam_id: string;
  dam_name: string;
  sire1_id: string;
  sire1_name: string;
  sire2_id?: string;
  sire2_name?: string;
  coi_pct: number;
  saturation_pct: number;
  verdict: "SAFE" | "CAUTION" | "HIGH_RISK";
  shared_ancestors: AncestorInfo[];
}

export interface MateCheckOverride {
  id: string;
  dam_id: string;
  dam_name: string;
  sire1_id: string;
  sire1_name: string;
  sire2_id?: string;
  sire2_name?: string;
  coi_pct: number;
  saturation_pct: number;
  verdict: string;
  override_reason: string;
  override_notes?: string;
  staff_name: string;
  staff_role: string;
  created_at: string;
}

export interface LitterListItem {
  id: string;
  breeding_record_id: string;
  dam_name: string;
  sire_name: string;
  whelp_date: string;
  alive_count: number;
  stillborn_count: number;
  total_count: number;
  delivery_method: string;
  puppy_count: number;
}

export interface LitterDetail extends LitterListItem {
  dam_id: string;
  dam_microchip: string;
  sire1_id: string;
  sire1_microchip: string;
  sire2_id?: string;
  sire2_name?: string;
  sire2_microchip?: string;
  notes?: string;
  puppies: PuppyListItem[];
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface PuppyListItem {
  id: string;
  litter_id: string;
  microchip?: string;
  gender: "M" | "F";
  colour: string;
  birth_weight?: number;
  confirmed_sire: string;
  paternity_method: string;
  status: "ALIVE" | "REHOMED" | "DECEASED";
  buyer_name?: string;
  sale_date?: string;
}

export interface BreedingRecordListItem {
  id: string;
  dam_name: string;
  dam_microchip: string;
  sire1_name: string;
  sire1_microchip: string;
  sire2_name?: string;
  sire2_microchip?: string;
  date: string;
  expected_whelp_date?: string;
  method: string;
  confirmed_sire: string;
  has_litter: boolean;
}

export interface BreedingRecordFilters {
  dam_chip?: string;
  sire_chip?: string;
  date_from?: string;
  date_to?: string;
  has_litter?: boolean;
}

export interface LitterFilters {
  dam_chip?: string;
  sire_chip?: string;
  whelp_date_from?: string;
  whelp_date_to?: string;
}

// =============================================================================
// Mate Checker Hooks
// =============================================================================

export function useMateCheck() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      dam_chip: string;
      sire1_chip: string;
      sire2_chip?: string;
    }) => {
      const response = await api.post<MateCheckResult>(
        "/api/v1/breeding/mate-check/",
        data
      );
      return response;
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to perform mate check");
    },
  });
}

export function useMateCheckOverride() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      dam_id: string;
      sire1_id: string;
      sire2_id?: string;
      coi_pct: number;
      saturation_pct: number;
      verdict: string;
      reason: string;
      notes?: string;
    }) => {
      const response = await api.post("/api/v1/breeding/mate-check/override/", data);
      return response;
    },
    onSuccess: () => {
      toast.success("Override recorded successfully");
      queryClient.invalidateQueries({ queryKey: ["mate-check-history"] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to create override");
    },
  });
}

export function useMateCheckHistory(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["mate-check-history", params],
    queryFn: async () => {
      const response = await api.get<{
        overrides: MateCheckOverride[];
        total: number;
        page: number;
        per_page: number;
      }>("/api/v1/breeding/mate-check/history/", { params });
      return response;
    },
  });
}

// =============================================================================
// Litter Hooks
// =============================================================================

export function useLitters(filters?: LitterFilters) {
  return useQuery({
    queryKey: ["litters", filters],
    queryFn: async () => {
      const response = await api.get<{
        litters: LitterListItem[];
        total: number;
        page: number;
        per_page: number;
      }>("/api/v1/breeding/litters/", { params: filters });
      return response;
    },
  });
}

export function useLitter(id: string) {
  return useQuery({
    queryKey: ["litter", id],
    queryFn: async () => {
      const response = await api.get<LitterDetail>(`/api/v1/breeding/litters/${id}/`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateLitter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      breeding_record_id: string;
      whelp_date: string;
      delivery_method: "NATURAL" | "C_SECTION";
      alive_count: number;
      stillborn_count: number;
      notes?: string;
    }) => {
      const response = await api.post("/api/v1/breeding/litters/", data);
      return response;
    },
    onSuccess: () => {
      toast.success("Litter created successfully");
      queryClient.invalidateQueries({ queryKey: ["litters"] });
      queryClient.invalidateQueries({ queryKey: ["breeding-records"] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to create litter");
    },
  });
}

export function useUpdateLitter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<{
        whelp_date: string;
        delivery_method: "NATURAL" | "C_SECTION";
        alive_count: number;
        stillborn_count: number;
        notes: string;
      }>;
    }) => {
      const response = await api.patch(`/api/v1/breeding/litters/${id}/`, data);
      return response;
    },
    onSuccess: (_, { id }) => {
      toast.success("Litter updated successfully");
      queryClient.invalidateQueries({ queryKey: ["litters"] });
      queryClient.invalidateQueries({ queryKey: ["litter", id] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to update litter");
    },
  });
}

// =============================================================================
// Puppy Hooks
// =============================================================================

export function useAddPuppy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      litter_id,
      data,
    }: {
      litter_id: string;
      data: {
        microchip?: string;
        gender: "M" | "F";
        colour: string;
        birth_weight?: number;
        confirmed_sire?: string;
        paternity_method?: string;
      };
    }) => {
      const response = await api.post(
        `/api/v1/breeding/litters/${litter_id}/puppies/`,
        data
      );
      return response;
    },
    onSuccess: (_, { litter_id }) => {
      toast.success("Puppy added successfully");
      queryClient.invalidateQueries({ queryKey: ["litter", litter_id] });
      queryClient.invalidateQueries({ queryKey: ["litters"] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to add puppy");
    },
  });
}

export function useUpdatePuppy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      litter_id,
      puppy_id,
      data,
    }: {
      litter_id: string;
      puppy_id: string;
      data: Partial<{
        microchip: string;
        colour: string;
        birth_weight: number;
        confirmed_sire: string;
        paternity_method: string;
        status: "ALIVE" | "REHOMED" | "DECEASED";
        buyer_name: string;
        buyer_contact: string;
        sale_date: string;
      }>;
    }) => {
      const response = await api.patch(
        `/api/v1/breeding/litters/${litter_id}/puppies/${puppy_id}/`,
        data
      );
      return response;
    },
    onSuccess: (_, { litter_id }) => {
      toast.success("Puppy updated successfully");
      queryClient.invalidateQueries({ queryKey: ["litter", litter_id] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to update puppy");
    },
  });
}

// =============================================================================
// Breeding Record Hooks
// =============================================================================

export function useBreedingRecords(filters?: BreedingRecordFilters) {
  return useQuery({
    queryKey: ["breeding-records", filters],
    queryFn: async () => {
      const response = await api.get<{
        records: BreedingRecordListItem[];
        total: number;
        page: number;
        per_page: number;
      }>("/api/v1/breeding/records/", { params: filters });
      return response;
    },
  });
}

export function useCreateBreedingRecord() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      dam_chip: string;
      sire1_chip: string;
      sire2_chip?: string;
      date: string;
      method: "NATURAL" | "ASSISTED";
      notes?: string;
    }) => {
      const response = await api.post("/api/v1/breeding/records/", data);
      return response;
    },
    onSuccess: () => {
      toast.success("Breeding record created successfully");
      queryClient.invalidateQueries({ queryKey: ["breeding-records"] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to create breeding record");
    },
  });
}

export function useUpdateBreedingRecord() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<{
        method: "NATURAL" | "ASSISTED";
        confirmed_sire: "SIRE1" | "SIRE2" | "UNCONFIRMED";
        notes: string;
      }>;
    }) => {
      const response = await api.patch(`/api/v1/breeding/records/${id}/`, data);
      return response;
    },
    onSuccess: () => {
      toast.success("Breeding record updated successfully");
      queryClient.invalidateQueries({ queryKey: ["breeding-records"] });
    },
    onError: (error: ApiError) => {
      toast.error(error.message || "Failed to update breeding record");
    },
  });
}
