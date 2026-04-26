/**
 * Dog Filters Component
 * =====================
 * Filter bar for dog master list.
 */

'use client';

import { X } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DOG_STATUSES, ENTITY_LABELS } from '@/lib/constants';
import type { DogFilterParams } from '@/lib/types';

interface DogFiltersProps {
  filters: DogFilterParams;
  onChange: (filters: DogFilterParams) => void;
  className?: string;
}

const GENDERS = [
  { value: '', label: 'All Genders' },
  { value: 'M', label: 'Male' },
  { value: 'F', label: 'Female' },
];

const STATUSES = [
  { value: '', label: 'All Statuses' },
  ...Object.entries(DOG_STATUSES).map(([value]) => ({
    value,
    label: value.charAt(0) + value.slice(1).toLowerCase(),
  })),
];

const ENTITIES = [
  { value: '', label: 'All Entities' },
  ...Object.entries(ENTITY_LABELS).map(([value, label]) => ({ value, label })),
];

export function DogFilters({ filters, onChange, className }: DogFiltersProps) {
  const hasActiveFilters = Object.values(filters).some(Boolean);

  const updateFilter = (key: keyof DogFilterParams, value: string) => {
    onChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const clearFilters = () => {
    onChange({});
  };

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {/* Status Chips */}
      <div className="flex flex-wrap gap-2">
        {STATUSES.slice(1).map((status) => (
          <button
            key={status.value}
            onClick={() =>
              updateFilter('status', filters.status === status.value ? '' : status.value)
            }
            className={cn(
              'rounded-full px-3 py-1 text-sm font-medium transition-colors',
              filters.status === status.value
                ? 'bg-[#F97316] text-white'
                : 'bg-white text-[#0D2030] hover:bg-[#E8F4FF] border border-[#C0D8EE]'
            )}
          >
            {status.label}
          </button>
        ))}
      </div>

      <div className="h-6 w-px bg-[#C0D8EE]" />

      {/* Gender Toggle */}
      <div className="flex rounded-lg border border-[#C0D8EE] bg-white overflow-hidden">
        {GENDERS.map((gender) => (
          <button
            key={gender.value}
            onClick={() => updateFilter('gender', gender.value)}
            className={cn(
              'px-3 py-1.5 text-sm font-medium transition-colors',
              filters.gender === gender.value ||
                (!filters.gender && !gender.value)
                ? 'bg-[#F97316] text-white'
                : 'text-[#0D2030] hover:bg-[#E8F4FF]'
            )}
          >
            {gender.label}
          </button>
        ))}
      </div>

      {/* Entity Dropdown */}
      <Select
        value={filters.entity || ''}
        onValueChange={(value) => updateFilter('entity', value)}
      >
        <SelectTrigger className="w-[160px] bg-white">
          <SelectValue placeholder="All Entities" />
        </SelectTrigger>
        <SelectContent>
          {ENTITIES.map((entity) => (
            <SelectItem key={entity.value} value={entity.value}>
              {entity.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Clear Button */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="text-muted-foreground hover:text-[#0D2030]"
        >
          <X className="mr-1 h-4 w-4" />
          Clear
        </Button>
      )}
    </div>
  );
}
