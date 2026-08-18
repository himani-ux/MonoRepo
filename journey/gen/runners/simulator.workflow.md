# Thin-runner contract — user-simulator engine (Increment 4)

The pipeline is deterministic at the edges and stochastic in the middle — and,
unlike the doc-derived (fan-out/persona) pipelines, has NO refuter stage: a
simulator candidate lands in `JOURNEY_INBOX.md` as `promotion_status:
PROPOSED`, and human triage (`journey-inbox-triage.sh`) is the ONLY filter
between a candidate and the canonical map. Two thin runners share the SAME
brain prompt and the SAME bundles; only the wrapper that invokes the model
differs — the sole portability-sensitive piece (spec §9).

## Pipeline

```
lint-personas.sh SSOT                                 # PREFLIGHT (model-free)
lint-test-surface.sh TEST_SURFACE                      # PREFLIGHT (model-free)
  -> simulator-gen-slice.sh SSOT TEST_SURFACE OUTDIR   # deterministic (sh/awk/jq); one bundle PER PERSONA;
                                                        #   injects APP_TARGET/APP_BUILD/RUNNER + inlines the schema
  -> for each bundle:  simulator-brain.md (model)      # frozen ## JOURNEY-CANDIDATE + field_sources + ## SIM-TRACE,
                                                        #   OR SIM-FAILED: <reason>, OR EMPTY-CANDIDATE
     -> journey-gen-check-candidate.sh --origin SIMULATOR (model-free)  # shared candidate-format gate
     -> runner-side SIM-TRACE re-verification (model-free)              # persona/app_build/runner/patience_budget
                                                                          #   MUST equal what the runner itself
                                                                          #   injected — never the model's echo
  -> deterministic assembly (model-free, NO model merge)                # runner assigns INBOX-<n> ids (append,
                                                                          #   next-free against the target inbox),
                                                                          #   forces origin/author_status/
                                                                          #   promotion_status, writes each raw
                                                                          #   candidate to transcripts/INBOX-<n>.
                                                                          #   transcript.md and injects that relpath
                                                                          #   as evidence[0]
  -> lint-journey-inbox.sh (model-free)                                 # gates the FULLY assembled/updated inbox
                                                                          #   BEFORE the temp->final rename
```

The live path requires `JOURNEY_RUNNER=<playwright|maestro|appium|pty|http|stub>`,
`SIM_APP_TARGET`, and `SIM_APP_BUILD` — ALL checked before any backend call, and
before the slicer even runs (house rule 6: runner-declared, never inferred).
`JOURNEY_TARGET_INBOX` (default `OUTDIR/JOURNEY_INBOX.md`) is append-only:
multiple simulator passes accumulate into the same file rather than
overwriting it.

## Guardrails (both runners MUST honor)

- **`RUN_LLM_GEN=1` gates every live model call.** With `RUN_LLM_GEN` unset the
  runner is a deterministic no-op and makes NO model or network call — default
  CI stays green and offline (house law: stochastic parts are never the gate,
  spec §3.3).
- The model is supplied by the operator, not hardcoded: the sh runner
  (`simulator-run.sh`) shells out to `$JOURNEY_GEN_BACKEND <prompt-file>
  <bundle-file>`; a Claude Workflow runner calls the model through its own
  agent step (with browser/mobile/pty tools as the actual "hands" driving the
  running app for a LIVE run). No vendor SDK is embedded in this repo.
- Output is ALWAYS staged to `JOURNEY_INBOX.md`, kept SEPARATE from
  `JOURNEY_MAP.md`. A candidate becomes canonical ONLY through a human
  `journey-inbox-triage.sh --approve` run — a SEPARATE, later invocation this
  runner never makes itself. **This runner never touches `JOURNEY_MAP.md` and
  never runs the triage gate.**
- **There is no refuter here.** The doc-derived pipelines (`fanout.workflow.md`)
  bind a refuter's review to a candidate hash because their candidates are
  DERIVED/PERSONA claims about document fidelity. A simulator candidate is a
  RUN RECORD (what a persona-faithful actor actually did against the running
  app), and its own `## SIM-TRACE` — runner-verified against the facts the
  runner itself injected — IS the fidelity check. Triage is the filter for
  simulator candidates, not a second model pass.
- Runtime truth (`ci_status`/`last_run`/`ci_run_id`/`ci_artifact`/
  `failure_summary`) is NEVER produced here. It lives only in the CI-owned
  ledger; this runner does not read or write it.
- **`covers:`/`flows:`/`test:` are triage-time placeholders, not this
  runner's job to resolve.** `covers:` is a SURFACE screen name (no
  FEAT-ID exists in a sim bundle), `flows:` is absent from the inbox
  schema (forced to `[]` only later, at promotion), and `test:` carries
  the literal `<n>` token — the full re-anchor law (screen-name ->
  FEAT-ID, optional AFJ re-anchor, `<n>` substitution) lives in
  `journey/docs/journey-inbox-format.md` §6.1, resolved by a human plus
  `journey-inbox-triage.sh` at promotion, never by this runner.

## The sh runner

`journey/gen/runners/simulator-run.sh` — see its header for the full
env/failure-mode contract. `RUN_LLM_GEN` unset → no-op; `RUN_LLM_GEN=1`
without `JOURNEY_GEN_BACKEND` → fail closed; `RUN_LLM_GEN=1` with a backend
(and `JOURNEY_RUNNER`/`SIM_APP_TARGET`/`SIM_APP_BUILD` all set) → the opt-in
live path above, staging to `JOURNEY_INBOX.md` and stopping (never triages,
never touches the map).

## The Claude Workflow JS runner (LIVE drive, operator-run, never CI)

A `Workflow` script that runs `simulator-gen-slice.sh`, then for each
per-persona bundle drives ONE agent turn through `simulator-brain.md` — but,
unlike the doc-derived pipelines' pure-text generation, this agent turn is
given ACTUAL hands: browser tools (Playwright MCP or equivalent) for a web
`TECH_STACK`, or the corresponding mobile/pty/HTTP driver named by the
bundle's `RUNNER:` line, so the model is genuinely driving the RUNNING app as
the persona, not narrating a plausible path from the TEST_SURFACE contract
alone. The workflow then runs `journey-gen-check-candidate.sh --origin
SIMULATOR` plus the same SIM-TRACE runner-side re-verification, assembles
deterministically, and gates with `lint-journey-inbox.sh` — same composed
gates as the sh runner, so the two can never disagree about what a valid
candidate looks like.

This path is **operator-run and opt-in, never CI**: browser/mobile-driving
agent turns are the textbook stochastic-discovery case the load-bearing
boundary in spec §3.3 exists for — an LLM actually clicking through a live
app in a CI pipeline is exactly the flakiness source that would get the whole
suite bypassed and eventually deleted. The simulator is a one-way PRODUCER of
candidates for a human to triage; it is never wired into a required check.
(Not built in this task; this is the contract it must satisfy.)
