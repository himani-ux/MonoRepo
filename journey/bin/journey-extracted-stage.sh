#!/bin/sh
# shellcheck shell=sh
# journey-extracted-stage.sh CANDIDATES MANIFEST REPO_ROOT OUT_EXTRACTED [GAPS] [--regenerate]
#
# Deterministic staging of Step 0 Stage 4b's extraction output into
# JOURNEY_EXTRACTED.md (spec §4.3, §6.1, §14 — task E4). This runner is
# DETERMINISTIC: Stage 4b's model work happens in another harness entirely;
# CANDIDATES is a plain INPUT FILE here, exactly as MANIFEST is. No
# RUN_LLM_GEN, no backend, no network — this script never calls a model.
#
# ── CANDIDATES grammar (step0-out/journey-candidates.md, spec §4.1) ────────
#   extraction_commit: <40-hex sha of the audited repo>   (shared header)
#
#   ## JOURNEY-CANDIDATE — "<title>"
#   origin:          EXTRACTED
#   ... the frozen JOURNEY-CANDIDATE field set (SAME grammar DERIVED/
#   PERSONA/SIMULATOR candidates use — persona, goal, priority, covers,
#   flows, oracle_surface, negative_states, grade, steps, oracle: |
#   oracle_gap:, evidence, test, runner, author_status) ...
#
#   ```json field_sources
#   { ... }
#   ```
#
#   ## EXTRACTION-SOURCES
#     - <path>:<line> — "<verbatim quote>"
#     - <path>#<heading>
#     - search: grep -rFn -- "<literal>" <relpath>   (absence evidence, DX-1)
#   prior_e2e: <relpath>                (optional — see below)
#
# The search-cite line (DX-1, live-characterization fix wave) is carried
# through to the staged entry BYTE-UNCHANGED, exactly like the other two
# citation-line shapes — this runner does not special-case it: it is just
# another `  - ` line inside `_src_lines` below, re-validated for grammar
# by the composed lint and byte-verified against the pinned commit by the
# composed provenance gate. Never re-parsed or re-interpreted here.
#
#   ## JOURNEY-CANDIDATE — "<next title>"
#   ...
#
# Degenerate whole-file tokens (checked before the header is even read —
# mirror simulator-run.sh's EMPTY-CANDIDATE loneness idiom): a CANDIDATES
# file whose only non-blank content is a lone `EXTRACTION-FAILED: <reason>`
# line is a loud, attributable failure (exit 1, mirrors journey-gen-check-
# candidate.sh's own CANDIDATE-FAILED / simulator-run.sh's SIM-FAILED). A
# CANDIDATES file whose only non-blank content is a lone `NO-JOURNEYS-FOUND`
# line (legitimate — e.g. a BACKEND_ONLY project with no user-facing flows)
# appends one line to OUT_EXTRACTED's SIBLING `EXTRACTED_ATTEMPTS.md`
# (simulator SIMULATOR_ATTEMPTS.md precedent, adapted to whole-run
# granularity — there is no per-bundle concept here) and exits 0; OUT_
# EXTRACTED itself, and everything else, is left completely untouched —
# including re-verification of any PRESERVED entries from a prior run: a
# NO-JOURNEYS-FOUND pass is a pure attempts-log append, nothing more (a
# documented, deliberate limitation — see journey-extracted-format.md).
#
# ── Candidate-side `prior_e2e:` syntax (this runner's own design decision,
# since the design spec leaves the candidate-side grammar open — only the
# STAGED entry's `prior_e2e:` shape, §4.2, is spec'd) ──────────────────────
# `prior_e2e:` is written as the LAST line of a candidate's own
# `## EXTRACTION-SOURCES` block (after its citation lines), never inside
# the JOURNEY-CANDIDATE field block itself. Rationale: `prior_e2e:` is
# extraction PROVENANCE (Stage 4b discovers it via the manifest's own
# `e2e_test:` lines), not a generic journey-intent field DERIVED/PERSONA/
# SIMULATOR candidates ever carry — it belongs structurally beside the
# other provenance the EXTRACTION-SOURCES block carries, and this placement
# means journey-gen-check-candidate.sh (which knows nothing about
# `prior_e2e:`) never has to special-case it: it is simply inert content to
# that checker, exactly like `## EXTRACTION-SOURCES` and its citation lines
# are already inert to it (the checker's per-block/RUNTIME_FIELD/BAD_ORIGIN
# checks all key off `^` line-start patterns for OTHER field names; none of
# them match `  - <cite>` or `prior_e2e:`). Carried into the staged entry
# verbatim (grammar re-validated there by the composed lint's own
# PRIOR_E2E_FORMAT check — never re-implemented here).
#
# ── field_sources fence on an EXTRACTED candidate (design decision,
# documented since the checker's requirement is unconditional and
# byte-unchanged — restrict-never-broaden) ──────────────────────────────────
# journey-gen-check-candidate.sh's MISSING_FIELD_SOURCES check is NOT
# origin-gated (same for every --origin value, on purpose — restrict-never-
# broaden means DERIVED/PERSONA/SIMULATOR/EXTRACTED behavior of that check
# is identical). An EXTRACTED candidate therefore still needs a
# `json field_sources` fence to clear the (byte-unchanged) checker, even
# though EXTRACTED's REAL provenance is the `## EXTRACTION-SOURCES` block,
# not this fence. Stage 4b's worked example emits `{}` (a trivially valid,
# empty JSON object) for this fence on EXTRACTED candidates — satisfying the
# checker's structural requirement (one fence per JOURNEY-CANDIDATE block,
# valid JSON object) without duplicating provenance the EXTRACTION-SOURCES
# block already carries byte-verifiably. This mirrors the SIMULATOR
# precedent exactly: simulator-run.sh's own candidates ALSO carry a
# `json field_sources` fence (see journey/tests/fixtures/simulator/expected-
# candidate-p1.md) even though their REAL provenance is the appended
# `## SIM-TRACE` block, not the fence.
#
# ── Runner argument/composition order (booby-trap-provable) ────────────────
#   1. args validated: CANDIDATES/REPO_ROOT/GAPS(if given) must exist ->
#      exit 2. REPO_ROOT is a directory-existence check happening HERE,
#      before ANY candidate is read or ANY gate composed — proven by a
#      dedicated test: a `git` PATH-shim that touches a sentinel file is
#      NEVER touched when REPO_ROOT is missing (journey-gen-check-
#      candidate.sh is not even invoked once). MANIFEST is deliberately NOT
#      checked here (see below).
#   2. CANDIDATES read: degenerate whole-file tokens (above).
#   3. mode determined from OUT_EXTRACTED's existence + --regenerate:
#      fresh (no pre-existing file, or --regenerate on an all-PENDING file)
#      vs restage (pre-existing file, no --regenerate, or --regenerate
#      refused per below). REGENERATE_REFUSED is checked here, against the
#      EXISTING file only, before CANDIDATES' header/body is parsed at all.
#   4. CANDIDATES header `extraction_commit:` validated (40-hex required;
#      EXTRACTION_COMMIT_INVALID otherwise — reusing lint-journey-
#      extracted.sh's own code name for the identical grammar violation,
#      applied to a different file, per task instruction).
#   5. CANDIDATES split into per-candidate slices (one temp file per
#      `## JOURNEY-CANDIDATE` heading through the next such heading or EOF —
#      INCLUDING that candidate's own `## EXTRACTION-SOURCES` block, mirror-
#      ing how simulator-run.sh feeds the WHOLE per-bundle candidate output,
#      SIM-TRACE included, to the same checker). Zero slices found ->
#      NO_CANDIDATE_BLOCK (reusing journey-gen-check-candidate.sh's own code
#      name, applied at CANDIDATES-file granularity instead of per-slice —
#      the two scopes can never actually collide in practice, since every
#      slice this runner builds always starts with a real JOURNEY-CANDIDATE
#      heading by construction).
#   6. per-candidate, IN ORDER, FAIL-FAST on the first bad candidate (mirrors
#      simulator-run.sh's per-bundle loop, not the schema-lint gates'
#      fail-slow-within-one-file style):
#        a. journey-gen-check-candidate.sh SLICE --origin EXTRACTED
#           (compose, fail closed; pass-through diagnostics).
#        b. CANDIDATE_WORKFLOW_FIELD: `needs_human_confirm:`/
#           `confirmation_status:`/`promoted_as:`/`resolution:`/
#           `resolved_from:` anywhere in the slice (workflow state is
#           never the model's to set — SIMULATOR precedent, promotion_
#           status/PROMOTION_STATUS_FORBIDDEN).
#        c. normalized-key dedup (norm_covers/norm_oracle, journey-lib.sh —
#           the SAME accessors journey-inbox-triage.sh/journey-reality-
#           intake.sh use, covers+oracle compared as a PAIR, never a single
#           joined string): a match against a PRESERVED entry (restage mode
#           only) whose confirmation_status is PENDING or CONFIRMED (incl.
#           promoted_as-stamped terminal) is an idempotent SKIPPED line,
#           never an error; a match against a REJECTED preserved sibling is
#           REJECTED_KEY_COLLISION, fail closed (V-E4 F1 — spec §6:
#           "surfaces, forcing the human to delete the REJECTED entry
#           first: deliberate friction"); a match against an EARLIER
#           candidate already kept THIS run is STAGED_DUP_KEY (fail
#           closed).
#        d. next-free id assignment (skips every id already in the
#           preserved set and every id already assigned this run —
#           simulator-run.sh's `_next_free` idiom).
#        e. the entry is appended to the in-progress assembly buffer,
#           fields copied from the candidate slice in the canonical
#           JOURNEY_EXTRACTED.md field order, `needs_human_confirm: true`
#           + `confirmation_status: PENDING` FORCED regardless of candidate
#           content, `grade:` copied verbatim from the candidate (the
#           extractor grades; GRADE_UNKNOWN is the composed lint's job to
#           catch, never re-validated here — never reimplement a check a
#           composed gate already owns).
#   7. header stamped: `extraction_commit:` from CANDIDATES' own header;
#      `manifest_sha256:` = sha256 of MANIFEST's CURRENT machine block,
#      computed via the IDENTICAL byte-range recipe check-extraction-
#      coverage.sh uses (BEGIN..END inclusive). When MANIFEST does not
#      exist, has no block, or no sha256 tool is on PATH, a syntactically-
#      valid 64-zero PLACEHOLDER is stamped instead — this temp file is
#      NEVER renamed to OUT_EXTRACTED in that case: the composed
#      check-extraction-coverage.sh call in step 8 (MANIFEST is its own
#      first positional arg, read directly, never through this stamp) will
#      independently and honestly report MANIFEST_MISSING / MANIFEST_BLOCK_
#      MISSING / TOOL_MISSING and the run fails before any rename. This
#      lets the runner avoid ever duplicating check-extraction-coverage.sh's
#      OWN MANIFEST_MISSING message (E3's `MANIFEST_MISSING` is deliberately
#      a CHAIN code, not a usage-class exit-2 check — a brand-new project
#      legitimately has no MANIFEST.md yet; this runner's composition
#      inherits that exact posture by construction, never re-implementing
#      it as an early exit-2 guard of its own).
#   8. restage mode ONLY: PRESERVED entries are written into the assembly
#      buffer BYTE-FOR-BYTE — not reconstructed field-by-field through
#      journey-lib.sh's block-extraction accessors (those are read-ONLY,
#      used purely to compute ids/keys for the logic above), but copied as
#      ONE CONTIGUOUS RAW TEXT SPAN straight from the pre-existing
#      OUT_EXTRACTED file (everything from its first `## EXTRACTED-`
#      heading through EOF) — §6.1's "byte-for-byte" guarantee. New
#      entries are appended after that span, in candidate order.
#   9. the temp file passes lint-journey-extracted.sh + check-extracted-
#      provenance.sh TMP REPO_ROOT + check-extraction-coverage.sh MANIFEST
#      TMP [GAPS] — composed as EXECUTABLES, in that order, never
#      reimplemented — before ANY rename. On any failure, the pre-existing
#      OUT_EXTRACTED (if any) is byte-unchanged (nothing renamed; the
#      failing temp lives only under a trap-cleaned scratch dir). In
#      restage mode, the runner ADDITIONALLY scans the failing gate's own
#      diagnostic text for every PRESERVED id (`EXTRACTED-<n>`, digit-
#      boundary-guarded) and prints `ORPHANED_AFTER_RESTAGE: EXTRACTED-<n>`
#      for each one implicated — this NEVER replaces the underlying gate's
#      own diagnostic (both print; the human sees WHAT failed and THAT it
#      was a regression against previously-staged, not brand-new, content).
#      This is how spec §14 Q7 ("terminal entries still integrity-checked")
#      is honored: a `promoted_as:`-stamped or `confirmation_status:
#      REJECTED` preserved entry is copied into the SAME temp file as every
#      other entry and is therefore re-verified by the SAME two composed
#      gates — there is no separate code path that would skip it.
#  10. only once ALL THREE composed gates pass: mktemp in OUT_EXTRACTED's
#      own directory + mv (temp+trap+mv, house rule 8) — `manifest_sha256`
#      is therefore only ever durably "re-stamped" at the moment of a
#      successful rename, never before.
#
# ── `--regenerate` (spec §14 Q5 — NO other override exists) ────────────────
# Refuses (REGENERATE_REFUSED, fail-slow across every offending entry) when
# ANY existing entry's `confirmation_status` is not exactly PENDING, or
# carries a `promoted_as:` or `resolution:` line. With an all-PENDING,
# unresolved, unpromoted file, it discards the existing entries entirely and
# rebuilds from CANDIDATES alone (ids from 1 — identical to fresh-stage
# assembly). A missing OUT_EXTRACTED makes `--regenerate` a no-op (fresh
# stage is already exactly that). There is deliberately no force flag, no
# override, no bypass beyond deleting OUT_EXTRACTED by hand (Q5, binding).
#
# ── Codes ────────────────────────────────────────────────────────────────
# Own: CANDIDATE_WORKFLOW_FIELD, STAGED_DUP_KEY, REJECTED_KEY_COLLISION
# (append-only, V-E4 F1 — the REJECTED-sibling carve-out of the skip path,
# spec §6), ORPHANED_AFTER_RESTAGE,
# REGENERATE_REFUSED, MKTEMP_FAILED (reused from check-extracted-
# provenance.sh — identical scratch-space-creation-failure meaning),
# CANDIDATES_HEADER_INVALID (own, DX-2, live-characterization fix wave —
# first-non-blank-line structural law, see step "2b" above),
# EXTRACTION_COMMIT_INVALID (reused from lint-journey-extracted.sh — same
# grammar violation, applied to the CANDIDATES header instead of OUT_
# EXTRACTED's), NO_CANDIDATE_BLOCK (reused from journey-gen-check-
# candidate.sh — same meaning, CANDIDATES-file granularity). Plus
# EXTRACTION-FAILED (pass-through of the model's own token, SIM-FAILED
# style) and every pass-through code journey-gen-check-candidate.sh /
# lint-journey-extracted.sh / check-extracted-provenance.sh / check-
# extraction-coverage.sh emit.
#
# Usage / missing CANDIDATES / missing REPO_ROOT dir / missing (but given)
# GAPS: exit 2. Any other failure: exit 1. Success: one summary line, exit 0.
#
# Deps: POSIX sh, awk, sed, grep, git (via the composed provenance gate),
# sha256sum|shasum (via this runner's own manifest_sha256 stamp AND via the
# composed coverage gate).
set -u

