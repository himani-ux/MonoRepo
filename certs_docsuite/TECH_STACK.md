# VIMS Certificates Module — Tech Stack (Version-Locked)

> **Platform: WEB** — responsive browser app (office desktop + vessel bridge tablet, same codebase). No native/mobile target, no offline mode (D-CERT-156). Other docs re-read this field before applying platform-conditional rules (CLAUDE.md → Platform Adherence).
>
> **Version:** 1.4
> **Last Updated:** 2026-07-22 (v1.4 — Certs OCR engine changed to PaddleOCR via CR-103. v1.3 — Phase 0.8 PDF renderer pick resolved: ReportLab 4.2.0 fallback after WeasyPrint 68.1 + MSYS2/Pango runtime verification failed on Windows. v1.2 — closure session: worker queue NAMED (Celery 5.4.0 + Redis 5.0.8 + django-celery-beat 2.6.0 per Safety lock); B-TECH-01/02 reclassified as scheduled Phase-0 picks (steps 0.7/0.8). v1.1 — Platform field added; TBD→BLOCKED. v1.0: 2026-05-13)
> **Status:** 🟢 Locked — Ready for Build (Phase-0 picks resolved through CR-103: PaddleOCR for Certs OCR, ReportLab PDF renderer at 0.8; Slack channel naming remains Step 0.9)
> **Source:** `../VIMS-CERTIFICATES-MODULE-SSOT.md` §14 (D-CERT-022) + sibling lock files (`VIMS-Reporting-Module/TECH_STACK.md`, `VIMS-Safety-Module/TECH_STACK.md`).
> **Inheritance rule:** Certs inherits the entire Reporting + Safety stack (Django, DRF, React, TypeScript, SQL Server, JWT, S3-compatible blob, `master_notification`). Certs adds parser + OCR + Slack libs only. **Never bump a shared dep without coordinating across all VIMS modules.**

---

## 1. Inherited Stack (DO NOT bump in isolation)

| Layer | Component | Version | Notes |
|-------|-----------|---------|-------|
| Backend framework | Django | 5.2.7 | LTS-track; matches Reporting + Safety |
| API layer | Django REST Framework | 3.14.0 | Matches Reporting + Safety |
| Auth | SimpleJWT (`djangorestframework-simplejwt`) | (per `ssot_auth_specific.md`) | JWT payload + refresh per platform pattern |
| ORM | Django ORM (built-in) | with Django 5.2.7 | — |
| Database | Microsoft SQL Server | `ksm_cms_live` (shared) | Same DB as Reporting / Safety / Inspection / PMS / Purchase / WRH |
| DB driver | `mssql-django` | (per existing platform lock) | Don't bump without DBA review |
| Frontend framework | React | 18.3.1 | Matches Reporting + Safety |
| Type system | TypeScript | 5.4.5 | Matches Reporting + Safety |
| Build / dev | Vite | (per platform lock) | Same `vite.config.ts` pattern |
| Routing | React Router | (per Reporting lock) | Match Safety/Reporting nav pattern |
| State — server | TanStack Query (React Query) | (per Reporting lock) | All `/api/certs/` reads via TanStack hooks |
| State — client | Zustand | (per Reporting lock) | One store per Cert sub-domain (catalog / wizard / reconciliation / print / notifications) |
| Forms | React Hook Form + Zod | (per Reporting lock) | Schema-first form validation; mirrors Safety `schemas/safety/` pattern |
| Styling | Tailwind CSS | (per Reporting lock) | + shadcn/ui primitives |
| Component library | shadcn/ui | (per Reporting lock) | Composed against Tailwind tokens |
| Icons | lucide-react | (per Reporting lock) | — |
| Date / time | date-fns | (per Reporting lock) | + timezone helpers from `wrh_ship_time_config` consumer pattern |
| HTTP client | fetch (native) wrapped in TanStack Query | — | No axios; consistent with Safety/Reporting |
| PDF generation | ReportLab | 4.2.0 | Matches Reporting + Safety; used for print export |
| Notifications (in-app) | `master_notification` table (shared) | — | Single bell-icon inbox across VIMS modules |
| Notifications (email) | `email_dispatcher` service (shared) | — | HTML+plain-text multipart per D-CERT-152 |
| Blob storage | S3-compatible (per existing platform lock) | — | AES-256 at-rest, TLS 1.3 in-transit per D-CERT-019, D-CERT-189 |
| Worker queue | **Celery + Redis + django-celery-beat** | Celery 5.4.0 / Redis 5.0.8 / django-celery-beat 2.6.0 (per Safety lock) | Named 2026-06-12 (B-OBS-08 resolution; was "per existing platform job runner"). 4-worker concurrency, platform setting. Async OCR per D-CERT-123, scheduled crons per D-CERT-021, heartbeat dead-man pair per OBS-CERT-11 |

