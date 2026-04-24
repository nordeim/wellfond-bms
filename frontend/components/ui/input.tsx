/**
 * Wellfond BMS - Input Component
 * ================================
 * With label, error message, and helper text support.
 */

import * as React from 'react';

import { cn } from '@/lib/utils';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helper?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, helper, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={props.id}
            className="mb-1.5 block text-sm font-medium text-[#0D2030]"
          >
            {label}
            {props.required && (
              <span className="ml-1 text-[#D94040]">*</span>
            )}
          </label>
        )}
        <input
          type={type}
          className={cn(
            // Base styles
            'flex h-10 w-full rounded-lg border bg-white px-3 py-2 text-sm',
            'text-[#0D2030] placeholder:text-[#4A7A94]/50',
            // Focus styles
            'focus:outline-none focus:ring-2 focus:ring-[#F97316] focus:ring-offset-0',
            // Disabled styles
            'disabled:cursor-not-allowed disabled:bg-[#E8F4FF] disabled:opacity-50',
            // Error state
            error
              ? 'border-[#D94040] focus:border-[#D94040] focus:ring-[#D94040]/20'
              : 'border-[#C0D8EE] focus:border-[#F97316]',
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-xs text-[#D94040]">{error}</p>
        )}
        {helper && !error && (
          <p className="mt-1.5 text-xs text-[#4A7A94]">{helper}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