_here="$(cd "$(dirname "$0")" && pwd)"
_bin="$_here"
_lib="$_here/../lib/journey-lib.sh"

usage() {
  printf 'Usage: journey-extracted-stage.sh CANDIDATES MANIFEST REPO_ROOT OUT_EXTRACTED [GAPS] [--regenerate]\n' >&2
  exit 2
}

[ $# -ge 4 ] || usage
CANDIDATES="$1"; MANIFEST="$2"; REPO_ROOT="$3"; OUT_EXTRACTED="$4"
shift 4

GAPS=""
REGEN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --regenerate) REGEN=1 ;;
    -*) usage ;;
    *)
      [ -z "$GAPS" ] || usage
      GAPS="$1"
      ;;
  esac
  shift
done

# ── step 1: args validated (exit 2), REPO_ROOT checked BEFORE anything else
# touches a candidate or composes a gate (booby-trap discipline) ───────────
[ -f "$CANDIDATES" ] || {
  printf 'journey-extracted-stage: file not found: %s\n' "$CANDIDATES" >&2
  exit 2
}
[ -d "$REPO_ROOT" ] || {
  printf 'journey-extracted-stage: repo root not found: %s\n' "$REPO_ROOT" >&2
  exit 2
}
if [ -n "$GAPS" ]; then
  [ -f "$GAPS" ] || {
    printf 'journey-extracted-stage: file not found: %s\n' "$GAPS" >&2
    exit 2
  }