**Source-of-truth lock files for shared deps:**
- `../VIMS-Reporting-Module/TECH_STACK.md` (canonical Django/DRF/React versions)
- `../VIMS-Safety-Module/TECH_STACK.md` (canonical PDF + notification additions)
- Platform-wide `package.json`, `requirements.txt`, `pyproject.toml` (one repo-root spec)

If a sibling module bumps a shared dep, Certs adopts the same version in the same PR — never lag.

---

## 2. Certs-Specific Additions

| Layer | Component | Version target | Purpose | D-CERT-\* |
|-------|-----------|----------------|---------|-----------|
| Class snapshot parser | `pdfplumber` + PaddleOCR fallback (`paddleocr`, `paddlepaddle`, `Pillow`) | pdfplumber ≥0.11.x; paddleocr/paddlepaddle/Pillow per backend requirements | Text extraction from NK / KR / BV class status PDFs; OCR fallback only when the PDF exposes no text layer | D-CERT-005, D-CERT-048, D-CERT-054, D-CERT-200 |
| Class snapshot parser fallback | `tabula-py` (optional) | latest stable | Table extraction fallback for complex layouts | D-CERT-054 |
| Per-class parser modules | KSM-internal Python modules | own version | NK / KR / BV format parsers; one module per class society | D-CERT-005 |
| OCR engine for cert PDFs | PaddleOCR (`paddleocr`, `paddlepaddle`) | paddleocr 3.7.0; paddlepaddle 3.2.0 | OCR vessel-uploaded cert PDFs per D-CERT-101, D-CERT-105, D-CERT-106, using the same payload and confidence-band contract | D-CERT-101, D-CERT-106, D-CERT-168 |
| Print PDF renderer | ReportLab | 4.2.0 | Phase 0.8 pick: WeasyPrint 68.1 preferred path was attempted, but Windows native runtime verification failed even after MSYS2/Pango remediation; use the already-pinned ReportLab fallback for SQE S 633 print export per D-CERT-125 and D-CERT-144. | D-CERT-125, D-CERT-144 |
| Excel renderer (data-only) | `openpyxl` | latest stable | Data-only Excel companion to print PDF (no live formulas) per D-CERT-141 | D-CERT-141 |
| ZIP bundle | `zipfile` (Python stdlib) | with Python 3.x | Manifest PDF + cert PDFs bundle per D-CERT-145 | D-CERT-145 |
| Slack SDK | `slack-sdk` (Python) | latest stable | Per-vessel + fleet-wide Slack channel routing per D-CERT-151, D-CERT-160, D-CERT-161 | D-CERT-151, D-CERT-161 |
| File hashing | `hashlib` (Python stdlib) | with Python 3.x | SHA-256 for PDF dedup per D-CERT-051, D-CERT-118 | D-CERT-051, D-CERT-118 |
| Magic-link signing | `itsdangerous` or `django.core.signing` | with Django | Signed 24h-expiring single-use URLs per D-CERT-154 | D-CERT-154 |
| Survey-window computation | KSM-internal Python module (`apps/certs/services/survey_window.py`) | own | Compute `window_open` / `window_close` from anniversary + cadence + IMO rules per D-CERT-063, D-CERT-064 | D-CERT-063, D-CERT-064 |

**Phase 0 picks — choose at scaffold time (plan steps 0.7 / 0.8; formerly B-TECH-01/02, reclassified at closure 2026-06-12):**
1. **OCR engine** — **RESOLVED 2026-07-22: PaddleOCR.** Certs uses PaddleOCR for vessel-uploaded certificate PDF OCR and for bounded class-snapshot fallback when a class-status PDF has no text layer. The wrapper interface remains stable for future benchmarking.
2. **HTML-to-PDF renderer** — **RESOLVED 2026-06-24: ReportLab 4.2.0 fallback.** WeasyPrint 68.1 installed, MSYS2 + `mingw-w64-x86_64-pango` installed, and MSYS2 DLL preload attempted; render still failed on Windows due DLL conflict/access violation. Do not add WeasyPrint to project requirements unless a future runtime smoke test passes.

---

## 3. Frontend Additions (none beyond inherited)

Certs introduces no new frontend libs. All UI built from inherited Reporting/Safety primitives:
- `shadcn/ui` for buttons, dialogs, tables, dropdowns, toasts, tabs.
- Tailwind utilities for layout.
- `react-hook-form` + Zod for forms.
- TanStack Query for data fetching.
- Zustand for client state.
- `date-fns` for dates.
- `lucide-react` for icons.

If a Certs-specific component (e.g. `OcrConfidenceBadge`, `BatchProgressBar`) needs a primitive that isn't already in shadcn, build it from scratch in `src/components/certs/shared/` rather than introducing a new lib.

---

## 4. Database Tables (new prefix `vims_certs_*`)

Per SSOT §14.3:

