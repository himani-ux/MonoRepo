import { z } from "zod";

const safetyIsoDateTimeSchema = z
  .string()
  .datetime({ offset: true })
  .or(z.string().datetime());

export const safetyOptionalStringSchema = z.preprocess(
  (value) => {
    if (value === null || value === undefined) {
      return undefined;
    }
    if (typeof value !== "string") {
      return value;
    }
    const trimmed = value.trim();
    return trimmed === "" ? undefined : trimmed;
  },
  z.string().min(1).optional(),
);

export const safetyOptionalNullableStringSchema = z.preprocess(
  (value) => {
    if (value === undefined) {
      return undefined;
    }
    if (value === null) {
      return null;
    }
    if (typeof value !== "string") {
      return value;
    }
    const trimmed = value.trim();
    return trimmed === "" ? null : trimmed;
  },
  z.string().min(1).nullable().optional(),
);

export const safetyVesselIdSchema = z.coerce.number().int().positive();

export const safetySchemaVersionSchema = z.coerce.number().int().positive();

export const safetyAttachmentRefSchema = z.object({
  content_type: z.string().min(1).optional(),
  file_name: z.string().min(1),
  file_path: z.string().min(1).optional(),
  id: z.string().min(1),
  uploaded_at: safetyIsoDateTimeSchema.nullable().optional(),
});

export const safetyTimestampsSchema = z.object({
  created_at: safetyIsoDateTimeSchema,
  updated_at: safetyIsoDateTimeSchema.nullable().optional(),
});

export const safetyCommonRecordSchema = z.object({
  attachments: z.array(safetyAttachmentRefSchema).default([]),
  schema_version: safetySchemaVersionSchema,
  vessel_id: safetyVesselIdSchema,
});

export type SafetyAttachmentRef = z.infer<typeof safetyAttachmentRefSchema>;
export type SafetyCommonRecord = z.infer<typeof safetyCommonRecordSchema>;
export type SafetyTimestamps = z.infer<typeof safetyTimestampsSchema>;
