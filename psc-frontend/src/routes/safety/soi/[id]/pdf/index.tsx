import { useMutation } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { useSafetySoiInspection } from "../../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../../lib/api/client";
import { safetyApi } from "../../../../../lib/api/safety";

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

const sectionItems = [
  "Cover metadata + closure chain",
  "Stamped areas with Last Inspected dates",
  "Findings table (M-SCAT, SHELL, priority, assignee, status)",
  "Trainees",
  "Signature block",
  "Audit-trail footer",
];

export default function SafetySoiPdfRoute() {
  const params = useParams();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const inspectionQuery = useSafetySoiInspection(inspectionId, enabled);
  const downloadMutation = useMutation({
    mutationFn: () => safetyApi.downloadSoiSummaryPdf(inspectionId),
    onSuccess: ({ blob, fileName }) => {
      saveBlob(blob, fileName);
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
        Loading SOI PDF summary...
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

  return (
    <section className="space-y-6 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            SOI Export
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">
            SOI Summary PDF
          </h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-600">
            The SOI export summary now reflects the live inspection metadata instead of demo values.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Permission: <span className="font-semibold text-slate-900">SAF_P_023</span>
          <div className="mt-2 text-xs text-slate-500">
            Inspection #{inspection.id}
          </div>
        </div>
      </header>

      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Signed SOI summary</h3>
          <p className="mt-1 text-sm text-slate-600">
            Download the live backend PDF for filing, audit review, or print.
          </p>
        </div>
        <button
          className="rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={downloadMutation.isPending}
          onClick={() => downloadMutation.mutate()}
          type="button"
        >
          {downloadMutation.isPending ? "Preparing..." : "Download / Print PDF"}
        </button>
      </div>

      {downloadMutation.isError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {getErrorMessage(downloadMutation.error)}
        </div>
      ) : null}

      <article className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-950">
        Paper checklist: unique-ID {inspection.checklist_unique_id ?? "pending first download"}, filed in ship SMS filing system.
      </article>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
            Summary Structure
          </h3>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {sectionItems.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-4">
          <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
              Export Rules
            </h3>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              <li className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                Auto-generated when the SOI reaches <code>REPORTED</code>
              </li>
              <li className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                No per-item Yes/No checklist reproduction
              </li>
              <li className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                Closed-Since-Last SCM feed indicator included
              </li>
            </ul>
          </article>
        </div>
      </div>
    </section>
  );
}
