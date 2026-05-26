import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi, type SafetyAuditorBundleExportRequest } from "../../../lib/api/safety";

const RECORD_TYPES = [
  { label: "Incidents", value: "INCIDENT" },
  { label: "Near misses", value: "NEAR_MISS" },
  { label: "SOI", value: "SOI" },
  { label: "SCM", value: "SCM" },
  { label: "Corrective actions", value: "CORRECTIVE_ACTION" },
] as const;

function formatDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function defaultStartDate(): string {
  const date = new Date();
  date.setDate(date.getDate() - 90);
  return formatDate(date);
}

function downloadBlob({ blob, fileName }: { blob: Blob; fileName: string }) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function SafetyAuditorExportRoute() {
  const [dateFrom, setDateFrom] = useState(defaultStartDate);
  const [dateTo, setDateTo] = useState(() => formatDate(new Date()));
  const [recordTypes, setRecordTypes] = useState<string[]>(() => RECORD_TYPES.map((item) => item.value));
  const [vesselId, setVesselId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [lastExportFile, setLastExportFile] = useState<string | null>(null);

  function toggleRecordType(value: string) {
    setRecordTypes((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLastExportFile(null);

    if (recordTypes.length === 0) {
      setError("Select at least one record type.");
      return;
    }

    const request: SafetyAuditorBundleExportRequest = {
      date_from: dateFrom,
      date_to: dateTo,
      record_types: recordTypes,
      vessel_id: vesselId.trim() || null,
    };

    setIsExporting(true);
    try {
      const result = await safetyApi.exportAuditorBundle(request);
      downloadBlob(result);
      setLastExportFile(result.fileName);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_58%,#fef3c7_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Auditor Export
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Auditor Bundle Export</h1>
        <Link
          className="mt-5 inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
          to="/safety/admin"
        >
          Back to safety admin
        </Link>
      </header>

      <form className="grid gap-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
        <section className="grid gap-4 md:grid-cols-3">
          <label className="grid gap-2 text-sm font-semibold text-slate-700">
            Date from
            <input
              className="rounded-2xl border border-slate-300 px-4 py-3 text-sm font-normal text-slate-900 outline-none focus:border-slate-500"
              onChange={(event) => setDateFrom(event.target.value)}
              required
              type="date"
              value={dateFrom}
            />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-slate-700">
            Date to
            <input
              className="rounded-2xl border border-slate-300 px-4 py-3 text-sm font-normal text-slate-900 outline-none focus:border-slate-500"
              onChange={(event) => setDateTo(event.target.value)}
              required
              type="date"
              value={dateTo}
            />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-slate-700">
            Vessel filter
            <input
              className="rounded-2xl border border-slate-300 px-4 py-3 text-sm font-normal text-slate-900 outline-none focus:border-slate-500"
              onChange={(event) => setVesselId(event.target.value)}
              placeholder="Optional"
              value={vesselId}
            />
          </label>
        </section>

        <fieldset className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
          <legend className="px-2 text-sm font-semibold text-slate-900">Record types</legend>
          <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {RECORD_TYPES.map((item) => (
              <label
                className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700"
                key={item.value}
              >
                <input
                  checked={recordTypes.includes(item.value)}
                  onChange={() => toggleRecordType(item.value)}
                  type="checkbox"
                />
                {item.label}
              </label>
            ))}
          </div>
        </fieldset>

        {error ? <p className="text-sm font-medium text-rose-700">{error}</p> : null}
        {lastExportFile ? (
          <p className="text-sm font-medium text-emerald-700">Export prepared: {lastExportFile}</p>
        ) : null}

        <button
          className="inline-flex min-h-11 w-fit items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isExporting}
          type="submit"
        >
          {isExporting ? "Building bundle..." : "Build auditor bundle"}
        </button>
      </form>
    </section>
  );
}
