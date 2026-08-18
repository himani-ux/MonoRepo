# VIMS Audit Module — Journey Map (v3, hand-authored from the banked decision record)

Authored 2026-07-13 (v3 handover upgrade); **persona layer repaired 2026-07-14 (v4)**. JOURNEY-1..14 across Batches A–D — A plan & schedule (1, 9, 10, 14), B conduct & submit (2, 3), C closure & review (4–8), D oversight queues, office audit & external (11, 12, 13). Grounded in the frozen `VIMS-AUDIT-RS-MODULE-SSOT.md` v0.21 (D-AUDRS-001..287 + supplemental D-124..137 + D-288..299) and `docs/COVERAGE.md` 237/237 GREEN (N=925); screens/routes per `docs/APP_FLOW.md` `## Screens`; every oracle cites `docs/PRD.md` FEAT acceptance criteria. Origin is PERSONA (hand-derived — this bundle predates Step-0 extraction). Runtime validation status: starter Playwright journey specs were authored under `tests/journeys/` on 2026-08-17, but no trusted runtime GREEN ledger is claimed; record-specific closure specs require seeded sample IDs via environment variables. Coverage accounting: 78 P0/P1 anchors = 76 journey-covered + 2 gap records (`JOURNEY_COVERAGE_GAPS.md` — FEAT-AUD-1401, FEAT-AUD-1403, build-time infra with no user surface).

**Two grammars, deliberately distinct (v4 repair — `journey/bin/check-persona-journeys.sh`).** Personas are the **SSOT `## Personas` set P1..P8** (D-AUDRS-295; mirrored at `docs/PERSONAS.md`) — not ad-hoc labels.
- `(misbehavior: <kebab-token>)` = **a human mistake made by this journey's own persona.** The token must be one of **that persona's** `known_misbehaviors` in the SSOT — the gate fails `FOREIGN_MISBEHAVIOR` otherwise. A persona journey without its persona's mistakes is a happy path in costume.
- `(negative_state: <snake_token>)` = **the system's reaction** — the guard, block, rejection or degraded state named in this journey's `negative_states:` field. These are *not* human mistakes and are never annotated as such.
- `persona:` names **one** persona — the **primary actor**, i.e. the persona who performs the journey's decisive/misbehavior step (SSOT §22 A-4). Where a second persona takes part, it stays named in the steps text (JOURNEY-3 · 8 · 12 · 13). No persona was dropped and no behavior changed.

## JOURNEY-1 — "SEQ Manager plans the internal vessel audit and the window, Lead Auditor and schedule notification come out right"
origin:          PERSONA
persona:         P1 (SEQ Manager / DPA)
goal:            plan a routine internal vessel audit from the register — auto-computed 8–12-month window, a qualified scope-matched Lead Auditor, and the schedule notification on all three channels — while an out-of-scope office user sees none of it
priority:        P0
covers:          FEAT-AUD-201, FEAT-AUD-202, FEAT-AUD-203, FEAT-AUD-801, FEAT-AUD-802, FEAT-AUD-803, FEAT-AUD-1003, FEAT-AUD-1204, FEAT-AUD-1205
flows:           AFJ-1
oracle_surface:  UI
negative_states: out_of_scope_vessel_blocked
data_fixtures:
steps:
  1. SEQ Manager opens the audit plan register (SCR-AUD-7), where the T-90 window tick has already auto-created a draft PLANNED entry for the target vessel; she completes it — classification INTERNAL, harmonised standards default — and the 8–12-month window shows, computed from the last completion via master_audit_window_rule, surfaced on both register and dashboard.
  2. Mid context-switch across four vessels, the DPA assigns the Lead Auditor on the plan entry (SCR-AUD-7) straight off the top of the list without checking that auditor's scope or standards match (misbehavior: assigns-lead-auditor-without-checking-scope-standards); the unchecked pick cannot land wrong, because the picker offers only active, non-expired, scope-matching rows from the qualified-auditor master; the plan moves PLANNED → CONFIRMED.
  3. The system fires AUDIT_SCHEDULED triple-channel (in-system + email + Slack) to Master + HoDs; the in-system row commits in the same DB transaction, and a Slack relay hiccup retries without ever rolling back the plan action.
  4. An office user whose master_RoleByVessel scope excludes this vessel tries to open the same plan entry and audit and is denied (negative_state: out_of_scope_vessel_blocked) — vessel-scope filtering shows them nothing outside their scope.