fi

# shellcheck disable=SC1090
. "$_lib"

# ── step 2: degenerate whole-file tokens ────────────────────────────────────
_nonblank="$(grep -vcE '^[[:space:]]*$' "$CANDIDATES")" || _nonblank=0
if [ "$_nonblank" -eq 1 ] && grep -qxE '[[:space:]]*EXTRACTION-FAILED:.*' "$CANDIDATES"; then
  _reason="$(grep -m1 -E '^[[:space:]]*EXTRACTION-FAILED:.*' "$CANDIDATES")"
  printf 'journey-extracted-stage: %s (fail closed)\n' "$_reason" >&2
  exit 1
fi
if [ "$_nonblank" -eq 1 ] && grep -qxE '[[:space:]]*NO-JOURNEYS-FOUND[[:space:]]*' "$CANDIDATES"; then
  _attempts="$(dirname "$OUT_EXTRACTED")/EXTRACTED_ATTEMPTS.md"
  _attdir="$(dirname "$_attempts")"
  mkdir -p "$_attdir" || {
    printf 'journey-extracted-stage: cannot create %s\n' "$_attdir" >&2
    exit 1
  }
  printf 'ATTEMPTED: %s — NO-JOURNEYS-FOUND\n' "$CANDIDATES" >> "$_attempts"
  printf 'journey-extracted-stage: NO-JOURNEYS-FOUND — %s updated, nothing else written\n' "$_attempts"
  exit 0
