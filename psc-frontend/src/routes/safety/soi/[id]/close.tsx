import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import SafetySoiCloseConfirmPanel from "../../../../components/safety/soi/close-confirm-panel";
import SafetyFloatingFeedback from "../../../../components/safety/shared/safety-floating-feedback";
import { useSafetyAuth } from "../../../../hooks/safety/use-auth";
import { safetyKeys, useSafetySoiCloseSnapshot } from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { safetyApi } from "../../../../lib/api/safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../../lib/safety/digital-signature";

export default function SafetySoiCloseRoute() {
  const params = useParams();
  const auth = useSafetyAuth();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const [typedName, setTypedName] = useState(() => resolveSignatureTypedName(auth.user));
  const [deviceFingerprint] = useState(() => getSafetyDeviceFingerprint());
  const [message, setMessage] = useState<string | null>(null);
  const snapshotQuery = useSafetySoiCloseSnapshot(inspectionId, enabled);

  const closeMutation = useMutation({
    mutationFn: () =>
      safetyApi.closeSoiInspection(inspectionId, {
        device_fingerprint: deviceFingerprint,
        typed_name: typedName,
      }),
    onSuccess: async () => {
      setMessage("SOI event closed successfully.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiCloseSnapshot(inspectionId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspection(inspectionId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspections({}) }),
      ]);
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI inspection id.
      </section>
    );
  }

  if (snapshotQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SOI close package...
      </section>
    );
  }

  if (snapshotQuery.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(snapshotQuery.error)}
      </section>
    );
  }

  const snapshot = closeMutation.data ?? snapshotQuery.data;

  return (
    <section className="space-y-6">
      {closeMutation.isError ? (
        <SafetyFloatingFeedback tone="error">{getErrorMessage(closeMutation.error)}</SafetyFloatingFeedback>
      ) : null}
      {message ? <SafetyFloatingFeedback tone="success">{message}</SafetyFloatingFeedback> : null}
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.14),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(251,191,36,0.18),_transparent_28%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">SOI Close Event</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Inspection
              </div>
              <div className="mt-2 font-medium text-slate-900">#{snapshot.inspection_id}</div>
              <div className="text-sm text-slate-600">{snapshot.inspection_reference}</div>
            </div>
            <Link
              className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
              to="/safety/soi"
            >
              Back to SOI list
            </Link>
          </div>
        </div>
      </section>

      <SafetySoiCloseConfirmPanel
        canClose={snapshot.state !== "CLOSED" && !closeMutation.isPending}
        error={null}
        onClose={() => {
          setMessage(null);
          closeMutation.mutate();
        }}
        onTypedNameChange={setTypedName}
        snapshot={snapshot}
        typedName={typedName}
      />
    </section>
  );
}