oracle:          per FEAT-AUD-203 AC-1 the T-90 tick notified the SEQ Manager and auto-created the draft PLANNED entry; per FEAT-AUD-202 AC-1/AC-3/AC-4 the window equals last_completion +8/+12 months, read from master_audit_window_rule (never hardcoded) and surfaced daily on dashboard + register; per FEAT-AUD-201 AC-2 the plan status runs PLANNED → CONFIRMED; per FEAT-AUD-1003 AC-1 and FEAT-AUD-1204 AC-1 the Lead Auditor picker filters to active + non-expired + scope-matching qualified-auditor rows — which is exactly what makes the DPA's unchecked pick safe rather than lucky; per FEAT-AUD-802 AC-1/AC-2 AUDIT_SCHEDULED is a fixed type with a fixed resolver; per FEAT-AUD-803 AC-1 recipients resolve to Master + HoDs; per FEAT-AUD-801 AC-1/AC-3 the in-system row is source-of-truth in the same transaction and channel failure never rolls back; per FEAT-AUD-1205 AC-1 the out-of-scope office user is denied by the master_RoleByVessel filter.
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-2 — "Conductor registers the audit, walks the checklist and a stalled-link double-save never yields a second CAR"
origin:          PERSONA
persona:         P3 (Conductor)
goal:            work from the pre-audit dashboard through type-branched registration and the F 605 checklist walk to a captured finding with clause refs and objective evidence — with exactly one CAR per finding even after a double-click on the slow satellite link
priority:        P0
covers:          FEAT-AUD-101, FEAT-AUD-102, FEAT-AUD-103, FEAT-AUD-104, FEAT-AUD-105, FEAT-AUD-106, FEAT-AUD-107, FEAT-AUD-108, FEAT-AUD-109, FEAT-AUD-301, FEAT-AUD-302, FEAT-AUD-303, FEAT-AUD-304, FEAT-AUD-305, FEAT-AUD-306, FEAT-AUD-307, FEAT-AUD-701, FEAT-AUD-1001, FEAT-AUD-1002, FEAT-AUD-1105, FEAT-AUD-1106, FEAT-AUD-1206
flows:           AFJ-2
oracle_surface:  UI
negative_states: duplicate_finding_submit_rejected
data_fixtures:
steps:
  1. Conductor opens the pre-audit dashboard (SCR-AUD-14) — the reused deficiencies view filtered to the target vessel — reviews previous-audit findings and outstanding NCs, and uploads a pre-audit reference PDF (≤10 MB) into the attachment store.
  2. Via the split sidebar's Audit module the Conductor registers the audit at the type-branched entry (SCR-AUD-1): the AUDIT branch loads (Detention checkbox hidden), header fields, harmonised standards, auditee type VESSEL, subtype ANNUAL_INTERNAL, audit team and named opening attendees (ranks auto-suggested) are captured; the F 605 checklist auto-picks by ship type; the audit goes CONFIRMED → IN_PROGRESS.
  3. Conductor walks the checklist (SCR-AUD-3) item by item — Compliant / Add Finding / Remarks — and raises one finding, but first books it against the wrong standard: he leaves rule_book_type on ISM out of habit while entering a SOLAS chapter reference (misbehavior: enters-finding-against-wrong-standard); the app layer validates rule_clause_id against the master named by rule_book_type and rejects the mismatch. Corrected, the finding carries finding_type NC, a primary ISM clause plus a second clause through the multi-clause junction, one OTHER-book clause with free-text ref (5–200 chars) that increments the OTHER QA counter, and objective evidence text.
  4. Saving the finding auto-creates exactly one CAR numbered AUDIT-YYYY-NNN through the existing application-code path (no DB trigger); the audit detail (SCR-AUD-2) shows the finding-CAR pair.
  5. On the stalled satellite link the save shows no confirmation and the Conductor clicks Save Finding again; the repeated submission is not honoured as a new capture (negative_state: duplicate_finding_submit_rejected) — the audit detail (SCR-AUD-2) still shows that finding with exactly one CAR, per the 1:1 rule.
oracle:          per FEAT-AUD-1206 AC-1 the pre-audit widget reuses /deficiencies + a vessel filter and shows previous findings + outstanding NCs; per FEAT-AUD-1105 AC-1 and FEAT-AUD-1106 AC-1 the PRE_AUDIT_REFERENCE upload lands in the categorised attachment store within type/size limits; per FEAT-AUD-109 AC-1/AC-2 the sidebar exposes Audit top-level with its sub-tabs; per FEAT-AUD-101 AC-1/AC-2, FEAT-AUD-102 AC-1/AC-2, FEAT-AUD-103 AC-1, FEAT-AUD-104 AC-1, FEAT-AUD-106 AC-1, FEAT-AUD-107 AC-1/AC-2, FEAT-AUD-108 AC-1 the AUDIT branch captures header/classification/standards/auditee/subtype/attendees/team with the Detention checkbox hidden; per FEAT-AUD-105 AC-2 the branch admits only office users holding AUDIT_P_001/003; per FEAT-AUD-301 AC-1/AC-2 the checklist auto-picks by auditee_type + standards + ship_type and walks per item; per FEAT-AUD-302 AC-1, FEAT-AUD-304 AC-1, FEAT-AUD-305 AC-1, FEAT-AUD-306 AC-1 and FEAT-AUD-307 AC-1 the finding carries its type, validated polymorphic clause refs with one primary, the OTHER free-text ref, and objective evidence — and per FEAT-AUD-304 AC-1 specifically, the app layer validates rule_clause_id against the master named by rule_book_type, so the Conductor's wrong-standard clause reference is rejected rather than stored; per FEAT-AUD-1001 AC-1 and FEAT-AUD-1002 AC-1 the pickers are powered by the seeded audit-domain and rule-book masters; per FEAT-AUD-303 AC-1/AC-2/AC-3 and FEAT-AUD-701 AC-1 exactly one CAR (AUDIT-YYYY-NNN, unchanged engine) exists for the finding after the duplicate click — the repeat never produces a second CAR.
evidence:        []
test:            tests/journeys/journey-002.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-3 — "Conductor is hard-blocked at submit until the record is complete, findings freeze, and the Master's acknowledgement starts the SLA clocks"
origin:          PERSONA
persona:         P3 (Conductor)
goal:            finish the scorecard and equipment list, clear the four submit gates, watch the findings list freeze against a late insert, and have the Master's acknowledgement — not the finding date — start the NC closure SLA clocks (primary actor = P3, who commits the decisive post-submit insert; P5 (Vessel Master) acts in step 4)
priority:        P0
covers:          FEAT-AUD-110, FEAT-AUD-308, FEAT-AUD-309, FEAT-AUD-310, FEAT-AUD-311, FEAT-AUD-412, FEAT-AUD-1101
flows:           AFJ-3
oracle_surface:  UI
negative_states: submit_gate_blocked, finding_add_after_submit_rejected
data_fixtures:
steps:
  1. Conductor fills the 14-area scorecard on the audit detail (SCR-AUD-2) — deliberately leaving one area blank — plus the equipment-tested list, a ≥100-char audit summary, and the named closing-meeting attendees.
  2. Conductor clicks Submit with the one scorecard row still blank; the transition hard-blocks (negative_state: submit_gate_blocked) naming the failed gate; after populating all 14 rows (N/A counts) the re-submit passes all four gates and the audit moves IN_PROGRESS → REPORT_FINALIZED.
  3. With the report finalized, classification/standards were already locked from the first finding, and the findings list freezes: Add Finding is hidden. The Conductor remembers one more deficiency from the engine-room walk and pushes it in through the API anyway, after the audit is submitted (misbehavior: adds-finding-after-audit-submitted); the forced insert is rejected HTTP 409 (negative_state: finding_add_after_submit_rejected) — the frozen record is the record.
  4. P5 (Vessel Master) opens the finalized report on SCR-AUD-2 and clicks "Vessel Acknowledge Audit Report" (Master-rank-bound); the status moves REPORT_FINALIZED → VESSEL_ACKNOWLEDGED and the NC closure SLA clocks start counting from this instant — the wet-ink signed report scan is uploaded, never a digital signature.
