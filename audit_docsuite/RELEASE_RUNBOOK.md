# RELEASE_RUNBOOK — VIMS Inspection Extension · Audit Module (Domain 14)

**Generated 2026-07-14** from SSOT **§23** (band `D-AUDRS-450..499`, decisions **D-AUDRS-450..461**) and
`docs/MIGRATION.md` (post-fork truth, D-AUDRS-288..294). Framework: KLOSS `Release.txt` / `release/`
layer, vendored at commit **`aeccc3c`** (re-vendored from the original `f908204` vendor this session —
`docs/FRAMEWORK_COMPATIBILITY.md`, Control 1). No field below changed as a result of the re-vendor; see
§12's amendment note for what did (the LEGACY-form rationale's upstream status only).

> ## ⚠ STATE: RUNBOOK GENERATED — **CROSSING BLOCKED**
>
> This is **real release law**, not a stub. It is also **not a licence to release.**
>
> `deploy.method` is an **open structured DEFERRED decision (D-AUDRS-453)**: KSM India has not
> supplied the executable deployment procedure, and **none is invented here**.
>
> | Machine | Verdict | Meaning |
> |---|---|---|
> | `sh release/bin/lint-release-runbook.sh .` | **`DEFERRED`** (exit 0) — `deferred_fields=deploy.method`, `reason_codes=DEFERRAL_OPEN` | the document is **structurally valid** and may be generated, reviewed and merged with the gap visible **in its own law** |
> | `sh release/bin/release-preflight.sh . <VERSION>` | **`BLOCKED`** (exit 1) — `reason_codes=…,DEFERRAL_OPEN` | the **crossing is impossible**. No override path — not for a hotfix, not for a deadline |
> | `sh release/bin/release-attest.sh …` | `result: ABORTED` | a tag pushed on unclosed law is attested **ABORTED**, never `RELEASED` |
>
> **This is a RELEASE blocker, not a build-handover blocker** (owner brief §6.3). The build team may
> take this bundle and build. Nobody may cross a release with it until D-AUDRS-453 closes.

---

## Table of Contents

1. Authority & inputs
2. Versioning & tags (D-AUDRS-451)
3. Deploy target — and the `deploy.method` deferral (D-AUDRS-452 / **453**)
4. Approval (D-AUDRS-454)
5. Required checks — and the whole-repo-tag mandate (D-AUDRS-456; amended by D-AUDRS-462)
6. Migration (D-AUDRS-457) — forward · reverse/recovery · verify probes
7. Rollback (D-AUDRS-458) — 8 triggers · timing · procedure
8. Attestation & evidence (D-AUDRS-455)
9. Handoff & the DRY crossing (D-AUDRS-459)
10. The crossing ceremony — order of operations
11. Honest current state of this bundle (D-AUDRS-460/461)
12. RELEASE-MACHINE-BLOCK (LEGACY form — D-AUDRS-461)

---

## 1. Authority & inputs

**Law, in precedence order.** ① The owner brief (Prince, 2026-07-14) — §3 Release, §6.0 (no-legacy-DDL
fork, EMPTY exception list), §6.1 (canonical four-state enum), §6.3–§6.5. ② SSOT **§23** — the banked
Domain 14 decisions. ③ `docs/MIGRATION.md` — **the authority for the forward/reverse/probe steps**
(it was rewritten by the no-legacy-DDL fork; the owner brief's pre-fork §4.1 draft text is
**superseded** by §6.0 and is NOT used here). ④ The **delivered** framework scripts under `release/`,
`quality/`, `journey/`, `mocks/` — the vendored copies in this bundle, never the framework originals.

**The crossing ceremony itself is `Release.txt`** (KLOSS framework). This runbook supplies the law it
executes: `versioning.tag_format`, `deploy.*`, `approval.authorizer`, `attestation.*`,
`required_checks[]`, `migration.*`, `rollback.*`, `handoff.part_a_done`.

**Four states, never collapsed** (owner brief §6.1, D-AUDRS-299④): `RESOLVED` · `DEFERRED` ·
`BLOCKED` · `NOT_APPLICABLE_YET`. **`NOT_APPLICABLE_YET` never appears in this runbook** — release-law
fields are **owner-dependent, not code-dependent** (framework `release-lib.sh`), so the only honest
state for a law field nobody has supplied is a **structured `DEFERRED` record**. Prose in a real field
("standard deploy", "to be finalised") is **none of the four**: it is an invented value that lints as
`RESOLVED` and lies to every gate downstream.

---

## 2. Versioning & tags (D-AUDRS-451)

| Item | Value |
|---|---|
| Scheme | **SemVer** |
| Tag format | **`vims-audit-v<version>`** — module-scoped, on the shared `VimsWithSafety` repo |
| Sibling | `vims-rs-v<version>` (RightShip). Modules advance **independently** |
| First cut | **MINOR (additive)** — the module adds tables/endpoints/screens and changes **no existing PSC/CAR behaviour** (D-AUDRS-001/003). Owner's worked example tag: **`vims-audit-v1.0.0`** |
| DRY namespace | **`vims-audit-dry-v0.0.1`** — never a production release (§9) |

