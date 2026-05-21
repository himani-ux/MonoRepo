import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SafetyIncidentPhase2Form } from "../../../src/components/safety/incident/phase2-form";

describe("SafetyIncidentPhase2Form", () => {
  it("renders the Phase 2 heading and keeps submit disabled until gate fields are complete", () => {
    render(<SafetyIncidentPhase2Form incidentId="42" />);

    expect(
      screen.getByRole("heading", { name: "Notifications + Resource Allocation" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Submit to office" })).toBeDisabled();
  });

  it("enables submit when band, classifier, pic, and position are present", () => {
    render(<SafetyIncidentPhase2Form incidentId="42" />);

    fireEvent.change(screen.getByLabelText("Internal risk band"), {
      target: { value: "YELLOW" },
    });
    fireEvent.change(screen.getByLabelText("IMO classifier"), {
      target: { value: "MI" },
    });
    fireEvent.change(screen.getByLabelText("PIC user ID"), {
      target: { value: "pic-9" },
    });
    fireEvent.change(screen.getByLabelText("Latitude"), {
      target: { value: "12.345678" },
    });
    fireEvent.change(screen.getByLabelText("Longitude"), {
      target: { value: "103.456789" },
    });

    expect(screen.getByRole("button", { name: "Submit to office" })).toBeEnabled();
  });

  it("shows the external expert prompt panel for RED incidents", () => {
    const onSubmitPhase = vi.fn();

    render(
      <SafetyIncidentPhase2Form incidentId="42" onSubmitPhase={onSubmitPhase} />,
    );

    fireEvent.change(screen.getByLabelText("Internal risk band"), {
      target: { value: "RED" },
    });

    expect(
      screen.getByRole("heading", { name: "External expert engagement prompt" }),
    ).toBeInTheDocument();
  });
});
