import { useParams } from "react-router-dom";

import SafetyClosedSinceLastBlock from "../../../../components/safety/scm/closed-since-last-block";
import { useSafetyScmClosedSinceLast } from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";

export default function SafetyScmClosedSinceLastRoute() {
  const params = useParams();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const query = useSafetyScmClosedSinceLast(meetingId, enabled);

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SCM meeting id.
      </section>
    );
  }

  if (query.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading closed-since-last summary...
      </section>
    );
  }

  if (query.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(query.error)}
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#ecfeff_0%,#ffffff_55%,#fef3c7_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / SCM
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Closed-Since-Last SCM
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Records closed after the previous SCM sign-off are shown here.
        </p>
      </header>

      <SafetyClosedSinceLastBlock payload={query.data} />
    </section>
  );
}
