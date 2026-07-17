# VIMS Certificates Module — Validation Rules

> **Version:** 1.0
> **Last Updated:** 2026-05-13
> **Status:** Locked
> **Source:** D-CERT-105, D-CERT-106, D-CERT-116, D-CERT-117, D-CERT-118, D-CERT-119, D-CERT-143, D-CERT-159, D-CERT-168, D-CERT-174, D-CERT-179, D-CERT-180.

---

## 1. OCR Confidence Thresholds

| Context | Threshold | Behavior | D-CERT |
|---------|-----------|----------|--------|
| Office migration upload | ≥ 80% | Auto-accept; hidden from gap-fill UI | D-CERT-106 |
| Office migration upload | 60–80% | Show in gap-fill with OCR best guess + low-confidence highlight | D-CERT-106 |
| Office migration upload | < 60% | Show blank with "Please enter manually" prompt | D-CERT-106 |
| Vessel-side cert upload (Master) | ≥ 85% | Auto-accept | D-CERT-168 |
| Vessel-side cert upload | 60–85% | Gap-fill | D-CERT-168 |
| Vessel-side cert upload | < 60% | Manual | D-CERT-168 |
| Whole-doc unprocessable | (any) | Full-form manual entry; orange banner | D-CERT-106 |
| Reconciliation auto-inclusion (class snapshot per-field) | ≥ 95% | Auto-include in reconciliation buckets | D-CERT-053 |
| Reconciliation auto-inclusion | < 95% | `flagged_low_confidence[]` for Marine Sup'tt review | D-CERT-053 |

All thresholds tunable post-launch via Settings (FEAT-CERT-OCR-012); defaults shipped in `vims_certs_alert_config`.

---

## 2. Field-Level Validation (D-CERT-105)

### 2.1 Required fields (block commit)
- Certificate type/name (must map to existing catalog row OR trigger inline-promotion D-CERT-122)
- Issuing authority
- Vessel name (auto-filled; immutable in vessel-locked context per D-CERT-112)
- IMO number (auto-filled; OCR mismatch surfaces warning, NOT auto-reroute)
- Issue date (must be ≤ today, valid date)
- Expiry date (unless `validity_type='permanent'`)
- Certificate number (with explicit bypass — see 2.2)
- Place of issue

### 2.2 Cert-number bypass (D-CERT-105)
- Checkbox: "This cert does not carry a number"
- When checked: reason field appears, required, min 10 chars max 512.
- DB: `certificate_number = NULL`, audit log entry includes `bypass_reason`.

### 2.3 Optional fields (do not block)
- Last annual / intermediate survey dates (conditional on cert hierarchy)
- Conditions / restrictions / endorsements (verbatim free text)
- Issuing officer signature / name

### 2.4 Date validation
- All dates parse as ISO 8601 (`YYYY-MM-DD`) at API layer regardless of display format (`dd-Mmm-yyyy` per D-CERT-131).
- `issue_date` ≤ today (D-CERT-116 blocks future issue dates).
- `expiry_date` > `issue_date` (when both set).
- `anniversary_date` immutable post-onboarding except via explicit DPA edit with confirm + audit reason (D-CERT-074).

---

## 3. Commit-Time Validation Gates (D-CERT-116)

When DPA clicks "Commit batch" in onboarding gap-fill:

### 3.1 BLOCKS commit (rejected outright)
| Condition | Reason |
|-----------|--------|
| Any required field missing on any row | Per §2.1 |
| Cert-number bypass without reason | Per §2.2 |
| OCR'd IMO unresolved against any KSM vessel | Cannot route PDF |
| Validity type undetermined (`unknown`) | Compliance ambiguity |
| Cert issue date in the future | Data quality |
| Cert duplicate within same batch (same `cert_number` on two PDFs) | Likely user error |

### 3.2 WARNS but allows (commit proceeds with warning logged)
| Condition | Reason |
|-----------|--------|
| `pdf_missing: true` row | Legitimate per D-CERT-113 |
| Issuer type undetermined | Catalog refinement can happen later |
| Cert expiry date in past | Already-expired at onboarding → quarantine per D-CERT-121 |
| Two cert rows for same `catalog_id` on same vessel | Legitimate (dispensation + original, STC + parent, etc.) |

