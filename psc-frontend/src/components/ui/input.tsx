import * as React from 'react';

import { cn } from '@/lib/utils';

/**
 * Input component per DESIGN_SYSTEM.md Section 11.2
 * - Default: white bg, neutral-300 border, neutral-800 text
 * - Focus: primary-500 border, primary-100 ring
 * - Error: error-500 border, error-100 ring
 * - Disabled: neutral-100 bg, neutral-400 text
 */
export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border bg-white px-3 py-2.5 text-base text-neutral-800 transition-colors duration-200',
          'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-neutral-700',
          'placeholder:text-neutral-400',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-0',
          'disabled:cursor-not-allowed disabled:bg-neutral-100 disabled:text-neutral-400',
          error
            ? 'border-error-500 focus-visible:border-error-500 focus-visible:ring-error-100'
            : 'border-neutral-300 focus-visible:border-primary-500 focus-visible:ring-primary-100',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';

export { Input };
