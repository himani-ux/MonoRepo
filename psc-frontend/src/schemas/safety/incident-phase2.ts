import { z } from "zod";

import {
  safetyIncidentImoClassifierSchema,
  safetyIncidentRiskBandSchema,
} from "./incident";
import { safetySchemaVersionSchema } from "./common";

export const SAFETY_INCIDENT_PHASE_2_SCHEMA_VERSION = 1;

export const safetyIncidentPhase2Schema = z.object({
  dpa_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  fm_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  imo_classifier: safetyIncidentImoClassifierSchema.optional(),
  investigation_depth: z.enum(["SHALLOW", "MEDIUM", "DEEP"]).nullable().optional(),
  latitude: z.string().optional(),
  longitude: z.string().optional(),
  loss_type_primary_id: z.coerce.number().int().positive().nullable().optional(),
  loss_type_secondary_id: z.coerce.number().int().positive().nullable().optional(),
  loss_type_tertiary_id: z.coerce.number().int().positive().nullable().optional(),
  loss_type_other: z.string().max(256, "Keep Other loss below 256 characters.").nullable().optional(),
  office_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  office_notification_mode: z.enum(["ON_CALL", "WHATSAPP", "EMAIL"]).nullable().optional(),
  office_notified: z.boolean().nullable().optional(),
  pic_user_id: z.string().nullable().optional(),
  risk_band: safetyIncidentRiskBandSchema.optional(),
  schema_version: safetySchemaVersionSchema.default(
    SAFETY_INCIDENT_PHASE_2_SCHEMA_VERSION,
  ),
});

export const safetyIncidentPhase2SubmitSchema = safetyIncidentPhase2Schema.superRefine(
  (values, ctx) => {
    const selectedLossTypes = [
      values.loss_type_primary_id,
      values.loss_type_secondary_id,
      values.loss_type_tertiary_id,
    ].filter((value): value is number => typeof value === "number");
    const otherSelected = values.loss_type_other !== null && values.loss_type_other !== undefined;
    const totalLossTypes = selectedLossTypes.length + (otherSelected ? 1 : 0);

    if (new Set(selectedLossTypes).size !== selectedLossTypes.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Do not select the same loss type twice.",
        path: ["loss_type_primary_id"],
      });
    }

    if (totalLossTypes > 3) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Select up to 3 loss types only.",
        path: ["loss_type_primary_id"],
      });
    }

    if (otherSelected && !values.loss_type_other?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Write the other loss type.",
        path: ["loss_type_other"],
      });
    }

    if (!values.risk_band) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Select risk level before submitting.",
        path: ["risk_band"],
      });
    }

    if (values.office_notified === null || values.office_notified === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Select if office was informed.",
        path: ["office_notified"],
      });
    }

    if (values.office_notified === true && !values.office_notification_mode) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Select how office was informed.",
        path: ["office_notification_mode"],
      });
    }
  },
);

export type SafetyIncidentPhase2Values = z.infer<typeof safetyIncidentPhase2Schema>;
export type SafetyIncidentPhase2SubmitValues = z.infer<
  typeof safetyIncidentPhase2SubmitSchema
>;
