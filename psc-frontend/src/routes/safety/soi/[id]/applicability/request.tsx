import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import SafetyAreaPicker from "../../../../../components/safety/soi/area-picker";
import { safetyKeys, useSafetySoiApplicabilityRequestScreen } from "../../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../../lib/api/client";
import { safetyApi } from "../../../../../lib/api/safety";

function targetStateLabel(newApplicable: boolean) {
  return newApplicable ? "Re-enable area" : "Request non-applicable";
}

export default function SafetySoiApplicabilityRequestRoute() {
  const params = useParams();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const screenQuery = useSafetySoiApplicabilityRequestScreen(inspectionId, enabled);
  const [areaId, setAreaId] = useState<number | null>(null);
  const [newApplicable, setNewApplicable] = useState(false);
  const [masterSignature, setMasterSignature] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!screenQuery.data || areaId !== null) {
      return;
    }
    setAreaId(screenQuery.data.areas[0]?.area_id ?? null);
  }, [screenQuery.data, areaId]);

  const submitMutation = useMutation({
    mutationFn: () => {
      if (areaId === null) {
        throw new Error("Select an area.");
      }
      return safetyApi.submitSoiApplicabilityRequest(inspectionId, {
        area_id: areaId,
        master_signature: masterSignature,
        new_applicable: newApplicable,
        reason,
      });
    },
    onSuccess: async (response) => {
      setMessage(`Applicability request #${response.request_id} submitted.`);
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiApplicabilityRequest(inspectionId) });
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI inspection id.
      </section>
    );
  }

  if (screenQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading applicability request screen...
      </section>
    );
  }

  if (screenQuery.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(screenQuery.error)}
      </section>
    );
  }

  const screen = screenQuery.data;

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.18),_transparent_32%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">SOI Applicability Request</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Area applicability requests now use the live vessel-area payload and submit to the backend approval queue.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Inspection
            </div>
            <div className="mt-2 font-medium text-slate-900">#{screen.inspection_id}</div>
            <div className="text-sm text-slate-600">{screen.inspection_reference}</div>
          </div>
        </div>
      </section>

      <SafetyAreaPicker
        areas={screen.areas}
        selectedAreaIds={areaId === null ? [] : [areaId]}
        title="Requested area"
      />

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Master request package</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              The request reason remains audit-visible and waits for a DPA decision before the vessel map changes.
            </p>
          </div>
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
            {targetStateLabel(newApplicable)}
          </span>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold text-slate-900">Area</span>
            <select
              className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              onChange={(event) => setAreaId(Number(event.target.value))}
              value={areaId ?? ""}
            >
              {screen.areas.map((area) => (
                <option key={area.area_id} value={area.area_id}>
                  {area.area_id} - {area.area_name}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-900">Master signature</span>
            <input
              className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              onChange={(event) => setMasterSignature(event.target.value)}
              type="text"
              value={masterSignature}
            />
          </label>
        </div>

        <label className="mt-4 flex items-center gap-3 text-sm text-slate-700">
          <input
            checked={newApplicable}
            onChange={(event) => setNewApplicable(event.target.checked)}
            type="checkbox"
          />
          Request this area to remain applicable
        </label>

        <label className="mt-4 block">
          <span className="text-sm font-semibold text-slate-900">Request reason</span>
          <textarea
            className="mt-2 min-h-36 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
            onChange={(event) => setReason(event.target.value)}
            value={reason}
          />
        </label>

        {submitMutation.isError ? (
          <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
            {getErrorMessage(submitMutation.error)}
          </div>
        ) : null}
        {message ? (
          <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            {message}
          </div>
        ) : null}

        <button
          className="mt-4 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={submitMutation.isPending}
          onClick={() => {
            setMessage(null);
            submitMutation.mutate();
          }}
          type="button"
        >
          {submitMutation.isPending ? "Submitting..." : "Submit request"}
        </button>
      </section>
    </section>
  );
}
