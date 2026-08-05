import { useParams } from "react-router-dom";

import SafetyScmAgendaEditor from "../../../../components/safety/scm/agenda-editor";
import { useSafetyScmAgenda } from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";

export default function SafetyScmAgendaRoute() {
  const params = useParams();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const agendaQuery = useSafetyScmAgenda(meetingId, enabled, true);

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SCM meeting id.
      </section>
    );
  }

  if (agendaQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM agenda...
      </section>
    );
  }

  if (agendaQuery.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(agendaQuery.error)}
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#fef3c7_0%,#ffffff_55%,#dbeafe_100%)] p-6 shadow-sm">
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">SCM Agenda</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Review meeting decisions and action items.
        </p>
      </header>

      <SafetyScmAgendaEditor payload={agendaQuery.data} />
    </section>
  );
}