oracle:          per FEAT-AUD-308 AC-1/AC-2 and FEAT-AUD-309 AC-1 the 14-area scorecard and equipment list capture with N/A counting as satisfied; per FEAT-AUD-310 AC-1..AC-4 the submit hard-blocks until opening/closing meetings + attendees, all 14 scorecard rows, the ≥100-char summary and a non-empty equipment list all pass; per FEAT-AUD-110 AC-1 classification/standards are read-only once a finding exists; per FEAT-AUD-311 AC-1/AC-2 the post-submit findings list is frozen and a new insert is rejected HTTP 409; per FEAT-AUD-412 AC-1/AC-2/AC-3 the chain adds VESSEL_ACKNOWLEDGED, the action is Master-rank-bound behind AUDIT_P_017, and the SLA clocks anchor on it; per FEAT-AUD-1101 AC-1/AC-2 signatures follow the wet-ink print-sign-scan-upload model.
evidence:        []
test:            tests/journeys/journey-003.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-4 — "Crew action owner closes a Minor NC in the plain-language wizard and a dead browser costs nothing past the last advance"
origin:          PERSONA
persona:         P6 (Vessel Crew / Action Owner)
goal:            close a Minor NC through the single-question plain-language wizard with the RCA template carousel — surviving a mid-closure browser death because every advance draft-saved server-side
priority:        P0
covers:          FEAT-AUD-401, FEAT-AUD-402, FEAT-AUD-403, FEAT-AUD-405, FEAT-AUD-407, FEAT-AUD-408, FEAT-AUD-410, FEAT-AUD-1005, FEAT-AUD-1404
flows:           AFJ-4
oracle_surface:  UI
negative_states: stale_wizard_draft
data_fixtures:
steps:
  1. Crew action owner opens the assigned Minor NC from the finding detail (SCR-AUD-12) and enters the plain-language wizard (SCR-AUD-5): one question per screen, plain-English prompts, inline examples and hints; the 30-day Minor-NC deadline shows.
  2. At the RCA step the crew picks the closest match from the "Pick a starting point" carousel of seeded RCA templates filtered to the NC category; the wizard pre-fills the RCA and the crew edits it to fit — then tries to save the step with a 40-character root-cause summary to be done with it (misbehavior: submits-wizard-step-under-50-chars); the save hard-blocks with an inline error until the text reaches 50 chars.
  3. Every advance draft-saves server-side. Called away to a bunkering operation, the crew action owner walks off mid-closure with two answered screens unsaved locally (misbehavior: abandons-wizard-mid-closure-after-interruption) and the shared browser dies while he is on deck; on re-entry the wizard resumes from the last server-persisted draft rather than any locally cached copy (negative_state: stale_wizard_draft) — nothing answered before the last advance is lost, and the stale local state is discarded.
  4. Finishing on the ship's office desktop (≥1024px), the same wizard renders the 2-column layout — 60% content, 40% persistent context panel with the Part A finding, prior answers and progress — and the crew completes Parts B–D; the CAR advances toward SUBMITTED_TO_PIC on the internal chain.
oracle:          per FEAT-AUD-407 AC-1/AC-2 the wizard is single-question-per-screen with draft-save on every advance and unchanged backend fields; per FEAT-AUD-408 AC-1/AC-2 and FEAT-AUD-1005 AC-1 the carousel pre-fills from the ~25-row seeded template library and the crew edits to fit; per FEAT-AUD-403 AC-3 and FEAT-AUD-1404 AC-1/AC-3 the ≥50-char RCA minimum hard-blocks on save with an inline error; per FEAT-AUD-401 AC-1 closure follows the 7-part KSM-F-NC-001 model; per FEAT-AUD-405 AC-1 the Minor-NC default deadline is 30 days; per FEAT-AUD-402 AC-1 the CAR advances along the internal state chain; per FEAT-AUD-410 AC-1/AC-2 the desktop 2-column layout and the mobile layout render from the same component — and re-entry resumes the server-persisted draft, never the stale local copy.
evidence:        []
test:            tests/journeys/journey-004.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-5 — "Master's signature gates the transition and a 45-day backdate is refused"
origin:          PERSONA
persona:         P5 (Vessel Master)
goal:            sign NC Parts B/C under the wet-ink model with rank-bound signer resolution — the transition blocked until the scan exists, an honest 12-day backdate recorded, a 45-day backdate refused
priority:        P0
covers:          FEAT-AUD-411, FEAT-AUD-413, FEAT-AUD-1101, FEAT-AUD-1102, FEAT-AUD-1103
flows:           AFJ-5
oracle_surface:  UI
negative_states: signature_missing_blocked, backdate_beyond_window_blocked
data_fixtures:
steps:
  1. Master reviews the completed Parts B/C on the NC closure form (SCR-AUD-4) and attempts the transition toward SUBMITTED_TO_PIC without uploading the signed Part B scan; the transition hard-blocks (negative_state: signature_missing_blocked).
  2. Master prints the part, wet-ink signs, scans and uploads; rank-bound resolution identifies the current Master via the active-crew-by-rank shared-DB read; the signature event records signer, rank-at-signing and timestamps; the transition now succeeds.
  3. For a part actually signed on paper 12 days earlier, the Master backdates the claimed datetime with a ≥50-char reason; claimed-vs-actual is captured in the sign event and the PDF renders the signing Master with the previous/current-Master badge where crew changed.
  4. On another finding — a part he actually signed on paper during the last port call and never uploaded — the Master claims a 45-day backdate (misbehavior: backdates-signature-past-30d-window); it is hard-blocked (negative_state: backdate_beyond_window_blocked) — 30 days is the limit, and the honest route is a fresh signature with the real date.
