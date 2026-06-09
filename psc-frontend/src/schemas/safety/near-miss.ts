import { z } from "zod";

export const SAFETY_NEAR_MISS_SCHEMA_VERSION = 1 as const;

export const SAFETY_NEAR_MISS_CATEGORY_TAGS = [
  "Safety",
  "Security",
  "Environment",
  "MLC",
  "Training",
  "Operational",
  "Management",
  "Others",
] as const;

export const SAFETY_NEAR_MISS_OTHER_PREFIX = "Others:" as const;

export const SAFETY_NEAR_MISS_PLACES = [
  { label: "At Anchor", value: "AT_ANCHOR" },
  { label: "At Sea", value: "AT_SEA" },
  { label: "At Port", value: "AT_PORT" },
] as const;

export const SAFETY_NEAR_MISS_LOSS_OPTIONS = [
  { label: "Injury", value: 1 },
  { label: "Property Damage", value: 2 },
  { label: "Environment", value: 3 },
  { label: "Financial", value: 4 },
  { label: "Reputation", value: 6 },
  { label: "Time", value: 7 },
  { label: "Non-conformity", value: 5 },
] as const;

export const safetyNearMissSchema = z.object({
  incident_type_id: z.coerce.number().int().positive().nullable().optional(),
  loss_type_primary_id: z.coerce.number().int().positive().nullable().optional(),
  narrative: z.string().default(""),
  near_miss_immediate_action: z.string().default(""),
  near_miss_place: z.enum(["AT_ANCHOR", "AT_SEA", "AT_PORT"]).nullable().optional(),
  near_miss_category_tags: z.array(z.string().trim().min(1)).max(3).default([]),
  near_miss_incident_type_ids: z.array(z.coerce.number().int().positive()).max(3).default([]),
  near_miss_mscat_category_id: z.coerce.number().int().positive().nullable().optional(),
  near_miss_mscat_subcode_id: z.string().nullable().optional(),
  near_miss_mscat_subcode_ids: z.array(z.string().min(1)).max(3).default([]),
  near_miss_severity: z.enum(["HIGH", "MED", "LOW"]).nullable().optional(),
  near_miss_shell_tag: z
    .string()
    .trim()
    .min(1)
    .nullable()
    .optional(),
  near_miss_suggestion: z.string().default(""),
  near_miss_root_cause_detail: z.string().default(""),
  near_miss_corrective_action: z.string().default(""),
  near_miss_weather_voyage_details: z.string().default(""),
  near_miss_equipment_details: z.string().default(""),
  near_miss_lessons_learned: z.string().default(""),
  occurred_at: z.string().default(""),
  reporter_device_fingerprint: z.string().default(""),
  reporter_name: z.string().default(""),
  reporter_rank: z.string().default(""),
  reporter_user_id: z.string().default(""),
  schema_version: z.literal(SAFETY_NEAR_MISS_SCHEMA_VERSION),
  vessel_code: z.string().min(1).optional(),
  vessel_id: z.string().min(1),
});

export const safetyNearMissSubmitSchema = safetyNearMissSchema.extend({
  incident_type_id: z.coerce.number().int().positive("Select incident type."),
  loss_type_primary_id: z.coerce.number().int().positive("Select category."),
  near_miss_category_tags: z.array(z.string().trim().min(1)).min(1, "Select category.").max(3),
  narrative: z
    .string()
    .trim()
    .min(100, "Near-miss description must be at least 100 characters (D-GAP-M38)."),
  occurred_at: z
    .string()
    .datetime({ offset: true, message: "Enter a valid occurred time." })
    .refine((value) => new Date(value).getTime() <= Date.now(), {
      message: "Occurred time cannot be in the future.",
    }),
  near_miss_immediate_action: z.string().trim().min(1, "Record the immediate action taken."),
  near_miss_severity: z.enum(["HIGH", "MED", "LOW"], {
    errorMap: () => ({ message: "Select a severity level before submitting." }),
  }),
  reporter_device_fingerprint: z.string().min(1, "Reporter signature device data was not captured. Refresh and try again."),
  reporter_name: z.string().min(1),
  reporter_rank: z.string().min(1),
  reporter_user_id: z.string().min(1),
});

export type SafetyNearMissValues = z.infer<typeof safetyNearMissSchema>;
export type SafetyNearMissSubmitValues = z.infer<typeof safetyNearMissSubmitSchema>;
