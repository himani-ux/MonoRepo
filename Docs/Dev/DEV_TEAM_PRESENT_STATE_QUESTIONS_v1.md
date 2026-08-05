# Present-State Discovery — Questions to Answer Before v2


## Why this document exists

The review request asks a great many questions about the **proposed** vessel system. On re-reading, it asks very few about the **current** one. That is a flaw in the review, not just in the plan, and this document corrects it.

The clearest example: the review demands committed p95 response times onboard (≤1.5 s to open a list page, ≤2 s to save). **Those numbers are meaningless without a shore baseline.** If a requisition register takes four seconds in production today, we would be demanding the vessel mini PC outperform a dedicated app server — which is not going to happen, and would sink the programme on a target we invented. **Question A1 below therefore takes precedence over the entire performance section of the review request.**

More generally: the vessel design is a set of decisions about how to change an existing system. Several of those decisions currently rest on assumptions about the present state that nobody has written down and confirmed.

**Please answer these before, or alongside, v2.** Where a question has no owner in the dev team, say who does own it.

---

## A. How the system performs today (answer these first)

**A1. What are the current p95 response times in production**, for the same interactions the review request lists — login, open a register/list, open a record, save, search, generate a report? Measured, not estimated.

**A2. Are these times measured from a shore office, or from a vessel over satellite?** Both, ideally. The gap between them is the actual size of the problem we are solving.

**A3. What is the slowest screen in each module today, and why?**

**A4. Are there known performance complaints from vessel users today?** What are they, and are they connectivity, application, or database?

**A5. What is the current query count and slowest query per heavy screen?** If you have not profiled, say so.

**A6. What hardware does production run on today** — cores, RAM, storage type — for the Linux app server and the Windows SQL Server separately? This is the number the NUC will be compared against.

**Note:** if the honest answer to A1 is "we have never measured," that is an acceptable answer, but then measuring it becomes the first task, because every performance target in the vessel design depends on it.

---

## B. Who actually uses what, and where

**B1. For each module (VIMS, CMS, Purchase, PMS, SMS), what proportion of usage is vessel-side versus shore-side?** Sessions, users, or transactions — whichever you can pull.

**B2. How many concurrent users are there on a single vessel at peak?** This drives NUC sizing more than anything else, and it is not stated anywhere in the plan.

**B3. How many distinct users per vessel in total?** Crew rotate; is the user population stable or churning?

**B4. Which specific workflows do crew perform onboard today?** A ranked list by frequency, per module. Phasing should follow this list, not our guess.

**B5. Which workflows are shore-only and will never need to work offline?** Equally important — it bounds the scope.

**B6. Are there workflows where vessel and shore genuinely edit the same record today?** This is the question that determines how much of the plan's conflict machinery we actually need. The plan assumes the answer is "few." Please confirm with evidence rather than assumption.

---

## C. What crew do today when connectivity is poor

**C1. What actually happens today when a vessel loses internet mid-task?** Walk through one real example.

**C2. Do crew currently work around outages** — paper forms, Excel, WhatsApp/email to the office, waiting until morning? Which, and how often?

**C3. How long are typical outages today, and how frequent?** If this has never been measured, how could we measure it over the next month?

**C4. How much rework does an outage cause today?** Lost form data, re-keying, duplicate entries?

**C5. What is the actual business consequence of an outage?** Delayed requisition, missed maintenance window, deferred inspection record, or just inconvenience? This is the business case, and it is currently asserted rather than evidenced.

**C6. Have crew asked for offline capability, or is this a shore-side initiative?** An honest answer here matters for adoption planning.

---

## D. Database reality

**D1. How many databases are there, actually?** The plan records "a single shared database" as a **confirmed fact**. The evidence contradicts it:

- Purchase → `ksm_marine_live` (`backend/config/settings/db_config.py`)
- CMS → `Ksm_marine_live` (`Cms.Web/Web.config`)
- **VIMS → `ksm_cms_live`** (`VIMS-Reporting-Module/CLAUDE.md:21`)

Please confirm the real topology for all five modules **with connection strings**, and tell us whether `ksm_cms_live` is a separate production database, a reporting replica, or stale documentation. If there is more than one database, the sync scope, checkpoint model, cross-module atomic groups and the rebaseline unit all change.

**D2. What else writes to this database besides the five applications?** Specifically: SSRS or Crystal jobs, scheduled ETL, Excel or Access tools, manual DBA scripts, third-party integrations, imports. **Any writer that bypasses the application will bypass the outbox, and its changes will never sync.** This is the single most dangerous unknown in the whole design.

**D3. Table ownership by naming family.** Of 295 tables, 182 fall into six recognisable families — `master_` 61, `pur_` 60, `psc_` 18, `django_` 13, `msc_` 12, `mapping_` 12 — and 45 have no underscore at all (`appmstr_Users`-style legacy names and similar). That leaves roughly 68 tables in neither group. **Who owns the tables outside the six families, and which applications read and write them?** These are the ones most likely to have no clear owner, and therefore the ones most likely to break a per-table ownership model.

