import { Link } from "react-router-dom";

import { formatVesselName } from "../../../lib/safety/vessel-display";

export type SafetySearchGroupKey = "INCIDENT" | "NEAR_MISS" | "SCM" | "SOI_FINDING";

export interface SafetySearchResultItem {
  archived: boolean;
  id: number;
  near_miss_priority?: string | null;
  record_label: string;
  record_type: SafetySearchGroupKey;
  reference: string;
  reporter_name?: string | null;
  route: string;
  snippet: string;
  state: string;
  title: string;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id: string;
  vessel_name?: string | null;
  when: string | null;
}

export interface SafetySearchResponse {
  counts: Record<SafetySearchGroupKey, number>;
  groups: Record<SafetySearchGroupKey, SafetySearchResultItem[]>;
  include_archived: boolean;
  labels: Record<SafetySearchGroupKey, string>;
  query: string;
  record_type: string;
  total_count: number;
}

interface SafetyCrossRecordResultsProps {
  error: string | null;
  loading: boolean;
  response: SafetySearchResponse;
}

const groupOrder: SafetySearchGroupKey[] = ["INCIDENT", "NEAR_MISS", "SCM", "SOI_FINDING"];

function formatWhen(value: string | null) {
  if (!value) {
    return "Date not recorded";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("en-US", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function SafetyCrossRecordResults({
  error,
  loading,
  response,
}: SafetyCrossRecordResultsProps) {
  if (loading) {
    return (
      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
          Search Results
        </div>
        <div className="mt-4 space-y-3" role="status">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-20 animate-pulse rounded-2xl bg-slate-100"
            />
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-[1.75rem] border border-rose-200 bg-rose-50 p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-rose-900">Search unavailable</h2>
        <p className="mt-2 text-sm leading-6 text-rose-700" role="alert">
          {error}
        </p>
      </section>
    );
  }

  if (response.query.length < 3) {
    return (
      <section className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-amber-950">Search terms need at least 3 characters</h2>
        <p className="mt-2 text-sm leading-6 text-amber-800">
          Enter at least 3 characters so the search can return useful fleet-wide matches.
        </p>
      </section>
    );
  }

  if (response.total_count === 0) {
    return (
      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">No matches found</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {response.include_archived
            ? "No matches found in the active or archived Safety records for this search."
            : "No matches. Try including archived records?"}
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <header className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Search Results
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">
              {response.total_count} matching Safety records
            </h2>
          </div>
          <p className="max-w-2xl text-sm leading-6 text-slate-600">
            Showing matches for <code>{response.query}</code> across incidents, near misses, SCM records, and SOI findings
            {response.include_archived ? ", including the current archive window." : "."}
          </p>
        </div>
      </header>

      {groupOrder.map((groupKey) => {
        const items = response.groups[groupKey] ?? [];
        if (items.length === 0) {
          return null;
        }

        return (
          <section
            key={groupKey}
            className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-lg font-semibold text-slate-900">
                {response.labels[groupKey] ?? groupKey}
              </h3>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                {response.counts[groupKey]} hit{response.counts[groupKey] === 1 ? "" : "s"}
              </span>
            </div>

            <div className="mt-4 space-y-3">
              {items.map((item) => (
                <Link
                  key={`${item.record_type}-${item.id}`}
                  className="block rounded-3xl border border-slate-200 bg-slate-50 p-4 transition hover:border-slate-400 hover:bg-white"
                  to={item.route}
                >
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                        <span>{item.record_label}</span>
                        <span className="rounded-full bg-slate-900 px-2 py-1 text-[11px] text-white">
                          {item.state.replaceAll("_", " ")}
                        </span>
                        {item.archived ? (
                          <span className="rounded-full bg-amber-100 px-2 py-1 text-[11px] text-amber-900">
                            Archived
                          </span>
                        ) : null}
                      </div>
                      <h4 className="mt-2 text-lg font-semibold text-slate-900">{item.title}</h4>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{item.snippet}</p>
                    </div>

                    <dl className="grid shrink-0 gap-2 text-sm text-slate-600">
                      <div>
                        <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                          Reference
                        </dt>
                        <dd>{item.reference}</dd>
                      </div>
                      <div>
                        <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                          Vessel
                        </dt>
                        <dd>{formatVesselName(item)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                          Recorded
                        </dt>
                        <dd>{formatWhen(item.when)}</dd>
                      </div>
                      {item.reporter_name ? (
                        <div>
                          <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">
                            Reporter
                          </dt>
                          <dd>{item.reporter_name}</dd>
                        </div>
                      ) : null}
                    </dl>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </section>
  );
}
