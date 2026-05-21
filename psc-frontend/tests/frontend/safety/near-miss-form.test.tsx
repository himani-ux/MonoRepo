import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafetyNearMissForm } from "../../../src/components/safety/near-miss/near-miss-form";

const useAuthMock = vi.fn();
const safetyApiMock = vi.hoisted(() => ({
  getNearMissRateLimit: vi.fn(),
}));

vi.mock("../../../src/hooks/use-auth", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("../../../src/components/safety/shared/reference-pickers", () => ({
  SafetyIncidentTypeSelect: () => <select aria-label="Incident type" />,
  SafetyLossTypeSelect: () => <select aria-label="Loss type" />,
  SafetyMscatPicker: () => <div data-testid="mscat-picker" />,
}));

vi.mock("../../../src/lib/api/safety", () => ({
  safetyApi: {
    getNearMissRateLimit: safetyApiMock.getNearMissRateLimit,
  },
}));

describe("SafetyNearMissForm", () => {
  beforeEach(() => {
    safetyApiMock.getNearMissRateLimit.mockResolvedValue({
      allowed: true,
      guidance_message: "Submission allowance available.",
      limit: 5,
      remaining: 4,
      reset_at: null,
      retry_after_seconds: 0,
      scope: "vessel_local_day",
      used: 1,
    });
  });

  it("auto-fills the reporter block from vessel auth details without editable identity fields", async () => {
    useAuthMock.mockReturnValue({
      isVessel: true,
      user: {
        crew_id: "crew-7",
        first_name: "Asha",
        rank: "CHIEF OFFICER",
        role: "VESSEL_CREW",
        surname: "Kumar",
        vessel_code: "VES007",
        vessel_id: "7",
      },
    });

    render(<SafetyNearMissForm />);

    expect(screen.getByText("crew-7")).toBeInTheDocument();
    expect(screen.getByText("Asha Kumar")).toBeInTheDocument();
    expect(screen.getByText("CHIEF OFFICER")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Reporter user ID" })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Reporter name" })).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Reporter rank" })).not.toBeInTheDocument();
    expect(await screen.findByText(/4 of 5 submissions remain/i)).toBeInTheDocument();
  });

  it("renders occurred time and rate-limit status on the create form", async () => {
    useAuthMock.mockReturnValue({
      isVessel: true,
      user: {
        crew_id: "crew-7",
        first_name: "Asha",
        rank: "CHIEF OFFICER",
        surname: "Kumar",
        vessel_code: "VES007",
        vessel_id: "7",
      },
    });

    render(<SafetyNearMissForm />);

    expect(screen.getByLabelText("Occurred at")).toBeInTheDocument();
    expect(await screen.findByText(/4 of 5 submissions remain/i)).toBeInTheDocument();
  });

  it("shows a non-editable reporter identity warning when auth details are missing", async () => {
    useAuthMock.mockReturnValue({
      isVessel: true,
      user: {
        vessel_code: "VES007",
        vessel_id: "7",
      },
    });

    render(<SafetyNearMissForm />);

    expect(screen.getAllByText("Resolved from login/session")).toHaveLength(3);
    expect(screen.getByText(/Reporter identity will be resolved from login\/session/i)).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Reporter user ID" })).not.toBeInTheDocument();
    expect(await screen.findByText(/4 of 5 submissions remain/i)).toBeInTheDocument();
  });
});
