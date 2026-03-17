# VALIDATION_RULES.md — Field Validation & Business Rules
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-04 | **Status:** APPROVED

---

## 1. Overview

This document consolidates all validation rules for the PSC module. **Both frontend and backend MUST implement these rules.** No exceptions.

### 1.1 Validation Principles

1. **Fail Fast:** Validate on the frontend before API call
2. **Trust No One:** Backend validates everything, regardless of frontend validation
3. **Clear Messages:** Error messages must be user-friendly and actionable
4. **Field-Level Errors:** Return errors per field, not generic messages

---

## 2. Inspection Validation

### 2.1 Create Inspection

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `vessel_id` | UUID | ✅ | Must exist in VesselData, not deleted | "Invalid vessel" |
| `inspection_type` | String | ✅ | Must be: PSC, RS, AUDIT, INTERNAL | "Invalid inspection type" |
| `psc_subtype` | String | ❌* | Required if inspection_type = PSC. Must be: INITIAL, EXPANDED, CIC, FOLLOW_UP | "PSC subtype is required for PSC inspections" |
| `inspection_date` | Date | ✅ | Cannot be in future | "Inspection date cannot be in the future" |
| `port_place` | String | ✅ | Min 2 chars, max 200 chars | "Port/Place is required (2-200 characters)" |
| `country` | String | ❌ | Max 100 chars | "Country must be less than 100 characters" |
| `mou_id` | UUID | ❌* | Required if inspection_type = PSC. Must exist in master_mou | "Invalid MOU selection" |
| `authority` | String | ❌ | Max 200 chars | "Authority must be less than 200 characters" |
| `inspector_name` | String | ❌ | Max 200 chars | "Inspector name must be less than 200 characters" |
| `report_reference` | String | ❌ | Max 100 chars | "Report reference must be less than 100 characters" |
| `is_detention` | Boolean | ❌ | Default false | - |

### 2.2 Submit Inspection

**Preconditions (all must pass):**

| Rule | Error Message |
|------|---------------|
| Status must be DRAFT | "Only draft inspections can be submitted" |
| At least 1 report file attached | "Inspection report must be attached before submission" |
| All deficiencies have valid def_code | "All deficiencies must have a deficiency code" |

### 2.3 PIC Review Inspection

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `comment` | String | ✅ | Min 10 chars | "PIC comment is required (minimum 10 characters)" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be SUBMITTED | "Only submitted inspections can be reviewed" |
| User must be OFFICE_PIC, OFFICE_SSQE, or OFFICE_SUPT | "Only PIC/SSQE/Superintendent can review inspections" |

### 2.4 DPA Close Inspection

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `comment` | String | ✅ | Min 10 chars | "DPA comment is required (minimum 10 characters)" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be PIC_REVIEWED | "Only PIC-reviewed inspections can be closed by DPA" |
| User must be DPA | "Only DPA can close inspections" |

### 2.5 Delete Inspection

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be DRAFT | "Only draft inspections can be deleted" |
| User must be VESSEL_MASTER | "Only Vessel Master can delete inspections" |

---

## 3. Deficiency Validation

### 3.1 Add Deficiency

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `def_code_id` | UUID | ✅ | Must exist in master_psc_def_code, is_active = 1 | "Invalid deficiency code" |
| `description` | String | ✅ | Min 10 chars, max 4000 chars | "Description is required (10-4000 characters)" |
| `action_code_id` | UUID | ❌ | If provided, must exist in master_psc_action_code | "Invalid action code" |
| `target_date` | Date | ❌ | If provided, must be today or future | "Target date must be today or in the future" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Inspection must exist and not deleted | "Inspection not found" |
| Inspection status must be DRAFT or (SUBMITTED and user is OFFICE) | "Deficiencies can only be added to draft inspections" |

### 3.2 Update Action Code

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `action_code_id` | UUID | ✅ | Must exist in master_psc_action_code | "Invalid action code" |
| `follow_up_inspection_id` | UUID | ❌ | If provided, must exist and be a FOLLOW_UP type | "Invalid follow-up inspection" |
| `change_reason` | String | ❌ | Max 500 chars | "Reason must be less than 500 characters" |

**Business Rules:**
- Action code 30 can transition to any code (including 10)
- When action code is a "clearing code" (e.g., 10), deficiency is automatically marked cleared

---

## 4. CAR Validation

### 4.1 Update CAR (Draft/Rework)

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `root_cause_summary` | String | ❌* | Required for submission, min 50 chars | "Root cause summary must be at least 50 characters" |
| `target_date` | Date | ❌ | If provided, must be today or future | "Target date must be today or in the future" |
| `clc_item_ids` | Array<UUID> | ❌ | Each must exist in master_clc_item | "Invalid CLC item selected" |
| `custom_cause_text` | String | ❌ | Max 500 chars | "Custom cause text must be less than 500 characters" |

