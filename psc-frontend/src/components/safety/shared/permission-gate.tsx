import type { PropsWithChildren, ReactNode } from "react";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";

interface GateProps extends PropsWithChildren {
  fallback?: ReactNode;
}

interface PermissionGateProps extends GateProps {
  formId: string;
}

interface ProcessGateProps extends GateProps {
  processId: string;
}

interface RoleGateProps extends GateProps {
  roles: string[];
}

function DefaultDeniedFallback({
  detail,
  title,
}: {
  detail: string;
  title: string;
}) {
  return (
    <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">
        Safety Access
      </p>
      <h2 className="mt-2 text-xl font-semibold text-amber-950">{title}</h2>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-amber-900">{detail}</p>
    </section>
  );
}

export function PermissionGate({
  children,
  fallback = (
    <DefaultDeniedFallback
      detail="Your current Safety form permissions do not include this route. Open a route linked to one of your seeded SAF_F_* permissions or update the assigned profile."
      title="Form access is not available for this page."
    />
  ),
  formId,
}: PermissionGateProps) {
  const auth = useSafetyAuth();

  if (!auth.hasForm(formId)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

export function ProcessGate({
  children,
  fallback = (
    <DefaultDeniedFallback
      detail="You can view this Safety area, but the required SAF_P_* process permission for this action is not assigned to your profile."
      title="Process access is not available for this page."
    />
  ),
  processId,
}: ProcessGateProps) {
  const auth = useSafetyAuth();

  if (!auth.hasProcess(processId)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

export function RoleGate({
  children,
  fallback = (
    <DefaultDeniedFallback
      detail="This Safety route is limited to specific vessel or office roles in the current rollout."
      title="Your role cannot open this page."
    />
  ),
  roles,
}: RoleGateProps) {
  const auth = useSafetyAuth();
  const normalizedRole = (auth.role ?? "").trim().toUpperCase();
  const allowedRoles = new Set(roles.map((role) => role.trim().toUpperCase()));

  if (!allowedRoles.has(normalizedRole)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
