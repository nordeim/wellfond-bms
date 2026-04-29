/**
 * Activity Feed Component
 * =======================
 * SSE-powered real-time activity stream with auto-scroll and pause on hover.
 *
 * Phase 8: Dashboard & Finance Exports
 * Design: Tangerine Sky theme with clean timeline aesthetics
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { Activity, Plus, Edit, Trash, FileText, LogIn, LogOut } from 'lucide-react';
import { useActivityFeed } from '@/hooks/use-dashboard';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ActivityFeedItem } from '@/lib/types';

interface ActivityFeedProps {
  className?: string;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
  create: <Plus className="h-4 w-4" />,
  update: <Edit className="h-4 w-4" />,
  delete: <Trash className="h-4 w-4" />,
  login: <LogIn className="h-4 w-4" />,
  logout: <LogOut className="h-4 w-4" />,
  view: <FileText className="h-4 w-4" />,
  export: <FileText className="h-4 w-4" />,
};

const ACTION_COLORS: Record<string, string> = {
  create: 'bg-[#E8F5E9] text-[#4EAD72]',
  update: 'bg-[#FFF8E1] text-[#D4920A]',
  delete: 'bg-[#FFEBEE] text-[#D94040]',
  login: 'bg-[#E8F4FF] text-[#0891B2]',
  logout: 'bg-[#F5F5F5] text-[#4A7A94]',
  view: 'bg-[#FFF0E6] text-[#F97316]',
  export: 'bg-[#F3E5F5] text-[#9C27B0]',
};

function ActivityItem({ activity }: { activity: ActivityFeedItem }) {
  const icon = ACTION_ICONS[activity.action] || <Activity className="h-4 w-4" />;
  const colorClass = ACTION_COLORS[activity.action] || 'bg-[#F5F5F5] text-[#4A7A94]';

  // Format timestamp
  const timeAgo = (() => {
    const now = new Date();
    const activityTime = new Date(activity.timestamp);
    const diffMinutes = Math.floor((now.getTime() - activityTime.getTime()) / 60000);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  })();

  return (
    <div className="flex items-start gap-3 py-3">
      {/* Icon */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          colorClass
        )}
      >
        {icon}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className="text-sm text-[#0D2030]">
          <span className="font-medium">{activity.actor_name}</span>{' '}
          <span className="text-[#4A7A94]">{activity.action}d</span>{' '}
          <span className="font-medium">{activity.resource_type}</span>
        </p>
        <p className="text-xs text-[#4A7A94]">{timeAgo}</p>
      </div>
    </div>
  );
}

export function ActivityFeed({ className }: ActivityFeedProps) {
  const { data: activities, isLoading } = useActivityFeed(20);
  const [isPaused, setIsPaused] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new activity
  useEffect(() => {
    if (!isPaused && scrollRef.current && activities) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activities, isPaused]);

  if (isLoading) {
    return (
      <Card className={cn('border-[#C0D8EE]', className)}>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="mb-3 h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={cn('border-[#C0D8EE]', className)}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-[#0D2030]">
          <Activity className="h-5 w-5 text-[#F97316]" />
          Recent Activity
          {isPaused && (
            <span className="text-xs font-normal text-[#4A7A94]">(paused)</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!activities || activities.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm text-[#4A7A94]">No recent activity</p>
          </div>
        ) : (
          <div
            ref={scrollRef}
            className="h-[300px] overflow-y-auto pr-4"
          >
            <div className="space-y-1">
              {activities.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
