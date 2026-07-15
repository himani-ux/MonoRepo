# VIMS Certificates Module — User Guide

> **Version:** 1.0
> **Last Updated:** 2026-05-13
> **Status:** Locked — Reflects locked SSOT decisions; refine after pilot vessel onboarding.
> **Audience:** End users — Master, C/O, C/E, 2/E, DPA, FM, Marine Sup'tt, Technical Manager, Tech Sup'tt, External Auditor.

---

## 1. Quick Reference per Role

### 1.1 Master (onboard)
- **Daily:** Open `/certs/vessels/<your-vessel>` → review status pills + alerts → action overdue/expiring rows.
- **On cert renewal:** Open the cert → "Upload renewed cert" → pick PDF (file or scanner) → confirm OCR-pre-filled fields → submit. System auto-detects renewal vs revision (D-CERT-170).
- **Approving subordinate submissions:** Open notifications inbox → tap pending approval → review submitted form + PDF → Approve or Reject (with reason).
- **Sharing certs externally:** Use `/certs/share-bundle` → multi-select certs → enter recipient name → "Generate ZIP". Recipient gets manifest PDF + cert PDFs.
- **Magic-link email ack:** When you get an email alert, tap "Acknowledge" — single-use link, expires in 24h.

### 1.2 C/O / C/E / 2/E (onboard sub-officers)
- You can submit cert updates for your assigned categories (Equipment / Calibrations / Tests / Misc); Master approves.
- Class Certificates + Statutory & Flag rows: Master submits these directly (you can view but not submit).
- After submitting: status shows `pending_master_approval`; Master will approve or reject with reason.

### 1.3 DPA (Designated Person Ashore)
- **Daily:** Open `/certs` fleet dashboard → check expiring KPIs, mandatory-coverage banners, bouncing-email surface.
- **Catalog edits:** `/certs/catalog` → add / deprecate / push to fleet. All audited.
- **Onboarding new vessel:** `/certs/onboarding` → start wizard → 7 steps. Use save-as-draft between batches; takes 2–4 hours per vessel total.
- **Class status snapshot upload:** every 3 months per vessel. Open vessel → "Upload class snapshot" → select PDF → parser runs → review reconciliation panel.
- **Provisioning external auditors:** `/certs/auditor-access` → "New grant" → set scope + expiry. System emails auditor a one-time signup link.
- **Settings:** `/certs/settings` to tune alert lead times, OCR thresholds, Slack routing.

### 1.4 FM (Fleet Manager)
- Read-only across full fleet for most operations.
- Sign-off authority at onboarding step 7 (vessel goes live).
- Co-approver for anniversary recompute bulk action (D-CERT-092).
- Print: per-vessel + fleet-wide scopes both available.

### 1.5 Marine Sup'tt
- **Primary reconciliation reviewer.** When a class snapshot is uploaded for an assigned vessel, you get an in-app + Slack notification → open `/certs/reconciliation/<run_id>` → resolve mismatches.
- **Primary external auditor provisioning.** Use `/certs/auditor-access` to grant access to visiting auditors.
- Direct write on assigned vessels (via `master_RoleByVessel`).

### 1.6 Technical Manager
- Read-only on assigned vessels.
- Receives escalation notifications for cert expiries on assigned vessels (D-CERT-089).
- Per-vessel TM assignment by DPA via Vessel Profile (D-CERT-098).

### 1.7 Tech Sup'tt
- Read + write on assigned vessels.
- Co-owner of class status snapshot uploads.
- Has access to Parser Ops page (dev-only, feature-flagged) for parser diagnostics.

### 1.8 External Auditor
- You'll receive a one-time signup email with a link.
- Click → set up your session.
- Access expires automatically; no early-revoke option.
- You see vessels and certs within your granted scope; free-text reasons in audit-related fields will appear as `[REDACTED — internal note]` (internal context).
- Print outputs you generate carry an `AUDIT COPY` watermark with your name + access expiry date.
- You'll need to visit each VIMS module separately — no cross-module bundle.

---

## 2. Common Workflows

### 2.1 Renewing an expiring cert (Master)
1. Notification arrives (in-app + email): "Cert expiring in 30 days — IOPP — YC FORTITUDE".
2. Open the cert via deep-link or `/certs/vessels/<imo>` → tap the cert.
3. "Upload renewed cert" → pick PDF or scanner.
4. System OCRs the PDF → pre-fills the form.
5. Verify highlighted (low-confidence) fields; correct any blanks.
6. System detects "Renewal" (new expiry > old expiry); old PDF will be archived.
7. Tap Submit. Cert status flips to `Current` (green ●). Notification cleared.

### 2.2 Submitting a service report (C/O for an Equipment item)
1. Open `/certs/vessels/<your-vessel>` → Equipment section → find the item (e.g. SCBA annual service).
2. Tap → "Update".
3. Fill issue date, last_done_date, attach service report PDF.
4. Save as draft (or submit immediately).
5. Submission goes to Master's approval queue.
6. Master approves → cert status updates.
7. If rejected: notification arrives with reason; correct + resubmit.

