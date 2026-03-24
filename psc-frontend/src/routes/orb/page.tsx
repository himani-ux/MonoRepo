import { Navigate } from 'react-router-dom';
import { RootLayout } from '@/components/layout/root-layout';
import { useAuth } from '@/hooks/use-auth';
import { LegacyBasicProvider } from '@/legacy/vims-basic/module-provider';
import OrbRoutes from '@/legacy/vims-basic/routes/orb/OrbRoutes.jsx';
import { ROUTES } from '@/lib/utils/constants';
import OfficeORBApprovedEntriesPage from './office-approved-entries';

export function ORBModulePage() {
  const { isAuthenticated, isOffice, isVessel } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  if (isVessel) {
    return (
      <LegacyBasicProvider>
        <RootLayout>
          <OrbRoutes />
        </RootLayout>
      </LegacyBasicProvider>
    );
  }

  if (isOffice) {
    return (
      <RootLayout>
        <OfficeORBApprovedEntriesPage />
      </RootLayout>
    );
  }

  return <Navigate to={ROUTES.DASHBOARD} replace />;
}
