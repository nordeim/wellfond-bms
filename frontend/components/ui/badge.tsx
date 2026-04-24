/**
 * Wellfond BMS - Badge Component
 * ===============================
 * Variants: default, success, warning, error, info
 * Pill shape, 12px font.
 */

import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  // Base styles
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        // Default: Navy
        default: 'bg-[#0D2030] text-white',
        // Success: Green
        success: 'bg-[#4EAD72] text-white',
        // Warning: Amber
        warning: 'bg-[#D4920A] text-white',
        // Error: Red
        error: 'bg-[#D94040] text-white',
        // Info: Teal
        info: 'bg-[#0891B2] text-white',
        // Secondary: Light background
        secondary: 'bg-[#E8F4FF] text-[#0D2030]',
        // Outline: Bordered
        outline: 'border border-[#C0D8EE] bg-white text-[#0D2030]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
