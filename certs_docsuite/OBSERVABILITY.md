# VIMS Certificates Module — Observability

> **Version:** 1.1
> **Last Updated:** 2026-06-12 (v1.1 — all 8 B-OBS blockers resolved same day; v1.0 created earlier same day)
> **Status:** 🟢 LOCKED — Ready for Build. All B-OBS-01 … B-OBS-08 RESOLVED 2026-06-12 (closure session, Prince/DPA + platform-fact sweep). `BLOCKERS.md` retained as the resolution audit trail. **V1 infrastructure-observability posture: deliberately minimal, matching the DEPLOYED Safety module** (no APM, no error-tracking vendor, no metrics stack) — with ONE addition: the cadence-heartbeat dead-man alert (§4a), because silent alert-engine death is unacceptable for a compliance module.
> **Source:** `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16 (D-CERT-\* decisions), `BACKEND_STRUCTURE.md` §11 (background jobs), `PRD.md`, `VALIDATION_RULES.md`, `FRONTEND_GUIDELINES.md`.
> **Why this doc exists:** KLOSS Step 2 framework revision (2026-05-27) added OBSERVABILITY.md to the canonical set (interrogation Domain 10). The Certs interrogation (D-CERT-001…198) decided rich **domain-level** observability (expiry alerting, escalation, parser anomaly detection, audit trail) but never interrogated **infrastructure-level** observability (error tracking, logging, tracing, health checks) — those are BLOCKED, not defaulted.
> **Module posture:** Certs is **audit-log-first**: the append-only `vims_certs_audit_log` is the canonical event stream. There is NO product-analytics instrumentation (Mixpanel/GA4/etc.) in scope — see §5.

---

## 1. Error Tracking

✅ **RESOLVED (B-OBS-01, 2026-06-12):** **NO error-tracking vendor in V1 — deliberate.** Platform fact: deployed Safety states "No Prometheus / Grafana / Datadog agent added at module level" and names no Sentry/App-Insights anywhere; Certs inherits that posture rather than introducing a vendor unilaterally. Errors are visible through: (a) Django/Gunicorn/Nginx server logs (platform default), (b) the audit-log ERROR surfacing on the DPA dashboard (APP_FLOW §5 ERROR state), (c) the §4a heartbeat alert for scheduled-job death. **PII scrubbing: moot — no third-party vendor receives error payloads.** If a vendor is ever adopted (platform-wide decision), D-CERT-184 employee data must be scrubbed before adoption.

---

## 2. Structured Logging

✅ **RESOLVED (B-OBS-02, 2026-06-12):** **standard Django logging to Gunicorn/Nginx logs — platform default, no structured-JSON schema in V1 (deliberate, matches deployed Safety).** Hosting context: Azure (southindia primary / centralindia standby), Nginx 1.24.x + Gunicorn 22.0.0, no Docker in prod. Log retention follows the platform file-system snapshot policy (Safety TECH_STACK precedent). Certs-specific rule: background jobs log start/finish/failure at INFO/ERROR via the standard logger, so job failures are greppable even before the §4a heartbeat fires.

**Boundary note (unchanged):** `vims_certs_audit_log` is a **business record** (5y retention, D-CERT-099) — it is NOT the application log and must not be used as one. Application logs and audit entries are separate write paths.

---

## 3. Metrics That Matter (decided, domain-level)

These are the numbers that indicate the module is working. All are sourced; thresholds are LOCKED decisions.

| Metric | Target / threshold | Action on breach | Source |
|--------|--------------------|------------------|--------|
| Per-vessel print generation (sync) | ≤ 60 s hard cap | Fail visibly; never silent | **D-CERT-144** |
| Fleet-wide print (async) | ≤ 5 min, ETA disclosed | Progress bar + ETA | D-CERT-144, APP_FLOW §3.11 |
| Class-snapshot parse time | > 3 min = anomaly | Escalate to Tech Sup'tt + DPA | **D-CERT-073** |
| Parse success rate | < expected × 0.7 = anomaly | Escalate to Tech Sup'tt + DPA | D-CERT-073 |
| Unmapped class rows per snapshot | > 15% = critical | Escalate to Marine Sup'tt | D-CERT-073 |
| Parser hard timeout | 5 min; retry ×2 (30s, 90s) | Job failure path | D-CERT-059 |
| OCR auto-accept rate | ≥ 80% office migration / ≥ 85% vessel-side | Below = manual gap-fill volume signal | D-CERT-106, D-CERT-168 |
| Email delivery | 3 retries (1/5/30 min) exhausted | Slack-DM fallback for critical; bounce count surfaced to DPA | **D-CERT-159** |
| Print volume per user | > 10/hour | Audit-log governance signal to FM dashboard | D-CERT-143 |
| Notification dedup | 60-min window per cert_row + cadence | Suppress duplicates | D-CERT-085 |

✅ **RESOLVED (B-OBS-03, 2026-06-12):** **no infrastructure-metrics stack in V1 — deliberate** (platform runs none; deployed-Safety precedent). The wake-someone-up list for this module is therefore exactly two signals: (1) the §4a cadence-heartbeat dead-man alert, (2) the D-CERT-073 parser-anomaly escalations. Everything else is next-business-day via server logs. Revisit if/when corporate IT adopts a platform metrics stack.

---

## 4. Alerts (domain-level — decided)

The module's alerting IS its core product (certificate expiry management). Escalation ladder is LOCKED:

| Alert | Trigger | Escalation | Source |
|-------|---------|-----------|--------|
| Window opening | Survey window opens (anniversary + cadence) | One-time; Master + office | D-CERT-016 |
| Window closing / expiry approach | Day 0 → Master + Marine/Tech Sup'tts; Day 7 → +DPA; Day 14 → +FM, daily; post-expiry → daily until renewed | Ladder per left | **D-CERT-089, D-CERT-162** |
| Snapshot upload due | 3-month cadence, 1-month lead (DPA-configurable) | No escalation | D-CERT-006 |
| Snapshot stale | Event-driven + 14-day grace | Prompt only | D-CERT-007 |
| Class mismatch >15% | Per snapshot | Critical → Marine Sup'tt | D-CERT-073 |
| Parser anomaly | >3 min or success <0.7× | Tech Sup'tt + DPA | D-CERT-073 |
| Email bounce ×3 | Per critical notification | Auto Slack-DM fallback; DPA counter | D-CERT-159 |
| High print volume | >10/h/user | FM dashboard surface (no page) | D-CERT-143 |

**Channel routing (LAW — D-CERT-161):** vessel-side = in-app + email ONLY; office-side = in-app + Slack ONLY. No quiet hours (D-CERT-157). No per-user preferences (D-CERT-160). Same-vessel-same-day grouping always on (D-CERT-164). Monthly digest to DPA + Marine Sup'tt, 1st 08:00 ICT (D-CERT-158).

### 4a. Heartbeat / Dead-Man Alert — ✅ RESOLVED (B-OBS-04, 2026-06-12, Prince/DPA)

**Decision: heartbeat + dead-man alert (OBS-CERT-11).** The hourly cadence cron silently dying = expiry alerts stop with no signal — unacceptable for a compliance module.

| Element | Spec |
|---------|------|
| Heartbeat write | Every cadence-cron run (hourly, idempotent) finishes by stamping `last_heartbeat_at` (UTC) — single platform-readable row (implementation slot: `vims_certs_settings`) |
| Dead-man check | Independent django-celery-beat task, every 30 min: if `now() - last_heartbeat_at > 2h` → fire alert. Independent of the cadence task so one failure mode can't kill both |
| Alert channel | Office Slack channel (D-CERT-161 office-side routing) + persistent red tile on the DPA dashboard until heartbeat resumes |
| Self-failure mode | If Celery itself is dead, both tasks stop — residual risk accepted; the DPA dashboard tile renders "heartbeat age" client-side from `last_heartbeat_at`, so a stale value is visible on every DPA dashboard load even with Celery fully down |
| Build slot | IMPLEMENTATION_PLAN step 6.7 |

No other infrastructure alerts in V1 (queue backlog, DB down → server-log territory, next-business-day).

---

## 5. Event Taxonomy (audit-log-first; no product analytics)

**Position:** Certs fires **no product-analytics events** (no GA4/Mixpanel/PostHog). The append-only audit log (BACKEND_STRUCTURE §3.9, 30+ action enum) is the event stream; it exists for ISM compliance, not funnel analysis. This satisfies the framework rule "every PRD feature fires at least one event **or explicitly notes why not**" as follows:

| PRD domain | Event coverage | Mechanism |
|------------|----------------|-----------|
| CAT (catalog) | `create/update/deprecate/hard_purge_catalog_row` | audit log |
| TRK (tracked items) | `create/update/submit/approve/reject_tracked_item` | audit log + `vims_certs_approval_event` |
| OCR / WIZ / MIG | `upload_pdf`, batch ingest events, gap-fill commits | audit log + `vims_certs_batch_ingest` |
| REC (reconciliation) | snapshot upload, run create, flag resolution | audit log + `vims_certs_reconciliation_run/flag` |
| PRT (print/export) | print artifact creation w/ `print_id` + state hash | audit log + `vims_certs_print_artifact` (D-CERT-128) |
| NOTIF | full dispatch trail: trigger, recipients, channels, delivery/ack, escalation level | `vims_certs_notification_meta` (D-CERT-155) |
| AUDIT | log reads are themselves… not logged (read access is RBAC-gated, not evented) | D-CERT-091 |
| EXT (external auditor) | grant create/edit/expiry logged; **in-window activity deliberately NOT tracked** | D-CERT-194/195/**196** |
| RBAC / DASH / LIFE / BLOB / XMOD | covered by the underlying mutation events above; pure-read dashboards fire no events — reason: audit-log-first posture, reads are not business records | — |

✅ **RESOLVED (B-OBS-05, 2026-06-12):** product analytics **permanently out of scope** — the audit-log-first posture above is the complete event story. If analytics is ever wanted (post-V1), it must NOT reuse the audit log (5y business record) and needs a separate, scrubbed pipeline.

---

## 6. Performance Budgets

**Decided (tactical):** see §3 table — print 60s / fleet 5min / parser 5min / OCR thresholds.

✅ **RESOLVED (B-OBS-06, 2026-06-12):** **no additional numeric web budgets in V1 — deliberate.** The decided domain budgets (§3: print ≤60s, fleet ≤5min, parser ≤5min, OCR thresholds) ARE the module's performance contract. Certs adds zero new frontend libraries (TECH_STACK §3), so the platform bundle is unchanged by construction; page-load/Lighthouse/API-p95 ceilings don't exist platform-wide (deployed-Safety precedent) and inventing module-only numbers nobody measures would be theater. Revisit alongside B-OBS-03 if a metrics stack ever lands.

---

## 7. Distributed Tracing

✅ **RESOLVED (B-OBS-07, 2026-06-12):** **none — deliberate.** Platform fact confirmed: no APM/tracing agent anywhere in the deployed stack (Safety TECH_STACK explicitly: "No Prometheus / Grafana / Datadog agent"). Single Django monolith + Celery — request flow is debuggable from server logs at this scale.

---

## 8. Health Checks & Background-Job Monitoring

**Background jobs (decided, BACKEND_STRUCTURE §11):**

| Job | Trigger | Guard |
|-----|---------|-------|
| OCR worker | event-driven queue | queued until completion |
| Parser worker | event-driven | 5-min timeout, retry ×2 (D-CERT-059) |
| Notification worker | queue drain | email retry ×3 + Slack fallback (D-CERT-159) |
| Cadence cron | hourly | idempotent per hour |
| Monthly digest | 1st of month 08:00 ICT | D-CERT-158 |
| Draft auto-expire | nightly | drafts >7d |
| Print-artifact GC | daily | 7-day grace then hard-delete |
| Audit-log retention batch | nightly | soft-delete, itself audited (D-CERT-099) |
| Auditor-grant auto-expire | periodic | D-CERT-195 |
| Audit-log tier flip (hot→cold) | periodic | D-CERT-183 |

✅ **RESOLVED (B-OBS-08, 2026-06-12):**
- **(a) Health endpoint:** `GET /api/certs/health/` — already the Phase-0 smoke endpoint (plan step 0.2), now promoted to the module health contract: returns 200 + `{status: "ok", last_cadence_heartbeat: <UTC>}`. Unauthenticated, read-only, no PII. No load balancer health-probe integration in V1 (none exists platform-wide).
- **(b) Job-failure monitoring:** the §4a heartbeat dead-man alert + INFO/ERROR job logging (§2). No dead-letter queue in V1 — failed jobs follow their decided retry ladders (D-CERT-059/159) then surface via audit/alert paths.
- **(c) Job runner NAMED:** **Celery 5.4.0 + Redis 5.0.8 (broker/result backend) + django-celery-beat 2.6.0**, 4-worker concurrency — the platform lock from deployed Safety. TECH_STACK.md worker-queue row updated to match.

---

## 9. Event/Metric Index (for IMPLEMENTATION_PLAN Traceability lines)

| ID | Item | Decision |
|----|------|----------|
| OBS-CERT-01 | Audit-log action events (30+ enum) | D-CERT-179, BACKEND_STRUCTURE §3.9 |
| OBS-CERT-02 | Notification dispatch trail | D-CERT-155 |
| OBS-CERT-03 | Expiry escalation ladder | D-CERT-089, D-CERT-162 |
| OBS-CERT-04 | Parser anomaly detection | D-CERT-073 |
| OBS-CERT-05 | Email-bounce fallback + DPA counter | D-CERT-159 |
| OBS-CERT-06 | Print budget (60s/5min) + print_id artifacts | D-CERT-144, D-CERT-128 |
| OBS-CERT-07 | Print-volume governance signal | D-CERT-143 |
| OBS-CERT-08 | OCR confidence-band thresholds | D-CERT-106, D-CERT-168 |
| OBS-CERT-09 | Fetch-failure audit surfacing (ERROR state) | APP_FLOW §5 |
| OBS-CERT-10 | Background-job guard rails | BACKEND_STRUCTURE §11 |
| OBS-CERT-11 | Cadence-heartbeat dead-man alert (stale >2h → office Slack + DPA tile) | B-OBS-04 resolution (2026-06-12) |
| OBS-CERT-12 | Health endpoint `GET /api/certs/health/` with heartbeat age | B-OBS-08 resolution (2026-06-12) |

---

*End of OBSERVABILITY.md v1.1 — all B-OBS items RESOLVED 2026-06-12; `BLOCKERS.md` is the resolution audit trail. New buildable scope from closure: heartbeat dead-man alert (plan step 6.7) + health-endpoint contract (step 0.2). Cascades applied to TECH_STACK (Celery named) and IMPLEMENTATION_PLAN.*
