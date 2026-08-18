#!/bin/sh
# check-extracted-provenance.sh EXTRACTED REPO_ROOT — gate E2 (spec §4.3, §7.2).
#
# Every `extraction_sources:` citation on every staged EXTRACTED-<n> entry —
# including REJECTED and promoted_as-stamped (terminal) entries, spec §14
# Q7 — is byte-verified against the file's pinned `extraction_commit`. This
# gate NEVER reads the working tree: every read is `git show`/`git cat-file`
# against the pinned commit, so editing the staging file (or the repo) after
# it was checked cannot silently invalidate or fake a citation (the D2-class
# proof this framework applies everywhere a commit is pinned).
#
# Composes lint-journey-extracted.sh FIRST, as an executable (never
# reimplemented) — grammar (SOURCE_FORMAT, ENTRY_HEADING_INVALID, ...) is
# that gate's job; this gate TRUSTS a lint-clean file and only re-parses it
# with the same journey-lib.sh accessors lint uses, so the two can never
# disagree about what a block/entry/citation line contains. A non-zero lint
# exit is reported as LINT_FAILED and this gate stops — LINT_FAILED is NOT
# one of spec §7.2's enum members; it is the same house composition-idiom
# pass-through code check-uat-preconditions.sh uses for lint-journey-map.sh
# (journey/bin/check-uat-preconditions.sh:76). Documented here and in
# journey/docs/journey-extracted-format.md, not added to the spec's closed
# enum, per the same precedent.
#
# Code-cite verification (`  - <path>:<line> — "<quote>"`) REUSES
# journey/lib/uat-lib.sh's uat_check_quote_line unchanged — never
# reimplemented. That function parses a "- evidence: <path>:<line> —
# \"<quote>\"" shaped line via uat_ev_path/uat_ev_line/uat_ev_quote; our
# code-cite grammar shares the identical "<path>:<line> — \"<quote>\""
# tail (same em-dash + double-quote convention as a UAT report's evidence
# line), so a cited line is adapted into that exact shape by swapping the
# "  - " staging-file prefix for a "- evidence: " prefix before the call —
# this is an input-shape adaptation, not a reimplementation of the byte
# verification itself (which still runs entirely inside uat-lib.sh).
#
# Search-cite verification (`  - search: grep -rFn -- "<literal>" <relpath>`,
# DX-1, live-characterization fix wave) is the absence-evidence form: it is
# REUSED, unchanged, from journey/lib/uat-lib.sh's uat_check_search_line —
# never reimplemented. The "  - " staging-file prefix is swapped for a
# bare "- " prefix (the same adaptation the code-cite path above performs)
# and handed to uat_check_search_line with expect="zero": the literal is
# re-executed as `git grep -Fn` against the pinned extraction_commit, and
# ANY hit is a divergence — an absence cite that finds something is wrong
# by construction, same name/semantics as the UAT layer's own
# `check-uat-evidence.sh`/`check-uat-verification.sh` (SEARCH_DIVERGED).
# A relpath that does not exist at the pinned commit, or a `git grep`
# internal error, surfaces as SEARCH_ERROR — also uat-lib.sh's own code,
# passed through unchanged. Both codes are additions to this gate's own
# enum (§8.1 below), not a UAT-layer duplication: uat-lib.sh's checker
# function is the single implementation both gates call.
#
# Section-cite verification (`  - <path>#<heading>`) is NEW to this gate
# (uat-lib.sh has no heading matcher): the cited file must exist at the
# pinned commit (SECTION_FILE_MISSING otherwise); its heading lines — ATX
# `#` lines OUTSIDE fenced code blocks (``` or ~~~); fence-aware by
# construction (V-E2 F1: a `#` line inside a fence is code, not a heading)
# — are stripped of leading `#`s + whitespace and matched against the
# cited heading via `grep -Fx` — FIXED-STRING, whole-line, case-sensitive
# equality. The heading is FREE TEXT (spec I9/§5): it is NEVER
# interpolated into a regex or ERE — `grep -F` treats it as a literal
# string regardless of what characters it contains, closing the same
# injection class L22 names for id tokens (.superpowers/sdd/
# sim-reality-progress.md L22: any operator/model-supplied token reaching a
# regex is an injection surface unless whitelisted or matched fixed-string).
# Zero matches -> SECTION_HEADING_MISSING; two or more -> SECTION_AMBIGUOUS
# (fail closed; the citer must disambiguate with a line-cite instead).
# Known simplification: fence LENGTH is not matched — a 4+-tick fence
# embedding 3-tick lines is mis-tracked; ruled residual (V-E2).
#
# A cited path of "." (the repo root) is syntactically legal under the
# citation grammar's path charset but is not a real "file with headings".
# `git cat-file -e <commit>:.` is not the git rev:path root-tree syntax (a
# known quirk: it fails with "path '.' exists on disk, but not in
# '<commit>'" even though `<commit>:` — empty suffix — IS the root tree);
# the existence pre-check special-cases relpath "." the same way
# uat-lib.sh's uat_check_search_line does (W3/D3-b,
# .superpowers/sdd/sim-reality-progress.md) so this degenerate case never
# reports a spurious SECTION_FILE_MISSING — it instead correctly reports
# SECTION_HEADING_MISSING once the (non-heading) tree listing is scanned.
#
# `prior_e2e:` (optional, staging-only, spec §9.3) is verified for
# existence-at-commit only (it claims a discovered test file, not a quote or
# a heading) — this needed its OWN code (PRIOR_E2E_MISSING) because it does
# not fit any existing code's shape (not a citation-cardinality problem like
# SOURCES_MISSING, not a quote problem like QUOTE_UNVERIFIED).
#
# Anti-vacuous law: zero extraction_sources lines anywhere in the whole file
# cannot happen once lint-journey-extracted.sh has passed (its own
# SOURCES_MISSING already demands >=1 per entry, and NO_EXTRACTED_ENTRIES
# demands >=1 entry) — but if the lint composition were ever bypassed, this
# gate must still refuse to pass vacuously: zero total source lines across
# every entry -> NO_SOURCE_LINES (new code; unreachable through normal
# composition, exercised directly in the test suite via a stubbed lint).
#
# PRIOR_E2E_MISSING, NO_SOURCE_LINES, SEARCH_DIVERGED, and SEARCH_ERROR are
# all additions to spec §7.2's drafted enum (`COMMIT_UNKNOWN
# QUOTE_UNVERIFIED LINE_MISMATCH SECTION_FILE_MISSING
# SECTION_HEADING_MISSING SECTION_AMBIGUOUS TOOL_MISSING MKTEMP_FAILED`) —
# the draft predates `prior_e2e:` existing in the entry grammar, predates
# the anti-vacuous backstop being specified, and predates the search-cite
# absence-evidence form (DX-1, live-characterization fix wave: the
# ratified §5 grammar admitted no absence-cite form at all, contradicting
# evidence_rules #2 and the [X] two-sided law — an honest model could not
# comply; see the spec §5 amendment note). All four are appended here,
# append-only, never replacing or renumbering anything (same append-only
# law spec §7's header states for every enum in this framework).
#
# Codes (closed enum, 13 total):
#   LINT_FAILED            — composition pass-through (not a schema code)
#   COMMIT_UNKNOWN          — extraction_commit does not resolve in REPO_ROOT
#   QUOTE_UNVERIFIED        — code-cite quote not found in the cited file at
#                             the pinned commit (uat-lib.sh, unchanged)
#   LINE_MISMATCH           — code-cite quote found in the file, but not at
#                             the cited line (uat-lib.sh, unchanged)
#   SEARCH_DIVERGED         — search-cite literal WAS found at the pinned
#                             commit (an absence claim that isn't absent —
#                             uat-lib.sh, unchanged; DX-1)
#   SEARCH_ERROR            — search-cite relpath does not exist at the
#                             pinned commit, or `git grep` itself errored
#                             (uat-lib.sh, unchanged; DX-1)
#   SECTION_FILE_MISSING    — section-cite path does not exist at the
#                             pinned commit
#   SECTION_HEADING_MISSING — section-cite heading matches zero heading
#                             lines in the cited file (fixed-string, exact)
#   SECTION_AMBIGUOUS       — section-cite heading matches 2+ heading lines
#                             (fail closed; citer must disambiguate)
#   PRIOR_E2E_MISSING: <id>: <path> — prior_e2e path does not exist at the
#                             pinned commit (new code, see above)
#   NO_SOURCE_LINES         — anti-vacuous backstop (new code, see above)
#   TOOL_MISSING            — git not found on PATH (fails closed)
#   MKTEMP_FAILED           — the fail-slow accumulator itself could not be
#                             created (mirrors check-uat-evidence.sh's
#                             M-T1-4 guard: an unguarded `_fail="$(mktemp)"`
#                             on mktemp failure leaves every violation
#                             append a silent no-op against `>>""`)
#
# Usage error / missing EXTRACTED file / missing REPO_ROOT dir: exit 2.
# Any violation: exit 1, fail-slow accumulation (never `| while read` — a
# pipeline subshell loses counter/accumulator mutations, house rule 2).
# Success: prints one OK summary line, exit 0.
#
# shellcheck shell=sh
set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB_JOURNEY="$_here/../lib/journey-lib.sh"
LIB_UAT="$_here/../lib/uat-lib.sh"

