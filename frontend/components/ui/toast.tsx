/**
 * Wellfond BMS - Toast Component
 * =================================
 * Auto-dismiss after 5 seconds, position bottom-right.
 * Uses Sonner library.
 */

'use client';

import { Toaster as Sonner } from 'sonner';

type ToasterProps = React.ComponentProps<typeof Sonner>;

/**
 * Toast notifications with Sonner.
 * Position: bottom-right
 * Duration: 5 seconds
 * 
 * Usage:
 *   import { toast } from 'sonner';
 *   toast.success('Operation completed');
 *   toast.error('Something went wrong');
 *   toast.info('Please check your email');
 */
function Toaster({ ...props }: ToasterProps) {
  return (
    <Sonner
      theme="light"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-white group-[.toaster]:text-[#0D2030] group-[.toaster]:border-[#C0D8EE] group-[.toaster]:shadow-lg group-[.toaster]:rounded-xl',
          description: 'group-[.toast]:text-[#4A7A94]',
          actionButton:
            'group-[.toast]:bg-[#F97316] group-[.toast]:text-white',
          cancelButton:
            'group-[.toast]:bg-[#E8F4FF] group-[.toast]:text-[#0D2030]',
          success: 'group-[.toast]:border-l-4 group-[.toast]:border-l-[#4EAD72]',
          error: 'group-[.toast]:border-l-4 group-[.toast]:border-l-[#D94040]',
          info: 'group-[.toast]:border-l-4 group-[.toast]:border-l-[#0891B2]',
          warning: 'group-[.toast]:border-l-4 group-[.toast]:border-l-[#D4920A]',
        },
      }}
      position="bottom-right"
      duration={5000}
      {...props}
    />
  );
}

export { Toaster };