fi

# ── step "2b": CANDIDATES_HEADER_INVALID (DX-2, live-characterization fix
# wave) — the CANDIDATES file's FIRST NON-BLANK line must be EXACTLY
# `extraction_commit: <40-hex>`, checked BEFORE any candidate-block parsing
# (booby-trap discipline). Runs AFTER step 2's degenerate-token exits
# (EXTRACTION-FAILED / NO-JOURNEYS-FOUND are legitimate whole-file
# outcomes with no header at all — exempt, not this check's business) but
# BEFORE step 4 below, which used to scan the whole pre-first-heading
# region for an `extraction_commit:` line ANYWHERE in it. That leniency
# was the hole: a prose preamble (an agentic backend narrating "I'll
# generate..." before the real content) or an earlier DECOY
# `extraction_commit:` line embedded in narration both silently won the
# parse — the live characterization reproduced both (attempt1-raw.md's
# prose-then-fence output; a synthetic probe with a fake commit line
# before the real one). This check makes the position itself load-bearing:
# only a literal, first-line `extraction_commit:` key is ever eligible —
# anything else, including a technically-correct value found further down,
# is CANDIDATES_HEADER_INVALID. The VALUE's own 40-hex format is still
# step 4's job (EXTRACTION_COMMIT_INVALID) — this check is structural
# (right key, right position), not a format check.
_first_nonblank_line="$(awk 'NF{print; exit}' "$CANDIDATES")"
case "$_first_nonblank_line" in
  extraction_commit:*) : ;;
  *)
    printf 'CANDIDATES_HEADER_INVALID: first non-blank line of %s must be "extraction_commit: <40-hex>" (got: %s)\n' \
      "$CANDIDATES" "${_first_nonblank_line:-<empty>}" >&2
    exit 1
    ;;
