import { SafetyNearMissWorkspace } from "../../../components/safety/near-miss/near-miss-workspace";

export function NearMissDetailRoute() {
  return <SafetyNearMissWorkspace mode="detail" />;
}

export function NearMissTriageRoute() {
  return <SafetyNearMissWorkspace mode="triage" />;
}

export function NearMissReviewRoute() {
  return <SafetyNearMissWorkspace mode="review" />;
}

export function NearMissReworkRoute() {
  return <SafetyNearMissWorkspace mode="rework" />;
}

export function NearMissAnalysisRoute() {
  return <SafetyNearMissWorkspace mode="analysis" />;
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