- `vims_certs_catalog_section`
- `vims_certs_catalog_row`
- `vims_certs_class_code_mapping`
- `vims_certs_tracked_item`
- `vims_certs_pdf_blob`
- `vims_certs_class_status_snapshot`
- `vims_certs_reconciliation_run`
- `vims_certs_reconciliation_flag`
- `vims_certs_audit_log`
- `vims_certs_alert_config`
- `vims_certs_approval_event`

Plus expected additions (per build-out):
- `vims_certs_notification_meta` — Certs-specific notification metadata linked to `master_notification.id` per D-CERT-151
- `vims_certs_print_artifact` — `print_id` index, blob refs, system-state hash per D-CERT-128, D-CERT-147
- `vims_certs_external_auditor_access` — auditor login records, scope, expiry per D-CERT-096, D-CERT-194
- `vims_certs_batch_ingest` — onboarding batch state per D-CERT-104, D-CERT-117

Schemas, columns, indices, FKs detailed in `BACKEND_STRUCTURE.md`. **Naming rule:** `vims_certs_*` strictly — never bare `certs_*`.

**Existing VIMS masters consumed (no duplication):**
- `master_role`, `master_RoleByVessel`, `master_user`, `master_vessel`, `master_notification`
- `wrh_ship_time_config` (vessel local-time for re-auth modal per D-CERT-082)
- `msc_profiles` (auth: `form_ids` + `process_ids`)
- `Mapping_CrewAssReviewers` + `has_global_vessel_access` flag (DPA full-fleet override per D-CERT-090)

---

## 5. API Surface (DRF, mounted at `/api/certs/`)

Per SSOT §14.4 + onboarding/auditor additions:

- `/api/certs/catalog/...` — catalog mgmt (DPA only)
- `/api/certs/tracked-items/...` — TrackedItem CRUD per vessel
- `/api/certs/class-snapshots/...` — upload, list, parse
- `/api/certs/reconciliation/...` — run history, mismatches, three-panel UI feed
- `/api/certs/print/...` — SQE S 633 PDF/Excel export, ZIP bundle
- `/api/certs/dashboard/...` — fleet rollup
- `/api/certs/alerts/...` — alert config (DPA-tunable lead times)
- `/api/certs/onboarding/...` — 7-step wizard endpoints (vessel-locked batch ingest, gap-fill, dry-run preview, commit, FM sign-off, rollback)
- `/api/certs/notifications/...` — Certs-side notification dispatch + ack endpoints (magic-link landing)
- `/api/certs/auditor-access/...` — provisioning (Marine Sup'tt + DPA), scoped read-only login flow
- `/api/certs/audit-log/...` — read (RBAC-scoped per D-CERT-091), DPA export

Detailed endpoint contracts (request/response schemas, status codes, RBAC scopes) in `BACKEND_STRUCTURE.md`.

---

## 6. Browser Support

Same matrix as Reporting + Safety:
- Chrome 90+
- Safari 14+
- Edge 90+
- Firefox 90+

Vessel bridge tablets: target Chrome on Android tablet + Safari on iPad. Office desktop: any of the four.

---

## 7. Python / Node Runtime

- **Python:** version per platform lock (currently 3.x; matches Reporting + Safety).
- **Node:** version per platform lock; LTS only.
- **Package managers:** `pip` + `pip-tools` (Python); `pnpm` (Node) — match repo-wide convention.

---

## 8. Dev Environment

- Local DB: SQL Server in Docker (`mcr.microsoft.com/mssql/server:2022-latest`), `localhost:1434`, mirrors `ksm_cms_live` schema via migrations.
- Auth: dev JWT issuer matches platform pattern.
- OCR engine + Slack SDK: stub modes for offline dev (mock OCR returns fixed payloads; Slack SDK no-ops with logged-only output).
- Worker queue: in-process for dev; production uses platform job runner.

---

## 9. CI / CD

Inherits VIMS monorepo CI:
- Lint: ruff (Python), eslint + prettier (TS).
- Type-check: mypy (Python, optional in V1), tsc (TS, mandatory).
- Test: pytest (Python), vitest (TS).
- **Certs-specific gate:** parser CI runs full 6-PDF reference class-status corpus (D-CERT-057). Every parser PR must pass; no skip.
- Build: standard Vite + Django collectstatic.
- Deploy: per platform CD pipeline.

---

## 10. Versioning Discipline

- **No isolated dep bumps.** Any change to a row in §1 (Inherited Stack) requires coordinated PR across all VIMS modules.
- **Certs-specific deps in §2 may bump independently** but require parser CI corpus to remain GREEN (D-CERT-057).
- **Lock files committed.** `requirements.txt` (or pip-tools output) and `pnpm-lock.yaml` are part of the repo; never `.gitignore`.

---

*End of TECH_STACK v1.0. Coordinate any version change with `../VIMS-Reporting-Module/TECH_STACK.md` and `../VIMS-Safety-Module/TECH_STACK.md` to avoid drift across the platform.*
