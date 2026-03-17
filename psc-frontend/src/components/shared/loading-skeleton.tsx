import type { FC } from 'react';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui';

/**
 * Loading skeleton variants per APP_FLOW.md loading states
 * Uses Skeleton component from ui/skeleton.tsx
 */

export interface LoadingSkeletonProps {
  /** Additional class names */
  className?: string;
}

// ============================================================================
// Text Skeletons
// ============================================================================

export interface TextSkeletonProps extends LoadingSkeletonProps {
  /** Width of the text line (default: full) */
  width?: 'full' | '3/4' | '1/2' | '1/4' | '1/3' | '2/3';
}

export const TextSkeleton: FC<TextSkeletonProps> = ({
  width = 'full',
  className,
}) => {
  const widthClass = {
    full: 'w-full',
    '3/4': 'w-3/4',
    '1/2': 'w-1/2',
    '1/4': 'w-1/4',
    '1/3': 'w-1/3',
    '2/3': 'w-2/3',
  }[width];

  return <Skeleton className={cn('h-4', widthClass, className)} />;
};

// ============================================================================
// Card Skeletons
// ============================================================================

export interface CardSkeletonProps extends LoadingSkeletonProps {
  /** Show as detention card (red left border) */
  isDetention?: boolean;
}

export const CardSkeleton: FC<CardSkeletonProps> = ({
  isDetention,
  className,
}) => (
  <div
    className={cn(
      'rounded-lg border border-neutral-200 bg-white p-4',
      isDetention && 'border-l-4 border-l-error-500',
      className
    )}
  >
    <div className="flex items-start justify-between">
      <div className="flex-1 space-y-2">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-4 w-1/2" />
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
    <div className="mt-3 space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  </div>
);

// ============================================================================
// List Skeletons
// ============================================================================

export interface ListSkeletonProps extends LoadingSkeletonProps {
  /** Number of skeleton items to show */
  count?: number;
  /** Show as card list */
  variant?: 'card' | 'simple';
}

export const ListSkeleton: FC<ListSkeletonProps> = ({
  count = 3,
  variant = 'card',
  className,
}) => (
  <div className={cn('space-y-3', className)}>
    {Array.from({ length: count }).map((_, i) =>
      variant === 'card' ? (
        <CardSkeleton key={i} />
      ) : (
        <div key={i} className="flex items-center gap-3 py-2">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      )
    )}
  </div>
);

// ============================================================================
// Form Skeletons
// ============================================================================

export interface FormFieldSkeletonProps extends LoadingSkeletonProps {
  /** Show label skeleton */
  showLabel?: boolean;
}

export const FormFieldSkeleton: FC<FormFieldSkeletonProps> = ({
  showLabel = true,
  className,
}) => (
  <div className={cn('space-y-2', className)}>
    {showLabel && <Skeleton className="h-4 w-24" />}
    <Skeleton className="h-10 w-full" />
  </div>
);

export interface FormSkeletonProps extends LoadingSkeletonProps {
  /** Number of fields */
  fieldCount?: number;
}

export const FormSkeleton: FC<FormSkeletonProps> = ({
  fieldCount = 4,
  className,
}) => (
  <div className={cn('space-y-4', className)}>
    {Array.from({ length: fieldCount }).map((_, i) => (
      <FormFieldSkeleton key={i} />
    ))}
    <div className="flex justify-end gap-2 pt-4">
      <Skeleton className="h-10 w-24" />
      <Skeleton className="h-10 w-24" />
    </div>
  </div>
);

// ============================================================================
// Detail Page Skeletons
// ============================================================================

export const DetailHeaderSkeleton: FC<LoadingSkeletonProps> = ({ className }) => (
  <div className={cn('space-y-3', className)}>
    <div className="flex items-start justify-between">
      <div className="space-y-2">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-6 w-24 rounded-full" />
    </div>
    <div className="flex gap-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-24" />
    </div>
  </div>
);

export const SectionSkeleton: FC<LoadingSkeletonProps> = ({ className }) => (
  <div className={cn('space-y-3', className)}>
    <Skeleton className="h-5 w-32" />
    <div className="space-y-2">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  </div>
);

// ============================================================================
// Inspection/CAR Specific Skeletons
// ============================================================================

export const InspectionCardSkeleton: FC<LoadingSkeletonProps> = ({ className }) => (
  <CardSkeleton className={className} />
);

export const CARCardSkeleton: FC<LoadingSkeletonProps> = ({ className }) => (
  <div
    className={cn(
      'rounded-lg border border-neutral-200 bg-white p-4',
      className
    )}
  >
    <div className="flex items-start justify-between">
      <div className="space-y-1">
        <Skeleton className="h-5 w-32" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-5 w-16 rounded bg-neutral-200" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
    <div className="mt-3 flex items-center gap-4">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-32" />
    </div>
  </div>
);

export const DeficiencyItemSkeleton: FC<LoadingSkeletonProps> = ({ className }) => (
  <div
    className={cn(
      'rounded-lg border border-neutral-200 bg-white p-3',
      className
    )}
  >
    <div className="flex items-start justify-between">
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-16 rounded bg-neutral-200" />
        <Skeleton className="h-4 w-32" />
      </div>
      <Skeleton className="h-5 w-16" />
    </div>
    <Skeleton className="mt-2 h-4 w-full" />
    <div className="mt-2 flex items-center gap-2">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-5 w-16 rounded-full" />
    </div>
  </div>
);
