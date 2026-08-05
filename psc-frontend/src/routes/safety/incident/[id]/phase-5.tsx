import IncidentPhaseSwitcher from "../../../../components/safety/incident/incident-phase-switcher";
import SafetyIncidentPhase5 from "../../../../components/safety/incident/phase-5-workspace";

export default function SafetyIncidentPhase5Route() {
  return (
    <section className="space-y-6">
      <IncidentPhaseSwitcher activePhase={2} />
      <SafetyIncidentPhase5 />
    </section>
  );
}