`VERSION` is the **raw** version handed to preflight (`sh release/bin/release-preflight.sh . 1.0.0`).
The **tag is derived** from `versioning.tag_format` by the tooling — **never hand-typed**, never
derived in the other direction.

---

## 3. Deploy target — and the `deploy.method` deferral (D-AUDRS-452 / **453**)

### 3.1 Target — RESOLVED (D-AUDRS-452)

- The **existing VIMS production deployment**, extended **in place inside the existing VIMS
  application** (D-AUDRS-273/001).
- **No new application server, host, or region.**
- **Shared `ksm_cms_live`** SQL Server database (D-AUDRS-135).
- **Existing cron infrastructure** for the audit background jobs (`BACKEND_STRUCTURE.md §12`).
- **KSM India owns execution.**

These are the **known** facts, banked as known. Nothing about *how* the deploy is executed is inferred
from them.

### 3.2 Method — **DEFERRED: `D-AUDRS-453`** (release-blocking)

`deploy.method` carries the **exact sentinel `DEFERRED:D-AUDRS-453`** with a matching `deferred[]`
register entry in §12's machine block. That sentinel is **one exact token** — uppercase, one colon,
no space, non-empty registered id. A near-miss ("DEFERRED", "deferred:D-453") is
**`DEFERRAL_MALFORMED`** and fails the lint, precisely because a value that merely *looks* deferred
would lint `PASS` and let the crossing run unblocked.

**Closure data — the seven facts KSM India must supply (owner-enumerated, verbatim):**

| # | Fact |
|---|---|
| 1 | exact deployment command or numbered procedure |
| 2 | execution environment and identity |
| 3 | required credential/secret references |
| 4 | migration command (the environment-level invocation of `migration.forward`) |
| 5 | success signal |
| 6 | failure signal |
| 7 | previous-tag redeploy/rollback command |

**Owner of the deferral:** **KSM India** (execution owner) supplies the facts; **Prince (DPA)**
authorizes the resulting law change.

**Closing it is a change to release law.** The real value replaces the sentinel **and** the register
entry is deleted — **together**, via the law's **Tier-2 CR path**. **Never inline. Never at ceremony
time.** Editing the runbook mid-crossing to unblock yourself is exactly the forgery this layer exists
to prevent.

**Everything that depends on the environment rides this deferral** and is referenced, never invented:
the migration invocation wrapper (host, identity, `DJANGO_SETTINGS_MODULE`, DB credentials), the
deploy command, the previous-tag redeploy command in §7.

---

## 4. Approval (D-AUDRS-454)

`approval.authorizer` = **Prince (DPA — final freeze authority, D-AUDRS-285)**. **KSM India executes;
only Prince authorizes the crossing.**

The authorizer is a **trust root and is never deferrable** (framework `release-lib.sh`: only
`deploy.target`, `deploy.method`, `migration.tooling`, `migration.forward`, `migration.reverse`,
`rollback.procedure` may be deferred — never the authorizer, the attestation location/ref, the
required checks, the verify probes, or the rollback triggers).

**Preflight output is evidence presented to the authorizer — never the trust root, and never a
substitute for the authorizer's judgement.** A clean preflight proves the artifacts existed and matched
on that machine at that time. Nothing more.

---

## 5. Required checks — and the whole-repo-tag mandate (D-AUDRS-456; amended by D-AUDRS-462)

**A module-scoped tag still points at the WHOLE repo commit** (owner brief §3.1). The tag therefore
ships every change in that commit, attributed to this release. Seven checks are mandatory before the
tag; all seven are carried **in `required_checks[]`**, and the trusted CI job **re-executes them at the
tag**.

| # | Check | Command | State today |
|---|---|---|---|
| 1 | Module **quality gate** (Domain 13) | `sh checks/quality-gate.sh` | ✅ runs green today |
| 2 | **Journey gates** (coverage · persona-journeys · map lint · doc-format · persona coverage) | the five delivered `journey/bin` gates, with this bundle's exact arguments | ✅ run green today |
| 3 | **Backend tests** + coverage tiers (D-AUDRS-296) | `sh checks/release/backend-tests.sh` | **FAIL-CLOSED** until the build wires it |
| 4 | **Frontend tests** + coverage tier | `sh checks/release/frontend-tests.sh` | **FAIL-CLOSED** until the build wires it |
| 5 | **RBAC-grid test** — AUDQ-001, **never-waivable** (D-AUDRS-299①) | `sh checks/release/rbac-grid-test.sh` | **FAIL-CLOSED** until the build wires it |
| 6 | **Shared PSC/CAR regression** (`TEST_PLAN.md §16` Suite M) | `sh checks/release/psc-car-regression.sh` | **FAIL-CLOSED** until the build wires it |
| 7 | **Shared-code diff check** — unrelated shared-code changes are absent, or deliberately included and named in `RELEASE.md` | `sh checks/release/shared-code-diff.sh` | **FAIL-CLOSED** until the build wires it |

**`release-preflight` MUST NOT appear in `required_checks[]`** — the shipped linter fails the runbook
for recursion. The preflight **report** (`checks/reports/release-preflight.json`) is nevertheless a
**mandatory evidence artifact** (§8).

