interface SafetySignatureBlockProps {
  role: "reporter" | "master" | "hod" | "dpa" | "fm" | "pic";
  mode: "capture" | "display";
  awaitingLabel?: string;
  existingSignature?: {
    signer_display_name: string;
    signed_at: string;
    device_fingerprint_last8: string;
  };
}

const roleLabels: Record<SafetySignatureBlockProps["role"], string> = {
  reporter: "Reporter",
  master: "Master",
  hod: "HOD",
  dpa: "DPA",
  fm: "FM",
  pic: "PIC",
};

export default function SafetySignatureBlock({
  role,
  mode,
  awaitingLabel,
  existingSignature,
}: SafetySignatureBlockProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Signature
          </p>
          <h3 className="mt-1 text-sm font-semibold text-slate-900">
            {roleLabels[role]}
          </h3>
        </div>
        <span className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium uppercase tracking-[0.15em] text-slate-600">
          {mode === "capture" ? "Capture" : "Display"}
        </span>
      </div>

      {existingSignature ? (
        <dl className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-3">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
              Signed By
            </dt>
            <dd className="mt-1 text-slate-900">{existingSignature.signer_display_name}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
              Signed At
            </dt>
            <dd className="mt-1 text-slate-900">{existingSignature.signed_at}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
              Device
            </dt>
            <dd className="mt-1 text-slate-900">{existingSignature.device_fingerprint_last8}</dd>
          </div>
        </dl>
      ) : (
        <p className="mt-4 text-sm text-slate-600">
          {awaitingLabel ?? "Awaiting signature capture from the current closer."}
        </p>
      )}
    </section>
  );
}

