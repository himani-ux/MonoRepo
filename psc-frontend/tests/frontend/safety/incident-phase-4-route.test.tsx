import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

vi.mock("@/components/layout/root-layout", () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock("../../../src/routes/safety/incident/[id]/phase-3/preventive", () => ({
  default: () => <h1>Preventive Action</h1>,
}));

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe("Safety Phase 4 route", () => {
  it("renders Preventive Action on the current phase-4 path", async () => {
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-3/preventive"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"], role: "MASTER" }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Preventive Action" }),
    ).toBeInTheDocument();
  });
});
