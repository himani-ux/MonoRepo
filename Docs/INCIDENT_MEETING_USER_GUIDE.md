# Incident Module Meeting Guide

Use this guide to explain the Incident workflow to vessel and office users. The key message is:

> The Incident module is not just a form. It is a controlled investigation workflow. Each phase answers one question, is filled by the responsible role, and creates an auditable record for closure, PDF export, and later verification.

## 1. Simple End-to-End Story

1. Phase 1 records what happened.
2. Phase 2 classifies the incident, notifies office, and assigns ownership.
3. Phase 3 collects evidence before it is lost.
4. Phase 4 turns evidence into verified facts.
5. Phase 5 analyses why it happened.
6. Phase 6 defines what must be done to prevent recurrence.
7. Phase 7 accepts the investigation and issues the report.
8. Phase 8 verifies actions are completed and effective.
9. Phase 9 keeps the closed record, simple phase history, approvals, and exports read-only.

## 2. Role Summary

| Role | Main responsibility in Incident workflow |
| --- | --- |
| Master | Owns vessel-side incident record, evidence quality, recommendations, and sign-off where required. |
| CO / CE / 2E | Can create/report incidents as top-4 officers and assist investigation/evidence collection. |
| HOD onboard | Reviews department-related investigation content and signs department-level review where applicable. |
| DPA | Office safety authority, accepts YELLOW incidents, can send back if investigation is incomplete, oversees verification for YELLOW/RED. |
| FM | Has RED incident authority, including RED acceptance/approval and RED edit authority. |
| PIC | Closer for GREEN incidents and follow-up verifier where assigned. |
| TD / HOD shore | Mainly read/comment depending on permission; not the primary action owner in the V1 workflow. |

## 3. Phase-by-Phase Explanation

| Phase | Purpose | Who normally fills / acts | Main fields users must understand |
| --- | --- | --- | --- |
| Incident List | Find, filter, and open incident records. | Any user with Incident access. | Ref No, Vessel, Date, Type, SMC/MC/MI, Band, Phase, Closer, Updated. |
| Phase 1: Intake | Capture the first report. | Master, CO, CE, 2E. | Incident type, loss type, occurred/reported time, narrative, position, reporter details, external-party injury if any, office notified/mode. |
| Phase 2: Notifications + Resource Allocation | Convert draft to formal incident, classify severity, notify office, assign ownership. | Master, CO, CE, DPA, FM depending on workflow state. | IMO classifier, loss types, risk band, investigation depth, PIC/user owner, office/DPA/FM notification timestamps or mode. |
| Phase 3: Evidence Workspace | Collect and preserve evidence before memory/data/items are lost. | Master, CO, CE, HOD onboard, DPA, FM for RED edit. | Position evidence, people/witnesses, parts/equipment, paper/logs/certificates, electronic evidence, chain of custody, interview records, evidence matrix, deadline tasks. |
| Phase 4: Sequence / Facts | Convert raw evidence into clear facts, each linked to evidence. | Investigation team: Master, CO, CE, HOD, DPA, FM for RED edit. | Fact text, sequence number, timestamp, source evidence, confidence, contradiction, hindsight override reason. |
| Phase 5: Analysis / Causes | Identify immediate and root causes without blame bias. | Investigation team: Master, CO, CE, HOD, DPA, FM for RED edit. | Analysis tool used, M-SCAT-compatible cause code, causal layer, rationale, safeguards, People/Process/Plant answers, bias guard acknowledgements, override justifications. |
| Phase 6: Recommendations | Define corrective, preventive, and lessons-learned actions. | Master, DPA, FM for RED edit; HOD review where applicable. | Recommendation tier, theme, title, description, corrective action owner, verifier, due date, ALARP fields, residual risk. |
| Phase 7: Acceptance / Report Issued | Final authority checks the investigation is complete and issues report. | PIC for GREEN, DPA for YELLOW, FM for RED. | Preflight blockers, root-cause count, recommendation counts, ALARP complete, signature chain, PDF preview, acceptance action. |
| Phase 8: Follow-up / Effectiveness Verification | Track whether actions are completed and actually effective. | PIC for GREEN, DPA for YELLOW/RED. | Corrective action status, physical verification, verifier, due date, residual risk, effectiveness notes, deferral reason if any. |
| Phase 9: Closure / Read-only | Preserve the final record, signatures, phase history, and exports. | Read-only for authorized users; reopen only by band authority. | Closure reason, closed date/by, signature chain, simple phase history, PDF exports, auditor ZIP. |

## 4. Field Purpose by Phase

