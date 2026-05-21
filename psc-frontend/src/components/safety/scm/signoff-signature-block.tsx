import SafetySignatureBlock from "../shared/signature-block";

export interface SafetyScmSignoffSignature {
  typed_name: string;
  signed_at: string;
  device_fingerprint: string;
}

function last8(value: string) {
  return value.slice(-8) || value;
}

export default function SafetyScmSignoffSignatureBlock({
  signature,
}: {
  signature?: SafetyScmSignoffSignature;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl">
          <h2 className="text-lg font-semibold text-slate-900">Master signature</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Capture the Master signature with typed name, timestamp, and device
            fingerprint after all sign-off checks pass.
          </p>
        </div>
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] text-amber-700">
          Hybrid Digital Signature
        </div>
      </div>

      <div className="mt-5">
        <SafetySignatureBlock
          role="master"
          mode={signature ? "display" : "capture"}
          awaitingLabel="Master signature is captured after all sign-off checks pass."
          existingSignature={
            signature
              ? {
                  signer_display_name: signature.typed_name,
                  signed_at: signature.signed_at,
                  device_fingerprint_last8: last8(signature.device_fingerprint),
                }
              : undefined
          }
        />
      </div>
    </section>
  );
}
