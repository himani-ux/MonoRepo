/**
 * Edit Inspection page
 *
 * Per APP_FLOW.md Section 2.2 and FEAT-INS-007, FEAT-INS-008
 * Allows editing an inspection based on status and role:
 * - DRAFT: Vessel Master can edit
 * - SUBMITTED/PIC_REVIEWED: Office can edit-assist
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useMemo } from 'react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { InspectionForm } from '@/components/inspection';
import {
  useInspection,
  useUpdateInspection,
  useUploadInspectionReport,
} from '@/hooks/use-inspections';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { FormSkeleton, ErrorState } from '@/components/shared';
import { API_BASE_URL, INSPECTION_STATUS, ROUTES } from '@/lib/utils/constants';
import type { CreateInspectionFormData } from '@/lib/validations/inspection';

// ============================================================================
// Permission Helpers
// ============================================================================

/**
 * Check if user can edit the inspection based on status and role.
 */
function canEditInspection(
  status: string,
  userType: string | undefined,
  role: string | undefined
): { canEdit: boolean; reason?: string } {
  const isVesselMaster = userType === 'vessel' && role === 'VESSEL_MASTER';
  const isOffice = userType === 'office';

  switch (status) {
    case INSPECTION_STATUS.DRAFT:
      // Vessel Master can edit draft
      if (isVesselMaster) {
        return { canEdit: true };
      }
      // Office can edit-assist draft
      if (isOffice) {
        return { canEdit: true };
      }
      return { canEdit: false, reason: 'Only Vessel Master or Office can edit draft inspections' };

    case INSPECTION_STATUS.SUBMITTED:
    case INSPECTION_STATUS.PIC_REVIEWED:
      // Only Office can edit submitted/reviewed inspections
      if (isOffice) {
        return { canEdit: true };
      }
      return { canEdit: false, reason: 'Only Office can edit submitted inspections' };

    case INSPECTION_STATUS.DPA_CLOSED:
      return { canEdit: false, reason: 'Closed inspections cannot be edited' };

    default:
      return { canEdit: false, reason: 'Unknown inspection status' };
  }
}

function resolveReportUrl(rawPath?: string): string | undefined {
  if (!rawPath) return undefined;
  if (rawPath.startsWith('http://') || rawPath.startsWith('https://')) return rawPath;
  const normalizedPath = rawPath.replace(/^\/+/, '');
  const baseUrl = API_BASE_URL.replace(/\/+$/, '');
  if (normalizedPath.startsWith('api/') || normalizedPath.startsWith('uploads/')) {
    return `${baseUrl}/${normalizedPath}`;
  }
  return `${baseUrl}/uploads/${normalizedPath}`;
}

// ============================================================================
// Component
// ============================================================================

export default function EditInspectionPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // Fetch inspection data
  const {
    data: inspection,
    isLoading,
    error,
    isError,
  } = useInspection(id);

  // Mutations
  const updateMutation = useUpdateInspection(id!);
  const uploadReportMutation = useUploadInspectionReport(id!);

  // Check edit permissions
  const editPermission = useMemo(
    () =>
      inspection
        ? canEditInspection(inspection.status, user?.user_type, user?.role)
        : { canEdit: false },
    [inspection, user?.user_type, user?.role]
  );

  // Redirect if no permission (after loading)
  useEffect(() => {
    if (inspection && !editPermission.canEdit) {
      toast({
        variant: 'destructive',
        title: 'Access Denied',
        description: editPermission.reason || 'You cannot edit this inspection',
      });
      navigate(`/inspections/${id}`, { replace: true });
    }
  }, [inspection, editPermission, id, navigate, toast]);

  // Convert inspection detail to form data
  const getInitialValues = (): Partial<CreateInspectionFormData> | undefined => {
    if (!inspection) return undefined;

    return {
      inspection_type: inspection.inspection_type as CreateInspectionFormData['inspection_type'],
      psc_subtype: inspection.psc_subtype as CreateInspectionFormData['psc_subtype'] | null,
      inspection_date: inspection.inspection_date,
      port: inspection.port,
      port_state: inspection.port_state || '',
      mou_code: inspection.mou_code || null,
      authority: inspection.authority || '',
      inspector_name: inspection.inspector_name || null,
      is_detention: inspection.is_detention,
      def_reported: inspection.def_reported ?? (undefined as unknown as 'YES' | 'NO'),
      detention_reason: null, // Not in InspectionDetail type, add if needed
    };
  };

  // Get existing report URL if any
  const existingReportUrl = resolveReportUrl(inspection?.reports?.[0]?.file_url || inspection?.reports?.[0]?.file_path);

  // Handle form submission
  const handleSubmit = async (
    data: CreateInspectionFormData,
    reportFile: File | null
  ) => {
    try {
      // Update inspection - map frontend form fields to backend field names
      await updateMutation.mutateAsync({
        inspection_type: data.inspection_type,
        psc_subtype: data.psc_subtype,
        inspection_date: data.inspection_date,
        port_place: data.port,
        country: data.port_state,
        mou_id: data.mou_code,
        authority: data.authority,
        inspector_name: data.inspector_name,
        is_detention: data.is_detention,
        detention_reason: data.detention_reason || '',
        def_reported: data.def_reported,
      });

      // Upload new report if provided
      if (reportFile) {
        await uploadReportMutation.mutateAsync(reportFile);
      }

      toast({
        title: 'Inspection Updated',
        description: 'The inspection has been updated successfully.',
      });

      // Navigate back to detail page
      navigate(`/inspections/${id}`);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Update Failed',
        description: err instanceof Error ? err.message : 'Failed to update inspection',
      });
    }
  };

  // Handle cancel
  const handleCancel = () => {
    navigate(`/inspections/${id}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Edit Inspection" showBack backTo={`/inspections/${id}`} />
        <div className="p-4">
          <FormSkeleton />
        </div>
      </RootLayout>
    );
  }

  // Error state
  if (isError || !inspection) {
    return (
      <RootLayout>
        <PageHeader title="Edit Inspection" showBack backTo={ROUTES.INSPECTIONS} />
        <div className="p-4">
          <ErrorState
            title="Inspection Not Found"
            message={
              error?.message ||
              'The inspection you are trying to edit could not be found.'
            }
            onRetry={() => navigate(ROUTES.INSPECTIONS)}
            retryLabel="Back to Inspections"
          />
        </div>
      </RootLayout>
    );
  }

  // No permission (should redirect, but show error as fallback)
  if (!editPermission.canEdit) {
    return (
      <RootLayout>
        <PageHeader title="Edit Inspection" showBack backTo={`/inspections/${id}`} />
        <div className="p-4">
          <ErrorState
            title="Access Denied"
            message={editPermission.reason || 'You do not have permission to edit this inspection.'}
            onRetry={() => navigate(`/inspections/${id}`)}
            retryLabel="Back to Inspection"
          />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader
        title="Edit Inspection"
        showBack
        backTo={`/inspections/${id}`}
      />
      <div className="p-4">
        <div className="mx-auto max-w-2xl rounded-lg border border-neutral-200 bg-white p-4 shadow-sm md:p-6">
          <InspectionForm
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isSubmitting={updateMutation.isPending || uploadReportMutation.isPending}
            submitLabel="Save Changes"
            initialValues={getInitialValues()}
            existingReportUrl={existingReportUrl}
          />
        </div>
      </div>
    </RootLayout>
  );
}