### Phase 1: Intake

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| Incident type | Select what kind of incident occurred. | Drives reporting, analytics, and required evidence. |
| Loss type 1/2/3 or Other | Select up to three loss categories. | Helps classify impact and risk band. |
| Occurred at / Reported at | Actual event time and reporting time. | Used for deadlines, evidence timers, and timeline accuracy. |
| Narrative | Clear description of what happened. Minimum detail is required. | Foundation for the entire investigation. Weak narrative creates weak analysis. |
| Position / Daily Report match | Latitude/longitude and source of position, including auto-fill if available. | Required for marine context and regulatory exports. |
| Reporter name/rank/user | Typed identity of the reporter. | Starts the signature chain and accountability trail. |
| Office notified / mode | Whether office was informed and by which channel: on-call, WhatsApp, or email. | Shows immediate communication control. |
| External-party injury | Details for pilot, shipyard, stevedore, contractor, passenger, port agent, or other party if involved. | Ensures third-party incidents are not hidden inside narrative text. |

### Phase 2: Notifications + Resource Allocation

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| IMO classifier | SMC, MC, MI, or Not Applicable. | Separates regulatory casualty classification from internal risk band. |
| Risk band | GREEN, YELLOW, or RED. | Decides investigation depth, closer role, and escalation. |
| Investigation depth | Shallow, Medium, or Deep. | Sets the expected level of evidence and analysis. |
| PIC / owner | Person responsible for follow-up or closure path. | Makes ownership visible. |
| Office/DPA/FM notification fields | When and how office authorities were notified. | Proves timely escalation. |
| Loss type confirmation | Confirm or correct Phase 1 loss categories. | Keeps classification accurate before formal submission. |

### Phase 3: Evidence Workspace

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| Position tab | Photos, sketches, location notes, deck plan references. | Shows where the event happened. |
| People tab | Witnesses, involved crew, qualification snapshot, interview links. | Captures who saw or was involved. |
| Parts tab | Damaged equipment, parts, samples, storage details. | Captures physical evidence. PMS is referenced manually. |
| Paper tab | SMS procedure, logs, voyage plan, certificates, cargo records if applicable. | Captures documentary evidence. |
| Electronic tab | VDR, ECDIS, GPS, UMS, VTS, CCTV, AIS, fire system, or justification if unavailable. | Captures time-sensitive digital evidence. |
| Chain of custody | Item description, collector, witness, storage location, current holder, handover log. | Proves evidence was controlled and not tampered with. |
| Interview record | Witness notes, questions, read-back confirmation, witness signature. | Makes witness evidence reliable and auditable. |
| Evidence matrix | Pro and con evidence for major findings. | Prevents confirmation bias. |
| Deadline tasks | VDR, ECDIS, AIS, photos, statements due dates. | Prevents time-sensitive evidence from being missed. |

### Phase 4: Sequence / Facts

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| Sequence index | Order of the fact in the event chain. | Builds a clear timeline. |
| Fact text | One factual statement, not opinion. | Keeps analysis evidence-based. |
| Fact timestamp | When the fact happened, if known. | Supports event sequencing. |
| Source evidence | Link to the evidence supporting the fact. | Every fact must be traceable. |
| Confidence | Low, Medium, or High. | Shows how strongly the team trusts the fact. |
| Contradicts fact | Link or describe contradiction if applicable. | Keeps conflicting evidence visible. |
| Hindsight override reason | Justification if post-event information is used. | Prevents hindsight bias. |

### Phase 5: Analysis / Causes

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| Analysis tool | STEP, Fact Tree, ECF, Barrier, or Change analysis. | Shows the method used. |
| M-SCAT cause code | Cause taxonomy code for the selected fact. | Standardizes causes across fleet. |
| Causal layer | Immediate or Root. | Separates direct causes from system/root causes. Legacy Intermediate rows remain readable under Root Cause but are not selected in the current flow. |
| Rationale | Why this cause was selected. | Prevents unexplained code picking. |
| Safeguard failure | Safeguard name and failure dimensions: design, installation, maintenance, operation, testing, override. | Explains which barrier failed and how. |
| People / Process / Plant | Short narrative answers for each area. | Forces balanced system thinking. |
| Human factors payload | SHELL / IMO human factor details where relevant. | Captures human and organizational contributors. |
| Bias guards | Acknowledge or justify warnings. | Prevents recency, assumption, hindsight, confirmation, and blame-fixation bias. |
| Monocausal justification | Required if only one root cause is claimed. | Discourages oversimplified conclusions. |

### Phase 6: Recommendations

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| Tier | Corrective, Preventive, or Lessons Learnt. | Separates immediate fix, recurrence prevention, and learning. |
| Theme | Training, contractor, compliance, HR, MoC, procedures, equipment, etc. | Supports fleet trend analysis. |
| Title / description | What action or lesson is required. | Makes the action understandable. |
| Rationale | Why the action is linked to the cause. | Shows action is not arbitrary. |
| Corrective action owner | Crew or office person assigned. | Creates accountability. |
| Verifier | Person who will check completion/effectiveness. | Avoids self-closure. |
| Due date | Target completion date. | Enables tracking and escalation. |
| ALARP fields | Effort, likelihood reduction, residual risk statement, attestation. | Required especially for YELLOW/RED system actions. |
| Purchase requisition link | Link action to Purchase if material support is needed. | Connects safety action to procurement execution. |

