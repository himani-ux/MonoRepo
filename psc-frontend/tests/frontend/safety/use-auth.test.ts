import { createElement, type PropsWithChildren } from "react";
import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  SafetyAuthProvider,
  useSafetyAuth,
} from "../../../src/hooks/safety/use-auth";

describe("useSafetyAuth", () => {
  it("reports form and process membership accurately", () => {
    const wrapper = ({ children }: PropsWithChildren) =>
      createElement(
        SafetyAuthProvider,
        {
          value: {
            formIds: ["SAF_F_001", "SAF_F_005"],
            isGlobal: true,
            processIds: ["SAF_P_002", "SAF_P_004"],
            role: "DPA",
            vesselIds: [7, 9],
            vesselNames: ["MV Atlas", "MV Beacon"],
          },
        },
        children,
      );

    const { result } = renderHook(() => useSafetyAuth(), { wrapper });

    expect(result.current.hasForm("SAF_F_001")).toBe(true);
    expect(result.current.hasForm("SAF_F_003")).toBe(false);
    expect(result.current.hasProcess("SAF_P_004")).toBe(true);
    expect(result.current.hasProcess("SAF_P_009")).toBe(false);
    expect(result.current.role).toBe("DPA");
    expect(result.current.isGlobal).toBe(true);
    expect(result.current.vesselIds).toEqual([7, 9]);
    expect(result.current.vesselNames).toEqual(["MV Atlas", "MV Beacon"]);
    expect(result.current.scopedVesselLabel).toBe("Global");
  });

  it("uses vessel names for scoped vessel display when available", () => {
    const wrapper = ({ children }: PropsWithChildren) =>
      createElement(
        SafetyAuthProvider,
        {
          value: {
            isGlobal: false,
            role: "MASTER",
            vesselIds: ["EF9029C2-A192-EF11-A9F2-933342524037"],
            vesselNames: ["MV Horizon"],
          },
        },
        children,
      );

    const { result } = renderHook(() => useSafetyAuth(), { wrapper });

    expect(result.current.scopedVesselLabel).toBe("MV Horizon");
  });
});
