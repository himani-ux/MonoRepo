import { useParams } from "react-router-dom";

import { SafetyIncidentPhase1Form } from "../../../../components/safety/incident/phase1-form";

export default function SafetyIncidentPhase1Route() {
  const { id } = useParams();
  return <SafetyIncidentPhase1Form incidentId={id ?? "draft"} mode="edit" />;
}
