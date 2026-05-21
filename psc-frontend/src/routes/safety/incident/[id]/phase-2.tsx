import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

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
  } | null)?.phase2Handoff;

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
          office_notified_at: phase2.office_notified_at,
          pic_user_id: phase2.pic_user_id ?? "",
          risk_band: phase2.risk_band,
          schema_version: phase2.schema_version,
        });
        setPhase2State(phase2.state);
      } catch (error) {
        if (!cancelled) {
          toast({
            title: "Unable to load Phase 2",
            description:
              error instanceof Error ? error.message : "Incident Phase 2 could not be loaded.",
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
        imo_classifier: values.imo_classifier,
        investigation_depth: values.investigation_depth ?? null,
        latitude: values.latitude,
        longitude: values.longitude,
        loss_type_primary_id: values.loss_type_primary_id ?? null,
        risk_band: values.risk_band,
        schema_version: values.schema_version,
      };
      await safetyApi.updateIncidentPhase2(id, payload);
      const submitted = await safetyApi.submitIncidentPhase2(id);
      setPhase2State(submitted.state);
      toast({
        title: "Phase 2 submitted",
        description: `Incident ${submitted.incident_number ?? id} is ready for Phase 3 evidence capture.`,
        variant: "success",
      });
      navigate(`/safety/incidents/${id}/phase-3/people`);
    } catch (error) {
      toast({
        title: "Unable to submit Phase 2",
        description:
          error instanceof Error ? error.message : "Incident Phase 2 could not be submitted.",
        variant: "destructive",
      });
    }
  }

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-600">Loading incident Phase 2...</p>
      </section>
    );
  }

  if (readOnly) {
    const authorizedRoles = handoffState?.authorized_roles?.join(", ") ?? "MASTER, CO, CE, DPA, FM";
    const message =
      handoffState?.message ??
      "Phase 2 editing is restricted to Master, CO, CE, DPA, or FM. Awaiting resource allocation.";

    return (
      <section className="space-y-6">
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-700">
            Incident / Phase 2
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-amber-950">Awaiting resource allocation</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-amber-900">{message}</p>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Phase 1 handoff status</h2>
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
                <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Authorized Phase 2 roles</dt>
                <dd className="mt-2 text-sm leading-6 text-slate-700">{authorizedRoles}</dd>
              </div>
            </dl>
          </section>

          <aside className="space-y-6">
            <section className="rounded-3xl border border-sky-200 bg-sky-50 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">What happens next</h2>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                Your Phase 1 intake is preserved. An authorized Phase 2 role must allocate resources and submit the office notification step before the investigation workspace opens.
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
      <SafetyIncidentPhase2Form
        incidentId={id ?? "phase-2"}
        initialValues={initialValues}
        onSubmitPhase={handleSubmitPhase}
      />
    </section>
  );
}
