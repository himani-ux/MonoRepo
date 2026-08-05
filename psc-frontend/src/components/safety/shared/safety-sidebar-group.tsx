import { Link } from "react-router-dom";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";

interface SafetySidebarGroupProps {
  counts?: {
    incidents?: number;
    findings?: number;
    nearMiss?: number;
  };
}

interface SidebarItemConfig {
  badgeCount?: number;
  formId: string;
  href: string;
  label: string;
}

function SidebarBadge({ count }: { count?: number }) {
  if (!count) {
    return null;
  }

  return (
    <span
      aria-label={`${count} pending`}
      className="rounded-full border border-slate-300 px-2 py-0.5 text-xs font-medium"
    >
      {count}
    </span>
  );
}

export function SafetySidebarGroup({
  counts = {},
}: SafetySidebarGroupProps) {
  const auth = useSafetyAuth();

  if (!auth.hasAnySafetyAccess()) {
    return null;
  }

  const items: SidebarItemConfig[] = [
    {
      badgeCount: counts.incidents,
      formId: "SAF_F_001",
      href: "/safety/incidents",
      label: "Incidents",
    },
    {
      badgeCount: counts.nearMiss,
      formId: "SAF_F_002",
      href: "/safety/near-miss",
      label: "Near Miss",
    },
    {
      formId: "SAF_F_003",
      href: "/safety/scm",
      label: "Committee Meetings",
    },
    {
      badgeCount: counts.findings,
      formId: "SAF_F_004",
      href: "/safety/soi",
      label: "Safety Officer Inspection",
    },
    {
      formId: "SAF_F_013",
      href: "/safety/soi",
      label: "SOI Applicability",
    },
    {
      formId: "SAF_F_015",
      href: "/safety/dashboard",
      label: "Dashboard",
    },
    {
      formId: "SAF_F_005",
      href: "/safety/search",
      label: "Search",
    },
    {
      formId: "SAF_F_020",
      href: "/safety/admin/auditor-export",
      label: "Auditor Export",
    },
  ];

  return (
    <nav aria-label="Safety" data-testid="safety-sidebar-group">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Safety
      </div>
      <ul className="space-y-1">
        {items
          .filter((item) => auth.hasForm(item.formId))
          .map((item) => (
            <li key={item.href}>
              <Link
                className="flex min-h-[44px] items-center justify-between rounded-md px-3 py-2 text-sm text-slate-700"
                to={item.href}
              >
                <span>{item.label}</span>
                <SidebarBadge count={item.badgeCount} />
              </Link>
            </li>
          ))}
      </ul>
    </nav>
  );
}
