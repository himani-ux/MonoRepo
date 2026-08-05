# VIMS Safety Module - Lessons Learned

> Corrections-driven learning file. Reviewed at every session start, updated after every user correction or confirmed non-obvious win.
>
> **Numbering:** `L-###` (zero-padded, append-only - never renumber).
> **Format per entry:** What happened | Why | Rule that prevents recurrence.
> **Trigger for new entry:** (a) any user correction, (b) any confirmed non-obvious win worth preserving, (c) any cross-module contract drift caught in review.
>
> Seed entries L-001 / L-002 / L-003 capture the most load-bearing lessons from Sessions 1-5 interrogation; preserve them verbatim.

---

## L-001 - External reference packs can reshape locked specs
**What happened:** Round 21 reference pack (TapRoot, ABS RCA, IMO RCA guidance) surfaced 23 enhancements after Session 4 had already "closed" the V1 spec. Causal layering (Immediate/Intermediate/Root) was added on top of M-SCAT as a result.
**Why:** "Interrogation complete" is a state-in-time, not permanence. External references introduce patterns the original interrogation didn't probe.
**Rule:** Before docsuite generation, always run a final gap-analysis pass against any new reference material the user contributes. Do not treat spec close as immutable.

## L-002 - Paper-first means no scan upload
**What happened:** Initial SOI design assumed scanned-PDF upload after paper fieldwork.
**Why:** User clarified (D-GAP-E4) that paper is filed in ship SMS filing system - scan upload is duplicative and creates a second source of truth.
**Rule:** When a workflow is "paper-first," the system generates -> user downloads -> paper becomes authoritative -> findings registered digitally via unique ID only. No upload column, no scan endpoint.

## L-003 - Role persists, person may change
**What happened:** Early drafts had "Acting-DPA" and "Acting-CO" concepts.
**Why:** D-GAP-A3/A4 locked that ranks are always staffed; the person in the role changes via normal crew rotation but the role itself is continuous.
**Rule:** No "Acting-*" concepts anywhere. No deputy chains. No MD-escalation logic. Use the timeline-extension procedure (D-GAP-B2) as the universal escape valve.

---

<!-- Append new L-### entries below as corrections occur. Never edit entries above; never renumber. -->

## L-004 - Do not edit the live monorepo when the handover workspace is the requested build target
**What happened:** Initial execution started by inspecting and preparing to patch `C:\Users\himan\Desktop\Complete_VIMS` because the user called it the monorepo folder, then the user corrected the target and required all development to stay inside the handover package.
**Why:** The session mixed "actual monorepo" discovery with "handover workspace" execution and did not lock the write target early enough.
**Rule:** Before any file edit, confirm the write target root from the user's latest instruction. If the user directs work to the handover package, do all implementation and verification there and keep the live monorepo read-only unless the user explicitly re-authorizes direct changes.

## L-005 - Treat DB-name drift against the locked docs as a contract issue, not a harmless default
**What happened:** Step `0.1` artifacts still referenced `ksm_marine_live`, while `AGENTS.md`, `CLAUDE.md`, `TECH_STACK.md`, and `BACKEND_STRUCTURE.md` all lock the shared Safety database to `ksm_marine_live`.
**Why:** Scaffold tests and progress notes can inherit stale environment assumptions from earlier workspace setup, and that drift silently contaminates later auth, migration, and repository work.
**Rule:** When a DB name, alias, or host in code/tests disagrees with the locked docs, correct the artifact immediately and carry the docs value forward. Do not preserve the stale default just because it currently exists in the workspace.

## L-006 - Use `progress.txt` as the execution handoff when `AGENTS.md` startup notes lag behind
**What happened:** `AGENTS.md` still said to begin at Step `0.1`, but `docsuite/progress.txt` showed that Steps `0.1` and `0.2` were already complete and that the correct carry-forward target was Step `0.3`.
**Why:** `AGENTS.md` is a stable entry-point document, while `progress.txt` is the cross-session state file and will change as implementation moves forward.
**Rule:** At session start, treat `AGENTS.md` as orientation and `progress.txt` as the live handoff. If they differ on current step, continue from `progress.txt` and record the newer state there again at session close.

## L-007 - When Step file paths and frontend naming guidance drift, preserve the step path but keep exported symbols aligned with the frontend rules
**What happened:** `docsuite/IMPLEMENTATION_PLAN.md` Step `0.4` named files like `src/hooks/safety/use-auth.ts` and `src/stores/safety/incident-draft-store.ts`, while `docsuite/FRONTEND_GUIDELINES.md` preferred `use-safety-auth.ts` and `safety-incident-draft-store.ts`.
**Why:** The implementation plan is the execution blueprint for which files to create in a phase, but the frontend guidelines carry the stronger naming convention for exported `Safety*` components and `useSafety*` hooks.
**Rule:** If a phase step's required file paths differ from the frontend-guideline naming examples, create the step-mandated paths for execution continuity, keep the exported component and hook names aligned with `FRONTEND_GUIDELINES.md`, and record the discrepancy in `tasks/todo.md` and `progress.txt`.

## L-008 - Seed artifacts outrank summary assumptions about natural keys and scalar types
**What happened:** Step `0.5` uncovered that `seed-data/soi_checklist_v1.csv` uses decimal Section 12 item numbers like `12.1` and contains a duplicated `(area_id, subsection_id, item_number)` pair with different descriptions.
**Why:** The docsuite summary for `master_soi_area_item` implied an integer `item_number` and uniqueness on `(area_id, subsection_id, item_number)`, but the real seed artifact is the load-bearing input and exposes the stronger truth the DDL must accommodate.
**Rule:** Before locking DDL or upsert keys for a seeded master table, validate the actual seed artifacts first. If the artifact and the summary disagree, preserve the artifact, record the drift, and carry the reconciliation into the next schema step instead of coercing the data to fit the summary.

## L-009 - Mid-phase migration stubs must not break the app migration graph or unrelated tests
**What happened:** Adding `0002_seed_master_tables.py` before Step `0.6` initially broke Django migration loading because there was no `0001_initial.py`, and then the data migration tried to seed tables that did not yet exist in SQLite test runs.
**Why:** Even placeholder migrations participate in the global migration graph, so a stub written for sequencing can still break unrelated tests if it assumes later schema work already exists.
**Rule:** When a phase requires introducing a migration stub ahead of the real DDL, add the minimum valid parent migration and guard the data migration so it no-ops cleanly until the required tables exist.

## L-010 - Raw SQL seeders need database defaults, not just Django field defaults
**What happened:** Step `0.6` initially created the real `0001_initial.py` table shells with Django-side `default=` values only, and the Step `0.5` raw SQL seed migration then failed because omitted `master_*` columns such as `active` and `created_date` had no database-level defaults.
**Why:** `default=` populates values through the ORM, but `seed_master_safety.py` inserts rows with explicit SQL and depends on the database schema itself to fill omitted columns.
**Rule:** If a migration-created table will be seeded by raw SQL or a management command that omits some non-null columns, either give those columns a `db_default` in the migration or have the seeder write them explicitly. Do not assume ORM defaults will protect raw inserts.

## L-011 - During development, do not change existing tables unless the task explicitly requires it
**What happened:** Ongoing Safety implementation work is being built around an existing shared schema surface, and unnecessary edits to already-existing tables create avoidable cross-module risk and migration drift.
**Why:** Existing tables may be consumed by other modules, seeded data, or live integrations, so changing them during routine feature development can break contracts outside the current task.
**Rule:** While doing development, do not make changes to existing tables unless the current task explicitly requires that table change and the impacted contract has been reviewed first.

## L-012 - Keep package `__init__` files import-light when tests bootstrap Django manually
**What happened:** Full `tests.safety` discovery initially failed because `apps.safety.authentication.__init__` imported DRF/SimpleJWT-backed modules before Django settings were configured, and one auth test imported DRF test helpers before calling its local bootstrap.
**Why:** In this handover workspace, many tests intentionally configure Django inside the test module. Heavy package-level imports can force Django/DRF settings access too early and turn harmless import order into false-red suite failures.
**Rule:** Keep package `__init__` modules lightweight in the handover workspace, especially around auth and DRF integrations. When a test uses manual bootstrap, call it before importing DRF, SimpleJWT, or project modules that transitively depend on configured Django settings.

## L-013 - When phase-gate rules conflict across docs, follow the arbitration order and record the chosen source
**What happened:** Step `1.3` exposed a direct conflict: `VALIDATION_RULES.md` still put `imo_classifier`, `risk_band`, and `investigation_depth` in the Phase `1 -> 2` gate, while `IMPLEMENTATION_PLAN.md` Step `1.4` and `APP_FLOW.md` clearly place those fields in Phase `2`.
**Why:** The docsuite contains phase-by-phase detail written from different angles, so gate rules can drift even when the underlying intent is stable.
**Rule:** When a validation rule conflicts with the phase breakdown or route contract, resolve it using the published arbitration order, implement against the higher-priority phase source, and record the decision in `tasks/todo.md` and `progress.txt` so the next session does not reintroduce the drift.

