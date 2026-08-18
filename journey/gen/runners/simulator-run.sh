#!/bin/sh
# shellcheck shell=sh
# simulator-run.sh SSOT TEST_SURFACE OUTDIR
#
# Thin runner for the Increment-4 user-simulator engine (spec DC-3, ruling
# D). Follows persona-run.sh's discipline exactly, with ONE structural
# difference: there is NO refuter stage here. Candidates land in
# JOURNEY_INBOX.md as `promotion_status: PROPOSED`; human triage
# (journey-inbox-triage.sh) is the filter, not a refuter model. This runner
# NEVER writes JOURNEY_MAP.md and NEVER runs the triage gate.
#
#   RUN_LLM_GEN unset  -> deterministic no-op (exit 0, no model, no network)
#   RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed
#   JOURNEY_RUNNER, SIM_APP_TARGET, SIM_APP_BUILD are ALL required, checked
#   BEFORE any backend call and before the slicer even runs (house rule 6:
#   runner-declared, never inferred).
#
# Env:
#   RUN_LLM_GEN=1              opt-in gate (house law: stochastic parts are
#                              never the gate — default CI stays a no-op)
#   JOURNEY_GEN_BACKEND=<cmd>  `<cmd> <prompt-file> <input-file>` on stdout
#   JOURNEY_RUNNER=<driver>    playwright|maestro|appium|pty|http (or stub
#                              with ALLOW_STUB_RUNNER=1) — the hands driver
#   SIM_APP_TARGET=<val>       the environment/base-URL this run targets
#   SIM_APP_BUILD=<val>        the build/commit identifier under test
#   JOURNEY_TARGET_INBOX=<path> optional; defaults to OUTDIR/JOURNEY_INBOX.md.
#                              Append semantics: an EXISTING target inbox is
#                              read for its ids and appended to, never
#                              overwritten wholesale (multiple simulator
#                              passes accumulate).
#
# Per bundle, in order:
#   1. backend call -> raw candidate/trace output
#   2. SIM-FAILED: <reason>  -> loud failure, exit 1 (fail closed)
#   3. EMPTY-CANDIDATE       -> logged to OUTDIR/SIMULATOR_ATTEMPTS.md as a
#                               positive result (spec 10.5), NOT a failure;
#                               next bundle
#   4. journey-gen-check-candidate.sh --origin SIMULATOR (fail closed;
#      DERIVED/PERSONA behavior of that gate is untouched — see its own
#      header)
#   5. a `promotion_status:` line anywhere in the candidate is a VALIDATION
#      FAILURE (fail closed) — promotion authority belongs to a human
#      triage reviewer alone; a model asserting it is never silently
#      rewritten, only rejected
#   6. the candidate must declare a `## SIM-TRACE` block at all (fail
#      closed if absent)
#   7. RUNNER-SIDE re-verification: the trace's persona/app_build/runner/
#      patience_budget must EQUAL what THIS runner itself injected into
#      the bundle (never what the model claims about itself) — any
#      mismatch fails the WHOLE run closed (TRACE_ECHO_MISMATCH /
#      PATIENCE_BUDGET_MISMATCH); >=1 `path:` entry required
#
# Assembly (deterministic, NO model merge — mirrors persona-run.sh's own
# assembly discipline): only after EVERY bundle in this pass has cleared
# the checks above does assembly happen at all — a SIM-FAILED or mismatch
# on bundle N aborts before any target-directory temp file is even
# created, so a pre-existing target inbox is provably byte-unchanged on
# any failure path (nothing to clean up; house rule 8). For each verified
# candidate: the runner assigns the next-free `## INBOX-<n>` id (skipping
# ids already in the target inbox, if one exists — append semantics),
# FORCES `origin: SIMULATOR` / `author_status: UNWRITTEN` / `promotion_
# status: PROPOSED` regardless of what the (already-validated) candidate
# said, writes the candidate's raw backend output verbatim to
# `OUTDIR/transcripts/INBOX-<n>.transcript.md`, and injects that path
# (relative to OUTDIR — transcripts and a default-location target inbox
# are colocated; an operator overriding JOURNEY_TARGET_INBOX to a
# directory other than OUTDIR is responsible for keeping the transcripts
# alongside it) as the FIRST `evidence:` entry in BOTH the assembled
# entry's top-level `evidence:` field and its `simulator_trace:` block —
# any model-supplied extra evidence lines pass through after it verbatim.
# The fully assembled/updated inbox is validated with lint-journey-
# inbox.sh BEFORE the temp->final rename (temp+trap+mv); on ANY failure
# from here on, nothing is renamed and the pre-existing target inbox (if
# any) is untouched.
#
# Codes (own; runner-prefixed PLAIN MESSAGES, not lint codes — persona-
# run.sh's style, per spec ruling F):
#   SIM-FAILED                    — pass-through of the model's own token
#   PROMOTION_STATUS_FORBIDDEN    — candidate declared promotion_status
#   SIM_TRACE_MISSING             — candidate has no ## SIM-TRACE block
#   TRACE_ECHO_MISMATCH           — persona/app_build/runner echo != bundle
#   PATIENCE_BUDGET_MISMATCH      — patience_budget echo != bundle
#   TRACE_PATH_EMPTY              — zero `path:` entries in the trace
# + pass-through of whatever journey-gen-check-candidate.sh / lint-
#   journey-inbox.sh / lint-personas.sh / lint-test-surface.sh emit.
set -u
_here=$(cd "$(dirname "$0")" && pwd)
_prompts="$_here/../prompts"
_bin="$_here/../../bin"
_lib="$_here/../../lib/journey-lib.sh"

