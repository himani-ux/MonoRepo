# VIMS Certificates Module — Security, Privacy & Compliance

> **Version:** 1.1
> **Last Updated:** 2026-06-12 (v1.1 — all 13 B-SEC blockers resolved same day; v1.0 created earlier same day)
> **Status:** 🟢 LOCKED — Ready for Build. All B-SEC-01 … B-SEC-13 RESOLVED 2026-06-12 (closure session, Prince/DPA + platform-fact sweep of deployed Safety/Reporting docs). `BLOCKERS.md` retained as the resolution audit trail.
> **Source:** `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16 (D-CERT-\* decisions), `../ssot_auth_specific.md`, `BACKEND_STRUCTURE.md`, `TECH_STACK.md`.
> **Why this doc exists:** KLOSS Step 2 framework revision (2026-05-27) added SECURITY.md to the canonical set (interrogation Domain 9). This doc consolidates security material that previously lived scattered across the SSOT and BACKEND_STRUCTURE, and marks BLOCKED what was never interrogated. **No defaults were invented** — every un-sourced topic is BLOCKED, not filled.
> **Enforcement:** the controls below are LAW for the build agent, verified via the `CLAUDE.md` Completion Checklist.

---

## 1. Platform & Scope

- **Platform:** WEB (responsive browser app inside the VIMS monorepo). No native/mobile codebase; bridge tablet uses the same web app.
- **Module status:** pre-production (not yet built; Phase 0 pending).
- **Auth perimeter:** inherited platform JWT chain (`msc_profiles` → `form_ids`/`process_ids`). **No new auth path, no new token class, no MFA override (D-AUDRS-276).**

---

## 2. Regulated Data Classes Touched

| # | Data class | In scope? | Source |
|---|-----------|-----------|--------|
| 1 | Vessel statutory/class/flag certificates (operational documents, not personal data) | YES — core domain | SSOT §1–2, D-CERT-001, D-CERT-014 |
| 2 | Vessel identity & config (IMO, name, class society, flag, anniversary date) | YES | BACKEND_STRUCTURE §3.4, §3.16 |
| 3 | **Internal KSM employee data ONLY** — VIMS user accounts (~30–50 employees: names, emails, roles), audit-log actor names, print artifact identities, approval/rejection actor logs, notification recipient logs | YES — the module's entire personal-data footprint | **D-CERT-184** |
| 4 | **Crew PII** (COC competency, COP, GMDSS, medicals, STCW, vaccinations) | **NO — zero crew PII.** Crew certs live in CMS (Crew Management System, separate platform). DMLC II row stores PDF + cert-level metadata only. | **D-CERT-001, D-CERT-177** |
| 5 | Free-text audit content (DPA reasons, Master rejection reasons) | YES — internal-sensitive; redacted from external auditors | D-CERT-180 |
| 6 | PHI / PCI / financial / minors' / biometric data | NO — none touched | SSOT scope §1 |

---

## 3. Regulatory Regimes

**Maritime-compliance regimes (drive functional requirements, retention, and audit posture):**

- IMO ISM Code (2010 amendments) — module is the digital replacement for SMS-controlled doc "SQE S 633" (D-CERT-103, D-CERT-125).
- SOLAS (as amended, esp. Ch IX certificate regimes).
- MARPOL Annex I/II/IV/V/VI consolidated 2022.
- MLC 2006 + DMLC I/II.
- Class society survey schemes (NK / KR / BV).
- KSM SSQE Manual Rev 01 Feb 2026 (internal SMS standard).

**Data-privacy regimes:**

- ✅ **RESOLVED (B-SEC-01, 2026-06-12):** formal GDPR/PDPA procedures are **NOT APPLICABLE** as a Certs-module concern. The internal employment-data context (~30–50 KSM employees, D-CERT-184) is governed by **KSM employment terms + Thai labor law** (**D-CERT-185**, LOCKED — under-reported in the original harvest). Any formal DSR request is handled at corporate level via HR + Legal, never via Certs tooling. CCPA: not applicable (no California consumers).

---

## 4. Authentication & Token Handling

| Control | Value | Source |
|---------|-------|--------|
| Token library | SimpleJWT (`djangorestframework-simplejwt`) — platform-locked | SSOT §14.1 (D-CERT-022), TECH_STACK §1 |
| Token payload | `user_id`, `role`, `form_ids`, `process_ids`, scoped vessel list, global-access flag | `../ssot_auth_specific.md` §9 |
| Client-side storage (WEB) | **Browser localStorage** (persistent client store, rehydrated on app load) — platform pattern, not a Certs choice | `../ssot_auth_specific.md` §10 |
| Refresh strategy | Refresh token issued at login; access token refreshed before expiry | `../ssot_auth_specific.md` §9–10 |
| MFA / step-up reauth | **NONE — by locked decision.** Confirmation dialog suffices for high-risk ops (rollback, catalog edit, decommissioning, anniversary change); all destructive ops are soft-delete + audited + recoverable. Do NOT introduce TOTP / push-confirm / yubikey. | **D-CERT-081**, D-AUDRS-276 |
| Token rotation policy | ✅ **RESOLVED (B-SEC-02):** access token **60 min**, refresh token **30 days** (43200 min); `ROTATE_REFRESH_TOKENS: True` + `BLACKLIST_AFTER_ROTATION: True` | Platform — `../VIMS DOCS/TECH_STACK.md` (env block + SIMPLE_JWT settings) |

> **Note on localStorage:** token-in-localStorage is the inherited platform posture (`ssot_auth_specific.md` §10). Certs does not deviate (D-AUDRS-276). Any hardening (httpOnly cookie migration) is a **platform** decision, out of Certs scope.

---

## 5. Session Policy

| Control | Value | Source |
|---------|-------|--------|
| Idle timeout — office (DPA, FM, Sup'tts) | **8 h** | **D-CERT-082** |
| Idle timeout — vessel (Master, C/O, C/E, 2/E) | **24 h** | **D-CERT-082** |
| Pre-timeout warnings | 15-min and 5-min toast warnings | D-CERT-082 |
| Re-auth UX | PMS-style modal overlay (not redirect); preserves form state; identifier pre-filled (CrewID vessel / Employee ID office) | D-CERT-082 |
| Time reference | Server-issued timestamps on vessel local time via `wrh_ship_time_config` | D-CERT-082 |
| Connectivity drop during session | No interruption until next sync (HTTP-level resilience only — NOT offline mode, per D-CERT-156) | D-CERT-082 |
| External-auditor session end | Grant auto-expires; **no early-revocation button** (DPA/Marine Sup'tt may shorten expiry by editing the grant = effective revocation) | D-CERT-195 |
| Multi-vessel Master | NOT supported — `vessel.master_user_id` strictly 1:1 | D-CERT-083 |
| Absolute session lifetime (max regardless of activity) | ✅ **RESOLVED (B-SEC-03, 2026-06-12):** no additional absolute cap — the **30-day refresh-token lifetime** is the effective ceiling; idle timeouts (D-CERT-082) are the operative control | Closure decision + platform JWT settings |
| Concurrent sessions / multi-device policy | ✅ **RESOLVED (B-SEC-03):** unrestricted — stateless JWT, no platform session registry; consistent with deployed Safety. No per-device limits in V1 | Closure decision (platform precedent) |

---

## 6. Password Policy

The Certs module introduces **no password surface of its own** — login is the shared platform flow (`Ship_UsersLogin` / office login per `../ssot_auth_specific.md` §3).

- ✅ **RESOLVED (B-SEC-04/05, 2026-06-12):** password policy and reset/change flow are **platform-inherited, out of Certs remit** — the same inheritance posture the SSOT locked for residency/encryption/keys/backup/DR/privacy-notice (**D-CERT-187…193 pattern**). The platform sweep found no written policy doc; recording the platform's actual values is a **corporate-IT documentation item, not a Certs build dependency** (Certs builds zero password code).
- Temporary passwords: `Ship_UsersLogin` carries an optional temp-password field (platform pattern, `ssot_auth_specific.md` §3.1); no Certs-specific behavior.

---

## 7. Encryption & Key Management

| Layer | Control | Source |
|-------|---------|--------|
| PDF blobs at rest | **AES-256** (S3-compatible store, matches Reporting + Safety pattern) | **D-CERT-019**, D-CERT-189, SSOT §10.1 |
| Blob transit | **TLS 1.3** | D-CERT-019 |
| App API transit (TLS floor) | ✅ **RESOLVED (B-SEC-06):** **TLS 1.3** policy-level lock applies platform-wide, not just blobs (**D-CERT-189**: "§10 already locked AES-256 at-rest and TLS 1.3 in-transit at the policy level"); certificates platform-managed (Let's Encrypt / Azure App Service per Safety TECH_STACK) | D-CERT-189, Safety TECH_STACK |
| Database at rest (`ksm_cms_live` SQL Server) | ✅ **RESOLVED (B-SEC-07):** **inherits VIMS-wide at-rest policy (D-CERT-189, LOCKED)** — implementation (full-disk vs TDE vs per-blob) follows the VIMS-wide standard; explicitly "No Certs-module-specific encryption design". No Certs field is individually encrypted (audit-log tamper-resistance is GRANT-based — see §9) | **D-CERT-189** |
| Key management & rotation | ✅ **RESOLVED (B-SEC-08):** **inherits VIMS-wide KMS (D-CERT-190, LOCKED)** — "No Certs-specific key provisioning, rotation policy, or escrow" | **D-CERT-190** |

---

## 8. Secrets Handling

| Secret | Handling | Source |
|--------|----------|--------|
| Magic-link ack URLs | Signed via `itsdangerous` or `django.core.signing`; **single-use, 24h expiry** | **D-CERT-154**, TECH_STACK §2 |
| External-auditor signup token | `signup_token_hash` = SHA-256 stored; raw token sent once in signup email then discarded | BACKEND_STRUCTURE §3.14 |
| External-auditor session token | `token_secret_hash` = SHA-256 post-signup | BACKEND_STRUCTURE §3.14 |
| Slack credentials, SMTP credentials, S3 keys, Django `SECRET_KEY` | Shared platform infrastructure — consumed per standard VIMS pattern | TECH_STACK §1 |
| Secrets storage / rotation / access audit | ✅ **RESOLVED (B-SEC-09):** platform convention = **`.env` files + `python-dotenv` 1.0.1** (`SECRET_KEY`, `DB_PASSWORD`, `JWT_*`, `SLACK_BOT_TOKEN` per `../VIMS DOCS/TECH_STACK.md` env block); no vault in V1; rotation = corporate IT per D-CERT-190 inheritance | Platform (VIMS DOCS + Safety TECH_STACK) |

---

## 9. Audit Log — Scope, Retention, Tamper-Evidence

| Control | Value | Source |
|---------|-------|--------|
| Table | `vims_certs_audit_log` — append-only | BACKEND_STRUCTURE §3.9 |
| Tamper-evidence (DB layer) | `vims_app` role holds **INSERT + SELECT only** — no UPDATE/DELETE GRANT, ever. `vims_admin` used only for migrations. **NEW (B-FM-03 resolution, 2026-06-12):** third role **`vims_jobs`** holds UPDATE scoped to retention columns (`retention_tier`, `archived_at`, soft-delete flags) on `vims_certs_audit_log` + the 5y-purge DELETE path ONLY; used exclusively by the two scheduled retention tasks. App write path stays append-only. | **D-CERT-179** + B-FM-03 |
| Tamper-evidence (app layer) | `AuditLog.objects.create(...)` only; manager exposes no update/delete | BACKEND_STRUCTURE §2 |
| Action scope | 30+ action enum (`create_catalog_row` … `retention_purge`) | BACKEND_STRUCTURE §3.9 |
| Retention | **5 years rolling** (D-CERT-099, AMENDS D-CERT-091) — hot 2y + cold 3y tiers (D-CERT-183); nightly soft-delete batch, itself audited | D-CERT-099, D-CERT-183, D-CERT-091 |
| Read access | DPA + FM full fleet; Marine/Tech Sup'tt assigned-vessel slice via filtered view | D-CERT-091 |
| Export | DPA only — watermarked PDF + CSV for ISM external audit | D-CERT-091 |
| External-auditor view | Free-text reasons rendered `[REDACTED — internal note]` at serializer layer | **D-CERT-180** |
| Cross-module writeback attribution | `vims_certs_cert_change_log` (append-only, same GRANT regime) records `source_module ∈ {CERTS, AUDIT, SYSTEM}` + `version_after` CAS trail | BACKEND_STRUCTURE §3.19 (D-AUDRS-236/239) |
| Print artifact identifiability | Stored artifact/audit/history records retain UTC date/time, user name + role, 8-char system-state hash, and unique `print_id`; normal visible PDFs omit these internal identifiers except `Printed by` | **D-CERT-128, D-CERT-202** |
| Notification audit trail | Trigger event, recipients, channels, delivery/ack status, escalation level; metadata 5y, body content 1y | D-CERT-155, D-CERT-181 |

---

## 10. Data Subject Rights

- **Personal-data footprint = internal KSM employees only** (D-CERT-184); zero crew PII (D-CERT-177); no external-customer data subjects.
- **Vessel decommissioning / sale:** vessel data deleted 30 days from handover or scrap date; deletion event retained in audit log indefinitely (D-CERT-044). KSM retains a **redacted audit-log slice** (cert events only, no personnel data) post-delete for compliance history (D-CERT-093).
- **Blob deletion lifecycle:** soft-delete to delete-pending bucket, 7-day grace, then irreversible hard-delete (D-CERT-021, SSOT §10.4).
- ✅ **RESOLVED (B-SEC-10, 2026-06-12):** already LOCKED by **D-CERT-185 + D-CERT-186** (under-reported in the original harvest): no self-service DSR UI, no formal DSR SOP in the module — requests route to corporate HR + Legal; departing employees get account deactivation per KSM IT policy; **audit-log entries are retained per maritime compliance regulations, which override deletion requests as a matter of law** (no pseudonymization mechanism in V1). The "5y retention vs erasure" tension is resolved by decision: retention wins.

---

## 11. Rate Limits & Abuse Controls

| Dimension | Limit | Behavior | Source |
|-----------|-------|----------|--------|
| Print generation | >10/hour/user | **Soft limit** — no hard block; audit-log entry "high-volume print activity" surfaces on FM dashboard | **D-CERT-143** |
| Batch PDF ingest | ≤10 PDFs/batch | Hard validation cap (OCR throughput) | D-CERT-104 |
| Bulk catalog soft-delete | ≤50 rows/batch | Hard cap + single confirm + reason field (prevents fleet-wide wipe) | D-CERT-092 |
| Class-snapshot parser | 5-min hard timeout; auto-retry ×2 (30s + 90s backoff) | Job-level guard | D-CERT-059 |
| Concurrent snapshot upload | Advisory lock, 5-min auto-release | Race guard | D-CERT-056 |
| Email dispatch | Retry ×3 (1min / 5min / 30min); then Slack-DM fallback for critical alerts | Delivery guard | D-CERT-159 |
| Per-IP / per-endpoint API rate limiting (429 + Retry-After) | ✅ **RESOLVED (B-SEC-11, 2026-06-12):** **no hard API throttling in V1.** Platform runs no DRF throttle config (sweep confirmed), and the module's locked philosophy is soft-surface-not-block (D-CERT-143). ~50 internal users on a private app ≠ public-API abuse surface. APP_FLOW §5 RATE_LIMITED = N/A is hereby **confirmed**, no longer contingent. Revisit only if the platform ever exposes public endpoints. | Closure decision + platform sweep |

---

## 12. Third-Party Sharing & External Access

| Channel | Control | Source |
|---------|---------|--------|
| External auditor portal | Time-bound grant: 7-day default, DPA-extendable to 30 max; scoped to specific vessel(s) AND document set(s) (section/category/cert-ID granularity) | **D-CERT-096** |
| Auditor activity | **NOT tracked** (deliberate): grant event logged; in-window reads/downloads opaque; only grant-level `last_accessed_at` | **D-CERT-196** |
| Auditor revocation | Auto-expire only; expiry-edit = effective revocation | D-CERT-195 |
| Master share-bundle | ZIP with auto-generated manifest PDF (title, issuer, dates, file ref per cert); for port agents / charterers / vetting inspectors | D-CERT-096, D-CERT-145 |
| Watermarking | Normal print PDFs show selected watermark label at the bottom-right of each page without recipient name; auditor/print scoping remains per watermark matrix | D-CERT-138, D-CERT-202 |
| Email-out of reports | Opt-in checkbox at print time; recipient + subject + attachment audit-logged | D-CERT-149 |
| Class-society portals | **NO API integration, EVER** (BV MOVE, KR e-Fleet, NK-SHIPS, ABS Eagle, RINA — all banned). Manual PDF upload in perpetuity. | **D-CERT-169** |
| Cross-module V1 | No sibling-module API calls in or out; URL cross-links only | D-CERT-176, D-CERT-178 |
| Sub-processors (S3 vendor, Slack, SMTP relay) | ✅ **RESOLVED (B-SEC-12, 2026-06-12):** hosting = **Azure (southindia primary / centralindia standby)**, Nginx + Gunicorn, blob on platform storage (Safety TECH_STACK); messaging = Slack workspace + platform SMTP. DPA paperwork with these vendors = **corporate IT, per the D-CERT-187/188 inheritance posture** ("cross-border-data-transfer compliance handled at corporate IT level for the entire VIMS platform") — not a Certs build dependency. | Platform sweep + **D-CERT-187/188** |

---

## 13. Pen-Test / Security Review Plan

✅ **RESOLVED (B-SEC-13, 2026-06-12 closure session):** V1 gate = **internal adversarial security review at end of Phase 8**, scope: (a) external-auditor portal — token forgery, scope escape, expired-grant access; (b) magic-link ack — replay, reuse after 24h, cross-cert substitution; (c) RBAC bypass — direct API calls against `CERT_F_*`/`CERT_P_*` gates and §20 redaction; (d) audit-log GRANT regime — attempt UPDATE/DELETE as `vims_app`. Executed as adversarial test cases inside the existing test suite, results logged in progress.txt before Phase 9 cutover. **External pen-test deferred post-V1** (internal app, ~50 users, no public surface) — DPA may commission one any time; this gate does not block go-live.

---

## 14. Control Index (for IMPLEMENTATION_PLAN Traceability lines)

| Control ID | Control | Decision |
|------------|---------|----------|
| SEC-CERT-01 | Append-only audit log via DB GRANT separation | D-CERT-179 |
| SEC-CERT-02 | Audit retention 5y rolling, hot/cold tiering | D-CERT-099, D-CERT-183 |
| SEC-CERT-03 | Session idle timeout + modal re-auth | D-CERT-082 |
| SEC-CERT-04 | Blob encryption AES-256 at rest / TLS 1.3 transit | D-CERT-019, D-CERT-189 |
| SEC-CERT-05 | External-auditor grant scoping + auto-expiry | D-CERT-096, D-CERT-195 |
| SEC-CERT-06 | No auditor activity tracking (grant-level only) | D-CERT-196 |
| SEC-CERT-07 | Audit free-text redaction for external view | D-CERT-180 |
| SEC-CERT-08 | Magic-link single-use 24h signed URLs | D-CERT-154 |
| SEC-CERT-09 | Print artifact identifiability in stored artifact/audit/history records | D-CERT-128, D-CERT-202 |
| SEC-CERT-10 | Soft-limit print throttle + FM surfacing | D-CERT-143 |
| SEC-CERT-11 | Bulk-delete cap (≤50) + ingest cap (≤10) | D-CERT-092, D-CERT-104 |
| SEC-CERT-12 | No MFA / no break-glass / no acting-Master | D-CERT-081, D-CERT-097, D-CERT-077 |
| SEC-CERT-13 | Zero crew PII | D-CERT-001, D-CERT-177 |
| SEC-CERT-14 | Token/secret hashing (SHA-256, store-hash-only) | BACKEND_STRUCTURE §3.14 |
| SEC-CERT-15 | Cross-module CAS + change-log attribution | D-AUDRS-236/239 |
| SEC-CERT-16 | `vims_jobs` retention role — sole UPDATE/DELETE path for audit-log retention ops | B-FM-03 resolution (2026-06-12) |
| SEC-CERT-17 | Uniform 5y rolling retention for all event/evidence tables (LOCKED exceptions: D-CERT-020/060 indefinite, D-CERT-044 30-day vessel delete, D-CERT-175 1y body purge) | B-FM-04 resolution (2026-06-12) |
| SEC-CERT-18 | Phase 8 internal adversarial security review gate | B-SEC-13 resolution (2026-06-12) |

---

*End of SECURITY.md v1.1 — all B-SEC items RESOLVED 2026-06-12; `BLOCKERS.md` is the resolution audit trail. Cascades applied same-day: APP_FLOW §5 (RATE_LIMITED confirmed N/A), FIELD_MAP §23/§24 (vims_jobs role, 5y retention), IMPLEMENTATION_PLAN (step 0.3 role provisioning, Phase 8 security-review gate).*