## L-014 - Treat the user's actual environment identifiers as higher-priority runtime truth than inherited handover defaults
**What happened:** The handover docsuite had been normalized around `ksm_cms_live`, but the user later clarified that the actual target database in this environment is `ksm_marine_live`, and the document set had to be corrected after Step `1.4` work was already complete.
**Why:** Handover packages can carry forward historical environment assumptions that are internally consistent but still wrong for the user's live setup.
**Rule:** When the user provides a concrete runtime identifier such as the real database name, treat it as authoritative for environment-specific docs and carry it through the handoff files immediately. Do not keep the inherited default just because multiple documents already agree with each other.

## L-015 - When the user gives exact environment config, mirror it verbatim in workspace settings before arguing for normalization
**What happened:** The workspace still had a stale DB smoke test and SQLite placeholder settings while the user supplied an explicit `DATABASES['default']` snippet for `ksm_marine_live` using `HOST='localhost'`, `PORT='1433'`, blank `DB_USER` / `DB_PASSWORD`, ODBC Driver 18, and `Trusted_Connection=yes`.
**Why:** It is easy to optimize for what looks more conventional (`HOST` / `PORT` fields, no `USER` on trusted auth) and postpone the literal user-provided config, but that leaves the checked-in workspace out of sync with the user's declared runtime truth.
**Rule:** If the user provides an exact environment configuration snippet, update the workspace to match that snippet first, then document any remaining runtime handshake issue separately. Do not silently normalize the shape before mirroring the user's stated config.

## L-016 - When a step description conflicts with higher-priority docs, preserve the higher-priority contract and record the drift
**What happened:** Step `1.6` in `IMPLEMENTATION_PLAN.md` described multi-vessel linking via a `related_incident_ids` array, but the higher-priority SSOT / PRD / APP_FLOW / BACKEND docs all locked the handover workspace to the existing self-link fields `linked_incident_id` and `superseded_by_id`.
**Why:** Step-level execution notes can carry shorthand or stale shape details that no longer match the canonical contract stack.
**Rule:** If a step file names a data shape that conflicts with higher-priority docs, implement the higher-priority contract, note the drift explicitly in `tasks/todo.md` and `progress.txt`, and do not add a second parallel shape just to satisfy the lower-priority wording.

## L-017 - A phase step is not complete until its transition gate matches the newly implemented contract
**What happened:** Step `1.6` initially added the Phase 4 fact-base tables and APIs, but the `PhaseStateMachine` still had an older placeholder Phase `4 -> 5` gate that did not enforce the locked recency-bias evidence-tab rule.
**Why:** It is easy to finish the visible CRUD surface and miss the phase-transition logic that actually determines whether the feature behaves according to the docsuite.
**Rule:** When implementing any phase-scoped feature, inspect and update the corresponding phase gate in `PhaseStateMachine` during the same step, then add a focused transition test so the step closes with both the data surface and the gate behavior aligned.

## L-018 - Seed-reference reality outranks implied typed subsets in the docs
**What happened:** Step `1.7` surfaced that the handover `seed-data/mscat_taxonomy.csv` currently loads only `cause_type='BASIC_CAUSE'` rows, even though the docsuite wording around blame-fixation and Lack-of-Control implies a richer typed subset that the workspace data cannot actually prove yet.
**Why:** Some docs summarize downstream semantic groupings as if they were already encoded in the seed data, but the real handover artifact may only provide a flatter source shape.
**Rule:** Before implementing logic that depends on a supposed typed subset inside a seeded master table, inspect the actual seed artifact first. If the artifact does not encode that subset, fall back to the strongest provable heuristic, record the drift in `tasks/todo.md` and `progress.txt`, and do not silently invent reference-data structure that the seed does not contain.

## L-019 - Distinguish sandboxed Windows-auth failures from a real SQL outage
**What happened:** Direct `pyodbc` and `sqlcmd` runs against `ksm_marine_live` failed inside the Codex sandbox with `SSL Provider: No credentials are available in the security package` / `Encryption not supported on the client`, while SQL MCP and an unsandboxed `python -m unittest tests.safety.test_db_connection -v` run both succeeded against the same server, database, and Windows identity.
**Why:** The failing path was the sandbox's integrated-auth token, not the SQL Server instance itself, so treating the symptom as "DB down" would create a false blocker and keep the workspace test surface red for the wrong reason.
**Rule:** When a live SQL smoke test fails under `Trusted_Connection=yes`, verify the same target through SQL MCP or an unsandboxed run before reporting the database as unreachable. If the failure is the known sandbox-only SSPI handshake issue, make the test skip explicitly or use SQL-auth overrides rather than leaving a false-red DB failure in the handoff.

## L-020 - Do not describe the SQLite unit harness as the user's actual database
**What happened:** Phase `1.9` verification used the existing `tests/safety/support.py` in-memory SQLite bootstrap for fast unit coverage, and that could be misread as the runtime environment even though the user's real target is SQL Server `ksm_marine_live`.
**Why:** The handover workspace mixes lightweight logic tests with SQL Server-specific integration checks, so it is easy to blur "test harness backend" with "deployment database".
**Rule:** When reporting test results in this workspace, explicitly separate the unit-test harness database from the real runtime database. Always state that the production target is SQL Server `ksm_marine_live`, and never imply that SQLite is the user's actual environment.

## L-021 - Treat sandboxed Vite or Vitest `spawn EPERM` as an execution-mode issue before treating it as a frontend misconfiguration
**What happened:** After the missing root frontend toolchain was added, `npm test` and Vite-backed config loading still failed inside the sandbox with `spawn EPERM`, while the same commands passed immediately when rerun outside the sandbox.
**Why:** Vite, Vitest, and esbuild spawn worker processes, and that can be blocked by the sandbox even when the project configuration is otherwise correct.
**Rule:** If Vite or Vitest fails in this workspace with `spawn EPERM`, verify the TypeScript surface locally, then rerun the command outside the sandbox before declaring the frontend toolchain broken. Distinguish environment execution limits from real config or code errors.

## L-022 - When a handover step depends on a missing sibling-module live join, ship a workspace-safe seam and record the exact production gap
**What happened:** Step `1.10` required the Inspection-module `psc_physical_verification` pattern plus HR/CMS-driven leave-transfer behavior, but those real cross-module surfaces were not present in the handover workspace.
**Why:** The handover package is intentionally narrower than the real monorepo, so some documented live joins cannot be proven end-to-end locally even when the step itself still needs a runnable implementation and test surface.
**Rule:** If a phase step depends on a sibling-module live join that the handover workspace does not contain, implement a workspace-safe seam that preserves the local contract shape, then record the missing production integration explicitly in `progress.txt` and `tasks/todo.md` instead of pretending the live join is complete.

## L-023 - When step prose and file inventory drift from the stronger schema contract, harden the existing surface instead of duplicating it
**What happened:** Step `1.11` prose asked for a new `apps/safety/models/corrective_action.py` file and a shorter `OPEN -> IN_PROGRESS -> VERIFIED -> CLOSED` CA lifecycle, but the higher-priority `BACKEND_STRUCTURE.md` already locked the workspace CA contract to the existing `CorrectiveAction` model under `apps/safety/models/recommendation.py` with `PENDING_VERIFY` and `REOPENED` states.
**Why:** Step-level execution notes can lag behind the canonical schema/API contract, and blindly following the file list would have created a second parallel CA implementation with the wrong lifecycle.
**Rule:** If a step's file inventory or state-machine summary conflicts with the stronger backend contract already present in the workspace, extend the existing implementation surface and record the drift. Do not create duplicate model paths or downgrade the canonical lifecycle just to match lower-priority shorthand.

## L-024 - If the user authorizes the real Safety target DB, prefer live SQL Server validation over the SQLite harness for schema/integration confidence
**What happened:** The workspace kept using the in-memory SQLite harness for focused Step `1.x` verification even after the user clarified that `ksm_marine_live` may be used, provided existing shared tables are not modified.
**Why:** The handover package already had fast SQLite bootstrap tests, and earlier sessions were conservative about live-schema churn, so the default testing path stayed local longer than the user's actual preference.
**Rule:** When the user explicitly authorizes use of `ksm_marine_live`, use the real SQL Server for live validation and Safety-owned table work where feasible, while still avoiding changes to existing shared tables unless the task explicitly requires them. Use the SQLite harness only for isolated unit-style coverage or when live SQL would be unnecessarily destructive/noisy.