oracle:          per FEAT-AUD-411 AC-1 the missing Part B/C signature scan hard-blocks leaving IN_PROGRESS; per FEAT-AUD-1101 AC-1/AC-2 the model is print, wet-ink sign, scan, upload with blank signature lines and pre-print name/date capture; per FEAT-AUD-1103 AC-1/AC-2 the signer resolves rank-bound at sign time and the UI badges previous/current Master; per FEAT-AUD-1102 AC-1/AC-2 each signature event records signer, rank-at-signing and claimed-vs-actual datetimes; per FEAT-AUD-413 AC-1/AC-2 a ≤30-day backdate with reason ≥50 chars records claimed vs actual, and beyond 30 days is a hard block.
evidence:        []
test:            tests/journeys/journey-005.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-6 — "Office Supt drafts for the vessel, picks up PIC review from the open pool, and the Lead Auditor is refused PIC on their own audit"
origin:          PERSONA
persona:         P4 (Office Supt / PIC)
goal:            draft NC Parts B+C for the vessel office-led, then take PIC review from the open pool first-come — while the audit's own Lead Auditor is denied PIC with HTTP 403
priority:        P0
covers:          FEAT-AUD-409, FEAT-AUD-701, FEAT-AUD-1203, FEAT-AUD-1204, FEAT-AUD-1207
flows:           AFJ-6
oracle_surface:  UI
negative_states: lead_auditor_pic_denied
data_fixtures:
steps:
  1. Supt opens the NC dense form (SCR-AUD-4) and clicks "Draft for Vessel", filling Parts B+C on the vessel's behalf; the CAR moves to sub-state OFFICE_DRAFTED and the Master is notified to review, edit or accept and wet-ink sign Part B — both names will render on the PDF Part B footer.
  2. After the Master signs, the CAR reaches the PIC-review pool at SUBMITTED_TO_PIC; no named PIC existed at plan time — the first office user with vessel scope + AUDIT_P_004 to click "Start PIC Review" becomes PIC of record.
  3. Before anyone picks it up, a second Office Supt — the one standing as Lead Auditor of record on this very audit — sees the CAR in the open pool and claims PIC review on it (misbehavior: claims-pic-review-while-being-lead-auditor); the action-time check rejects them HTTP 403 (negative_state: lead_auditor_pic_denied), because Lead Auditor ≠ PIC.
  4. The Supt picks it up, becomes PIC of record, and completes the review; the CAR moves PIC_REVIEW → SUBMITTED_TO_LEAD_AUDITOR through the unchanged CAR engine; the audit header keeps conductor and Lead Auditor as two distinct fields throughout.
oracle:          per FEAT-AUD-409 AC-1/AC-2/AC-3 office-led drafting sets OFFICE_DRAFTED, the Master reviews and signs Part B, and both names render on the PDF footer; per FEAT-AUD-1203 AC-1 the first in-scope AUDIT_P_004 holder to act becomes PIC of record; per FEAT-AUD-1204 AC-2 Lead Auditor ≠ PIC is enforced at action time with HTTP 403; per FEAT-AUD-701 AC-1 the CAR state machine is the unchanged engine; per FEAT-AUD-1207 AC-1 conductor and Lead Auditor stay distinct fields with their own edit locks.
evidence:        []
test:            tests/journeys/journey-006.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-7 — "Lead Auditor accepts closure, and a NOT_EFFECTIVE effectiveness review re-opens the finding"
origin:          PERSONA
persona:         P2 (Lead Auditor)
goal:            accept closure (Part F), let the Effectiveness Review schedule at +30/+90, and have a NOT_EFFECTIVE outcome re-open the finding through rework — with every action gated by the AUDIT_P_* family, closer = Lead Auditor, never the DPA
priority:        P0
covers:          FEAT-AUD-402, FEAT-AUD-404, FEAT-AUD-406, FEAT-AUD-411, FEAT-AUD-1201, FEAT-AUD-1202
flows:           AFJ-7
oracle_surface:  UI
negative_states: effrev_not_effective_reopen, signature_missing_blocked
data_fixtures:
steps:
  1. Lead Auditor — holding AUDIT_P_002/003/004 per the role mapping, gates from the audit-specific AUDIT_P_* family — opens the CAR at SUBMITTED_TO_LEAD_AUDITOR on the NC closure form (SCR-AUD-4), records certificates_at_risk = SMC, and accepts closure Part F. Working the closure queue at speed, he pushes the CAR to LEAD_AUDITOR_CLOSED before printing and uploading his wet-ink-signed Part F scan (misbehavior: closes-nc-without-required-signature-scan); the transition hard-blocks (negative_state: signature_missing_blocked). With the signed Part F scan uploaded, the CAR moves to LEAD_AUDITOR_CLOSED.
  2. The Effectiveness Review schedules automatically: due T+30, expiry T+90; the NC_EFFECTIVENESS_REVIEW_DUE notification fires at T+30 on the Lead Auditor's task list.
  3. At the review the Lead Auditor records outcome NOT_EFFECTIVE; the finding re-opens via REWORK_REQUESTED (negative_state: effrev_not_effective_reopen) and returns to the vessel for rework — the DPA is at no point the closer.
  4. After rework the Lead Auditor accepts Part F again and completes Part G verification; the CAR runs LEAD_AUDITOR_CLOSED → EFFECTIVENESS_REVIEWED → AUDITOR_VERIFIED with the full state history visible.
