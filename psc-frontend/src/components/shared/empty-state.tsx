import type { FC, ReactNode } from 'react';
import { FileText, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui';

/**
 * Empty state component per APP_FLOW.md Section 2.2
 * Shows when there's no data to display
 */

export interface EmptyStateProps {
  /** Icon to display (default: FileText) */
  icon?: LucideIcon;
  /** Title text */
  title: string;
  /** Description text */
  description?: string;
  /** Action button label */
  actionLabel?: string;
  /** Action button click handler */
  onAction?: () => void;
  /** Custom content to render below description */
  children?: ReactNode;
  /** Additional class names */
  className?: string;
}

export const EmptyState: FC<EmptyStateProps> = ({
  icon: Icon = FileText,
  title,
  description,
  actionLabel,
  onAction,
  children,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center px-4 py-12 text-center',
        className
      )}
    >
      <div className="mb-4 rounded-full bg-neutral-100 p-4">
        <Icon className="h-8 w-8 text-neutral-400" />
      </div>
      <h3 className="mb-1 text-lg font-medium text-neutral-800">{title}</h3>
      {description && (
        <p className="mb-4 max-w-md text-sm text-neutral-500">{description}</p>
      )}
      {children}
      {actionLabel && onAction && (
        <Button onClick={onAction} className="mt-4">
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

// Pre-configured empty states per APP_FLOW.md

export interface EmptyStateInspectionsProps {
  onCreateFirst?: () => void;
}

export const EmptyStateInspections: FC<EmptyStateInspectionsProps> = ({
  onCreateFirst,
}) => (
  <EmptyState
    title="No inspections recorded yet"
    description="Previous inspection records (up to 3 years) will appear here once uploaded."
    actionLabel={onCreateFirst ? 'Create First Inspection' : undefined}
    onAction={onCreateFirst}
  />
);

export interface EmptyStateFilterResultsProps {
  onClearFilters?: () => void;
  title?: string;
  description?: string;
  clearLabel?: string;
}

export const EmptyStateFilterResults: FC<EmptyStateFilterResultsProps> = ({
  onClearFilters,
  title = 'No inspections found',
  description = 'No inspections match your current filter criteria.',
  clearLabel = 'Clear Filters',
}) => (
  <EmptyState
    title={title}
    description={description}
    actionLabel={onClearFilters ? clearLabel : undefined}
    onAction={onClearFilters}
  />
);

export const EmptyStateCARs: FC = () => (
  <EmptyState
    title="No CARs found"
    description="CARs are automatically created when deficiencies are added to inspections."
  />
);

export const EmptyStateDeficiencies: FC = () => (
  <EmptyState
    title="No deficiencies added yet"
    description="Add deficiencies found during the inspection."
  />
);

export const EmptyStateNotifications: FC = () => (
  <EmptyState
    title="No notifications"
    description="You're all caught up! New notifications will appear here."
  />
);
