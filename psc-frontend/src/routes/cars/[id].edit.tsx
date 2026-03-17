/**
 * Edit CAR page
 *
 * Per APP_FLOW.md Section 2.3 and FEAT-CAR-002, FEAT-CAR-011
 * Allows editing a CAR based on status and role:
 * - Vessel workflow statuses: Vessel Master can edit
 * - Any non-closed status: Office can edit-assist
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect, useMemo } from 'react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { CARForm, EvidenceUploadModal } from '@/components/car';
import { useCAR, useUpdateCAR, useTransitionCAR, useCARAvailableActions } from '@/hooks/use-cars';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { FormSkeleton, ErrorState } from '@/components/shared';
import { CAR_STATUS, ROUTES } from '@/lib/utils/constants';
import type { UpdateCarFormData } from '@/lib/validations/car';
import type { EvidenceType } from '@/types';

// ============================================================================
// Permission Helpers
// ============================================================================

/**
 * Check if user can edit the CAR based on status and role.
 * Per current CAR workflow: Office can edit any non-closed CAR, vessel edit is
 * limited to Master in vessel-side statuses.
 */
function canEditCAR(
  status: string,
  userType: string | undefined,
  role: string | undefined
): { canEdit: boolean; reason?: string } {
  const isVessel = userType === 'vessel';
  const isOffice = userType === 'office';
  const isMaster = role === 'VESSEL_MASTER';

  const VESSEL_EDITABLE: string[] = [
    CAR_STATUS.ALLOTTED,
    CAR_STATUS.IN_PROGRESS,
    CAR_STATUS.PENDING_CE_REVIEW,
    CAR_STATUS.PENDING_MASTER_REVIEW,
    CAR_STATUS.RETURNED_FOR_REWORK,
  ];

  if (isOffice) {
    return status === CAR_STATUS.CLOSED
      ? { canEdit: false, reason: 'Closed CARs are read-only' }
      : { canEdit: true };
  }

  if (isVessel) {
    if (!isMaster) {
      return { canEdit: false, reason: 'Only Master can edit CARs' };
    }
    if (status === CAR_STATUS.PENDING_MASTER_REVIEW) {
      return { canEdit: true };
    }
    if (VESSEL_EDITABLE.includes(status)) {
      return { canEdit: true };
    }
    return {
      canEdit: false,
      reason: 'Vessel can only edit CARs in vessel-side workflow statuses',
    };
  }

  return { canEdit: false, reason: 'You do not have permission to edit this CAR' };
}

// ============================================================================
// Component
// ============================================================================

