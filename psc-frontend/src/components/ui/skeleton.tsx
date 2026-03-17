import { cn } from '@/lib/utils';

/**
 * Skeleton loading component per DESIGN_SYSTEM.md
 * - Used for loading states (FRONTEND_GUIDELINES.md Section 3.3)
 * - Animated pulse effect
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-neutral-200', className)}
      {...props}
    />
  );
}

export { Skeleton };