oracle:          per FEAT-AUD-411 AC-1 the Lead Auditor cannot reach LEAD_AUDITOR_CLOSED without the Part F signature scan — the signature-gated transition hard-blocks the unsigned close attempt; per FEAT-AUD-402 AC-1/AC-2 the internal chain runs to LEAD_AUDITOR_CLOSED then EFFECTIVENESS_REVIEWED → AUDITOR_VERIFIED with the Lead Auditor of record (not the DPA) as closer; per FEAT-AUD-1201 AC-1 and FEAT-AUD-1202 AC-1 the actions gate on the AUDIT_P_* family per the fixed role mapping; per FEAT-AUD-404 AC-1 certificates_at_risk multi-selects from the cert enum; per FEAT-AUD-406 AC-1/AC-2/AC-4 the EffRev schedules due +30d / expiry +90d, notifies at T+30, and a NOT_EFFECTIVE outcome re-opens the finding via REWORK_REQUESTED.
evidence:        []
test:            tests/journeys/journey-007.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-8 — "Master closes an Observation terminal at his signature, and a dropped satellite link denies the action instead of faking an offline save"
origin:          PERSONA
persona:         P5 (Vessel Master)
goal:            close an Observation through the 3-question wizard, terminal at the Master's closure — and when the satellite link drops mid-sign, the action is denied outright because the module is online-only, with no offline save or sync (primary actor = P5, whose signature is the terminal act; P6 (Vessel Crew / Action Owner) works the wizard in steps 1–2)
priority:        P1
covers:          FEAT-AUD-501, FEAT-AUD-502, FEAT-AUD-503, FEAT-AUD-1102, FEAT-AUD-1103, FEAT-AUD-1406
flows:           AFJ-8
oracle_surface:  UI
negative_states: connection_lost_action_blocked
data_fixtures:
steps:
  1. Master opens the Observation from the finding detail (SCR-AUD-12) into the observation closure screen (SCR-AUD-6); the P6 crew action owner works the 3-question wizard (immediate action, root cause, corrective action + evidence) with the same adaptive layout as the NC wizard.
  2. Crew completes Part B responses; each advance draft-saves server-side as in the NC flow.
  3. Mid-close the satellite link drops and the Master's sign/submit action is denied with no offline queue and no local persistence beyond the last server-saved advance (negative_state: connection_lost_action_blocked) — the module is online-only by decision, so connection loss is action denial, never a sync state.
  4. Link restored, the Master signs Part B at the shared ship's-office PC without logging the crew action owner out first — resuming whatever session was left open on it rather than authenticating as himself (misbehavior: signs-on-shared-browser-after-session-lock). The signature binds to the authenticated account and to the Master rank, not to whoever is at the keyboard: the signer is resolved rank-bound at sign time from the active-crew-by-rank lookup, and the sign event records signer, rank-at-signing and timestamps — so a signature made from the wrong session is attributable, not anonymous. The Observation reaches MASTER_CLOSED — terminal; the later DPA Part C review and auditor Part D verification are recorded as timestamps/remarks only and change no state.
oracle:          per FEAT-AUD-501 AC-1/AC-2 the closure follows the 4-part KSM-F-OBS-001 model with Parts C/D audit-trail only; per FEAT-AUD-502 AC-1/AC-2 the state machine runs NOT_STARTED → IN_PROGRESS → SUBMITTED → MASTER_CLOSED (terminal) and C/D gate nothing; per FEAT-AUD-503 AC-1 the 3-question crew wizard + adaptive layout apply; per FEAT-AUD-1103 AC-1 the Master signature binds to rank, not person — the active-crew-by-rank lookup resolves the signer at sign time — and per FEAT-AUD-1102 AC-1/AC-2 the signature event records signer_user_id, signed_at and rank-at-signing, so the shared-browser signature is traceable to the account that made it; per FEAT-AUD-1406 AC-1 the module is online-only (sync columns present but unused, no offline shell) — the dropped link denies the sign action rather than queuing an offline write.
evidence:        []
test:            tests/journeys/journey-008.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-9 — "SEQ Manager rescues an overdue plan through OPM F 713, and a date beyond window_end + 3 months is refused"
origin:          PERSONA
persona:         P1 (SEQ Manager / DPA)
goal:            take an overdue plan through the OPM F 713 extension — reason and date validated, DPA approval auto-numbered, Flag notification recorded — then cancel a stale plan and watch the register re-plan itself
priority:        P1
covers:          FEAT-AUD-203, FEAT-AUD-204, FEAT-AUD-205, FEAT-AUD-206, FEAT-AUD-1404
flows:           AFJ-9
oracle_surface:  UI
negative_states: extension_beyond_window_rejected
data_fixtures:
steps:
  1. The plan entry (SCR-AUD-7) sits at OVERDUE with the T-0 dashboard banner; SEQ Manager opens "Request Audit Window Extension" (OPM F 713); a 40-char reason_for_delay hard-blocks with an inline error until it reaches 50 chars, and justification files attach.
  2. SEQ Manager first proposes a new target date 4 months past window_end; the save is rejected (negative_state: extension_beyond_window_rejected) — proposed_new_target_date must be ≤ window_end + 3 months.
  3. With a compliant date the plan moves to EXTENSION_REQUESTED; the DPA approves it straight from the queue without opening the reason_for_delay text or the attached justification files (misbehavior: approves-extension-without-reading-reason) — the approval still stands on the record: extended_due_date is set, the request auto-numbers OPM-F-713-YYYY-NNN, the plan goes EXTENDED and AUDIT_EXTENSION_APPROVED fires, and the ≥50-char reason plus its attachments are preserved on the F 713 record, so what was approved unread stays auditable afterwards.
  4. DPA records the Flag notification (date, ref, attachment) on the plan entry (SCR-AUD-7); the persistent critical alert clears only once it is set.
  5. On a different vessel's stale entry the DPA cancels with a ≥50-char reason and a mandatory future next_planned_date; the entry goes CANCELLED read-only, AUDIT_CANCELLED fires, and a new PLANNED entry auto-creates at next_planned_date − 90 days.
