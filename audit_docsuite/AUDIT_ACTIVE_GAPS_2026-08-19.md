# Audit Active Gaps - 2026-08-19

## Purpose

This file lists only the Audit items that still need a decision, approved data, or formal validation. The aim is to close the remaining gaps in one clear round instead of continuing repeated back-and-forth responses.

Current local code evidence commit before this document:

```text
717aefb29eaf03d4e9708f399afa0a8f86fea086
```

## Already Resolved Locally

These items do not need to be treated as active blockers in the current local code:

1. `/audit` and `/audit/dashboard` routes are implemented locally.
2. Audit plan edit/detail UUID issue on SQL Server is fixed locally.
3. Backend APIs for Audit qualified auditors, external audit organisations, and vessel RO delegations are implemented locally.
4. ORB is not an active security blocker in the current application flow. The four previously discussed ORB functions do not have active `AllowAny` decorators in the local code. Three are not URL-registered, and the only registered one has a session login check.

Evidence files:

```text
crs/CR-148.md
crs/CR-149.md
audit_docsuite/resolution response.md
audit_docsuite/GAPS_2.md
audit_docsuite/AUDIT_RUNTIME_GAPS.md
```

## Cross-Check Against `RESOLUTION_08-19.md`

The file `C:\Users\himan\Downloads\RESOLUTION_08-19.md` was reread before finalizing this active gap list. It does not provide final solution, approval, or confirmation for the active items below.

| Active item | Is it closed by `RESOLUTION_08-19.md`? | What the resolution file actually says |
| --- | --- | --- |
| Real qualified-auditor, external-organisation, and RO-delegation data | No | It confirms developers should not invent production-looking rows and says real data remains with Prince/DPA/business owner. |
| `AUDIT_P_019` and `AUDIT_P_020` approval | No | It says `D-AUDRS-138` is still proposed and pending registration/approval. |
| `msc_profiles` mapping for the new gates | No | It accepts this as a real follow-up and says real profile rows still need the new process IDs after approval. |
| Lead Auditor selection source | No | It says the Phase 5 chain re-walk / Lead Auditor stall confirmation is not addressed. It does not confirm whether Lead Auditor is office, vessel, external, or mixed. |
| External Audit RO fallback or hard-block behavior | No | It explicitly says the fallback versus hard-block behavior for empty `vessel_audit_ro_delegation` is not addressed. |
| Acting HoD screen | No | It does not provide a confirmed route, screen behavior, or deferral decision. |
| Formal UAT rerun evidence | No | It carries forward journey/testing evidence gaps and asks for proper rerun evidence. |
| Release closure facts | No | It still lists deploy-method facts, progress/current-position, quality pass, and related release items as owed. |
| PRD wording correction | No | It says the PRD correction belongs to the document owner/reissue process; it does not provide the corrected issued wording. |
| ORB evidence acceptance | Not fully | It does not accept the `msc_profiles` explanation alone. It asks for direct code-level decorator confirmation and unauthenticated-request evidence. Current local code evidence is now recorded separately in `audit_docsuite/resolution response.md`, but this still needs reviewer acceptance. |

## Active Gap 1 - Real Audit Master Data Is Missing

### Current Problem

The required master tables exist, and backend APIs now exist, but the local data is not usable for real workflow testing:

```text
master_audit_qualified_auditor
master_external_audit_org
vessel_audit_ro_delegation
```

Current local observation:

```text
master_audit_qualified_auditor: only demo/inactive data
master_external_audit_org: only demo/inactive data
vessel_audit_ro_delegation: only demo/no usable operational data
```

### Why This Blocks Closure

Lead Auditor dropdowns, External Audit organisation dropdowns, and vessel RO delegation logic cannot be properly verified with demo or inactive rows.

### Exact Input Needed

Please provide or approve the real operational data source for:

1. Qualified auditors
2. External audit organisations
3. Vessel-wise RO delegation

If this data must be seeded by development, please confirm the official source file/table and whether inactive/demo rows should be excluded.

## Active Gap 2 - Permission IDs Need Formal Approval And Profile Configuration

### Current Problem

The backend now supports these Audit process IDs:

```text
AUDIT_P_019 - External audit organisation master access
AUDIT_P_020 - Vessel RO delegation master access
```

But code support alone does not update production `msc_profiles`.

### Why This Blocks Closure

Users will not receive these permissions in deployed environments until the IDs are approved and added to the intended production profile rows.

### Exact Input Needed

Please confirm:

1. Are `AUDIT_P_019` and `AUDIT_P_020` approved as final permission IDs?
2. Which `msc_profiles.profile_name` rows should receive each permission?
3. Should SEQ Manager receive both `AUDIT_P_019` and `AUDIT_P_020`?
4. Should admin and Super Admin receive both permissions?

No production permission update should be run until this mapping is confirmed.

## Active Gap 3 - Lead Auditor Selection Source Is Not Fully Defined

### Current Problem

Audit registration should not ask users to type UUIDs or free-text auditor identities. It should use dropdowns.

The current direction is:

```text
User identity should come from existing common user/crew master tables.
Qualified-auditor eligibility should come from master_audit_qualified_auditor.
```

