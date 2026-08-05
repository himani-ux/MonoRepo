export interface SafetyAuditPhaseLogEntry {
  actorRoleCode: string;
  actorUserId: string;
  occurredAt: string;
  phaseFrom: number;
  phaseTo: number;
  transitionType: string;
}

export interface SafetyAuditFieldHistoryEntry {
  actorRoleCode: string;
  actorUserId: string;
  changedAt: string;
  fieldName: string;
  newValue: string | null;
  oldValue: string | null;
}

interface SafetyAuditTrailPanelProps {
  fieldHistory: SafetyAuditFieldHistoryEntry[];
  incidentNumber: string;
  phaseLog: SafetyAuditPhaseLogEntry[];
}

export function SafetyAuditTrailPanel({
  fieldHistory,
  incidentNumber,
  phaseLog,
}: SafetyAuditTrailPanelProps) {
  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_55%,#dbeafe_100%)] p-6 shadow-sm">
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Incident Audit Trail
        </h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Combined phase-log and field-history review for incident{" "}
          <span className="font-semibold text-slate-900">{incidentNumber}</span>.
        </p>
      </header>

      <div className="grid gap-4 xl:grid-cols-2">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Phase Log</h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
              {phaseLog.length} entries
            </span>
          </div>
          <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Transition</th>
                  <th className="px-4 py-3 font-medium">Actor</th>
                  <th className="px-4 py-3 font-medium">When</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {phaseLog.map((row, index) => (
                  <tr key={`${row.occurredAt}-${index}`}>
                    <td className="px-4 py-4 text-slate-900">
                      P{row.phaseFrom} to P{row.phaseTo} ({row.transitionType})
                    </td>
                    <td className="px-4 py-4 text-slate-600">
                      {row.actorRoleCode} / {row.actorUserId}
                    </td>
                    <td className="px-4 py-4 text-slate-600">{row.occurredAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Field History</h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
              {fieldHistory.length} entries
            </span>
          </div>
          <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Field</th>
                  <th className="px-4 py-3 font-medium">Change</th>
                  <th className="px-4 py-3 font-medium">Actor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {fieldHistory.map((row, index) => (
                  <tr key={`${row.changedAt}-${index}`}>
                    <td className="px-4 py-4 text-slate-900">{row.fieldName}</td>
                    <td className="px-4 py-4 text-slate-600">
                      {row.oldValue ?? "null"} to {row.newValue ?? "null"}
                    </td>
                    <td className="px-4 py-4 text-slate-600">
                      {row.actorRoleCode} / {row.actorUserId}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </section>
  );
}

export default SafetyAuditTrailPanel;