**Checks 3–7 are shipped fail-closed.** Each script under `checks/release/` carries its exact contract
in its header and **exits non-zero until Phase 0 replaces its body with the real suite invocation**. A
release **cannot cross on an unrun check**, and a check that cannot run **FAILS — it never passes by
absence**. `NOT_APPLICABLE_YET` is a **quality-gate lens state, never a release-check result**: a
required release check is either green, or the crossing does not happen.

`required_checks[]` is an **evidence source — never deferrable.**

**Amendment (D-AUDRS-462, appended 2026-07-14 — supersedes one clause of D-AUDRS-456, banked row NOT
edited):** check ② chained only **four** `journey/bin` gates (coverage · persona-journeys · map lint ·
persona coverage), omitting **`check-doc-format.sh`**. That is not a fact difference — this bundle's
own `sh journey/bin/check-doc-format.sh docs/PRD.md docs/APP_FLOW.md --allow-unlinked` exits **0**
today. `--allow-unlinked` defers only `SCREEN_UNTOUCHED` / `UNLINKED_FEAT` / `UNLINKED_AFJ` to the
structured coverage-gap workflow (`JOURNEY_COVERAGE_GAPS.md`) — **every other doc-format structural
rule stays enforced.** Omitting the gate from `required_checks[]` would silently discard those
structural checks at the tag. Check ② is therefore **five** delivered `journey/bin` gates, and the
machine-block command for check ② below carries the appended
`&& sh journey/bin/check-doc-format.sh docs/PRD.md docs/APP_FLOW.md --allow-unlinked`. RightShip's
sibling runbook already chains this fifth gate; this amendment brings Audit into parity for the
same reason.

---

## 6. Migration (D-AUDRS-457)

**Source of truth: `docs/MIGRATION.md` (post-fork).** The owner brief's pre-fork §4.1 draft is
**superseded by §6.0** and is not used.

### 6.1 Tooling

**Django 5.2.7 `managed=True` migrations** inside the **existing `inspection` app** (the audit code is
the `inspection/audit/` sub-package — `TECH_STACK.md §1/§2`, `BACKEND_STRUCTURE.md §2`).

- **ADDITIVE ONLY.** Zero `ALTER`/`DROP` against **any** shared legacy table — `psc_*`, `HRM501`,
  `VesselData` (the 9 protected tables of `MIGRATION.md §10`).
- **Approved shared-table mutation exception list: `[]` — EMPTY** (D-AUDRS-290/299③). Audit claims
  **no** exception and none may be added without a new owner ruling. **Never-waivable.**
- **This runbook PROHIBITS shared-table DDL; it prescribes none.** No step below emits schema DDL
  against a protected table, in either direction.
- Seeds load through the **idempotent** `inspection/audit/seeds/` runner (`BACKEND_STRUCTURE.md §13`,
  FK order per `MIGRATION.md §5`).

### 6.2 Forward — exact, fail-fast (`&&` chain; the machine block carries it verbatim)

Run from the `VimsWithSafety` repo root **at the release tag**, inside the deployment's Python
environment. **The environment wrapper — host, identity, `DJANGO_SETTINGS_MODULE`, DB credentials — is
owed by KSM India under D-AUDRS-453 (`closure_data` ②③④) and is deliberately NOT invented here.**

| # | Command | What it proves / does |
|---|---|---|
| 0 | `python manage.py showmigrations inspection > checks/reports/audit-migrations-pre.txt` | Records **`PRE_AUDIT_MIGRATION`** — the last applied `inspection` migration before this release. **This is the reverse target of §6.3; capture it before you need it.** |
| 1 | `python manage.py audit_schema_fingerprint --capture pre --out checks/reports/audit-fingerprint-pre.json` | **Pre-migration schema fingerprint** of the 9 protected tables (`sys.columns` + `sys.check_constraints` + `sys.indexes`) — D-AUDRS-290, `MIGRATION.md §10`. |
| 2 | `python manage.py audit_assert_no_car_check_constraint` | **D-AUDRS-294 — P0, fail-closed.** `psc_car` must carry **0** CHECK constraints. **If one IS found: the build FAILS `BLOCKED`, the crossing stops, and Prince is consulted. The migration MUST NOT self-authorize a schema change.** |
| 3 | `python manage.py audit_legacy_discovery_probe --out checks/reports/audit-legacy-discovery.json` | **READ-ONLY** pre-deploy discovery: `SELECT COUNT(*) FROM psc_inspection WHERE inspection_type IN ('AUDIT','RS')` (D-AUDRS-291; verified **0** on the restored snapshot — production may drift, so it is still run). |
| 4 | `python manage.py migrate inspection` | Creates the **44 Audit-owned tables** + indexes/constraints, including `aud_master_qual_body`. The `CARStatus` **`choices`** extension emits a Django `AlterField` that generates **no SQL** (D-AUDRS-289). |
| 5 | `python manage.py audit_verify_pk_standard` | **PK-standard verification** (D-AUDRS-137/271/299②): every Audit-owned table has `id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID()`; `INT IDENTITY` anywhere = FAIL. **Any violation FAILS the build.** Sole exception: `char(32)` **FK columns** to legacy `psc_*` tables — never a new table's `id` PK. |
| 6 | `python manage.py audit_legacy_tag_load` | Conditional on step 3. Writes **only** `audit_legacy_inspection_tag` rows — **never a write of any kind to `psc_inspection`** (D-AUDRS-288/291). No-op when the probe returned 0. Idempotent (unique index on `psc_inspection_id`). |
| 7 | `python manage.py load_audit_seeds` | Idempotent seed load, FK order per `MIGRATION.md §5`. Regulatory-source seeds load **only after human review** (D-AUDRS-098/267). |
| 8 | `python manage.py audit_schema_fingerprint --capture post --compare checks/reports/audit-fingerprint-pre.json` | **Post-migration fingerprint compare. `pre == post` MUST hold over the 9 protected tables. Any difference FAILS — never-waivable, no override.** |