if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'simulator-run: no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> JOURNEY_RUNNER=<runner> SIM_APP_TARGET=<t> SIM_APP_BUILD=<b> %s SSOT TEST_SURFACE OUTDIR\n' "$0"
  exit 0
fi
[ -n "${JOURNEY_GEN_BACKEND:-}" ] || {
  printf 'simulator-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2; exit 1; }
[ $# -eq 3 ] || {
  printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> JOURNEY_RUNNER=<runner> SIM_APP_TARGET=<t> SIM_APP_BUILD=<b> simulator-run.sh SSOT TEST_SURFACE OUTDIR\n' >&2; exit 1; }
SSOT="$1"; TEST_SURFACE="$2"; OUTDIR="$3"

# ── runner-declared facts, required BEFORE any model call (house rule 6) ──
[ -n "${JOURNEY_RUNNER:-}" ] || {
  printf 'simulator-run: JOURNEY_RUNNER is unset (allowed: playwright|maestro|appium|pty|http|stub) — fail closed before any model call\n' >&2; exit 1; }
[ -n "${SIM_APP_TARGET:-}" ] || {
  printf 'simulator-run: SIM_APP_TARGET is unset — fail closed before any model call\n' >&2; exit 1; }
[ -n "${SIM_APP_BUILD:-}" ] || {
  printf 'simulator-run: SIM_APP_BUILD is unset — fail closed before any model call\n' >&2; exit 1; }
_RUNNER_LC=$(printf '%s' "$JOURNEY_RUNNER" | tr '[:upper:]' '[:lower:]')

mkdir -p "$OUTDIR/candidates" "$OUTDIR/transcripts" || {
  printf 'simulator-run: cannot create %s\n' "$OUTDIR" >&2; exit 1; }

# 0. preflights — every doc violation reported before any model call
sh "$_bin/lint-personas.sh" "$SSOT" || {
  printf 'simulator-run: lint-personas failed (fail closed)\n' >&2; exit 1; }
sh "$_bin/lint-test-surface.sh" "$TEST_SURFACE" || {
  printf 'simulator-run: lint-test-surface failed (fail closed)\n' >&2; exit 1; }

# 1. deterministic slice -> one bundle per persona
sh "$_bin/simulator-gen-slice.sh" "$SSOT" "$TEST_SURFACE" "$OUTDIR" || {
  printf 'simulator-run: slicer failed (fail closed)\n' >&2; exit 1; }

_MANIFEST="$OUTDIR/simulator-manifest.json"
_trace_field() { # FILE KEY -> first "  - KEY: value" value in FILE
  awk -v key="$2" '$0 ~ ("^  - " key ": ") { sub("^  - " key ": ", ""); print; exit }' "$1"
}

_attempts_buf="$OUTDIR/.attempts.buf"
: > "$_attempts_buf"
_verified_buf="$OUTDIR/.verified.buf"
: > "$_verified_buf"

# 2. per-bundle: generate, screen degenerate tokens, validate, runner-verify
for _b in "$OUTDIR"/bundles/*.md; do
  [ -f "$_b" ] || continue
  _name=$(basename "$_b" .md)
  _cfile="$OUTDIR/candidates/$_name.candidate"

  "$JOURNEY_GEN_BACKEND" "$_prompts/simulator-brain.md" "$_b" > "$_cfile" || {
    printf 'simulator-run: backend failed on bundle %s\n' "$_name" >&2; exit 1; }

  # ── SIM-FAILED: loud failure, never silence ──────────────────────────
  if grep -qE '^SIM-FAILED:' "$_cfile"; then
    _reason=$(grep -m1 '^SIM-FAILED:' "$_cfile")
    printf 'simulator-run: bundle %s — %s (fail closed)\n' "$_name" "$_reason" >&2
    exit 1
  fi

  # ── EMPTY-CANDIDATE: a clean run is a legitimate, positive outcome ────
  _nonblank=$(grep -vcE '^[[:space:]]*$' "$_cfile")
  if [ "$_nonblank" -eq 1 ] && grep -qxE '[[:space:]]*EMPTY-CANDIDATE[[:space:]]*' "$_cfile"; then
    _p_id=$(jq -r --arg p "bundles/$_name.md" '.bundles[] | select(.bundle_path==$p) | .persona' "$_MANIFEST")
    _p_goal=$(jq -r --arg p "bundles/$_name.md" '.bundles[] | select(.bundle_path==$p) | .goal' "$_MANIFEST")
    printf 'ATTEMPTED: %s %s — no candidate\n' "$_p_id" "$_p_goal" >> "$_attempts_buf"
    continue
  fi

  # ── the shared candidate-format gate (restrict-never-broaden; DERIVED/
  # PERSONA behavior untouched — see journey-gen-check-candidate.sh) ─────
  sh "$_bin/journey-gen-check-candidate.sh" "$_cfile" --origin SIMULATOR || {
    printf 'simulator-run: candidate %s failed the format check (fail closed before assembly)\n' "$_name" >&2; exit 1; }

  # ── a model NEVER gets authority over the human triage decision ───────
  if grep -qE '^promotion_status:' "$_cfile"; then
    printf 'simulator-run: PROMOTION_STATUS_FORBIDDEN: bundle %s candidate declared promotion_status (authority line) — a model never sets human-triage status (fail closed)\n' "$_name" >&2
    exit 1
  fi

  grep -qE '^## SIM-TRACE[[:space:]]*$' "$_cfile" || {
    printf 'simulator-run: SIM_TRACE_MISSING: bundle %s candidate has no "## SIM-TRACE" block (fail closed)\n' "$_name" >&2; exit 1; }

  _tracefile="$OUTDIR/candidates/$_name.trace"
  awk '/^## SIM-TRACE[[:space:]]*$/ { intrace = 1; next } intrace { print }' "$_cfile" > "$_tracefile"

  # ── runner-side re-verification: bundle facts, never the model's echo ─
  _exp_persona=$(jq -r --arg p "bundles/$_name.md" '.bundles[] | select(.bundle_path==$p) | .persona' "$_MANIFEST")
  _exp_patience=$(grep -m1 -E '^patience_budget:' "$_b" | sed 's/^patience_budget:[[:space:]]*//;s/[[:space:]]*$//')

  _act_persona=$(_trace_field "$_tracefile" persona)
  _act_app_build=$(_trace_field "$_tracefile" app_build)
  _act_runner=$(_trace_field "$_tracefile" runner)
  _act_patience=$(_trace_field "$_tracefile" patience_budget)

  if [ "$_act_persona" != "$_exp_persona" ]; then
    printf 'simulator-run: TRACE_ECHO_MISMATCH: bundle %s persona (bundle=%s, trace=%s) — fail closed\n' "$_name" "$_exp_persona" "$_act_persona" >&2
    exit 1
  fi
  if [ "$_act_app_build" != "$SIM_APP_BUILD" ]; then
    printf 'simulator-run: TRACE_ECHO_MISMATCH: bundle %s app_build (bundle=%s, trace=%s) — fail closed\n' "$_name" "$SIM_APP_BUILD" "$_act_app_build" >&2
    exit 1
  fi
  if [ "$_act_runner" != "$_RUNNER_LC" ]; then
    printf 'simulator-run: TRACE_ECHO_MISMATCH: bundle %s runner (bundle=%s, trace=%s) — fail closed\n' "$_name" "$_RUNNER_LC" "$_act_runner" >&2
    exit 1
  fi
  if [ "$_act_patience" != "$_exp_patience" ]; then
    printf 'simulator-run: PATIENCE_BUDGET_MISMATCH: bundle %s (bundle=%s, trace=%s) — fail closed\n' "$_name" "$_exp_patience" "$_act_patience" >&2
    exit 1
  fi

  _path_count=$(grep -cE '^  - path: ' "$_tracefile")
  [ "$_path_count" -ge 1 ] || {
    printf 'simulator-run: TRACE_PATH_EMPTY: bundle %s candidate has zero path: entries (fail closed)\n' "$_name" >&2; exit 1; }

  printf '%s\n' "$_name" >> "$_verified_buf"
done

# 3. no verified candidate this pass -> nothing to assemble; attempts log
# only, target inbox (if any) is untouched. Still success (spec 10.5: a
# clean sweep is positive evidence, not a failure).
if [ ! -s "$_verified_buf" ]; then
  if [ -s "$_attempts_buf" ]; then
    cat "$_attempts_buf" > "$OUTDIR/SIMULATOR_ATTEMPTS.md"
    printf 'simulator-run: no candidates this pass — %s written (positive evidence, spec 10.5)\n' "$OUTDIR/SIMULATOR_ATTEMPTS.md"
  else
    printf 'simulator-run: no bundles produced a candidate or an attempt (nothing to do)\n'
  fi
  exit 0
fi

if [ -s "$_attempts_buf" ]; then
  cat "$_attempts_buf" > "$OUTDIR/SIMULATOR_ATTEMPTS.md"
fi

# 4. deterministic assembly (NO model merge) — append semantics against the
# target inbox (default OUTDIR/JOURNEY_INBOX.md).
_target="${JOURNEY_TARGET_INBOX:-$OUTDIR/JOURNEY_INBOX.md}"
: > "$OUTDIR/existing-inbox-ids.txt"
if [ -f "$_target" ]; then
  JOURNEY_INBOX="$_target"; export JOURNEY_INBOX
  # shellcheck disable=SC1090
  . "$_lib"
  inbox_ids > "$OUTDIR/existing-inbox-ids.txt"
fi

_assembling="$OUTDIR/.JOURNEY_INBOX.assembling.md"
if [ -f "$_target" ]; then
  cat "$_target" > "$_assembling"
else
  printf '# JOURNEY-INBOX\n' > "$_assembling"
fi

_next=1
_next_free() {
  while grep -qxF "INBOX-$_next" "$OUTDIR/existing-inbox-ids.txt"; do
    _next=$((_next + 1))
  done
}

while IFS= read -r _name; do
  [ -n "$_name" ] || continue
  _cfile="$OUTDIR/candidates/$_name.candidate"
  _tracefile="$OUTDIR/candidates/$_name.trace"

  _next_free
  _nid="$_next"; _next=$((_next + 1))
  printf 'INBOX-%s\n' "$_nid" >> "$OUTDIR/existing-inbox-ids.txt"

  _transcript_rel="transcripts/INBOX-$_nid.transcript.md"
  cp "$_cfile" "$OUTDIR/$_transcript_rel" || {
    printf 'simulator-run: failed to write transcript for %s (fail closed)\n' "$_name" >&2; exit 1; }

  _mapfields="$OUTDIR/candidates/$_name.mapfields"
  awk '/^## JOURNEY-CANDIDATE/ { inmap = 1; print; next } /^## SIM-TRACE[[:space:]]*$/ { inmap = 0 } inmap { print }' "$_cfile" > "$_mapfields"

  _field() { awk -v key="$1" '$0 ~ ("^" key ":") { sub("^" key ":[ \t]*", ""); sub(/[ \t]+$/, ""); print; exit }' "$_mapfields"; }
  _title=$(head -n1 "$_mapfields" | sed 's/^## JOURNEY-CANDIDATE //')

  # top-level evidence: transcript relpath FIRST, then any model-declared
  # trace evidence values (well-formedness is enforced downstream by the
  # composed lint-journey-inbox.sh on the fully assembled file — never
  # re-implemented here).
  _evi_joined="$_transcript_rel"
  _more_evi=$(awk '/^  - evidence: /{ sub(/^  - evidence: /, ""); print }' "$_tracefile")
  if [ -n "$_more_evi" ]; then
    while IFS= read -r _ev; do
      [ -n "$_ev" ] || continue
      _evi_joined="$_evi_joined, $_ev"
    done << _MORE_EOF_
$_more_evi
_MORE_EOF_
  fi

  {
    printf '\n## INBOX-%s %s\n' "$_nid" "$_title"
    printf '%-18s%s\n' "promotion_status:" "PROPOSED"
    printf '%-18s%s\n' "origin:" "SIMULATOR"
    printf '%-18s%s\n' "persona:" "$(_field persona)"
    printf '%-18s%s\n' "goal:" "$(_field goal)"
    printf '%-18s%s\n' "priority:" "$(_field priority)"
    printf '%-18s%s\n' "covers:" "$(_field covers)"
    printf '%-18s%s\n' "oracle_surface:" "$(_field oracle_surface)"
    printf '%-18s%s\n' "negative_states:" "$(_field negative_states)"
    awk '/^steps:/ { print; ins = 1; next } ins && /^[a-zA-Z_][a-zA-Z0-9_]*:/ { exit } ins { print }' "$_mapfields"
    printf '%-18s%s\n' "oracle:" "$(_field oracle)"
    printf '%-18s%s\n' "evidence:" "$_evi_joined"
    printf '%-18s%s\n' "test:" "$(_field test)"
    printf '%-18s%s\n' "runner:" "$(_field runner)"
    printf '%-18s%s\n' "author_status:" "UNWRITTEN"
    printf 'simulator_trace:\n'
    awk -v tl="$_transcript_rel" '
      /^  - evidence:/ && !injected { printf "  - evidence: %s\n", tl; injected = 1 }
      { print }
      END { if (!injected) printf "  - evidence: %s\n", tl }
    ' "$_tracefile"
  } >> "$_assembling"
done < "$_verified_buf"

# 5. the composed gate proves the assembled/updated inbox BEFORE any rename
# (never re-implemented) — on failure, the target directory temp below is
# never created, so a pre-existing target inbox is byte-unchanged.
sh "$_bin/lint-journey-inbox.sh" "$_assembling" || {
  printf 'simulator-run: assembled inbox failed lint-journey-inbox.sh (fail closed; %s untouched)\n' "$_target" >&2
  exit 1
}

# 6. temp + trap + mv (house rule 8): nothing with a final name exists on
# disk on any failure path from here on.
_target_dir=$(dirname "$_target")
mkdir -p "$_target_dir" || {
  printf 'simulator-run: cannot create %s\n' "$_target_dir" >&2; exit 1; }
_inbox_tmp=$(mktemp "$_target_dir/.inbox-XXXXXXXX") || {
  printf 'simulator-run: mktemp failed (fail closed)\n' >&2; exit 1; }
trap 'rm -f "$_inbox_tmp"' EXIT INT TERM
cat "$_assembling" > "$_inbox_tmp"
mv "$_inbox_tmp" "$_target" || {
  printf 'simulator-run: failed to write %s (fail closed)\n' "$_target" >&2; exit 1; }
trap - EXIT INT TERM

_n_new=$(grep -c . "$_verified_buf")
printf 'simulator-run: %d candidate(s) staged to %s (promotion_status: PROPOSED). Triage with:\n' "$_n_new" "$_target"
printf '  sh %s/journey-inbox-triage.sh <JOURNEY_MAP.md> %s --approve\n' "$_bin" "$_target"
exit 0