## L-025 - Treat same-DB cross-module schema drift as a live-contract check, not a naming cleanup exercise
**What happened:** Step `1.13` docs referenced shorthand Reporting surfaces like `vims_noon_report` / `vims_reporting_daily_report`, but the actual `ksm_marine_live` schema exposed the legacy tables `dbo.NoonReport`, `dbo.DepartureReport`, `dbo.ArrivalReport`, and `dbo.NoonReportPort` with inconsistent coordinate column names such as `Longitud2` / `Longitud3`.
**Why:** Cross-module handover docs can normalize or summarize sibling schemas, while the live database remains the runtime integration contract that the code must actually survive.
**Rule:** Before implementing any same-DB live join, inspect the real target tables and columns in `ksm_marine_live` first. Use the observed schema as integration truth, then record any docs drift explicitly in `tasks/todo.md` and `docsuite/progress.txt` instead of coding against the shorthand alone.

## L-026 - Role-based visibility exceptions belong in the shared scope filter, not in ad hoc view branches
**What happened:** Step `1.14` needed a non-default visibility rule: Masters may read closed incidents fleet-wide, while DPA and FM must be global by role even when `is_global` is not explicitly populated on the request user.
**Why:** If these exceptions are patched separately into individual list or detail views, the workspace drifts quickly and the same RBAC rule gets enforced differently across routes.
**Rule:** When a Safety visibility rule changes by role, implement it once in the shared vessel-scope layer and verify both list and detail behavior with focused tests. Do not scatter role-specific visibility branches across multiple views.

## L-027 - When a dedicated module step starts on a shared table, add dedicated API and route surfaces before expanding schema
**What happened:** Step `2.1` introduced the first dedicated Near Miss module surfaces, but the current handover workspace still models Near Miss on the shared `vims_safety_incident` shell rather than on a richer near-miss-specific schema.
**Why:** The docsuite can describe a fuller eventual module shape than the current workspace schema can safely support, and jumping straight to new columns would create undocumented drift before the next phase steps justify it.
**Rule:** When a new module phase starts on top of an existing shared record, first carve out dedicated serializers, views, routes, and tests around the shared model. Expand schema only when the later step explicitly requires it and the stronger backend contract supports it.

## L-028 - When route-level action gates drift from the frozen step plan, implement the step-plan contract and record the docs drift
**What happened:** Step `2.2` surfaced a direct mismatch: `APP_FLOW.md` still described Near Miss triage and fleet-alert action gates as `SAF_P_008` / `SAF_P_009`, while `IMPLEMENTATION_PLAN.md` explicitly assigned Step `2.2` triage to `SAF_P_002`.
**Why:** Screen-flow docs can lag behind the frozen execution blueprint, especially when later-step action IDs are described before the intermediate workspace slice is built.
**Rule:** If route-level process IDs in `APP_FLOW.md` conflict with the current frozen implementation step, implement the `IMPLEMENTATION_PLAN.md` contract, note the drift in `progress.txt` and `tasks/todo.md`, and avoid inventing a second parallel gate just to satisfy the lower-priority route prose.

## L-029 - When a feature's route surface drifts across docs, follow the frozen implementation step and record the UI-contract mismatch
**What happened:** Step `2.3` surfaced another near-miss docs mismatch: `IMPLEMENTATION_PLAN.md` explicitly required a dedicated `src/routes/safety/near-miss/[id]/analysis.tsx` route, while `APP_FLOW.md` still mapped `FEAT-SAF-NM-004` to the generic near-miss detail surface instead of a separate analysis route.
**Why:** Screen-flow documentation and frozen execution steps can diverge when a feature is described both as a user-facing surface and as a file-by-file implementation slice.
**Rule:** If a feature's route/file surface in `APP_FLOW.md` conflicts with the current frozen implementation step, build the `IMPLEMENTATION_PLAN.md` surface, log the drift in `progress.txt` and `tasks/todo.md`, and do not collapse the feature back into an older generic route just to satisfy lower-priority flow prose.

## L-030 - When a step's anti-spam shorthand conflicts with the validation and screen contract, enforce the higher-priority create-path rules
**What happened:** Step `2.4` in `IMPLEMENTATION_PLAN.md` described near-miss throttling as `5 per vessel per hour` with `>=50` characters, while the broader create-path docs locked the user-facing and validation contract to `>=100` characters and reset guidance at `00:00` vessel local time from `wrh_ship_time_config`.
**Why:** Execution-plan prose can compress a feature so far that it drifts from the actual validation and route behavior defined elsewhere in the docsuite.
**Rule:** If a step summary disagrees with the create-screen and validation contract, resolve it with the published arbitration order and implement the higher-priority input/UI rule on the real endpoint. Record the discarded shorthand in `progress.txt` and `tasks/todo.md` so later sessions do not revert it.

## L-031 - When an action gate in APP_FLOW conflicts with the backend permission registry, use the backend registry and record the stale route prose
**What happened:** Step `2.5` surfaced a near-miss fleet-alert gate mismatch: `APP_FLOW.md` still assigned the route to `SAF_P_009`, while `BACKEND_STRUCTURE.md` owns the `SAF_P_*` registry and locks fleet circular emit authority to `SAF_P_024`.
**Why:** UI-flow prose can preserve older route/action IDs even after the backend permission registry has been refined and frozen more precisely.
**Rule:** If a route-level action gate in `APP_FLOW.md` conflicts with `BACKEND_STRUCTURE.md`'s permission registry, implement the backend registry value, note the drift in `progress.txt` and `tasks/todo.md`, and do not reuse the stale APP_FLOW process ID just to keep the prose unchanged.

## L-032 - Near-miss anonymity is not complete until audit and derived exits are filtered too
**What happened:** Step `2.6` started with serializer-level masking already in place for the main near-miss list/detail responses, but the workspace still lacked a near-miss audit exit and would have leaked reporter-history rows if the incident audit pattern were copied over unchanged.
**Why:** It is easy to treat `AnonymityMixin` as the whole solution because it protects the primary record serializers, while append-only field history, PDF/search payload builders, and other derived exits can bypass that path entirely.
**Rule:** When a feature depends on near-miss anonymity, verify every exit that can expose reporter identity: list, detail, audit/history, and any PDF/search/export payload builders in scope. Do not assume serializer masking alone closes the boundary.

## L-033 - When the handover workspace already ships the schema shell for a step, extend that shell instead of recreating the step from prose
**What happened:** Step `3.1` prose described a fresh SCM model with dedicated ten-section meeting fields, but the workspace already had `vims_safety_scm_meeting` and `vims_safety_scm_agenda` table shells in `0001_initial.py`.
**Why:** Frozen step prose can summarize the desired feature shape at a higher level than the current checked-in workspace, and blindly following it would have created a second parallel storage path or forced an unnecessary migration.
**Rule:** Before implementing a new phase step in the handover workspace, inspect the existing migration and model surface first. If the required table shell already exists, extend that shell and map the feature onto the strongest existing schema path, then record any prose-vs-schema drift in `progress.txt` and `tasks/todo.md`.

## L-034 - When a seeded permission catalog conflicts with the active step contract, follow the higher-priority workflow docs and keep the extra permission as recorded drift
**What happened:** Step `3.2` exposed a new SCM gate mismatch: the workspace permission seed already contains `SAF_P_012 = SAFETY_SCM_AD_HOC_CREATE`, while the higher-priority startup docs and SCM user-flow docs still keep both Regular and Ad-Hoc SCM creation on shared `SAF_P_001` with role differentiation in the view layer.
**Why:** Permission catalogs can be broader or older than the currently active workflow slice, and blindly splitting the gate to match the seed would have diverged from the stronger handover contract already used in `Step 3.1`.
**Rule:** If a seeded `SAF_P_*` code suggests a narrower action gate than the active step contract in the higher-priority docs, keep the implemented workflow aligned with the higher-priority contract, enforce role differentiation in code where required, and record the seed-vs-workflow drift explicitly in `progress.txt` and `tasks/todo.md`.

## L-035 - When a live same-DB module schema has moved to a newer table family, join the real tables instead of preserving older docs shorthand
**What happened:** Step `3.3` SCM attendance initially pointed toward the docsuite shorthand `wrh_attendance` / `wrh_daily_rest_hours`, but the real `ksm_marine_live` WRH contract in this environment had already moved to `wrh_s520_day_entry` + `wrh_s520_month` + `wrh_ship_time_config`.
**Why:** Cross-module docs can preserve an older abstraction even after the sibling module has consolidated its runtime schema onto newer transactional tables.
**Rule:** Before implementing any same-DB live join, inspect the current production table family first. If the real module contract has moved to a newer schema path, join that path directly, record the shorthand drift in `progress.txt` and `tasks/todo.md`, and do not add compatibility code around obsolete intermediate tables unless the current step explicitly requires it.