> **⚠ Gate-author law (D-AUDRS-290, `MIGRATION.md §10.3`) — load-bearing.** The fingerprint gate asserts
> on the **DATABASE**, **never on migration-file text**. A `choices`-only change (D-AUDRS-289)
> legitimately emits an `AlterField` operation that generates **no SQL**; a grep over migration files
> would **false-positive and block a fully compliant build**. Assert on the fingerprint. Always.

**Management-command names are RELEASE LAW** (D-AUDRS-457): `audit_schema_fingerprint`,
`audit_assert_no_car_check_constraint`, `audit_legacy_discovery_probe`, `audit_verify_pk_standard`,
`audit_legacy_tag_load`, `load_audit_seeds`, `audit_verify_tables`, `audit_verify_seed_counts`,
`audit_cutover_smoke`, `audit_psc_regression_probe`, `audit_data_reset`. **Phase 0 MUST implement them
under exactly these names.** They are **specified here, not observed** — no claim is made that they
exist in the repo today.

### 6.3 Reverse / recovery (`MIGRATION.md §6`)

**Ordering rule, absolute: any data reset occurs BEFORE object removal — never the reverse.**

**Case A — BEFORE production Audit data exists.** Explicitly tested reverse, **Audit-owned objects
only**:

```
python manage.py audit_data_reset --confirm && python manage.py migrate inspection <PRE_AUDIT_MIGRATION>
```

1. **Data reset first** — clears Audit-owned tables (including `audit_legacy_inspection_tag`) and
   reverses the seed loads.
2. **Then object removal** — Django reverses the Audit migrations back to `<PRE_AUDIT_MIGRATION>`
   (captured by forward step 0), removing the **Audit-owned** tables and indexes.
3. The `CARStatus` `choices` extension reverts **with the application code** — no SQL was ever emitted,
   so there is nothing to migrate back (D-AUDRS-289).

**Case B — AFTER production Audit data exists.** **Rollback = redeploy the previous module tag (§7).**
The additive, backward-compatible Audit-owned schema **REMAINS IN PLACE**. **Schema reversal is NEVER
automatically triggered by a deployment rollback, and production Audit data is NEVER destructively
dropped as an automatic application rollback.** Corrections go through **forward-fix migrations**; a DB
restore is a **separate, human-authorized** action.

**Because the migration performs no DDL and no writes against any shared legacy table, rollback can
never touch `psc_*`, `HRM501`, or `VesselData` in either direction.** There is no `legacy` column to
remove and no migration-time `UPDATE` to reverse — the classification lives in the Audit-owned
`audit_legacy_inspection_tag` (D-AUDRS-288).

**Confirm the reverse path is available BEFORE deploy** (`Release.txt` migration ceremony): read the
command, confirm it runs against the migrated state. Never discover you cannot roll back after you
already need to.

### 6.4 Verify probes (`migration.verify_probes[]`)

Run **every** probe after the forward migration. A probe that does not pass **is the signal a failed
migration must produce** — if one fails, execute the reverse path **before stopping**, and never
proceed to authorization.

| # | Probe | Proves |
|---|---|---|
| 1 | `python manage.py audit_verify_tables` | Every expected **Audit-owned table + its constraints/indexes** exists (44 tables incl. `audit_legacy_inspection_tag` and `aud_master_qual_body`; `DATA_MODEL.md §12`). |
| 2 | `python manage.py audit_verify_pk_standard` | **Module PK compliance** — `UNIQUEIDENTIFIER` + `NEWSEQUENTIALID()` (D-AUDRS-137/271). |
| 3 | `python manage.py audit_schema_fingerprint --capture post --compare checks/reports/audit-fingerprint-pre.json --exceptions-must-be-empty` | **Exactly the approved legacy exceptions — and the list is EMPTY.** i.e. **zero shared-table mutation** across the 9 protected tables (D-AUDRS-290/299③). |
| 4 | `python manage.py audit_verify_seed_counts --provenance docs/SEEDS_PROVENANCE.md` | **Seed/provenance counts** match `SEEDS_PROVENANCE.md`. |
| 5 | `python manage.py audit_cutover_smoke` | **Cutover smoke** — an internal audit can be **registered → submitted → DPA-closed**, and its **NC reaches `LEAD_AUDITOR_CLOSED`** (`MIGRATION.md §8`). |
| 6 | `python manage.py audit_psc_regression_probe` | **Existing PSC and CAR flows healthy** — the PSC lifecycle, the CAR state machine and `/api/psc/health/` are unaffected (`TEST_PLAN.md §16`). |