Block + warn lists rendered in `ValidationBlocksDialog` / `ValidationWarnsDialog` before final commit; warnings require DPA acknowledgment checkbox.

---

## 4. Re-Import Idempotency (D-CERT-118)

- Every uploaded PDF hashed (SHA-256) at upload.
- If same hash already attached to a vessel's cert row → silently skip re-attach; log "already imported" in batch report.
- If a PDF with same `cert_number` on same vessel but DIFFERENT content hash → modal: "A cert with this number already exists. Does this PDF supersede it?"
  - Yes → old PDF archived `superseded_at=now()`; new PDF attached as current; `supersedes_id` set on the new TrackedItem version.
  - No → DPA returns to gap-fill, corrects `certificate_number` field, retries.

---

## 5. Notification Idempotency (D-CERT-174)

- Every notification carries idempotency key `(cert_row_id, cadence, sent_date)`.
- **App-level dedup:** Check `vims_certs_notification_meta` for existing key within 24h before dispatching.
- **DB-level unique constraint:** `vims_certs_notification_meta.idempotency_key` UNIQUE; duplicate insert rejected silently.

Both layers active simultaneously. Protects against server restart, scheduled job re-run, DB recovery scenarios.

---

## 6. Mandatory-Coverage Gate (D-CERT-119)

At onboarding wizard step 6:

```
coverage_pct = (count of TrackedItems for vessel where catalog.mandatory_for_all_vessels=true
                AND status NOT IN ('pending_first_upload'))
               / (count of catalog rows where mandatory_for_all_vessels=true
                  AND vessel's ship_type ∈ catalog.applicable_ship_types)
               × 100
```

| Outcome | Behavior |
|---------|----------|
| coverage_pct == 100 | "Auto-enable alerts" button visible; FM sign-off (step 7) enabled |
| coverage_pct < 100 | List missing certs; require DPA written override reason (textarea min 20 chars); override audit-logged; visible on vessel dashboard banner until coverage reaches 100% |

---

## 7. Approval State-Transition Guards (D-CERT-076, D-CERT-079, D-CERT-165, D-CERT-080)

| From | To | Allowed actor | Notes |
|------|----|---------------|------|
| (none) | draft | Master / CO / CE / 2E / Office direct | New row |
| draft | pending_master_approval | Submitter (CO / CE / 2E) | `submission_scope = all_ranks_with_approval` rows |
| draft | approved | Submitter Master direct / Office direct | Master self-submit = NO approval gate (D-CERT-165/D-CERT-199); Office direct write skips approval (D-CERT-018) |
| pending_master_approval | approved | Master (own vessel) | Audit captures both submitter and approver |
| pending_master_approval | rejected | Master | `rejection_reason` required (min 10 chars); increments `rejection_count` |
| rejected | draft | Original submitter | "Resubmit" button |
| rejected | (auto-flag FM) | system | When `rejection_count >= 3` (D-CERT-080) — does NOT block further resubmission |
| draft (any) | (deleted) | system | Nightly cron when `draft_expires_at <= now()` (D-CERT-076) |
| approved | (no transition) | — | Terminal except via new version supersession |

All active Certs catalog rows now use `submission_scope = all_ranks_with_approval` (D-CERT-199). CO / CE / 2E uploads enter `pending_master_approval`; Master and office direct uploads are approved directly. Other onboard ranks remain read-only for uploads unless the backend sub-officer recognition list is expanded.

Catalog add/edit rejects submitted `submission_scope = master_only`; DPA/System Admin catalog writes must save `all_ranks_with_approval` so newly added rows do not drift from D-CERT-199.

---

## 8. RBAC Guards (server-enforced)

Every endpoint checks both:
1. **Form ID** (`CERT_F_*`) — does the user have access to this Certs sub-feature at all?
2. **Process ID** (`CERT_P_*`) — does the user have permission for this specific action?

