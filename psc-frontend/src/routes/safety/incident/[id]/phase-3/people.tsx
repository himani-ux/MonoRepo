import { Navigate, useParams } from "react-router-dom";

export default function SafetyIncidentPhase3PeoplePage() {
  const { id } = useParams();
  return <Navigate replace to={`/safety/incidents/${id}/phase-3`} />;
}
