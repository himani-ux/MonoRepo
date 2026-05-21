import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafetyIncidentPhase1Form } from "../../../src/components/safety/incident/phase1-form";

const useMscmepc3PositionMock = vi.fn();

vi.mock("../../../src/hooks/safety/use-msc-mepc3-position", () => ({
  toUtcIsoTimestamp: (value: string | null | undefined) =>
    value ? "2026-04-20T10:00:00.000Z" : null,
  useMscmepc3Position: () => useMscmepc3PositionMock(),
}));

describe("SafetyIncidentPhase1Form", () => {
  beforeEach(() => {
    useMscmepc3PositionMock.mockReturnValue({
      data: null,
      error: null,
      refresh: vi.fn(),
      status: "idle",
    });
  });

  it("renders the Phase 1 heading and keeps submit disabled until gate fields are complete", () => {
    render(<SafetyIncidentPhase1Form mode="create" />);

    expect(
      screen.getByRole("heading", { name: "Intake + Scene Control" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Continue to Phase 2" }),
    ).toBeDisabled();
  });

  it("enables submit when the Phase 1 gate fields are filled", () => {
    render(<SafetyIncidentPhase1Form mode="create" />);

    fireEvent.change(screen.getByLabelText("Vessel ID"), {
      target: { value: "7" },
    });
    fireEvent.click(screen.getByLabelText("Checklist complete"));
    fireEvent.change(screen.getByLabelText("Reporter user ID"), {
      target: { value: "master-7" },
    });
    fireEvent.change(screen.getByLabelText("Reporter name"), {
      target: { value: "Master Seven" },
    });
    fireEvent.change(screen.getByLabelText("Reporter rank"), {
      target: { value: "MASTER" },
    });
    fireEvent.change(screen.getByLabelText("Narrative"), {
      target: { value: `Narrative ${"details ".repeat(30)}` },
    });

    const submitButton = screen.getByRole("button", {
      name: "Continue to Phase 2",
    });

    expect(submitButton).toBeEnabled();
  });

  it("opens the self-report conflict modal when reporter and PIC candidate match", () => {
    const onSubmitPhase = vi.fn();

    render(
      <SafetyIncidentPhase1Form
        mode="create"
        onSubmitPhase={onSubmitPhase}
      />,
    );

    fireEvent.change(screen.getByLabelText("Vessel ID"), {
      target: { value: "7" },
    });
    fireEvent.click(screen.getByLabelText("Checklist complete"));
    fireEvent.change(screen.getByLabelText("Reporter user ID"), {
      target: { value: "master-7" },
    });
    fireEvent.change(screen.getByLabelText("Reporter name"), {
      target: { value: "Master Seven" },
    });
    fireEvent.change(screen.getByLabelText("Reporter rank"), {
      target: { value: "MASTER" },
    });
    fireEvent.change(screen.getByLabelText("PIC candidate"), {
      target: { value: "master-7" },
    });
    fireEvent.change(screen.getByLabelText("Narrative"), {
      target: { value: `Narrative ${"details ".repeat(30)}` },
    });

    fireEvent.click(screen.getByRole("button", { name: "Continue to Phase 2" }));

    expect(
      screen.getByRole("heading", { name: "Different approver required" }),
    ).toBeInTheDocument();
    expect(onSubmitPhase).not.toHaveBeenCalled();
  });

  it("renders the Daily Report auto-fill banner when a suggested position is available", () => {
    useMscmepc3PositionMock.mockReturnValue({
      data: {
        awaiting_daily_report_match: false,
        delta_minutes: 180,
        latitude: 9.216667,
        longitude: 115.583333,
        matched: true,
        message:
          "Position auto-filled from Daily Report NoonReport:11560. Edit if a more recent position is available.",
        position_daily_report_id: "NoonReport:11560",
        position_source: "AUTO_FROM_DAILY_REPORT",
        report_date: "2026-04-27T09:00:00Z",
        source_reference: "NoonReport:11560",
        source_table: "NoonReport",
      },
      error: null,
      refresh: vi.fn(),
      status: "matched",
    });

    render(<SafetyIncidentPhase1Form mode="create" />);

    expect(
      screen.getByText(/Position auto-filled from Daily Report NoonReport:11560/i),
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("9.216667")).toBeInTheDocument();
    expect(screen.getByDisplayValue("115.583333")).toBeInTheDocument();
  });
});