oracle:          per FEAT-AUD-203 AC-3 the T-0 OVERDUE banner shows on the register/dashboard; per FEAT-AUD-204 AC-1/AC-2/AC-3 the extension captures reason ≥50 chars, enforces proposed_new_target_date ≤ window_end + 3 months, and DPA approval sets extended_due_date with the auto-numbered OPM-F-713-{YYYY}-{NNN}; per FEAT-AUD-1404 AC-1/AC-3 the ≥50-char minimum hard-blocks on save with an inline error; per FEAT-AUD-205 AC-1/AC-2 the Flag notification fields record and the persistent alert clears only when set; per FEAT-AUD-206 AC-1/AC-2/AC-3 cancellation is DPA-only with reason + future date, leaves the entry read-only, fires AUDIT_CANCELLED, and auto-creates the next PLANNED entry at −90 days.
evidence:        []
test:            tests/journeys/journey-009.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-10 — "DPA raises an incident-triggered additional audit that never touches the routine cadence clock"
origin:          PERSONA
persona:         P1 (SEQ Manager / DPA)
goal:            create an incident-triggered additional internal audit with mandatory trigger linkage, run it on the normal forms, and see it excluded from cadence math and KPI while staying visually distinct everywhere
priority:        P1
covers:          FEAT-AUD-207, FEAT-AUD-208, FEAT-AUD-209, FEAT-AUD-312, FEAT-AUD-313, FEAT-AUD-1204
flows:           AFJ-10
oracle_surface:  UI
negative_states: additional_audit_excluded_from_cadence
data_fixtures:
steps:
  1. DPA opens the plan register (SCR-AUD-7) → "Create Additional Audit" (DPA-only): trigger_reason INCIDENT_FOLLOWUP resolves through the FK picker to the Safety incident (ref + port + date), and additional_reason is entered ≥50 chars; a Flag-letter trigger would instead demand free text plus a mandatory TRIGGER_EVIDENCE attachment.
  2. is_additional=1 is set and the audit runs the normal Flow-A forms, CAR engine and closure path — including the plan-time Lead Auditor selection, which the DPA makes in a hurry off the reactive incident, without checking the auditor's scope or standards match (misbehavior: assigns-lead-auditor-without-checking-scope-standards); the qualified-auditor picker offers only active, non-expired, scope-matching rows, so the unchecked pick still cannot land outside scope. No T-90/T-30 alert ladder is scheduled — the audit is reactive.
  3. The register shows the ADDITIONAL badge and filter chip; the F 601/F 602 previews carry the red "ADDITIONAL AUDIT — DPA AUTHORISED" banner; on the audit dashboard (SCR-AUD-11) the cadence-compliance KPI ignores this audit while the "Additional Audits This Quarter" card counts it, and the vessel's routine window/next-due dates stand unmoved (negative_state: additional_audit_excluded_from_cadence — the reactive audit never resets the routine clock).
  4. During the additional audit the conductor raises an NC with priority HIGH and flags is_fleetwide_relevance; from the NC closure record the DPA later clicks "Issue Circular" — a pre-filled Circular module entry opens and the cross-link is stored on the finding.
oracle:          per FEAT-AUD-207 AC-1/AC-2/AC-3 the additional audit carries is_additional + reason ≥50 chars, is DPA-only with no alert ladder, and is excluded from cadence math (window calc filters is_additional=0); per FEAT-AUD-207 AC-4 it then runs the same forms, CAR engine and closure path as a routine audit — which is why the plan-time Lead Auditor selection applies here at all — and per FEAT-AUD-1204 AC-1 that picker is filtered to active + non-expired + scope-matching qualified-auditor rows, so the DPA's unchecked pick cannot produce an out-of-scope Lead Auditor; per FEAT-AUD-208 AC-1/AC-2 the trigger enum + polymorphic linkage resolve via FK picker or free text + mandatory TRIGGER_EVIDENCE; per FEAT-AUD-209 AC-1/AC-2/AC-3 the red PDF banner, register badge and KPI exclusion (with the separate quarterly card) all render; per FEAT-AUD-312 AC-1 the finding priority field captures; per FEAT-AUD-313 AC-1/AC-2 the fleet-wide flag and the pre-filled Circular cross-link work from the closure record.
evidence:        []
test:            tests/journeys/journey-010.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-11 — "DPA works the operational queues: a permanently failed email and a QR-mismatched scan both get honest resolutions"
origin:          PERSONA
persona:         P1 (SEQ Manager / DPA)
goal:            resolve a FAILED_PERMANENT vessel-email notification by retry and by marked-offline, and clear the scan-validation queue where an uploaded signed scan's QR hash does not match — with the DRAFT-watermark and QR-footer guarantees visible on the PDFs
priority:        P1
covers:          FEAT-AUD-804, FEAT-AUD-806, FEAT-AUD-807, FEAT-AUD-901, FEAT-AUD-902, FEAT-AUD-903
flows:           AFJ-11
oracle_surface:  UI
negative_states: notification_delivery_failed_permanent, scan_qr_mismatch
data_fixtures:
steps:
  1. DPA opens the failed-notification widget (SCR-AUD-9): a vessel row shows status FAILED_PERMANENT with error CMS_NO_EMAIL_ON_FILE because VesselData.Email is empty (negative_state: notification_delivery_failed_permanent); the widget polls every 60 seconds.
  2. DPA clicks Manual Retry on one row — attempt count resets and the row goes QUEUED — and "Mark as Notified Offline" on another with a ≥30-char reason; every attempt and resolution is written to the delivery log (7-year retention), exportable per row for evidence packs.
  3. DPA opens the scan-validation queue (SCR-AUD-10): an uploaded signed NC scan decoded to a content-hash MISMATCH against the generated PDF version (negative_state: scan_qr_mismatch). Clearing the queue between meetings, the DPA accepts one row without ever opening the attached scan to see what actually differs (misbehavior: clears-scan-queue-item-without-opening-attachment) — the accept is still gated at AUDIT_P_018 and still demands a ≥50-char reason, and both the reason and the accepting user are written to the audit trail against the scan she did not read; she rejects another row requesting a rescan.
  4. Spot-checking the source documents, the DPA confirms the F 602 carried the diagonal grey DRAFT watermark while the audit was IN_PROGRESS and lost it on submission, and that every generated page footer carries the QR encoding the finding/audit/kind/version/hash tuple with each generation recorded.
