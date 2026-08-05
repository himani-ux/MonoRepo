import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useAuth } from '../../../hooks/use-auth';
import { getErrorMessage } from '../../../lib/api/client';
import { safetyApi } from '../../../lib/api/safety';
import {
  getSafetyDeviceFingerprint,
  resolveSignatureTypedName,
} from '../../../lib/safety/digital-signature';
import { incidentPhaseRoute } from '../../../lib/safety/incident-phase-display';
import type { SafetyIncidentPhase7Preflight } from '../../../schemas/safety/incident-phase7';
import {
  DEFAULT_INCIDENT_PDF_SECTION_KEYS,
  type IncidentPdfSectionKey,
} from './incident-pdf-section-selector';

const SEND_BACK_TARGET_PHASE = 6;
const LOSS_EVALUATION_PDF_SECTION_KEY: IncidentPdfSectionKey = 'estimated_cost';
const REQUIRED_INCIDENT_PDF_SECTION_KEYS = DEFAULT_INCIDENT_PDF_SECTION_KEYS.filter(
  (sectionKey) => sectionKey !== LOSS_EVALUATION_PDF_SECTION_KEY
);
const GREEN_PIC_ROLE_CODES = new Set([
  'PIC',
  'VESSEL SUPERINTENDENT',
  'OFFICE_PIC',
  'OFFICE_SSQE',
  'OFFICE_SUPT',
]);
const OFFICE_REVIEW_ROLE_CODES = new Set(['DPA', ...GREEN_PIC_ROLE_CODES]);
const OFFICE_REVIEW_PROCESS_IDS = ['SAF_P_004', 'SAF_P_006'];
const HOD_SIGNER_ROLE_CODES = new Set([
  'HOD',
  'HEAD OF DEPARTMENT',
  'CE',
  'CHIEF ENGINEER',
  'CO',
  'CHIEF OFFICER',
]);
const CENTRAL_OFFICE_ROLE_CODES = new Set([
  'DPA',
  'FM',
  'FLEET MANAGER',
  'OFFICE_PIC',
  'OFFICE_SSQE',
  'OFFICE_SUPT',
  'PHYSICAL_VERIFIER',
]);

function emptyPreflight(): SafetyIncidentPhase7Preflight {
  return {
    alarp_complete: false,
    bias_guards_resolved: false,
    blockers: [],
    closer_role: 'DPA',
    current_phase: 7,
    generated_at: '',
    incident_id: 0,
    pdf_preview: {
      available: false,
      expected_sections: 10,
      incident_id: 0,
      message: '',
      status: 'NOT_AVAILABLE',
    },
    ready_for_acceptance: false,
    recommendation_tier_count: {},
    required_process_id: 'SAF_P_004',
    risk_band: null,
    root_count: 0,
    signature_chain_status: {
      dpa: { present: false, required: false },
      fm: { present: false, required: false },
      hod: { present: false, required: true },
      master: { present: false, required: true },
      pic: { present: false, required: false },
      reporter: { present: false, required: true },
    },
    office_comment: '',
    rework_summary: null,
  };
}

function normalizeCode(value: unknown) {
  return String(value ?? '')
    .trim()
    .toUpperCase();
}

function normalizeRoleCode(value: unknown) {
  const normalized = normalizeCode(value)
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ');
  if (
    normalized === 'FLEET MANAGER' ||
    normalized === 'FLEETMANAGER' ||
    normalized === 'OFFICE FM'
  ) {
    return 'FM';
  }
  if (normalized === 'OFFICE PIC') {
    return 'OFFICE_PIC';
  }
  if (normalized === 'OFFICE SSQE') {
    return 'OFFICE_SSQE';
  }
  if (normalized === 'OFFICE SUPT') {
    return 'OFFICE_SUPT';
  }
  if (normalized === 'PHYSICAL VERIFIER') {
    return 'PHYSICAL_VERIFIER';
  }
  return normalized;
}

function resolveRoleCode(
  user: ReturnType<typeof useAuth>['user'],
  fallbackRole: string | undefined
) {
  const centralRole = normalizeRoleCode(user?.role || fallbackRole);
  const safetyRole = normalizeRoleCode(
    user?.safety_role_name || user?.role_name || user?.rank
  );
  if (safetyRole) {
    return safetyRole;
  }
  if (CENTRAL_OFFICE_ROLE_CODES.has(centralRole)) {
    return centralRole;
  }
  return centralRole;
}

function phasePath(id: string | undefined, phase: number) {
  return incidentPhaseRoute(id ?? '', phase);
}

interface IncidentFleetAlertVessel {
  display_name: string;
  has_email?: boolean;
  vessel_code?: string;
  vessel_id: string;
  vessel_name?: string;
}

