import { AlertTriangle, ClipboardCheck, Eye, FileText, Plus, ShieldCheck, type LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMemo } from 'react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { ErrorState, SectionSkeleton } from '@/components/shared';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuditPlans } from '@/hooks/audit/use-audit-plan';
import { useRegisteredAudits } from '@/hooks/audit/use-audit-registration';
import { useAuth } from '@/hooks/use-auth';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import { formatEnumLabel, getStatusLabel } from '@/lib/utils/format-status';
import type { RegisteredAudit } from '@/lib/api/audit';
import type { AuditPlan } from '@/schemas/audit/plan';

const ACTIVE_STATUSES = new Set(['CONFIRMED', 'IN_PROGRESS']);
const ATTENTION_STATUSES = new Set(['EXTENSION_REQUESTED', 'OVERDUE', 'CRITICAL_OVERDUE']);

export default function AuditDashboardRoute() {
  const { data, isLoading, error, refetch } = useAuditPlans();
  const registeredAuditsQuery = useRegisteredAudits();
  const { hasProcess } = useAuth();
  const plans = data?.results ?? [];
  const registeredAudits = registeredAuditsQuery.data?.results ?? [];
  const summary = useAuditDashboardSummary(plans, data?.count ?? plans.length);
  const upcomingPlans = useMemo(() => plans.slice(0, 6), [plans]);
  const recentRegisteredAudits = useMemo(() => registeredAudits.slice(0, 8), [registeredAudits]);

  const canCreateAudit = hasProcess(PROCESS_IDS.AUDIT_CREATE) || hasProcess(PROCESS_IDS.AUDIT_CONDUCT);
  const canRegisterExternal = hasProcess(PROCESS_IDS.AUDIT_REGISTER_EXTERNAL);
  const canManageQualifiedAuditors = hasProcess(PROCESS_IDS.AUDIT_MANAGE_QUALIFIED_AUDITORS);
  const canViewQueues =
    hasProcess(PROCESS_IDS.AUDIT_NOTIFY) ||
    hasProcess(PROCESS_IDS.AUDIT_APPROVE_EXTENSION) ||
    hasProcess(PROCESS_IDS.AUDIT_CANCEL_PLAN);

  return (
    <RootLayout>
      <div className="space-y-6 p-4 md:p-6">
        <PageHeader
          title="Audit Dashboard"
          subtitle="Current audit plan status and next actions."
          actions={
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline">
                <Link to="/audit/plans">
                  <ClipboardCheck className="mr-2 h-4 w-4" />
                  Audit Plans
                </Link>
              </Button>
              {canCreateAudit || canRegisterExternal ? (
                <Button asChild>
                  <Link to="/audit/register">
                    <Plus className="mr-2 h-4 w-4" />
                    Register Audit
                  </Link>
                </Button>
              ) : null}
            </div>
          }
        />

        {isLoading ? (
          <SectionSkeleton />
        ) : error ? (
          <ErrorState
            title="Unable to load audit dashboard"
            message={error.message || 'Audit plan data could not be loaded.'}
            onRetry={() => refetch()}
          />
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                title="Total Plans"
                value={summary.total}
                caption="All audit plan records."
                icon={FileText}
                tone="neutral"
              />
              <MetricCard
                title="Active"
                value={summary.active}
                caption="Confirmed or in progress."
                icon={ShieldCheck}
                tone="success"
              />
              <MetricCard
                title="Need Attention"
                value={summary.needsAttention}
                caption="Extension requested or overdue."
                icon={AlertTriangle}
                tone="warning"
              />
              <MetricCard
                title="Additional Audits"
                value={summary.additional}
                caption="Added outside routine plan."
                icon={Plus}
                tone="info"
              />
            </section>

            <RegisteredAuditsCard
              audits={recentRegisteredAudits}
              totalCount={registeredAuditsQuery.data?.count ?? registeredAudits.length}
              isLoading={registeredAuditsQuery.isLoading}
              error={registeredAuditsQuery.error}
              onRetry={() => registeredAuditsQuery.refetch()}
            />

            <section className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
              <Card>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle>Upcoming Plans</CardTitle>
                    <p className="mt-1 text-sm text-neutral-500">Latest audit plan rows from the register.</p>
                  </div>
                  <Button asChild variant="outline" size="sm">
                    <Link to="/audit/plans">Open Register</Link>
                  </Button>
                </CardHeader>
                <CardContent>
                  {upcomingPlans.length ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-left text-sm">
                        <thead className="border-b border-neutral-200 text-xs uppercase text-neutral-500">
                          <tr>
                            <th className="py-2 pr-4 font-medium">Target</th>
                            <th className="py-2 pr-4 font-medium">Window</th>
                            <th className="py-2 pr-4 font-medium">Standards</th>
                            <th className="py-2 pr-4 font-medium">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-neutral-100">
                          {upcomingPlans.map((plan) => (
                            <tr key={plan.id}>
                              <td className="py-3 pr-4 font-medium text-neutral-800">{plan.target_label || 'Not set'}</td>
                              <td className="py-3 pr-4 text-neutral-600">{plan.window_label || formatWindow(plan)}</td>
                              <td className="py-3 pr-4 text-neutral-600">{plan.audit_standards_csv || 'Not set'}</td>
                              <td className="py-3 pr-4">
                                <StatusBadge status={plan.status} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-neutral-300 p-6 text-sm text-neutral-500">
                      No audit plans are available yet.
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <p className="text-sm text-neutral-500">Common Audit work areas.</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <QuickAction href="/audit/plans" title="Audit Plan Register" caption="Create, edit, extend, or cancel plan rows." />
                  {canCreateAudit || canRegisterExternal ? (
                    <QuickAction href="/audit/register" title="Register Audit" caption="Choose internal or external audit registration." />
                  ) : null}
                  {canManageQualifiedAuditors ? (
                    <QuickAction href="/audit/masters/qualified-auditors" title="Qualified Auditors" caption="Maintain Lead Auditor qualification rows." />
                  ) : null}
                  {canViewQueues ? (
                    <QuickAction href="/dpa/notifications/failed" title="Failed Notifications" caption="Review audit notifications that need attention." />
                  ) : null}
                  <QuickAction href="/dpa/scan-validation-queue" title="Scan Validation Queue" caption="Validate signed audit scans when permitted." />
                </CardContent>
              </Card>
            </section>
          </>
        )}
      </div>
    </RootLayout>
  );
}

function RegisteredAuditsCard({
  audits,
  totalCount,
  isLoading,
  error,
  onRetry,
}: {
  audits: RegisteredAudit[];
  totalCount: number;
  isLoading: boolean;
  error: Error | null;
  onRetry: () => void;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Registered Audits</CardTitle>
          <p className="mt-1 text-sm text-neutral-500">
            {totalCount ? `${totalCount} audit${totalCount === 1 ? '' : 's'} available to open.` : 'Open audit records appear here after registration.'}
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/audit/register">
            <Plus className="mr-2 h-4 w-4" />
            Register Audit
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <SectionSkeleton />
        ) : error ? (
          <ErrorState
            title="Unable to load registered audits"
            message={error.message || 'Registered audit records could not be loaded.'}
            onRetry={onRetry}
          />
        ) : audits.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-neutral-200 text-xs uppercase text-neutral-500">
                <tr>
                  <th className="py-2 pr-4 font-medium">Target</th>
                  <th className="py-2 pr-4 font-medium">Audit Period</th>
                  <th className="py-2 pr-4 font-medium">Type</th>
                  <th className="py-2 pr-4 font-medium">Lead Auditor</th>
                  <th className="py-2 pr-4 font-medium">Status</th>
                  <th className="py-2 text-right font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {audits.map((audit) => (
                  <tr key={audit.id}>
                    <td className="py-3 pr-4 font-medium text-neutral-800">{audit.target_label || 'Not set'}</td>
                    <td className="py-3 pr-4 text-neutral-600">{formatDateRange(audit.audit_start_date, audit.audit_end_date)}</td>
                    <td className="py-3 pr-4 text-neutral-600">{formatAuditType(audit)}</td>
                    <td className="py-3 pr-4 text-neutral-600">{audit.lead_auditor_name || 'Not set'}</td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={audit.status} />
                    </td>
                    <td className="py-3 text-right">
                      <Button asChild variant="outline" size="sm">
                        <Link to={registeredAuditOpenPath(audit)}>
                          <Eye className="mr-2 h-4 w-4" />
                          Open
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-neutral-300 p-6 text-sm text-neutral-500">
            No registered audits are available yet.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function useAuditDashboardSummary(plans: AuditPlan[], totalCount: number) {
  return useMemo(
    () => ({
      total: totalCount,
      active: plans.filter((plan) => ACTIVE_STATUSES.has(String(plan.status).toUpperCase())).length,
      needsAttention: plans.filter((plan) => ATTENTION_STATUSES.has(String(plan.status).toUpperCase())).length,
      additional: plans.filter((plan) => plan.is_additional).length,
    }),
    [plans, totalCount]
  );
}

function formatWindow(plan: AuditPlan) {
  const start = plan.planned_window_start || 'Not set';
  const end = plan.extended_due_date || plan.planned_window_end || 'Not set';
  return `${start} -> ${end}`;
}

function formatDateRange(start: string, end: string | null) {
  return `${formatDate(start)} -> ${formatDate(end)}`;
}

function formatDate(value: string | null) {
  if (!value) {
    return 'Not set';
  }
  return value;
}

function formatAuditType(audit: RegisteredAudit) {
  const classification = formatEnumLabel(audit.audit_classification);
  const subtype = formatEnumLabel(audit.audit_subtype);
  return [classification, subtype].filter(Boolean).join(' / ') || 'Not set';
}

function registeredAuditOpenPath(audit: RegisteredAudit) {
  return String(audit.audit_classification || '').toUpperCase() === 'EXTERNAL'
    ? `/audit/external/${audit.id}`
    : `/audit/audits/${audit.id}`;
}

function StatusBadge({ status }: { status: string }) {
  const normalized = String(status || '').toUpperCase();
  const variant = ATTENTION_STATUSES.has(normalized) ? 'warning' : ACTIVE_STATUSES.has(normalized) ? 'success' : 'secondary';
  return <Badge variant={variant}>{getStatusLabel(normalized || 'UNKNOWN')}</Badge>;
}

function MetricCard({
  title,
  value,
  caption,
  icon: Icon,
  tone,
}: {
  title: string;
  value: number;
  caption: string;
  icon: LucideIcon;
  tone: 'neutral' | 'success' | 'warning' | 'info';
}) {
  const toneClass = {
    neutral: 'bg-neutral-50 text-neutral-700',
    success: 'bg-success-100 text-success-700',
    warning: 'bg-warning-100 text-warning-700',
    info: 'bg-info-100 text-info-700',
  }[tone];

  return (
    <Card>
      <CardContent className="flex items-start justify-between gap-4 p-4">
        <div>
          <p className="text-sm font-medium text-neutral-500">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-neutral-900">{value}</p>
          <p className="mt-1 text-xs text-neutral-500">{caption}</p>
        </div>
        <div className={`rounded-lg p-2 ${toneClass}`}>
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

function QuickAction({ href, title, caption }: { href: string; title: string; caption: string }) {
  return (
    <Link
      to={href}
      className="block rounded-lg border border-neutral-200 p-3 transition-colors hover:border-primary-300 hover:bg-primary-50"
    >
      <p className="text-sm font-medium text-neutral-800">{title}</p>
      <p className="mt-1 text-xs text-neutral-500">{caption}</p>
    </Link>
  );
}