Plus **scope filter**:
- DPA + FM (global): `has_global_vessel_access = true` → no vessel filter.
- Sup'tts: scope = `master_RoleByVessel` for current user.
- Master / sub-officers: scope = `vessel.master_user_id = current_user` OR vessel-rank role assignments.
- Other onboard officers: read-only own-vessel.
- External Auditor: scope = `vims_certs_external_auditor_access.scope_json` (vessel IDs + section codes + optional cert IDs).

`apps/certs/permissions/certs_perms.py` exposes a single `has_certs_perm(user, form_id, process_id, vessel=None)` helper used by every view.

---

## 9. Audit Log Integrity (D-CERT-179)

- DB-level: `vims_app` role has `INSERT, SELECT` only on `vims_certs_audit_log` and on `master_notification` rows where `module='certs'`.
- App-level: `AuditLog` model has no `update()` or `delete()` method; only `record()` classmethod accepts writes.
- Migration runner authenticates as `vims_admin` (full GRANTs) — used only for schema changes, never runtime.

Belt-and-suspenders; both layers active.

---

## 10. Audit Log Read Redaction (D-CERT-180)

| Viewer | Visibility |
|--------|-----------|
| DPA, FM | Full content for all events (full fleet) |
| Marine Sup'tt, Tech Sup'tt, Technical Manager | Full content within `master_RoleByVessel` scope |
| External Auditor | Auditor portal has NO audit-log screen (D-CERT-178). Free-text reason fields in any other surface (rejection_reason, extension_reason, override_reason) → `[REDACTED — internal note]` |

Server-side enforcement via `serializers/auditor.py` — never relied on client-side hiding.

---

## 11. Retention Windows