esac

# ── step 3: mode determination (fresh vs restage vs regenerate) ────────────
MODE="fresh"
_preserved_ids=""
if [ -f "$OUT_EXTRACTED" ]; then
  if [ "$REGEN" -eq 1 ]; then
    JOURNEY_EXTRACTED="$OUT_EXTRACTED"; export JOURNEY_EXTRACTED
    _old_ids="$(extracted_ids | sort -u)"
    _refused=0
    for _oid in $_old_ids; do
      [ -n "$_oid" ] || continue
      _blk="$(extracted_block "$_oid")"
      _cs="$(extracted_field "$_oid" confirmation_status 2>/dev/null)" || _cs=""
      _bad_reason=""
      if [ "$_cs" != "PENDING" ]; then
        _bad_reason="confirmation_status is $_cs"
      elif printf '%s\n' "$_blk" | grep -qE '^(promoted_as|resolution):'; then
        _bad_reason="carries promoted_as/resolution"
      fi
      if [ -n "$_bad_reason" ]; then
        printf 'REGENERATE_REFUSED: %s — %s (delete %s by hand to force a rebuild; no other override exists)\n' \
          "$_oid" "$_bad_reason" "$OUT_EXTRACTED" >&2
        _refused=1
      fi
    done
    [ "$_refused" -eq 0 ] || exit 1
    MODE="fresh"
  else
    MODE="restage"
  fi
fi

# ── step 4: CANDIDATES header extraction_commit (40-hex, required) ─────────
_cand_header="$(awk '/^## JOURNEY-CANDIDATE/{exit} {print}' "$CANDIDATES")"
_commit="$(printf '%s\n' "$_cand_header" | awk '/^extraction_commit:/{sub(/^extraction_commit:[ \t]*/,""); print; exit}')"
if ! printf '%s' "$_commit" | grep -qE '^[0-9a-f]{40}$'; then
  printf 'EXTRACTION_COMMIT_INVALID: CANDIDATES extraction_commit must be exactly 40 lowercase hex characters (got: %s)\n' \
    "${_commit:-<missing>}" >&2
  exit 1
fi

# ── scratch space (temp+trap+mv, house rule 8) ──────────────────────────────
_wkdir="$(mktemp -d)" || {
  printf 'MKTEMP_FAILED: cannot create scratch dir (fail closed)\n' >&2
  exit 1
}
_out_tmp=""
trap 'rm -rf "$_wkdir"; [ -n "$_out_tmp" ] && rm -f "$_out_tmp"' EXIT INT TERM

# ── step 5: split CANDIDATES into per-candidate slices ──────────────────────
awk -v out="$_wkdir" '
  /^## JOURNEY-CANDIDATE — / { n++; f = out "/cand_" n ".md" }
  n > 0 { print > f }
' "$CANDIDATES"

_n_cand=0
for _cf in "$_wkdir"/cand_*.md; do
  [ -f "$_cf" ] || continue
  _n_cand=$((_n_cand + 1))
done
if [ "$_n_cand" -eq 0 ]; then
  printf 'NO_CANDIDATE_BLOCK: no "## JOURNEY-CANDIDATE" block found in %s (and no degenerate EXTRACTION-FAILED/NO-JOURNEYS-FOUND token) — a candidates file must contain one or the other\n' \
    "$CANDIDATES" >&2
  exit 1
fi

