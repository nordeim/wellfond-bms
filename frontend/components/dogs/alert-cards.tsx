/**
 * Alert Cards Component
 * =====================
 * Dashboard alert cards strip.
 */

'use client';

import { useMemo } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Heart,
  Calendar,
  Bell,
  Clock,
  ChevronUp,
  ChevronDown,
  Minus,
} from 'lucide-react';

import { useAlertCards } from '@/hooks/use-dogs';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import type { AlertCard } from '@/lib/types';

interface AlertCardsProps {
  entityId?: string;
  className?: string;
}

const ALERT_CONFIG: Record<string, { icon: React.ReactNode; label: string }> = {
  vaccine_overdue: {
    icon: <AlertCircle className="h-5 w-5" />,
    label: 'Vaccines Overdue',
  },
  vaccine_due_soon: {
    icon: <Clock className="h-5 w-5" />,
    label: 'Vaccines Due Soon',
  },
  rehome_overdue: {
    icon: <AlertTriangle className="h-5 w-5" />,
    label: 'Rehome Age',
  },
  in_heat: {
    icon: <Heart className="h-5 w-5" />,
    label: 'In Heat',
  },
  '8week_litters': {
    icon: <Calendar className="h-5 w-5" />,
    label: '8-Week Litters',
  },
  nursing_flags: {
    icon: <Bell className="h-5 w-5" />,
    label: 'Nursing Flags',
  },
  nparks_countdown: {
    icon: <Clock className="h-5 w-5" />,
    label: 'NParks Deadline',
  },
};

const COLOR_MAP: Record<string, string> = {
  red: 'bg-[#D94040] border-[#D94040] text-white',
  yellow: 'bg-[#D4920A] border-[#D4920A] text-white',
  pink: 'bg-pink-500 border-pink-500 text-white',
  blue: 'bg-[#0891B2] border-[#0891B2] text-white',
  orange: 'bg-[#F97316] border-[#F97316] text-white',
  navy: 'bg-[#0D2030] border-[#0D2030] text-white',
  green: 'bg-[#4EAD72] border-[#4EAD72] text-white',
};

function TrendIndicator({ trend }: { trend: number }) {
  if (trend > 0) {
    return <ChevronUp className="h-4 w-4" />;
  }
  if (trend < 0) {
    return <ChevronDown className="h-4 w-4" />;
  }
  return <Minus className="h-4 w-4" />;
}

function AlertCardItem({ alert }: { alert: AlertCard }) {
  const config = ALERT_CONFIG[alert.type] || {
    icon: <AlertCircle className="h-5 w-5" />,
    label: alert.title,
  };

  const colorClass = COLOR_MAP[alert.color] || COLOR_MAP.red;

  return (
    <div
      className={cn(
        'flex min-w-[180px] flex-col rounded-lg border p-3 transition-all',
        'hover:shadow-md cursor-pointer',
        colorClass
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {config.icon}
          <span className="text-sm font-medium">{config.label}</span>
        </div>
        <div className="flex items-center gap-1 text-xs opacity-80">
          <TrendIndicator trend={alert.trend} />
        </div>
      </div>
      <div className="mt-2 text-2xl font-bold">{alert.count}</div>
    </div>
  );
}

export function AlertCards({ entityId, className }: AlertCardsProps) {
  const { data: alerts, isLoading } = useAlertCards({ entityId });

  const skeletonCards = useMemo(
    () => Array.from({ length: 6 }, (_, i) => i),
    []
  );

  if (isLoading) {
    return (
      <div className={cn('flex gap-3 overflow-x-auto pb-2', className)}>
        {skeletonCards.map((i) => (
          <Skeleton key={i} className="h-[88px] min-w-[180px] rounded-lg" />
        ))}
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className={cn('rounded-lg border border-[#C0D8EE] bg-[#E8F4FF] p-4 text-center', className)}>
        <p className="text-sm text-[#4A7A94]">No alerts</p>
      </div>
    );
  }

  return (
    <div className={cn('flex gap-3 overflow-x-auto pb-2', className)}>
      {alerts.map((alert) => (
        <AlertCardItem key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
