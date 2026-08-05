import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import IncidentPhaseSwitcher from "../../../../components/safety/incident/incident-phase-switcher";
import { SafetyIncidentPhase2Form } from "../../../../components/safety/incident/phase2-form";
import { useSafetyAuth } from "../../../../hooks/safety/use-auth";
import { useToast } from "../../../../hooks/use-toast";
import {
  safetyApi,
  type SafetyIncidentPhase2Payload,
} from "../../../../lib/api/safety";
import type { SafetyIncidentPhase2Values } from "../../../../schemas/safety/incident-phase2";

const PHASE_2_MUTATION_ROLES = new Set([
  "MASTER",
  "CO",
  "CE",
  "DPA",
  "FM",
  "CHIEF OFFICER",
  "CHIEF ENGINEER",
  "FLEET MANAGER",
]);

function canEditPhase2(role: string | null) {
  return PHASE_2_MUTATION_ROLES.has((role ?? "").trim().toUpperCase());
}

function deriveInvestigationDepth(riskBand: SafetyIncidentPhase2Values["risk_band"]) {
  if (riskBand === "RED") {
    return "DEEP" as const;
  }
  if (riskBand === "YELLOW") {
    return "MEDIUM" as const;
  }
  return "SHALLOW" as const;
}

export default function SafetyIncidentPhase2Page() {
  const { id } = useParams();
  const auth = useSafetyAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [initialValues, setInitialValues] = useState<Partial<SafetyIncidentPhase2Values>>();
  const [phase2State, setPhase2State] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const readOnly = !canEditPhase2(auth.role);
  const handoffState = (location.state as {
    phase2Handoff?: {
      authorized_roles?: string[];
      can_edit_phase_2?: boolean;
      message?: string;
      notifications_emitted?: number;
    };
    workflowMessage?: string;
  } | null)?.phase2Handoff;
  const workflowMessage = (location.state as { workflowMessage?: string } | null)?.workflowMessage;

  useEffect(() => {
    if (!id) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    async function loadPhase2() {
      try {
        const phase2 = await safetyApi.getIncidentPhase2(id);
        if (cancelled) {
          return;
        }

        setInitialValues({
          dpa_notified_at: phase2.dpa_notified_at,
          fm_notified_at: phase2.fm_notified_at,
          imo_classifier: phase2.imo_classifier,
          investigation_depth: phase2.investigation_depth ?? null,
          latitude: phase2.latitude ?? "",
          longitude: phase2.longitude ?? "",
          loss_type_primary_id: phase2.loss_type_primary_id ?? null,
          loss_type_secondary_id: phase2.loss_type_secondary_id ?? null,
          loss_type_tertiary_id: phase2.loss_type_tertiary_id ?? null,
          loss_type_other: phase2.loss_type_other ?? null,
          office_notification_mode: phase2.office_notification_mode ?? null,
          office_notified: phase2.office_notified ?? null,
          office_notified_at: phase2.office_notified_at,
          pic_user_id: phase2.pic_user_id ?? "",
          risk_band: phase2.risk_band,
          schema_version: phase2.schema_version,
        });
        setPhase2State(phase2.state);
      } catch (error) {
        if (!cancelled) {
          toast({
            title: "Unable to load office communication",
            description:
              error instanceof Error ? error.message : "Incident office communication could not be loaded.",
            variant: "destructive",
          });
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadPhase2();
    return () => {
      cancelled = true;
    };
  }, [id, toast]);

  async function handleSubmitPhase(values: SafetyIncidentPhase2Values) {
    if (!id) {
      return;
    }

    try {
      const payload: SafetyIncidentPhase2Payload = {
        imo_classifier: "NOT_APPLICABLE",
        investigation_depth: deriveInvestigationDepth(values.risk_band),
        loss_type_primary_id: values.loss_type_primary_id ?? null,
        loss_type_secondary_id: values.loss_type_secondary_id ?? null,
        loss_type_tertiary_id: values.loss_type_tertiary_id ?? null,
        loss_type_other: values.loss_type_other?.trim() || null,
        office_notification_mode: values.office_notification_mode ?? null,
        office_notified: values.office_notified ?? null,
        risk_band: values.risk_band,
        schema_version: values.schema_version,
      };
      await safetyApi.updateIncidentPhase2(id, payload);
      const submitted = await safetyApi.submitIncidentPhase2(id);
      setPhase2State(submitted.state);
      toast({
        title: "Office communication submitted",
        description: `Incident ${submitted.incident_number ?? id} is ready for root cause entry.`,
        variant: "success",
      });
      navigate(`/safety/incidents/${id}/phase-2`);
    } catch (error) {
      toast({
        title: "Unable to submit office communication",
        description:
          error instanceof Error ? error.message : "Incident office communication could not be submitted.",
        variant: "destructive",
      });
    }
  }

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-600">Loading incident office communication...</p>
      </section>
    );
  }

  if (readOnly) {
    const authorizedRoles = handoffState?.authorized_roles?.join(", ") ?? "MASTER, CO, CE, DPA, FM";
    const message =
      handoffState?.message ??
      "Office communication can be updated by Master, CO, CE, DPA, or FM.";

    return (
      <section className="space-y-6">
        <IncidentPhaseSwitcher activePhase={1} />
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">
            Incident / Office Communication
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-amber-950">Office communication pending</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-amber-900">{message}</p>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Phase 1 office communication</h2>
            <dl className="mt-5 grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Incident</dt>
                <dd className="mt-2 text-base font-semibold text-slate-900">#{id}</dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Current state</dt>
                <dd className="mt-2 text-base font-semibold text-slate-900">{phase2State ?? "SUBMITTED"}</dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Users who can update</dt>
                <dd className="mt-2 text-sm leading-6 text-slate-700">{authorizedRoles}</dd>
              </div>
            </dl>
          </section>

          <aside className="space-y-6">
            <section className="rounded-3xl border border-sky-200 bg-sky-50 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">What happens next</h2>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                Your Phase 1 details are saved. An authorized user confirms whether office was informed before root cause work starts.
              </p>
              <p className="mt-3 text-sm leading-6 text-slate-700">
                Notification fan-out sent: {handoffState?.notifications_emitted ?? 0}
              </p>
            </section>

            <Link
              className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:border-slate-400 hover:bg-slate-50"
              to="/safety/incidents"
            >
              Back to incidents
            </Link>
          </aside>
        </section>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <IncidentPhaseSwitcher activePhase={1} />
      {workflowMessage ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {workflowMessage}
        </section>
      ) : null}
      <SafetyIncidentPhase2Form
        incidentId={id ?? "phase-2"}
        initialValues={initialValues}
        onSubmitPhase={handleSubmitPhase}
      />
    </section>
  );
}
