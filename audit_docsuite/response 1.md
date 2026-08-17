Checked locally against `Complete_VIMS`.

1. ORB decorator issue

Yes, the 08/14 ORB decorator fix is applied for the four named functions.

No, these four functions are not reachable without authentication:

- `get_operations`: no `AllowAny` on this function, and it is not URL-wired locally.
- `list_for_chief`: no `AllowAny` on this function, and it is not URL-wired locally.
- `get_all_crew_onboarding_history`: no `AllowAny` on this function, and it is not URL-wired locally.
- `get_vessel_id_for_current_user`: URL-wired, but protected by DRF `IsAuthenticated` and also checks session login.


2. 08/14 status items

Cross-checked against:

```text
C:\Users\himan\Desktop\VIMS_handovers\VIMS-AUDIT-HANDOVER-v5\VIMS-AUDIT-HANDOVER-v5\progress.txt
```

- `PyPDF2==3.0.1` restored: No. The progress file says this recommendation was reviewed but not applied. The active `Complete_VIMS_audit_dev` handover tree pins `pypdf==6.15.0`, and production imports were updated to match `pypdf`.
- Seven `deploy.method` closure facts closed: No. The progress file says `D-AUDRS-453` remains open, so deployment command, execution identity, credential refs, migration command, success/failure signals, and rollback command are still not closed.
- `progress.txt` current position updated to Phase 13.4: Yes. The progress file says the Phase 13.4 official KLOSS handover package is generated and linted at `tmp/handover/VIMS-AUDIT-HANDOVER-v5`.
- Phase 13.4 completed/closed: Yes, for handover structure and byte-integrity. The progress file explicitly says Phase 13.4 is closed for handover structure and byte-integrity.
- Fresh Domain 13 / quality pass for the Phase 13.4 handover package: Yes. The final Phase 13.4 quality citation is recorded as `QUALITY: PASS stamp=7cab688e67a2 tree=fe57e69e86d5`.

Important boundary:

- The Phase 13.4 pass is a handover/package quality pass, not a release, deployment, pre-ship review, DPA close, Tier-R, Step 5, or dry-crossing claim.
- Later local runtime/debug edits after that handover stamp still need their own fresh Domain 13 rerun before claiming current edited-tree quality.

3. `/audit` and `/audit/dashboard`

These routes are still missing locally.

Current local Audit routes start from `/audit/plans` and other child routes. This is a real build item, not only a documentation issue.

4. `msc_profiles` seeding

The local export evidence still points to the older 2026-02-27 export.

Current local DB rows with Audit process IDs are:

- `SEQ Manager`
- `Fleet Manager`
- `MASTER`
- `Marine Superintendent`
- `Technical Superintendent`
- `Senior Technical Superintendent`
- `admin`
- `Super Admin`

5. Per-record permission gates

The SSOT decision is already clear.

`Lead Auditor`, `Conductor`, `HoD`, and `Acting HoD` are per-audit-record roles, not `msc_profiles` rows.

Current local implementation status:

- Backend merges static `AUDIT_P_*` grants with per-record assignment grants.
- `audit_detail.lead_auditor_user_id` is used for Lead Auditor access.
- `audit_detail.conductor_user_id` is used for Conductor access.
- `master_hod_assignment` is used for HoD / Acting HoD access.
- Audit Detail frontend reads `effective_permissions` from the API for visible actions.

So the permission model is wired, but the failed journeys still need validation with deliberately assigned users on the exact test records.

6. Failed journeys 3, 5, 6, 7, and 8

These should be rerun after writing the test users directly into the matching assignment fields:

- `audit_detail.lead_auditor_user_id`
- `audit_detail.conductor_user_id`
- `master_hod_assignment`

Previous runs against arbitrary or pre-existing IDs should not be treated as proof of a permission bug.

`SCR-AUD-13` is confirmed as not yet built. The Acting HoD screen or route is absent and should be scheduled.
