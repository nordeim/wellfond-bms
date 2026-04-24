/**
 * Wellfond BMS - Skeleton Component
 * ====================================
 * Pulse animation for loading states.
 * Variants: line, circle, rect
 */

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'line' | 'circle' | 'rect';
  width?: string | number;
  height?: string | number;
}

/**
 * Skeleton loading placeholder.
 * Use during data fetching to improve perceived performance.
 */
function Skeleton({
  className,
  variant = 'line',
  width,
  height,
}: SkeletonProps) {
  const style: React.CSSProperties = {};

  if (width) {
    style.width = typeof width === 'number' ? `${width}px` : width;
  }
  if (height) {
    style.height = typeof height === 'number' ? `${height}px` : height;
  }

  const baseClasses =
    'animate-pulse bg-[#C0D8EE]/50 rounded-md';

  const variantClasses = {
    line: 'h-4 w-full',
    circle: 'h-12 w-12 rounded-full',
    rect: 'h-24 w-full rounded-lg',
  };

  return (
    <div
      className={cn(baseClasses, variantClasses[variant], className)}
      style={style}
      aria-hidden="true"
    />
  );
}

/**
 * Skeleton card for card-shaped loading states.
 */
function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('space-y-3 rounded-xl border border-[#C0D8EE] bg-white p-6', className)}>
      <Skeleton variant="line" className="w-3/4" />
      <Skeleton variant="line" className="w-1/2" />
      <Skeleton variant="rect" />
    </div>
  );
}

/**
 * Skeleton table for table loading states.
 */
function SkeletonTable({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn('w-full space-y-2', className)}>
      {/* Header */}
      <div className="flex gap-4">
        <Skeleton variant="line" className="w-1/4" />
        <Skeleton variant="line" className="w-1/4" />
        <Skeleton variant="line" className="w-1/4" />
        <Skeleton variant="line" className="w-1/4" />
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <Skeleton variant="line" className="w-1/4 h-10" />
          <Skeleton variant="line" className="w-1/4 h-10" />
          <Skeleton variant="line" className="w-1/4 h-10" />
          <Skeleton variant="line" className="w-1/4 h-10" />
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton text for paragraph loading states.
 */
function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="line"
          className={i === lines - 1 ? 'w-3/4' : 'w-full'}
        />
      ))}
    </div>
  );
}

export { Skeleton, SkeletonCard, SkeletonTable, SkeletonText };
