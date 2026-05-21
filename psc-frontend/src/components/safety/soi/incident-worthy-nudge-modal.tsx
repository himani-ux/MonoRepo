import { useEffect, useState } from "react";

interface SafetyIncidentWorthyNudgeModalProps {
  open: boolean;
  onClose: () => void;
  onCreateIncident: () => void;
  onKeepSoiOnly: (reason: string) => void;
}

export default function SafetyIncidentWorthyNudgeModal({
  open,
  onClose,
  onCreateIncident,
  onKeepSoiOnly,
}: SafetyIncidentWorthyNudgeModalProps) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setReason("");
      setError(null);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4">
      <div className="w-full max-w-xl rounded-[1.75rem] border border-amber-200 bg-white p-6 shadow-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">
          Step 4.8 HIGH-severity nudge
        </p>
        <h2 className="mt-3 text-2xl font-semibold text-slate-950">This looks incident-worthy</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Create an Incident now, or keep the finding in SOI only with a written reason. The save path stays
          nudge-only and does not auto-escalate.
        </p>

        <label className="mt-5 block">
          <span className="text-sm font-semibold text-slate-900">Reason if you keep this in SOI only</span>
          <textarea
            aria-label="Incident-worthy nudge reason"
            className="mt-2 min-h-28 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
            onChange={(event) => setReason(event.target.value)}
            value={reason}
          />
        </label>

        {error ? (
          <div className="mt-4 rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
            {error}
          </div>
        ) : null}

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button
            className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="rounded-full border border-amber-300 bg-amber-50 px-5 py-3 text-sm font-semibold text-amber-900 transition hover:bg-amber-100"
            onClick={() => {
              if (reason.trim().length === 0) {
                setError("Reason is required when keeping a HIGH-severity finding in SOI only.");
                return;
              }
              setError(null);
              onKeepSoiOnly(reason.trim());
            }}
            type="button"
          >
            Keep in SOI only
          </button>
          <button
            className="rounded-full bg-rose-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-rose-600"
            onClick={onCreateIncident}
            type="button"
          >
            Create Incident
          </button>
        </div>
      </div>
    </div>
  );
}
