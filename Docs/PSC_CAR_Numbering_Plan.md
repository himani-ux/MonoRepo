# PSC-CAR Numbering Plan (vessel-aware series)

**Date:** 2026-08-10  
**Goal:** Change numbering for newly generated PSC-CARs to `VESSEL_CODE-PSC-YEAR-NUMBER` without changing any existing CAR records.

## 1) Target behavior
- New CARs (after rollout) must use:
  - Format: `VESSEL_CODE-PSC-YYYY-XXX`
  - Example: `EAT-PSC-2026-001`
- Existing CARs must remain exactly as-is (legacy format like `PSC-2026-001`).
- No retroactive renumbering.

## 2) Sequence rules
- Sequence scope = **per vessel + per calendar year**.
- On first CAR of a vessel in a year, sequence starts at `001`.
- Number width = 3 digits at minimum, padded: `001`, `002`, ... `999`.
- Sequence should not cross vessels (each vessel has its own sequence counter).
- Sequence should reset by year.

## 3) Data model strategy
- Add a dedicated sequence state table (or equivalent transactional counter store):
  - `vessel_code` (or `vessel_id` if more reliable)
  - `year`
  - `last_sequence`
  - Unique constraint on `(vessel_code, year)`
- Use row-level locking inside a DB transaction when allocating next sequence.
- Keep existing `car_number` field unchanged.

## 4) Number generation logic (new CAR creation)
1. Resolve `vessel_code` from existing deficiency/inspection ownership path.
2. Get current year from server date.
3. In one transaction:
   - Load/lock sequence row for `(vessel_code, year)`.
   - Increment `last_sequence`.
   - Persist increment.
4. Construct:
   - `car_number = f"{vessel_code}-PSC-{year}-{seq:03d}"`.

## 5) Failure and fallback handling
- If `vessel_code` is unavailable:
  - Prefer to block creation with a clear user-facing error and fix the source record.
  - (Fallback mode such as `UNKNOWN-PSC-YYYY-XXX` should only be used if strict continuity is required.)
- Log fallback/blocked events for operations follow-up.

## 6) Backward compatibility requirements
- Do not update historical CAR rows.
- Keep any display, sort, filter, and export behavior that reads existing CAR numbers compatible with both formats.
- Avoid breaking API contracts where clients expect a string `car_number`.

## 7) Migration sequence
1. Add sequence state model/migration.
2. Initialize counters:
   - If legacy/new mixed records exist for a vessel-year, seed from highest existing sequence for that vessel-year.
   - Otherwise initialize to `0`.
3. Keep legacy records unchanged.

## 8) Test plan
- Unit tests:
  - Old CAR format remains unchanged.
  - New format generation is correct.
  - Vessel-wise sequences are independent.
  - Year boundary resets numbering.
  - Concurrent creation under same vessel/year does not duplicate sequence.
- API regression tests:
  - Legacy and new CAR numbers are returned in list/detail responses.
  - Filters/search by car number still work.
- Optional end-to-end staging verification:
  - Create CARs across ≥2 vessels in same year and validate numbering continuity per vessel.

## 9) Deployment and rollback
- Deploy to staging first, verify with 1–2 days of test creation traffic.
- Move to production after duplicate/empty-vessel alerts are clean.
- Rollback plan: switch generator back to legacy `PSC-YYYY-XXX` path while preserving all stored CAR records.