---

## 7. Rollback (D-AUDRS-458)

**Strategy: redeploy the previous module tag.** The additive, backward-compatible Audit-owned schema
**remains in place**. **Schema reversal is never automatically triggered by a deployment rollback.**

### 7.1 Triggers — any ONE fires a rollback (owner brief §3.4, verbatim)

1. A required post-deploy probe fails.
2. `/api/psc/health/` is down or unhealthy past the banked retry window.
3. The module cutover smoke fails.
4. Existing PSC/CAR behaviour regresses.
5. Vessel scoping / authorization / state guards regress.
6. Data corruption or integrity failure — partial writes, forbidden state transitions, uniqueness
   violations, broken references, unexpected legacy-data mutation.
7. A newly introduced **unwaived Critical** security defect attributable to the release.
8. A newly introduced **High** defect that is remotely exploitable, crosses an authorization /
   vessel-isolation boundary, exposes secrets/PII, or cannot be immediately contained.

### 7.2 Timing (owner brief §3.4, verbatim)

- **Within 10 minutes of confirmation** — halt further deployment activity · declare rollback ·
  identify the previous tag.
- **Within 30 minutes** — redeploy the previous tag · verify health · run the **shared PSC/CAR smoke** ·
  run the **affected module smoke** · record **`ROLLED_BACK`**.

### 7.3 Procedure

1. Halt. Declare. Identify the previous module tag `vims-audit-v<previous>`.
2. **Redeploy the previous tag** using `deploy.method` — **the exact command rides D-AUDRS-453
   (`closure_data` ⑦)**.
3. Verify `/api/psc/health/`.
4. Run the shared PSC/CAR smoke — `sh checks/release/psc-car-regression.sh`.
5. Run the module smoke — `python manage.py audit_cutover_smoke`.
6. Record **`result: ROLLED_BACK`** in `RELEASE.md`; the trusted job attests it.

**A rollback is the ceremony working as designed — not a failed ceremony.** Both outcomes
(`RELEASED`, `ROLLED_BACK`) proceed to the record and the attestation; only the `result` field differs.

---

## 8. Attestation & evidence (D-AUDRS-455)

| Field | Value |
|---|---|
| `attestation.ref` | **`refs/heads/release-evidence`** — protected, append-only |
| `attestation.location` | **`release-evidence/<tag>/`** — e.g. `release-evidence/vims-audit-v1.0.0/` |
| DRY namespace | `release-evidence/dry/<dry-tag>/` (§9) |

**Every published evidence directory contains at least:**

- `RELEASE_ATTESTATION.json`
- `RELEASE.md`
- `REVIEW.md`
- `checks/reports/release-preflight.json`
- the **required-check reports, or their SHA-256 hashes**

**Controls:**

- **Only trusted CI may publish.**
- **No force-push.**
- **A published tag directory is immutable** — never modified, never deleted.
- **Corrections** are published under **`<tag>/corrections/<n>/`**, and **every correction records the
  SHA-256 hash of the attestation it supersedes**. The original stays exactly as published.
- **An existing tag with NO attestation means the trusted job did not complete and must be re-run** —
  never that it ran to completion and hid a failure.

Attestation location and ref are **trust roots — never deferrable**.

Independent audit, from outside CI:
`sh release/bin/verify-release-attestation.sh EVIDENCE_DIR PROJECT_ROOT TAG`.

---

## 9. Handoff & the DRY crossing (D-AUDRS-459)

**`handoff.part_a_done: false`.**

**No backfilling.** Existing VIMS deployments are **historical facts only** — **no tags, no
`RELEASE.md`, no attestations are backfilled onto pre-protocol deployments.** The first production
attestation must correspond to a **genuinely new module release under this runbook**.

**Before KSM India's first production release, execute a COMPLETE DRY crossing** against a **local bare
repo + non-production target**. **A failed DRY crossing BLOCKS the first production crossing.**

**DRY scope must prove all 13:**

1. Release preflight + stamp verification
2. Module-scoped tag derivation
3. Migration forward command
4. Migration verification probes
5. Reverse / restore-point recovery
6. Human-authorization pause
7. Deployment simulation
8. Post-deploy probes
9. Rollback trigger + previous-tag redeployment
10. Evidence staging
11. Trusted attestation publication
12. Independent attestation verification
13. Append-only correction behaviour

**DRY namespace (NEVER a production release):** tag **`vims-audit-dry-v0.0.1`**, evidence
**`release-evidence/dry/<dry-tag>/`**.

**One-time handoff semantics.** The DRY crossing may produce DRY evidence and a DRY attestation, but it
**does NOT set `handoff.part_a_done = true`** and it **does NOT run Step 5 Part A** as production
activation. **The first genuine production crossing** — `RELEASED` or `ROLLED_BACK`, durably attested in
the **production** namespace — **runs Step 5 Part A exactly once.** Thereafter `handoff.part_a_done`
changes **only** through the governed release-law change process (Tier-2 CR) — **never by silently
editing this runbook**. Later crossings observe `part_a_done = true` and do not repeat Part A.

