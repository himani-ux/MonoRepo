import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  useMscmepc3Position,
} from "../../../src/hooks/safety/use-msc-mepc3-position";

describe("useMscmepc3Position", () => {
  it("stays idle when vessel or timestamp is missing", () => {
    const fetcher = vi.fn();
    const { result } = renderHook(() => useMscmepc3Position({ fetcher }));

    expect(result.current.status).toBe("idle");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("returns a matched auto-fill payload when the fetch succeeds", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      awaiting_daily_report_match: false,
      delta_minutes: 180,
      latitude: 9.216667,
      longitude: 115.583333,
      matched: true,
      message: "Position auto-filled from Daily Report NoonReport:11560.",
      position_daily_report_id: "NoonReport:11560",
      position_source: "AUTO_FROM_DAILY_REPORT",
      report_date: "2026-04-27T09:00:00Z",
      source_reference: "NoonReport:11560",
      source_table: "NoonReport",
    });

    const { result } = renderHook(() =>
      useMscmepc3Position({
        fetcher,
        occurredAt: "2026-04-27T12:00:00Z",
        vesselId: "EBK",
      }),
    );

    await waitFor(() => expect(result.current.status).toBe("matched"));

    expect(result.current.data?.position_daily_report_id).toBe("NoonReport:11560");
    expect(result.current.data?.latitude).toBe(9.216667);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});