But usable qualified-auditor data is not present yet.

### Why This Blocks Closure

Without confirmed source data, the Lead Auditor dropdown can either be empty or show incorrect users.

### Exact Input Needed

Please confirm the intended Lead Auditor source:

1. Can Lead Auditor be an office user?
2. Can Lead Auditor be a vessel user?
3. Can Lead Auditor be an external person?
4. If office/vessel users are allowed, which existing master tables should be used as the identity source?
5. Should `master_audit_qualified_auditor` only store qualification/eligibility details, linked to the real user identity?
6. Did the Phase 5 chain re-walk stall at Lead Auditor selection because `master_audit_qualified_auditor` has no active usable rows?

## Active Gap 4 - External Audit Registration Needs Organisation And RO Rules

### Current Problem

External Audit registration currently needs an external organisation value, but real external organisation data and real vessel RO delegation data are missing.

The code does not yet automatically resolve the external organisation from vessel RO delegation.

### Why This Blocks Closure

External Audit registration and External Audit close-out cannot be fully tested without a real external audit organisation and a valid external audit detail record.

### Exact Input Needed

Please confirm:

1. Should the user manually select the External Audit Organisation from a dropdown?
2. Or should the system auto-resolve it from `vessel_audit_ro_delegation` based on vessel and standard?
3. If auto-resolution is required, which fields define the match: vessel, standard, RO, effective date, or something else?
4. If no matching `vessel_audit_ro_delegation` row exists, should registration hard-block or fall back to manual selection?
5. Please provide one valid External Audit test record/data set for UAT.

## Active Gap 5 - Acting HoD Screen Is Still Not Confirmed

### Current Problem

Acting HoD assignment data exists locally, but no confirmed frontend route or screen exists for the Acting HoD journey.

### Why This Blocks Closure

`JOURNEY-14` cannot be passed until the route/screen is confirmed or built.

### Exact Input Needed

Please confirm one of the following:

1. Acting HoD screen is required now, and the expected route/screen behavior should be implemented.
2. Acting HoD is out of current scope, and `JOURNEY-14` should be deferred.

If it is required, please confirm the expected route name, who can access it, and what actions the user must perform on that screen.

## Active Gap 6 - UAT Journey Evidence Still Needs A Proper Rerun

### Current Problem

Formal UAT closure needs rerun evidence in the agreed format:

```text
UAT_REPORT_<date>.md
```

The report must include:

```text
commit SHA
account/persona used
route tested
record IDs
command executed
raw output/log
screenshot or artifact hash for manual steps
```

### Why This Blocks Closure

Earlier journey results cannot be treated as final because some were blocked by runtime setup, missing test data, or missing screen confirmation.

### Exact Input Needed

Please provide or confirm:

1. Credentials through the approved secret channel.
2. Test records in the required workflow states.
3. A usable External Audit record ID.
4. Acting HoD route status.
5. Approval to rerun these journeys after the above inputs are ready:

```text
JOURNEY-1
JOURNEY-2
JOURNEY-3
JOURNEY-4
JOURNEY-5
JOURNEY-6
JOURNEY-7
JOURNEY-8
JOURNEY-9
JOURNEY-10
JOURNEY-11
JOURNEY-12
JOURNEY-13
JOURNEY-14
```

## Active Gap 7 - Release Closure Items Are Still Pending

### Current Problem

The code can be reviewed locally, but release-level closure still needs operations/release evidence.

### Exact Input Needed

Please confirm or provide:

1. Fresh full quality/restamp instruction or owner.
2. The seven deploy-method closure facts:
   - deployment command or procedure
   - execution environment
   - execution identity
   - credential or secret references
   - migration command
   - success signal
   - rollback command
3. Credential rotation confirmation with date.

## Active Gap 8 - PRD / Documentation Correction Needs Owner Decision

### Current Problem

The resolution notes say some PRD wording claims operational Audit master tables are seeded, but current local evidence shows the tables do not contain usable real data.

### Why This Blocks Closure

If documentation says the data is seeded but the actual system has no usable rows, reviewers will keep seeing a mismatch.

### Exact Input Needed

Please confirm who should update/reissue the PRD wording:

1. Senior/design owner
2. Development team after written approval
3. Deferred until real master data is provided

## Summary Of Required Senior Decisions

To close the current Audit gap loop, please confirm these items directly:

1. Real data source for qualified auditors, external audit organisations, and vessel RO delegations.
2. Approval and profile mapping for `AUDIT_P_019` and `AUDIT_P_020`.
3. Lead Auditor source rule: office user, vessel user, external person, or mixed.
4. External Audit organisation rule: manual dropdown or auto-resolve from vessel RO delegation.
5. Acting HoD route: build now or defer.
6. UAT rerun inputs: credentials through secret channel, proper test records, and External Audit test record.
7. Release closure inputs: fresh restamp, deploy facts, and credential rotation date.
8. PRD correction owner.

## Non-Blocker Clarification

ORB should not be treated as an active Audit blocker unless a currently registered public route proves unauthenticated access. Current local code check shows the earlier ORB `AllowAny` concern is not active in the configured application flow.
