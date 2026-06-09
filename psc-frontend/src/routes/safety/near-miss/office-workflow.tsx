import { SafetyNearMissWorkspace } from "../../../components/safety/near-miss/near-miss-workspace";

export function NearMissDetailRoute() {
  return <SafetyNearMissWorkspace mode="detail" />;
}

export function NearMissOfficeCommentsRoute() {
  return <SafetyNearMissWorkspace mode="office-comments" />;
}

export function NearMissReviewRoute() {
  return <SafetyNearMissWorkspace mode="review" />;
}

export function NearMissReworkRoute() {
  return <SafetyNearMissWorkspace mode="rework" />;
}

export function NearMissFleetAlertRoute() {
  return <SafetyNearMissWorkspace mode="fleet-alert" />;
}

export function NearMissClosureRoute() {
  return <SafetyNearMissWorkspace mode="closure" />;
}

export function NearMissAuditRoute() {
  return <SafetyNearMissWorkspace mode="audit" />;
}

export function NearMissPdfRoute() {
  return <SafetyNearMissWorkspace mode="pdf" />;
}
