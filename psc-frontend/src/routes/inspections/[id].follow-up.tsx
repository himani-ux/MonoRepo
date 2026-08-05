/**
 * Register PSC Follow-up page — 5-step wizard
 *
 * Allows Vessel Master to record a follow-up on the SAME inspection.
 * Updates deficiency action codes and optionally uploads follow-up reports.
 */

import { useParams, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { FollowUpWizard } from '@/components/inspection/follow-up-wizard';
import { useInspection, useSubmitFollowUp } from '@/hooks/use-inspections';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { FormSkeleton, ErrorState } from '@/components/shared';
import { INSPECTION_TYPES, ROUTES } from '@/lib/utils/constants';
import type { FollowUpFormData } from '@/lib/validations/follow-up';

export default function RegisterFollowUpPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // Fetch parent inspection data
  const {
    data: inspection,
    isLoading,
    error,
    isError,
  } = useInspection(id);

  // Follow-up submission mutation
  const followUpMutation = useSubmitFollowUp(id!);

  // Check if user is Vessel Master
  const isVesselMaster = user?.user_type === 'vessel' && user?.role === 'VESSEL_MASTER';

  // Check if inspection is PSC type
  const isPSCInspection = inspection?.inspection_type === INSPECTION_TYPES.PSC;

  // Redirect if not allowed
  useEffect(() => {
    if (isLoading) return;

    if (!isVesselMaster) {
      toast({
        variant: 'destructive',
        title: 'Access Denied',
        description: 'Only Vessel Master can register PSC follow-ups.',
      });
      navigate(id ? `/inspections/${id}` : ROUTES.INSPECTIONS, { replace: true });
      return;
    }

    if (inspection && !isPSCInspection) {
      toast({
        variant: 'destructive',
        title: 'Invalid Inspection Type',
        description: 'Follow-up can only be registered for PSC inspections.',
      });
      navigate(`/inspections/${id}`, { replace: true });
      return;
    }
  }, [inspection, isLoading, isVesselMaster, isPSCInspection, id, navigate, toast]);

  // Handle wizard submission
  const handleSubmit = async (data: FollowUpFormData) => {
    if (!id) return;

    const formData = new FormData();
    formData.append('deficiency_updates', JSON.stringify(data.deficiency_updates));
    formData.append('reinspection_date', data.reinspection_date);
    if (data.notes) {
      formData.append('notes', data.notes);
    }
    const reportFiles = data.report_files?.length
      ? data.report_files
      : data.report_file
        ? [data.report_file]
        : [];
    reportFiles.forEach((reportFile) => {
      formData.append('report_files', reportFile);
    });
    if (reportFiles.length > 0) {
      formData.append('report_description', data.report_description || '');
    }

    try {
      await followUpMutation.mutateAsync(formData);

      const updatedCount = data.deficiency_updates.length;
      toast({
        title: 'Follow-up Recorded',
        description: `Follow-up recorded successfully. ${updatedCount} deficiencies updated.`,
      });

      // Navigate back to inspection detail
      navigate(`/inspections/${id}`);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Submission Failed',
        description: err instanceof Error ? err.message : 'Failed to record follow-up',
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
        <PageHeader title="Register Follow-up" showBack backTo={`/inspections/${id}`} />
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
        <PageHeader title="Register Follow-up" showBack backTo={ROUTES.INSPECTIONS} />
        <div className="p-4">
          <ErrorState
            title="Inspection Not Found"
            message={
              error?.message ||
              'The inspection you are trying to register a follow-up for could not be found.'
            }
            onRetry={() => navigate(ROUTES.INSPECTIONS)}
            retryLabel="Back to Inspections"
          />
        </div>
      </RootLayout>
    );
  }

  // Not PSC inspection
  if (!isPSCInspection) {
    return (
      <RootLayout>
        <PageHeader title="Register Follow-up" showBack backTo={`/inspections/${id}`} />
        <div className="p-4">
          <ErrorState
            title="Invalid Inspection Type"
            message="Follow-up can only be registered for PSC inspections."
            onRetry={() => navigate(`/inspections/${id}`)}
            retryLabel="Back to Inspection"
          />
        </div>
      </RootLayout>
    );
  }

  // Not Vessel Master
  if (!isVesselMaster) {
    return (
      <RootLayout>
        <PageHeader title="Register Follow-up" showBack backTo={`/inspections/${id}`} />
        <div className="p-4">
          <ErrorState
            title="Access Denied"
            message="Only Vessel Master can register PSC follow-ups."
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
        title="Register Follow-up"
        showBack
        backTo={`/inspections/${id}`}
      />
      <div className="p-4">
        <div className="mx-auto max-w-2xl rounded-lg border border-neutral-200 bg-white shadow-sm">
          <FollowUpWizard
            inspection={inspection}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isSubmitting={followUpMutation.isPending}
          />
        </div>
      </div>
    </RootLayout>
  );
}
