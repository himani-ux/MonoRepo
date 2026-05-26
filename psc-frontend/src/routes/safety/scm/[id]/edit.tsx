import { useMutation } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import SafetyScmTenSectionForm from "../../../../components/safety/scm/scm-10-section-form";
import {
  useSafetyScmAttendance,
  useSafetyScmCreateAdhocConfig,
  useSafetyScmCreateRegularConfig,
  useSafetyScmMeeting,
  useSafetyScmOpenFindings,
} from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { safetyApi, type SafetyScmCreateAttendeeRow } from "../../../../lib/api/safety";

function normalizeMeetingType(value: string | null | undefined): "REGULAR" | "AD_HOC" {
  return String(value || "").toUpperCase() === "AD_HOC" ? "AD_HOC" : "REGULAR";
}

function normalizeAttendanceRows(rows: SafetyScmCreateAttendeeRow[]): SafetyScmCreateAttendeeRow[] {
  return rows.map((row) => ({
    ...row,
    absence_reason: row.absence_reason ?? null,
    department: row.department ?? "",
    present: row.present ?? true,
    remarks: row.remarks ?? null,
    schema_version: row.schema_version ?? 1,
    warning_codes: row.warning_codes ?? [],
    warnings: row.warnings ?? [],
    wrh_data_available: row.wrh_data_available ?? false,
    wrh_flag: row.wrh_flag ?? "RED",
    wrh_non_compliance_flag: row.wrh_non_compliance_flag ?? false,
    wrh_rest_hours_24h: row.wrh_rest_hours_24h ?? null,
    wrh_rest_hours_7d: row.wrh_rest_hours_7d ?? null,
  }));
}

export default function SafetyScmEditRoute() {
  const params = useParams();
  const navigate = useNavigate();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const meetingQuery = useSafetyScmMeeting(meetingId, enabled);
  const meeting = meetingQuery.data;
  const meetingType = normalizeMeetingType(meeting?.meeting_type);
  const vesselId = meeting?.vessel_id ?? "";
  const regularConfigQuery = useSafetyScmCreateRegularConfig(
    vesselId,
    enabled && Boolean(vesselId) && meetingType === "REGULAR",
  );
  const adhocConfigQuery = useSafetyScmCreateAdhocConfig(
    vesselId,
    enabled && Boolean(vesselId) && meetingType === "AD_HOC",
  );
  const attendanceQuery = useSafetyScmAttendance(meetingId, enabled);
  const autoFeedQuery = useSafetyScmOpenFindings(vesselId, enabled && Boolean(vesselId));
  const updateMutation = useMutation({
    mutationFn: safetyApi.updateScmMeeting.bind(null, meetingId),
    onSuccess: (updated) => navigate(`/safety/scm/${updated.id}`),
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SCM meeting id.
      </section>
    );
  }

  const configQuery = meetingType === "AD_HOC" ? adhocConfigQuery : regularConfigQuery;
  if (meetingQuery.isLoading || configQuery.isLoading || attendanceQuery.isLoading || autoFeedQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM edit form...
      </section>
    );
  }

  if (meetingQuery.isError || configQuery.isError || attendanceQuery.isError || autoFeedQuery.isError) {
    const error = meetingQuery.error ?? configQuery.error ?? attendanceQuery.error ?? autoFeedQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  if (!meeting || !configQuery.data) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        SCM meeting could not be loaded.
      </section>
    );
  }

  if (meeting.is_reviewed || meeting.office_comment_at) {
    return (
      <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        This SCM has already been reviewed by office and can no longer be edited.
      </section>
    );
  }

  const attendanceRows = normalizeAttendanceRows(
    (attendanceQuery.data?.rows as SafetyScmCreateAttendeeRow[] | undefined) ?? configQuery.data.attendee_rows,
  );
  const editConfig = {
    ...configQuery.data,
    attendee_rows: attendanceRows,
    meeting_date_default: meeting.meeting_date,
    meeting_type: meetingType,
    sections: meeting.sections,
    vessel: {
      id: meeting.vessel_id,
      vessel_code: meeting.vessel_code || configQuery.data.vessel.vessel_code,
      vessel_name: meeting.vessel_name || meeting.vessel_display_name || configQuery.data.vessel.vessel_name,
    },
  };

  return (
    <>
      <SafetyScmTenSectionForm
        autoFeedPayload={autoFeedQuery.data}
        config={editConfig}
        formMode="edit"
        initialValues={{
          ad_hoc_trigger_reason: meeting.ad_hoc_trigger_reason ?? "",
          attendance_rows: attendanceRows,
          chair_crew_id: meeting.chair_crew_id ?? "",
          comm_time: meeting.comm_time ?? "",
          comp_time: meeting.comp_time ?? "",
          latitude: meeting.latitude ?? "",
          location: meeting.location ?? "",
          longitude: meeting.longitude ?? "",
          meeting_date: meeting.meeting_date,
          meeting_time_local: meeting.meeting_time_local ?? "",
          meeting_type: meetingType,
          occasion: meeting.occasion || "M",
          schema_version: meeting.schema_version,
          sections: meeting.sections,
          ship_pos_from: meeting.ship_pos_from ?? "",
          ship_pos_to: meeting.ship_pos_to ?? "",
          ship_position: meeting.ship_position === "S" ? "S" : "P",
          vessel_code: meeting.vessel_code ?? editConfig.vessel.vessel_code,
          vessel_id: meeting.vessel_id,
          voyage_no: meeting.voyage_no ?? "",
        }}
        isSubmitting={updateMutation.isPending}
        mode={meetingType === "AD_HOC" ? "adhoc" : "regular"}
        onSubmit={(values) => {
          if (!updateMutation.isPending) {
            updateMutation.mutate(values);
          }
        }}
        submitLabel="Update Meeting"
        submittingLabel="Updating..."
      />
      {updateMutation.isError ? (
        <section className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(updateMutation.error)}
        </section>
      ) : null}
    </>
  );
}
