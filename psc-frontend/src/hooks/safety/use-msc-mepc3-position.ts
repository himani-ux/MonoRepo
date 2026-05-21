import { useEffect, useMemo, useState } from "react";

export interface SafetyMscmepc3PositionPayload {
  awaiting_daily_report_match: boolean;
  delta_minutes: number | null;
  latitude: number | null;
  longitude: number | null;
  matched: boolean;
  message: string;
  position_daily_report_id: string | null;
  position_source: string | null;
  report_date: string | null;
  source_reference: string | null;
  source_table: string | null;
}

export type SafetyMscmepc3PositionStatus =
  | "awaiting"
  | "error"
  | "idle"
  | "loading"
  | "matched";

export interface SafetyMscmepc3PositionState {
  data: SafetyMscmepc3PositionPayload | null;
  error: string | null;
  refresh: () => Promise<void>;
  status: SafetyMscmepc3PositionStatus;
}

export type SafetyMscmepc3PositionFetcher = (args: {
  occurredAt: string;
  signal?: AbortSignal;
  vesselId: string;
}) => Promise<SafetyMscmepc3PositionPayload>;

interface UseMscmepc3PositionOptions {
  enabled?: boolean;
  fetcher?: SafetyMscmepc3PositionFetcher;
  occurredAt?: string | null;
  vesselId?: string | null;
}

async function defaultFetcher({
  occurredAt,
  signal,
  vesselId,
}: {
  occurredAt: string;
  signal?: AbortSignal;
  vesselId: string;
}): Promise<SafetyMscmepc3PositionPayload> {
  const url = new URL("/api/safety/incidents/position-prefill/", window.location.origin);
  url.searchParams.set("vessel_id", vesselId);
  url.searchParams.set("timestamp", occurredAt);

  const response = await fetch(url.toString(), { signal });
  if (!response.ok) {
    throw new Error("Unable to load MSC-MEPC.3 position auto-fill.");
  }

  return (await response.json()) as SafetyMscmepc3PositionPayload;
}

export function toUtcIsoTimestamp(value?: string | Date | null): string | null {
  if (!value) {
    return null;
  }

  const dateValue = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(dateValue.getTime())) {
    return null;
  }

  return dateValue.toISOString();
}

export function useMscmepc3Position({
  enabled = true,
  fetcher = defaultFetcher,
  occurredAt,
  vesselId,
}: UseMscmepc3PositionOptions): SafetyMscmepc3PositionState {
  const [data, setData] = useState<SafetyMscmepc3PositionPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<SafetyMscmepc3PositionStatus>("idle");

  const requestKey = useMemo(
    () => `${vesselId ?? ""}::${occurredAt ?? ""}`,
    [occurredAt, vesselId],
  );

  async function runFetch(signal?: AbortSignal) {
    if (!enabled || !vesselId || !occurredAt) {
      setData(null);
      setError(null);
      setStatus("idle");
      return;
    }

    setStatus("loading");
    setError(null);

    try {
      const result = await fetcher({ occurredAt, signal, vesselId });
      setData(result);
      setStatus(result.matched ? "matched" : "awaiting");
    } catch (fetchError) {
      if (fetchError instanceof DOMException && fetchError.name === "AbortError") {
        return;
      }
      setData(null);
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "Unable to load MSC-MEPC.3 position auto-fill.",
      );
      setStatus("error");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void runFetch(controller.signal);
    return () => controller.abort();
  }, [enabled, fetcher, requestKey]);

  return {
    data,
    error,
    refresh: async () => {
      await runFetch();
    },
    status,
  };
}

