# DefIntel / OpenSource + Checklist + Prediction — Phase-wise Build Prompt (Codex CLI)

> **Use this file as the single source of truth.**  
> Codex must follow it **phase-wise** and must not assume anything not proven from the repo.

## References (repo-relative, exact and stable)
- `docs/Wireframe_Pack_v4_Page9.jpg` (Page 9 = DefIntel/OpenSource step)
- `docs/DeficiencyData_9.xlsx` (Monthly OpenSource file format will NOT change)

---

### Path lock
- These paths are authoritative and must exist in the repo exactly as written:
  - `docs/Wireframe_Pack_v4_Page9.jpg`
  - `docs/DeficiencyData_9.xlsx`
  - `docs/templates/Preparation Checklist.xlsx`

## Global rules (apply to all phases)

### Role
You are **Codex CLI**. You will (1) audit the repo to remove unknowns, then (2) implement the DefIntel/OpenSource + Checklist + Prediction feature **exactly** as specified.

### No guesswork
- No assumptions. No invented fields. No invented relationships.
- If something is unclear, you must **locate the authoritative source in the repo** and cite the exact file path(s).
- If still impossible, stop and list a minimal set of blocking questions.

### Online/Offline
- **DefIntel is ONLINE-ONLY** but must be accessible to **both Vessel and Office users when online**.
- When offline or API unreachable: show a clear **“Online required”** UI state (no crashes).
- Offline requirements remain ONLY for vessel registering inspection + creating CAR (out of scope here).

### Two data domains

### Data separation (mandatory)
- **OpenSource data must NEVER be inserted into internal inspection/deficiency/CAR tables.**
- OpenSource persists **only** in DefIntel tables (`OpenSourceImportRun`, `OpenSourceDeficiencyRecord`).
- “Merge” is allowed **only** for checklist output aggregation (read-only queries).
- Checklist output must show split counts by source (internal vs opensource) so users can distinguish them.


- **INTERNAL:** our DB inspection deficiencies
- **OPENSOURCE:** monthly uploaded Excel persisted in DB

### Checklist scope modes (strict)
- **VESSEL** -> INTERNAL ONLY (ignore OpenSource)
- **FLEET** -> INTERNAL ONLY (ignore OpenSource)
- **INSPECTOR** -> INTERNAL ONLY (ignore OpenSource)
- **FILTER_COMBINED** (Port/DefCode/ActionCode/MOU/Country filters) -> INTERNAL + OPENSOURCE combined  
  - **Requires** OpenSource imported at least once. If not imported: return a clear error and UI must guide to import.

### Monthly OpenSource dedup definition (strict)
A row is a **DUPLICATE** if ALL match an existing stored OpenSource row (**after normalization**):
- `year`
- `def_code`
- `action_code`
- `port`
- `mou`

> **Country/Description/Date are NOT part of OpenSource duplicate identity** for storage.

### Fleet scope definition (strict)
- **FLEET = all vessels under `company_id` from current user session**  
  Use existing auth/tenant implementation, do not invent.

### Inspector linkage (must be discovered)
- The user is not sure where `inspector_id` is stored.  
  You MUST locate authoritative fields and the correct query path in models/serializers.

### Prediction windows (must support both)
- **ALL_TIME**
- **LAST_24_MONTHS** (default)
- If some rows lack dates, document fallback behavior explicitly.

### Normalization (must match current system)
- You MUST find and reuse existing normalization conventions/utilities in the repo.
- `def_code` normalization is mandatory: 5 chars left pad zeros consistent with master data rules.
- `action_code` normalization: cast to integer consistent with current action code handling.

### Excel format (no change)
- Monthly file format is exactly `docs/DeficiencyData_9.xlsx`.
- Parse using the exact headers in that file (case-insensitive match).
- If required headers are missing: reject import and list missing headers.
- You must discover headers by reading the file and coding against them.

---

# Phase 1 — Repo Audit (eliminate unknowns)

## Objectives
1. Confirm existing `/reports` placeholder route(s) and where to implement the real Page 9 screen.
2. Locate existing deficiency code/action code masters and any normalization/matching utilities.
3. Determine where `inspector_id` lives and how to query inspector-based deficiencies correctly.
4. Determine which date field(s) exist for internal deficiencies and how LAST_24_MONTHS will be computed.

## Output (MANDATORY)
Return a **DECISION LOCK** section (max 30 lines) containing:
- Exact normalization functions/logic to use (with file paths)
- Exact model field paths for vessel, inspector, and `company_id` scope
- Exact date field used for 24 months filtering and fallback behavior

---

# Phase 2 — Backend: OpenSource persistence + monthly import

## DB changes (minimal, mandatory)
Create minimal new tables only for OpenSource:
- `OpenSourceImportRun`
  - `uploaded_by`, `uploaded_at`, `filename`, `file_hash`
  - `total_rows`, `valid_rows`, `inserted_rows`, `duplicate_rows`, `invalid_rows`
- `OpenSourceDeficiencyRecord`
  - `year`
  - `def_code_norm`
  - `action_code_norm`
  - `port_norm`
  - `mou_norm`
  - optional: `country_norm`, `description_raw` (only if needed later for checklist display)
  - `dedup_key_hash` (UNIQUE)
  - FK to `import_run`

