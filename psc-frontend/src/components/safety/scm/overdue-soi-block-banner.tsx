export interface SafetyOverdueSoiArea {
  area_id: number;
  area_name: string | null;
  due_at: string | null;
  message: string;
  overdue_days: number;
}

interface SafetyOverdueSoiBlockBannerProps {
  overdueAreas: SafetyOverdueSoiArea[];
}

export default function SafetyOverdueSoiBlockBanner({
  overdueAreas,
}: SafetyOverdueSoiBlockBannerProps) {
  if (overdueAreas.length === 0) {
    return (
      <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700">
          SOI block clear
        </p>
        <h2 className="mt-2 text-lg font-semibold text-emerald-950">No overdue SOI areas</h2>
        <p className="mt-2 text-sm leading-6 text-emerald-900">
          The vessel currently sits inside the 90-day SOI ceiling, so the Master may proceed
          to sign-off once the remaining SCM preflight items are satisfied.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-rose-700">
        Hard block
      </p>
      <h2 className="mt-2 text-lg font-semibold text-rose-950">Overdue SOI hard block</h2>
      <p className="mt-2 text-sm leading-6 text-rose-900">
        Sign-off is blocked until the overdue Safety Officer Inspection areas are cleared.
        The meeting may continue, but the SCM compliance artefact cannot be signed yet.
      </p>
      <ul className="mt-4 space-y-3">
        {overdueAreas.map((area) => (
          <li
            className="rounded-2xl border border-rose-200 bg-white px-4 py-3"
            key={`${area.area_id}-${area.due_at ?? "no-due-at"}`}
          >
            <p className="text-sm font-semibold text-slate-900">
              Area {area.area_id}
              {area.area_name ? ` · ${area.area_name}` : ""}
            </p>
            <p className="mt-1 text-sm text-rose-800">{area.message}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
              Due at {area.due_at ?? "Unavailable"}
            </p>
          </li>
        ))}
      </ul>
      <a
        className="mt-5 inline-flex min-h-[44px] items-center rounded-full bg-rose-700 px-4 py-2 text-sm font-medium text-white"
        href="/safety/soi/?vessel_id=7&filter=overdue"
      >
        Open overdue SOI list
      </a>
    </section>
  );
}