**D4. `django_*` and `auth_*` tables live in the shared production database.** Do Django migrations therefore run directly against `ksm_marine_live`? What is the current control on that?

**D5. There are `temp_`, `tmp_` and `tbl_` prefixed tables in the live database.** Are these in active use, abandoned, or genuinely temporary? Are any of them in the sync scope?

**D6. Row counts and growth rate for the twenty largest tables.** Not total DB size — the distribution, because it determines what a vessel actually needs to hold.

**D7. Which tables are genuinely vessel-scoped versus fleet-wide reference data?** A first-pass split, even rough.

**D8. Roughly fifteen tables appear to have no primary key.** Which are they, are they in scope, and can they be given one?

**D9. What is the current SQL Server edition, CU level, recovery model and collation in production?**

**D10. Is there any existing replication, ETL, log shipping, or sync in place today?** The VIMS handover folder contains a `sql_source` directory — what is that?

**D11. How much data would a single vessel actually need locally?** Full history, or a working window? This determines whether SQL Express (10 GB limit) is viable and could remove the largest licensing line from the programme.

---

## E. Current operations

**E1. How are the applications deployed and updated today?** Manual, scripted, CI/CD? How long does a release take, and how often do you ship?

**E2. What is the current backup practice** — actual schedule, actual destination, and **when was the last successful restore test?**

**E3. What monitoring exists today?** What alerts fire, to whom?

**E4. What breaks most often in production today?** The incident history is the single best predictor of what will break onboard, unattended, at sea.

**E5. What is the current support model** — hours, escalation path, who is on call?

**E6. How do you currently support a vessel user with a problem?** Remote access, phone, email? What is the typical resolution time?

**E7. Have you ever deployed anything to a vessel before?** If so, what went wrong?

---

## F. Vessel-side infrastructure that already exists

**F1. What IT infrastructure is already on a typical vessel?** Servers, NAS, switches, Wi-Fi, workstations — and who owns and maintains it?

**F2. Is there an existing vessel LAN the mini PC would join, and what condition is it in?**

**F3. What devices will crew actually use** — fixed bridge/ECR workstations, personal laptops, tablets? Browser and OS versions? This affects the PWA and the front-end asset strategy.

**F4. What is the current satellite setup** — provider, bandwidth, data cap, and is it shared with crew welfare traffic? Competing with crew streaming is a real scheduling constraint.

**F5. Is there already a vessel-side file share or NAS** that attachments could use, or does the NUC provide it?

**F6. Power quality and UPS** — what exists today, and has anything been lost to power events?

**F7. Who physically has access to the space where the NUC would live?**

---

## G. Offline and sync work already built

**G1. What is the current status of the React Vessel PWA offline layer** in `frontend/src/pwa/` — in production, in testing, or shelved?

**G2. If it is live, how many vessels and users are using it, and how well is it working?**

**G3. Has anyone observed duplicate records created by its replay path?** Please check — the queue has no idempotency keys, so a lost response after a successful POST should produce a duplicate.

**G4. What drove that work originally, and why was it built client-side rather than server-side?** The answer likely contains requirements the vessel plan should inherit.

**G5. What did you learn from it?** `emergencyExport.ts` — dumping a stranded draft to Excel — suggests some real operational pain. What happened?

**G6. Is there similar offline work in VIMS, CMS, PMS or SMS?**

---

## H. People and change

**H1. Who onboard is the most technical person on a typical vessel, and what can we reasonably ask them to do?** This directly determines how the failure-recovery procedure must be written.

**H2. What is crew rotation frequency?** Anything requiring training has to survive full crew turnover.

**H3. What languages must crew-facing procedures and error messages be in?**

**H4. Who trains crew on these systems today, and how?**

**H5. Are there vessels that would be poor pilots** — old hardware, weak connectivity, resistant crew — and one that would be a good pilot?

---

## I. Constraints we may not know about

**I1. Are there flag-state, classification-society or ISM cyber requirements** that apply to installing a server aboard? IACS UR E26/E27 may be relevant depending on vessel contract dates.

**I2. Are there charterer, owner or client contractual constraints** on where vessel data is stored or processed?

**I3. Any data-residency, privacy or crew-data rules** affecting replicating a user table containing password hashes to every vessel?

**I4. Are any of these applications subject to external audit** where an auditor would need to see vessel-side records?

**I5. Is there anything else about the present system** — technical debt, known fragility, an in-flight project, a planned migration — that would materially change this design and has not surfaced yet? **Please treat this as an open invitation. It is better raised now than discovered in the pilot.**

---

## How to respond

- Answer inline, or in whatever format is easiest.
- **"We don't know" is an acceptable answer** — but pair it with how and when you would find out.
- **A1, B2, C1 and D2 are the four that matter most.** If time is short, answer those.
- If any question rests on a wrong assumption about your system, say so. Parts of this review were built from reading the repository, and it is entirely possible I have misread something.

We would rather delay v2 by two weeks and build on confirmed facts than approve a design resting on assumptions.
