/**
 * Dogs Page - Wellfond BMS
 * =========================
 * Master list with alerts, filters, and table.
 */

import { Suspense } from 'react';
import Link from 'next/link';
import { Plus, Download, Dog } from 'lucide-react';

import { AlertCards } from '@/components/dogs/alert-cards';
import { ChipSearch } from '@/components/dogs/chip-search';
import { DogFilters } from '@/components/dogs/dog-filters';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { DogFilterParams } from '@/lib/types';
import { DogTable } from '@/components/dogs/dog-table';

interface DogsPageProps {
  searchParams: { [key: string]: string | string[] | undefined };
}

export default function DogsPage({ searchParams }: DogsPageProps) {
  // Parse filters from URL
  const filters: DogFilterParams = {
    status: searchParams.status as string | undefined,
    entity: searchParams.entity as string | undefined,
    breed: searchParams.breed as string | undefined,
    gender: searchParams.gender as string | undefined,
    search: searchParams.search as string | undefined,
    unit: searchParams.unit as string | undefined,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#0D2030]">Dogs</h1>
          <p className="text-sm text-[#4A7A94]">
            Manage breeding dogs, health records, and vaccinations
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dogs/import">
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Import CSV
            </Button>
          </Link>
          <Link href="/dogs/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Dog
            </Button>
          </Link>
        </div>
      </div>

      {/* Alert Cards */}
      <Suspense fallback={<AlertCardsSkeleton />}>
        <AlertCards />
      </Suspense>

      {/* Main Content */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Dog className="h-5 w-5" />
            Dog Master List
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Search & Filters */}
          <div className="mb-4 space-y-3">
            <ChipSearch placeholder="Search by chip or name..." />
            <DogFilters filters={filters} />
          </div>

          {/* Dog Table */}
          <Suspense fallback={<DogTableSkeleton />}>
            <DogTable filters={filters} />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}

function AlertCardsSkeleton() {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-[88px] min-w-[180px] rounded-lg" />
      ))}
    </div>
  );
}

function DogTableSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 10 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}
