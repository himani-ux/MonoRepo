import { Navigate, useParams } from "react-router-dom";

export default function SafetyIncidentPhase4PlacesPage() {
  const { id } = useParams();
  return <Navigate replace to={`/safety/incidents/${id}/phase-4/paper`} />;
}
