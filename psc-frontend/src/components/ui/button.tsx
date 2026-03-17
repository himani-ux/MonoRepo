/* eslint-disable react-refresh/only-export-components */
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

/**
 * Button variants per DESIGN_SYSTEM.md Section 11.1
 * - Primary: primary-500 bg, white text
 * - Secondary: white bg, neutral-300 border
 * - Destructive: error-600 bg, white text
 * - Ghost: transparent bg, neutral-100 hover
 * - Outline: transparent bg, neutral-300 border
 * - Link: text-primary-500, underline on hover
 */
const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-semibold transition-all duration-150 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700',
        destructive:
          'bg-error-600 text-white hover:bg-error-700 active:bg-error-700',
        outline:
          'border border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50 hover:border-neutral-400',
        secondary:
          'bg-neutral-100 text-neutral-700 hover:bg-neutral-200',
        ghost:
          'text-neutral-700 hover:bg-neutral-100',
        link:
          'text-primary-500 underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2.5', // 10px 16px padding
        sm: 'h-8 px-3 py-2 text-xs', // 8px 12px padding
        lg: 'h-12 px-5 py-3', // 12px 20px padding
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
