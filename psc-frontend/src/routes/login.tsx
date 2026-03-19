/**
 * Login page route.
 *
 * Screen: Login (`/login`) per APP_FLOW.md Section 2.1
 *
 * Layout:
 * - Centered card with company logo
 * - Login form with username/password
 * - Redirects to /dashboard on success
 */

import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Ship } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { LoginForm } from '@/components/auth/login-form';
import { useAuth } from '@/hooks/use-auth';
import { ROUTES } from '@/lib/utils/constants';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isInitialized } = useAuth();

  // Get the redirect path from location state, or default to dashboard
  const from = (location.state as { from?: string })?.from || ROUTES.DASHBOARD;

  // Redirect if already authenticated
  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isInitialized, navigate, from]);

  const handleLoginSuccess = () => {
    navigate(from, { replace: true });
  };

  // Don't render until auth is initialized
  if (!isInitialized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  // If authenticated, show loading while redirecting
  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 px-4 py-8">
      {/* Logo and Title */}
      <div className="mb-8 flex flex-col items-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-500 text-white">
          <Ship className="h-8 w-8" />
        </div>
        <h1 className="mt-4 text-2xl font-semibold text-neutral-800">
          VIMS 
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          PSC / RS / Audit Close-out System
        </p>
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 pb-4">
          <h2 className="text-center text-xl font-semibold text-neutral-800">
            Sign in to your account
          </h2>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={handleLoginSuccess} />
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-8 text-center text-xs text-neutral-400">
        &copy; {new Date().getFullYear()} KSM. All rights reserved.
      </p>
    </div>
  );
}

export default LoginPage;
