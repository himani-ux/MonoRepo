import { formatVesselName } from "../../../lib/safety/vessel-display";
import type { SafetyDuplicateCandidate } from "../../../schemas/safety/incident-phase4";

interface SafetyDuplicateWarningBannerProps {
  candidates: SafetyDuplicateCandidate[];
}

export function SafetyDuplicateWarningBanner({
  candidates,
}: SafetyDuplicateWarningBannerProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
            FEAT-SAF-INC-032
          </p>
          <h2 className="text-lg font-semibold text-amber-900">
            Possible duplicate incidents detected
          </h2>
        </div>
        <span className="rounded-full border border-amber-300 px-3 py-1 text-xs font-medium uppercase text-amber-800">
          Review before linking
        </span>
      </div>
      <ul className="mt-4 grid gap-3 md:grid-cols-2">
        {candidates.map((candidate) => (
          <li
            key={candidate.incident_id}
            className="rounded-2xl border border-amber-200 bg-white p-4 text-sm text-slate-700"
          >
            <p className="font-semibold text-slate-900">
              Incident #{candidate.incident_id} - {formatVesselName(candidate)}
            </p>
            <p className="mt-1">
              {candidate.distance_nm.toFixed(1)} nm apart - {candidate.overlap_hours.toFixed(1)}h overlap
            </p>
            <p className="mt-1">
              Narrative overlap {(candidate.narrative_overlap * 100).toFixed(0)}%
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default SafetyDuplicateWarningBanner;
