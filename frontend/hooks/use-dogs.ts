'use client';

/**
 * Dog data hooks for Wellfond BMS
 * ================================
 * TanStack Query hooks for dog CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { api } from '@/lib/api';
import type {
  Dog,
  DogCreate,
  DogDetailResponse,
  DogFilterParams,
  DogListResponse,
  DogUpdate,
  HealthRecordCreate,
  VaccinationCreate,
  AlertCard,
} from '@/lib/types';

// Query keys
const DOGS_KEY = 'dogs';
const DOG_DETAIL_KEY = 'dog';
const ALERTS_KEY = 'alerts';
const DOG_SEARCH_KEY = 'dog-search';

// =============================================================================
// Dog List Hook
// =============================================================================

interface UseDogListOptions extends DogFilterParams {
  page?: number;
  perPage?: number;
}

export function useDogList(options: UseDogListOptions = {}) {
  const { page = 1, perPage = 25, ...filters } = options;
  
  return useQuery({
    queryKey: [DOGS_KEY, { page, perPage, ...filters }],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('per_page', String(perPage));
      
      if (filters.status) params.append('status', filters.status);
      if (filters.entity) params.append('entity', filters.entity);
      if (filters.breed) params.append('breed', filters.breed);
      if (filters.gender) params.append('gender', filters.gender);
      if (filters.search) params.append('search', filters.search);
      if (filters.unit) params.append('unit', filters.unit);
      
      const response = await api.get<DogListResponse>(`/dogs/?${params.toString()}`);
      return response;
    },
    staleTime: 30000, // 30 seconds
  });
}

// =============================================================================
// Dog Detail Hook
// =============================================================================

export function useDog(id: string | null) {
  return useQuery<Dog | null>({
    queryKey: [DOG_DETAIL_KEY, id],
    queryFn: async () => {
      if (!id) return null;
      const response = await api.get<DogDetailResponse>(`/dogs/${id}`);
      return response.dog;
    },
    enabled: !!id,
    staleTime: 60000, // 1 minute
  });
}

// =============================================================================
// Dog Search Hook (Debounced)
// =============================================================================

export function useDogSearch() {
  const [query, setQuery] = useState('');
  
  const { data, isLoading } = useQuery({
    queryKey: [DOG_SEARCH_KEY, query],
    queryFn: async () => {
      if (!query || query.length < 2) return [];
      const response = await api.get<Dog[]>(`/dogs/search/${encodeURIComponent(query)}?limit=10`);
      return response;
    },
    enabled: query.length >= 2,
    staleTime: 10000,
  });
  
  return {
    query,
    setQuery,
    results: data || [],
    isLoading,
  };
}

// =============================================================================
// Alert Cards Hook
// =============================================================================

interface UseAlertCardsOptions {
  entityId?: string;
}

export function useAlertCards(options: UseAlertCardsOptions = {}) {
  const { entityId } = options;
  
  return useQuery({
    queryKey: [ALERTS_KEY, entityId],
    queryFn: async () => {
      const params = entityId ? `?entity=${entityId}` : '';
      const response = await api.get<{ alerts: AlertCard[] }>(`/alerts/${params}`);
      return response.alerts;
    },
    staleTime: 60000, // 1 minute
  });
}

// =============================================================================
// Create Dog Mutation
// =============================================================================

export function useCreateDog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: DogCreate) => {
      const response = await api.post<Dog>('/dogs/', data);
      return response;
    },
    onSuccess: () => {
      // Invalidate dog list cache
      queryClient.invalidateQueries({ queryKey: [DOGS_KEY] });
    },
  });
}

// =============================================================================
// Update Dog Mutation
// =============================================================================

export function useUpdateDog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: DogUpdate }) => {
      const response = await api.patch<Dog>(`/dogs/${id}`, data);
      return response;
    },
    onSuccess: (data) => {
      // Invalidate specific dog cache
      queryClient.invalidateQueries({ queryKey: [DOG_DETAIL_KEY, data.id] });
      // Invalidate list cache
      queryClient.invalidateQueries({ queryKey: [DOGS_KEY] });
    },
  });
}

// =============================================================================
// Delete Dog Mutation
// =============================================================================

export function useDeleteDog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/dogs/${id}`);
      return id;
    },
    onSuccess: (id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: [DOG_DETAIL_KEY, id] });
      // Invalidate list cache
      queryClient.invalidateQueries({ queryKey: [DOGS_KEY] });
    },
  });
}

// =============================================================================
// Health Record Mutations
// =============================================================================

export function useCreateHealthRecord() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ dogId, data }: { dogId: string; data: HealthRecordCreate }) => {
      const response = await api.post(`/dogs/${dogId}/health`, data);
      return response;
    },
    onSuccess: (_, { dogId }) => {
      // Invalidate dog detail to refresh health records
      queryClient.invalidateQueries({ queryKey: [DOG_DETAIL_KEY, dogId] });
    },
  });
}

// =============================================================================
// Vaccination Mutations
// =============================================================================

export function useCreateVaccination() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ dogId, data }: { dogId: string; data: VaccinationCreate }) => {
      const response = await api.post(`/dogs/${dogId}/vaccinations`, data);
      return response;
    },
    onSuccess: (_, { dogId }) => {
      // Invalidate dog detail to refresh vaccinations
      queryClient.invalidateQueries({ queryKey: [DOG_DETAIL_KEY, dogId] });
      // Invalidate alerts (vaccine overdue counts)
      queryClient.invalidateQueries({ queryKey: [ALERTS_KEY] });
    },
  });
}
