import { AlertTriangle, ClipboardCheck, FileText, Plus, ShieldCheck, type LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMemo } from 'react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { ErrorState, SectionSkeleton } from '@/components/shared';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuditPlans } from '@/hooks/audit/use-audit-plan';
import { useAuth } from '@/hooks/use-auth';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import type { AuditPlan } from '@/schemas/audit/plan';

const ACTIVE_STATUSES = new Set(['CONFIRMED', 'IN_PROGRESS']);
const ATTENTION_STATUSES = new Set(['EXTENSION_REQUESTED', 'OVERDUE', 'CRITICAL_OVERDUE']);

export default function AuditDashboardRoute() {
  const { data, isLoading, error, refetch } = useAuditPlans();
  const { hasProcess } = useAuth();
  const plans = data?.results ?? [];
  const summary = useAuditDashboardSummary(plans, data?.count ?? plans.length);
  const upcomingPlans = useMemo(() => plans.slice(0, 6), [plans]);

  const canCreateAudit = hasProcess(PROCESS_IDS.AUDIT_CREATE) || hasProcess(PROCESS_IDS.AUDIT_CONDUCT);
  const canRegisterExternal = hasProcess(PROCESS_IDS.AUDIT_REGISTER_EXTERNAL);
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
              {canCreateAudit ? (
                <Button asChild>
                  <Link to="/inspections/new">
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
                  {canRegisterExternal ? (
                    <QuickAction href="/audit/external/new" title="External Audit Registration" caption="Register vessel-side external audit records." />
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

function StatusBadge({ status }: { status: string }) {
  const normalized = String(status || '').toUpperCase();
  const variant = ATTENTION_STATUSES.has(normalized) ? 'warning' : ACTIVE_STATUSES.has(normalized) ? 'success' : 'secondary';
  return <Badge variant={variant}>{normalized || 'UNKNOWN'}</Badge>;
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
