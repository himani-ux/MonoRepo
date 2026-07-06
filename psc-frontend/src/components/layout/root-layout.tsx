/**
 * Root layout component for authenticated pages.
 *
 * Provides:
 * - Header with navigation
 * - Sidebar (desktop) / Bottom nav (mobile)
 * - Main content area
 * - Auth protection
 *
 * Per APP_FLOW.md Section 3.1 and FRONTEND_GUIDELINES.md
 */

import { useState, ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Header } from './header';
import { Sidebar } from './sidebar';
import { BottomNav } from './bottom-nav';
import { OfflineBanner } from '@/components/sync/offline-banner';
import { SessionReauthGate } from '@/components/auth/session-reauth-gate';
import { useRequireAuth } from '@/hooks/use-auth';
import { useOffline } from '@/hooks/use-offline';

export interface RootLayoutProps {
  /** Page content */
  children: ReactNode;
  /** Hide navigation (for full-screen pages) */
  hideNavigation?: boolean;
  /** Additional CSS classes for main content */
  className?: string;
}

export function RootLayout({
  children,
  hideNavigation = false,
  className,
}: RootLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isLoading } = useRequireAuth();
  const { isOnline, lastSyncTime } = useOffline();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  if (hideNavigation) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <Header showMenuButton={false} />
        <OfflineBanner isOnline={isOnline} lastSyncTime={lastSyncTime} />
        <main className={cn('px-4 py-4 md:px-6', className)}>{children}</main>
        <SessionReauthGate />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-neutral-50">
      {/* Header */}
      <Header onMenuClick={() => setSidebarOpen(true)} />

      {/* Offline indicator banner */}
      <OfflineBanner isOnline={isOnline} lastSyncTime={lastSyncTime} />

      <div className="flex min-h-0 flex-1">
        {/* Desktop sidebar */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* Mobile sidebar (drawer) */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          className="md:hidden"
        />

        {/* Main content */}
        <main
          className={cn(
            'min-w-0 flex-1 overflow-y-auto px-4 pb-20 pt-4 md:pb-6 md:px-6',
            className
          )}
        >
          {children}
        </main>
      </div>

      {/* Mobile bottom navigation */}
      <BottomNav />
      <SessionReauthGate />
    </div>
  );
}
