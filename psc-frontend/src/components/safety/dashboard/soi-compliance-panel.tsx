import SafetySoiCompliancePill from "../shared/soi-compliance-pill";

type SafetySoiComplianceStatus = "AMBER" | "GREEN" | "NA" | "RED";

export interface SafetySoiCompliancePanelProps {
  currentVessel: {
    applicableAreaCount: number;
    displayValue: string;
    inspectedAreaCount: number;
    overdueAreaCount: number;
    status: SafetySoiComplianceStatus;
    vesselLabel: string;
  };
  fleetAverage: {
    displayValue: string;
    note: string;
    vesselCount: number;
  };
  label: string;
}

function buildCurrentVesselNote({
  displayValue,
  overdueAreaCount,
  status,
}: Pick<SafetySoiCompliancePanelProps["currentVessel"], "displayValue" | "overdueAreaCount" | "status">) {
  if (status === "NA") {
    return displayValue;
  }
  if (overdueAreaCount > 0) {
    return `${overdueAreaCount} area${overdueAreaCount === 1 ? "" : "s"} need attention.`;
  }
  return "All required areas are on time.";
}

export default function SafetySoiCompliancePanel({
  currentVessel,
  fleetAverage,
  label,
}: SafetySoiCompliancePanelProps) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            {label}
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            SOI check status
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Shows whether required SOI areas are being checked on time.
          </p>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          90-day check cycle.
        </div>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_320px]">
        <div>
          <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            {currentVessel.vesselLabel}
          </div>
          <SafetySoiCompliancePill
            applicableAreaCount={currentVessel.applicableAreaCount}
            displayValue={currentVessel.displayValue}
            inspectedAreaCount={currentVessel.inspectedAreaCount}
            label={label}
            note={buildCurrentVesselNote(currentVessel)}
            status={currentVessel.status}
          />
        </div>

        <article className="rounded-md border border-slate-200 bg-slate-50 px-5 py-5 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Fleet average
          </div>
          <div className="mt-3 text-3xl font-semibold text-slate-900">{fleetAverage.displayValue}</div>
          <p className="mt-3 text-sm leading-6 text-slate-600">{fleetAverage.note}</p>
          <div className="mt-4 rounded-md border border-white bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            {fleetAverage.vesselCount} vessel{fleetAverage.vesselCount === 1 ? "" : "s"} currently
            included in this average.
          </div>
        </article>
      </div>
    </section>
  );
}
