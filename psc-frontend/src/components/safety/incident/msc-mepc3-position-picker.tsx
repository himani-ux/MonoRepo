import type { SafetyMscmepc3PositionStatus } from "../../../hooks/safety/use-msc-mepc3-position";

interface SafetyMscmepc3PositionPickerProps {
  autoFillMessage?: string | null;
  awaitingDailyReportMatch?: boolean;
  latitude?: number | string | null;
  longitude?: number | string | null;
  onApplySuggested?: () => void;
  onLatitudeChange: (value: string) => void;
  onLongitudeChange: (value: string) => void;
  sourceReference?: string | null;
  status: SafetyMscmepc3PositionStatus;
}

export default function SafetyMscmepc3PositionPicker({
  autoFillMessage,
  awaitingDailyReportMatch = false,
  latitude,
  longitude,
  onApplySuggested,
  onLatitudeChange,
  onLongitudeChange,
  sourceReference,
  status,
}: SafetyMscmepc3PositionPickerProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-slate-900">
            MSC-MEPC.3 position
          </h2>
          <p className="max-w-2xl text-sm leading-6 text-slate-600">
            Pull the nearest Reporting Daily Report position within ±12 hours,
            then allow a manual override if a more recent bridge position is
            available.
          </p>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600">
          {status === "loading" ? "Looking up daily report" : "Manual override allowed"}
        </div>
      </div>

      {status === "matched" && autoFillMessage ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <p>{autoFillMessage}</p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              className="min-h-[44px] rounded-full border border-amber-300 bg-white px-4 py-2 text-sm font-medium text-slate-700"
              onClick={onApplySuggested}
              type="button"
            >
              Use Daily Report auto-fill
            </button>
            {sourceReference ? (
              <span className="rounded-full border border-amber-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
                {sourceReference}
              </span>
            ) : null}
          </div>
        </div>
      ) : null}

      {status === "awaiting" || awaitingDailyReportMatch ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          No Daily Report within ±12h. Enter latitude and longitude manually.
          The record stays flagged for DPA review.
        </div>
      ) : null}

      {status === "error" ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          Unable to load the Daily Report position right now. Manual entry stays available.
        </div>
      ) : null}

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Latitude</span>
          <input
            aria-label="Latitude"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            inputMode="decimal"
            onChange={(event) => onLatitudeChange(event.target.value)}
            type="number"
            value={latitude ?? ""}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Longitude</span>
          <input
            aria-label="Longitude"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            inputMode="decimal"
            onChange={(event) => onLongitudeChange(event.target.value)}
            type="number"
            value={longitude ?? ""}
          />
        </label>
      </div>
    </section>
  );
}
