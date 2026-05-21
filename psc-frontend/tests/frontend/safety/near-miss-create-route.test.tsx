import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SafetyNearMissCreatePage from "../../../src/routes/safety/near-miss/create";

const navigateMock = vi.fn();
const toastMock = vi.fn();
const createNearMissMock = vi.fn();
const getNearMissRateLimitMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/hooks/use-auth", () => ({
  useAuth: () => ({
    isVessel: true,
    user: {
      crew_id: "crew-7",
      first_name: "Asha",
      rank: "CHIEF OFFICER",
      surname: "Kumar",
      vessel_code: "VES007",
      vessel_id: "7",
    },
  }),
}));

vi.mock("../../../src/hooks/use-toast", () => ({
  useToast: () => ({
    toast: toastMock,
  }),
}));

vi.mock("../../../src/components/safety/shared/reference-pickers", () => ({
  SafetyIncidentTypeSelect: ({
    onChange,
    value,
  }: {
    onChange: (value: number | null) => void;
    value?: number | null;
  }) => (
    <select aria-label="Incident type" onChange={(event) => onChange(Number(event.target.value) || null)} value={value ?? ""}>
      <option value="">Select incident type</option>
      <option value="1">PERSONAL_NEAR_MISS - Personal near miss</option>
    </select>
  ),
  SafetyLossTypeSelect: ({
    label = "Loss type",
    onChange,
    value,
  }: {
    label?: string;
    onChange: (value: number | null) => void;
    value?: number | null;
  }) => (
    <select aria-label={label} onChange={(event) => onChange(Number(event.target.value) || null)} value={value ?? ""}>
      <option value="">Select loss type</option>
      <option value="1">People</option>
    </select>
  ),
  SafetyMscatPicker: () => <div data-testid="mscat-picker" />,
}));

vi.mock("../../../src/lib/api/safety", () => ({
  safetyApi: {
    createNearMiss: (...args: unknown[]) => createNearMissMock(...args),
    getNearMissRateLimit: (...args: unknown[]) => getNearMissRateLimitMock(...args),
    getReferenceIncidentTypes: vi.fn().mockResolvedValue([
      {
        active: true,
        description: "Fixture incident type",
        id: 1,
        imo_reportable: false,
        type_code: "PERSONAL_NEAR_MISS",
        type_name: "Personal near miss",
      },
    ]),
    getReferenceLossTypes: vi.fn().mockResolvedValue([
      {
        active: true,
        description: "People exposure",
        id: 1,
        loss_type_id: 1,
        loss_type_name: "People",
      },
    ]),
    getReferenceMscat: vi.fn().mockResolvedValue([
      {
        active: true,
        category_id: 10,
        category_name: "Immediate Causes",
        cause_type: "Immediate",
        id: 1,
        subcode_description: "Unsafe condition observed",
        subcode_id: "10.01",
      },
    ]),
  },
}));

describe("SafetyNearMissCreatePage", () => {
  it("submits the near miss and navigates to the detail page", async () => {
    createNearMissMock.mockResolvedValue({ id: 42 });
    getNearMissRateLimitMock.mockResolvedValue({
      allowed: true,
      guidance_message: "Submission allowance available.",
      limit: 5,
      remaining: 5,
      reset_at: null,
      retry_after_seconds: 0,
      scope: "vessel_local_day",
      used: 0,
    });

    render(<SafetyNearMissCreatePage />);

    fireEvent.change(screen.getByLabelText("Occurred at"), {
      target: { value: "2026-05-13T10:30" },
    });
    fireEvent.change(screen.getByLabelText("What happened"), {
      target: { value: `Narrative ${"details ".repeat(20)}` },
    });
    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "MED" },
    });
    fireEvent.change(await screen.findByLabelText("Incident type"), {
      target: { value: "1" },
    });
    fireEvent.change(await screen.findByLabelText("Loss type"), {
      target: { value: "1" },
    });
    fireEvent.change(screen.getByLabelText("Immediate action"), {
      target: { value: "Crew isolated the unsafe condition immediately." },
    });

    await screen.findByText(/5 of 5 submissions remain/i);
    fireEvent.click(screen.getByRole("button", { name: "Submit near miss" }));

    await waitFor(() => {
      expect(createNearMissMock).toHaveBeenCalledWith(
        expect.objectContaining({
          incident_type_id: 1,
          loss_type_primary_id: 1,
          narrative: expect.stringContaining("Narrative"),
          near_miss_immediate_action: "Crew isolated the unsafe condition immediately.",
          near_miss_severity: "MED",
          occurred_at: expect.any(String),
          reporter_name: "Asha Kumar",
          reporter_rank: "CHIEF OFFICER",
          reporter_user_id: "crew-7",
          vessel_code: "VES007",
          vessel_id: "7",
        }),
      );
    });

    expect(toastMock).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Near miss created successfully",
        variant: "success",
      }),
    );
    expect(navigateMock).toHaveBeenCalledWith("/safety/near-miss/42", {
      state: { resultMessage: "Near miss created successfully." },
    });
  });
});
