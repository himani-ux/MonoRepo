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
      <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#2563EB] border-t-transparent" />
      </div>
    );
  }

  // If authenticated, show loading while redirecting
  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#2563EB] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#F8FAFC] px-4 py-8 font-sans text-[#0F172A]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#2563EB]/[0.045] blur-3xl" />
        <div className="absolute left-[8%] top-[12%] h-48 w-48 rounded-full border border-[#2563EB]/[0.035] bg-white/30 blur-sm" />
        <div className="absolute bottom-[11%] right-[10%] h-56 w-56 rounded-full bg-[#4F8EF7]/[0.04] blur-2xl" />
        <div className="absolute inset-x-0 top-24 h-32 opacity-[0.035]">
          <svg className="h-full w-full" viewBox="0 0 1440 180" fill="none" aria-hidden="true">
            <path d="M-40 95C140 35 260 35 440 95C620 155 780 155 960 95C1140 35 1280 35 1480 95" stroke="#2563EB" strokeWidth="1.5" />
            <path d="M-40 125C140 65 260 65 440 125C620 185 780 185 960 125C1140 65 1280 65 1480 125" stroke="#0F172A" strokeWidth="1" />
          </svg>
        </div>
        <div className="absolute right-[12%] top-[18%] h-40 w-40 opacity-[0.045] [background-image:radial-gradient(#2563EB_1px,transparent_1px)] [background-size:14px_14px]" />
        <div className="absolute bottom-[15%] left-[14%] h-32 w-48 rounded-full border border-[#0F172A]/[0.035]" />
      </div>
      <div className="relative z-10 flex w-full flex-col items-center motion-safe:animate-[loginFade_520ms_ease-out]">
      {/* Logo and Title */}
      <div className="mb-8 flex flex-col items-center text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-[18px] border border-[#DBEAFE] bg-gradient-to-br from-[#4F8EF7] to-[#2563EB] text-white shadow-[0_18px_36px_rgba(37,99,235,0.24)]">
          <Ship className="h-8 w-8" aria-hidden="true" />
        </div>
        <h1 className="mt-5 text-3xl font-bold tracking-tight text-[#0F172A]">
          VIMS 
        </h1>
        <p className="mt-2 text-sm font-medium text-[#64748B]">
          PSC / RS / Audit Close-out System
        </p>
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-[450px] rounded-[20px] border border-[#E2E8F0] bg-[#FFFFFF] shadow-[0_28px_90px_rgba(15,23,42,0.13),0_8px_24px_rgba(15,23,42,0.06)] transition-shadow duration-300">
        <CardHeader className="space-y-1 px-10 pb-5 pt-10">
          <h2 className="text-center text-xl font-semibold tracking-tight text-[#0F172A]">
            Sign in to your account
          </h2>
        </CardHeader>
        <CardContent className="px-10 pb-10">
          <LoginForm onSuccess={handleLoginSuccess} />
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-10 text-center text-xs font-medium text-[#94A3B8]">
        &copy; {new Date().getFullYear()} KSM. All rights reserved.
      </p>
      </div>
    </div>
  );
}

export default LoginPage;
