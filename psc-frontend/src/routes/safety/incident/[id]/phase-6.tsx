import IncidentPhaseSwitcher from "../../../../components/safety/incident/incident-phase-switcher";
import SafetyIncidentPhase6 from "../../../../components/safety/incident/phase-6-workspace";

export default function SafetyIncidentPhase6Page() {
  return (
    <section className="space-y-6">
      <IncidentPhaseSwitcher activePhase={3} />
      <SafetyIncidentPhase6 />
    </section>
  );
}