# ── restage-only prep: preserved ids/keys (the verbatim byte region itself
# is re-read DIRECTLY from OUT_EXTRACTED at assembly time in step 8 below —
# NEVER through a `$(...)` capture here, which would strip trailing
# newlines and subtly disturb the byte-for-byte guarantee at EOF) ─────────
_preserved_covers_keys=""
_preserved_oracle_keys=""
_next=1
if [ "$MODE" = "restage" ]; then
  JOURNEY_EXTRACTED="$OUT_EXTRACTED"; export JOURNEY_EXTRACTED
  _preserved_ids="$(extracted_ids | sort -u)"
  for _pid in $_preserved_ids; do
    [ -n "$_pid" ] || continue
    _pcov="$(norm_covers "$(extracted_field "$_pid" covers 2>/dev/null)")"
    _por="$(extracted_field "$_pid" oracle 2>/dev/null)" || _por=""
    if [ -z "$_por" ]; then
      _por="$(extracted_field "$_pid" oracle_gap 2>/dev/null)" || _por=""
    fi
    _por="$(norm_oracle "$_por")"
    _preserved_covers_keys="$_preserved_covers_keys
$_pid	$_pcov"
    _preserved_oracle_keys="$_preserved_oracle_keys
$_pid	$_por"
  done
fi

_next_free() {
  while printf '%s\n' "$_preserved_ids" | grep -qxF "EXTRACTED-$_next" \
     || printf '%s\n' "$_used_new_ids" | grep -qxF "EXTRACTED-$_next"; do
    _next=$((_next + 1))
  done
}
_used_new_ids=""
# one "id<TAB>norm_covers<TAB>norm_oracle" line per NEW candidate kept this
# run so far (never a preserved one) — used ONLY for the new-vs-new
# STAGED_DUP_KEY check below.
_new_entry_keys=""

_assembling="$_wkdir/.JOURNEY_EXTRACTED.assembling.md"
: > "$_assembling"
_n_new=0
_n_skipped=0

# ── step 6: per-candidate, fail-fast (mirrors simulator-run.sh) ────────────
for _cf in "$_wkdir"/cand_*.md; do
  [ -f "$_cf" ] || continue

  _title_quoted="$(head -n1 "$_cf" | sed 's/^## JOURNEY-CANDIDATE — //')"
  _title="$(printf '%s' "$_title_quoted" | sed 's/^"//; s/"$//')"

  # (a) composed candidate checker — the WHOLE slice, EXTRACTION-SOURCES
  # included, mirrors feeding simulator-run.sh's whole $_cfile (SIM-TRACE
  # included) to the same checker.
  sh "$_bin/journey-gen-check-candidate.sh" "$_cf" --origin EXTRACTED || {
    printf 'journey-extracted-stage: candidate %s failed the format check (fail closed before assembly)\n' "$_title" >&2
    exit 1
  }

  # (b) CANDIDATE_WORKFLOW_FIELD — workflow state is never the model's
  _wf_hit=0
  for _wf in needs_human_confirm confirmation_status promoted_as resolution resolved_from; do
    if grep -qE "^[[:space:]]*${_wf}:" "$_cf"; then
      printf 'CANDIDATE_WORKFLOW_FIELD: %s: %s — the model never sets workflow-state fields (human/gate-authored only)\n' \
        "$_title" "$_wf" >&2
      _wf_hit=1
    fi
  done
  [ "$_wf_hit" -eq 0 ] || exit 1

  # field block (everything before ## EXTRACTION-SOURCES) + sources block
  _fields="$(awk '/^## EXTRACTION-SOURCES/{exit} {print}' "$_cf")"
  _esrc="$(awk '/^## EXTRACTION-SOURCES/{ins=1;next} ins{print}' "$_cf")"
  _src_lines="$(printf '%s\n' "$_esrc" | grep -E '^  - ')" || _src_lines=""
  _prior_e2e="$(printf '%s\n' "$_esrc" | awk '/^prior_e2e:/{sub(/^prior_e2e:[ \t]*/,""); print; exit}')"

  _fget() { # KEY -> value from THIS candidate's field block
    printf '%s\n' "$_fields" | awk -v key="$1" '
      $0 ~ ("^" key ":") { sub("^" key ":[ \t]*", ""); sub(/[ \t]+$/, ""); print; exit }
    '
  }

  _cov="$(_fget covers)"
  _or="$(_fget oracle)"
  if [ -z "$_or" ]; then _or="$(_fget oracle_gap)"; fi
  _norm_cov="$(norm_covers "$_cov")"
  _norm_or="$(norm_oracle "$_or")"

  # (c) normalized-key dedup: preserved match -> SKIPPED; new-vs-new -> STAGED_DUP_KEY
  _match_pid=""
  if [ "$MODE" = "restage" ]; then
    for _pid in $_preserved_ids; do
      [ -n "$_pid" ] || continue
      _pcov="$(printf '%s\n' "$_preserved_covers_keys" | awk -F'\t' -v id="$_pid" '$1==id{print $2; exit}')"
      _por="$(printf '%s\n' "$_preserved_oracle_keys" | awk -F'\t' -v id="$_pid" '$1==id{print $2; exit}')"
      if [ "$_norm_cov" = "$_pcov" ] && [ "$_norm_or" = "$_por" ]; then
        _match_pid="$_pid"
        break
      fi
    done
  fi
  if [ -n "$_match_pid" ]; then
    # V-E4 F1: a key-match against a REJECTED preserved sibling is NOT an
    # idempotent skip — spec §6's owner-approved text: the match
    # "surfaces, forcing the human to delete the REJECTED entry first:
    # deliberate friction". A silent skip would block the documented
    # recovery path for a wrongly-rejected entry (delete the REJECTED
    # entry -> re-stage -> the candidate returns as a NEW entry) behind a
    # mislabeled "idempotent re-run" message. Status read via the SAME
    # first-match extracted_field accessor every gate uses (L11;
    # JOURNEY_EXTRACTED is still exported to OUT_EXTRACTED from the
    # restage prep above). Matches against PENDING/CONFIRMED (incl.
    # promoted_as-stamped terminal) siblings keep the idempotent skip —
    # that part of §6.1 is correct as shipped.
    _match_cs="$(extracted_field "$_match_pid" confirmation_status 2>/dev/null)" || _match_cs=""
    if [ "$_match_cs" = "REJECTED" ]; then
      printf 'REJECTED_KEY_COLLISION: candidate %s matches REJECTED %s — delete the REJECTED entry first to re-stage (deliberate friction, spec §6)\n' \
        "$_title" "$_match_pid" >&2
      exit 1
    fi
    printf 'SKIPPED: %s — already staged as %s (idempotent re-run, normalized covers+oracle match)\n' "$_title" "$_match_pid"
    _n_skipped=$((_n_skipped + 1))
    continue
  fi

  _dup_hit=0
  while IFS="$(printf '\t')" read -r _uid _ucov _uor; do
    [ -n "$_uid" ] || continue
    if [ "$_norm_cov" = "$_ucov" ] && [ "$_norm_or" = "$_uor" ]; then
      printf 'STAGED_DUP_KEY: %s shares a normalized covers+oracle key with %s already staged this run\n' \
        "$_title" "$_uid" >&2
      _dup_hit=1
    fi
  done <<EOF