## L-036 - When a step summary drifts from the FEAT acceptance criteria, implement the higher-priority feature state and record the shorthand drift
**What happened:** Step `3.4` summary prose in `IMPLEMENTATION_PLAN.md` described the Closed-Since-Last block as including "near-miss triaged" rows, while `PRD.md` `FEAT-SAF-SCM-006` and `APP_FLOW.md` both defined the block around records/items closed since the prior SCM sign-off timestamp.
**Why:** Step-level summaries can compress workflow states and accidentally carry an older shorthand even when the feature acceptance criteria and route contract have already narrowed the real state boundary.
**Rule:** If a step summary conflicts with the feature acceptance criteria and route contract, implement the higher-priority FEAT/UI state contract, then record the shorthand drift in `progress.txt` and `tasks/todo.md` so later sessions do not revert to the looser wording.

## L-037 - When later step prose implies a freer agenda model than the locked table shell, keep the authoritative shell and attach lifecycle data through the existing related model
**What happened:** Step `3.5` asked for agenda owner / due-date / status tracking plus an `[+ Add agenda item]` route behavior, but the locked workspace schema still preserves the fixed legacy 10-section `vims_safety_scm_agenda` shell with one row per `agenda_item_number` and no dedicated owner/due/status columns.
**Why:** Execution-step prose and screen-flow text can describe a richer future workflow than the stronger backend contract that is already frozen into the current table shell.
**Rule:** If a later step implies a freer agenda/action model than the authoritative table shell supports, keep the authoritative shell unchanged and attach the extra lifecycle data through the existing related model already named by the backend contract. Do not invent undocumented columns or a second parallel agenda store just to satisfy lower-priority prose.

## L-038 - When the sign-off preflight contract is stronger than the current schema, enforce the real block at the active seam and derive the rest
**What happened:** Step `3.6` surfaced two SCM sign-off drifts at once: higher-priority Step/PRD/validation docs kept the overdue SOI rule as a sign-off-only hard block, while `BACKEND_STRUCTURE.md` still carried stale submit wording and a different process-ID registry; the same preflight contract also asked for `attendance_acknowledged` even though the current workspace schema has no dedicated acknowledgement field.
**Why:** Endpoint summaries and route prose can drift from the active workflow slice, and preflight UX can name a control state that the current table shell does not actually persist yet.
**Rule:** If the sign-off preflight contract is ahead of the current schema, enforce the documented hard block at the active sign-off seam, record any stale submit/process-ID prose as drift, and derive unsupported preflight booleans from the strongest existing persisted signal instead of adding undocumented columns or moving the block earlier.

## L-039 - When signature capture is required before the final document pipeline exists, store the hybrid payload in audit history and expose the downstream export as an explicit seam
**What happened:** Step `3.7` required SCM Master signature capture plus a PDF-generation trigger, but the workspace schema still only had `master_signed_off_at` / `master_signed_off_by` on `vims_safety_scm_meeting` and the actual SCM PDF endpoint remains a Step `6.4` dependency.
**Why:** The workflow can require a legally/audit-relevant signature event earlier than the document-export phase, and adding fake PDF behavior or new signature columns mid-phase would create unsupported drift.
**Rule:** If a step requires hybrid digital signature capture before the final export pipeline exists, record the full payload (`typed_name`, `timestamp`, `device_fingerprint`) append-only in `vims_safety_field_history`, keep the canonical state stamp on the current table, and expose any not-yet-built export behavior as an explicit pending seam instead of inventing storage or pretending the export already exists.

## L-040 - Keep time-based SCM tests relative to the live session date
**What happened:** Step `3.8` verification surfaced false-red SCM tests on 2026-04-29 because `test_scm_cadence_warn.py` and `test_scm_overdue_soi_block.py` encoded absolute calendar dates while the production code correctly uses the live current date/time.
**Why:** Handover tests run across sessions and calendar days, so fixed-date fixtures eventually drift even when the feature behavior is still correct.
**Rule:** For time-sensitive Safety tests, anchor fixtures to `timezone.localdate()` / `timezone.now()` or inject a controlled `now_func` into the service under test. Do not hard-code "overdue by N days" calendar dates unless the behavior is explicitly tied to a fixed absolute date.

## L-041 - ORM-backed test tables still need database defaults when older fixtures write raw SQL
**What happened:** Step `4.1` switched the SOI test harness from hand-written SQL table creation to ORM-created `SOIInspection` / area-map / applicability-log tables, and the pre-existing Step `3.8` SOI raw SQL fixtures immediately failed because they omitted fields like `lost_paper_flag`, `section_12_included`, `schema_version`, `is_deleted`, and `created_date`.
**Why:** Replacing a hand-written fixture table with a schema-editor-created model table changes which defaults are enforced at the database layer versus only through ORM inserts, and older raw SQL tests keep depending on the DB side of that contract.
**Rule:** When upgrading a test harness from manual SQL DDL to ORM-created tables, audit every existing raw SQL fixture that inserts into those tables. Add `db_default` for any omitted non-null column or update the fixture explicitly before treating the harness migration as complete.

## L-042 - Frontend route tests must satisfy the full gate stack, not just the form gate
**What happened:** Step `4.2` frontend verification initially surfaced a failing older route test for `/safety/incidents/create/` even though the screen code was fine, because the test only provided `SAF_F_001` and omitted the existing `SAF_P_001` + role gate required by the route.
**Why:** Safety routes frequently stack `PermissionGate`, `ProcessGate`, and `RoleGate`, so an under-specified auth fixture renders `null` and can look like a UI regression when the real mismatch is in the test harness.
**Rule:** When writing or maintaining frontend route tests for gated Safety screens, provide the full auth contract required by the route: form IDs, process IDs, and role. Do not assume a form ID alone is enough unless the route is actually form-gated only.

## L-043 - When step prose names a schema field that the authoritative backend contract does not define, follow the backend contract and carry the drift explicitly
**What happened:** Step `4.3` in `IMPLEMENTATION_PLAN.md` referenced `checklist_version_id` on `vims_safety_soi_inspection`, but `BACKEND_STRUCTURE.md` and the current `0001_initial.py` shell do not define that column.
**Why:** Step-level execution prose can preserve an intended persistence shape that never made it into the authoritative schema contract, and implementing the lower-priority field would create undocumented drift immediately.
**Rule:** If a step file names a schema field that the backend authority does not define, implement the strongest schema-backed behavior available, record the docs drift in `progress.txt` and `tasks/todo.md`, and do not invent the missing column until the authoritative backend contract is revised.

## L-044 - When the current phase needs a live route but the later dashboard contract names a different endpoint, ship the current-phase surface and record the drift
**What happened:** Step `4.4` exposed a docsuite route mismatch: `APP_FLOW.md` put the SOI list compliance tile on `GET /api/safety/soi/compliance/?vessel_id=...`, while `BACKEND_STRUCTURE.md` only named the later dashboard endpoint `GET /api/safety/dashboard/soi-compliance/?vessel_id=...`.
**Why:** The screen-flow document described the phase-local SOI list behavior before the broader dashboard API section caught up, so waiting for the later route would have left the active Step `4.4` surface undocumented in code.
**Rule:** If the active phase needs a route now but a later dashboard section names a different endpoint for the eventual aggregate surface, implement the current-phase route required by the active screen contract, record the mismatch in `progress.txt` and `tasks/todo.md`, and defer endpoint unification until the higher-level dashboard step is reached.

## L-045 - DRF file endpoints must neutralize the framework `?format=` override before using `format` as a business query parameter
**What happened:** Step `4.5` initially shipped the SOI download view with the documented `?format=pdf|xlsx` contract, but DRF intercepted that query parameter during content negotiation and returned `404 Not Found` before the view logic ran.
**Why:** DRF treats `?format=` as a renderer-selection override by default, which silently collides with business routes that also need a `format` query parameter in their API contract.
**Rule:** If a Safety download/export endpoint must accept `?format=` as a business parameter, disable or bypass DRF's query-string format override on that view before wiring the serializer or tests. Do not assume the framework will leave `format` alone.

## L-046 - Mandatory-reason recovery flows must not be implemented as GET actions
**What happened:** Step `4.6` surfaced a docs drift: `BACKEND_STRUCTURE.md` still listed SOI lost-paper recovery as `GET /api/safety/soi/{id}/lost-paper/recover/`, while the step contract and validation rules required a mandatory reason plus an inspection-note mutation before re-download.
**Why:** Endpoint inventory prose can lag behind the actual workflow contract, and a GET route is the wrong shape for a state-changing action that must carry a required reason.
**Rule:** If a Safety workflow mutates audit state and requires a mandatory reason, implement it as a body-carrying write action and record any stale GET route prose as documentation drift. Do not weaken the workflow just to preserve an older endpoint-method summary.

