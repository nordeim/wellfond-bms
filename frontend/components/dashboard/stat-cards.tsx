/**
 * Stat Cards Component
 * ====================
 * Summary stat cards for dashboard: dogs, litters, agreements, vaccinations.
 *
 * Phase 8: Dashboard & Finance Exports
 * Design: Tangerine Sky theme with subtle shadows and orange accents
 */

'use client';

import { Dog, Heart, FileText, AlertCircle } from 'lucide-react';
import { useQuickStats } from '@/hooks/use-dashboard';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import type { DashboardStats } from '@/lib/types';

interface StatCardsProps {
  entityId?: string | undefined;
  className?: string | undefined;
  variant?: 'default' | 'compact';
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'orange' | 'blue' | 'green' | 'red';
  href?: string;
}

const COLOR_MAP = {
  orange: {
    bg: 'bg-[#FFF0E6]',
    text: 'text-[#F97316]',
    border: 'border-[#FFD4B8]',
  },
  blue: {
    bg: 'bg-[#E8F4FF]',
    text: 'text-[#0891B2]',
    border: 'border-[#C0D8EE]',
  },
  green: {
    bg: 'bg-[#E8F5E9]',
    text: 'text-[#4EAD72]',
    border: 'border-[#A5D6A7]',
  },
  red: {
    bg: 'bg-[#FFEBEE]',
    text: 'text-[#D94040]',
    border: 'border-[#EF9A9A]',
  },
};

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colors = COLOR_MAP[color];

  return (
    <div
      className={cn(
        'flex items-center gap-4 rounded-lg border p-4 transition-all',
        'hover:shadow-md cursor-pointer',
        colors.bg,
        colors.border
      )}
    >
      <div
        className={cn(
          'flex h-12 w-12 items-center justify-center rounded-lg',
          'bg-white shadow-sm',
          colors.text
        )}
      >
        {icon}
      </div>
      <div>
        <p className="text-sm text-[#4A7A94]">{title}</p>
        <p className={cn('text-2xl font-bold', colors.text)}>{value}</p>
      </div>
    </div>
  );
}

export function StatCards({ entityId, className, variant = 'default' }: StatCardsProps) {
  const { data: stats, isLoading } = useQuickStats();

  if (isLoading) {
    return (
      <div className={cn('grid gap-4 sm:grid-cols-2', className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-lg" />
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className={cn('rounded-lg border border-[#C0D8EE] bg-white p-4 text-center', className)}>
        <p className="text-sm text-[#4A7A94]">No stats available</p>
      </div>
    );
  }

  const cards: StatCardProps[] = [
    {
      title: 'Total Dogs',
      value: stats.total_dogs,
      icon: <Dog className="h-6 w-6" />,
      color: 'orange',
    },
    {
      title: 'Active Litters',
      value: stats.active_litters,
      icon: <Heart className="h-6 w-6" />,
      color: 'blue',
    },
    {
      title: 'Pending Agreements',
      value: stats.pending_agreements,
      icon: <FileText className="h-6 w-6" />,
      color: 'green',
    },
    {
      title: 'Overdue Vaccines',
      value: stats.overdue_vaccinations,
      icon: <AlertCircle className="h-6 w-6" />,
      color: 'red',
    },
  ];

  return (
    <div
      className={cn(
        'grid gap-4',
        variant === 'compact' ? 'grid-cols-2' : 'sm:grid-cols-2',
        className
      )}
    >
      {cards.map((card) => (
        <StatCard key={card.title} {...card} />
      ))}
    </div>
  );
}
