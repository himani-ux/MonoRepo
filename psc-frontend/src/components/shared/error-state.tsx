import type { FC, ReactNode } from 'react';
import { AlertCircle, RefreshCw, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui';

/**
 * Error state component per APP_FLOW.md
 * Shows when an error occurs during data fetching
 */

export interface ErrorStateProps {
  /** Error title */
  title?: string;
  /** Error message */
  message?: string;
  /** Retry button click handler */
  onRetry?: () => void;
  /** Retry button label */
  retryLabel?: string;
  /** Show as network/offline error */
  isNetworkError?: boolean;
  /** Custom content to render */
  children?: ReactNode;
  /** Additional class names */
  className?: string;
}

export const ErrorState: FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message = 'An error occurred while loading the data. Please try again.',
  onRetry,
  retryLabel = 'Try Again',
  isNetworkError = false,
  children,
  className,
}) => {
  const Icon = isNetworkError ? WifiOff : AlertCircle;

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center px-4 py-12 text-center',
        className
      )}
    >
      <div className="mb-4 rounded-full bg-error-50 p-4">
        <Icon className="h-8 w-8 text-error-500" />
      </div>
      <h3 className="mb-1 text-lg font-medium text-neutral-800">{title}</h3>
      <p className="mb-4 max-w-md text-sm text-neutral-500">{message}</p>
      {children}
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-2 gap-2">
          <RefreshCw className="h-4 w-4" />
          {retryLabel}
        </Button>
      )}
    </div>
  );
};

// Pre-configured error states

export interface NetworkErrorStateProps {
  onRetry?: () => void;
}

export const NetworkErrorState: FC<NetworkErrorStateProps> = ({ onRetry }) => (
  <ErrorState
    title="Unable to connect"
    message="Check your internet connection and try again."
    isNetworkError
    onRetry={onRetry}
  />
);

export interface NotFoundErrorStateProps {
  entityName?: string;
  onGoBack?: () => void;
}

export const NotFoundErrorState: FC<NotFoundErrorStateProps> = ({
  entityName = 'Item',
  onGoBack,
}) => (
  <ErrorState
    title={`${entityName} not found`}
    message={`The ${entityName.toLowerCase()} may have been deleted or you don't have access.`}
  >
    {onGoBack && (
      <Button onClick={onGoBack} variant="outline" className="mt-2">
        Go Back
      </Button>
    )}
  </ErrorState>
);

export interface ServerErrorStateProps {
  onRetry?: () => void;
}

export const ServerErrorState: FC<ServerErrorStateProps> = ({ onRetry }) => (
  <ErrorState
    title="Server error"
    message="Something went wrong on our end. Please try again later."
    onRetry={onRetry}
  />
);
