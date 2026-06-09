/**
 * Root application component with routing setup.
 *
 * Sets up:
 * - React Router with all application routes
 * - Route structure per APP_FLOW.md Section 1
 * - Protected routes with auth guard
 * - Layout components for authenticated pages
 */

import { lazy, Suspense, type ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useRoutes } from 'react-router-dom';
import { LoginPage } from '@/routes/login';
import { useAuthInitializer, useAuth } from '@/hooks/use-auth';
import { SafetyAuthProvider, type SafetyAuthUser } from '@/hooks/safety/use-auth';
import { safetyRoutes } from '@/routes/safety';
import { ROUTES } from '@/lib/utils/constants';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import { Toaster } from '@/components/ui/toaster';
import { AuthGuard } from '@/components/auth/auth-guard';
import { RootLayout } from '@/components/layout/root-layout';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy-loaded route components — code splitting per IMPLEMENTATION_PLAN.md Step 8.4
const InspectionListPage = lazy(() =>
  import('@/routes/inspections').then((m) => ({ default: m.InspectionListPage }))
);
const CreateInspectionPage = lazy(() =>
  import('@/routes/inspections/new').then((m) => ({ default: m.CreateInspectionPage }))
);
const InspectionDetailPage = lazy(() => import('@/routes/inspections/[id]'));
const EditInspectionPage = lazy(() => import('@/routes/inspections/[id].edit'));
const RegisterFollowUpPage = lazy(() => import('@/routes/inspections/[id].follow-up'));
const DashboardPage = lazy(() =>
  import('@/routes/dashboard').then((m) => ({ default: m.DashboardPage }))
);
const DeficiencyDashboardPage = lazy(() =>
  import('@/routes/deficiencies').then((m) => ({ default: m.DeficiencyDashboardPage }))
);
const CARListPage = lazy(() =>
  import('@/routes/cars').then((m) => ({ default: m.CARListPage }))
);
const CARDetailPage = lazy(() => import('@/routes/cars/[id]'));
const EditCARPage = lazy(() => import('@/routes/cars/[id].edit'));
const SyncStatusPage = lazy(() => import('@/routes/sync/page'));
const NotificationsPage = lazy(() => import('@/routes/notifications/page'));
const SettingsPage = lazy(() => import('@/routes/settings/page'));
const ReportsPage = lazy(() => import('@/routes/reports/page'));
const HelpPage = lazy(() => import('@/routes/help/page'));
const CircularModulePage = lazy(() =>
  import('@/routes/circular/page').then((m) => ({ default: m.CircularModulePage }))
);
const ORBModulePage = lazy(() =>
  import('@/routes/orb/page').then((m) => ({ default: m.ORBModulePage }))
);

/**
 * Page-level loading fallback for lazy-loaded routes.
 */
function PageLoadingFallback() {
  return (
    <RootLayout>
      <div className="space-y-4 p-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    </RootLayout>
  );
}

/**
 * Permission guard for routes based on process IDs.
 */
function PermissionGuard({
  children,
  requiredForm,
  requiredProcess,
}: {
  children: ReactNode;
  requiredForm?: string;
  requiredProcess: string;
}) {
  const { hasForm, hasProcess } = useAuth();
  if ((requiredForm && !hasForm(requiredForm)) || !hasProcess(requiredProcess)) {
    return <Navigate to={ROUTES.CARS} replace />;
  }
  return <>{children}</>;
}

/**
 * Smart default redirect — crew goes to CARs, master/office to Dashboard.
 */
function DefaultRedirect() {
  const { hasProcess } = useAuth();
  return (
    <Navigate
      to={hasProcess(PROCESS_IDS.VIEW_DASHBOARD) ? ROUTES.DASHBOARD : ROUTES.CARS}
      replace
    />
  );
}

