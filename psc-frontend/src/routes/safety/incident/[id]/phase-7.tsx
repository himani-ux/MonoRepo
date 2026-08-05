import IncidentPhaseSwitcher from "../../../../components/safety/incident/incident-phase-switcher";
import SafetyIncidentPhase7 from "../../../../components/safety/incident/phase-7-workspace";

export default function SafetyIncidentPhase7Route() {
  return (
    <section className="space-y-6">
      <IncidentPhaseSwitcher activePhase={7} />
      <SafetyIncidentPhase7 />
    </section>
  );
}