### 2.3 Onboarding a new vessel (DPA)
1. `/certs/onboarding` → "New vessel onboarding".
2. **Step 1:** Pick vessel (or create new).
3. **Step 2:** Set anniversary date (one-time anchor — important per D-CERT-074), ship type, current Master, Marine Sup'tt, Technical Manager.
4. **Step 3:** Upload cert PDFs in batches of 10. After each batch:
   - System OCRs (async; you'll be notified when ready).
   - Review gap-fill UI per PDF; correct low-confidence fields.
   - Click "Commit batch" — preview, confirm.
   - Repeat until all PDFs uploaded.
5. **Step 4:** Upload class status PDF (NK / KR / BV). Parser runs. Anniversary cross-validated.
6. **Step 5:** Resolve reconciliation discrepancies in the three-panel review.
7. **Step 6:** Coverage gate. If 100%, click "Auto-enable alerts". If <100%, write override reason.
8. **Step 7:** FM signs off. Vessel goes live. Master gets welcome notification.

### 2.4 Generating a fleet-wide section print (DPA / FM)
1. `/certs/print` → Choose scope: "Per-section fleet-wide".
2. Pick section (e.g. "Statutory & Flag").
3. Generate (async; ETA shown). You'll be notified in-app + Slack when ready.
4. Download PDF + Excel companion.

### 2.5 Sharing certs with a port agent (Master)
1. `/certs/share-bundle`.
2. Multi-select the certs to share (e.g. all certs needed for upcoming PSC inspection).
3. Enter recipient name (port agent).
4. "Generate ZIP".
5. Bundle filename: `VIMS_CertBundle_<vessel>_<yyyymmdd>_<print_id>.zip`.
6. Share via your usual channel (email, etc.); recipient sees manifest + cert PDFs.

### 2.6 Acknowledging a critical alert via email (Master at sea)
1. Email arrives: "[VIMS Certs] URGENT — IOPP expires in 7 days — YC FORTITUDE".
2. Tap "Acknowledge" button in email.
3. Magic-link opens browser → verifies token → ack recorded.
4. You may still need to follow up by uploading the renewal cert when issued — ack ≠ resolution.

### 2.7 Reviewing a reconciliation run (Marine Sup'tt)
1. Notification: "Reconciliation completed — N mismatches, M unmapped".
2. Open `/certs/reconciliation/<run_id>`.
3. Tabs across the top: Matches / Mismatches / Missing-in-Catalog / etc.
4. Per row: side-by-side diff. Action: "Notify Master to update", "Mark as reviewed", "Add to ClassCodeMapping" (DPA only).
5. Master receives the notification → updates the cert from their side.

### 2.8 Decommissioning a vessel (DPA)
1. Vessel Profile → "Decommission" button.
2. Confirms 30-day soft-delete window starts (D-CERT-044).
3. During those 30 days: vessel surfaces with `pending_disposal` banner; all data still accessible.
4. After 30 days: hard-delete cron purges data; audit trail preserved.

### 2.9 Recording a flag change (DPA)
1. Vessel Profile → "Flag Change" button.
2. Enter effective date, old flag, new flag, reason (free text).
3. System auto-flags statutory certs as `invalid_due_to_reflag` (NOT deleted — audit preserved).
4. Banner shown to Master: "Pending statutory re-upload after flag change".
5. Master uploads replacement statutory certs from new flag → banner clears.

---

## 3. UI Conventions

- **Status pill colors + shapes:** Green ● = current, amber half-circles = expiring (90/30/7 day bands), red ◯ with hatch = expired. See DESIGN_SYSTEM §2 for the full palette.
- **Date format:** `dd-Mmm-yyyy` everywhere (e.g. `15-Mar-2027`).
- **Notifications:** Bell icon in platform top bar — click to see Certs entries (filter by module=certs).
- **Save-as-draft:** Available in cert renewal forms + onboarding gap-fill. Drafts auto-expire after 7 days.
- **Confirmation dialogs:** Destructive actions show confirm + reason fields. No 2FA / OTP — confirm + audit trail is the safety net.
- **Re-auth:** If session expires, a modal overlay appears asking you to re-authenticate. Form state is preserved.

---

## 4. Notification Routing (How to expect alerts)

Per D-CERT-161:

| Your role | You receive notifications via |
|-----------|-------------------------------|
| Master, C/O, C/E, 2/E (vessel-side) | In-app inbox + email (NO Slack) |
| DPA, FM, Marine Sup'tt, Technical Manager, Tech Sup'tt (office-side) | In-app inbox + Slack (NO email) |

You cannot personally tune channel preference (D-CERT-160) — DPA centrally configures Slack channel routing per vessel. If you have channel-noise feedback, raise it with DPA.

24/7 notification cadence — no quiet hours (D-CERT-157). Use device-level OS controls to mute if needed (acknowledged trade-off).

---

## 5. Special States You Might See

| State | What it means | What to do |
|-------|---------------|-----------|
| `expired_at_onboarding` | Cert was already expired when onboarding completed. Alerts suppressed. | DPA: upload renewal PDF when received, OR explicitly mark "expired in reality, awaiting renewal" to begin alerts. |
| `pdf_missing: true` | Cert exists but PDF not on file. | DPA: request copy from issuer when convenient. No active escalation. |
| `pending_first_upload` | Catalog row pushed to fleet, but vessel hasn't uploaded yet. | Master: upload the cert when received. |
| `invalid_due_to_reflag` | Statutory cert from old flag, now invalid after flag change. | Master: upload replacement from new flag. |
| `pending_supersession` | Class change in progress; old class certs being phased out. | DPA: upload new-class snapshot within 30 days. |

---

## 6. Key Compliance Notes

- **Audit trail is permanent for 5 years** (D-CERT-099); free-text reasons stay in your record.
- **Print artifacts are immutable** once generated (D-CERT-146); they remain in audit log indefinitely (subject to retention).
- **Class society is authoritative** for class-tracked certs (D-CERT-009); when reconciliation flags a mismatch, the class document wins.
- **Crew certificates** (COC, GMDSS, medicals, etc.) are NOT in this module — they live in CMS (Crew Management System), a separate platform.
- **DMLC II PDF** is here, but contains zero crew personal data — only cert metadata.

---

## 7. Getting Help

- **Build bug / data issue:** Tech Sup'tt or DPA (per the support escalation chain).
- **Process question / unclear procedure:** DPA.
- **Network / login problem:** IT helpdesk per existing platform process.
- **Cert renewal received from class but not appearing in VIMS:** Check that you uploaded via `/certs/vessels/<imo>/cert/<id>` → "Upload renewed cert" — auto-detect catches it.

---

*End of USER_GUIDE v1.0. Refine after pilot vessel onboarding feedback.*

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `USER_GUIDE.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-001 | V1 scope = vessel certs + surveys; | LOCKED |
| D-CERT-079 | Submission scope by catalog row: new field `submission_scope`. | LOCKED |
| D-CERT-081 | No 2FA / step-up reauth for high-risk operations (rollback, catalog edit, vessel decommissioning, anniversary date change, depu... | LOCKED |
| D-CERT-093 | Vessel sale: 30-day soft-delete window, then hard-delete (same path as decommissioning per D-CERT-038). | LOCKED |
| D-CERT-094 | Flag-change event: recorded by DPA in vessel profile (effective date, old flag, new flag, reason free-text). | LOCKED |
| D-CERT-104 | Vessel-data migration = iterative batch PDF ingest (no filled-Excel source): DPA uploads actual certificate PDFs in batches of ... | LOCKED |
| D-CERT-110 | Anniversary date discovery = manual DPA entry + Class Status Report cross-validation. | LOCKED |
| D-CERT-113 | Missing-PDF cert rows allowed at onboarding. | LOCKED |
| D-CERT-115 | Dry-run = preview before commit. | LOCKED |
| D-CERT-119 | Per-vessel onboarding completion = hybrid auto-enable / override. | LOCKED |
| D-CERT-120 | Per-vessel onboarding wizard sequence (7 steps, no Master acknowledgment step): (1) Vessel selection from `master_vessel` (or c... | LOCKED |
| D-CERT-121 | Already-expired certs at onboarding = quarantine state. | LOCKED |
| D-CERT-131 | Date format throughout print = `dd-Mmm-yyyy` (e.g., `15-Mar-2027`). | LOCKED |
| D-CERT-132 | Validity codes printed as legacy short forms: `A` · `Bi-A` · `5-Y` · `10-Y` · `Perm.` · `ST` · `6-Mth`. | LOCKED |
| D-CERT-135 | Status visualization = color + shape hybrid (B/W-photocopy-resilient). | LOCKED |
| D-CERT-145 | Third-party deliverable = ZIP bundle (manifest PDF + cert PDFs). | LOCKED |
| D-CERT-154 | Email-to-action = magic-link one-click ack. | LOCKED |
| D-CERT-177 | Crew certificates (COC, COP, GMDSS, medicals, STCW endorsements, vaccinations) handled by CMS (Crew Management System — a separ... | LOCKED |
| D-CERT-178 | External auditor access = per-module only (no cross-module bundle, no federated SSO). | LOCKED |
| D-CERT-194 | External auditor access provisioning = Marine Sup'tt self-service (AMENDS D-CERT-096). | LOCKED |
| D-CERT-195 | External auditor access revocation = AUTO-EXPIRE ONLY (no early revocation). | LOCKED |
