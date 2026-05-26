import type { SafetySoiAreaOption, SafetySoiSection12Status } from "../../../schemas/safety/soi";

interface SafetyAreaPickerProps {
  areas: SafetySoiAreaOption[];
  disabledAreaIds?: number[];
  maxSelectableAreas?: number;
  onToggleAreaId?: (areaId: number) => void;
  section12Status?: SafetySoiSection12Status;
  selectedAreaIds: number[];
  title?: string;
}

function formatAuditDate(value: string | null) {
  if (!value) {
    return "Awaiting first cycle";
  }

  return value.slice(0, 10);
}

export default function SafetyAreaPicker({
  areas,
  disabledAreaIds = [],
  maxSelectableAreas,
  onToggleAreaId,
  section12Status,
  selectedAreaIds,
  title = "Picked areas",
}: SafetyAreaPickerProps) {
  const disabledIds = new Set(disabledAreaIds);
  const maxReached = typeof maxSelectableAreas === "number" && selectedAreaIds.length >= maxSelectableAreas;

  return (
    <section className="rounded-[1.75rem] border border-amber-200 bg-gradient-to-br from-amber-50 via-white to-rose-50 p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            The create and pick-areas screens both read from the same applicable-area
            surface. Section 12 is intentionally visible alongside the physical areas so
            the quarterly culture checkpoint does not drift out of the inspection cadence.
          </p>
          {typeof maxSelectableAreas === "number" ? (
            <p className="mt-2 text-sm font-medium text-amber-800">
              Select up to {maxSelectableAreas} areas for one SOI. Selected: {selectedAreaIds.length}/{maxSelectableAreas}.
            </p>
          ) : null}
        </div>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
          Standard SOI areas
        </span>
      </div>

      {section12Status ? (
        <div
          className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${
            section12Status.covered_this_cycle
              ? "border-slate-200 bg-slate-900 text-white"
              : "border-amber-300 bg-amber-100 text-amber-950"
          }`}
        >
          {section12Status.covered_this_cycle ? (
            <span>
              Section 12 already carried for {section12Status.cycle_label}
              {section12Status.covered_by_inspection_reference
                ? ` through ${section12Status.covered_by_inspection_reference}.`
                : "."}{" "}
              {section12Status.next_allowed_date
                ? `Additional carry opens ${section12Status.next_allowed_date}.`
                : null}
            </span>
          ) : (
            <span>Cross-cutting Safety &amp; Culture not yet covered this quarter - include now?</span>
          )}
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {areas.map((area) => {
          const selected = selectedAreaIds.includes(area.area_id);
          const areaDisabled = disabledIds.has(area.area_id) || (!selected && maxReached);

          return (
            <article
              key={area.area_id}
              className={`rounded-2xl border p-4 transition ${
                selected
                  ? "border-amber-400 bg-white shadow-lg shadow-amber-100"
                  : "border-slate-200 bg-white/80 shadow-sm"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {area.section_12_flag ? "Section 12" : `Area ${area.area_id}`}
                  </div>
                  <h3 className="mt-2 text-base font-semibold text-slate-900">{area.area_name}</h3>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    selected
                      ? "bg-amber-100 text-amber-800"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {selected ? "Selected" : "Optional"}
                </span>
              </div>

              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-slate-500">Last inspected</dt>
                  <dd className="font-medium text-slate-700">{formatAuditDate(area.last_inspected_at)}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt className="text-slate-500">Due by</dt>
                  <dd className="font-medium text-slate-700">{formatAuditDate(area.due_at)}</dd>
                </div>
              </dl>

              {area.section_12_flag ? (
                <div className="mt-4 rounded-2xl bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">
                  Section 12 carried once per cycle.
                </div>
              ) : null}

              {onToggleAreaId ? (
                <label className="mt-4 flex items-center gap-3 text-sm font-medium text-slate-800">
                  <input
                    checked={selected}
                    disabled={areaDisabled}
                    onChange={() => onToggleAreaId(area.area_id)}
                    type="checkbox"
                  />
                  {disabledIds.has(area.area_id)
                    ? "Locked for this cycle"
                    : !selected && maxReached
                      ? `Maximum ${maxSelectableAreas} areas selected`
                      : "Include in this SOI"}
                </label>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
