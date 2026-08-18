# Thin-runner contract — doc-derived journey generation pipeline

The pipeline is deterministic at the edges and generative in the middle. The two
thin runners (a Claude Workflow JS runner and a `codex exec` sh runner) share the
SAME prompt assets and the SAME bundles; only the wrapper that invokes the model
differs. Neither runner promotes — promotion is a separate, human-gated step.

## Pipeline

```
check-doc-format.sh PRD APP_FLOW                     # PREFLIGHT: every doc violation at once (model-free)
  -> journey-gen-slice.sh SSOT PRD APP_FLOW OUTDIR   # deterministic (sh/awk/jq); injects RUNNER/GAP_EXPIRY/schema
  -> for each bundle:  fanout-generator.md (model)   # frozen ## JOURNEY-CANDIDATE format OR §5.1 gap
     -> journey-gen-check-candidate.sh (model-free)  # candidate format validated BEFORE merge (fail closed)
  -> merge-dedup.md (model)                          # sentinel-delimited stdout (three artifacts)
  -> journey-gen-split.sh (model-free)               # splits merge.out -> map + §5.2 manifest + §5.1 gaps (fail closed)
  -> check-journey-coverage.sh (model-free)          # COMPLETENESS proof (deterministic gate; NEVER skipped)
  -> check-journey-provenance.sh (model-free)        # quotes verbatim-grounded + AC accounting (oracle-dilution catch)
  -> refuter-fidelity.md (model)                     # JOURNEY_FIDELITY_REVIEW.md (review-only, block/warn/correct)
     -> runner stamps reviewed_sha256 (model-free)   # hash-binds the review to THIS candidate
  -> journey-gen-promote.sh --approve                # HUMAN-GATED promotion (separate invocation)

The live path requires `JOURNEY_RUNNER=<playwright|maestro|appium|pty|http|stub>`
(fail closed before any model call) and honors `JOURNEY_GEN_ALLOW_UNLINKED=1`
(defers unlinked ids to the structured-gap workflow) and `JOURNEY_TARGET_MAP`
(source of existing-ids.txt for the merge's collision rule).
```

The deterministic steps (`journey-gen-slice.sh`, `check-journey-coverage.sh`,
`journey-gen-promote.sh`) run without a model. The generative steps run the three
prompt assets under `journey/gen/prompts/`.

## Guardrails (both runners MUST honor)

- **`RUN_LLM_GEN=1` gates every live model call.** With `RUN_LLM_GEN` unset the
  runner is a deterministic no-op and makes NO model or network call — default CI
  stays green and offline.
- The model is supplied by the operator, not hardcoded: the sh runner
  (`fanout-run.sh`) shells out to `$JOURNEY_GEN_BACKEND <prompt-file> <input>`; the
  Claude Workflow JS runner calls the model through its own agent step. No vendor
  SDK is embedded in this repo.
- Output is always a **CANDIDATE** in a generated-output directory, kept SEPARATE
  from the canonical `JOURNEY_MAP.md`. It becomes canonical ONLY through
  `journey-gen-promote.sh --approve`.
- Coverage is proven deterministically. **Fidelity is refuter-plus-human-bounded,
  not executable proof.** The refuter can `block`/`warn` but never blesses, never
  marks coverage green, and never promotes.
- Runtime truth (`ci_status`/`last_run`/`ci_run_id`/`ci_artifact`/`failure_summary`)
  is NEVER produced here. It lives only in the CI-owned ledger; these runners do
  not read or write it.

## The sh runner

`journey/gen/runners/fanout-run.sh` — see its header. `RUN_LLM_GEN` unset → no-op;
`RUN_LLM_GEN=1` without `JOURNEY_GEN_BACKEND` → fail closed; `RUN_LLM_GEN=1` with a
backend → the opt-in live path above (stops before promotion).

## The Claude Workflow JS runner

A `Workflow` script that runs `journey-gen-slice.sh`, fans out one agent per
bundle over `fanout-generator.md`, runs one `merge-dedup.md` agent, calls
`check-journey-coverage.sh`, runs one `refuter-fidelity.md` agent, and stops —
surfacing the candidate + fidelity review for human promotion. It is gated behind
`RUN_LLM_GEN=1` exactly like the sh runner. (Not built in this task; this is the
contract it must satisfy.)
