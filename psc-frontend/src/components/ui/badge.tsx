/* eslint-disable react-refresh/only-export-components */
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

/**
 * Badge component per DESIGN_SYSTEM.md Section 11.4 and 1.4 (Status Badge Colors)
 * - Pill shape (radius-full)
 * - text-xs, font-medium, uppercase
 * - Status-specific colors per Section 1.4
 */
const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium uppercase transition-colors',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary-500 text-white',
        secondary: 'border-transparent bg-neutral-100 text-neutral-700',
        outline: 'border-neutral-300 text-neutral-700',
        // Status variants per DESIGN_SYSTEM.md Section 1.4
        draft: 'border-neutral-300 bg-neutral-100 text-neutral-700',
        submitted: 'border-primary-300 bg-primary-100 text-primary-700',
        pic_reviewed: 'border-info-500 bg-info-100 text-info-700',
        pic_accepted: 'border-info-500 bg-info-100 text-info-700',
        rework_requested: 'border-warning-500 bg-warning-100 text-warning-700',
        dpa_closed: 'border-success-500 bg-success-100 text-success-700',
        overdue: 'border-error-500 bg-error-100 text-error-700',
        detention: 'border-2 border-error-500 bg-error-100 text-error-700',
        // Generic semantic variants
        success: 'border-transparent bg-success-100 text-success-700',
        warning: 'border-transparent bg-warning-100 text-warning-700',
        destructive: 'border-transparent bg-error-100 text-error-700',
        info: 'border-transparent bg-info-100 text-info-700',
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
