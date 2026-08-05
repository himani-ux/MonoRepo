import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, MemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import SafetyAuditorExportRoute from "../../../src/routes/safety/admin/auditor-export";
import { safetyRoutes } from "../../../src/routes/safety";

const safetyApiMocks = vi.hoisted(() => ({
  exportAuditorBundle: vi.fn(),
  getIncidentRegisterVessels: vi.fn(),
}));

vi.mock("../../../src/lib/api/safety", async () => {
  const actual = await vi.importActual<typeof import("../../../src/lib/api/safety")>(
    "../../../src/lib/api/safety",
  );
  return {
    ...actual,
    safetyApi: {
      ...actual.safetyApi,
      exportAuditorBundle: safetyApiMocks.exportAuditorBundle,
      getIncidentRegisterVessels: safetyApiMocks.getIncidentRegisterVessels,
    },
  };
});

describe("Safety auditor export route", () => {
  beforeEach(() => {
    safetyApiMocks.exportAuditorBundle.mockReset();
    safetyApiMocks.getIncidentRegisterVessels.mockReset();
    safetyApiMocks.exportAuditorBundle.mockResolvedValue({
      blob: new Blob(["zip"], { type: "application/zip" }),
      fileName: "safety-auditor-bundle.zip",
    });
    safetyApiMocks.getIncidentRegisterVessels.mockResolvedValue([
      {
        id: "vessel-1",
        vessel_code: "YCF",
        vessel_name: "Yellow Chief",
      },
    ]);
  });

  it("renders a vessel dropdown on the auditor export route for Master users with SAF_F_020", async () => {
    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_020"], role: "MASTER" }}>
        <MemoryRouter>
          <SafetyAuditorExportRoute />
        </MemoryRouter>
      </SafetyAuthProvider>,
    );

    expect(
      await screen.findByRole("heading", { name: "Auditor Bundle Export" }),
    ).toBeInTheDocument();
    expect(await screen.findByRole("option", { name: "YCF - Yellow Chief" })).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("SOI"));
    fireEvent.change(screen.getByLabelText("Vessel filter"), {
      target: { value: "vessel-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Build auditor bundle" }));

    await waitFor(() => {
      expect(safetyApiMocks.exportAuditorBundle).toHaveBeenCalledWith(
        expect.objectContaining({
          record_types: ["INCIDENT", "NEAR_MISS", "SCM"],
          vessel_id: "vessel-1",
        }),
      );
    });
  });

  it("hides the auditor export route when the dedicated form gate is missing", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/admin/auditor-export"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_006"], role: "MASTER" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Auditor Bundle Export" }),
    ).not.toBeInTheDocument();
  });

  it("hides the auditor export route when the role gate is neither Master nor DPA", () => {
    const router = createMemoryRouter(safetyRoutes, {
      initialEntries: ["/admin/auditor-export"],
    });

    render(
      <SafetyAuthProvider value={{ formIds: ["SAF_F_020"], role: "FM" }}>
        <RouterProvider router={router} />
      </SafetyAuthProvider>,
    );

    expect(
      screen.queryByRole("heading", { name: "Auditor Bundle Export" }),
    ).not.toBeInTheDocument();
  });
});
