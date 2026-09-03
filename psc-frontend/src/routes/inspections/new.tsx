/**
 * Create Inspection page route.
 *
 * Screen: Create Inspection (`/inspections/new`) per APP_FLOW.md Section 2.2
 *
 * Features:
 * - InspectionForm with validation
 * - Create inspection via API
 * - Upload report after creation
 * - Navigate to detail page on success
 * - Cancel confirmation dialog
 *
 * PRD Reference: FEAT-INS-001, FEAT-INS-002
 */

import { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { InspectionForm } from '@/components/inspection/inspection-form';
import {
  AuditRegistrationForm,
  type AuditRegistrationPlanOption,
} from '@/components/audit/registration/audit-registration-form';
import { ConfirmDialog } from '@/components/shared';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/use-auth';
import { useCreateInspection } from '@/hooks/use-inspections';
import { useAuditPlans } from '@/hooks/audit/use-audit-plan';
import { useAuditVessels, useCreateAuditRegistration } from '@/hooks/audit/use-audit-registration';
import { inspectionsApi } from '@/lib/api/inspections';
import { INSPECTION_TYPES, ROUTES, USER_ROLES } from '@/lib/utils/constants';
import { getErrorMessage } from '@/lib/api/client';
import type { CreateInspectionFormData } from '@/lib/validations/inspection';
import type { AuditRegistrationFormData } from '@/schemas/audit/registration';

/**
 * Create Inspection page component.
 */
export function CreateInspectionPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // Cancel confirmation dialog state
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  // Mutations
  const createMutation = useCreateInspection();

  // Loading state
  const [isUploading, setIsUploading] = useState(false);
  const isSubmitting = createMutation.isPending || isUploading;
  const isVesselMaster = user?.role === USER_ROLES.VESSEL_MASTER;
  const allowedInspectionTypes = isVesselMaster
    ? [INSPECTION_TYPES.PSC, INSPECTION_TYPES.RS, INSPECTION_TYPES.AUDIT]
    : [INSPECTION_TYPES.AUDIT];

  /**
   * Handle form submission.
   * Creates the inspection, then uploads the report if provided.
   */
  const handleSubmit = useCallback(
    async (data: CreateInspectionFormData, reportFile: File | null) => {
      try {
        if (
          (data.inspection_type === INSPECTION_TYPES.PSC ||
            data.inspection_type === INSPECTION_TYPES.RS) &&
          user?.role !== USER_ROLES.VESSEL_MASTER
        ) {
          toast({
            title: 'Access denied',
            description: 'Only Vessel Master can create PSC or RightShip inspections.',
            variant: 'destructive',
          });
          return;
        }

        // For vessel users, use their vessel_id from auth
        // For office users, they would need to select a vessel (not implemented yet)
        const vesselId = user?.vessel_id || '';

        if (!vesselId) {
          toast({
            title: 'Error',
            description: 'Unable to determine vessel. Please try again.',
            variant: 'destructive',
          });
          return;
        }

        // Create the inspection
        // Map frontend form field names to backend serializer field names
        const inspection = await createMutation.mutateAsync({
          vessel_id: vesselId,
          inspection_type: data.inspection_type,
          psc_subtype: data.psc_subtype,
          inspection_date: data.inspection_date,
          port_place: data.port,
          country: data.port_state || '',
          mou_id: data.mou_code,
          authority: data.authority,
          inspector_name: data.inspector_name,
          is_detention: data.is_detention,
          detention_reason: data.detention_reason || '',
          def_reported: data.def_reported,
        });

        // Upload report if provided — call API directly with the new inspection ID
        // (cannot use hook here because the ID isn't known until after create)
        if (reportFile) {
          try {
            setIsUploading(true);
            await inspectionsApi.uploadInspectionReport(inspection.id, reportFile);
          } catch (uploadError) {
            // Show warning but still navigate (inspection was created)
            toast({
              title: 'Warning',
              description:
                'Inspection created, but report upload failed. You can upload it later.',
              variant: 'destructive',
            });
          } finally {
            setIsUploading(false);
          }
        }

        // Success toast
        toast({
          title: 'Inspection created',
          description: 'Your inspection draft has been saved.',
        });

        // Navigate to inspections list so the user immediately sees all inspections.
        navigate(ROUTES.INSPECTIONS, { replace: true });
      } catch (error) {
        const message = getErrorMessage(error);
        toast({
          title: 'Failed to create inspection',
          description: message,
          variant: 'destructive',
        });
      }
    },
    [createMutation, user, navigate, toast]
  );

  /**
   * Handle cancel button click.
   * Shows confirmation dialog if form has data.
   */
  const handleCancel = useCallback(() => {
    setShowCancelDialog(true);
  }, []);

  /**
   * Confirm cancel and navigate back.
   */
  const handleConfirmCancel = useCallback(() => {
    setShowCancelDialog(false);
    navigate(ROUTES.INSPECTIONS);
  }, [navigate]);

  return (
    <RootLayout>
      {/* Page header with back button */}
      <PageHeader
        title={isVesselMaster ? 'New Inspection' : 'Register Audit'}
        showBack
        backTo={ROUTES.INSPECTIONS}
      />

      {/* Form */}
      <div className={isVesselMaster ? 'mx-auto max-w-2xl pb-8' : 'mx-auto max-w-6xl pb-8'}>
        {isVesselMaster ? (
          <InspectionForm
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isSubmitting={isSubmitting}
            submitLabel="Create Draft"
            requireReport
            allowedInspectionTypes={allowedInspectionTypes}
          />
        ) : (
          <OfficeAuditRegistrationSection user={user} onCancel={handleCancel} />
        )}
      </div>

      {/* Cancel confirmation dialog */}
      <ConfirmDialog
        open={showCancelDialog}
        onOpenChange={setShowCancelDialog}
        title="Discard changes?"
        description="You have unsaved changes. Are you sure you want to leave? Your changes will be lost."
        confirmLabel="Discard"
        cancelLabel="Keep editing"
        variant="destructive"
        onConfirm={handleConfirmCancel}
      />
    </RootLayout>
  );
}

