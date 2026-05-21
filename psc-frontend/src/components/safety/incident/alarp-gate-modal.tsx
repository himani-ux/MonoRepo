interface SafetyAlarpGateModalProps {
  blockingRows: number;
  thresholdHint?: string | null;
}

export function SafetyAlarpGateModal({
  blockingRows,
  thresholdHint,
}: SafetyAlarpGateModalProps) {
  return (
    <section className="rounded-3xl border border-amber-300 bg-amber-50 p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
        FEAT-SAF-INC-028
      </p>
      <h2 className="mt-2 text-xl font-semibold text-amber-950">ALARP Gate</h2>
      <p className="mt-3 text-sm leading-6 text-amber-900">
        {blockingRows} system-action row
        {blockingRows === 1 ? "" : "s"} still need full effort, likelihood
        reduction, residual-risk text, and attestation before Phase 7 can
        issue the report.
      </p>
      <p className="mt-3 text-xs text-amber-800">
        Threshold hint: {thresholdHint ?? "Higher-priority docs make ALARP mandatory on YELLOW/RED preventive rows."}
      </p>
    </section>
  );
}

export default SafetyAlarpGateModal;