| Data | Retention | D-CERT |
|------|-----------|--------|
| `vims_certs_audit_log` | 5 years rolling; hot 2y + cold 3y tiering | D-CERT-099, D-CERT-183 |
| `vims_certs_notification_meta` metadata | 5 years (matches audit) | D-CERT-175 |
| `vims_certs_notification_meta.body_content` | 1 year (then NULL'd) | D-CERT-175 |
| `vims_certs_pdf_blob` (Class + Statutory) | Old versions deleted immediately on new upload | D-CERT-020 |
| `vims_certs_pdf_blob` (other categories) | Old versions retained 18 months then auto-purge | D-CERT-020 |
| `vims_certs_class_status_snapshot` PDF | Retained indefinitely | D-CERT-020 |
| `vims_certs_class_status_snapshot` PDF (hot vs cold) | Hot 5y, then cold archive (Glacier-equivalent, 12h retrieval) | D-CERT-060 |
| CSR amendments (`retain_all_versions: true`) | All versions retained indefinitely | D-CERT-039 |
| Audit always preserved | Even when PDF purged, audit row remains | D-CERT-020 |

Daily retention sweeper job: `apps/certs/jobs/retention_sweeper.py`:
1. Scans `vims_certs_pdf_blob` where `scheduled_delete_at <= now()` AND `is_active=false` AND `dpa_retention_override_until IS NULL OR dpa_retention_override_until <= now()`.
2. Soft-delete (move to delete-pending bucket); set `delete_pending_since = now()`.
3. Next day: any row with `delete_pending_since <= now() - 7 days` → hard-delete (irreversible).

Audit-log archiver job: `apps/certs/jobs/audit_archiver.py` nightly:
- Hot → cold transition: rows where `timestamp_utc <= now() - 2y` AND `retention_tier='hot'` → move blob/data to cold; set `retention_tier='cold'`, `archived_at=now()`.
- Cold → purged: rows where `timestamp_utc <= now() - 5y` → hard-delete; itself audited per D-CERT-091.

---

## 12. Soft-Throttle Print Activity (D-CERT-143)

- Per-user count of print actions in trailing 60 min.
- Threshold: 10 prints/hour.
- Above threshold: audit log entry tagged `high_volume_print_activity` (no hard block).
- FM dashboard surfaces aggregate "users above threshold" count for governance review.

Hard block deliberately excluded — legitimate burst scenarios (fleet audit prep) not penalized.

---

## 13. Email Delivery + Bouncing (D-CERT-159)

- Per-email send: 3 retries with exponential backoff (1 min → 5 min → 30 min).
- 3 retries exhausted → user flagged `delivery_status='bouncing'` in `master_user`.
- Bouncing-user count surfaced on DPA dashboard ("N users have failing email delivery — review").
- If cert severity ∈ {expiring_7d, expired} (critical) AND user is bouncing → auto-fall-back to Slack DM via shared relay.
- All retry attempts + final outcome logged in `vims_certs_notification_meta.delivery_status_json`.

---

## 14. Concurrent Upload Lock (D-CERT-056)

- Class snapshot upload acquires advisory lock on `(vessel_id, snapshot_upload_in_progress)`.
- Second concurrent upload for same vessel → user choice: "Wait for current upload to finish" OR "Override (cancel current)".
- Lock auto-released after 5-min timeout (in case parser hangs).

NOT applied to per-cert PDF uploads (multiple in flight per vessel are fine).

---

## 15. Parser Hard Timeout (D-CERT-059)

- Per class-snapshot parse: 5-min hard timeout.
- Auto-retry 2x with 30s + 90s backoff.
- Final failure → `parse_status='failed'`; raw PDF retained; admin notification fires.

---

## 16. Bulk Action Caps (D-CERT-092)

- Catalog bulk soft-delete: max 50 rows per batch. Confirm dialog requires reason (min 10 chars).
- Anniversary recompute: requires FM 2nd-approver + preview modal (affected vessel count + cert count + sample preview) before commit.
- Catalog push to fleet: auto-creates `pending_first_upload` rows; no opt-in friction; audit entry per affected vessel.

All audited per D-CERT-091.

---

## 17. External Auditor Provisioning (D-CERT-194 → D-CERT-197)

- Marine Sup'tt or DPA can create grant.
- Required fields: auditor name, auditor email, scope (vessels + sections + optional cert IDs), expiry.
- Default expiry: 7 days. Max expiry: 30 days (DPA-extendable per D-CERT-096).
- One-time signup token: SHA-256-hashed in DB; raw token sent in signup email; single-use.
- Auto-expire only; no early-revoke button (D-CERT-195). To effectively revoke: edit `expiry_at` to a past timestamp.
- No per-action audit logging during auditor session (D-CERT-196); only `last_accessed_at` grant-level signal.
- No system-side attestation tooling (D-CERT-197); auditor produces own report.

---

## 18. WCAG AA

- All interactive elements: keyboard-accessible, visible focus ring, 4.5:1 contrast for text.
- Status indicators: shape + color + text (not color alone) per D-CERT-135.
- ARIA labels for icon-only buttons.
- Focus trap inside modals.

Tested per release via automated axe-core run + manual screen-reader walkthrough of primary user journeys.

---

## 19. Cross-Module Boundary Enforcement (D-CERT-176)

Static analysis check in CI: any `import` from `apps.<sibling>.*` in `apps/certs/*` blocks the build. Same for any `requests.get('/api/<sibling>/...')` literal.

Shared platform consumption (`master_*`, `master_notification`, `email_dispatcher`, Slack relay, S3 blob, company-logo endpoint, `wrh_ship_time_config`, `msc_profiles`) is allowed and listed in `apps/certs/permissions/allowed_shared_surfaces.py`.

---

*End of VALIDATION_RULES v1.0.*

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `VALIDATION_RULES.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-006 | Class snapshot upload cadence: every 3 months, alert 1 month in advance. | LOCKED |
| D-CERT-021 | Migration: per-vessel onboarding wizard (catalog seed → upload S633 + class PDF + bulk PDFs → review with Master → vessel live). | LOCKED |
| D-CERT-090 | Office hierarchy = inherit PSC Inspection RBAC pattern (`VIMS DOCS/BACKEND_STRUCTURE.md §11`). | LOCKED |
| D-CERT-115 | Dry-run = preview before commit. | LOCKED |
| D-CERT-161 | Channel routing = per-side split, clean separation: Vessel-side users (Master, C/O, C/E, 2/E) receive notifications on in-app (... | LOCKED |
| D-CERT-167 | Master upload UX flow: (1) Master clicks "Upload renewed cert" on cert card; | LOCKED |
