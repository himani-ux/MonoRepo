import { Link, useLocation, useParams } from "react-router-dom";

type IncidentPhaseStep = 1 | 2 | 3 | 4 | 6 | 7 | 8;

const INCIDENT_PHASES = [
  {
    id: 1,
    label: "Phase 1",
    title: "Report Incident",
    description: "What happened",
    path: "phase-1",
  },
  {
    id: 2,
    label: "Phase 2",
    title: "RCA (Root Cause Analysis)",
    description: "Root cause analysis",
    path: "phase-2",
  },
  {
    id: 3,
    label: "Phase 3",
    title: "Corrective Action",
    description: "Fix it",
    path: "phase-3",
  },
  {
    id: 4,
    label: "Phase 4",
    title: "Preventive Action",
    description: "Prevent it",
    path: "phase-3/preventive",
  },
  {
    id: 6,
    label: "Phase 5",
    title: "Add Evidence",
    description: "Documents",
    path: "phase-4/paper",
  },
  {
    id: 7,
    label: "Phase 6",
    title: "Office Review",
    description: "Approve or return",
    path: "phase-5",
  },
  {
    id: 8,
    label: "Phase 7",
    title: "Loss Evaluation",
    description: "Assess loss and cost",
    path: "phase-6",
  },
] as const;

function activePhaseFromPath(pathname: string) {
  if (/\/(office-communication|resource-handoff)(?:\/|$)/.test(pathname)) {
    return 1;
  }
  if (/\/phase-3\/preventive(?:\/|$)/.test(pathname)) {
    return 4;
  }
  if (/\/phase-4(?:\/|$)/.test(pathname)) {
    return 6;
  }
  if (/\/phase-5(?:\/|$)/.test(pathname)) {
    return 7;
  }
  if (/\/phase-6(?:\/|$)/.test(pathname)) {
    return 8;
  }
  if (/\/phase-3(?:\/|$)/.test(pathname)) {
    return 3;
  }
  const match = pathname.match(/\/phase-(\d)(?:\/|$)/);
  if (!match) {
    return null;
  }
  const phase = Number(match[1]);
  return Number.isFinite(phase) && phase >= 1 && phase <= 2 ? (phase as IncidentPhaseStep) : null;
}

export function IncidentPhaseSwitcher({ activePhase }: { activePhase?: IncidentPhaseStep }) {
  const { id } = useParams();
  const location = useLocation();
  const currentPhase = activePhase ?? activePhaseFromPath(location.pathname);

  if (!id) {
    return null;
  }

  return (
    <nav className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm" aria-label="Incident phases">
      <div className="grid gap-2 md:grid-cols-4 xl:grid-cols-7">
        {INCIDENT_PHASES.map((item) => {
          const active = currentPhase === item.id;
          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={[
                "min-h-24 rounded-xl border px-3 py-3 text-left transition",
                active
                  ? "border-slate-900 bg-slate-900 text-white shadow-sm"
                  : "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300 hover:bg-white",
              ].join(" ")}
              key={item.id}
              to={`/safety/incidents/${id}/${item.path}`}
            >
              <span className={active ? "text-xs font-semibold text-slate-200" : "text-xs font-semibold text-slate-500"}>
                {item.label}
              </span>
              <span className="mt-2 block text-sm font-semibold leading-5">{item.title}</span>
              <span className={active ? "mt-1 block text-xs leading-4 text-slate-200" : "mt-1 block text-xs leading-4 text-slate-500"}>
                {item.description}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export default IncidentPhaseSwitcher;
