import { useParams } from "react-router-dom";

import SafetyAreaPicker from "../../../../components/safety/soi/area-picker";
import { useSafetySoiInspection, useSafetySoiPickAreas } from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";

export default function SafetySoiPickAreasRoute() {
  const params = useParams();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const inspectionQuery = useSafetySoiInspection(inspectionId, enabled);
  const pickAreasQuery = useSafetySoiPickAreas(inspectionId, enabled);

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI inspection id.
      </section>
    );
  }

  if (inspectionQuery.isLoading || pickAreasQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading picked areas...
      </section>
    );
  }

  if (inspectionQuery.isError || pickAreasQuery.isError) {
    const error = inspectionQuery.error ?? pickAreasQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const inspection = inspectionQuery.data;
  const pickAreas = pickAreasQuery.data;

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.12),_transparent_35%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">SOI Pick Areas</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              The selected and available area lists are now read from the inspection&apos;s live pick-areas payload.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Inspection
            </div>
            <div className="mt-2 font-medium text-slate-900">#{inspection.id}</div>
            <div className="text-sm text-slate-600">{inspection.inspection_reference}</div>
          </div>
        </div>
      </section>

      <SafetyAreaPicker
        areas={pickAreas.available_areas}
        section12Status={pickAreas.section_12_status}
        selectedAreaIds={pickAreas.selected_areas.map((area) => area.area_id)}
        title="Picked areas"
      />
    </section>
  );
}