function SafetyModuleRouter() {
  const { user, formIds, processIds, role, vesselId } = useAuth();
  const element = useRoutes(safetyRoutes);
  const safetyRole = user?.safety_role_name ?? user?.rank ?? user?.role_name ?? role ?? null;
  const normalizedSafetyRole = String(safetyRole ?? "").trim().toUpperCase();
  const hasFleetWideSafetyScope =
    Boolean(user?.has_global_vessel_access) ||
    normalizedSafetyRole === "DPA" ||
    normalizedSafetyRole === "FM" ||
    normalizedSafetyRole === "FLEET MANAGER";
  const scopedVesselIds = hasFleetWideSafetyScope
    ? ['ALL']
    : user?.vessel_ids?.length
      ? user.vessel_ids
      : vesselId
        ? [vesselId]
        : [];
  const scopedVesselNames = hasFleetWideSafetyScope
    ? []
    : user?.vessel_names?.length
      ? user.vessel_names
      : user?.vessel_name
        ? [user.vessel_name]
        : [];
  const safetyAuthUser: SafetyAuthUser = {
    crewId: user?.crew_id,
    displayName: user?.display_name,
    employeeId: user?.employee_id,
    firstName: user?.first_name,
    formIds: [...new Set(formIds.map((id) => String(id).trim().toUpperCase()).filter((id) => id.startsWith('SAF_F_')))],
    fullName: user?.full_name,
    id: user?.id,
    isGlobal: hasFleetWideSafetyScope,
    login_id: user?.login_id,
    processIds: [...new Set(processIds.map((id) => String(id).trim().toUpperCase()).filter((id) => id.startsWith('SAF_P_')))],
    profileId: user?.profile_id ?? user?.profileId ?? user?.office_profile_id,
    role: safetyRole,
    surname: user?.surname,
    userName: user?.username ?? user?.UserName,
    vesselIds: scopedVesselIds,
    vesselNames: scopedVesselNames,
  };

  return <SafetyAuthProvider value={safetyAuthUser}>{element}</SafetyAuthProvider>;
}

/**
 * App shell with auth initialization.
 */
function AppShell() {
  // Initialize auth on app startup
  useAuthInitializer();

  return (
    <>
      <Suspense fallback={<PageLoadingFallback />}>
      <Routes>
        {/* Public routes */}
        <Route path={ROUTES.LOGIN} element={<LoginPage />} />

        {/* Default redirect — crew → /cars, master/office → /dashboard */}
        <Route path="/" element={<AuthGuard><DefaultRedirect /></AuthGuard>} />

        {/* Protected routes */}
        <Route
          path={ROUTES.DASHBOARD}
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_DASHBOARD}>
                <DashboardPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.INSPECTIONS}
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_INSPECTIONS}>
                <InspectionListPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/inspections/new"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.CREATE_INSPECTION}>
                <CreateInspectionPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/inspections/:id"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_INSPECTION_DETAIL}>
                <InspectionDetailPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/inspections/:id/edit"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.EDIT_INSPECTION}>
                <EditInspectionPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/inspections/:id/follow-up"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.SUBMIT_FOLLOW_UP}>
                <RegisterFollowUpPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.DEFICIENCIES}
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_DEFICIENCIES}>
                <DeficiencyDashboardPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.CARS}
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_CARS}>
                <CARListPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/cars/:id"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_CARS}>
                <CARDetailPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/cars/:id/edit"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.EDIT_CAR}>
                <EditCARPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.NOTIFICATIONS}
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_NOTIFICATIONS}>
                <NotificationsPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.SYNC}
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_SYNC}>
                <SyncStatusPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/reports"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_REPORTS}>
                <ReportsPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path="/settings"
          element={
            <AuthGuard>
              <PermissionGuard requiredProcess={PROCESS_IDS.VIEW_SETTINGS}>
                <SettingsPage />
              </PermissionGuard>
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.HELP}
          element={
            <AuthGuard>
              <HelpPage />
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.CIRCULAR + '/*'}
          element={
            <AuthGuard>
              <CircularModulePage />
            </AuthGuard>
          }
        />
        <Route
          path={ROUTES.ORB + '/*'}
          element={
            <AuthGuard>
              <ORBModulePage />
            </AuthGuard>
          }
        />
        <Route
          path="/safety/*"
          element={
            <AuthGuard>
              <SafetyModuleRouter />
            </AuthGuard>
          }
        />

        {/* 404 fallback */}
        <Route
          path="*"
          element={
            <div className="flex min-h-screen flex-col items-center justify-center bg-neutral-50 p-8">
              <h1 className="text-6xl font-bold text-neutral-200">404</h1>
              <p className="mt-4 text-lg text-neutral-500">Page not found</p>
              <a
                href="/"
                className="mt-6 text-primary-500 hover:text-primary-600 hover:underline"
              >
                Return to Dashboard
              </a>
            </div>
          }
        />
      </Routes>
      </Suspense>

      {/* Toast notifications */}
      <Toaster />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}

export default App;
