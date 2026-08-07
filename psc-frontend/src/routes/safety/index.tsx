import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, type RouteObject } from "react-router-dom";

import { PermissionGate, ProcessGate, RoleGate } from "../../components/safety/shared/permission-gate";
import { useSafetyAuth } from "../../hooks/safety/use-auth";
import SafetyLayout from "./layout";

interface SafetyPlaceholderProps {
  description: string;
  title: string;
}

function SafetyRoutePlaceholderPage({
  description,
  title,
}: SafetyPlaceholderProps) {
  return (
    <section
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      data-testid={`safety-page-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
    >
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
    </section>
  );
}

function renderWithSuspense(node: ReactNode) {
  return (
    <Suspense
      fallback={
        <SafetyRoutePlaceholderPage
          description="Loading Safety page."
          title="Loading"
        />
      }
    >
      {node}
    </Suspense>
  );
}

const SafetyIncidentIndexRoute = lazy(() => import("./incident"));
const SafetyIncidentCreateRoute = lazy(() => import("./incident/new"));
const SafetyIncidentPhase1Route = lazy(() => import("./incident/[id]/phase-1"));
const SafetyIncidentPhase2Route = lazy(() => import("./incident/[id]/phase-2"));
const SafetyIncidentPhase3Route = lazy(() => import("./incident/[id]/phase-3"));
const SafetyIncidentPreventiveActionRoute = lazy(() => import("./incident/[id]/phase-3/preventive"));
const SafetyIncidentLessonsLearnedRoute = lazy(() => import("./incident/[id]/phase-3/lessons"));
const SafetyIncidentPhase4Route = lazy(() => import("./incident/[id]/phase-4"));
const SafetyIncidentPhase5Route = lazy(() => import("./incident/[id]/phase-5"));
const SafetyIncidentPhase6Route = lazy(() => import("./incident/[id]/phase-6"));
const SafetyIncidentPhase7Route = lazy(() => import("./incident/[id]/phase-7"));
const SafetyIncidentPhase8Route = lazy(() => import("./incident/[id]/phase-8"));
const SafetyIncidentPhase9Route = lazy(() => import("./incident/[id]/phase-9"));
const SafetyIncidentPdfRoute = lazy(() => import("./incident/[id]/pdf/index"));
const SafetyIncidentMscMepc3Route = lazy(() => import("./incident/[id]/pdf/mscmepc3"));
const SafetyAuditorExportRoute = lazy(() => import("./admin/auditor-export"));
const SafetyAdminIndexRoute = lazy(() => import("./admin/index"));
const SafetyAdminTaxonomyRoute = lazy(() => import("./admin/taxonomy"));
const SafetyAdminCaseStudiesRoute = lazy(() => import("./admin/case-studies"));
const SafetyIncidentClosureRoute = lazy(() => import("./incident/[id]/closure"));
const SafetyIncidentAuditRoute = lazy(() => import("./incident/[id]/audit"));
const SafetyIncidentReopenRoute = lazy(() => import("./incident/[id]/reopen"));
const SafetyNearMissIndexRoute = lazy(() => import("./near-miss"));
const SafetyNearMissCreateRoute = lazy(() => import("./near-miss/create"));
const SafetyNearMissDetailRoute = lazy(() => import("./near-miss/[id]"));
const SafetyNearMissAuditRoute = lazy(() => import("./near-miss/[id]/audit"));
const SafetyNearMissClosureRoute = lazy(() => import("./near-miss/[id]/closure"));
const SafetyNearMissFleetAlertRoute = lazy(() => import("./near-miss/[id]/fleet-alert"));
const SafetyNearMissPdfRoute = lazy(() => import("./near-miss/[id]/pdf/index"));
const SafetyNearMissReviewRoute = lazy(() => import("./near-miss/[id]/review"));
const SafetyNearMissReworkRoute = lazy(() => import("./near-miss/[id]/rework"));
const SafetyNearMissOfficeCommentsRoute = lazy(() => import("./near-miss/[id]/office-comments"));
const SafetyDashboardRoute = lazy(() => import("./dashboard/index"));
const SafetySearchRoute = lazy(() => import("./search/index"));
const SafetyScmCreateAdHocRoute = lazy(() => import("./scm/create-adhoc"));
const SafetyScmCreateRegularRoute = lazy(() => import("./scm/create-regular"));
const SafetyScmAgendaRoute = lazy(() => import("./scm/[id]/agenda"));
const SafetyScmAttendanceRoute = lazy(() => import("./scm/[id]/attendance"));
const SafetyScmClosedSinceLastRoute = lazy(() => import("./scm/[id]/closed-since-last"));
const SafetyScmDetailRoute = lazy(() => import("./scm/[id]/index"));
const SafetyScmEditRoute = lazy(() => import("./scm/[id]/edit"));
const SafetyScmIndexRoute = lazy(() => import("./scm"));
const SafetyScmPdfRoute = lazy(() => import("./scm/[id]/pdf/index"));
const SafetySoiCreateRoute = lazy(() => import("./soi/create"));
const SafetySoiApplicabilityApproveRoute = lazy(() => import("./soi/[id]/applicability/approve"));
const SafetySoiApplicabilityRequestRoute = lazy(() => import("./soi/[id]/applicability/request"));
const SafetySoiCloseRoute = lazy(() => import("./soi/[id]/close"));
const SafetySoiDownloadRoute = lazy(() => import("./soi/[id]/download"));
const SafetySoiFindingCreateRoute = lazy(() => import("./soi/[id]/findings/create"));
const SafetySoiFindingDetailRoute = lazy(() => import("./soi/[id]/findings/[findId]"));
const SafetySoiFindingsRoute = lazy(() => import("./soi/[id]/findings/index"));
const SafetySoiIndexRoute = lazy(() => import("./soi"));
const SafetySoiPickAreasRoute = lazy(() => import("./soi/[id]/pick-areas"));
const SafetySoiPdfRoute = lazy(() => import("./soi/[id]/pdf/index"));
const SafetyIncidentCorrectiveActionsRoute = lazy(
  () => import("./incident/[id]/corrective-actions/index"),
);
const SafetyIncidentPhase4PeopleRoute = lazy(() => import("./incident/[id]/phase-4/people"));
const SafetyIncidentPhase4PlacesRoute = lazy(() => import("./incident/[id]/phase-4/places"));
const SafetyIncidentPhase4PartsRoute = lazy(() => import("./incident/[id]/phase-4/parts"));
const SafetyIncidentPhase4PaperRoute = lazy(() => import("./incident/[id]/phase-4/paper"));
const SafetyIncidentPhase4PhotosRoute = lazy(() => import("./incident/[id]/phase-4/photos"));
const SafetyIncidentPhase4InterviewsRoute = lazy(() => import("./incident/[id]/phase-4/interviews"));

export const safetyRoutePermissions = {
  auditorExport: "SAF_F_020",
  admin: "SAF_F_018",
  dashboard: "SAF_F_015",
  incidents: "SAF_F_001",
  nearMiss: "SAF_F_002",
  scm: "SAF_F_003",
  search: "SAF_F_005",
  soi: "SAF_F_004",
  soiApplicability: "SAF_F_013",
} as const;

const safetyRouteCandidates = [
  { formId: safetyRoutePermissions.dashboard, href: "dashboard" },
  { formId: safetyRoutePermissions.incidents, href: "incidents" },
  { formId: safetyRoutePermissions.nearMiss, href: "near-miss" },
  { formId: safetyRoutePermissions.scm, href: "scm" },
  { formId: safetyRoutePermissions.soi, href: "soi" },
  { formId: safetyRoutePermissions.soiApplicability, href: "soi" },
  { formId: safetyRoutePermissions.search, href: "search" },
  { formId: safetyRoutePermissions.admin, href: "admin" },
  { formId: safetyRoutePermissions.auditorExport, href: "admin/auditor-export" },
] as const;

function SafetyIndexRedirect() {
  const auth = useSafetyAuth();
  const destination =
    safetyRouteCandidates.find((candidate) => auth.hasForm(candidate.formId))?.href ?? "dashboard";

  return <Navigate replace to={destination} />;
}

function SafetySoiRecordRedirect() {
  const { id } = useParams();
  return <Navigate replace to={`/safety/soi/${id}/findings`} />;
}

export const safetyRoutes: RouteObject[] = [
  {
    children: [
      {
        element: <SafetyIndexRedirect />,
        index: true,
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <ProcessGate processId="SAF_P_001">
              <RoleGate roles={["MASTER", "CO", "CE", "2E", "2/E"]}>
                <SafetyIncidentCreateRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "incidents/create",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase1Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-1",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase2Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/office-communication",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase2Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/resource-handoff",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase5Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-2",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase3Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-3",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPreventiveActionRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-3/preventive",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentLessonsLearnedRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-3/lessons",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentCorrectiveActionsRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/corrective-actions",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase7Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-5",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <ProcessGate processId="SAF_P_023">
              <SafetyIncidentPdfRoute />
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "incidents/:id/pdf/incident",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <ProcessGate processId="SAF_P_023">
              <RoleGate roles={["DPA"]}>
                <SafetyIncidentMscMepc3Route />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "incidents/:id/pdf/mscmepc3",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase8Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-6",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase9Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-7",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase8Route />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-6/verification",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentClosureRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/closure",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentAuditRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/audit",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentReopenRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/reopen",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4PeopleRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4/people",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4PlacesRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4/places",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4PartsRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4/parts",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4PaperRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4/paper",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4PhotosRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4/photos",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentPhase4InterviewsRoute />
          </PermissionGate>,
        ),
        path: "incidents/:id/phase-4/interviews",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <ProcessGate processId="SAF_P_001">
              <RoleGate roles={["CO", "MASTER"]}>
                <SafetyScmCreateRegularRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "scm/create-regular",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <ProcessGate processId="SAF_P_001">
              <RoleGate roles={["CO", "MASTER"]}>
                <SafetyScmCreateAdHocRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "scm/create-adhoc",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <SafetyScmDetailRoute />
          </PermissionGate>,
        ),
        path: "scm/:id",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <ProcessGate processId="SAF_P_002">
              <RoleGate roles={["CO", "MASTER"]}>
                <SafetyScmAgendaRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "scm/:id/agenda",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <ProcessGate processId="SAF_P_002">
              <RoleGate roles={["CO", "MASTER"]}>
                <SafetyScmEditRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "scm/:id/edit",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <RoleGate roles={["CO", "MASTER"]}>
              <SafetyScmAttendanceRoute />
            </RoleGate>
          </PermissionGate>,
        ),
        path: "scm/:id/attendance",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <ProcessGate processId="SAF_P_023">
              <SafetyScmPdfRoute />
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "scm/:id/pdf",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <SafetyScmClosedSinceLastRoute />
          </PermissionGate>,
        ),
        path: "scm/:id/closed-since-last",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.scm}>
            <SafetyScmIndexRoute />
          </PermissionGate>,
        ),
        path: "scm",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <ProcessGate processId="SAF_P_001">
              <SafetyNearMissCreateRoute />
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "near-miss/create",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <ProcessGate processId="SAF_P_024">
              <RoleGate roles={["DPA"]}>
                <SafetyNearMissFleetAlertRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "near-miss/:id/fleet-alert",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <ProcessGate processId="SAF_P_023">
              <SafetyNearMissPdfRoute />
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "near-miss/:id/pdf",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <SafetyNearMissReviewRoute />
          </PermissionGate>,
        ),
        path: "near-miss/:id/review",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <ProcessGate processId="SAF_P_001">
              <SafetyNearMissReworkRoute />
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "near-miss/:id/rework",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <SafetyNearMissOfficeCommentsRoute />
          </PermissionGate>,
        ),
        path: "near-miss/:id/office-comments",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <SafetyNearMissClosureRoute />
          </PermissionGate>,
        ),
        path: "near-miss/:id/closure",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <SafetyNearMissAuditRoute />
          </PermissionGate>,
        ),
        path: "near-miss/:id/audit",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <SafetyNearMissDetailRoute />
          </PermissionGate>,
        ),
        path: "near-miss/:id",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.nearMiss}>
            <SafetyNearMissIndexRoute />
          </PermissionGate>,
        ),
        path: "near-miss",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <ProcessGate processId="SAF_P_001">
              <RoleGate roles={["SO", "SAFETY OFFICER", "CO", "CHIEF OFFICER", "2E", "2/E", "SECOND ENGINEER"]}>
                <SafetySoiCreateRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/create",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <ProcessGate processId="SAF_P_001">
              <RoleGate roles={["SO", "SAFETY OFFICER", "CO", "CHIEF OFFICER", "2E", "2/E", "SECOND ENGINEER"]}>
                <SafetySoiDownloadRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/download",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <ProcessGate processId="SAF_P_004">
              <RoleGate roles={["MASTER"]}>
                <SafetySoiCloseRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/close",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soiApplicability}>
            <ProcessGate processId="SAF_P_016">
              <RoleGate roles={["MASTER"]}>
                <SafetySoiApplicabilityRequestRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/applicability/request",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soiApplicability}>
            <ProcessGate processId="SAF_P_017">
              <RoleGate roles={["DPA"]}>
                <SafetySoiApplicabilityApproveRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/applicability/approve",
      },
      {
        element: <SafetySoiRecordRedirect />,
        path: "soi/:id",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <SafetySoiFindingsRoute />
          </PermissionGate>,
        ),
        path: "soi/:id/findings",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <ProcessGate processId="SAF_P_002">
              <RoleGate roles={["SO", "SAFETY OFFICER", "CO", "CHIEF OFFICER", "2E", "2/E", "SECOND ENGINEER"]}>
                <SafetySoiFindingCreateRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/findings/create",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <ProcessGate processId="SAF_P_023">
              <SafetySoiPdfRoute />
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/pdf",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <SafetySoiFindingDetailRoute />
          </PermissionGate>,
        ),
        path: "soi/:id/findings/:findId",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <ProcessGate processId="SAF_P_001">
              <RoleGate roles={["SO", "SAFETY OFFICER", "CO", "CHIEF OFFICER", "2E", "2/E", "SECOND ENGINEER"]}>
                <SafetySoiPickAreasRoute />
              </RoleGate>
            </ProcessGate>
          </PermissionGate>,
        ),
        path: "soi/:id/pick-areas",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.soi}>
            <SafetySoiIndexRoute />
          </PermissionGate>,
        ),
        path: "soi",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.incidents}>
            <SafetyIncidentIndexRoute />
          </PermissionGate>,
        ),
        path: "incidents/*",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.dashboard}>
            <SafetyDashboardRoute />
          </PermissionGate>,
        ),
        path: "dashboard/*",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.search}>
            <SafetySearchRoute />
          </PermissionGate>,
        ),
        path: "search/*",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.auditorExport}>
            <RoleGate roles={["MASTER", "DPA"]}>
              <SafetyAuditorExportRoute />
            </RoleGate>
          </PermissionGate>,
        ),
        path: "admin/auditor-export",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.admin}>
            <RoleGate roles={["DPA"]}>
              <SafetyAdminIndexRoute />
            </RoleGate>
          </PermissionGate>,
        ),
        path: "admin",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.admin}>
            <RoleGate roles={["DPA"]}>
              <SafetyAdminTaxonomyRoute />
            </RoleGate>
          </PermissionGate>,
        ),
        path: "admin/taxonomy",
      },
      {
        element: renderWithSuspense(
          <PermissionGate formId={safetyRoutePermissions.admin}>
            <RoleGate roles={["DPA"]}>
              <SafetyAdminCaseStudiesRoute />
            </RoleGate>
          </PermissionGate>,
        ),
        path: "admin/case-studies",
      },
    ],
    element: <SafetyLayout />,
  },
];

export default safetyRoutes;