function OfficeAuditRegistrationSection({
  user,
  onCancel,
}: {
  user: unknown;
  onCancel: () => void;
}) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createAuditRegistration = useCreateAuditRegistration();
  const vesselQuery = useAuditVessels();
  const planQuery = useAuditPlans();
  const auditPlanOptions = useMemo(
    () => (planQuery.data?.results ?? []).filter(isRegisterableAuditPlan),
    [planQuery.data]
  );

  const handleAuditRegistrationSubmit = useCallback(
    async (data: AuditRegistrationFormData) => {
      try {
        const audit = await createAuditRegistration.mutateAsync(data);
        toast({
          title: 'Audit registered',
          description: 'The audit record has been created.',
        });
        navigate(`/audit/audits/${audit.id}`, { replace: true });
      } catch (error) {
        toast({
          title: 'Audit not registered',
          description: getErrorMessage(error),
          variant: 'destructive',
        });
      }
    },
    [createAuditRegistration, navigate, toast]
  );

  return (
    <AuditRegistrationForm
      onSubmit={handleAuditRegistrationSubmit}
      onCancel={onCancel}
      isSubmitting={createAuditRegistration.isPending}
      vesselOptions={vesselQuery.data ?? []}
      auditPlanOptions={auditPlanOptions}
      defaultVesselId={getUserVesselId(user)}
      defaultLeadAuditorName={getUserDisplayName(user)}
    />
  );
}

const REGISTERABLE_AUDIT_PLAN_STATUSES = new Set(['CONFIRMED', 'EXTENDED', 'CRITICAL_OVERDUE']);

function isRegisterableAuditPlan(plan: AuditRegistrationPlanOption): boolean {
  const status = String(plan.status || '').toUpperCase();
  return REGISTERABLE_AUDIT_PLAN_STATUSES.has(status) && Boolean(plan.lead_auditor_user_id);
}

function getUserVesselId(user: unknown): string | null {
  if (!user || typeof user !== 'object') return null;
  const candidate = user as { vessel_id?: string };
  return candidate.vessel_id || null;
}

function getUserDisplayName(user: unknown): string {
  if (!user || typeof user !== 'object') return '';
  const candidate = user as {
    full_name?: string;
    name?: string;
    display_name?: string;
    username?: string;
    user_id?: string;
  };
  return candidate.full_name || candidate.name || candidate.display_name || candidate.username || candidate.user_id || '';
}

export default CreateInspectionPage;
