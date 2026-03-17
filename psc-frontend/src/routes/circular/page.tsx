import { Navigate } from 'react-router-dom';
import { RootLayout } from '@/components/layout/root-layout';
import { useAuth } from '@/hooks/use-auth';
import { LegacyBasicProvider } from '@/legacy/vims-basic/module-provider';
import CircularRoutes from '@/legacy/vims-basic/routes/circular/CircularRoutes.jsx';
import { ROUTES } from '@/lib/utils/constants';

export function CircularModulePage() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return (
    <LegacyBasicProvider>
      <RootLayout>
        <CircularRoutes />
      </RootLayout>
    </LegacyBasicProvider>
  );
}