export function SafetyIncidentPhase7() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, role, hasProcess } = useAuth();
  const [preflight, setPreflight] =
    useState<SafetyIncidentPhase7Preflight>(emptyPreflight());
  const [typedName, setTypedName] = useState(() =>
    resolveSignatureTypedName(user)
  );
  const [officeComment, setOfficeComment] = useState('');
  const [device] = useState(() => getSafetyDeviceFingerprint());
  const [sendBackReason, setSendBackReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [includeLossEvaluationInPdf, setIncludeLossEvaluationInPdf] =
    useState(false);
  const [fleetAlertOpen, setFleetAlertOpen] = useState(false);
  const [fleetAlertVessels, setFleetAlertVessels] = useState<
    IncidentFleetAlertVessel[]
  >([]);
  const [selectedFleetAlertVesselIds, setSelectedFleetAlertVesselIds] =
    useState<string[]>([]);
  const [isFleetAlertLoading, setIsFleetAlertLoading] = useState(false);
  const [isFleetAlertSending, setIsFleetAlertSending] = useState(false);

  const reload = useCallback(async () => {
    if (!id) {
      setError('Invalid incident id.');
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const response = await safetyApi.getIncidentPhase7Preflight(id);
      const payload = response as unknown as SafetyIncidentPhase7Preflight;
      setPreflight(payload);
      setOfficeComment(String(payload.office_comment ?? ''));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const actionLabel = 'Accept / Close';

  const authority = preflight.authority;
  const requiredProcessId =
    authority?.required_process_id || preflight.required_process_id;
  const currentRoleCode = resolveRoleCode(user, role);
  const allowedRoleCodes = new Set(
    (authority?.allowed_role_codes ?? []).map(normalizeCode)
  );
  const allowedProcessIds = authority?.allowed_process_ids?.length
    ? authority.allowed_process_ids
    : OFFICE_REVIEW_PROCESS_IDS;
  const hasRequiredProcess =
    allowedProcessIds.some((processId) => hasProcess(processId)) ||
    (requiredProcessId ? hasProcess(requiredProcessId) : false);
  const hodSignatureMissing = false;
  const canSignHod =
    hodSignatureMissing && HOD_SIGNER_ROLE_CODES.has(currentRoleCode);
  const actionBlockers = useMemo(() => {
    const blockers = new Set(preflight.blockers);
    return Array.from(blockers);
  }, [preflight.blockers]);
  const hasBandAuthority = useMemo(() => {
    if (allowedRoleCodes.size > 0) {
      return allowedRoleCodes.has(currentRoleCode);
    }
    return OFFICE_REVIEW_ROLE_CODES.has(currentRoleCode);
  }, [allowedRoleCodes, currentRoleCode]);
  const canSubmitAcceptance =
    hasRequiredProcess && hasBandAuthority && actionBlockers.length === 0;
  const isOfficeReviewUser =
    hasBandAuthority || CENTRAL_OFFICE_ROLE_CODES.has(currentRoleCode);
  const allFleetAlertVesselIds = useMemo(
    () => fleetAlertVessels.map((vessel) => vessel.vessel_id),
    [fleetAlertVessels]
  );
  const allFleetAlertVesselsSelected =
    allFleetAlertVesselIds.length > 0 &&
    allFleetAlertVesselIds.every((vesselId) =>
      selectedFleetAlertVesselIds.includes(vesselId)
    );
  const pdfControlsVisible = Boolean(
    preflight.pdf_preview.download_path || preflight.pdf_preview.message
  );
  const hasVisibleOfficeComment = officeComment.trim().length > 0;
  const reworkSummaryComment = String(
    preflight.rework_summary?.comment ?? ''
  );
  const hasReworkSummary = reworkSummaryComment.trim().length > 0;
  const blockerLabels = actionBlockers.map((blocker) =>
    blocker.replace(/_/g, ' ')
  );
  const disabledReasons = useMemo(() => {
    const reasons: string[] = [];
    if (!typedName.trim()) {
      reasons.push('Typed full name is required.');
    }
    if (actionBlockers.length > 0) {
      reasons.push(
        blockerLabels.length > 0
          ? `Please fix this first: ${blockerLabels.join(', ')}.`
          : 'Please fix the pending items first.'
      );
    }
    if (!hasRequiredProcess) {
      reasons.push('This action is not available for your login.');
    }
    if (!hasBandAuthority) {
      reasons.push('Your current login cannot approve this incident.');
    }
    return reasons;
  }, [
    actionBlockers.length,
    blockerLabels,
    hasBandAuthority,
    hasRequiredProcess,
    requiredProcessId,
    typedName,
  ]);

  async function submitAcceptance(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const currentPhaseBeforeAcceptance = Number(preflight.current_phase ?? 0);
      if (currentPhaseBeforeAcceptance < 7) {
        await safetyApi.transitionIncident(id, { target_phase: 7 });
        setPreflight((current) => ({ ...current, current_phase: 7 }));
      }
      const payload = {
        device_fingerprint: device,
        office_comment: officeComment,
        typed_name: typedName,
      };
      const response = await safetyApi.acceptIncidentPhase7(id, payload);
      const currentPhase = Number(
        response.current_phase ?? preflight.current_phase
      );
      if (currentPhase >= 8) {
        navigate(phasePath(id, 8));
        return;
      }
      setResultMessage('Office Review signature captured.');
      setTypedName('');
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitHodSignature() {
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      await safetyApi.signIncidentPhase7Hod(id, {
        device_fingerprint: device,
        typed_name: typedName,
      });
      setResultMessage('HOD signature captured.');
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitSendBack(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.sendBackIncidentPhase7(id, {
        reason: sendBackReason,
        target_phase: SEND_BACK_TARGET_PHASE,
      });
      const targetPhase = Number(
        response.current_phase ?? SEND_BACK_TARGET_PHASE
      );
      navigate(phasePath(id, targetPhase));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function markReworkDone() {
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      await safetyApi.transitionIncident(id, { target_phase: 7 });
      setResultMessage('Rework marked done.');
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  const pdfSectionKeys = useMemo(() => {
    if (includeLossEvaluationInPdf) {
      return [
        ...REQUIRED_INCIDENT_PDF_SECTION_KEYS,
        LOSS_EVALUATION_PDF_SECTION_KEY,
      ];
    }
    return REQUIRED_INCIDENT_PDF_SECTION_KEYS;
  }, [includeLossEvaluationInPdf]);

  async function downloadPdf() {
    if (!id || !preflight.pdf_preview.available) {
      return;
    }
    setIsMutating(true);
    setError(null);
    try {
      const { blob, fileName } = await safetyApi.downloadIncidentPdf(
        id,
        pdfSectionKeys
      );
      const downloadUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = downloadUrl;
      anchor.download = fileName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 60_000);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function openFleetAlertSelector() {
    if (!id) {
      return;
    }
    if (fleetAlertOpen) {
      setFleetAlertOpen(false);
      return;
    }
    setFleetAlertOpen(true);
    if (fleetAlertVessels.length > 0) {
      return;
    }
    setIsFleetAlertLoading(true);
    setError(null);
    try {
      const currentPhaseBeforeFleetAlert = Number(preflight.current_phase ?? 0);
      if (currentPhaseBeforeFleetAlert < 7) {
        const transition = await safetyApi.transitionIncident(id, {
          target_phase: 7,
        });
        setPreflight((current) => ({
          ...current,
          current_phase: Number(transition?.current_phase ?? 7),
        }));
      }
      const response = await safetyApi.getIncidentFleetAlert(id);
      const vessels = Array.isArray(response.recipient_vessels)
        ? (response.recipient_vessels as IncidentFleetAlertVessel[])
        : [];
      setFleetAlertVessels(vessels);
    } catch (caught) {
      setError(getErrorMessage(caught));
      setFleetAlertOpen(false);
    } finally {
      setIsFleetAlertLoading(false);
    }
  }

  async function submitFleetAlert() {
    if (!id || selectedFleetAlertVesselIds.length === 0) {
      return;
    }
    setIsFleetAlertSending(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.issueIncidentFleetAlert(id, {
        recipient_vessel_ids: selectedFleetAlertVesselIds,
      });
      const responseRecipientIds = Array.isArray(response.recipient_vessel_ids)
        ? response.recipient_vessel_ids
        : [];
      const vesselCount =
        responseRecipientIds.length || selectedFleetAlertVesselIds.length;
      const emailsSent = Number(response.emails_sent ?? 0);
      const emailFailed = Number(response.email_failed ?? 0);
      const vesselsWithoutEmail = Number(response.vessels_without_email ?? 0);
      const addressedVesselCount =
        emailsSent > 1
          ? emailsSent
          : Math.max(0, vesselCount - emailFailed - vesselsWithoutEmail);
      const deliveryParts = [
        `Email batch addressed to ${addressedVesselCount} vessel(s)`,
      ];
      if (emailFailed > 0) {
        deliveryParts.push(`failed: ${emailFailed}`);
      }
      if (vesselsWithoutEmail > 0) {
        deliveryParts.push(`without email: ${vesselsWithoutEmail}`);
      }
      setResultMessage(
        `Fleet alert sent to ${vesselCount} selected ship(s). ${deliveryParts.join(', ')}.`
      );
      setSelectedFleetAlertVesselIds([]);
      setFleetAlertOpen(false);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsFleetAlertSending(false);
    }
  }

  function toggleFleetAlertVessel(vesselId: string) {
    setSelectedFleetAlertVesselIds((current) =>
      current.includes(vesselId)
        ? current.filter((value) => value !== vesselId)
        : [...current, vesselId]
    );
  }

  function toggleAllFleetAlertVessels() {
    setSelectedFleetAlertVesselIds(
      allFleetAlertVesselsSelected ? [] : allFleetAlertVesselIds
    );
  }

  const pdfPreviewReady = Boolean(
    preflight.pdf_preview.available && preflight.pdf_preview.download_path
  );

  return (
    <section className="space-y-6">
      {error ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {error}
        </section>
      ) : null}
      {resultMessage ? (
        <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {resultMessage}
        </section>
      ) : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
          Loading Office Review...
        </section>
      ) : (
        <>
          {hodSignatureMissing ? (
            <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-amber-950">
                    HOD Sign Needed
                  </h2>
                  <p className="mt-1 leading-6">
                    The department HOD must sign before office can approve.
                  </p>
                </div>
                <button
                  className="min-h-11 rounded-full bg-amber-950 px-5 text-sm font-semibold text-white disabled:bg-amber-300"
                  disabled={isMutating || !typedName.trim() || !canSignHod}
                  onClick={() => void submitHodSignature()}
                  type="button"
                >
                  {isMutating ? 'Signing...' : 'Add HOD Sign'}
                </button>
              </div>
              {!canSignHod ? (
                <p className="mt-3 rounded-2xl border border-amber-300 bg-white/70 px-3 py-2">
                  Login as HOD, Chief Engineer, or Chief Officer to sign.
                </p>
              ) : null}
            </section>
          ) : null}

          {hasReworkSummary ? (
            <section className="rounded-3xl border border-rose-300 bg-rose-50 p-5 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-rose-950">
                    Rework summary
                  </h2>
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-rose-950">
                    {reworkSummaryComment}
                  </p>
                </div>
                <button
                  className="min-h-11 rounded-full bg-rose-700 px-5 text-sm font-semibold text-white disabled:bg-rose-300"
                  disabled={isMutating}
                  onClick={() => void markReworkDone()}
                  type="button"
                >
                  {isMutating ? 'Updating...' : 'Rework Done'}
                </button>
              </div>
            </section>
          ) : null}

          {!isOfficeReviewUser ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">
                Office Comments/lesson learnt
              </h2>
              {hasVisibleOfficeComment ? (
                <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                  {officeComment}
                </p>
              ) : (
                <p className="mt-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  Office comment is not added yet.
                </p>
              )}
            </section>
          ) : null}

          {isOfficeReviewUser ? (
            <div className="grid gap-6 xl:grid-cols-2">
              <form
                className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
                onSubmit={submitAcceptance}
              >
                <h2 className="text-xl font-semibold text-slate-900">
                  {actionLabel}
                </h2>
                {disabledReasons.length > 0 ? (
                  <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                    {disabledReasons[0]}
                  </p>
                ) : null}
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Office Comments/lesson learnt
                  <textarea
                    className="mt-2 min-h-36 w-full rounded-2xl border border-slate-300 p-3"
                    disabled={isMutating}
                    onChange={(event) => setOfficeComment(event.target.value)}
                    placeholder="Enter office review comments or lessons learnt."
                    value={officeComment}
                  />
                </label>
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Type your full name
                  <input
                    className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                    onChange={(event) => setTypedName(event.target.value)}
                    value={typedName}
                  />
                </label>
                <button
                  className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
                  disabled={
                    isMutating ||
                    disabledReasons.length > 0 ||
                    !canSubmitAcceptance
                  }
                  type="submit"
                >
                  {isMutating ? 'Submitting...' : actionLabel}
                </button>
                <div className="mt-5 border-t border-slate-200 pt-5">
                  <button
                    className="min-h-11 rounded-full border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-800 disabled:bg-slate-100 disabled:text-slate-400"
                    disabled={isMutating || isFleetAlertLoading}
                    onClick={() => void openFleetAlertSelector()}
                    type="button"
                  >
                    {isFleetAlertLoading ? 'Loading ships...' : 'Fleet Alert'}
                  </button>
                </div>
              </form>

              <form
                className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
                onSubmit={submitSendBack}
              >
                <h2 className="text-xl font-semibold text-slate-900">
                  Send for rework
                </h2>
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Comment
                  <textarea
                    className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                    onChange={(event) => setSendBackReason(event.target.value)}
                    value={sendBackReason}
                  />
                </label>
                <button
                  className="mt-4 min-h-11 rounded-full border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
                  disabled={isMutating || !sendBackReason.trim()}
                  type="submit"
                >
                  Send for rework
                </button>
              </form>
            </div>
          ) : null}
        </>
      )}

      {fleetAlertOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
          <section
            aria-labelledby="fleet-alert-dialog-title"
            aria-modal="true"
            className="max-h-[85vh] w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-xl"
            role="dialog"
          >
            <div className="border-b border-slate-200 px-5 py-4">
              <h2
                className="text-lg font-semibold text-slate-900"
                id="fleet-alert-dialog-title"
              >
                Select vessels for Fleet Alert
              </h2>
            </div>
            <div className="max-h-[55vh] overflow-y-auto px-5 py-4">
              {isFleetAlertLoading ? (
                <p className="text-sm text-slate-600">Loading vessels...</p>
              ) : fleetAlertVessels.length > 0 ? (
                <div className="space-y-2">
                  <label className="flex min-h-12 items-center gap-3 rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-900">
                    <input
                      checked={allFleetAlertVesselsSelected}
                      className="h-4 w-4 rounded border-slate-300"
                      disabled={isFleetAlertSending}
                      onChange={toggleAllFleetAlertVessels}
                      type="checkbox"
                    />
                    <span>Select all vessels</span>
                  </label>
                  {fleetAlertVessels.map((vessel) => (
                    <label
                      className="flex min-h-12 items-center gap-3 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-800"
                      key={vessel.vessel_id}
                    >
                      <input
                        checked={selectedFleetAlertVesselIds.includes(
                          vessel.vessel_id
                        )}
                        className="h-4 w-4 rounded border-slate-300"
                        disabled={isFleetAlertSending}
                        onChange={() =>
                          toggleFleetAlertVessel(vessel.vessel_id)
                        }
                        type="checkbox"
                      />
                      <span className="flex-1">
                        <span className="block font-medium">
                          {vessel.display_name}
                        </span>
                        {vessel.has_email === false ? (
                          <span className="text-xs text-amber-700">
                            Email not recorded in VesselData
                          </span>
                        ) : null}
                      </span>
                    </label>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-600">
                  No active vessels are available.
                </p>
              )}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4">
              <span className="text-sm text-slate-600">
                {selectedFleetAlertVesselIds.length} selected
              </span>
              <div className="flex flex-wrap items-center gap-3">
                <button
                  className="min-h-10 rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
                  disabled={isFleetAlertSending}
                  onClick={() => setFleetAlertOpen(false)}
                  type="button"
                >
                  Cancel
                </button>
                <button
                  className="min-h-10 rounded-full bg-slate-900 px-4 text-sm font-semibold text-white disabled:bg-slate-400"
                  disabled={
                    isFleetAlertLoading ||
                    isFleetAlertSending ||
                    selectedFleetAlertVesselIds.length === 0
                  }
                  onClick={() => void submitFleetAlert()}
                  type="button"
                >
                  {isFleetAlertSending ? 'Sending...' : 'Confirm'}
                </button>
              </div>
            </div>
          </section>
        </div>
      ) : null}

      {pdfControlsVisible ? (
        <section
          aria-labelledby="incident-pdf-options-title"
          className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <h2
            className="text-lg font-semibold text-slate-900"
            id="incident-pdf-options-title"
          >
            PDF Options
          </h2>
          <label className="mt-4 flex min-h-11 items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-800">
            <input
              checked={includeLossEvaluationInPdf}
              className="h-4 w-4 rounded border-slate-300"
              disabled={isMutating || !pdfPreviewReady}
              onChange={(event) =>
                setIncludeLossEvaluationInPdf(event.target.checked)
              }
              type="checkbox"
            />
            Print Loss Evaluation
          </label>
        </section>
      ) : null}

      <div className="flex flex-wrap gap-3">
        {isOfficeReviewUser ? (
          <Link
            className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
            to={`/safety/incidents/${id}/phase-3/preventive`}
          >
            Back to Preventive Action
          </Link>
        ) : null}
        {pdfControlsVisible ? (
          <button
            className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
            disabled={isMutating || !pdfPreviewReady}
            onClick={() => void downloadPdf()}
            title={pdfPreviewReady ? undefined : preflight.pdf_preview.message}
            type="button"
          >
            Download PDF
          </button>
        ) : null}
      </div>
    </section>
  );
}

export default SafetyIncidentPhase7;
