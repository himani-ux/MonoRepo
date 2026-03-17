import * as React from 'react';

import { cn } from '@/lib/utils';

/**
 * Textarea component - same styling as Input per DESIGN_SYSTEM.md Section 11.2
 * Used for root_cause_summary (min 50 chars), rework reasons (min 20 chars), etc.
 */
export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          'flex min-h-[80px] w-full rounded-md border bg-white px-3 py-2 text-base text-neutral-800 transition-colors duration-200',
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
Textarea.displayName = 'Textarea';

export { Textarea };