$_new_entry_keys
EOF
  [ "$_dup_hit" -eq 0 ] || exit 1

  # (d) next-free id
  _next_free
  _id="EXTRACTED-$_next"
  _used_new_ids="$_used_new_ids
$_id"
  _new_entry_keys="$_new_entry_keys
$_id	$_norm_cov	$_norm_or"
  _next=$((_next + 1))

  # (e) append the entry, forced fields regardless of candidate content
  _grade="$(_fget grade)"
  {
    printf '## %s — %s\n' "$_id" "$_title_quoted"
    printf 'needs_human_confirm: true\n'
    printf 'confirmation_status: PENDING\n'
    printf 'grade:               %s\n' "$_grade"
    printf 'origin:              EXTRACTED\n'
    printf 'persona:             %s\n' "$(_fget persona)"
    printf 'goal:                %s\n' "$(_fget goal)"
    printf 'priority:            %s\n' "$(_fget priority)"
    printf 'covers:              %s\n' "$_cov"
    printf 'flows:               %s\n' "$(_fget flows)"
    printf 'oracle_surface:      %s\n' "$(_fget oracle_surface)"
    printf 'negative_states:     %s\n' "$(_fget negative_states)"
    printf '%s\n' "$_fields" | awk '/^steps:/{print;ins=1;next} ins&&/^[a-zA-Z_][a-zA-Z0-9_]*:/{exit} ins{print}'
    if printf '%s\n' "$_fields" | grep -qE '^oracle:'; then
      printf 'oracle:              %s\n' "$(_fget oracle)"
    fi
    if printf '%s\n' "$_fields" | grep -qE '^oracle_gap:'; then
      printf 'oracle_gap:          %s\n' "$(_fget oracle_gap)"
    fi
    printf 'evidence:            %s\n' "$(_fget evidence)"
    printf 'test:                %s\n' "$(_fget test)"
    printf 'runner:              %s\n' "$(_fget runner)"
    printf 'author_status:       UNWRITTEN\n'
    printf 'extraction_sources:\n'
    [ -n "$_src_lines" ] && printf '%s\n' "$_src_lines"
    if [ -n "$_prior_e2e" ]; then
      printf 'prior_e2e:           %s\n' "$_prior_e2e"
    fi
    printf '\n'
  } >> "$_assembling"
  _n_new=$((_n_new + 1))
done

# ── step 7: manifest_sha256 stamp (real, or a syntactically-valid
# placeholder — see header comment: check-extraction-coverage.sh in step 9
# reports the real MANIFEST_MISSING/MANIFEST_BLOCK_MISSING/TOOL_MISSING
# honestly if the placeholder path was taken) ───────────────────────────────
_manifest_sha="0000000000000000000000000000000000000000000000000000000000000000"
if command -v sha256sum >/dev/null 2>&1; then _SHATOOL="sha256sum"
elif command -v shasum >/dev/null 2>&1; then _SHATOOL="shasum -a 256"
else _SHATOOL=""
fi
if [ -f "$MANIFEST" ] && [ -n "$_SHATOOL" ]; then
  _mblock="$(awk '
    /^EXTRACTION-MANIFEST BEGIN$/ { inblk = 1; print; next }
    /^EXTRACTION-MANIFEST END$/   { if (inblk) { print }; exit }
    inblk { print }
  ' "$MANIFEST")"
  if [ -n "$_mblock" ]; then
    # shellcheck disable=SC2086
    _computed="$(printf '%s\n' "$_mblock" | $_SHATOOL | awk '{print $1}')"
    [ -n "$_computed" ] && _manifest_sha="$_computed"
  fi
