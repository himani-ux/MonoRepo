import { beforeEach, describe, expect, it } from "vitest";

import {
  buildSafetyDashboardPeriodScopeKey,
  DEFAULT_SAFETY_DASHBOARD_PERIOD,
  SAFETY_DASHBOARD_PERIOD_STORAGE_KEY,
  useSafetyDashboardPeriodStore,
} from "../../../src/stores/safety/dashboard-period-store";

describe("dashboard period persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    useSafetyDashboardPeriodStore.getState().reset();
  });

  it("stores dashboard period selections independently per user scope", () => {
    const dpaScope = buildSafetyDashboardPeriodScopeKey({
      id: 42,
      role: "DPA",
      vesselIds: [7],
    });
    const fmScope = buildSafetyDashboardPeriodScopeKey({
      id: 77,
      role: "FM",
      vesselIds: [9],
    });

    useSafetyDashboardPeriodStore.getState().bindScope(dpaScope);
    useSafetyDashboardPeriodStore.getState().setPeriod("12M");
    expect(useSafetyDashboardPeriodStore.getState().period).toBe("12M");

    useSafetyDashboardPeriodStore.getState().bindScope(fmScope);
    expect(useSafetyDashboardPeriodStore.getState().period).toBe(
      DEFAULT_SAFETY_DASHBOARD_PERIOD,
    );

    useSafetyDashboardPeriodStore.getState().setPeriod("90D");
    useSafetyDashboardPeriodStore.getState().bindScope(dpaScope);
    expect(useSafetyDashboardPeriodStore.getState().period).toBe("12M");

    expect(
      JSON.parse(localStorage.getItem(SAFETY_DASHBOARD_PERIOD_STORAGE_KEY) ?? "{}"),
    ).toMatchObject({
      state: {
        periodByScope: {
          [dpaScope]: "12M",
          [fmScope]: "90D",
        },
      },
    });
  });

  it("falls back to 3Y when persisted storage contains an invalid period", async () => {
    const scopeKey = buildSafetyDashboardPeriodScopeKey({
      id: 42,
      role: "DPA",
      vesselIds: [7],
    });

    localStorage.setItem(
      SAFETY_DASHBOARD_PERIOD_STORAGE_KEY,
      JSON.stringify({
        state: {
          periodByScope: {
            [scopeKey]: "INVALID",
          },
        },
        version: 1,
      }),
    );

    await useSafetyDashboardPeriodStore.persist.rehydrate();
    useSafetyDashboardPeriodStore.getState().bindScope(scopeKey);

    expect(useSafetyDashboardPeriodStore.getState().period).toBe(
      DEFAULT_SAFETY_DASHBOARD_PERIOD,
    );
  });
});
