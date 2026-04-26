/**
 * Dog Table Component
 * ===================
 * Master list table with sorting and actions.
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  MoreHorizontal,
  MessageSquare,
  Pencil,
  Trash2,
} from 'lucide-react';

import { useDogList, useDeleteDog } from '@/hooks/use-dogs';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import type { Dog, DogFilterParams } from '@/lib/types';
import { DOG_STATUS_LABELS, DNA_STATUS_LABELS } from '@/lib/constants';

interface DogTableProps {
  filters: DogFilterParams;
}

type SortField = 'microchip' | 'name' | 'breed' | 'dob' | 'unit' | 'status';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-[#4EAD72]',
  RETIRED: 'bg-[#4A7A94]',
  REHOMED: 'bg-[#0891B2]',
  DECEASED: 'bg-[#D94040]',
};

const DNA_STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-[#D4920A]',
  SUBMITTED: 'bg-[#0891B2]',
  RESULTS_RECEIVED: 'bg-[#4EAD72]',
  EXCLUDED: 'bg-[#D94040]',
};

function getAgeDot(ageYears: number): { color: string; label: string } {
  if (ageYears >= 6) return { color: 'bg-[#D94040]', label: '6+' };
  if (ageYears >= 5) return { color: 'bg-[#D4920A]', label: '5-6' };
  if (ageYears >= 3) return { color: 'bg-[#D4920A]', label: '3-5' };
  return { color: 'bg-[#4EAD72]', label: '<3' };
}

function SortButton({
  field,
  currentSort,
  onSort,
  children,
}: {
  field: SortField;
  currentSort: SortConfig;
  onSort: (field: SortField) => void;
  children: React.ReactNode;
}) {
  const isActive = currentSort.field === field;

  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 hover:text-[#F97316]"
    >
      {children}
      <span className="text-xs">
        {!isActive && <ArrowUpDown className="h-3 w-3" />}
        {isActive && currentSort.direction === 'asc' && <ArrowUp className="h-3 w-3" />}
        {isActive && currentSort.direction === 'desc' && <ArrowDown className="h-3 w-3" />}
      </span>
    </button>
  );
}

function formatChip(chip: string): React.ReactNode {
  if (chip.length <= 4) return chip;
  const last4 = chip.slice(-4);
  const rest = chip.slice(0, -4);
  return (
    <>
      <span className="text-[#4A7A94]">{rest}</span>
      <span className="font-semibold text-[#0D2030]">{last4}</span>
    </>
  );
}

function DogRow({ dog }: { dog: Dog }) {
  const deleteMutation = useDeleteDog();
  const [isDeleting, setIsDeleting] = useState(false);

  const ageDot = getAgeDot(dog.ageYears || 0);

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${dog.name}?`)) return;
    
    setIsDeleting(true);
    try {
      await deleteMutation.mutateAsync(dog.id);
      toast.success(`${dog.name} deleted successfully`);
    } catch {
      toast.error('Failed to delete dog');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleWhatsAppCopy = () => {
    const text = `*${dog.name}*\nChip: ${dog.microchip}\nBreed: ${dog.breed}\nGender: ${dog.gender === 'M' ? 'Male' : 'Female'}\nAge: ${dog.ageDisplay}`;
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <TableRow className="group">
      <TableCell>
        <div className="font-mono text-sm">{formatChip(dog.microchip)}</div>
      </TableCell>
      <TableCell>
        <div>
          <Link
            href={`/dogs/${dog.id}`}
            className="font-medium text-[#0D2030] hover:text-[#F97316] hover:underline"
          >
            {dog.name}
          </Link>
          <div className="text-xs text-[#4A7A94]">{dog.breed}</div>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <span className="text-sm">{dog.gender === 'M' ? 'Male' : 'Female'}</span>
          <span
            className={cn(
              'h-2.5 w-2.5 rounded-full',
              ageDot.color
            )}
            title={`Age: ${ageDot.label}`}
          />
        </div>
      </TableCell>
      <TableCell>
        <span className="text-sm text-[#4A7A94]">{dog.ageDisplay}</span>
      </TableCell>
      <TableCell>
        <Badge variant="secondary" className="text-xs">
          {dog.unit || '-'}
        </Badge>
      </TableCell>
      <TableCell>
        <div className="text-xs">
          {dog.damName && (
            <div className="text-[#4A7A94]">Dam: {dog.damName.slice(0, 15)}</div>
          )}
          {dog.sireName && (
            <div className="text-[#4A7A94]">Sire: {dog.sireName.slice(0, 15)}</div>
          )}
        </div>
      </TableCell>
      <TableCell>
        {dog.dnaStatus && (
          <Badge
            className={cn(
              'text-xs text-white',
              DNA_STATUS_COLORS[dog.dnaStatus] || 'bg-[#4A7A94]'
            )}
          >
            {DNA_STATUS_LABELS[dog.dnaStatus] || dog.dnaStatus}
          </Badge>
        )}
      </TableCell>
      <TableCell>
        <Badge
          className={cn(
            'text-xs text-white',
            STATUS_COLORS[dog.status] || 'bg-[#4A7A94]'
          )}
        >
          {DOG_STATUS_LABELS[dog.status] || dog.status}
        </Badge>
      </TableCell>
      <TableCell className="text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="rounded p-1 hover:bg-[#E8F4FF]">
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href={`/dogs/${dog.id}`}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleWhatsAppCopy}>
              <MessageSquare className="mr-2 h-4 w-4" />
              Copy for WhatsApp
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={handleDelete}
              className="text-[#D94040]"
              disabled={isDeleting}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              {isDeleting ? 'Deleting...' : 'Delete'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}

export function DogTable({ filters }: DogTableProps) {
  const [sort, setSort] = useState<SortConfig>({
    field: 'created_at',
    direction: 'desc',
  });
  const [page, setPage] = useState(1);
  const perPage = 25;

  const { data, isLoading, error } = useDogList({
    ...filters,
    page,
    perPage,
  });

  const handleSort = (field: SortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-[#D94040] bg-[#D94040]/10 p-4 text-center">
        <p className="text-sm text-[#D94040]">
          Failed to load dogs. Please try again.
        </p>
      </div>
    );
  }

  if (!data?.results?.length) {
    return (
      <div className="rounded-lg border border-[#C0D8EE] bg-[#E8F4FF] p-8 text-center">
        <Dog className="mx-auto h-12 w-12 text-[#C0D8EE]" />
        <h3 className="mt-2 text-lg font-medium text-[#0D2030]">No dogs found</h3>
        <p className="text-sm text-[#4A7A94]">
          Try adjusting your filters or search query
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-[#C0D8EE]">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#E8F4FF]">
              <TableHead>
                <SortButton field="microchip" currentSort={sort} onSort={handleSort}>
                  Chip
                </SortButton>
              </TableHead>
              <TableHead>
                <SortButton field="name" currentSort={sort} onSort={handleSort}>
                  Name / Breed
                </SortButton>
              </TableHead>
              <TableHead>Gender</TableHead>
              <TableHead>Age</TableHead>
              <TableHead>Unit</TableHead>
              <TableHead>Dam / Sire</TableHead>
              <TableHead>DNA</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.results.map((dog) => (
              <DogRow key={dog.id} dog={dog} />
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-[#4A7A94]">
          Showing {data.results.length} of {data.count} dogs
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded border border-[#C0D8EE] px-3 py-1 text-sm hover:bg-[#E8F4FF] disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={data.results.length < perPage}
            className="rounded border border-[#C0D8EE] px-3 py-1 text-sm hover:bg-[#E8F4FF] disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
