# VIMS Safety Module — Lessons Learned

> Corrections-driven learning file. Reviewed at every session start, updated after every user correction or confirmed non-obvious win.
>
> **Numbering:** `L-###` (zero-padded, append-only — never renumber).
> **Format per entry:** What happened | Why | Rule that prevents recurrence.
> **Trigger for new entry:** (a) any user correction, (b) any confirmed non-obvious win worth preserving, (c) any cross-module contract drift caught in review.
>
> Seed entries L-001 / L-002 / L-003 capture the most load-bearing lessons from Sessions 1–5 interrogation; preserve them verbatim.

---

## L-001 — External reference packs can reshape locked specs
**What happened:** Round 21 reference pack (TapRoot, ABS RCA, IMO RCA guidance) surfaced 23 enhancements after Session 4 had already "closed" the V1 spec. Causal layering (Immediate/Intermediate/Root) was added on top of M-SCAT as a result.
**Why:** "Interrogation complete" is a state-in-time, not permanence. External references introduce patterns the original interrogation didn't probe.
**Rule:** Before docsuite generation, always run a final gap-analysis pass against any new reference material the user contributes. Do not treat spec close as immutable.

## L-002 — Paper-first means no scan upload
**What happened:** Initial SOI design assumed scanned-PDF upload after paper fieldwork.
**Why:** User clarified (D-GAP-E4) that paper is filed in ship SMS filing system — scan upload is duplicative and creates a second source of truth.
**Rule:** When a workflow is "paper-first," the system generates → user downloads → paper becomes authoritative → findings registered digitally via unique ID only. No upload column, no scan endpoint.

## L-003 — Role persists, person may change
**What happened:** Early drafts had "Acting-DPA" and "Acting-CO" concepts.
**Why:** D-GAP-A3/A4 locked that ranks are always staffed; the person in the role changes via normal crew rotation but the role itself is continuous.
**Rule:** No "Acting-*" concepts anywhere. No deputy chains. No MD-escalation logic. Use the timeline-extension procedure (D-GAP-B2) as the universal escape valve.

---

<!-- Append new L-### entries below as corrections occur. Never edit entries above; never renumber. -->