### 4.2 Submit CAR

**ALL preconditions must pass:**

| Rule | Error Message |
|------|---------------|
| Status must be DRAFT or REWORK_REQUESTED | "Only draft or rework CARs can be submitted" |
| `root_cause_summary` >= 50 characters | "Root cause summary must be at least 50 characters" |
| At least 1 IMMEDIATE corrective action | "At least one immediate corrective action is required" |
| At least 1 LONG_TERM corrective action | "At least one long-term corrective action is required" |
| At least 1 BEFORE evidence | "At least one BEFORE evidence photo is required" |
| At least 1 AFTER evidence | "At least one AFTER evidence photo is required" |

**Validation Summary for UI:**
```typescript
interface CarSubmissionValidation {
  root_cause_min_length: 50;
  immediate_actions_min: 1;
  long_term_actions_min: 1;
  before_evidence_min: 1;
  after_evidence_min: 1;
}
```

### 4.3 PIC Accept CAR

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `comment` | String | ✅ | Min 10 chars | "PIC comment is required (minimum 10 characters)" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be SUBMITTED | "Only submitted CARs can be accepted" |
| User must be OFFICE_PIC, OFFICE_SSQE, or OFFICE_SUPT | "Only PIC/SSQE/Superintendent can accept CARs" |

### 4.4 Request Rework

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `reason` | String | ✅ | Min 20 chars | "Rework reason must be at least 20 characters" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be SUBMITTED or PIC_ACCEPTED | "Rework can only be requested for submitted or accepted CARs" |
| User must be OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, or DPA | "Only office personnel can request rework" |

### 4.5 DPA Close CAR

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `comment` | String | ✅ | Min 10 chars | "DPA comment is required (minimum 10 characters)" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be PIC_ACCEPTED | "Only PIC-accepted CARs can be closed by DPA" |
| User must be DPA | "Only DPA can close CARs" |

---

## 5. Corrective Action Validation

### 5.1 Add Corrective Action

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `action_type` | String | ✅ | Must be: IMMEDIATE, LONG_TERM | "Invalid action type" |
| `description` | String | ✅ | Min 10 chars, max 4000 chars | "Description is required (10-4000 characters)" |
| `owner_crew_id` | UUID | ❌* | One of owner_crew_id or owner_user_id recommended | "Action owner recommended" |
| `owner_user_id` | String | ❌* | If provided, must exist in users table | "Invalid user selected" |
| `due_date` | Date | ❌ | If provided, must be today or future | "Due date must be today or in the future" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| CAR must exist and not deleted | "CAR not found" |
| CAR status must be DRAFT or REWORK_REQUESTED (for vessel) | "Actions can only be added to draft or rework CARs" |

### 5.2 Complete Corrective Action

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `completion_remarks` | String | ❌ | Max 4000 chars | "Remarks must be less than 4000 characters" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Action must not already be completed | "Action is already completed" |
| User must be owner or VESSEL_MASTER or OFFICE | "Only the action owner can mark as complete" |

---

## 6. Evidence Validation

### 6.1 Upload Evidence

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `file` | Binary | ✅ | Max 3MB (3,145,728 bytes) | "File size must not exceed 3MB" |
| `file` | Binary | ✅ | Mime type: application/pdf, image/jpeg, image/jpg | "Only PDF and JPG files are allowed" |
| `evidence_type` | String | ✅ | Must be: BEFORE, AFTER, EVIDENCE, OTHER | "Invalid evidence type" |
| `description` | String | ✅ | Min 5 chars, max 500 chars | "Description is required (5-500 characters)" |

**File Validation (Backend):**
```python
ALLOWED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg']
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB

def validate_evidence_file(file):
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("File size must not exceed 3MB")
    
    # Check mime type (don't trust Content-Type header)
    import magic
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    
    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError("Only PDF and JPG files are allowed")
```

**File Validation (Frontend):**
```typescript
const ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg'];
const MAX_SIZE = 3 * 1024 * 1024; // 3MB

function validateFile(file: File): string | null {
  if (file.size > MAX_SIZE) {
    return "File size must not exceed 3MB";
  }
  if (!ALLOWED_TYPES.includes(file.type)) {
    return "Only PDF and JPG files are allowed";
  }
  return null;
}
```

---

## 7. Physical Verification Validation

### 7.1 Create Physical Verification

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `scheduled_date` | Date | ❌ | If provided, must be today or future | "Scheduled date must be today or in the future" |
| `visit_port` | String | ❌ | Max 200 chars | "Port must be less than 200 characters" |
| `verifier_user_id` | String | ❌ | If provided, must exist in users table | "Invalid verifier selected" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| CAR status must be DPA_CLOSED | "Physical verification can only be created for DPA-closed CARs" |
| CAR must not already have an open physical verification | "CAR already has an open physical verification" |

