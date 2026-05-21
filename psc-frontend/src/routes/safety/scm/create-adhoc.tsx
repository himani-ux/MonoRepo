import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import SafetyScmTenSectionForm from "../../../components/safety/scm/scm-10-section-form";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import {
  useSafetyScmCreateAdhocConfig,
  useSafetyScmOpenFindings,
} from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";

export default function SafetyScmCreateAdHocRoute() {
  const navigate = useNavigate();
  const auth = useSafetyAuth();
  const vesselId = auth.isGlobal ? undefined : String(auth.vesselIds[0] ?? "");
  const configQuery = useSafetyScmCreateAdhocConfig(vesselId);
  const autoFeedQuery = useSafetyScmOpenFindings(vesselId);
  const createMutation = useMutation({
    mutationFn: safetyApi.createScmMeeting,
    onSuccess: (meeting) => navigate(`/safety/scm/${meeting.public_id ?? meeting.id}`),
  });

  if (configQuery.isLoading || autoFeedQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading Ad-Hoc SCM create form...
      </section>
    );
  }

  if (configQuery.isError || autoFeedQuery.isError) {
    const error = configQuery.error ?? autoFeedQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const config = configQuery.data;

  return (
    <>
      <SafetyScmTenSectionForm
        autoFeedPayload={autoFeedQuery.data}
        config={config}
        isSubmitting={createMutation.isPending}
        mode="adhoc"
        onSubmit={(values) => {
          if (!createMutation.isPending) {
            createMutation.mutate(values);
          }
        }}
      />
      {createMutation.isError ? (
        <section className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(createMutation.error)}
        </section>
      ) : null}
    </>
  );
}
