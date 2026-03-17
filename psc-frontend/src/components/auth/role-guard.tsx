/**
 * Role-based access guard component.
 *
 * Restricts access based on user roles.
 * Shows access denied message if user doesn't have required role.
 *
 * Per IMPLEMENTATION_PLAN.md Step 2.5
 */

import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ShieldX } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';
import { ROUTES } from '@/lib/utils/constants';
import type { UserRole } from '@/types';

export interface RoleGuardProps {
  /** Child components to render if role check passes */
  children: ReactNode;
  /** Required role(s) - user must have at least one of these */
  allowedRoles: UserRole[];
  /** Allow vessel users */
  allowVessel?: boolean;
  /** Allow office users */
  allowOffice?: boolean;
  /** Custom fallback for access denied */
  fallback?: ReactNode;
}

/**
 * Default access denied component
 */
function AccessDenied() {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center gap-4 p-8">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
        <ShieldX className="h-8 w-8 text-red-600" />
      </div>
      <h2 className="text-xl font-semibold text-neutral-800">Access Denied</h2>
      <p className="max-w-md text-center text-neutral-500">
        You do not have permission to access this page. Please contact your
        administrator if you believe this is an error.
      </p>
      <Link
        to={ROUTES.INSPECTIONS}
        className="mt-4 text-primary-500 hover:text-primary-600 hover:underline"
      >
        Return to Inspections
      </Link>
    </div>
  );
}

export function RoleGuard({
  children,
  allowedRoles,
  allowVessel,
  allowOffice,
  fallback,
}: RoleGuardProps) {
  const { role, isVessel, isOffice } = useAuth();

  // Check vessel/office type first
  if (allowVessel !== undefined || allowOffice !== undefined) {
    const vesselAllowed = allowVessel && isVessel;
    const officeAllowed = allowOffice && isOffice;

    if (!vesselAllowed && !officeAllowed) {
      return <>{fallback || <AccessDenied />}</>;
    }
  }

  // Check specific roles if provided
  if (allowedRoles.length > 0) {
    if (!role || !allowedRoles.includes(role)) {
      return <>{fallback || <AccessDenied />}</>;
    }
  }

  return <>{children}</>;
}

/**
 * Guard that only allows vessel users
 */
export function VesselOnlyGuard({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { isVessel } = useAuth();

  if (!isVessel) {
    return <>{fallback || <AccessDenied />}</>;
  }

  return <>{children}</>;
}

/**
 * Guard that only allows office users
 */
export function OfficeOnlyGuard({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { isOffice } = useAuth();

  if (!isOffice) {
    return <>{fallback || <AccessDenied />}</>;
  }

  return <>{children}</>;
}

/**
 * Guard that only allows DPA users
 */
export function DPAOnlyGuard({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { isDPA } = useAuth();

  if (!isDPA) {
    return <>{fallback || <AccessDenied />}</>;
  }

  return <>{children}</>;
}

/**
 * Guard that only allows PIC-level users (PIC, SSQE, Supt, DPA)
 */
export function PICGuard({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { isPIC } = useAuth();

  if (!isPIC) {
    return <>{fallback || <AccessDenied />}</>;
  }

  return <>{children}</>;
}
