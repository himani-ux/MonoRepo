/**
 * Authentication guard component.
 *
 * Protects routes that require authentication.
 * Redirects to login if not authenticated.
 *
 * Per IMPLEMENTATION_PLAN.md Step 2.5
 */

import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/use-auth';
import { ROUTES } from '@/lib/utils/constants';

export interface AuthGuardProps {
  /** Child components to render if authenticated */
  children: ReactNode;
  /** Fallback component while loading */
  fallback?: ReactNode;
}

/**
 * Default loading fallback
 */
function LoadingFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
    </div>
  );
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const location = useLocation();
  const { isAuthenticated, isInitialized, isLoading } = useAuth();

  // Show loading state while initializing
  if (!isInitialized || isLoading) {
    return <>{fallback || <LoadingFallback />}</>;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate
        to={ROUTES.LOGIN}
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  return <>{children}</>;
}