---

## 10. The crossing ceremony — order of operations

Executed per the framework's `Release.txt` (paste it, this runbook, `REVIEW.md`, and the `progress.txt`
`QUALITY: PASS` citation into a fresh session — nothing else).

| Step | Action | Gate |
|---|---|---|
| 0 | `sh release/bin/release-preflight.sh . <VERSION>` | **`PASS` continues. `FAIL` = no crossing (no override). `BLOCKED` = no crossing either — and it cannot be fixed from here.** |
| 1 | Migration ceremony — run `migration.forward`, run **every** `verify_probes` command, **confirm the reverse path is available** | A failed probe ⇒ execute the reverse path **before stopping**. Never leave a failed probe un-rolled-back. |
| 2 | **Human deploy authorization** — present preflight + migration results to **Prince** | Only the authorizer may approve. Declined ⇒ reverse the migration, then record the abort. |
| 3 | Cut the tag (derived from `tag_format` + raw `VERSION`), push it, **deploy ONLY from the tag** via `deploy.method` | Never from a working branch, never from an untagged commit. |
| 4 | **Post-deploy probes** — deploy-specific verification that the LIVE system serves this release | Pass ⇒ `RELEASED`. Fail ⇒ rollback trigger ① ⇒ §7 ⇒ `ROLLED_BACK`. **Migration probes alone are never deploy verification.** |
| 5 | Write root `RELEASE.md` (release-record schema: version · tag · authorized_by · result · migration_outcome · probes_outcome · evidence) | `result` is `RELEASED` or `ROLLED_BACK`. **Never `ABORTED`** — that is attestation-only. |
| 6 | Stage evidence (`RELEASE.md`, `REVIEW.md`, `checks/reports/release-preflight.json`) to `release-staging/<tag>` | Claims, not authority — the trusted job hash-binds and re-derives them. |
| 7 | Trusted CI job — `release/bin/release-attest.sh` — re-executes `required_checks[]` at the tag, recomputes the tree hash, publishes `RELEASE_ATTESTATION.json` to `refs/heads/release-evidence` | Append-only. A failed trusted re-run still publishes a **failing** attestation (`ABORTED` + reason codes). Silence is never an outcome once the tag exists. |
| 8 | **First crossing only** — run Step 5 Part A, then flip `handoff.part_a_done` via the Tier-2 CR path | Never inline (§9). |

**Step 0 is currently `BLOCKED`.** The ceremony above cannot start until D-AUDRS-453 closes.

---

## 11. Honest current state of this bundle (D-AUDRS-460/461)

**Run against the delivered/vendored scripts, stock `/bin/sh`, at this commit:**

- `sh release/bin/lint-release-runbook.sh .` → **`VERDICT: DEFERRED lint-release-runbook
  deferred_fields=deploy.method reason_codes=DEFERRAL_OPEN`** (exit 0). **Never `PASS`** while the
  deferral is open — by design.
- `sh release/bin/release-preflight.sh . 1.0.0` → **`VERDICT: BLOCKED`** (exit 1), reason codes
  including **`DEFERRAL_OPEN`**. `BLOCKED` **dominates** every other reason code: fixing the others
  cannot turn a blocked crossing into a passing one — **only closing the deferral can.**

**The other reason codes preflight reports here are true, and are not defects of this runbook** — they
are the honest state of a **documentation bundle that contains no application code**:

| Reason code | Why it is true here | Register |
|---|---|---|
| `REVIEW_MISSING` | No `REVIEW.md` exists. A pre-ship review must be run in a **fresh session** (generator ≠ verifier). | `docs/BLOCKERS.md` **PSB-2** |
| `STAMP_UNVERIFIED` | `progress.txt` carries **no `QUALITY: PASS stamp=<12> tree=<12>` phase-exit citation** — and **must not**: 10 code-dependent lenses report `NOT_APPLICABLE_YET` because no code exists, and **`NOT_APPLICABLE_YET` can never satisfy a phase exit**. Fabricating a citation to green the preflight is exactly the lie this layer forbids. | `docs/BLOCKERS.md` **PSB-1** note |
| `CHECK_FAILED` | Required checks 3–7 (§5) are **shipped fail-closed** and exit non-zero until the build wires them to real suites. **Correct behaviour** — a release may not cross on an unrun check. | D-AUDRS-456 |

**The crossing happens in the `VimsWithSafety` build repo after KLOSS Step 3 lands the code** — not in
this handover bundle. This runbook is the law it will execute.

**`docs/BLOCKERS.md` PSB-3 is now split, honestly:** the *runbook-missing* half is
**RESOLVED-BY-GENERATION**; the *crossing* half remains **OPEN and BLOCKED** on D-AUDRS-453 (and PSB-2
independently blocks it). **No release may be claimed.**

---

## 12. RELEASE-MACHINE-BLOCK

