import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import SafetyScmTenSectionForm from "../../../components/safety/scm/scm-10-section-form";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import {
  useSafetyScmCreateRegularConfig,
  useSafetyScmOpenFindings,
} from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../lib/safety/digital-signature";

export default function SafetyScmCreateRegularRoute() {
  const navigate = useNavigate();
  const auth = useSafetyAuth();
  const vesselId = auth.isGlobal ? undefined : String(auth.vesselIds[0] ?? "");
  const configQuery = useSafetyScmCreateRegularConfig(vesselId);
  const autoFeedQuery = useSafetyScmOpenFindings(vesselId);
  const createMutation = useMutation({
    mutationFn: async (values: Parameters<typeof safetyApi.createScmMeeting>[0]) => {
      const meeting = await safetyApi.createScmMeeting(values);
      return safetyApi.submitScmMeeting(meeting.id, {
        device_fingerprint: getSafetyDeviceFingerprint(),
        typed_name: resolveSignatureTypedName(auth.user),
      });
    },
    onSuccess: (meeting) => navigate(`/safety/scm/${meeting.id}`),
  });

  if (configQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM create form...
      </section>
    );
  }

  if (configQuery.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(configQuery.error)}
      </section>
    );
  }

  const config = configQuery.data;

  return (
    <>
      <SafetyScmTenSectionForm
        autoFeedPayload={autoFeedQuery.data ?? null}
        config={config}
        isSubmitting={createMutation.isPending}
        onSubmit={(values) => {
          if (!createMutation.isPending) {
            createMutation.mutate(values);
          }
        }}
        submittingLabel="Submitting to office..."
      />
      {createMutation.isError ? (
        <section className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(createMutation.error)}
        </section>
      ) : null}
      {autoFeedQuery.isError ? (
        <section className="mt-6 rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900 shadow-sm">
          SOI findings could not be loaded: {getErrorMessage(autoFeedQuery.error)}
        </section>
      ) : null}
    </>
  );
}