## L-047 - When SOI endpoint auth prose drifts outside the locked permission namespace, keep the shared module gates and treat the endpoint summary as stale
**What happened:** Step `4.7` surfaced a direct SOI auth mismatch: `BACKEND_STRUCTURE.md` still described finding registration with `SAF_F_012` + `SAF_P_013`, while `CLAUDE.md`, the seeded workspace contract, and `APP_FLOW.md` all keep SOI inside the shared `SAF_F_004` form plus `SAF_P_002` register-findings action seam.
**Why:** Endpoint inventory prose can preserve an older or shorthand permission registry even after the module's canonical form/process namespace has been frozen and implemented elsewhere in the workspace.
**Rule:** If an SOI endpoint summary introduces form or process IDs outside the locked shared module namespace, keep the implemented route on the authoritative `SAF_F_*` / `SAF_P_*` contract already seeded in the workspace and record the endpoint auth drift explicitly. Do not mint a second permission namespace just to satisfy stale prose.

## L-048 - When a later phase needs new workflow linkage but the authoritative table shell has no column for it, prefer append-only audit metadata over ad hoc schema widening
**What happened:** Step `4.8` needed SOI findings to remember incident-worthy outcomes, life-threat escalation choices, and linked Incident / Near Miss references, but the current authoritative `vims_safety_soi_finding` shell still has no dedicated link or nudge-note column.
**Why:** Frozen step prose can imply a richer persistence shape than the checked-in workspace schema actually supports, and adding undocumented columns mid-phase would create new drift immediately.
**Rule:** If a phase step requires additional workflow metadata but the authoritative table shell does not define the needed columns, first look for an append-only audit surface already accepted in the workspace, such as `vims_safety_field_history`. Record the metadata there and expose it as derived state instead of widening the schema unless the authoritative backend contract explicitly changes.

## L-049 - When SOI action summaries and the seeded permission registry diverge, follow the seeded/backend action codes for dedicated finding workflows
**What happened:** Step `4.9` surfaced another SOI permission drift: `APP_FLOW.md` still summarized finding closure under the broader shared SOI actions `SAF_P_002` / `SAF_P_004`, while the seeded catalog and backend permission registry already define dedicated finding-closure gates `SAF_P_014` and `SAF_P_015`.
**Why:** Screen-flow summaries can compress multiple SOI actions back into the shared module verbs even after the backend permission map has split them into dedicated action IDs for finer auditability.
**Rule:** When a dedicated SOI finding workflow already has explicit `SAF_P_*` codes in the seeded registry and backend authority, use those dedicated action codes in routes and endpoints, then record any broader APP_FLOW summary as documentation drift instead of collapsing the implementation back to the shared verbs.

## L-050 - When a step example conflicts with the repeated cycle contract, implement the repeated contract and carry the example as drift
**What happened:** Step `4.10` included a sample sentence saying a Feb 1 Section 12 carry should block new carries until July 1, while the Step `4.10` description, `PRD.md`, `APP_FLOW.md`, `USER_GUIDE.md`, and the cited decision all consistently define Section 12 by the current calendar quarter.
**Why:** Step-level sample prose can preserve an older timeline example even when the governing decision and the surrounding docsuite have already converged on a clearer rule.
**Rule:** If a phase-step example conflicts with its governing decision and the repeated docsuite contract, implement the repeated contract, note the example as documentation drift in `progress.txt` / `tasks/todo.md`, and do not encode the stale sample timeline into the product.

## L-051 - When a dedicated backend permission registry exists for a workflow, do not reuse the broader module gate from stale route prose
**What happened:** Step `4.11` surfaced a direct applicability-workflow auth drift: `APP_FLOW.md` still assigned the Master/DPA flow to `SAF_F_004` with `SAF_P_011` / `SAF_P_010`, while `BACKEND_STRUCTURE.md` already split the workflow onto the dedicated applicability gate `SAF_F_013` with `SAF_P_016` / `SAF_P_017`.
**Why:** Route-flow prose can preserve the broader module gate even after the backend permission registry has carved out a dedicated audited workflow surface.
**Rule:** If a Safety workflow already has a dedicated `SAF_F_*` / `SAF_P_*` registry entry in the backend authority, implement that dedicated gate on both API and frontend routes, record the older route prose as drift, and do not collapse the workflow back onto the broader module permission just for consistency with stale docs.

## L-052 - Rolling-window analytics should compare by business date when the persistence seam can normalize timestamps differently than the in-process clock
**What happened:** Step `4.12` introduced the crew-rotation coverage service and then immediately exposed a false-zero metric in the close-flow test even though the same service passed its standalone fixture. The difference came from the close flow persisting `closed_at` through the ORM/DB seam, which normalized the timestamp differently than the fixed in-process clock used to define the rolling-window upper bound.
**Why:** When a workflow persists timezone-aware timestamps and then queries them again inside the same session, the database storage/readback path can normalize the value differently from the Python object that originally generated it. A strict datetime upper-bound can then drop rows that are semantically on the same business day.
**Rule:** For rolling-window analytics that are defined in business-day terms rather than exact wall-clock cutoffs, compare persisted timestamps by date at the query seam unless the spec explicitly requires sub-day precision. This avoids false misses caused by timezone normalization between save-time and query-time representations.

## L-053 - Validate same-DB sibling table families against the live schema before hardening a cross-module join
**What happened:** Step `5.1` still referenced `vims_noon_report` / `vims_departure_report` / `vims_arrival_report` in parts of the Safety docsuite, but the real shared Reporting contract in `ksm_marine_live` for this environment remained the legacy `NoonReport` / `DepartureReport` / `ArrivalReport` / `NoonReportPort` tables.
**Why:** Cross-module handover docs can preserve shorthand or future-state names even when the live sibling module still runs on older table families, and hardening the join against the prose alone would target the wrong runtime surface.
**Rule:** Before hardening any same-DB Safety join, verify the actual sibling table family and key columns in the live shared database first. Implement against the proven runtime contract, then record the docs shorthand drift explicitly in `progress.txt` and `tasks/todo.md`.

## L-054 - Validate live join key types as well as live table names
**What happened:** Step `5.2` confirmed that the live WRH runtime family in `ksm_marine_live` is `wrh_s520_day_entry` / `wrh_s520_month` / `wrh_ship_time_config`, and it also surfaced that the WRH-side `vessel_id` columns are `uniqueidentifier` in SQL Server even though the handover workspace test harness still models vessel IDs as strings.
**Why:** Same-DB join hardening can appear complete once the right table family is identified, but column-type drift on the join keys can still break the runtime contract or produce misleading local assumptions.
**Rule:** When validating a live same-DB integration, inspect the join-key column types in the live schema before closing the step. Record any workspace-vs-runtime type drift explicitly, and keep the implementation passing the live type in the shape the shared database actually expects.

## L-055 - Live CMS roster joins need date-window filtering and GUID-reference resolution, not just "current crew" flags
**What happened:** Step `5.3` surfaced that the real CMS runtime surface in `ksm_marine_live` does not match the simplified handover fixture: `Crew_Onboarding_History` uses `CrewID` / `Vessel` / `SignOnDate` / `SignOffDate`, `HRM501.rank_name` and `HRM501.department_name` store GUID references, and signed-off rows can still carry `is_active = 1`.
**Why:** A naive repository that only checks an "is current" style flag or expects text rank/department columns will silently mis-resolve crew availability across rotation boundaries and will return unreadable GUIDs instead of business labels.
**Rule:** Before closing a CMS live join, validate the real sign-on / sign-off window columns and resolve any GUID-backed rank or department references through the owning master tables. Do not treat `is_active` alone as the onboard truth when the live onboarding history already carries the date window.

## L-056 - A same-DB FK step is only runtime-live if the sibling table family actually exists in the shared database
**What happened:** Step `5.4` targeted the documented `pur_requisition` Purchase contract, but live SQL validation on `2026-04-30` confirmed that the rebuilt `pur_*` Purchase tables are not present in this `ksm_marine_live` environment yet.
**Why:** The Safety docsuite can lock a future same-DB cross-module contract before the sibling module has been deployed into the shared runtime database.
**Rule:** Before calling a same-DB FK or live-join step runtime-complete, verify that the target sibling table family exists in the live database. If it does not, implement the Safety-side seam against the documented contract, record the missing runtime surface explicitly in `progress.txt` and `tasks/todo.md`, and do not guess a legacy substitute table.

