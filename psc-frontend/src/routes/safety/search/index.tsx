import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import SafetyCrossRecordResults, {
  type SafetySearchGroupKey,
  type SafetySearchResponse,
} from "../../../components/safety/search/cross-record-results";
import SafetyArchiveOptInToggle from "../../../components/safety/search/archive-opt-in-toggle";
import { useSafetySearch } from "../../../hooks/use-safety";

type SearchRecordTypeFilter = "ALL" | SafetySearchGroupKey;

const searchTypeOptions: Array<{ description: string; value: SearchRecordTypeFilter; label: string }> = [
  { value: "ALL", label: "All", description: "Cross-record full-text scan across every Step 8.8 source." },
  { value: "INCIDENT", label: "Incident", description: "Formal incident records only." },
  { value: "NEAR_MISS", label: "Near Miss", description: "Reporter-masked near-miss hits where required." },
  { value: "SCM", label: "SCM", description: "Safety committee meeting records." },
  { value: "SOI_FINDING", label: "SOI", description: "SOI finding title and description hits." },
];

function createEmptyResponse(
  query = "",
  recordType: SearchRecordTypeFilter = "ALL",
  includeArchived = false,
): SafetySearchResponse {
  return {
    counts: {
      INCIDENT: 0,
      NEAR_MISS: 0,
      SCM: 0,
      SOI_FINDING: 0,
    },
    groups: {
      INCIDENT: [],
      NEAR_MISS: [],
      SCM: [],
      SOI_FINDING: [],
    },
    include_archived: includeArchived,
    labels: {
      INCIDENT: "Incidents",
      NEAR_MISS: "Near Miss",
      SCM: "SCM",
      SOI_FINDING: "SOI Findings",
    },
    query,
    record_type: recordType,
    total_count: 0,
  };
}

function normalizeRecordType(value: string | null): SearchRecordTypeFilter {
  if (value === "INCIDENT" || value === "NEAR_MISS" || value === "SCM" || value === "SOI_FINDING") {
    return value;
  }
  return "ALL";
}

function normalizeIncludeArchived(value: string | null): boolean {
  if (!value) {
    return false;
  }
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

export default function SafetySearchRoute() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = String(searchParams.get("q") ?? "");
  const initialRecordType = normalizeRecordType(searchParams.get("record_type"));
  const initialIncludeArchived = normalizeIncludeArchived(searchParams.get("include_archived"));
  const [queryInput, setQueryInput] = useState(initialQuery);
  const [recordType, setRecordType] = useState<SearchRecordTypeFilter>(initialRecordType);
  const [includeArchived, setIncludeArchived] = useState(initialIncludeArchived);
  const [response, setResponse] = useState<SafetySearchResponse>(
    createEmptyResponse(initialQuery.trim(), initialRecordType, initialIncludeArchived),
  );
  const deferredQuery = String(searchParams.get("q") ?? "").trim();
  const deferredRecordType = normalizeRecordType(searchParams.get("record_type"));
  const deferredIncludeArchived = normalizeIncludeArchived(searchParams.get("include_archived"));
  const searchQuery = useSafetySearch(
    deferredQuery,
    deferredRecordType,
    deferredIncludeArchived,
    deferredQuery.length >= 3,
  );
  const loading = searchQuery.isLoading;
  const error =
    searchQuery.error instanceof Error ? searchQuery.error.message : null;

  useEffect(() => {
    const nextQuery = String(searchParams.get("q") ?? "").trim();
    const nextRecordType = normalizeRecordType(searchParams.get("record_type"));
    const nextIncludeArchived = normalizeIncludeArchived(searchParams.get("include_archived"));
    setQueryInput(nextQuery);
    setRecordType(nextRecordType);
    setIncludeArchived(nextIncludeArchived);

    if (nextQuery.length === 0) {
      setResponse(createEmptyResponse("", nextRecordType, nextIncludeArchived));
      return;
    }

    if (nextQuery.length < 3) {
      setResponse(createEmptyResponse(nextQuery, nextRecordType, nextIncludeArchived));
      return;
    }
  }, [searchParams]);

  useEffect(() => {
    if (searchQuery.data) {
      setResponse(searchQuery.data);
    }
  }, [searchQuery.data]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextParams = new URLSearchParams();
    const trimmedQuery = queryInput.trim();
    if (trimmedQuery.length > 0) {
      nextParams.set("q", trimmedQuery);
    }
    if (recordType !== "ALL") {
      nextParams.set("record_type", recordType);
    }
    if (includeArchived) {
      nextParams.set("include_archived", "true");
    }
    setSearchParams(nextParams);
  }

  return (
    <section className="space-y-6">
      <header className="rounded-[2rem] border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_45%,#dbeafe_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Search
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">Safety Search</h1>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
          Step 8.8 resolves the earlier fallback with the platform SQL Server full-text engine while keeping the
          grouped cross-record search surface and archive opt-in unchanged for users.
        </p>
      </header>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_260px_auto]">
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Query
              </span>
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500"
                onChange={(event) => setQueryInput(event.target.value)}
                placeholder="Search narrative, title, and description fields"
                type="search"
                value={queryInput}
              />
            </label>

            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Record Type
              </span>
              <select
                className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500"
                onChange={(event) => setRecordType(normalizeRecordType(event.target.value))}
                value={recordType}
              >
                {searchTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <button
              className="self-end rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
              type="submit"
            >
              Search
            </button>
          </div>

          <SafetyArchiveOptInToggle
            checked={includeArchived}
            onChange={setIncludeArchived}
          />

          <div className="grid gap-3 lg:grid-cols-4">
            {searchTypeOptions.map((option) => (
              <article
                key={option.value}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
              >
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {option.label}
                </div>
                <div className="mt-2 text-sm leading-6 text-slate-700">{option.description}</div>
              </article>
            ))}
          </div>
        </form>
      </section>

      <SafetyCrossRecordResults error={error} loading={loading} response={response} />
    </section>
  );
}
