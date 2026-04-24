/**
 * Wellfond BMS - Button Component
 * ================================
 * Variants: primary, secondary, ghost, destructive
 * Sizes: sm, md, lg
 */

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  // Base styles
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F97316] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        // Primary: Tangerine orange
        primary:
          'bg-[#F97316] text-white hover:bg-[#EA580C] shadow-md hover:shadow-lg active:scale-[0.98]',
        // Secondary: Cyan
        secondary:
          'bg-[#0891B2] text-white hover:bg-[#0E7490] shadow-md hover:shadow-lg active:scale-[0.98]',
        // Ghost: Transparent
        ghost:
          'bg-transparent text-[#0D2030] hover:bg-[#E8F4FF] active:bg-[#DDEEFF]',
        // Destructive: Red
        destructive:
          'bg-[#D94040] text-white hover:bg-[#B91C1C] shadow-md hover:shadow-lg active:scale-[0.98]',
        // Outline: Bordered
        outline:
          'border-2 border-[#C0D8EE] bg-white text-[#0D2030] hover:bg-[#E8F4FF] hover:border-[#4A7A94]',
      },
      size: {
        sm: 'h-8 px-3 text-sm rounded-md',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-lg',
        icon: 'h-10 w-10 p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

// Loading spinner component
function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin h-4 w-4', className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      asChild = false,
      loading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : 'button';

    return (
      <Comp
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            <LoadingSpinner />
            <span className="opacity-70">{children}</span>
          </>
        ) : (
          children
        )}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
