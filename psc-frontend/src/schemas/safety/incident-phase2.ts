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
  office_notified_at: z.string().datetime({ offset: true }).nullable().optional(),
  pic_user_id: z.string().nullable().optional(),
  risk_band: safetyIncidentRiskBandSchema.optional(),
  schema_version: safetySchemaVersionSchema.default(
    SAFETY_INCIDENT_PHASE_2_SCHEMA_VERSION,
  ),
});

export const safetyIncidentPhase2SubmitSchema = safetyIncidentPhase2Schema.superRefine(
  (values, ctx) => {
    if (!values.risk_band) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Internal risk band is required before submitting Phase 2.",
        path: ["risk_band"],
      });
    }

    if (!values.imo_classifier) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "IMO classifier is required before submitting Phase 2.",
        path: ["imo_classifier"],
      });
    }

    if (
      values.imo_classifier &&
      values.imo_classifier !== "NOT_APPLICABLE" &&
      (!values.latitude || !values.longitude)
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Latitude is required for IMO-classified casualties.",
        path: ["latitude"],
      });
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Longitude is required for IMO-classified casualties.",
        path: ["longitude"],
      });
    }
  },
);

export type SafetyIncidentPhase2Values = z.infer<typeof safetyIncidentPhase2Schema>;
export type SafetyIncidentPhase2SubmitValues = z.infer<
  typeof safetyIncidentPhase2SubmitSchema
>;