## Identity rules (mandatory)
- Import run identity: `file_hash = SHA-256(file bytes)` (for traceability)
- Row identity for dedup: `dedup_key_hash = SHA-256(normalized(year, def_code, action_code, port, mou))`
- Enforce uniqueness on `dedup_key_hash` at DB level; duplicates skipped and counted

## API (mandatory)
Add endpoint:
- `POST /api/psc/reports/opensource/import/`
  - multipart: `file=.xlsx`
  - returns: `import_run_id` + counts
  - include first N invalid rows + first N duplicates (for troubleshooting)

## Must not change
- Do NOT modify existing inspection upload validators/endpoints.

---

# Phase 3 — Backend: Checklist Builder

## Endpoints (new, mandatory)
Do NOT reuse `/inspections/export-excel/`.
Add:
- `POST /api/psc/reports/vessel-prep/preview/`
- `POST /api/psc/reports/vessel-prep/export/`

## Request shape
- `scope_mode`: `VESSEL | FLEET | INSPECTOR | FILTER_COMBINED`
- `vessel_id` (VESSEL)
- `inspector_id` (INSPECTOR)
- `filters` (FILTER_COMBINED): `def_code[]`, `action_code[]`, `mou[]`, `port[]`, `country[]`
- optional: `date_from`, `date_to`
- `dedup=true|false` (default true; dedup applies AFTER merge)

## Data logic (strict)
- INTERNAL ONLY modes: query internal deficiencies and aggregate.
- FILTER_COMBINED:
  - require OpenSource imported at least once
  - query internal deficiencies using filters
  - query `OpenSourceDeficiencyRecord` using filters
  - normalize, merge, dedup AFTER merge
  - aggregate to checklist rows

## Checklist row fields (mandatory)
- `def_code` (5-char)
- `action_code`
- `mou`
- `port`
- `country` (from internal if available; from OpenSource if stored; else blank)
- `occurrence_count_total`
- `occurrence_count_internal`
- `occurrence_count_opensource`
- `last_seen_date` (max; if OpenSource lacks date and internal has date, use internal; document rule)
- `example_description` (prefer internal; else OpenSource description_raw if stored)

## Export workbook (mandatory)
- Sheet 1: `Vessel Preparation Checklist`
- Sheet 2: `Input Summary` (scope mode, filters, counts, invalid counts, dedup stats)

---

# Phase 4 — Backend: Prediction API (probability, not heavy ML)

## Goal
Predict top DefCodes per **Port** or **MOU** using historic frequency with Bayesian smoothing.

## Endpoint (mandatory)
- `GET /api/psc/reports/defintel/predict-defcodes/`
  - query:
    - `context=PORT|MOU`
    - `port=...` (if PORT)
    - `mou=...` (if MOU)
    - `window=ALL_TIME|LAST_24_MONTHS` (default LAST_24_MONTHS)
    - `top_n=20`

## Data sources
- Use INTERNAL + OPENSOURCE stored data for predictions.

## Return fields (mandatory)
- `def_code`
- `probability` (smoothed)
- `count_context`
- `count_global`
- `last_seen_date` (if available)

## Smoothing (mandatory)
- `alpha = 100` (configurable constant)
- `P = (count_context + alpha * P_global) / (total_context + alpha)`

---

# Phase 5 — Frontend: Real `/reports` Page (Page 9 parity)

Replace placeholder `/reports` with a real **DefIntel** screen aligned to wireframe intent.

## Sections (mandatory)
### A) Import OpenSource Excel (monthly)
- Upload -> call import endpoint -> show summary counts

### B) Checklist Builder
- Scope selector (VESSEL/FLEET/INSPECTOR/FILTER_COMBINED)
- FILTER_COMBINED requires OpenSource imported; otherwise show **“Import required”** callout
- Preview table + Export button

### C) Prediction
- Context selector PORT/MOU
- Window selector LAST_24_MONTHS/ALL_TIME
- Top N results table with probability and evidence counts

## Offline guard (mandatory)
- If offline or API unreachable: show “Online required”, no crashes.

## UI hygiene (mandatory)
- Do NOT display internal IDs in UI tables or exported Excel.

---

# Phase 6 — Tests (mandatory)

## Backend tests
- Import same file twice -> second import `inserted_rows=0`, `duplicate_rows>0`
- Import partially overlapping file -> inserts only new uniques
- Dedup uses ONLY (year, def_code, action_code, port, mou) after normalization
- FILTER_COMBINED rejects if no OpenSource imported
- Scope rules: VESSEL/FLEET/INSPECTOR omit OpenSource even if OpenSource exists
- Existing `/inspections/export-excel/` unchanged
- Prediction endpoint supports both windows and returns sorted stable probabilities

## Frontend tests
- `/reports` is not placeholder
- Offline guard shows “Online required”
- Import flow works and displays counts
- Checklist preview/export works
- FILTER_COMBINED shows “Import required” when needed
- Prediction renders

---

# Required final delivery format (for each phase)
For each phase completion, output exactly:
1. **FILES CHANGED/CREATED** (paths)
2. **DB MIGRATIONS** (what, why) (if any)
3. **API CONTRACTS** (example requests/responses) (if any)
4. **MANUAL VERIFICATION CHECKLIST**
5. **PERFORMANCE NOTES** (how it stays fast)
