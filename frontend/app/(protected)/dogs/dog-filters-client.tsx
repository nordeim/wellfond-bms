/**
 * Dog Filters Client Component
 * ============================
 * Client-side wrapper for filter state management with URL sync.
 */

'use client';

import { useRouter, useSearchParams } from 'next/navigation';

import { DogFilters } from '@/components/dogs/dog-filters';
import type { DogFilterParams } from '@/lib/types';

interface DogFiltersClientProps {
  initialFilters: DogFilterParams;
}

export function DogFiltersClient({ initialFilters }: DogFiltersClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleFilterChange = (filters: DogFilterParams) => {
    const params = new URLSearchParams(searchParams.toString());

    // Update or remove parameters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        params.set(key, String(value));
      } else {
        params.delete(key);
      }
    });

    // Navigate with new params
    router.push(`/dogs?${params.toString()}`);
  };

  return (
    <DogFilters
      filters={initialFilters}
      onChange={handleFilterChange}
    />
  );
}