## L-057 - When PDF export permissions drift across docs, follow the seeded/backend registry and carry the route prose as stale
**What happened:** Step `6.1` surfaced a direct export-auth mismatch: `BACKEND_STRUCTURE.md` plus the seeded permission catalog used `SAF_P_023` for record-PDF export, while `APP_FLOW.md` and parts of the frontend guidance still summarized export actions under `SAF_P_007`.
**Why:** Endpoint and route prose can preserve an older shared export action even after the backend permission registry has split record-PDF export into a dedicated audited process ID.
**Rule:** If a Safety export workflow already has an explicit `SAF_P_*` code in the seeded registry and backend authority, implement that dedicated code on the API and route gate, then record the older export prose as documentation drift instead of collapsing back to the stale shared action.

## L-058 - Validate the live vessel-particulars table family and lookup keys before hardening MSC-MEPC.3 exports
**What happened:** Step `6.2` needed Appendix 2 ship-particulars auto-fill, and the docsuite named `vims_vessel_particulars`, but live SQL validation on `2026-04-30` showed that this environment exposes the vessel-particulars contract through `dbo.VesselData` instead, with `id` as a GUID and `vesselCode` as the reporting-friendly lookup key.
**Why:** Cross-module handover docs can normalize future-state table names before the sibling runtime has actually been renamed or reshaped in the shared database.
**Rule:** Before hardening any Safety vessel-particulars join or export mapping, verify the live table family and lookup keys in `ksm_marine_live` first. Implement against the proven runtime contract, support the real key shape (`id` and/or `vesselCode`) where needed, and record any docs drift explicitly in `progress.txt` and `tasks/todo.md`.

## L-059 - When a PDF contract describes richer near-miss fields than the shared handover schema exposes, map from proven current fields and record the seam explicitly
**What happened:** Step `6.3` required a near-miss lightweight PDF with `What Happened + Suggestion + Immediate Action`, but the current shared `vims_safety_incident` handover shell has no dedicated `suggestion` or `immediate_action` column for near misses.
**Why:** The docsuite can lock a user-facing export shape that is richer than the currently modeled shared-table surface in the handover workspace, especially where Near Miss still rides on the generic incident shell.
**Rule:** When an export contract references dedicated near-miss fields that do not exist in the proven workspace schema, do not invent new columns or silent defaults mid-step. Map from the strongest current source fields or helpers already present in the implementation, keep the behavior explicit in code, and record the schema-vs-export seam in `progress.txt` and `tasks/todo.md`.

## L-060 - When a PDF contract expects richer signature persistence than the workspace stores, expose the status seam instead of inventing signature rows
**What happened:** Step `6.4` required the SCM PDF to show Master + CO + attendee signatures, but the handover workspace currently persists only the Master hybrid digital signature explicitly while CO and attendee digital-signature rows remain unmodeled.
**Why:** Export-facing docs can lock a richer signature presentation than the underlying handover schema actually stores, especially where attendance/preparer surfaces exist but dedicated signature records do not.
**Rule:** When an export surface needs signature coverage beyond the persisted schema, render the strongest current status from proven stored fields, label the remaining gap explicitly in the export and tracker files, and do not invent new signature storage mid-step just to satisfy the document prose.

## L-061 - Paper-first SOI exports must stay audit-summary only, even when the PDF surface is implemented later than the checklist workflow
**What happened:** Step `6.5` introduced the SOI summary PDF after the earlier paper-first SOI checklist flow was already complete, and the export still needed to avoid reproducing per-item Yes/No checklist answers even though it now had access to the reported inspection context.
**Why:** A later export step can create pressure to reconstruct richer digital detail from the reporting workflow, but D-GAP-E4 keeps the paper checklist as the authoritative record and the post-submission PDF is only an audit summary.
**Rule:** When implementing a paper-first SOI export after the main workflow already exists, include only the post-submission audit summary surfaces that the docs lock: stamped areas, findings, trainees, signatures, audit metadata, and the checklist unique-ID footer. Do not rebuild or infer per-item checklist answers into the digital PDF just because the export layer can access the record.

## L-062 - Attachment-mining export bundles must ignore generated export metadata or they will recurse their own PDFs back into the bundle
**What happened:** Step `6.6` initially over-counted auditor ZIP attachments because the bundle builder scanned `SafetyFieldHistory` JSON for path-like values and picked up the freshly written `export_path` / `file_name` metadata from the record-PDF audit rows.
**Why:** The export pipeline legitimately records generated PDF storage metadata in append-only field history, and a generic path scan cannot distinguish "supporting attachment" from "just-generated bundle member" unless export bookkeeping keys or rows are filtered out explicitly.
**Rule:** When building attachment bundles from field-history JSON, exclude known export-history row types and export bookkeeping keys such as `download_path`, `export_path`, and `file_name`. Only real supporting evidence paths belong under the bundle's `attachments/` subtree.

## L-063 - When the docs lock dashboard contributors but not the numeric score formula, keep the handover score transparent and record it as a seam
**What happened:** Step `7.1` locked the composite rollup inputs for FEAT-SAF-DASH-001 (`open incidents`, `open near misses`, `open findings`, `overdue CAs`, and `SOI Compliance %`), but the docsuite still did not freeze the exact weighting formula that converts those contributors into one 0-100 Safety Health Score.
**Why:** The product docs were specific enough to implement the rollup contract and API shape, but not specific enough to justify a hidden or arbitrary weighting model without carrying the assumption forward.
**Rule:** If a dashboard step locks the contributing metrics but not the final numeric weighting formula, implement a transparent interim score calculation, expose the component scores directly in the payload/UI, and record the formula as an explicit handover seam in `progress.txt` and `tasks/todo.md` until product freezes the final rule.

## L-064 - When dashboard route prose conflicts with the backend form registry, align the whole surface to the dedicated dashboard gate
**What happened:** Step `7.2` exposed a dashboard permission drift: `BACKEND_STRUCTURE.md` locked the dashboard surface to `SAF_F_015`, while `APP_FLOW.md` and the older workspace route shell still referenced `SAF_F_005`.
**Why:** Screen-flow prose and carry-forward frontend shells can preserve an earlier shared form gate even after the backend authority has split the dashboard into its own audited surface.
**Rule:** If dashboard route prose conflicts with the backend form registry, align the backend view, frontend route shell, sidebar, tests, and demo auth surface to the dedicated backend dashboard gate, then record the stale route prose as drift in `progress.txt` and `tasks/todo.md`.

## L-065 - When the backend permission registry is internally stale, do not mint a new search gate mid-step
**What happened:** Step `7.3` surfaced a search permission drift: `APP_FLOW.md` and the existing route shell used `SAF_F_005`, while `BACKEND_STRUCTURE.md` listed `SAF_F_016` for Safety Search but also mislabeled nearby form IDs such as `SAF_F_005`.
**Why:** The backend permission table around the search IDs is internally inconsistent in this handover package, so blindly switching to the newer-looking code would have created a second parallel gate without a coherent surrounding registry.
**Rule:** If the permission-registry source is internally stale around the target IDs, keep the already-implemented route gate that matches the broader route shell and user flow, then record the drift explicitly instead of inventing a new permission surface mid-phase.

## L-066 - When export throttling prose conflicts with higher-priority product acceptance, follow the product contract and carry the throttle table as drift
**What happened:** Step `7.6` exposed a dashboard-export rule conflict: `VALIDATION_RULES.md` still lists `POST /api/safety/dashboard/export/` at `5/hour`, while the higher-priority `PRD.md` acceptance criteria for `FEAT-SAF-DASH-007` explicitly say "No DPA export rate-limiting in V1."
**Why:** Validation tables can preserve an older operational guardrail even after the product contract has been relaxed for a specific privileged export surface.
**Rule:** If an export throttle in `VALIDATION_RULES.md` conflicts with the higher-priority `PRD.md` acceptance criteria, implement the PRD contract, omit the stale throttle from the API, and record the mismatch in `progress.txt` and `tasks/todo.md` until the docs are reconciled.

## L-067 - If parent-bound audit history must purge with the record, write retention summaries to a system-scoped audit parent instead
**What happened:** Step `7.8` required an audit entry for the hard-delete retention job, but the same docsuite also locks `D-GAP-M33`, which deletes parent-bound `vims_safety_field_history` rows when the parent incident / near-miss / SCM / SOI is purged.
**Why:** A purge workflow can ask for an audit trail and also require parent-tied audit cleanup; if both are implemented on the same parent-bound history surface, the summary audit row deletes itself in the same operation.
**Rule:** When a workflow needs a durable purge summary but the normal append-only history is contractually tied to the deleted parent, store the purge summary under a separate system-scoped audit parent and record that seam explicitly in `progress.txt` and `tasks/todo.md` instead of violating the parent-retention rule.

