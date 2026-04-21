/**
 * Desktop sidebar navigation component.
 *
 * Features:
 * - Navigation items based on user role
 * - Active state highlighting
 * - Collapsible on smaller screens
 *
 * Per APP_FLOW.md Section 3.1
 */

import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Ship,
  ClipboardList,
  ListChecks,
  Bell,
  RefreshCw,
  Settings,
  BarChart3,
  LayoutDashboard,
  BookText,
  BookOpenCheck,
  X,
  ChevronDown,
  ChevronRight,
  LifeBuoy,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';
import { useUnreadCount } from '@/hooks/use-notifications';
import { ROUTES } from '@/lib/utils/constants';
import { FORM_IDS } from '@/lib/utils/permission-ids';
import { Button } from '@/components/ui/button';

export interface SidebarProps {
  /** Whether sidebar is open on mobile */
  isOpen?: boolean;
  /** Close sidebar handler for mobile */
  onClose?: () => void;
  /** Additional CSS classes */
  className?: string;
}

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
    label: 'Reports',
    href: '/reports',
    icon: BarChart3,
    formId: FORM_IDS.REPORTS,
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: Settings,
    formId: FORM_IDS.SETTINGS,
  },
];

const pscPriorityOrder = [
  ROUTES.DASHBOARD,
  ROUTES.INSPECTIONS,
  ROUTES.CARS,
  '/reports',
  ROUTES.NOTIFICATIONS,
  '/settings',
] as const;

export function Sidebar({ isOpen, onClose, className }: SidebarProps) {
  const location = useLocation();
  const { hasForm, user, isVessel } = useAuth();
  const { data: unreadCount = 0 } = useUnreadCount();

  // Filter nav items based on user role
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

  // Preserve the requested PSC order first, then keep any existing sidebar links
  // under the same dropdown so current navigation functionality is not lost.
  const orderedNavItems = [
    ...pscPriorityOrder
      .map((href) => filteredNavItems.find((item) => item.href === href))
      .filter((item): item is NavItem => Boolean(item)),
    ...filteredNavItems.filter((item) => !pscPriorityOrder.includes(item.href as (typeof pscPriorityOrder)[number])),
  ];

  const hasActivePscItem = orderedNavItems.some((item) => isActive(item.href));
  const legacyModuleItems = [
    {
      label: 'Circular',
      href: ROUTES.CIRCULAR,
      icon: BookText,
      visible: Boolean(user),
    },
    {
      label: 'ORB',
      href: ROUTES.ORB,
      icon: BookOpenCheck,
      visible: isVessel,
    },
  ].filter((item) => item.visible);
  const [inspectionOpen, setInspectionOpen] = useState(hasActivePscItem);
  const [pscOpen, setPscOpen] = useState(hasActivePscItem);

  useEffect(() => {
    setInspectionOpen(hasActivePscItem);
    setPscOpen(hasActivePscItem);
  }, [hasActivePscItem]);

  const handleInspectionToggle = () => {
    setInspectionOpen((open) => {
      if (open) {
        setPscOpen(false);
        return false;
      }

      return true;
    });
  };

  const helpActive = isActive(ROUTES.HELP);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-full w-64 shrink-0 flex-col bg-white shadow-lg transition-transform duration-300',
          'md:relative md:z-0 md:h-auto md:translate-x-0 md:shadow-none md:border-r md:border-neutral-200',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          className
        )}
      >
        {/* Mobile header */}
        <div className="flex h-14 items-center justify-between border-b border-neutral-200 px-4 md:hidden">
          <span className="text-lg font-semibold text-neutral-800">Menu</span>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4">
          <ul className="space-y-1">
            <li>
              {/* New hierarchy: Inspection -> PSC -> existing sidebar destinations. */}
              <button
                type="button"
                onClick={handleInspectionToggle}
                aria-expanded={inspectionOpen}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  hasActivePscItem || inspectionOpen
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                )}
              >
                <Ship
                  className={cn(
                    'h-5 w-5',
                    hasActivePscItem || inspectionOpen ? 'text-primary-600' : 'text-neutral-500'
                  )}
                />
                <span className="flex-1 text-left">Inspection</span>
                {inspectionOpen ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>

              {inspectionOpen && (
                <ul className="mt-1 space-y-1 pl-3">
                  <li>
                    <button
                      type="button"
                      onClick={() => setPscOpen((open) => !open)}
                      aria-expanded={pscOpen}
                      className={cn(
                        'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                        hasActivePscItem || pscOpen
                          ? 'bg-primary-50/70 text-primary-700'
                          : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                      )}
                    >
                      <span className="flex-1 text-left">PSC</span>
                      {pscOpen ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </button>

                    {pscOpen && (
                      <ul className="mt-1 space-y-1 pl-3">
                        {orderedNavItems.map((item) => {
                          const Icon = item.icon;
                          const active = isActive(item.href);

                          return (
                            <li key={item.href}>
                              <NavLink
                                to={item.href}
                                onClick={onClose}
                                className={cn(
                                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                                  active
                                    ? 'bg-primary-50 text-primary-700'
                                    : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                                )}
                              >
                                <Icon
                                  className={cn(
                                    'h-5 w-5',
                                    active ? 'text-primary-600' : 'text-neutral-500'
                                  )}
                                />
                                <span className="flex-1">{item.label}</span>
                                {item.href === ROUTES.NOTIFICATIONS && unreadCount > 0 && (
                                  <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-xs font-semibold text-white">
                                    {unreadCount > 99 ? '99+' : unreadCount}
                                  </span>
                                )}
                              </NavLink>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </li>
                </ul>
              )}
            </li>

            {legacyModuleItems.map((item) => {
              const Icon = item.icon;
              const active = location.pathname.startsWith(item.href);

              return (
                <li key={item.href}>
                  <NavLink
                    to={item.href}
                    onClick={onClose}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      active
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                    )}
                  >
                    <Icon
                      className={cn(
                        'h-5 w-5',
                        active ? 'text-primary-600' : 'text-neutral-500'
                      )}
                    />
                    <span className="flex-1 text-left">{item.label}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="space-y-3 border-t border-neutral-200 p-4">
          <NavLink
            to={ROUTES.HELP}
            onClick={onClose}
            className={cn(
              'flex items-center gap-3 rounded-lg border px-3 py-3 text-sm font-medium transition-colors',
              helpActive
                ? 'border-primary-200 bg-primary-50 text-primary-700'
                : 'border-neutral-200 text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
            )}
          >
            <LifeBuoy
              className={cn(
                'h-5 w-5',
                helpActive ? 'text-primary-600' : 'text-neutral-500'
              )}
            />
            <div className="min-w-0 flex-1">
              <p>Help</p>
              <p className="text-xs font-normal text-neutral-400">
                User guides by module
              </p>
            </div>
          </NavLink>

          <p className="text-xs text-neutral-400">VIMS v0.1.0</p>
        </div>
      </aside>
    </>
  );
}