### 7.2 Close Physical Verification

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `visit_date` | Date | ✅ | Cannot be in future | "Visit date cannot be in the future" |
| `comments` | String | ✅ | Min 10 chars | "Comments are required (minimum 10 characters)" |

**Preconditions:**

| Rule | Error Message |
|------|---------------|
| Status must be OPEN | "Physical verification is already closed" |
| User must be assigned verifier or DPA | "Only the assigned verifier or DPA can close" |

---

## 8. Inspection Report Validation

### 8.1 Upload Inspection Report

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `file` | Binary | ✅ | Max 3MB | "File size must not exceed 3MB" |
| `file` | Binary | ✅ | Mime type: application/pdf, image/jpeg, image/jpg | "Only PDF and JPG files are allowed" |
| `description` | String | ✅ | Max 500 chars | "Description is required and must be less than 500 characters" |

---

## 9. Sync Validation

### 9.1 Push Sync

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `sync_id` | UUID | ✅ | Must be unique (idempotency key) | "Duplicate sync request" |
| `vessel_id` | UUID | ✅ | Must match authenticated user's vessel | "Vessel mismatch" |
| `checksum` | String | ✅ | SHA-256 hash, must match calculated hash | "Payload integrity check failed" |
| `events` | Array | ✅ | Max 100 events per request | "Maximum 100 events per sync" |

**Event Validation:**

| Field | Rules | Error Message |
|-------|-------|---------------|
| `event_id` | Must be unique within sync | "Duplicate event ID" |
| `entity_type` | Must be valid type | "Invalid entity type" |
| `operation` | Must be: CREATE, UPDATE, DELETE | "Invalid operation" |
| `client_version` | Must be >= 1 | "Invalid client version" |
| `timestamp` | Cannot be in future | "Invalid timestamp" |

### 9.2 Conflict Resolution

| Field | Type | Required | Rules | Error Message |
|-------|------|----------|-------|---------------|
| `conflict_id` | UUID | ✅ | Must exist and be PENDING | "Conflict not found or already resolved" |
| `resolution` | String | ✅ | Must be: KEEP_SERVER, KEEP_VESSEL, REOPEN_FOR_MERGE | "Invalid resolution option" |
| `notes` | String | ❌ | Max 1000 chars | "Notes must be less than 1000 characters" |

---

## 10. State Machine Validation

### 10.1 Inspection Status Transitions

```
DRAFT → SUBMITTED (submit)
SUBMITTED → PIC_REVIEWED (pic-review)
PIC_REVIEWED → DPA_CLOSED (dpa-close)
```

**Invalid Transitions (reject with error):**
- DRAFT → PIC_REVIEWED: "Inspection must be submitted first"
- DRAFT → DPA_CLOSED: "Inspection must be submitted and reviewed first"
- SUBMITTED → DPA_CLOSED: "Inspection must be PIC reviewed first"
- DPA_CLOSED → any: "Closed inspections cannot be modified"

### 10.2 CAR Status Transitions

```
DRAFT → SUBMITTED (submit)
SUBMITTED → PIC_ACCEPTED (pic-accept)
SUBMITTED → REWORK_REQUESTED (rework)
PIC_ACCEPTED → DPA_CLOSED (dpa-close)
PIC_ACCEPTED → REWORK_REQUESTED (rework)
REWORK_REQUESTED → DRAFT (auto-transition)
```

**Invalid Transitions (reject with error):**
- DRAFT → PIC_ACCEPTED: "CAR must be submitted first"
- DRAFT → DPA_CLOSED: "CAR must be submitted and accepted first"
- SUBMITTED → DPA_CLOSED: "CAR must be PIC accepted first"
- DPA_CLOSED → any: "Closed CARs cannot be modified"

---

## 11. Business Rule Validation

### 11.1 DefCode Visibility Rule

**Rule:** DefCode MUST be displayed on every screen showing deficiencies.

**Frontend Enforcement:**
```typescript
// Every deficiency display component MUST show def_code
interface DeficiencyDisplayProps {
  deficiency: {
    def_code: string;  // ALWAYS required in UI
    def_code_description?: string;
    description: string;
    // ...
  };
}

// Component MUST render def_code prominently
const DeficiencyCard = ({ deficiency }: DeficiencyDisplayProps) => (
  <div>
    <span className="font-mono font-bold text-lg">
      {deficiency.def_code}  {/* MANDATORY */}
    </span>
    {/* rest of component */}
  </div>
);
```