> **Why this block is in the LEGACY (no `schema_version` / no `decisions[]`) form — a FRAMEWORK
> defect, recorded not worked around silently.** See `docs/BLOCKERS.md` **OQ-2**.
>
> The delivered linter at framework commit `f908204` makes **origin provenance** and a **structured
> deferral** mutually exclusive in the same runbook. Its near-miss scan flags **any** string anywhere
> outside the `deferred[]` register that begins (case-insensitively) with `deferred` and is not the
> exact sentinel — and the canonical origin enum's own value **`"origin": "DEFERRED"`** (the enum is
> `USER | PROPOSED | DEFERRED`, per `release/contract/runbook-schema.json`) is exactly such a string.
> A **correctly backed** deferral therefore lints **`FAIL … DEFERRAL_MALFORMED`** the moment the
> runbook also claims provenance.
>
> **Reproduced minimally** against the delivered script (a schema-conformant 1-decision runbook,
> `deploy.method: "DEFERRED:D-301"`, a complete `deferred[]` record, `decisions: [{"id":"D-301",
> "origin":"DEFERRED"}]`) → `VERDICT: FAIL … reason_codes=DEFERRAL_MALFORMED`. The framework's own
> `release/tests/origin-provenance_test.sh` only ever exercises the **unbacked** DEFERRED origin
> (line 114, expecting `DEFERRED_ORIGIN_UNBACKED`); the **backed** case — the one this module needs,
> and the one `DEFERRED_ORIGIN_UNBACKED` exists to make legal — is **never tested and is structurally
> unreachable**.
>
> **The three ways out, and why only one is honest.** ① Patch the vendored linter — **forbidden**
> (owner brief §6.5 Control 1: the vendored gates stay byte-identical to `f908204`; framework law
> changes need owner authorization). ② Declare D-AUDRS-453's origin as `USER` to slip past the scan —
> **a quiet falsification**: that decision's origin *is* a deferral, and mislabelling it to green a
> linter is the exact class of lie this layer exists to prevent. ③ **Emit the LEGACY block** — the
> optional provenance projection is omitted, the linter classifies the artifact as `LEGACY` and prints
> the **non-blocking** `NOTE: ORIGIN_PROVENANCE_ABSENT` on stderr, and the **verdict is the honest
> `DEFERRED`**. **③ is taken.** It is the same deliberate posture this bundle's `QUALITY-MACHINE-BLOCK`
> already holds (`progress.txt`, 2026-07-14).
>
> **Nothing is lost that matters:** all **12** Domain 14 decisions (D-AUDRS-450..461) are listed in
> `decision_ids[]`, and every origin is recorded in **SSOT §23.2** — the record of authority. `RightShip's runbook will hit
> this identically.` The framework fix is a one-line exclusion in the near-miss path filter
> (`decisions[].origin` is not a law field and must not be scanned) — **owner-authorized, upstream,
> never here.**

**Amendment (D-AUDRS-463, appended 2026-07-14 — annotation only, no clause of D-AUDRS-461 superseded,
banked row NOT edited):** the framework defect described above is now **FIXED UPSTREAM**, at framework
commit `aeccc3c` (fix at `68d5afd`, regression test at `cdedc72`; re-vendored into this bundle
wholesale, byte-identical). Verified against the delivered script:
`sh release/tests/deferral-origin-collision_test.sh` → **61/61 assertions pass, 0 failures** — a
backed deferral plus `decisions[].origin` provenance now lints the honest `DEFERRED`, and every
trust-root / near-miss guard the original hardening established is provably unweakened. **This block
does not change as a result.** The **LEGACY form above remains valid and non-blocking BY DESIGN**, not
as a stopgap awaiting a fix — the gate contract passes a `LEGACY` block additively regardless of
whether provenance is *possible*, only whether it is *present*. Adopting `schema_version: 2` +
`decisions[]` provenance in this block is therefore **optional future work, required by no gate, and
not undertaken here** (out of scope — see `docs/BLOCKERS.md` OQ-2, now CLOSED).