### Phase 7: Acceptance / Report Issued

| Field / section | What user should check | Why it matters |
| --- | --- | --- |
| Preflight checks | Bias guards resolved, root causes present, recommendations complete, ALARP complete, signatures present. | Prevents incomplete report issue. |
| Blockers | Any red blocker must be resolved or sent back. | Keeps closure authority accountable. |
| PDF preview | Check report output before issue. | Ensures the formal report is complete. |
| Accept & Issue Report | Final acceptance by PIC, DPA, or FM depending on risk band. | Locks the investigation into report-issued state. |

### Phase 8: Follow-up / Effectiveness Verification

| Field / section | What user should enter | Why it matters |
| --- | --- | --- |
| Corrective action status | Open, In Progress, Pending Verify, Closed, Deferred. | Shows real action progress. |
| Physical verification | Done/pending, date, verifier, notes. | Confirms work was physically checked where needed. |
| Effectiveness verification | Whether recommendation is effective, residual risk, notes. | Confirms the action solved the problem. |
| Deferral reason | Why verification or action is deferred. | Prevents silent non-closure. |
| Close Incident | Only when required actions are closed or validly deferred. | Ends the active workflow. |

### Phase 9: Closure / Read-only

| Field / section | What user should use it for | Why it matters |
| --- | --- | --- |
| Incident summary | Review final incident details. | Single source of truth after closure. |
| Signature chain | Reporter, Master, HOD, DPA, FM/PIC as applicable. | Shows who approved each stage. |
| Phase log | Phase movement history and loop-back reasons. | Audit trail of workflow decisions. |
| Field history | Before/after changes and reasons. | Audit trail of content changes. |
| PDF / MSC-MEPC.3 / Auditor ZIP | Export official records. | Supports audit, regulatory, and management review. |
| Re-open Incident | Used only by authorized closer authority when new information requires reopening. | Keeps closure controlled. |

## 5. Signature Chain to Explain in Meeting

The signature order is controlled:

1. Reporter signature: captured when Phase 1/2 is submitted.
2. Master signature: captured when recommendations are submitted from Phase 6.
3. HOD signature: captured during department-level review where applicable.
4. DPA signature: required for YELLOW acceptance.
5. FM signature: required for RED acceptance.
6. PIC signature: terminal closer for GREEN incidents.

Explain this simply: "The next person cannot sign until the earlier responsibility is complete."

## 6. Risk Band Closure Rule

| Risk band | What it means operationally | Final acceptance / closure authority |
| --- | --- | --- |
| GREEN | Lower severity, lighter investigation path. | PIC. |
| YELLOW | More serious, requires DPA ownership and stronger controls. | DPA. |
| RED | Highest seriousness, office/fleet leadership control. | FM. |

## 7. Suggested Meeting Agenda

1. Start with the workflow story: report -> evidence -> facts -> causes -> actions -> acceptance -> verification.
2. Explain role ownership using the role summary table.
3. Walk through one sample incident record phase by phase.
4. Stop at each phase and ask: "What question is this phase answering?"
5. Demonstrate required fields only first, then optional/advanced fields.
6. Explain risk band and signature chain.
7. Close with common mistakes and expectations.

## 8. Common User Mistakes to Warn About

| Mistake | Correct behavior |
| --- | --- |
| Writing a short or vague narrative. | Write enough detail that someone not onboard can understand what happened. |
| Treating Phase 3 as attachment dumping. | Each evidence item should support a fact or eliminate uncertainty. |
| Writing opinions in Phase 4 facts. | Facts must be evidence-linked statements. Analysis comes later. |
| Selecting only immediate causes in Phase 5. | At least one root cause is required before moving forward. |
| Creating weak actions in Phase 6. | Actions must link back to causes and have owners/verifiers/due dates. |
| Trying to close before verification. | Phase 8 must show actions are completed/effective or validly deferred. |
| Expecting UI to allow every user to edit every phase. | Access depends on role, risk band, phase, and process permission. |

## 9. One-Line Explanation for Each Phase

Use these during the meeting:

| Phase | One-line explanation |
| --- | --- |
| Phase 1 | "Tell us what happened and prove the scene is controlled." |
| Phase 2 | "Classify it, notify the right people, and assign ownership." |
| Phase 3 | "Collect evidence before it disappears." |
| Phase 4 | "Turn evidence into verified facts." |
| Phase 5 | "Find system causes, not just who made a mistake." |
| Phase 6 | "Decide what will be fixed and who owns it." |
| Phase 7 | "Final authority checks and issues the report." |
| Phase 8 | "Verify actions worked." |
| Phase 9 | "Keep the closed record and audit trail." |
