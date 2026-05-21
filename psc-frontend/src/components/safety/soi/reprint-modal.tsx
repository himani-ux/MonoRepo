import { useEffect, useState } from "react";

interface SafetySoiReprintModalProps {
  currentFormat: "PDF" | "XLSX";
  onClose: () => void;
  onSubmit: (reason: string) => void;
  open: boolean;
}

export default function SafetySoiReprintModal({
  currentFormat,
  onClose,
  onSubmit,
  open,
}: SafetySoiReprintModalProps) {
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

  const handleSubmit = () => {
    const normalized = reason.trim();
    if (!normalized) {
      setError("Recovery reason is required.");
      return;
    }
    onSubmit(normalized);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4">
      <section
        aria-labelledby="soi-reprint-title"
        aria-modal="true"
        className="w-full max-w-xl rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-2xl"
        role="dialog"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">
              Lost / damaged paper recovery
            </p>
            <h2 className="mt-2 text-xl font-semibold text-slate-900" id="soi-reprint-title">
              Re-download checklist package
            </h2>
          </div>
          <button
            className="rounded-full border border-slate-200 px-3 py-1 text-sm text-slate-600"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </div>

        <p className="mt-4 text-sm leading-6 text-slate-600">
          Recovery keeps the existing checklist ID and re-serves the stored format. The backend
          appends a timestamped loss note before returning the artifact.
        </p>

        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Stored checklist format: <span className="font-semibold text-slate-900">{currentFormat}</span>
        </div>

        <label className="mt-5 block" htmlFor="soi-reprint-reason">
          <span className="text-sm font-medium text-slate-900">Reason</span>
          <textarea
            className="mt-2 min-h-32 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            id="soi-reprint-reason"
            onChange={(event) => {
              setReason(event.target.value);
              if (error) {
                setError(null);
              }
            }}
            placeholder="Describe why the paper checklist must be reprinted."
            value={reason}
          />
        </label>

        {error ? (
          <p className="mt-3 text-sm font-medium text-rose-700">{error}</p>
        ) : null}

        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            className="rounded-full border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-700"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500"
            onClick={handleSubmit}
            type="button"
          >
            Log loss and re-download
          </button>
        </div>
      </section>
    </div>
  );
}
