/**
 * Shared components barrel export
 * All reusable components used across the application
 */

// Status display
export {
  StatusBadge,
  type StatusBadgeProps,
  type StatusType,
} from './status-badge';

// Status utilities (from lib/utils to avoid react-refresh warnings)
export { getStatusVariant, getStatusLabel } from '@/lib/utils/format-status';

// Date picker
export { DatePicker, type DatePickerProps } from './date-picker';

// Date utilities (from lib/utils to avoid react-refresh warnings)
export { formatDisplayDate, formatAPIDate } from '@/lib/utils/format-date';

// File upload
export { FileUpload, type FileUploadProps } from './file-upload';

// Search input
export { SearchInput, type SearchInputProps } from './search-input';

// Empty states
export {
  EmptyState,
  EmptyStateInspections,
  EmptyStateFilterResults,
  EmptyStateCARs,
  EmptyStateDeficiencies,
  EmptyStateNotifications,
  type EmptyStateProps,
  type EmptyStateInspectionsProps,
  type EmptyStateFilterResultsProps,
} from './empty-state';

// Error states
export {
  ErrorState,
  NetworkErrorState,
  NotFoundErrorState,
  ServerErrorState,
  type ErrorStateProps,
  type NetworkErrorStateProps,
  type NotFoundErrorStateProps,
  type ServerErrorStateProps,
} from './error-state';

// Loading skeletons
export {
  TextSkeleton,
  CardSkeleton,
  ListSkeleton,
  FormFieldSkeleton,
  FormSkeleton,
  DetailHeaderSkeleton,
  SectionSkeleton,
  InspectionCardSkeleton,
  CARCardSkeleton,
  DeficiencyItemSkeleton,
  type LoadingSkeletonProps,
  type TextSkeletonProps,
  type CardSkeletonProps,
  type ListSkeletonProps,
  type FormFieldSkeletonProps,
  type FormSkeletonProps,
} from './loading-skeleton';

// Confirmation dialogs
export {
  ConfirmDialog,
  DeleteConfirmDialog,
  DiscardChangesDialog,
  SubmitConfirmDialog,
  type ConfirmDialogProps,
  type DeleteConfirmDialogProps,
  type DiscardChangesDialogProps,
  type SubmitConfirmDialogProps,
} from './confirm-dialog';

// DefCode select
export {
  DefCodeSelect,
  DefCodeDisplay,
  type DefCodeSelectProps,
  type DefCodeDisplayProps,
} from './def-code-select';