fi

# ── step 8: assemble the full temp file (header + preserved region + new) ──
_full_tmp="$_wkdir/.JOURNEY_EXTRACTED.full.md"
{
  printf '# JOURNEY-EXTRACTED\n'
  printf 'extraction_commit: %s\n' "$_commit"
  printf 'manifest_sha256:   %s\n' "$_manifest_sha"
  printf '\n'
  if [ "$MODE" = "restage" ]; then
    # DIRECT stream copy, not a variable round-trip: awk's own ORS
    # reproduces every preserved line exactly as it exists on disk,
    # including its own final newline — §6.1's byte-for-byte guarantee.
    awk '/^## EXTRACTED-/{f=1} f{print}' "$OUT_EXTRACTED"
  fi
  cat "$_assembling"
} > "$_full_tmp"

# ── step 9: composed gates, in order, ALL green before any rename ──────────
_report_orphans() { # OUTPUT_TEXT — restage mode only
  [ "$MODE" = "restage" ] || return 0
  for _pid in $_preserved_ids; do
    [ -n "$_pid" ] || continue
    if printf '%s\n' "$1" | grep -qE "${_pid}([^0-9]|\$)"; then
      printf 'ORPHANED_AFTER_RESTAGE: %s\n' "$_pid" >&2
    fi
  done
}

_lint_out="$(sh "$_bin/lint-journey-extracted.sh" "$_full_tmp" 2>&1)"; _lint_rc=$?
if [ "$_lint_rc" -ne 0 ]; then
  printf '%s\n' "$_lint_out" >&2
  _report_orphans "$_lint_out"
  printf 'journey-extracted-stage: lint-journey-extracted.sh failed (fail closed; %s untouched)\n' "$OUT_EXTRACTED" >&2
  exit 1
fi

_prov_out="$(sh "$_bin/check-extracted-provenance.sh" "$_full_tmp" "$REPO_ROOT" 2>&1)"; _prov_rc=$?
if [ "$_prov_rc" -ne 0 ]; then
  printf '%s\n' "$_prov_out" >&2
  _report_orphans "$_prov_out"
  printf 'journey-extracted-stage: check-extracted-provenance.sh failed (fail closed; %s untouched)\n' "$OUT_EXTRACTED" >&2
  exit 1
fi

if [ -n "$GAPS" ]; then
  _cov_out="$(sh "$_bin/check-extraction-coverage.sh" "$MANIFEST" "$_full_tmp" "$GAPS" 2>&1)"
else
  _cov_out="$(sh "$_bin/check-extraction-coverage.sh" "$MANIFEST" "$_full_tmp" 2>&1)"
fi
_cov_rc=$?
if [ "$_cov_rc" -ne 0 ]; then
  printf '%s\n' "$_cov_out" >&2
  _report_orphans "$_cov_out"
  printf 'journey-extracted-stage: check-extraction-coverage.sh failed (fail closed; %s untouched)\n' "$OUT_EXTRACTED" >&2
  exit 1
fi

# ── step 10: temp + trap + mv (house rule 8) ────────────────────────────────
_out_dir="$(dirname "$OUT_EXTRACTED")"
mkdir -p "$_out_dir" || {
  printf 'journey-extracted-stage: cannot create %s\n' "$_out_dir" >&2
  exit 1
}
_out_tmp="$(mktemp "$_out_dir/.extracted-XXXXXXXX")" || {
  printf 'MKTEMP_FAILED: cannot create output temp file (fail closed)\n' >&2
  exit 1
}
cat "$_full_tmp" > "$_out_tmp"
mv "$_out_tmp" "$OUT_EXTRACTED" || {
  printf 'journey-extracted-stage: failed to write %s\n' "$OUT_EXTRACTED" >&2
  exit 1
}
_out_tmp=""

printf 'journey-extracted-stage: %d new entr%s staged to %s' "$_n_new" "$([ "$_n_new" -eq 1 ] && echo y || echo ies)" "$OUT_EXTRACTED"
if [ "$_n_skipped" -gt 0 ]; then
  printf ' (%d already-staged candidate(s) skipped)' "$_n_skipped"
fi
printf ' (needs_human_confirm: true, confirmation_status: PENDING). Confirm with journey-extracted-confirm.sh (task E5).\n'
exit 0
