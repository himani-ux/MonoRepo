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
  ShieldCheck,
  ClipboardList,
  ClipboardCheck,
  ListChecks,
  Bell,
  RefreshCw,
  Settings,
  BarChart3,
  LayoutDashboard,
  ShipWheel,
  TriangleAlert,
  Search,
  UsersRound,
  FileBarChart2,
  BookText,
  BookOpenCheck,
  FileCheck2,
  X,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';
import { useUnreadCount } from '@/hooks/use-notifications';
import { getCertsHomeRoute } from '@/lib/certs/navigation';
import { ROUTES } from '@/lib/utils/constants';
import { FORM_IDS, PROCESS_IDS } from '@/lib/utils/permission-ids';
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

interface SafetyNavItem {
  formId: string;
  href: string;
  label: string;
  icon: typeof Ship;
}

interface AuditNavItem {
  href: string;
  label: string;
  processIds: string[];
  icon: typeof Ship;
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

const safetyNavItems: SafetyNavItem[] = [
  { formId: 'SAF_F_015', href: '/safety/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { formId: 'SAF_F_001', href: '/safety/incidents', label: 'Incidents', icon: TriangleAlert },
  { formId: 'SAF_F_002', href: '/safety/near-miss', label: 'Near Miss', icon: Search },
  { formId: 'SAF_F_003', href: '/safety/scm', label: 'Committee Meetings', icon: UsersRound },
  { formId: 'SAF_F_004', href: '/safety/soi', label: 'Safety Officer Inspection', icon: ClipboardCheck },
  { formId: 'SAF_F_013', href: '/safety/soi', label: 'SOI Applicability', icon: ListChecks },
  { formId: 'SAF_F_005', href: '/safety/search', label: 'Search', icon: Search },
  { formId: 'SAF_F_020', href: '/safety/admin/auditor-export', label: 'Auditor Export', icon: FileBarChart2 },
];

const auditNavItems: AuditNavItem[] = [
  {
    href: '/audit/dashboard',
    label: 'Audit Dashboard',
    processIds: [
      PROCESS_IDS.AUDIT_CREATE,
      PROCESS_IDS.AUDIT_EDIT,
      PROCESS_IDS.AUDIT_CONDUCT,
      PROCESS_IDS.AUDIT_CLOSE_NC,
      PROCESS_IDS.AUDIT_APPROVE_EXTENSION,
      PROCESS_IDS.AUDIT_CANCEL_PLAN,
      PROCESS_IDS.AUDIT_REGISTER_EXTERNAL,
      PROCESS_IDS.AUDIT_ACTING_HOD_AUTHORIZE,
      PROCESS_IDS.AUDIT_ACKNOWLEDGE_REPORT,
      PROCESS_IDS.AUDIT_SCAN_VALIDATION,
    ],
    icon: LayoutDashboard,
  },
  {
    href: '/audit/plans',
    label: 'Audit Plans',
    processIds: [PROCESS_IDS.AUDIT_CREATE, PROCESS_IDS.AUDIT_EDIT, PROCESS_IDS.AUDIT_CONDUCT],
    icon: ClipboardList,
  },
  {
    href: ROUTES.INSPECTION_NEW,
    label: 'Register Audit',
    processIds: [PROCESS_IDS.AUDIT_CREATE, PROCESS_IDS.AUDIT_CONDUCT],
    icon: ClipboardCheck,
  },
  {
    href: '/audit/external/new',
    label: 'External Audit',
    processIds: [PROCESS_IDS.AUDIT_REGISTER_EXTERNAL],
    icon: ShipWheel,
  },
  {
    href: '/dpa/notifications/failed',
    label: 'Failed Notifications',
    processIds: [
      PROCESS_IDS.AUDIT_CREATE,
      PROCESS_IDS.AUDIT_APPROVE_EXTENSION,
      PROCESS_IDS.AUDIT_CANCEL_PLAN,
    ],
    icon: Bell,
  },
  {
    href: '/dpa/scan-validation-queue',
    label: 'Scan Validation Queue',
    processIds: [PROCESS_IDS.AUDIT_SCAN_VALIDATION],
    icon: FileCheck2,
  },
];

const certsFormIds = [
  FORM_IDS.CERTS_CATALOG,
  FORM_IDS.CERTS_TRACKED_ITEMS,
  FORM_IDS.CERTS_RECONCILIATION,
  FORM_IDS.CERTS_PRINT_EXPORT,
  FORM_IDS.CERTS_ONBOARDING,
  FORM_IDS.CERTS_NOTIFICATION_CONFIG,
  FORM_IDS.CERTS_AUDITOR_ACCESS,
  FORM_IDS.CERTS_AUDIT_LOG,
] as const;

const navItemBase =
  'group flex w-full items-center gap-3 whitespace-nowrap rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150';
const navItemActive = 'bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-100';
const navItemIdle = 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 hover:shadow-sm';
const nestedListClass = 'mt-1 space-y-1 border-l border-neutral-100 pl-2';

function navItemClass(active: boolean) {
  return cn(navItemBase, active ? navItemActive : navItemIdle);
}

function navIconClass(active: boolean) {
  return cn(
    'h-5 w-5 shrink-0 transition-colors duration-150',
    active ? 'text-primary-600' : 'text-neutral-500 group-hover:text-neutral-700'
  );
}

function chevronClass(active: boolean) {
  return cn(
    'h-4 w-4 shrink-0 transition-colors duration-150',
    active ? 'text-primary-500' : 'text-neutral-400 group-hover:text-neutral-600'
  );
}

export function Sidebar({ isOpen, onClose, className }: SidebarProps) {
  const location = useLocation();
  const { hasForm, hasProcess = () => false, user, isVessel, vesselId } = useAuth();
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
  const visibleAuditItems = auditNavItems.filter((item) => (
    item.processIds.some((processId) => hasProcess(processId))
  ));
  const visibleSafetyItems = safetyNavItems.filter((item) => hasForm(item.formId));

  const hasActivePscItem = orderedNavItems.some((item) => isActive(item.href));
  const hasAuditAccess = visibleAuditItems.length > 0;
  const hasActiveAuditItem = (
    location.pathname.startsWith('/audit') ||
    location.pathname === ROUTES.INSPECTION_NEW ||
    location.pathname === '/dpa/notifications/failed' ||
    location.pathname === '/dpa/scan-validation-queue'
  );
  const hasSafetyAccess = visibleSafetyItems.length > 0;
  const hasActiveSafetyItem = location.pathname.startsWith('/safety');
  const hasActiveInspectionItem = hasActivePscItem || hasActiveAuditItem || hasActiveSafetyItem;
  const hasCertsAccess = certsFormIds.some((formId) => hasForm(formId));
  const certsHref = getCertsHomeRoute({ user, vesselId, hasForm });
  const legacyModuleItems = [
    {
      label: 'Certs',
      href: certsHref,
      icon: FileCheck2,
      visible: hasCertsAccess,
    },
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
  const [inspectionOpen, setInspectionOpen] = useState(hasActiveInspectionItem);
  const [pscOpen, setPscOpen] = useState(hasActivePscItem);
  const [auditOpen, setAuditOpen] = useState(hasActiveAuditItem);
  const [safetyOpen, setSafetyOpen] = useState(hasActiveSafetyItem);

  useEffect(() => {
    setInspectionOpen(hasActiveInspectionItem);
    setPscOpen(hasActivePscItem);
    setAuditOpen(hasActiveAuditItem);
    setSafetyOpen(hasActiveSafetyItem);
  }, [hasActiveAuditItem, hasActiveInspectionItem, hasActivePscItem, hasActiveSafetyItem]);

  const handleInspectionToggle = () => {
    setInspectionOpen((open) => {
      if (open) {
        setPscOpen(false);
        return false;
      }

      return true;
    });
  };

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
          'fixed left-0 top-0 z-50 flex h-full min-h-0 w-80 shrink-0 flex-col bg-white shadow-lg transition-transform duration-300',
          'md:relative md:z-0 md:h-full md:translate-x-0 md:shadow-none md:border-r md:border-neutral-200',
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
        <nav
          aria-label="Main navigation"
          className="min-h-0 flex-1 overflow-x-auto overflow-y-auto px-3 py-4 pr-2 [scrollbar-gutter:stable] [scrollbar-width:thin]"
        >
          <ul className="w-max min-w-full space-y-1.5">
            <li>
              {/* New hierarchy: Inspection -> PSC -> existing sidebar destinations. */}
              <button
                type="button"
                onClick={handleInspectionToggle}
                aria-expanded={inspectionOpen}
                className={navItemClass(hasActivePscItem || inspectionOpen)}
              >
                <Ship
                  aria-hidden="true"
                  className={navIconClass(hasActivePscItem || inspectionOpen)}
                />
                <span className="min-w-max flex-1 text-left">Inspection</span>
                {inspectionOpen ? (
                  <ChevronDown className={chevronClass(hasActivePscItem || inspectionOpen)} />
                ) : (
                  <ChevronRight className={chevronClass(hasActivePscItem || inspectionOpen)} />
                )}
              </button>

              {inspectionOpen && (
                <ul className={cn(nestedListClass, 'ml-4')}>
                  <li>
                    <button
                      type="button"
                      onClick={() => setPscOpen((open) => !open)}
                      aria-expanded={pscOpen}
                      className={navItemClass(hasActivePscItem || pscOpen)}
                    >
                      <ShipWheel
                        aria-hidden="true"
                        className={navIconClass(hasActivePscItem || pscOpen)}
                      />
                      <span className="min-w-max flex-1 text-left">PSC</span>
                      {pscOpen ? (
                        <ChevronDown className={chevronClass(hasActivePscItem || pscOpen)} />
                      ) : (
                        <ChevronRight className={chevronClass(hasActivePscItem || pscOpen)} />
                      )}
                    </button>

                    {pscOpen && (
                      <ul className={cn(nestedListClass, 'ml-4')}>
                        {orderedNavItems.map((item) => {
                          const Icon = item.icon;
                          const active = isActive(item.href);

                          return (
                            <li key={item.href}>
                              <NavLink
                                to={item.href}
                                onClick={onClose}
                                className={navItemClass(active)}
                              >
                                <Icon
                                  aria-hidden="true"
                                  className={navIconClass(active)}
                                />
                                <span className="min-w-max flex-1 text-left">{item.label}</span>
                                {item.href === ROUTES.NOTIFICATIONS && unreadCount > 0 && (
                                  <span className="shrink-0 rounded-full bg-red-500 px-1.5 py-0.5 text-xs font-semibold text-white">
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

                  {hasAuditAccess && (
                    <li>
                      <button
                        type="button"
                        onClick={() => setAuditOpen((open) => !open)}
                        aria-expanded={auditOpen}
                        className={navItemClass(hasActiveAuditItem || auditOpen)}
                      >
                        <ClipboardList
                          aria-hidden="true"
                          className={navIconClass(hasActiveAuditItem || auditOpen)}
                        />
                        <span className="min-w-max flex-1 text-left">Audit</span>
                        {auditOpen ? (
                          <ChevronDown className={chevronClass(hasActiveAuditItem || auditOpen)} />
                        ) : (
                          <ChevronRight className={chevronClass(hasActiveAuditItem || auditOpen)} />
                        )}
                      </button>
                      {auditOpen ? (
                        <ul className={cn(nestedListClass, 'ml-4')}>
                          {visibleAuditItems.map((item) => {
                            const Icon = item.icon;
                            const active = location.pathname === item.href ||
                              (item.href === '/audit/dashboard' && location.pathname === '/audit') ||
                              (item.href === '/audit/plans' && location.pathname.startsWith('/audit/plans')) ||
                              (item.href === '/audit/external/new' && location.pathname.startsWith('/audit/external')) ||
                              (item.href === ROUTES.INSPECTION_NEW && location.pathname === ROUTES.INSPECTION_NEW);

                            return (
                              <li key={`${item.href}-${item.label}`}>
                                <NavLink
                                  to={item.href}
                                  onClick={onClose}
                                  className={navItemClass(active)}
                                >
                                  <Icon aria-hidden="true" className={navIconClass(active)} />
                                  <span className="min-w-max flex-1 text-left">{item.label}</span>
                                </NavLink>
                              </li>
                            );
                          })}
                        </ul>
                      ) : null}
                    </li>
                  )}

                  {hasSafetyAccess && (
                    <li>
                      <button
                        type="button"
                        onClick={() => setSafetyOpen((open) => !open)}
                        aria-expanded={safetyOpen}
                        className={navItemClass(hasActiveSafetyItem || safetyOpen)}
                      >
                        <ShieldCheck
                          aria-hidden="true"
                          className={navIconClass(hasActiveSafetyItem || safetyOpen)}
                        />
                        <span className="min-w-max flex-1 text-left">Safety</span>
                        {safetyOpen ? (
                          <ChevronDown className={chevronClass(hasActiveSafetyItem || safetyOpen)} />
                        ) : (
                          <ChevronRight className={chevronClass(hasActiveSafetyItem || safetyOpen)} />
                        )}
                      </button>
                      {safetyOpen ? (
                        <ul className={cn(nestedListClass, 'ml-4')}>
                          {visibleSafetyItems.map((item) => {
                            const Icon = item.icon;
                            const active = location.pathname.startsWith(item.href);

                            return (
                              <li key={`${item.formId}-${item.label}`}>
                                <NavLink
                                  to={item.href}
                                  onClick={onClose}
                                  className={navItemClass(active)}
                                >
                                  <Icon aria-hidden="true" className={navIconClass(active)} />
                                  <span className="min-w-max flex-1 text-left">{item.label}</span>
                                </NavLink>
                              </li>
                            );
                          })}
                        </ul>
                      ) : null}
                    </li>
                  )}
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
                    className={navItemClass(active)}
                  >
                    <Icon
                      aria-hidden="true"
                      className={navIconClass(active)}
                    />
                    <span className="min-w-max flex-1 text-left">{item.label}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        {/* <div className="border-t border-neutral-200 p-4">
          <p className="text-xs text-neutral-400">VIMS v0.1.0</p>
        </div> */}
      </aside>
    </>
  );
}
