import { useState } from "react";

import SafetySoiReprintModal from "./reprint-modal";

export interface SafetySoiDownloadArea {
  area_id: number;
  area_name: string;
  section_12_flag: boolean;
}

interface SafetySoiDownloadPanelProps {
  checklistFormat: "PDF" | "XLSX" | null;
  cycleLabel: string;
  downloadFormat?: "PDF" | "XLSX";
  downloadPending?: boolean;
  inspectionReference: string;
  lostPaperActionPending?: boolean;
  lostPaperFlag?: boolean;
  lostPaperNote?: string | null;
  onDownload?: (format: "PDF" | "XLSX") => void;
  onRecover?: (reason: string, format: "PDF" | "XLSX") => void;
  plannedDate: string;
  selectedAreas: SafetySoiDownloadArea[];
  statusMessage?: string | null;
  state: string;
  uniqueId: string | null;
}

function FormatCard({
  active,
  description,
  label,
}: {
  active: boolean;
  description: string;
  label: "PDF" | "XLSX";
}) {
  return (
    <article
      className={`rounded-2xl border p-4 transition ${
        active
          ? "border-emerald-400 bg-emerald-950 text-white shadow-lg shadow-emerald-100"
          : "border-slate-200 bg-white text-slate-700 shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] opacity-75">
            Checklist format
          </div>
          <h3 className="mt-2 text-lg font-semibold">{label}</h3>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            active ? "bg-white/15 text-white" : "bg-slate-100 text-slate-600"
          }`}
        >
          {active ? "First-choice format" : "Available"}
        </span>
      </div>
      <p className={`mt-3 text-sm leading-6 ${active ? "text-emerald-100" : "text-slate-600"}`}>
        {description}
      </p>
    </article>
  );
}

function formatSoiState(state: string) {
  const labels: Record<string, string> = {
    CLOSED: "Closed",
    DOWNLOADED: "Downloaded",
    IN_FIELDWORK: "Fieldwork",
    PLANNED: "Ready to Download",
    REPORTED: "Submitted",
  };
  return labels[state] ?? state;
}

export default function SafetySoiDownloadPanel({
  checklistFormat,
  cycleLabel,
  downloadFormat = "PDF",
  downloadPending = false,
  inspectionReference,
  lostPaperActionPending = false,
  lostPaperFlag = false,
  lostPaperNote = null,
  onDownload,
  onRecover,
  plannedDate,
  selectedAreas,
  statusMessage = null,
  state,
  uniqueId,
}: SafetySoiDownloadPanelProps) {
  const [isRecoveryOpen, setIsRecoveryOpen] = useState(false);
  const effectiveFormat = checklistFormat ?? downloadFormat;
  const showRecoveryNote = lostPaperFlag || Boolean(lostPaperNote);

  return (
    <>
      <section className="rounded-[1.75rem] border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-sky-50 p-5 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Checklist package</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              The first generated pack freezes the paper checklist identity for this SOI.
              Every later download reuses the same unique ID so paper and digital findings stay linked.
            </p>
          </div>
          <div className="flex flex-col gap-3">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Inspection reference
              </div>
              <div className="mt-2 font-medium text-slate-900">{inspectionReference}</div>
              <div className="text-sm text-slate-600">
                {cycleLabel} - Planned {plannedDate}
              </div>
              <div className="mt-3 border-t border-slate-200 pt-3">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Unique checklist ID
                </div>
                <div className="mt-2 font-medium text-slate-900">
                  {uniqueId ?? "Allocated on first download"}
                </div>
                <div className="text-sm text-slate-600">Current state: {formatSoiState(state)}</div>
              </div>
            </div>
            <button
              className="rounded-full border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm font-semibold text-amber-900 shadow-sm transition hover:border-amber-400 hover:bg-amber-100"
              disabled={lostPaperActionPending}
              onClick={() => setIsRecoveryOpen(true)}
              type="button"
            >
              {lostPaperActionPending ? "Recovering..." : "Lost paper? Re-download"}
            </button>
          </div>
        </div>

            <div className="mt-5 grid gap-3 lg:grid-cols-2">
          <FormatCard
            active={effectiveFormat === "PDF"}
            description="ReportLab output for a print-ready vessel pack with the QR-linked checklist ID on every page."
            label="PDF"
          />
          <FormatCard
            active={effectiveFormat === "XLSX"}
            description="OpenXML worksheet pack for crews that prefer spreadsheet printouts without changing the checklist ID."
            label="XLSX"
          />
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            className="rounded-full bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={downloadPending}
            onClick={() => onDownload?.("PDF")}
            type="button"
          >
            {downloadPending && downloadFormat === "PDF" ? "Downloading PDF..." : "Download PDF"}
          </button>
          <button
            className="rounded-full border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:bg-slate-100"
            disabled={downloadPending}
            onClick={() => onDownload?.("XLSX")}
            type="button"
          >
            {downloadPending && downloadFormat === "XLSX" ? "Downloading XLSX..." : "Download XLSX"}
          </button>
        </div>

        {showRecoveryNote ? (
          <div className="mt-5 rounded-3xl border border-amber-200 bg-white/90 px-4 py-4 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-amber-800">
                  Recovery log
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {lostPaperNote ??
                    "Lost-paper recovery was logged for this inspection before the replacement download."}
                </p>
              </div>
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                Timestamped backend note required
              </span>
            </div>
          </div>
        ) : null}

        {statusMessage ? (
          <div className="mt-5 rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
            {statusMessage}
          </div>
        ) : null}

        <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-4 py-3">
            <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              Selected inspection areas
            </h3>
          </div>
          <div className="divide-y divide-slate-100">
            {selectedAreas.map((area) => (
              <div
                key={area.area_id}
                className="flex items-center justify-between gap-4 px-4 py-3 text-sm"
              >
                <div>
                  <div className="font-medium text-slate-900">
                    Area {area.area_id}: {area.area_name}
                  </div>
                  <div className="mt-1 text-slate-500">
                    {area.section_12_flag ? "Section 12 cross-cutting checkpoint included." : "Physical inspection area."}
                  </div>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  Included
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <SafetySoiReprintModal
        currentFormat={effectiveFormat}
        onClose={() => setIsRecoveryOpen(false)}
        onSubmit={(reason) => {
          onRecover?.(reason, effectiveFormat);
          setIsRecoveryOpen(false);
        }}
        open={isRecoveryOpen}
      />
    </>
  );
}