oracle:          per FEAT-AUD-804 AC-1/AC-2 the null vessel email produces notification_delivery_log FAILED_PERMANENT surfaced in the DPA queue; per FEAT-AUD-807 AC-1..AC-4 the widget lists FAILED_PERMANENT rows, Manual Retry resets attempts to QUEUED, mark-offline demands ≥30 chars, and the poll is 60s; per FEAT-AUD-806 AC-1/AC-2 every attempt writes the 7-year delivery log with per-row PDF export; per FEAT-AUD-903 AC-1/AC-2/AC-3 the QR footer tuple and generation record exist and MISMATCH/UNREADABLE scans surface in the queue for accept-with-reason/reject under AUDIT_P_018; per FEAT-AUD-902 AC-1 the DRAFT watermark shows pre-final and is removed at submission; per FEAT-AUD-901 AC-1 the audit PDFs render from the 4-generator A4-portrait set.
evidence:        []
test:            tests/journeys/journey-011.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-12 — "Master and DPA register an external SMC audit late under override, link Certs, and a writeback conflict surfaces for ACCEPT/FORCE"
origin:          PERSONA
persona:         P5 (Vessel Master)
goal:            register a Class-conducted SMC audit post-facto past the 30-day hard cap under DPA override, capture org/auditor/report and cert linkage, run the simplified closure with certificate_impact, and resolve the Certs writeback CAS conflict from the DPA queue (primary actor = P5, who registers the audit vessel-side and signs the external NC's Part B; P1 (SEQ Manager / DPA) holds the override, close-out and queue authority)
priority:        P2
covers:          FEAT-AUD-111, FEAT-AUD-601, FEAT-AUD-602, FEAT-AUD-603, FEAT-AUD-604, FEAT-AUD-605, FEAT-AUD-606, FEAT-AUD-1102, FEAT-AUD-1103
flows:           AFJ-12
oracle_surface:  UI
negative_states: cert_writeback_conflict, late_registration_override
data_fixtures:
steps:
  1. Master registers the vessel-side external SMC audit 34 days after its completion at the external register (create at /audit/external/new, record at SCR-AUD-8); past the 30-day hard cap the registration proceeds only as a late_registration_override — P1 (DPA) override with the reason recorded (negative_state: late_registration_override); the record is created directly at status SUBMITTED with no PLANNED → IN_PROGRESS lifecycle.
  2. Registration captures the external org from the org master, org type CLASS_SOCIETY, the external lead auditor's name and credential, the mandatory external report PDF, and cert linkage through the type-ahead picker scoped to vessel + flag + cert type; staff then enter the report's NCs (is_external=1) with the same wizard, RCA templates and office-led drafting — the external auditor never logs in.
  3. Closure runs simplified on SCR-AUD-8: the Master signs the external NC's Part B from the shared ship's-office PC on a session the Chief Officer had left open, rather than authenticating as himself (misbehavior: signs-on-shared-browser-after-session-lock) — the signer is resolved rank-bound at sign time from the active-crew-by-rank lookup and the sign event records signer, rank-at-signing and timestamps, so the signature binds to the account that made it and the wrong-session signature is visible in the trail rather than silently attributed to the Master. Then Supt PIC review → AWAITING_EXTERNAL_CLOSE_OUT; the external close-out letter uploads and P1 (DPA) clicks "Confirm External Closure" → EXTERNAL_AUDITOR_CLOSED, setting the mandatory certificate_impact at close-out.
  4. The Certs writeback enqueues an outbox row; the background worker hits a CAS version conflict on the cert row and the CONFLICT surfaces in the DPA queue for ACCEPT (re-read + retry) or FORCE with reason (negative_state: cert_writeback_conflict); the close-out itself never blocked on Certs availability.
oracle:          per FEAT-AUD-111 AC-1/AC-3 the external record is created at SUBMITTED and the 7-day-soft/30-day-hard SLA admits a late registration only under DPA override with reason; per FEAT-AUD-601 AC-1..AC-3 the external foundation registers post-facto with Master vessel-side; per FEAT-AUD-602 AC-1..AC-3 org, org type, auditor name/credential and the mandatory report PDF capture; per FEAT-AUD-603 AC-1/AC-2 cert linkage uses the scoped type-ahead and Certs data is read, never recomputed; per FEAT-AUD-606 AC-1/AC-2/AC-3 findings enter is_external=1 with no auditor login and closure runs the simplified chain requiring the close-out letter + DPA confirmation with no internal Lead Auditor step; per FEAT-AUD-605 AC-1 certificate_impact is mandatory at close-out; per FEAT-AUD-604 AC-1..AC-3 the outbox drains asynchronously, close-out never blocks, and the CAS CONFLICT surfaces in the DPA queue with ACCEPT/FORCE; per FEAT-AUD-1103 AC-1 the Master's Part B signature binds to rank, not person (active-crew-by-rank resolves the signer at sign time), and per FEAT-AUD-1102 AC-1/AC-2 the sign event records signer_user_id, signed_at and rank-at-signing — so the shared-browser signature is attributable to the authenticated account rather than assumed to be the Master's.
evidence:        []
test:            tests/journeys/journey-012.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-13 — "HoD and DPA run an office-department audit, and the SEQ conflict-of-interest rejects the DPA as Lead Auditor"
origin:          PERSONA
persona:         P1 (SEQ Manager / DPA)
goal:            run an internal office-department audit — F 606 checklist, vessel scope bypassed, office recipient resolution, Slack skipped, DOC/NONE certs only — with the SEQ-department conflict-of-interest rule refusing the DPA as Lead Auditor at HTTP 422 (primary actor = P1, who registers the audit and commits the decisive CoI Lead-Auditor attempt; P7 (HoD (office)) is the auditee who signs Part B in step 4)
priority:        P0
covers:          FEAT-AUD-103, FEAT-AUD-404, FEAT-AUD-805, FEAT-AUD-1204, FEAT-AUD-1205
flows:           AFJ-13
oracle_surface:  UI
negative_states: seq_coi_blocked
data_fixtures:
steps:
  1. SEQ Manager registers an office-department internal audit at the type-branched entry (SCR-AUD-1): auditee_type OFFICE_DEPT with the mandatory department qualifier — dept SEQ — and the F 606 office checklist auto-picks; the office 9–15-month cadence governs the plan.
  2. On the plan the DPA puts herself down as Lead Auditor for the SEQ-department audit — her own department — without checking the scope rule that governs who may audit SEQ (misbehavior: assigns-lead-auditor-without-checking-scope-standards); the server rejects the save with HTTP 422 (negative_state: seq_coi_blocked) under the SEQ conflict-of-interest rule; the pre-filtered picker instead offers a cross-department HoD with qualified_for_seq=1, who is selected.
  3. Notifications for the office audit resolve to the audited department's HoD (via the HoD-assignment master) + key staff + DPA + auditor team, and skip Slack — in-system + email only; vessel-scope filtering is bypassed, so all office users with read gates see the audit.
  4. An office NC captures certificates_at_risk restricted to DOC | NONE in the UI — vessel-specific certs are hidden and a forced vessel-cert value is rejected HTTP 400; P7 (HoD (office)) signs NC Part B as the responsible officer on the same form template.
oracle:          per FEAT-AUD-103 AC-2 the OFFICE_DEPT department qualifier is mandatory; per FEAT-AUD-1204 AC-4 the SEQ CoI rule rejects Lead Auditor = DPA with HTTP 422 and the picker pre-filters to qualified_for_seq rows; per FEAT-AUD-1205 AC-2 office audits bypass vessel scope for all office users with read gates; per FEAT-AUD-805 AC-2 office-internal audits skip Slack (in-system + email only); per FEAT-AUD-404 AC-2/AC-3 office cert-at-risk restricts to DOC | NONE with HTTP 400 on vessel values.
evidence:        []
test:            tests/journeys/journey-013.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-14 — "Fleet Manager assigns an Acting HoD, and a self-assignment is forbidden"
origin:          PERSONA
persona:         P8 (Fleet Manager)
goal:            assign a time-boxed Acting HoD so office-audit notifications route correctly during leave — self-assignment forbidden, 90 days the hard maximum, auto-expiry at 00:01 ITC, resolver semantics honoured
priority:        P1
covers:          FEAT-AUD-803, FEAT-AUD-1004
flows:           AFJ-14
oracle_surface:  UI
negative_states: acting_hod_self_assign_forbidden
data_fixtures:
steps:
  1. Fleet Manager opens the Acting-HoD coverage screen (SCR-AUD-13) and assigns an Acting HoD for the TECH department with a 30-day effective range, so office-audit notifications route to the acting user while the confirmed HoD is on leave.
  2. Covering the department himself while the search for a stand-in drags on, the FM records himself as Acting HoD for his own coverage (misbehavior: tries-to-self-authorise-acting-hod); the assignment is refused (negative_state: acting_hod_self_assign_forbidden) — only FM or DPA may authorise an Acting HoD, and never for themselves.
  3. The FM then tries to cover the whole leave period in one go with a 120-day acting assignment (misbehavior: authorises-acting-hod-past-90-day-cap); it is rejected — 90 days is the maximum; the accepted 30-day assignment will auto-expire at 00:01 ITC on its end date, with the history row preserved.
  4. A subsequent office-audit notification resolves through the HoD-assignment master: the confirmed HoD wins over acting where both are active and the latest assignment within a tier wins, so the TECH notification lands on the Acting HoD only while no confirmed HoD is active.
oracle:          per FEAT-AUD-1004 AC-1/AC-2/AC-3 the assignment master carries dept/user/is_acting/effective range with confirmed-over-acting latest-wins resolution and history preserved, Acting-HoD authorisation is DPA + FM only via AUDIT_P_016 with self-acting forbidden, and the period caps at 90 days with auto-expiry at 00:01 ITC; per FEAT-AUD-803 AC-2 the office-audit notification resolves the audited department's HoD through master_hod_assignment.
evidence:        []
test:            tests/journeys/journey-014.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
