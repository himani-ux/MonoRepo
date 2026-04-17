import { useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { MoreVertical, Edit, Trash2, FileCheck, Download, Info } from 'lucide-react';
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import {
  ErrorState,
  DeleteConfirmDialog,
} from '@/components/shared';
import { DetailHeaderSkeleton, SectionSkeleton } from '@/components/shared/loading-skeleton';
import {
  InspectionDetail,
  DeficiencyModal,
} from '@/components/inspection';
import {
  useInspection,
  useDeleteInspection,
} from '@/hooks/use-inspections';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { ROUTES, INSPECTION_TYPES } from '@/lib/utils/constants';
import { exportInspectionCARs } from '@/lib/api/inspections';
import type { CARPDFAudience } from '@/lib/api/cars';

/**
 * Inspection Detail Page
 *
 * Displays full inspection details with:
 * - Header info (vessel, date, port, etc.)
 * - Report section (Original + Follow-up)
 * - Deficiencies list
 * - Activity history
 * - Action buttons based on role
 */
export default function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user, isVessel, isOffice } = useAuth();

  // Query
  const { data: inspection, isLoading, error, refetch } = useInspection(id);

  // Mutations
  const deleteMutation = useDeleteInspection();

  // Dialog states
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showDeficiencyModal, setShowDeficiencyModal] = useState(false);
  const [showCARAudienceDialog, setShowCARAudienceDialog] = useState(false);

  // Derived state
  const isPSC = inspection?.inspection_type === INSPECTION_TYPES.PSC;

  // Permission checks (simplified — no status gate)
  const canEdit = isVessel;
  const canDelete = isVessel && (!inspection?.deficiencies || inspection.deficiencies.length === 0);
  const canAddDeficiency = (isVessel || isOffice) && inspection?.def_reported !== 'NO';
  const canRegisterFollowUp = isPSC && isVessel;

  // Bulk submit: Master can submit multiple APPROVED DEFs at once
  const userRank = (user?.rank || '').toLowerCase();
  const isMaster = userRank.includes('master') || userRank.includes('captain');
  const hasApprovedDefs = inspection?.deficiencies?.some((d) => d.def_status === 'APPROVED');
  const canBulkSubmit = isMaster && !!hasApprovedDefs;

  // Download All CARs: shown when inspection has deficiencies with CARs
  const hasCARs = inspection?.deficiencies?.some((d) => d.car);
  const [isDownloadingCARs, setIsDownloadingCARs] = useState(false);

  // Handlers
  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(id!);
      toast({
        title: 'Inspection deleted',
        description: 'The inspection has been deleted successfully.',
      });
      navigate(ROUTES.INSPECTIONS);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete inspection. Please try again.',
      });
    }
  };

  const handleDeficiencyAdded = () => {
    setShowDeficiencyModal(false);
    toast({
      title: 'Deficiency added',
      description: 'A CAR has been automatically created for this deficiency.',
    });
  };

  const handleDownloadAllCARs = useCallback(async (audience: CARPDFAudience) => {
    if (!id) return;
    setIsDownloadingCARs(true);
    try {
      const blob = await exportInspectionCARs(id, audience);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      // Content-type determines extension
      const ext = blob.type === 'application/pdf' ? 'pdf' : 'zip';
      const suffix = audience === 'external' ? 'External' : 'Internal';
      link.download = `CARs_${id.slice(0, 8)}_${suffix}.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      toast({
        variant: 'destructive',
        title: 'Download failed',
        description: 'Failed to download CAR reports. Please try again.',
      });
    } finally {
      setIsDownloadingCARs(false);
    }
  }, [id, toast]);

  // Loading state
  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Inspection Detail" showBack backTo={ROUTES.INSPECTIONS} />
        <div className="space-y-4">
          <DetailHeaderSkeleton />
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  // Error state
  if (error || !inspection) {
    return (
      <RootLayout>
        <PageHeader title="Inspection Detail" showBack backTo={ROUTES.INSPECTIONS} />
        <ErrorState
          title="Inspection not found"
          message="The inspection may have been deleted or you don't have access."
          onRetry={() => refetch()}
        >
          <Button
            variant="outline"
            onClick={() => navigate(ROUTES.INSPECTIONS)}
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
        title="Inspection Detail"
        showBack
        backTo={ROUTES.INSPECTIONS}
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
                  <Link to={ROUTES.INSPECTION_EDIT(id!)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit Inspection
                  </Link>
                </DropdownMenuItem>
              )}
              {isOffice && (
                <DropdownMenuItem asChild>
                  <Link to={ROUTES.INSPECTION_EDIT(id!)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit (Office Assist)
                  </Link>
                </DropdownMenuItem>
              )}
              {hasCARs && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => setShowCARAudienceDialog(true)}
                    disabled={isDownloadingCARs}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    {isDownloadingCARs ? 'Downloading...' : 'Download All CARs'}
                  </DropdownMenuItem>
                </>
              )}
              {canRegisterFollowUp && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to={ROUTES.INSPECTION_FOLLOW_UP(id!)}>
                      <FileCheck className="mr-2 h-4 w-4" />
                      Register Follow-up
                    </Link>
                  </DropdownMenuItem>
                </>
              )}
              {canDelete && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="text-error-600 focus:text-error-600"
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Inspection
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        }
      />

      {/* Info message when def_reported is NO */}
      {inspection.def_reported === 'NO' && (
        <div className="mx-4 mt-2 flex items-center gap-2 rounded-md bg-blue-50 p-3 text-sm text-blue-700">
          <Info className="h-4 w-4 flex-shrink-0" />
          <span>No deficiencies reported. To add deficiencies, edit the inspection and change &quot;Deficiencies Reported&quot; to Yes.</span>
        </div>
      )}

      {/* Content */}
      <InspectionDetail
        inspection={inspection}
        onAddDeficiency={canAddDeficiency ? () => setShowDeficiencyModal(true) : undefined}
        bulkSubmitEnabled={canBulkSubmit}
      />

      {/* Dialogs */}
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        itemName="this inspection"
        onConfirm={handleDelete}
      />

      <Dialog
        open={showCARAudienceDialog}
        onOpenChange={(open) => {
          if (!isDownloadingCARs) {
            setShowCARAudienceDialog(open);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Download All CARs</DialogTitle>
            <DialogDescription>
              Choose which report version should be generated for all CARs in this inspection.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowCARAudienceDialog(false)}
              disabled={isDownloadingCARs}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setShowCARAudienceDialog(false);
                handleDownloadAllCARs('external');
              }}
              disabled={isDownloadingCARs}
            >
              {isDownloadingCARs ? 'Generating...' : 'External Report'}
            </Button>
            <Button
              onClick={() => {
                setShowCARAudienceDialog(false);
                handleDownloadAllCARs('internal');
              }}
              disabled={isDownloadingCARs}
            >
              {isDownloadingCARs ? 'Generating...' : 'Internal Report'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Deficiency Modal */}
      <DeficiencyModal
        open={showDeficiencyModal}
        onOpenChange={setShowDeficiencyModal}
        inspectionId={id!}
        vesselId={inspection?.vessel_id ? String(inspection.vessel_id) : undefined}
        onSuccess={handleDeficiencyAdded}
      />
    </RootLayout>
  );
}
