import { useState } from "react";

interface SafetyNearMissTriageModalProps {
  incidentId: string;
  initialPriority?: "LOW" | "HIGH";
  onConfirm?: (payload: {
    near_miss_priority: "LOW" | "HIGH";
    override_reason?: string;
    supersede_to_incident: boolean;
  }) => void;
  suggestedPriority: "LOW" | "HIGH";
}

export function SafetyNearMissTriageModal({
  incidentId,
  initialPriority = "LOW",
  onConfirm,
  suggestedPriority,
}: SafetyNearMissTriageModalProps) {
  const [nearMissPriority, setNearMissPriority] = useState<"LOW" | "HIGH">(initialPriority);
  const [overrideReason, setOverrideReason] = useState("");
  const [supersedeToIncident, setSupersedeToIncident] = useState(initialPriority === "HIGH");

  const overrideRequired = nearMissPriority !== suggestedPriority;
  const submitReady = !overrideRequired || overrideReason.trim().length > 0;

  function handlePriorityChange(nextPriority: "LOW" | "HIGH") {
    setNearMissPriority(nextPriority);
    if (nextPriority !== "HIGH") {
      setSupersedeToIncident(false);
    }
  }

  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Safety / Near Miss / Office
          </p>
          <h1 className="text-3xl font-semibold text-slate-900">Near Miss Office Comments</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            Office reviewer confirms the LOW vs HIGH path, logs any override reason, and can
            supersede HIGH-priority cases into the full incident workflow.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <div>Ref: {incidentId}</div>
          <div>Suggested priority: {suggestedPriority}</div>
          <div>Office decision is captured on save.</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="space-y-5 rounded-3xl border border-slate-200 bg-slate-50 p-5">
          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">Priority</span>
            <select
              aria-label="Priority"
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
              onChange={(event) => handlePriorityChange(event.target.value as "LOW" | "HIGH")}
              value={nearMissPriority}
            >
              <option value="LOW">LOW</option>
              <option value="HIGH">HIGH</option>
            </select>
          </label>

          <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
            <input
              checked={supersedeToIncident}
              className="mt-1 h-4 w-4 rounded border-slate-300"
              disabled={nearMissPriority !== "HIGH"}
              onChange={(event) => setSupersedeToIncident(event.target.checked)}
              type="checkbox"
            />
            <span>
              Supersede to incident now
              <span className="mt-1 block text-xs text-slate-500">
                Enabled only for HIGH-priority decisions.
              </span>
            </span>
          </label>
        </section>

        <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5">
          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">Override reason</span>
            <textarea
              aria-label="Override reason"
              className="min-h-[160px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => setOverrideReason(event.target.value)}
              placeholder="Required when you override the suggested LOW/HIGH decision."
              value={overrideReason}
            />
          </label>

          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900">
            {overrideRequired
              ? "Override reason is required because the selected priority differs from the auto-suggestion."
              : "No override reason needed when the selected priority matches the current suggestion."}
          </div>

          <button
            className="min-h-[44px] w-full rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={!submitReady}
            onClick={() =>
              onConfirm?.({
                near_miss_priority: nearMissPriority,
                override_reason: overrideReason.trim() || undefined,
                supersede_to_incident: supersedeToIncident,
              })
            }
            type="button"
          >
            Save Office Comments
          </button>
        </section>
      </div>
    </section>
  );
}

export default SafetyNearMissTriageModal;
