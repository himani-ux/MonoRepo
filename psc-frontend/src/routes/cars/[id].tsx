import { useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  MoreVertical,
  Edit,
  FileDown,
} from 'lucide-react';
import {
  Button,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { ErrorState } from '@/components/shared';
import { DetailHeaderSkeleton, SectionSkeleton } from '@/components/shared/loading-skeleton';
import { CARDetail } from '@/components/car/car-detail';
import { CARWorkflowActions } from '@/components/car/car-workflow-actions';
import { EvidenceUploadModal } from '@/components/car/evidence-upload-modal';
import { PhysicalVerificationSection } from '@/components/car/physical-verification-section';
import { PVCreateModal } from '@/components/car/pv-create-modal';
import { PVCloseModal } from '@/components/car/pv-close-modal';
import { useCAR } from '@/hooks/use-cars';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { ROUTES, CAR_STATUS } from '@/lib/utils/constants';
import { exportCARPDF } from '@/lib/api/cars';

/**
 * CAR Detail Page
 *
 * Displays full CAR details with:
 * - Header with CAR number, status, dates
 * - Deficiency section (DefCode prominent)
 * - Root cause analysis + CLC codes
 * - Corrective actions grouped by type
 * - Evidence grouped by type
 * - Activity history (all users)
 * - Audit log (Office/DPA only)
 * - Conditional action buttons by status/role
 */
export default function CARDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, isVessel, isOffice, isDPA } = useAuth();

  // Query
  const { data: car, isLoading, error, refetch } = useCAR(id);

  // Dialog states
  const [showEvidenceUpload, setShowEvidenceUpload] = useState(false);
  const [showPVCreate, setShowPVCreate] = useState(false);
  const [showPVClose, setShowPVClose] = useState(false);
  const [isExportingPDF, setIsExportingPDF] = useState(false);

  // Derived state (unified workflow statuses)
  const status = car?.status;
  const isAllotted = status === CAR_STATUS.ALLOTTED;
  const isInProgress = status === CAR_STATUS.IN_PROGRESS;
  const isReturnedForRework = status === CAR_STATUS.RETURNED_FOR_REWORK;
  const isPendingCE = status === CAR_STATUS.PENDING_CE_REVIEW;
  const isPendingMaster = status === CAR_STATUS.PENDING_MASTER_REVIEW;
  const isClosed = status === CAR_STATUS.CLOSED;
  const isOfficeOrDPA = isOffice || isDPA;

  // Vessel-editable statuses
  const vesselEditable = isAllotted || isInProgress || isPendingCE || isPendingMaster || isReturnedForRework;
  const canEdit = vesselEditable && (isVessel || isOffice);
  const canUploadEvidence = isAllotted || isInProgress || isReturnedForRework;

  // PV permissions per BACKEND_STRUCTURE.md permission matrix
  const pv = car?.physical_verification ?? null;
  const verifierUserId = pv?.verifier_user_id?.trim().toLowerCase();
  const currentUserIds = [user?.employee_id, user?.id]
    .filter((value): value is string => Boolean(value))
    .map((value) => value.trim().toLowerCase());
  const isAssignedVerifier = Boolean(
    verifierUserId && currentUserIds.includes(verifierUserId)
  );
  const canCreatePV = isClosed && isOfficeOrDPA && !pv;
  const canClosePV =
    pv?.status === 'OPEN' && (isDPA || (isOffice && isAssignedVerifier));

  // PDF Export handlers — FEAT-RPT-001
  const handleExportPDF = useCallback(async (audience: 'internal' | 'external') => {
    if (!id) return;
    setIsExportingPDF(true);
    try {
      const blob = await exportCARPDF(id, audience);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const suffix = audience === 'external' ? 'External' : 'Internal';
      link.download = `${car?.car_number?.replace(/-/g, '_') || 'CAR'}_Report_${suffix}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Export failed',
        description: 'Failed to generate PDF report. Please try again.',
      });
    } finally {
      setIsExportingPDF(false);
    }
  }, [id, car?.car_number, toast]);

  // Loading state
  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="CAR Detail" showBack backTo={ROUTES.CARS} />
        <div className="space-y-4">
          <DetailHeaderSkeleton />
          <SectionSkeleton />
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  // Error state
  if (error || !car) {
    return (
      <RootLayout>
        <PageHeader title="CAR Detail" showBack backTo={ROUTES.CARS} />
        <ErrorState
          title="CAR not found"
          message="The CAR may have been deleted or you don't have access."
          onRetry={() => refetch()}
        >
          <Button
            variant="outline"
            onClick={() => navigate(ROUTES.CARS)}
            className="mt-2"
          >
            Go Back
          </Button>
        </ErrorState>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      {/* Header */}
      <PageHeader
        title="CAR Detail"
        showBack
        backTo={ROUTES.CARS}
        actions={
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreVertical className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {canEdit && (
                <DropdownMenuItem asChild>
                  <Link to={ROUTES.CAR_EDIT(id!)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit CAR
                  </Link>
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => handleExportPDF('external')}
                disabled={isExportingPDF}
              >
                <FileDown className="mr-2 h-4 w-4" />
                {isExportingPDF ? 'Downloading...' : 'Download (External)'}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => handleExportPDF('internal')}
                disabled={isExportingPDF}
              >
                <FileDown className="mr-2 h-4 w-4" />
                {isExportingPDF ? 'Downloading...' : 'Download (Internal)'}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        }
      />

      {/* Content */}
      <CARDetail
        car={car}
        isOfficeOrDPA={isOfficeOrDPA}
        onUploadEvidence={canUploadEvidence ? () => setShowEvidenceUpload(true) : undefined}
      />

      {/* Physical Verification Section — FEAT-PV-001, FEAT-PV-002 */}
      <PhysicalVerificationSection
        physicalVerification={pv}
        isDPAClosed={isClosed}
        canCreatePV={canCreatePV}
        canClosePV={canClosePV}
        onCreatePV={() => setShowPVCreate(true)}
        onClosePV={() => setShowPVClose(true)}
      />

      {/* Action Buttons (sticky bottom bar) — unified workflow */}
      <div className="sticky bottom-0 border-t bg-white p-4 mt-4">
        <div className="flex flex-wrap gap-2 justify-end">
          {canEdit && (
            <Button variant="outline" asChild>
              <Link to={ROUTES.CAR_EDIT(id!)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Link>
            </Button>
          )}
          <CARWorkflowActions
            carId={id!}
            onTransitioned={() => {
              toast({ title: 'Action completed', description: 'CAR workflow status updated.' });
            }}
          />
        </div>
      </div>

      {/* Evidence Upload Modal */}
      <EvidenceUploadModal
        open={showEvidenceUpload}
        onOpenChange={setShowEvidenceUpload}
        carId={id!}
        onSuccess={() => {
          toast({
            title: 'Evidence uploaded',
            description: 'The evidence file has been uploaded successfully.',
          });
        }}
      />

      {/* PV Create Modal — FEAT-PV-001 */}
      <PVCreateModal
        open={showPVCreate}
        onOpenChange={setShowPVCreate}
        carId={id!}
        carNumber={car.car_number}
        onSuccess={() => {
          toast({
            title: 'Verification scheduled',
            description: 'Physical verification has been created.',
          });
        }}
      />

      {/* PV Close Modal — FEAT-PV-002 */}
      {pv && (
        <PVCloseModal
          open={showPVClose}
          onOpenChange={setShowPVClose}
          carId={id!}
          pvId={pv.id}
          onSuccess={() => {
            toast({
              title: 'Verification closed',
              description: 'Physical verification has been closed successfully.',
            });
          }}
        />
      )}
    </RootLayout>
  );
}
