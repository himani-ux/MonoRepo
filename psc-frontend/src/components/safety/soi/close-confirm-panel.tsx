import SafetySignatureBlock from "../shared/signature-block";
import type {
  SafetySoiCloseSnapshot,
  SafetySoiDigitalSignatureSnapshot,
} from "../../../schemas/safety/soi";

interface SafetySoiCloseConfirmPanelProps {
  canClose: boolean;
  error?: string | null;
  onClose: () => void;
  onTypedNameChange: (value: string) => void;
  snapshot: SafetySoiCloseSnapshot;
  typedName: string;
}

function metricCard(label: string, value: string, note?: string) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
      {note ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">{note}</p>
      ) : null}
    </article>
  );
}

function renderSignature(signature: SafetySoiDigitalSignatureSnapshot | null) {
  return (
    <SafetySignatureBlock
      awaitingLabel="Awaiting the final Master digital signature before this SOI event can move from Reported to Closed."
      existingSignature={signature ?? undefined}
      mode={signature ? "display" : "capture"}
      role="master"
    />
  );
}

export default function SafetySoiCloseConfirmPanel({
  canClose,
  error = null,
  onClose,
  onTypedNameChange,
  snapshot,
  typedName,
}: SafetySoiCloseConfirmPanelProps) {
  return (
    <section className="space-y-6">
      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Master close package</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Step 4.12 closes the full SOI event after fieldwork reporting. The close event
              captures the final Master signature, while the 90-day compliance reset stays
              anchored to the earlier submit-time fieldwork stamp for each reported area.
            </p>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
            {snapshot.state === "CLOSED"
              ? `Closed at ${snapshot.closed_at ?? "recorded"}`
              : "Ready for final Master close"}
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {metricCard(
            "Crew Rotation Coverage",
            snapshot.crew_rotation.display_value,
            `${snapshot.crew_rotation.accompanied_crew_count} of ${snapshot.crew_rotation.total_active_crew} active crew have accompanied >=1 SOI in the last 12 months.`,
          )}
          {metricCard(
            "Findings Registered",
            String(snapshot.finding_summary.total_count),
            `${snapshot.finding_summary.pending_closure_count} pending closure, ${snapshot.finding_summary.open_count} still open.`,
          )}
          {metricCard(
            "Areas In This Event",
            String(snapshot.selected_areas.length),
            "Compliance timing stays anchored to the existing fieldwork stamp for each selected area.",
          )}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
        <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Selected inspection areas</h2>
          <div className="mt-4 grid gap-3">
            {snapshot.selected_areas.map((area) => (
              <article
                key={area.selection_id}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <div className="text-sm font-semibold text-slate-900">
                    Area {area.area_id} - {area.area_name}
                  </div>
                  {area.section_12_flag ? (
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">
                      Section 12
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Last fieldwork stamp: {area.last_inspected_at ?? "Awaiting submit-time fieldwork stamp"}
                </p>
                {area.notes ? (
                  <p className="mt-2 text-sm leading-6 text-slate-700">{area.notes}</p>
                ) : null}
              </article>
            ))}
          </div>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
              Trainee participation
            </h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {snapshot.trainees.map((trainee) => (
                <span
                  key={`${trainee.crew_id}-${trainee.trainee_slot}`}
                  className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700"
                >
                  Slot {trainee.trainee_slot}: {trainee.crew_id}
                </span>
              ))}
            </div>
          </div>
        </section>

        <aside className="space-y-6">
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Master signature</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              SO and Assistant remain paper-signature roles. This panel captures only the
              final Master digital signature for the close event.
            </p>

            <div className="mt-5">{renderSignature(snapshot.signature)}</div>

            {error ? (
              <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800">
                {error}
              </div>
            ) : null}

            {snapshot.signature ? null : (
              <div className="mt-5 grid gap-4">
                <label className="block">
                  <span className="text-sm font-semibold text-slate-900">Typed name</span>
                  <input
                    aria-label="SOI close typed name"
                    className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    onChange={(event) => onTypedNameChange(event.target.value)}
                    type="text"
                    value={typedName}
                  />
                </label>
                <button
                  className="rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                  disabled={!canClose}
                  onClick={onClose}
                  type="button"
                >
                  Close SOI event
                </button>
              </div>
            )}
          </section>

          <section className="rounded-[1.75rem] border border-sky-200 bg-sky-50 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">SCM handoff note</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Closing the SOI event does not close the findings themselves. Open and pending
              items still feed the next SCM Closed-Since-Last review surface.
            </p>
          </section>
        </aside>
      </section>
    </section>
  );
}
