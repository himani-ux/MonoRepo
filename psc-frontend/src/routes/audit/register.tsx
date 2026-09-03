import { ClipboardCheck, ShipWheel } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { useAuth } from '@/hooks/use-auth';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';

export default function AuditRegisterRoute() {
  const { hasProcess } = useAuth();
  const canRegisterInternal = hasProcess(PROCESS_IDS.AUDIT_CREATE) || hasProcess(PROCESS_IDS.AUDIT_CONDUCT);
  const canRegisterExternal = hasProcess(PROCESS_IDS.AUDIT_REGISTER_EXTERNAL);

  return (
    <RootLayout>
      <div className="space-y-4 p-4 md:p-6">
        <PageHeader
          title="Register Audit"
          subtitle="Choose the registration path for the audit record."
        />

        <div className="grid gap-4 md:grid-cols-2">
          {canRegisterInternal ? (
            <Card>
              <CardHeader>
                <CardTitle>Internal Audit</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-neutral-600">
                  Register a planned or additional internal audit from the Audit Plan Register.
                </p>
                <Button asChild>
                  <Link to="/inspections/new">
                    <ClipboardCheck className="mr-2 h-4 w-4" />
                    Open Internal Audit Form
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ) : null}

          {canRegisterExternal ? (
            <Card>
              <CardHeader>
                <CardTitle>External Audit</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-neutral-600">
                  Register an already completed external audit and attach the external audit report PDF.
                </p>
                <Button asChild>
                  <Link to="/audit/external/new">
                    <ShipWheel className="mr-2 h-4 w-4" />
                    Open External Audit Form
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ) : null}
        </div>

        {!canRegisterInternal && !canRegisterExternal ? (
          <Card>
            <CardContent className="p-4 text-sm text-neutral-600">
              You do not have permission to register audit records.
            </CardContent>
          </Card>
        ) : null}
      </div>
    </RootLayout>
  );
}
