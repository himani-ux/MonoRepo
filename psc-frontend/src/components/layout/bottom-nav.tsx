/**
 * Mobile bottom navigation component.
 *
 * Features:
 * - Fixed bottom navigation bar
 * - 4-5 primary navigation items
 * - Active state highlighting
 * - Only visible on mobile
 *
 * Per APP_FLOW.md Section 3.1
 */

import { NavLink, useLocation } from 'react-router-dom';
import { Ship, ClipboardList, ListChecks, Bell, RefreshCw, Settings, LayoutDashboard } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';
import { ROUTES } from '@/lib/utils/constants';
import { FORM_IDS } from '@/lib/utils/permission-ids';

interface NavItem {
  label: string;
  href: string;
  icon: typeof Ship;
  formId?: string;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: ROUTES.DASHBOARD,
    icon: LayoutDashboard,
    formId: FORM_IDS.DASHBOARD,
  },
  {
    label: 'Inspections',
    href: ROUTES.INSPECTIONS,
    icon: Ship,
    formId: FORM_IDS.INSPECTIONS,
  },
  {
    label: 'Deficiencies',
    href: ROUTES.DEFICIENCIES,
    icon: ListChecks,
    formId: FORM_IDS.DEFICIENCIES,
  },
  {
    label: 'CARs',
    href: ROUTES.CARS,
    icon: ClipboardList,
    formId: FORM_IDS.CARS,
  },
  {
    label: 'Notifications',
    href: ROUTES.NOTIFICATIONS,
    icon: Bell,
    formId: FORM_IDS.NOTIFICATIONS,
  },
  {
    label: 'Sync',
    href: ROUTES.SYNC,
    icon: RefreshCw,
    formId: FORM_IDS.SYNC,
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: Settings,
    formId: FORM_IDS.SETTINGS,
  },
];

export function BottomNav() {
  const location = useLocation();
  const { hasForm } = useAuth();

  // Filter nav items based on permissions
  const filteredNavItems = navItems.filter((item) => {
    if (item.formId && !hasForm(item.formId)) return false;
    return true;
  });
  const isActive = (href: string) => {
    if (href === ROUTES.DASHBOARD) {
      return location.pathname === '/' || location.pathname === '/dashboard';
    }
    if (href === ROUTES.INSPECTIONS) {
      return location.pathname.startsWith('/inspections');
    }
    if (href === ROUTES.DEFICIENCIES) {
      return location.pathname.startsWith('/deficiencies');
    }
    if (href === ROUTES.CARS) {
      return location.pathname.startsWith('/cars');
    }
    return location.pathname === href;
  };

  return (
    <nav aria-label="Main navigation" className="fixed bottom-0 left-0 right-0 z-40 border-t border-neutral-200 bg-white md:hidden">
      <ul className="flex h-16 items-center justify-around">
        {filteredNavItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);

          return (
            <li key={item.href} className="flex-1">
              <NavLink
                to={item.href}
                className={cn(
                  'flex flex-col items-center justify-center gap-1 py-2 transition-colors',
                  active ? 'text-primary-600' : 'text-neutral-500'
                )}
              >
                <Icon className="h-5 w-5" />
                <span
                  className={cn(
                    'text-[10px]',
                    active ? 'font-medium' : 'font-normal'
                  )}
                >
                  {item.label}
                </span>
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
