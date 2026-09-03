/**
 * Application header component.
 *
 * Features:
 * - App logo/title
 * - Notification badge (unread count)
 * - User menu with logout
 *
 * Per APP_FLOW.md Section 3.1
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, BellRing, ChevronDown, CircleUserRound, LogOut, PanelLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';
import { useUnreadCount } from '@/hooks/use-notifications';
import { ROUTES } from '@/lib/utils/constants';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import { CircularHeaderActions } from './circular-header-actions';
import { OrbHeaderActions } from './orb-header-actions';

export interface HeaderProps {
  /** Toggle sidebar on mobile */
  onMenuClick?: () => void;
  /** Show menu button (mobile only) */
  showMenuButton?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function Header({ onMenuClick, showMenuButton = true, className }: HeaderProps) {
  const navigate = useNavigate();
  const { fullName, role, logout, isVessel, hasProcess } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const { data: unreadCount = 0 } = useUnreadCount();
  const NotificationIcon = unreadCount > 0 ? BellRing : Bell;

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      navigate(ROUTES.LOGIN, { replace: true });
    } catch {
      // Ignore errors, we're logging out anyway
      navigate(ROUTES.LOGIN, { replace: true });
    }
  };

  return (
    <header
      className={cn(
        'sticky top-0 z-40 flex h-14 items-center justify-between border-b border-neutral-200/80 bg-white/95 px-3 shadow-sm backdrop-blur',
        'md:h-16 md:px-5',
        className
      )}
    >
      {/* Left section */}
      <div className="flex min-w-0 items-center gap-2 md:gap-3">
        {showMenuButton && (
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-xl border border-neutral-200 bg-white text-neutral-600 shadow-sm hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700 md:hidden"
            onClick={onMenuClick}
            aria-label="Toggle menu"
          >
            <PanelLeft className="h-5 w-5" />
          </Button>
        )}

        <Link
          to={hasProcess(PROCESS_IDS.VIEW_INSPECTIONS) ? ROUTES.INSPECTIONS : ROUTES.CARS}
          className="group flex min-w-0 items-center gap-3 rounded-xl px-1.5 py-1 transition-colors hover:bg-neutral-50"
          aria-label="VIMS Home"
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-neutral-200 bg-white p-1 shadow-sm ring-1 ring-neutral-100 transition-colors group-hover:border-primary-200">
            <img
              src="/icons/ksm-icon-192x192.png"
              alt=""
              className="h-full w-full object-contain"
              aria-hidden="true"
            />
          </div>
          <div className="hidden min-w-0 leading-tight sm:block" aria-hidden="true">
            <p className="text-base font-semibold text-neutral-900 md:text-lg">VIMS</p>
            <p className="hidden text-xs font-medium text-neutral-500 md:block">
              Vessel Inspection Management System
            </p>
          </div>
        </Link>
      </div>

      {/* Right section */}
      <div className="flex shrink-0 items-center gap-2">
        <CircularHeaderActions />
        <OrbHeaderActions />

        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative h-10 w-10 rounded-full border border-neutral-200 bg-white text-neutral-600 shadow-sm hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700"
          onClick={() => navigate(ROUTES.NOTIFICATIONS)}
          aria-label="Notifications"
        >
          <NotificationIcon className="h-5 w-5" />
          {unreadCount > 0 && (
            <span
              role="status"
              aria-live="polite"
              className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full border-2 border-white bg-red-500 px-1 text-[11px] font-semibold leading-none text-white shadow-sm"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="h-10 gap-2 rounded-full border border-neutral-200 bg-white py-1 pl-1 pr-2 shadow-sm hover:border-primary-200 hover:bg-neutral-50"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-700 ring-1 ring-primary-100">
                <CircleUserRound className="h-4 w-4" />
              </div>
              <div className="hidden min-w-0 text-left md:block">
                <p className="max-w-[10rem] truncate text-sm font-semibold text-neutral-800">
                  {fullName || 'User'}
                </p>
                <p className="max-w-[10rem] truncate text-xs font-medium text-neutral-500">
                  {role || (isVessel ? 'Vessel' : 'Office')}
                </p>
              </div>
              <ChevronDown className="hidden h-4 w-4 text-neutral-400 md:block" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="px-2 py-2 md:hidden">
              <p className="text-sm font-medium text-neutral-800">
                {fullName || 'User'}
              </p>
              <p className="text-xs text-neutral-500">
                {role || (isVessel ? 'Vessel' : 'Office')}
              </p>
            </div>
            <DropdownMenuSeparator className="md:hidden" />
            <DropdownMenuItem
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="text-red-600 focus:bg-red-50 focus:text-red-600"
            >
              <LogOut className="mr-2 h-4 w-4" />
              {isLoggingOut ? 'Signing out...' : 'Sign out'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