## L-068 - When the user says remove a title, identify whether it is a page heading or a field label before editing
**What happened:** A Maintain Mode cleanup initially removed Phase 3 page/PDF headings when the requested target was the `Title` field shown alongside `Type`, `Description`, and `Why is this needed?`.
**Why:** The word "title" can refer to a visible page heading, a phase navigation label, a PDF section title, or a form field label. Treating it as a generic heading created the wrong change.
**Rule:** Before removing ambiguous "title" text, search for the surrounding labels or wording the user cites and patch that exact UI/PDF field surface. If the surrounding labels are provided, use them as the selector and do not change unrelated headings.

## L-069 - Reclassify immediately when a validation request contradicts canonical warn-only behavior
**What happened:** CR-014 was initially classified as Tier 2 because it changed SCM validation, but discovery showed canonical APP_FLOW, BACKEND_STRUCTURE, VALIDATION_RULES, USER_GUIDE, and SSOT statements explicitly made SCM WRH gaps warn-only and non-blocking for meeting creation.
**Why:** A validation rule can look local until docs reveal it supersedes a frozen cross-module decision such as D-GAP-M11.
**Rule:** When Maintain Mode discovery finds a requested validation change contradicts a documented "warn-only", "never blocks", or equivalent canonical statement, stop before coding, reclassify to Tier 3, add an implementation-plan amendment and superseding SSOT decision, then continue.

## L-070 - UI removal can still be Tier 3 when docs make the tool a canonical guard
**What happened:** CR-015 was initially classified as Tier 2 because it looked like a Phase 4 UI cleanup, but discovery showed SSOT, PRD, APP_FLOW, USER_GUIDE, and VALIDATION_RULES still described Evidence Check / Evidence Matrix as a current Phase 4 supporting tool and confirmation-bias gate.
**Why:** A visible tool can be part of a documented validation or investigation-control contract even if the code change is mostly frontend routing.
**Rule:** When removing a UI tool, search the canonical docs for that tool's validation, route, and decision references before coding. If the tool is documented as a gate or canonical workflow element, reclassify to Tier 3, add an implementation-plan amendment, and record the superseding SSOT decision.

## L-071 - Removing form fields can be Tier 3 when docs define them as investigation controls
**What happened:** CR-016 looked like a Phase 4 Witness Notes simplification, but discovery showed SSOT, PRD, APP_FLOW, USER_GUIDE, and VALIDATION_RULES still described formal/informal selection, 4-phase interview fields, read-back, witness signature, and copy-to-witness as current investigation controls.
**Why:** Form fields may encode documented evidence-quality or legal-defensibility behavior even when the user experiences them as UI clutter.
**Rule:** Before removing Safety investigation form fields, search canonical docs for the field labels and validation IDs. If the fields are tied to a canonical decision or validation rule, reclassify to Tier 3, keep legacy API compatibility explicit, and add a superseding SSOT decision for the current UI.

## L-072 - Removing stale validation controls must update UI, API, PDF, and docs together
**What happened:** CR-018 removed the Incident Phase 1 First Checks checklist after discovery showed the current backend submit path no longer required it, while SSOT, PRD, APP_FLOW, VALIDATION_RULES, FRONTEND_GUIDELINES, and PDF field summaries still described it as a current control.
**Why:** A control can become stale unevenly: backend validation may stop enforcing it while UI, serializers, PDF output, and canonical docs continue to surface the old concept.
**Rule:** When removing a stale Safety validation/control field, search all four surfaces before coding: visible UI, frontend/API payload contracts, PDF/report output, and canonical docs. If any canonical doc still defines the field as current behavior, treat the removal as Tier 3, add a superseding SSOT decision, and leave any database-only compatibility explicitly documented.

## L-073 - Hiding a field can supersede a prior CR even when the DB column stays
**What happened:** CR-032 was initially classified as Tier 2 because it looked like a Phase 1 UI cleanup, but discovery showed CR-024 and the current SSOT explicitly defined Last Port as a visible Phase 1 reporting-context field.
**Why:** Keeping the database column for compatibility does not make the change only cosmetic when the current docs say the field is part of the visible user workflow.
**Rule:** Before hiding or omitting a Safety form field, search recent CRs and SSOT field-contract rows for that exact label/column. If current docs state it is visible/current, reclassify to Tier 3, add an implementation-plan amendment, and supersede only the visible/payload behavior while documenting database compatibility.

## L-074 - Backend editability is incomplete without visible UI affordances
**What happened:** CR-039 made Incident phases 2-6 save endpoints editable before office approval, but the Phase 2 RCA saved-cause cards still had no Edit action, so users could not discover how to correct saved Immediate/Root causes.
**Recurrence:** CR-041 found the same gap on later incident phases: Corrective Action, Preventive Action, Lessons Learned, Documents, and Witness Statement saved cards also needed visible Edit controls and existing-row update tests.
**Why:** Treating an API update path as "editable" misses the user-facing workflow requirement: users need an obvious control at the saved item they want to change.
**Rule:** When declaring a screen state editable, verify the visible UI has an edit affordance, the form can load existing values, the save path updates the existing row rather than duplicating it, and a regression test covers that interaction.

## L-075 - Visible workflow phases must be reversible across nav, routes, gates, PDFs, and docs
**What happened:** CR-038 split Incident Corrective Action, Preventive Action, and Lessons Learned into separate visible phases, but the user later removed the Lessons Learned phase and requested Office Review comments instead.
**Why:** A phase split can look like a UI-only improvement, but it changes navigation, route compatibility, continue buttons, office-review readiness, PDF section defaults, and canonical workflow docs. Removing one phase later requires touching every one of those surfaces, not only hiding a tab.
**Rule:** When adding or removing a visible workflow phase, verify the phase switcher, direct routes, redirect/back-link behavior, transition targets, validation/preflight copy, PDF selector defaults, endpoint contracts, tests, SSOT, implementation plan, and user docs in one change. Keep old URLs as redirects when existing links may still point there.

## L-076 - Removing a visible phase requires renumbering the remaining visible sequence
**What happened:** CR-042 removed the visible Lessons Learned phase but left Add Evidence, Office Review, and Check Actions displayed as Phase 6, Phase 7, and Phase 8, so the UI appeared to skip from Phase 4 to Phase 6.
**Why:** Keeping backend compatibility numbers in the visible labels leaks implementation details and makes a cleaned workflow look broken to users.
**Rule:** After any visible workflow phase is removed, verify the user-facing sequence has no numbering gaps. Keep legacy backend phase numbers only in compatibility notes, route/API names, and helper mappings, not in tab labels or user training copy.

## L-077 - Do not hide a direct navigation task behind a second click
**What happened:** CR-045 found the Phase 5 Add Evidence Witness Statement card expanded first and then showed an **Open Witness Statement** link, even though the user expected the Witness Statement click to open the witness page directly.
**Why:** Disclosure cards are useful for optional detail, but they add friction when the card label is itself the intended navigation action.
**Rule:** For support-tool cards like Witness Statement, decide whether the first click should expand details or perform navigation. If the user asks to open a tool, make the labelled card/link navigate directly and add a regression test that the intermediate action copy is absent.

## L-078 - PDF availability wording can hide a validation contract
**What happened:** CR-050 was initially classified as Tier 2 because it looked like an Office Review UI wording cleanup, but the requested removal of "Formal incident PDF export is available after Phase 7 acceptance" also removed backend export validation and superseded canonical PDF availability behavior.
**Why:** A visible warning line can be backed by the same backend guard that blocks the user, so removing the wording without checking the renderer would leave the product behavior unchanged.
**Rule:** When a user asks to remove export availability wording and "no such validation", search both the preview message and the actual renderer/export endpoint. If the guard contradicts current docs, reclassify to Tier 3, add an implementation-plan amendment, and test both preview and download paths.

## L-079 - Cardinality changes can contradict frozen plan locks
**What happened:** CR-057 was initially classified as Tier 2 because it looked like a local duplicate-row validation change, but the frozen implementation plan explicitly locked recommendation cardinality to one-row-per-tier.
**Why:** A uniqueness constraint or duplicate-row guard may encode an old architecture decision, not just a field validation rule.
**Rule:** Before changing Safety row cardinality, search the implementation plan and backend-structure docs for the table name, constraint name, and domain word such as cardinality. If a frozen plan lock is superseded, reclassify to Tier 3, add an implementation-plan amendment, and record the superseding SSOT decision before closing the change.

