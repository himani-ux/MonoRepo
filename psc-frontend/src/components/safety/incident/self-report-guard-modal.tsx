interface SafetySelfReportGuardModalProps {
  message: string;
  onAcknowledge?: () => void;
  onCancel?: () => void;
  open: boolean;
  requiredApproverRole: "MASTER" | "DPA";
}

export function SafetySelfReportGuardModal({
  message,
  onAcknowledge,
  onCancel,
  open,
  requiredApproverRole,
}: SafetySelfReportGuardModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-3xl border border-amber-300 bg-white shadow-xl">
        <header className="rounded-t-3xl border-b border-amber-200 bg-amber-50 px-6 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">
            Self-Report Conflict
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            Different approver required
          </h2>
        </header>
        <div className="space-y-4 px-6 py-5 text-sm leading-6 text-slate-600">
          <p>{message}</p>
          <p>
            Route this Phase 1 submission through{" "}
            <span className="font-semibold text-slate-900">{requiredApproverRole}</span>{" "}
            before continuing.
          </p>
        </div>
        <footer className="flex flex-col gap-3 border-t border-slate-200 px-6 py-4 sm:flex-row sm:justify-end">
          <button
            className="min-h-[44px] rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            onClick={onCancel}
            type="button"
          >
            Return to form
          </button>
          <button
            className="min-h-[44px] rounded-full bg-amber-600 px-4 py-2 text-sm font-semibold text-white"
            onClick={onAcknowledge}
            type="button"
          >
            Acknowledge and continue
          </button>
        </footer>
      </div>
    </div>
  );
}
