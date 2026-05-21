import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import SafetySoiDownloadPanel from "../../../../components/safety/soi/download-panel";
import SafetyPaperFirstGuidance from "../../../../components/safety/soi/paper-first-guidance";
import { useSafetySoiInspection, safetyKeys } from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { safetyApi } from "../../../../lib/api/safety";

function saveBlob(blob: Blob, fileName: string) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

export default function SafetySoiDownloadRoute() {
  const params = useParams();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const inspectionQuery = useSafetySoiInspection(inspectionId, enabled);

  const downloadMutation = useMutation({
    mutationFn: (format: "PDF" | "XLSX") => safetyApi.downloadSoiChecklist(inspectionId, format),
    onSuccess: async ({ blob, fileName }) => {
      saveBlob(blob, fileName);
      setStatusMessage(`Checklist downloaded as ${fileName}.`);
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspection(inspectionId) });
    },
  });

  const recoveryMutation = useMutation({
    mutationFn: ({ format, reason }: { format: "PDF" | "XLSX"; reason: string }) =>
      safetyApi.recoverSoiChecklist(inspectionId, { format, reason }),
    onSuccess: async ({ blob, fileName }) => {
      saveBlob(blob, fileName);
      setStatusMessage(`Lost-paper recovery logged and ${fileName} downloaded.`);
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspection(inspectionId) });
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI inspection id.
      </section>
    );
  }

  if (inspectionQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SOI checklist package...
      </section>
    );
  }

  if (inspectionQuery.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(inspectionQuery.error)}
      </section>
    );
  }

  const inspection = inspectionQuery.data;
  const busy = downloadMutation.isPending || recoveryMutation.isPending;

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.18),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(14,165,233,0.14),_transparent_30%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Download SOI Checklist</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              The checklist identity and recovery log now come from the live SOI inspection record.
            </p>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
            Inspection #{inspection.id} stays linked to a single checklist identity through the full cycle.
          </div>
        </div>
      </section>

      <SafetySoiDownloadPanel
        checklistFormat={inspection.checklist_format as "PDF" | "XLSX" | null}
        cycleLabel={inspection.cycle_label}
        downloadFormat={inspection.checklist_format === "XLSX" ? "XLSX" : "PDF"}
        downloadPending={downloadMutation.isPending}
        inspectionReference={inspection.inspection_reference}
        lostPaperActionPending={recoveryMutation.isPending}
        lostPaperFlag={inspection.lost_paper_flag}
        lostPaperNote={inspection.lost_paper_note}
        onDownload={(format) => {
          setStatusMessage(null);
          downloadMutation.mutate(format);
        }}
        onRecover={(reason, format) => {
          setStatusMessage(null);
          recoveryMutation.mutate({ format, reason });
        }}
        plannedDate={inspection.planned_date}
        selectedAreas={inspection.selected_areas.map((area) => ({
          area_id: area.area_id,
          area_name: area.area_name,
          section_12_flag: area.section_12_flag,
        }))}
        state={inspection.state}
        statusMessage={statusMessage}
        uniqueId={inspection.checklist_unique_id}
      />

      {busy && !statusMessage ? (
        <section className="rounded-3xl border border-sky-200 bg-sky-50 p-5 text-sm text-sky-900 shadow-sm">
          Preparing checklist artifact...
        </section>
      ) : null}

      {(downloadMutation.isError || recoveryMutation.isError) ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(downloadMutation.error ?? recoveryMutation.error)}
        </section>
      ) : null}

      <SafetyPaperFirstGuidance />
    </section>
  );
}
