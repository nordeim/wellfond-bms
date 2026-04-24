/**
 * Wellfond BMS - Progress Component
 * ====================================
 * Animated fill bar with orange background.
 * Built on Radix Progress.
 */

'use client';

import * as ProgressPrimitive from '@radix-ui/react-progress';
import * as React from 'react';

import { cn } from '@/lib/utils';

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      'relative h-2 w-full overflow-hidden rounded-full bg-[#C0D8EE]/50',
      className
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="h-full w-full flex-1 bg-[#F97316] transition-all duration-500 ease-out"
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

/**
 * Progress with label showing percentage.
 */
interface ProgressWithLabelProps {
  className?: string;
  value?: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'error';
}

const ProgressWithLabel = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressWithLabelProps
>(
  (
    { className, value = 0, showLabel = true, size = 'md', variant = 'default', ...props },
    ref
  ) => {
    const variantColors = {
      default: 'bg-[#F97316]',
      success: 'bg-[#4EAD72]',
      warning: 'bg-[#D4920A]',
      error: 'bg-[#D94040]',
    };

    const sizes = {
      sm: 'h-1.5',
      md: 'h-2',
      lg: 'h-3',
    };

    return (
      <div className={cn('w-full space-y-1.5', className)}>
        {showLabel && (
          <div className="flex justify-between text-xs text-[#4A7A94]">
            <span>Progress</span>
            <span className="font-medium text-[#0D2030]">{Math.round(value)}%</span>
          </div>
        )}
        <ProgressPrimitive.Root
          ref={ref}
          className={cn(
            'relative w-full overflow-hidden rounded-full bg-[#C0D8EE]/50',
            sizes[size]
          )}
          {...props}
        >
          <ProgressPrimitive.Indicator
            className={cn(
              'h-full w-full flex-1 transition-all duration-500 ease-out',
              variantColors[variant]
            )}
            style={{ transform: `translateX(-${100 - value}%)` }}
          />
        </ProgressPrimitive.Root>
      </div>
    );
  }
);
ProgressWithLabel.displayName = 'ProgressWithLabel';

export { Progress, ProgressWithLabel };
