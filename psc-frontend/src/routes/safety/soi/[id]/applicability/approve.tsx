import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { safetyKeys, useSafetySoiApplicabilityApprovalScreen } from "../../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../../lib/api/client";
import { safetyApi } from "../../../../../lib/api/safety";

export default function SafetySoiApplicabilityApproveRoute() {
  const params = useParams();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const screenQuery = useSafetySoiApplicabilityApprovalScreen(inspectionId, enabled);
  const [requestIndex, setRequestIndex] = useState(0);
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [dpaSignature, setDpaSignature] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (screenQuery.data && requestIndex >= screenQuery.data.pending_requests.length) {
      setRequestIndex(0);
    }
  }, [screenQuery.data, requestIndex]);

  const submitMutation = useMutation({
    mutationFn: (selectedDecision: "APPROVED" | "REJECTED") => {
      const request = screenQuery.data?.pending_requests[requestIndex];
      if (!request) {
        throw new Error("No pending request selected.");
      }
      return safetyApi.submitSoiApplicabilityApproval(inspectionId, {
        area_id: request.area_id,
        dpa_decision: selectedDecision,
        dpa_signature: dpaSignature,
        reason,
      });
    },
    onSuccess: async (response) => {
      setMessage(`Applicability request #${response.request_id} ${response.decision.toLowerCase()}.`);
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiApplicabilityApproval(inspectionId) });
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
        Loading applicability approval queue...
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
  const pendingRequest = screen.pending_requests[requestIndex];

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.14),_transparent_32%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">SOI Applicability Approval</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              The DPA approval screen now reads the live pending-request queue and posts real decisions.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Inspection
            </div>
            <div className="mt-2 font-medium text-slate-900">#{screen.inspection_id}</div>
            <div className="text-sm text-slate-600">
              {pendingRequest ? `Pending request #${pendingRequest.request_id}` : "No pending requests"}
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Pending vessel-area request</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Each request stays queued by vessel and area until a DPA decision is posted.
            </p>
          </div>
          <span className="rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-sky-800">
            DPA gate
          </span>
        </div>

        {pendingRequest ? (
          <>
            <label className="mt-5 block">
              <span className="text-sm font-semibold text-slate-900">Pending request</span>
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setRequestIndex(Number(event.target.value))}
                value={requestIndex}
              >
                {screen.pending_requests.map((request, index) => (
                  <option key={request.request_id} value={index}>
                    #{request.request_id} - Area {request.area_id} {request.area_name}
                  </option>
                ))}
              </select>
            </label>

            <dl className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Area
                </dt>
                <dd className="mt-2 text-sm font-medium text-slate-900">{pendingRequest.area_name}</dd>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Requested by
                </dt>
                <dd className="mt-2 text-sm font-medium text-slate-900">{pendingRequest.master_requested_by}</dd>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Requested state
                </dt>
                <dd className="mt-2 text-sm font-medium text-slate-900">
                  {pendingRequest.new_applicable ? "Applicable" : "Non-applicable"}
                </dd>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Master signature
                </dt>
                <dd className="mt-2 text-sm font-medium text-slate-900">
                  {pendingRequest.master_signature}
                </dd>
              </div>
            </dl>

            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-sm font-semibold text-slate-900">Master reason</h3>
              <p className="mt-3 text-sm leading-6 text-slate-700">{pendingRequest.reason}</p>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-sm font-semibold text-slate-900">Decision</span>
                <select
                  className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  onChange={(event) => setDecision(event.target.value as "APPROVED" | "REJECTED")}
                  value={decision}
                >
                  <option value="APPROVED">APPROVED</option>
                  <option value="REJECTED">REJECTED</option>
                </select>
              </label>
              <label className="block">
                <span className="text-sm font-semibold text-slate-900">DPA signature</span>
                <input
                  className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  onChange={(event) => setDpaSignature(event.target.value)}
                  type="text"
                  value={dpaSignature}
                />
              </label>
            </div>

            <label className="mt-4 block">
              <span className="text-sm font-semibold text-slate-900">DPA decision note</span>
              <textarea
                className="mt-2 min-h-32 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
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

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                className="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={submitMutation.isPending}
                onClick={() => {
                  setMessage(null);
                  setDecision("APPROVED");
                  submitMutation.mutate("APPROVED");
                }}
              >
                {submitMutation.isPending && decision === "APPROVED" ? "Submitting..." : "Approve request"}
              </button>
              <button
                type="button"
                className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:bg-slate-100"
                disabled={submitMutation.isPending}
                onClick={() => {
                  setMessage(null);
                  setDecision("REJECTED");
                  submitMutation.mutate("REJECTED");
                }}
              >
                {submitMutation.isPending && decision === "REJECTED" ? "Submitting..." : "Reject request"}
              </button>
            </div>
          </>
        ) : (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
            No pending applicability requests for this vessel.
          </div>
        )}
      </section>
    </section>
  );
}
