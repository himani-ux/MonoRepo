import { useState } from "react";

import { ProcessGate } from "../shared/permission-gate";

interface SafetyReopenIncidentModalProps {
  authorityLabel: string;
  incidentId: string;
  onConfirm?: (reason: string) => void;
  open?: boolean;
  riskBand: "GREEN" | "YELLOW" | "RED";
}

export function SafetyReopenIncidentModal({
  authorityLabel,
  incidentId,
  onConfirm,
  open = true,
  riskBand,
}: SafetyReopenIncidentModalProps) {
  const [reason, setReason] = useState("");

  if (!open) {
    return null;
  }

  return (
    <ProcessGate processId="SAF_P_008">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Incident {incidentId}
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-900">
              Re-open Closed Incident
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Re-open sends the incident back to Phase 5 so new evidence can be
              analysed without losing the closure audit trail.
            </p>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <div>Risk band: {riskBand}</div>
            <div>Required closer: {authorityLabel}</div>
          </div>
        </div>

        <label className="mt-6 block space-y-2 text-sm text-slate-700">
          <span className="font-medium">Reason for re-open</span>
          <textarea
            className="min-h-[140px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
            onChange={(event) => setReason(event.target.value)}
            placeholder="Describe the new evidence or closure gap."
            value={reason}
          />
        </label>

        <div className="mt-5 flex flex-col gap-3 lg:flex-row lg:justify-end">
          <button
            className="min-h-[44px] rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={reason.trim().length === 0}
            onClick={() => onConfirm?.(reason.trim())}
            type="button"
          >
            Re-open to Phase 5
          </button>
        </div>
      </section>
    </ProcessGate>
  );
}

export default SafetyReopenIncidentModal;
