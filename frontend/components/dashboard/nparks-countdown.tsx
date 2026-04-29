/**
 * NParks Countdown Widget
 * =======================
 * Shows days until NParks submission deadline with status colors.
 *
 * Phase 8: Dashboard & Finance Exports
 * Design: Tangerine Sky theme with urgency-based color coding
 */

'use client';

import { Calendar, Clock, AlertTriangle } from 'lucide-react';
import { useNParksCountdown } from '@/hooks/use-dashboard';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface NParksCountdownProps {
  className?: string;
}

const STATUS_CONFIG = {
  upcoming: {
    icon: Calendar,
    color: 'text-[#0891B2]',
    bgColor: 'bg-[#E8F4FF]',
    borderColor: 'border-[#C0D8EE]',
    label: 'Upcoming',
  },
  due_soon: {
    icon: Clock,
    color: 'text-[#D4920A]',
    bgColor: 'bg-[#FFF8E1]',
    borderColor: 'border-[#FFE082]',
    label: 'Due Soon',
  },
  overdue: {
    icon: AlertTriangle,
    color: 'text-[#D94040]',
    bgColor: 'bg-[#FFEBEE]',
    borderColor: 'border-[#EF9A9A]',
    label: 'Overdue',
  },
};

export function NParksCountdown({ className }: NParksCountdownProps) {
  const { data: countdown, isLoading } = useNParksCountdown();

  if (isLoading) {
    return (
      <Card className={cn('border-[#C0D8EE]', className)}>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!countdown) {
    return (
      <Card className={cn('border-[#C0D8EE]', className)}>
        <CardContent className="p-6 text-center">
          <p className="text-sm text-[#4A7A94]">Unable to load NParks countdown</p>
        </CardContent>
      </Card>
    );
  }

  const status = countdown.status;
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  // Only show if within a week or overdue
  if (status === 'upcoming' && countdown.days > 7) {
    return null;
  }

  return (
    <Card
      className={cn(
        'border-2 transition-all hover:shadow-md',
        config.borderColor,
        config.bgColor,
        className
      )}
    >
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-[#0D2030]">
          <Icon className={cn('h-5 w-5', config.color)} />
          NParks Submission
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Days Counter */}
        <div className="flex items-baseline gap-2">
          <span className={cn('text-4xl font-bold', config.color)}>
            {countdown.days}
          </span>
          <span className="text-sm text-[#4A7A94]">
            {countdown.days === 1 ? 'day' : 'days'} remaining
          </span>
        </div>

        {/* Deadline Date */}
        <p className="text-sm text-[#4A7A94]">
          Deadline:{' '}
          <span className="font-medium text-[#0D2030]">
            {new Date(countdown.deadline_date).toLocaleDateString('en-SG', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </span>
        </p>

        {/* Status Badge */}
        <div
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
            config.bgColor,
            config.color
          )}
        >
          <Icon className="h-3.5 w-3.5" />
          {config.label}
        </div>

        {/* Action Button */}
        <Link href="/compliance">
          <Button
            variant="outline"
            className={cn(
              'w-full border-[#C0D8EE] hover:bg-white',
              status === 'overdue' && 'border-[#D94040] text-[#D94040] hover:bg-[#FFEBEE]'
            )}
          >
            {status === 'overdue' ? 'Submit Now' : 'Go to Compliance'}
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}