### 11.2 1:1 Deficiency-CAR Rule

**Rule:** Every deficiency MUST have exactly one CAR. No manual CAR creation.

**Backend Enforcement:**
- Trigger auto-creates CAR on deficiency INSERT
- No POST endpoint for standalone CAR creation
- Delete deficiency → soft-delete associated CAR

### 11.3 Offline Storage Limits

| Limit | Value | Warning Threshold |
|-------|-------|-------------------|
| Total offline cache | 150MB | <10MB remaining |
| Single file size | 3MB | - |
| Sync batch size | 100 events | - |

### 11.4 Retry Logic

| Retry | Delay | After All Retries |
|-------|-------|-------------------|
| 1 | 1 second | - |
| 2 | 2 seconds | - |
| 3 | 4 seconds | Mark as FAILED, queue for next sync |

---

## 12. Zod Schemas (Frontend)

### 12.1 Inspection Schema

```typescript
import { z } from 'zod';

export const inspectionSchema = z.object({
  vessel_id: z.string().uuid("Invalid vessel"),
  inspection_type: z.enum(['PSC', 'RS', 'AUDIT', 'INTERNAL'], {
    errorMap: () => ({ message: "Invalid inspection type" })
  }),
  psc_subtype: z.enum(['INITIAL', 'EXPANDED', 'CIC', 'FOLLOW_UP']).nullable(),
  inspection_date: z.string().refine(
    (date) => new Date(date) <= new Date(),
    "Inspection date cannot be in the future"
  ),
  port_place: z.string()
    .min(2, "Port/Place is required (minimum 2 characters)")
    .max(200, "Port/Place must be less than 200 characters"),
  country: z.string().max(100).nullable(),
  mou_id: z.string().uuid().nullable(),
  authority: z.string().max(200).nullable(),
  inspector_name: z.string().max(200).nullable(),
  report_reference: z.string().max(100).nullable(),
  is_detention: z.boolean().default(false),
}).refine(
  (data) => data.inspection_type !== 'PSC' || data.psc_subtype !== null,
  { message: "PSC subtype is required for PSC inspections", path: ['psc_subtype'] }
).refine(
  (data) => data.inspection_type !== 'PSC' || data.mou_id !== null,
  { message: "MOU is required for PSC inspections", path: ['mou_id'] }
);
```

### 12.2 CAR Schema

```typescript
export const carUpdateSchema = z.object({
  root_cause_summary: z.string()
    .min(50, "Root cause summary must be at least 50 characters")
    .max(4000)
    .nullable(),
  target_date: z.string().nullable(),
  clc_item_ids: z.array(z.string().uuid()).default([]),
  custom_cause_text: z.string().max(500).nullable(),
});

export const carSubmissionSchema = carUpdateSchema.extend({
  root_cause_summary: z.string()
    .min(50, "Root cause summary must be at least 50 characters"),
});
```

### 12.3 Evidence Schema

```typescript
export const evidenceSchema = z.object({
  evidence_type: z.enum(['BEFORE', 'AFTER', 'EVIDENCE', 'OTHER'], {
    errorMap: () => ({ message: "Invalid evidence type" })
  }),
  description: z.string()
    .min(5, "Description is required (minimum 5 characters)")
    .max(500, "Description must be less than 500 characters"),
});

// File validation (separate, for upload)
export const MAX_FILE_SIZE = 3 * 1024 * 1024;
export const ALLOWED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg'];
```

---

## 13. Error Response Format

### 13.1 Standard Error Response

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Validation failed",
  "details": {
    "root_cause_summary": "Root cause summary must be at least 50 characters",
    "corrective_actions": "At least one immediate corrective action is required"
  }
}
```

### 13.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Field validation failed |
| INVALID_STATE | 400 | Invalid state transition |
| PRECONDITION_FAILED | 400 | Business rule precondition not met |
| UNAUTHORIZED | 401 | Not authenticated |
| FORBIDDEN | 403 | Not authorized for this action |
| NOT_FOUND | 404 | Entity not found |
| CONFLICT | 409 | Sync conflict detected |
| FILE_TOO_LARGE | 413 | File exceeds size limit |
| UNSUPPORTED_MEDIA | 415 | Invalid file type |
| SYNC_ERROR | 422 | Sync processing failed |
| INTEGRITY_ERROR | 422 | Checksum validation failed |

---

## Document References

| Document | Reference |
|----------|-----------|
| PRD.md | Feature acceptance criteria |
| BACKEND_STRUCTURE.md | Database constraints |
| FRONTEND_GUIDELINES.md | Form validation patterns |
| APP_FLOW.md | Screen validation requirements |

---

**Document Control:**
- Created: 2026-02-04
- Author: System Generated
- Validation Version: 1.0