usage() { printf 'Usage: check-extracted-provenance.sh EXTRACTED REPO_ROOT\n' >&2; exit 2; }
[ $# -ne 2 ] && usage

EXTRACTED="$1"
REPO_ROOT="$2"

[ -f "$EXTRACTED" ] || {
  printf 'check-extracted-provenance: file not found: %s\n' "$EXTRACTED" >&2
  exit 2
}
[ -d "$REPO_ROOT" ] || {
  printf 'check-extracted-provenance: repo root not found: %s\n' "$REPO_ROOT" >&2
  exit 2
}

# ── compose lint-journey-extracted.sh FIRST — grammar is its job, not ours ─
/bin/sh "$_here/lint-journey-extracted.sh" "$EXTRACTED"
_lint_rc=$?
if [ "$_lint_rc" -ne 0 ]; then
  printf 'LINT_FAILED: staging file failed lint-journey-extracted.sh\n' >&2
  exit 1
fi

command -v git >/dev/null 2>&1 || {
  printf 'TOOL_MISSING: git not found on PATH (fail closed)\n' >&2
  exit 1
}

JOURNEY_EXTRACTED="$EXTRACTED"
export JOURNEY_EXTRACTED
# shellcheck disable=SC1090
. "$LIB_JOURNEY"
# shellcheck disable=SC1090
. "$LIB_UAT"

repo="$REPO_ROOT"

# ── header extraction_commit — grammar already lint-validated (40-hex) ────
_header="$(awk '/^## EXTRACTED-/{exit} {print}' "$EXTRACTED")"
commit="$(printf '%s\n' "$_header" | awk '/^extraction_commit:/{sub(/^extraction_commit:[ \t]*/,""); print; exit}')"

git -C "$repo" cat-file -e "${commit}^{commit}" 2>/dev/null || {
  printf 'COMMIT_UNKNOWN: extraction_commit %s not found in %s\n' "$commit" "$repo" >&2
  exit 1
}

# ── fail-slow accumulator (M-T1-4 guard: check both the substitution's exit
# status AND that $_fail is non-empty before trusting it — an unguarded
# mktemp failure would otherwise leave every later `>>"$_fail"` a silent
# no-op against `>>""`, and `[ -s "$_fail" ]` would read false with real
# violations present) ───────────────────────────────────────────────────────
_fail="$(mktemp)" || {
  printf 'MKTEMP_FAILED: cannot create scratch file (fail closed)\n' >&2
  exit 1
}
[ -n "$_fail" ] || {
  printf 'MKTEMP_FAILED: mktemp returned empty path (fail closed)\n' >&2
  exit 1
}
trap 'rm -f "$_fail"' EXIT

# uat_check_quote_line (uat-lib.sh) reads $repo/$commit/$_fail from this
# scope — already set above.

_n_entries=0
_n_code=0
_n_section=0
_n_search=0
_n_prior=0
_n_src_total=0

ids="$(extracted_ids | sort -u)"

for id in $ids; do
  [ -z "$id" ] && continue
  _n_entries=$((_n_entries + 1))
  block="$(extracted_block "$id")"

  # Same extraction_sources block-extraction idiom as
  # lint-journey-extracted.sh Check E11, so the two gates can never disagree
  # about what the block contains.
  _src="$(printf '%s\n' "$block" | awk '
    /^extraction_sources:/{ins=1; next}
    ins && /^[a-zA-Z_][a-zA-Z0-9_]*:/{exit}
    ins && /^## /{exit}
    ins{print}
  ')"

  while IFS= read -r _sline; do
    case "$_sline" in
      '') continue ;;
    esac

    if printf '%s\n' "$_sline" | grep -qE '^  - search: grep -rFn -- "[^"\\]+" [A-Za-z0-9._/-]+$'; then
      # ── search-cite (DX-1): reuse uat-lib.sh's search checker UNCHANGED,
      # expect="zero" — an absence cite that finds ANY hit is a divergence.
      # Same prefix adaptation as the code-cite branch below ("  - " ->
      # "- "), never a reimplementation: the re-execution itself (the
      # `.`-relpath root-tree special case included) runs entirely inside
      # uat_check_search_line.
      _n_src_total=$((_n_src_total + 1))
      _n_search=$((_n_search + 1))
      _uat_line="- ${_sline#  - }"
      uat_check_search_line "$id" "$_uat_line" zero

    elif printf '%s\n' "$_sline" | grep -qE '^  - [A-Za-z0-9._/-]+:[0-9]+ — ".+"$'; then
      # ── code-cite: reuse uat-lib.sh's pinned-commit quote checker ───────
      _n_src_total=$((_n_src_total + 1))
      _n_code=$((_n_code + 1))
      _uat_line="- evidence: ${_sline#  - }"
      uat_check_quote_line "$id" "$_uat_line"

    elif printf '%s\n' "$_sline" | grep -qE '^  - [A-Za-z0-9._/-]+#[^#]+$'; then
      # ── section-cite: file-exists + fixed-string heading match ──────────
      _n_src_total=$((_n_src_total + 1))
      _n_section=$((_n_section + 1))
      _spath="$(printf '%s\n' "$_sline" | awk -F'#' '{s=$1; sub(/^  - /,"",s); print s}')"
      _sheading="$(printf '%s\n' "$_sline" | sed 's/^[^#]*#//')"

      if [ "$_spath" = "." ]; then
        # W3/D3-b special case (uat-lib.sh:uat_check_search_line): the
        # rev:path root-tree syntax is "<commit>:" (empty suffix), never
        # "<commit>:.".
        _sect_exists=0
        git -C "$repo" cat-file -e "$commit:" 2>/dev/null && _sect_exists=1
      else
        _sect_exists=0
        git -C "$repo" cat-file -e "$commit:$_spath" 2>/dev/null && _sect_exists=1
      fi

      if [ "$_sect_exists" -eq 0 ]; then
        printf 'SECTION_FILE_MISSING: %s: %s\n' "$id" "$_spath" >&2
        echo x >>"$_fail"
      else
        if [ "$_spath" = "." ]; then
          _fcontent="$(git -C "$repo" show "$commit:" 2>/dev/null)"
        else
          _fcontent="$(git -C "$repo" show "$commit:$_spath" 2>/dev/null)"
        fi
        # Fence-aware heading extraction (V-E2 F1): a `#` line inside a
        # ``` or ~~~ fenced code block is CODE, not a heading — a bare
        # `grep '^#'` here was a proven fail-open (a cite whose text
        # existed only inside a fence verified) AND a false-ambiguous
        # nuisance (a real heading duplicated by a fenced `#` line
        # reported 2 matches). The awk state machine toggles in-fence
        # state on lines starting with a fence marker — a fence closes
        # only on its own matching form (a ~~~ line inside a ``` fence is
        # content, and vice versa) — and emits only `#`-prefixed lines
        # OUTSIDE any fence. Indented (4-space) code blocks need no
        # handling: they cannot match /^#/.
        #
        # The stripped heading text is then compared fixed-string,
        # whole-line, case-sensitive — never a regex. $_sheading is free
        # text (I9/§5); grep -F treats it as a literal string no matter
        # what characters it contains (L22 discipline).
        _hcount="$(printf '%s\n' "$_fcontent" | awk '
          /^```/ { if (fence == "") fence = "```"; else if (fence == "```") fence = ""; next }
          /^~~~/ { if (fence == "") fence = "~~~"; else if (fence == "~~~") fence = ""; next }
          fence == "" && /^#/ { print }
        ' | sed 's/^#\{1,\}[ \t]*//' | grep -Fxc -- "$_sheading")"
        if [ "$_hcount" -eq 0 ]; then
          printf 'SECTION_HEADING_MISSING: %s: %s#%s\n' "$id" "$_spath" "$_sheading" >&2
          echo x >>"$_fail"
        elif [ "$_hcount" -ge 2 ]; then
          printf 'SECTION_AMBIGUOUS: %s: %s#%s (%s matches)\n' "$id" "$_spath" "$_sheading" "$_hcount" >&2
          echo x >>"$_fail"
        fi
      fi
    fi
    # A line matching neither grammar cannot survive a lint-clean file
    # (SOURCE_FORMAT) — this gate trusts lint for format and does not
    # re-check it.
  done << _SRC_EOF_
$_src
_SRC_EOF_

  # ── prior_e2e: existence-at-commit (new code, staging-only field) ───────
  if printf '%s\n' "$block" | grep -qE '^prior_e2e:'; then
    _pe="$(extracted_field "$id" prior_e2e 2>/dev/null)" || _pe=""
    if [ -n "$_pe" ]; then
      _n_prior=$((_n_prior + 1))
      if ! git -C "$repo" cat-file -e "$commit:$_pe" 2>/dev/null; then
        printf 'PRIOR_E2E_MISSING: %s: %s\n' "$id" "$_pe" >&2
        echo x >>"$_fail"
      fi
    fi
  fi
done

# ── anti-vacuous backstop — only reachable if the lint composition above
# was bypassed (see header comment); on a real lint-clean file, lint's own
# SOURCES_MISSING/NO_EXTRACTED_ENTRIES already guarantee _n_src_total >= 1
if [ "$_n_src_total" -eq 0 ]; then
  printf 'NO_SOURCE_LINES: zero extraction_sources lines found anywhere in the staging file\n' >&2
  echo x >>"$_fail"
fi

[ -s "$_fail" ] && exit 1

printf 'OK: %s entries, %s code-cite(s), %s section-cite(s), %s search-cite(s), %s prior_e2e checked\n' \
  "$_n_entries" "$_n_code" "$_n_section" "$_n_search" "$_n_prior"
exit 0
