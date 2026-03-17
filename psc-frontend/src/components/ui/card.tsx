import * as React from 'react';

import { cn } from '@/lib/utils';

/**
 * Card component per DESIGN_SYSTEM.md Section 11.3
 * - Default: white bg, neutral-200 border, rounded-lg (8px), shadow-md
 * - Clickable hover: shadow-lg, translateY(-2px)
 * - Detention variant: 4px error-500 left border, error-50 bg
 */

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    clickable?: boolean;
    detention?: boolean;
  }
>(({ className, clickable, detention, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-lg border bg-surface-card text-neutral-800 shadow-md',
      clickable &&
        'cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg',
      detention
        ? 'border-l-4 border-l-error-500 bg-error-50'
        : 'border-neutral-200',
      className
    )}
    {...props}
  />
));
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-4', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('text-lg font-medium leading-none tracking-tight', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-neutral-500', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-4 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-4 pt-0', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