<!-- RELEASE-MACHINE-BLOCK BEGIN -->
```json
{
  "decision_ids": ["D-AUDRS-450","D-AUDRS-451","D-AUDRS-452","D-AUDRS-453","D-AUDRS-454","D-AUDRS-455","D-AUDRS-456","D-AUDRS-457","D-AUDRS-458","D-AUDRS-459","D-AUDRS-460","D-AUDRS-461","D-AUDRS-462"],
  "versioning": { "scheme": "semver", "tag_format": "vims-audit-v<version>" },
  "deploy": {
    "target": "Existing VIMS production deployment (shared VimsWithSafety application) — extended IN PLACE inside the existing VIMS application (D-AUDRS-273/001): no new application server, host or region; shared ksm_cms_live SQL Server database (D-AUDRS-135); existing cron infrastructure for the audit background jobs. KSM India owns execution.",
    "method": "DEFERRED:D-AUDRS-453"
  },
  "approval": { "authorizer": "Prince (DPA — final freeze authority, D-AUDRS-285). KSM India executes; only Prince authorizes the crossing." },
  "attestation": { "location": "release-evidence/<tag>/", "ref": "refs/heads/release-evidence" },
  "required_checks": [
    "sh checks/quality-gate.sh",
    "sh journey/bin/check-journey-coverage.sh docs/PRD.md docs/APP_FLOW.md JOURNEY_MAP.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md && sh journey/bin/check-persona-journeys.sh JOURNEY_MAP.md ssot/VIMS-AUDIT-RS-MODULE-SSOT.md && sh journey/bin/lint-journey-map.sh JOURNEY_MAP.md && sh journey/bin/check-persona-coverage.sh docs/PRD.md ssot/VIMS-AUDIT-RS-MODULE-SSOT.md JOURNEY_MAP.md PERSONA_COVERAGE_GAPS.md && sh journey/bin/check-doc-format.sh docs/PRD.md docs/APP_FLOW.md --allow-unlinked",
    "sh checks/release/backend-tests.sh",
    "sh checks/release/frontend-tests.sh",
    "sh checks/release/rbac-grid-test.sh",
    "sh checks/release/psc-car-regression.sh",
    "sh checks/release/shared-code-diff.sh"
  ],
  "migration": {
    "tooling": "Django 5.2.7 managed=True migrations in the existing `inspection` app (audit code = the inspection/audit/ sub-package; TECH_STACK §1/§2). ADDITIVE ONLY — zero ALTER/DROP against any shared legacy table (psc_*, HRM501, VesselData); approved shared-table mutation exception list is EMPTY (D-AUDRS-290/299③, never-waivable). Seeds load via the idempotent inspection/audit/seeds/ runner (BACKEND_STRUCTURE §13). Environment wrapper (host, identity, DJANGO_SETTINGS_MODULE, DB credentials) is owed by KSM India under D-AUDRS-453.",
    "forward": "python manage.py showmigrations inspection > checks/reports/audit-migrations-pre.txt && python manage.py audit_schema_fingerprint --capture pre --out checks/reports/audit-fingerprint-pre.json && python manage.py audit_assert_no_car_check_constraint && python manage.py audit_legacy_discovery_probe --out checks/reports/audit-legacy-discovery.json && python manage.py migrate inspection && python manage.py audit_verify_pk_standard && python manage.py audit_legacy_tag_load && python manage.py load_audit_seeds && python manage.py audit_schema_fingerprint --capture post --compare checks/reports/audit-fingerprint-pre.json",
    "reverse": "python manage.py audit_data_reset --confirm && python manage.py migrate inspection <PRE_AUDIT_MIGRATION>",
    "verify_probes": [
      "python manage.py audit_verify_tables",
      "python manage.py audit_verify_pk_standard",
      "python manage.py audit_schema_fingerprint --capture post --compare checks/reports/audit-fingerprint-pre.json --exceptions-must-be-empty",
      "python manage.py audit_verify_seed_counts --provenance docs/SEEDS_PROVENANCE.md",
      "python manage.py audit_cutover_smoke",
      "python manage.py audit_psc_regression_probe"
    ]
  },
  "rollback": {
    "triggers": [
      "a required post-deploy probe fails",
      "/api/psc/health/ is down or unhealthy past the banked retry window",
      "the module cutover smoke fails",
      "existing PSC/CAR behavior regresses",
      "vessel scoping / authorization / state guards regress",
      "data corruption or integrity failure (partial writes, forbidden state transitions, uniqueness violations, broken references, unexpected legacy-data mutation)",
      "a newly introduced unwaived Critical security defect attributable to the release",
      "a newly introduced High defect that is remotely exploitable, crosses an authorization/vessel-isolation boundary, exposes secrets/PII, or cannot be immediately contained"
    ],
    "procedure": "Redeploy the previous module tag — RELEASE_RUNBOOK.md §7. Within 10 min of confirmation: halt deployment activity, declare rollback, identify the previous tag vims-audit-v<previous>. Within 30 min: redeploy that tag via deploy.method (exact command rides D-AUDRS-453 closure_data ⑦), verify /api/psc/health/, run the shared PSC/CAR smoke (sh checks/release/psc-car-regression.sh), run the module smoke (python manage.py audit_cutover_smoke), and record result: ROLLED_BACK in RELEASE.md. The additive Audit-owned schema REMAINS IN PLACE — schema reversal is never automatically triggered by a deployment rollback, and production Audit data is never destructively dropped as an automatic application rollback (D-AUDRS-458; MIGRATION.md §6 Case B)."
  },
  "handoff": { "part_a_done": false },
  "deferred": [
    {
      "field": "deploy.method",
      "decision_id": "D-AUDRS-453",
      "reason": "KSM India owns deployment execution and has not yet supplied the executable procedure for this module. The known facts are banked in deploy.target (in-place inside the existing VIMS application, shared ksm_cms_live DB, existing cron infrastructure, no new servers or region). The executable method is NOT among them and is not invented: generic wording would lint as a settled value and let the crossing run unblocked. Release blocker — NOT a build-handover blocker (owner brief §3.2/§6.3).",
      "owner": "KSM India (execution owner) supplies the facts; Prince (DPA) authorizes the resulting release-law change via the Tier-2 CR path — the sentinel and this register entry are removed together, never inline at ceremony time.",
      "closure_data": [
        "exact deployment command or numbered procedure",
        "execution environment and identity",
        "required credential/secret references",
        "migration command (the environment-level invocation of migration.forward)",
        "success signal",
        "failure signal",
        "previous-tag redeploy/rollback command"
      ]
    }
  ]
}
```
<!-- RELEASE-MACHINE-BLOCK END -->
