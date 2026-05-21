import { z } from "zod";

export const SAFETY_NEAR_MISS_SCHEMA_VERSION = 1 as const;

export const safetyNearMissSchema = z.object({
  incident_type_id: z.coerce.number().int().positive().nullable().optional(),
  loss_type_primary_id: z.coerce.number().int().positive().nullable().optional(),
  narrative: z.string().default(""),
  near_miss_immediate_action: z.string().default(""),
  near_miss_mscat_category_id: z.coerce.number().int().positive().nullable().optional(),
  near_miss_mscat_subcode_id: z.string().nullable().optional(),
  near_miss_severity: z.enum(["HIGH", "MED", "LOW"]).nullable().optional(),
  near_miss_shell_tag: z
    .enum(["Software", "Hardware", "Environment", "Liveware", "Liveware-Liveware"])
    .nullable()
    .optional(),
  near_miss_suggestion: z.string().default(""),
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
  loss_type_primary_id: z.coerce.number().int().positive("Select loss type."),
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