export default function EditCARPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // Fetch CAR data
  const { data: car, isLoading, error, isError } = useCAR(id);

  // Mutations
  const updateMutation = useUpdateCAR(id!);
  const transitionMutation = useTransitionCAR(id!);

  // Available workflow actions (determines what "submit" does for this user)
  const { data: availableActions = [] } = useCARAvailableActions(id);

  // Primary forward action (first non-rework action) for the submit button
  const primaryAction = availableActions.find(
    (a) => !a.action.includes('REWORK') && a.action !== 'REOPEN_CAR'
  );

  // Check edit permissions
  const editPermission = useMemo(
    () =>
      car
        ? canEditCAR(car.status, user?.user_type, user?.role)
        : { canEdit: false },
    [car, user?.user_type, user?.role]
  );

  // Redirect if no permission (after loading)
  useEffect(() => {
    if (car && !editPermission.canEdit) {
      toast({
        variant: 'destructive',
        title: 'Access Denied',
        description: editPermission.reason || 'You cannot edit this CAR',
      });
      navigate(ROUTES.CAR_DETAIL(id!), { replace: true });
    }
  }, [car, editPermission, id, navigate, toast]);

  // Handle save draft
  const handleSaveDraft = async (data: UpdateCarFormData) => {
    try {
      await updateMutation.mutateAsync({
        root_cause_summary: data.root_cause_summary || undefined,
        target_date: data.target_date,
        clc_item_ids: data.clc_item_ids,
        custom_cause_text: data.custom_cause_text || undefined,
      });

      toast({
        title: 'CAR Saved',
        description: 'Draft has been saved successfully.',
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Save Failed',
        description:
          err instanceof Error ? err.message : 'Failed to save CAR',
      });
      throw err;
    }
  };

  // Handle submit — uses unified workflow transition
  const handleSubmit = async () => {
    if (!primaryAction) return;
    try {
      await transitionMutation.mutateAsync({
        action: primaryAction.action,
        comment: '',
      });

      toast({
        title: 'Success',
        description: `CAR action "${primaryAction.label}" completed.`,
      });

      navigate(ROUTES.CAR_DETAIL(id!));
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Submit Failed',
        description:
          err instanceof Error ? err.message : 'Failed to submit CAR',
      });
      throw err;
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate(ROUTES.CAR_DETAIL(id!));
  };

  // Evidence upload modal state
  const [showEvidenceUpload, setShowEvidenceUpload] = useState(false);
  const [evidenceDefaultType, setEvidenceDefaultType] = useState<EvidenceType | undefined>();

  const handleUploadEvidence = (type: 'BEFORE' | 'AFTER' | 'EVIDENCE' | 'OTHER') => {
    setEvidenceDefaultType(type as EvidenceType);
    setShowEvidenceUpload(true);
  };

  // Loading state
  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader
          title="Edit CAR"
          showBack
          backTo={id ? ROUTES.CAR_DETAIL(id) : ROUTES.CARS}
        />
        <div className="p-4">
          <FormSkeleton />
        </div>
      </RootLayout>
    );
  }

  // Error state
  if (isError || !car) {
    return (
      <RootLayout>
        <PageHeader title="Edit CAR" showBack backTo={ROUTES.CARS} />
        <div className="p-4">
          <ErrorState
            title="CAR Not Found"
            message={
              error?.message ||
              'The CAR you are trying to edit could not be found.'
            }
            onRetry={() => navigate(ROUTES.CARS)}
            retryLabel="Back to CARs"
          />
        </div>
      </RootLayout>
    );
  }

  // No permission fallback
  if (!editPermission.canEdit) {
    return (
      <RootLayout>
        <PageHeader
          title="Edit CAR"
          showBack
          backTo={ROUTES.CAR_DETAIL(id!)}
        />
        <div className="p-4">
          <ErrorState
            title="Access Denied"
            message={
              editPermission.reason ||
              'You do not have permission to edit this CAR.'
            }
            onRetry={() => navigate(ROUTES.CAR_DETAIL(id!))}
            retryLabel="Back to CAR"
          />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader
        title={`Edit CAR: ${car.car_number}`}
        showBack
        backTo={ROUTES.CAR_DETAIL(id!)}
      />
      <div className="p-4">
        <div className="mx-auto max-w-3xl">
          <CARForm
            car={car}
            onSaveDraft={handleSaveDraft}
            onSubmit={primaryAction ? handleSubmit : undefined}
            onCancel={handleCancel}
            onUploadEvidence={handleUploadEvidence}
            isSaving={updateMutation.isPending}
            isSubmitting={transitionMutation.isPending}
            submitLabel={primaryAction?.label}
            submitDescription={
              primaryAction
                ? `This will perform "${primaryAction.label}" on the CAR. Continue?`
                : undefined
            }
          />
        </div>
      </div>

      {/* Evidence Upload Modal */}
      <EvidenceUploadModal
        open={showEvidenceUpload}
        onOpenChange={setShowEvidenceUpload}
        carId={id!}
        defaultType={evidenceDefaultType}
        onSuccess={() => {
          toast({
            title: 'Evidence uploaded',
            description: 'The evidence file has been uploaded successfully.',
          });
        }}
      />
    </RootLayout>
  );
}