## L-080 - Prefer ORM relationship checks over RawSQL for list flags
**What happened:** The CAR list `pv_due` flag used a raw SQL table subquery while the matching filter used ORM joins, so a dashboard probe with `pv_due=true&page_size=1` could fail on the SQL Server runtime path even though lightweight test coverage did not expose the raw-table dependency.
**Why:** List flags often look like harmless annotations, but raw SQL bypasses Django's backend quoting, relationship metadata, and test portability. SQLite-style coverage can miss SQL Server-specific failures until a normal frontend query hits the endpoint.
**Rule:** For booleans derived from related rows, use ORM `Exists`, `Prefetch`, or serializer methods before RawSQL. If RawSQL is unavoidable, add a regression test for the exact frontend query shape and validate against the SQL Server path when available.

<!-- Session close review completed 2026-04-30 10:21. No new lesson added for Step 5.5. Latest standing addition remains L-056. Session closure confirmed after Step 5.5 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 10:37. No new lesson added for Step 5.6. Latest standing addition remains L-056. Session closure confirmed after Step 5.6 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 10:57. Added L-057 for the Step 6.1 PDF export permission-registry drift. Session closure confirmed after Step 6.1 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 11:39. Added L-059 for the Step 6.3 near-miss schema-vs-export mapping seam. Session closure confirmed after Step 6.3 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 11:53. Added L-060 for the Step 6.4 SCM signature-surface seam. Session closure confirmed after Step 6.4 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 12:05. No new lesson added for the Step 6.5 planning-only handoff session. Latest standing addition remains L-060. Session closure confirmed after docs review, plan preparation, and tracker sync in the handover workspace. -->
<!-- Session close review completed 2026-04-30 12:22. Added L-061 for the Step 6.5 paper-first SOI summary export boundary. Session closure confirmed after tracker sync and verification-backed Step 6.5 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 12:49. Added L-062 for the Step 6.6 export-history attachment recursion boundary. Session closure confirmed after tracker sync and verification-backed Step 6.6 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 13:21. Added L-063 for the Step 7.1 composite-score weighting seam. Session closure confirmed after tracker sync and verification-backed Step 7.1 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 13:49. Added L-064 for the Step 7.2 dashboard form-gate drift. Session closure confirmed after tracker sync and verification-backed Step 7.2 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 15:52. Added L-065 for the Step 7.3 search permission-registry drift. Session closure confirmed after tracker sync and verification-backed Step 7.3 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 16:02. No new lesson added for Step 7.4. Latest standing addition remains L-065. Session closure confirmed after tracker sync and verification-backed Step 7.4 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 16:27. No new lesson added for Step 7.5. Latest standing addition remains L-065. Session closure confirmed after tracker sync and verification-backed Step 7.5 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 16:46. Added L-066 for the Step 7.6 dashboard-export throttle drift. Session closure confirmed after tracker sync and verification-backed Step 7.6 completion in the handover workspace. -->
<!-- Session close review completed 2026-04-30 17:15. No new lesson added for Step 7.7. Existing L-006, L-051, and L-064 already cover the progress-handoff and permission-registry drifts handled in this session. -->
<!-- Session close review completed 2026-04-30 17:29. Added L-067 for the Step 7.8 retention-audit summary conflict with parent-bound field-history purge. Session closure confirmed after tracker sync and verification-backed Step 7.8 completion in the handover workspace. -->
2026-07-21 | Certs class snapshot PDFs | User correction showed that visible page data from page 3 onward can still be image-only PDF content with zero extractable text. Before declaring a class-status upload unusable, inspect all pages for extractable text and image objects, then test OCR on embedded page images; if OCR reads the class table, add a bounded OCR fallback instead of rejecting the PDF.

## L-081 - PDF copy changes can supersede canonical artifact controls
**What happened:** A Certs print PDF cleanup was initially classified as Tier 1 because it looked like a renderer text change, but discovery showed the implementation plan, PRD, design system, security, and field map explicitly required visible print ID, state hash, footer, and validity output.
**Why:** Report labels can encode audit and identifiability decisions even when they look like visual clutter.
**Rule:** Before removing labels from generated PDFs, search canonical docs for the exact labels and related control IDs. If the labels are tied to artifact identity, security, footer, watermark, or glossary decisions, reclassify to Tier 3 and supersede only the visible-output behavior while preserving DB/API/audit traceability.

## L-082 - Class report memoranda are not Conditions of Class
**What happened:** BV Class Memoranda and Statutory Memoranda were treated as Conditions of class because docs and code broadened the class-report review bucket beyond the exact BV Conditions of Class section. The user corrected the behavior, and the change had to be reclassified from Tier 1 to Tier 3 because canonical docs described the broader behavior.
**Recurrence:** Immediately after the BV-only correction, the user clarified that the same strict rule applies to all class societies: KR Actionable Note / Statutory Condition rows and NK Condition of Installation / Condition of Statutory Survey rows must also stay out of the Conditions of class bucket.
**Why:** Class society reports can place operationally relevant note sections near Conditions of Class, but nearby note sections are not the same regulatory condition bucket.
**Rule:** Before putting parsed class-report text into Conditions of class, match the exact Condition of Class / Conditions of Class source section for that class society and add negative regressions for adjacent note, installation, statutory, and memoranda sections. If canonical docs generalized the section incorrectly, reclassify to Tier 3 and add a superseding SSOT decision.

## L-083 - Print UI simplification can supersede locked print controls
**What happened:** CR-121 initially looked like a visible Certs print-form simplification, but discovery showed locked decisions for normal print scope variants, watermark controls, and optional recipient email.
**Why:** Print controls are not only visual form fields; they encode documented artifact scope, delivery, and audit behavior even when backend compatibility remains.
**Rule:** Before removing Certs print controls, search SSOT and docs for D-CERT-138, D-CERT-140, D-CERT-149, scope labels, watermark labels, and recipient/email labels. If current docs define those controls as visible behavior, reclassify to Tier 3, add a superseding SSOT decision, and document which API/artifact capabilities remain compatible.

## L-084 - Locked UI labels need the same cascade as behavior
**What happened:** The normal Certs print label was locked as "Print Vessel Status" in D-CERT-208, then the user corrected it to "Print certs status".
**Why:** A label-only change can still contradict canonical docs when the exact visible text was recorded as a decision.
**Rule:** When changing a label that appears in SSOT, implementation-plan amendments, user guide, app flow, or tests, treat it as a docs cascade and add a superseding decision if the old wording was locked.

## L-085 - Large certificate lists should be section-first in print/share UI
**What happened:** The Certs print/share UI exposed individual certificate selection even though vessels can have hundreds of certificate rows, making the picker impractical.
**Why:** A technically precise selection model can fail operationally when the normal user intent is section-wise printing or sharing.
**Rule:** For Certs print/share user workflows, prefer section-based selection in the normal UI and keep individual certificate IDs only as backend-compatible payload support unless the user explicitly asks for per-certificate selection.

## L-086 - Section dropdowns must use catalog sections, not paged certificate rows
**What happened:** The Print certs status and Share Bundle section pickers were built from the current tracked-item query, so the dropdown could be empty or incomplete instead of matching the vessel dashboard Section filter.
**Why:** Tracked-item queries are paged and may not carry a complete section list, while the user's mental model is the canonical catalog section list.
**Rule:** When a UI asks for certificate sections, source options from `useCatalogSections()` / `vims_certs_catalog_section`. Use tracked items only for vessel context or row data, not for the section option list.

## L-087 - Section dropdown labels should say sections
**What happened:** The Print certs status dropdown contained certificate sections but still used the older "Certificate List" label.
**Why:** A generic list label is ambiguous after the workflow changed from certificate-row selection to section selection.
**Rule:** When replacing certificate-row pickers with section pickers, update the visible label to "Certificate sections" on every user-facing section-selection control and cascade exact locked labels in docs/tests.

## L-088 - Generated result panels should stay action-focused
**What happened:** The Certs generated artifact result panel showed Scope, Hash, Watermark, and Recipient even after the normal print workflow was simplified for users.
**Why:** Audit metadata is still stored, but showing it in the immediate success panel makes the post-generation view look technical and crowded.
**Rule:** For normal Certs print/share success panels, show the user what they can act on: generated time, page count, downloads, and email status. Keep audit/hash/scope/watermark metadata in stored records/history unless explicitly needed on the screen.

## L-089 - Clean print output rules must cover every generated format
**What happened:** The normal Certs PDF had already stopped printing internal print ID/hash/scope metadata, but the Excel companion still printed Print ID, Scope, and System state hash rows.
**Why:** A print/export workflow can generate multiple artifacts from separate renderers, so fixing only the PDF leaves the user-facing Excel with the same technical clutter.
**Rule:** When removing internal metadata from generated print output, inspect and test every delivered format in the workflow: PDF, Excel, ZIP manifest, result panel, email body, and Print History. Preserve DB/API/audit traceability, but keep normal user-facing files clean unless the user explicitly asks for those identifiers.
