import { useState } from "react";

import { useAuth } from "../../../hooks/use-auth";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../lib/safety/digital-signature";

interface SafetyFleetAlertComposerProps {
  dueBy: string;
  incidentId: string;
  initialDraft: string;
  onPublish?: (payload: {
    alert_text: string;
    device_fingerprint: string;
    typed_name: string;
  }) => void;
}

export function SafetyFleetAlertComposer({
  dueBy,
  incidentId,
  initialDraft,
  onPublish,
}: SafetyFleetAlertComposerProps) {
  const { user } = useAuth();
  const [alertText, setAlertText] = useState(initialDraft);
  const [typedName, setTypedName] = useState(() => resolveSignatureTypedName(user));
  const [deviceFingerprint] = useState(() => getSafetyDeviceFingerprint());

  const publishReady =
    alertText.trim().length > 0 &&
    typedName.trim().length >= 3;

  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-slate-900">Fleet Alert Composer</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            HIGH-priority near misses require a fleet alert within 7 days. The
            workspace draft keeps vessel and crew identifiers anonymised and fans
            the alert out through the shared notification queue.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <div>Ref: {incidentId}</div>
          <div>Alert due by: {dueBy}</div>
          <div>DPA publish signature is captured on send.</div>
        </div>
      </div>

      <section className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
        <label className="block space-y-2 text-sm text-slate-700">
          <span className="font-medium">Fleet alert draft</span>
          <textarea
            aria-label="Fleet alert draft"
            className="min-h-[240px] w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 leading-6"
            onChange={(event) => setAlertText(event.target.value)}
            value={alertText}
          />
        </label>
      </section>

      <div className="grid gap-5">
        <label className="block space-y-2 text-sm text-slate-700">
          <span className="font-medium">Typed name</span>
          <input
            aria-label="Typed name"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => setTypedName(event.target.value)}
            value={typedName}
          />
        </label>
      </div>

      <button
        className="min-h-[44px] rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
        disabled={!publishReady}
        onClick={() =>
          onPublish?.({
            alert_text: alertText.trim(),
            device_fingerprint: deviceFingerprint.trim(),
            typed_name: typedName.trim(),
          })
        }
        type="button"
      >
        Publish Fleet Alert
      </button>
    </section>
  );
}

export default SafetyFleetAlertComposer;
