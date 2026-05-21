import { useState } from "react";

import SafetySignatureBlock from "../shared/signature-block";
import type { SafetySoiDigitalSignatureSnapshot } from "../../../schemas/safety/soi-finding";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../lib/safety/digital-signature";

interface SafetyMasterCountersignBlockProps {
  canAct: boolean;
  error?: string | null;
  existingSignature?: SafetySoiDigitalSignatureSnapshot | null;
  onApprove: (payload: {
    closureNote: string;
    deviceFingerprint: string;
    typedName: string;
  }) => void;
  onReject: (reason: string) => void;
  status: string;
}

export default function SafetyMasterCountersignBlock({
  canAct,
  error = null,
  existingSignature,
  onApprove,
  onReject,
  status,
}: SafetyMasterCountersignBlockProps) {
  const auth = useSafetyAuth();
  const [typedName, setTypedName] = useState(() => resolveSignatureTypedName(auth.user));
  const [deviceFingerprint] = useState(() => getSafetyDeviceFingerprint());
  const [closureNote, setClosureNote] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const helperError = localError ?? error;

  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Master countersignature</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Step 4.9 keeps the paper-signature rule for the Safety Officer and Assistant, and records the Master
            approval digitally when the finding can move from pending closure to closed.
          </p>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-700">
          {status}
        </span>
      </div>

      <div className="mt-5">
        <SafetySignatureBlock
          awaitingLabel="Awaiting Master counter-signature after the Safety Officer marks this finding pending closure."
          existingSignature={existingSignature ?? undefined}
          mode={existingSignature ? "display" : "capture"}
          role="master"
        />
      </div>

      {helperError ? (
        <div className="mt-4 rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
          {helperError}
        </div>
      ) : null}

      {canAct && !existingSignature && status === "PENDING_CLOSURE" ? (
        <div className="mt-5 grid gap-4">
          <label className="block">
            <span className="text-sm font-semibold text-slate-900">Typed name</span>
            <input
              aria-label="Master typed name"
              className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              onChange={(event) => setTypedName(event.target.value)}
              type="text"
              value={typedName}
            />
          </label>

          <label className="block">
            <span className="text-sm font-semibold text-slate-900">Closure note</span>
            <textarea
              aria-label="Master closure note"
              className="mt-2 min-h-28 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              onChange={(event) => setClosureNote(event.target.value)}
              value={closureNote}
            />
          </label>

          <div className="grid gap-4 rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 lg:grid-cols-[1fr,auto]">
            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Reject back to open reason</span>
              <textarea
                aria-label="Master rejection reason"
                className="mt-2 min-h-24 w-full rounded-3xl border border-amber-300 bg-white px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setRejectionReason(event.target.value)}
                value={rejectionReason}
              />
            </label>
            <div className="flex flex-col gap-3 lg:justify-end">
              <button
                className="rounded-full bg-emerald-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800"
                onClick={() => {
                  if (typedName.trim().length < 3) {
                    setLocalError("Master typed name is required for digital counter-signature.");
                    return;
                  }
                  setLocalError(null);
                  onApprove({
                    closureNote,
                    deviceFingerprint,
                    typedName,
                  });
                }}
                type="button"
              >
                Approve closure
              </button>
              <button
                className="rounded-full border border-rose-300 bg-white px-5 py-3 text-sm font-semibold text-rose-800 transition hover:border-rose-400 hover:bg-rose-50"
                onClick={() => {
                  if (rejectionReason.trim().length === 0) {
                    setLocalError("Master rejection requires a written reason.");
                    return;
                  }
                  setLocalError(null);
                  onReject(rejectionReason);
                }}
                type="button"
              >
                Reject to Open
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
