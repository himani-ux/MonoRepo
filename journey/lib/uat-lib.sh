#!/bin/sh
# shellcheck shell=sh
# uat-lib.sh — shared helpers for the UAT report layer (spec 2026-07-09 §4).
# Sourced by gates; defines no globals beyond uat_* functions.

uat_die() { printf '%s: %s\n' "$1" "$2" >&2; exit 1; }

uat_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else printf 'TOOL_MISSING: no sha256 tool\n' >&2; return 1; fi
}

uat_norm() { printf '%s' "$1" | tr -s '[:space:]' ' '; }

uat_contains() { printf '%s\n' "$1" | grep -qF -- "$2"; }

uat_header_field() { # FILE KEY -> value (first match in first 10 lines)
  head -10 "$1" | awk -v k="$2" -F': ' '$1==k {sub($1 FS,""); print; exit}'
}

uat_claim_ids() { grep -o '^## UAT-CLAIM-[0-9][0-9]*' "$1" | sed 's/^## //'; }

uat_claim_block() { # FILE ID -> block body
  awk -v id="## $2:" 'index($0,id)==1 {p=1; print; next}
                      p && /^## / {exit}
                      p {print}' "$1"
}

uat_verdict_ids() { grep -o '^UAT-VERDICT: UAT-CLAIM-[0-9][0-9]*' "$1" | sed 's/^UAT-VERDICT: //'; }

uat_verdict_block() { # FILE ID -> block body
  awk -v id="UAT-VERDICT: $2" '$0==id {p=1; print; next}
                               p && /^UAT-VERDICT: / {exit}
                               p {print}' "$1"
}

# Evidence-line parsers. Input: one full "- evidence: ..." line.
uat_ev_is_artifact() { case "$1" in "- evidence: artifact "*) return 0;; *) return 1;; esac; }
uat_ev_path() { printf '%s\n' "$1" | sed 's/^- evidence: //' | awk -F' — ' '{print $1}' | sed 's/:[0-9][0-9]*$//'; }
uat_ev_line() { printf '%s\n' "$1" | sed 's/^- evidence: //' | awk -F' — ' '{print $1}' | grep -o '[0-9][0-9]*$'; }
uat_ev_quote() { # first '"' after em-dash to last '"' on the line
  printf '%s\n' "$1" | sed 's/^[^—]*— *//' | sed 's/^"//; s/"[^"]*$//'; }
uat_ev_art_path() { printf '%s\n' "$1" | sed 's/^- evidence: artifact //' | awk '{print $1}'; }
uat_ev_art_sha()  { printf '%s\n' "$1" | grep -o 'sha256:[0-9a-f]\{64\}$' | sed 's/^sha256://'; }

# Search-line parsers. Input: one full "- search: ..." line.
uat_srch_literal() { printf '%s\n' "$1" | sed 's/^- search: grep -rFn -- "//; s/" [^"]*$//'; }
uat_srch_relpath() { printf '%s\n' "$1" | awk '{print $NF}'; }
uat_srch_wellformed() { # exit 0 iff the line matches the restricted grammar
  printf '%s\n' "$1" | grep -q '^- search: grep -rFn -- "[^"\\]\{1,\}" [A-Za-z0-9._/-]\{1,\}$' || return 1
  _rp="$(uat_srch_relpath "$1")"
  case "$_rp" in /*|*..*) return 1;; esac
  return 0
}

# Oracle-clause reference-line parsers (spec G4 — oracle observability
# classes; journey/docs/uat-report-format.md §2.2/§5.1/§5.8). Input to both:
# one full "- oracle_clause: ..." line. Grammar: "JOURNEY-<digits>#<k>"
# where <k> is a 1-based, positive-integer index into that journey's own
# " AND "-split `oracle:` clauses. Shared by lint-uat-report.sh (format
# check only) and check-uat-oracle-scope.sh (format + journey/index/class
# adjudication) so the two can never disagree about what counts as
# well-formed.
uat_oc_ref() { printf '%s\n' "$1" | sed 's/^- oracle_clause: //'; }
uat_oc_wellformed() { # exit 0 iff the line is exactly
                       # "- oracle_clause: JOURNEY-<digits>#<positive-int>"
  printf '%s\n' "$1" | grep -qE '^- oracle_clause: JOURNEY-[0-9]+#[1-9][0-9]*$'
}
uat_oc_journey_id() { uat_oc_ref "$1" | awk -F'#' '{print $1}'; }
uat_oc_index()      { uat_oc_ref "$1" | awk -F'#' '{print $2}'; }

# Pinned-commit evidence checkers (gate 4.2). NOT self-contained: callers must
# have these in scope before invoking —
#   repo   = repo root passed to `git -C "$repo" ...`
#   commit = the report's repo_commit (already verified to exist in $repo)
#   rdir   = dirname of the report file (artifact paths are relative to this)
#   $_fail = path to a scratch file; each violation appends one line to it
#            (fail-closed accumulator visible across `while | read` subshells)
# Each function writes one CODE: message to stderr per violation found and
# appends to "$_fail"; callers check `[ -s "$_fail" ]` after the sweep.

uat_check_quote_line() { # $1=claim/verdict id  $2=evidence line
  _p="$(uat_ev_path "$2")"; _l="$(uat_ev_line "$2")"; _q="$(uat_ev_quote "$2")"
  case "$_l" in ''|*[!0-9]*)
    printf 'QUOTE_UNVERIFIED: %s: citation has no valid line number\n' "$1" >&2
    echo x >>"$_fail"; return;;
  esac
  _file="$(git -C "$repo" show "$commit:$_p" 2>/dev/null)" \
    || { printf 'QUOTE_UNVERIFIED: %s: %s not in pinned commit\n' "$1" "$_p" >&2; echo x >>"$_fail"; return; }
  _line="$(printf '%s\n' "$_file" | sed -n "${_l}p")"
  _nq="$(uat_norm "$_q")"
  case "$_nq" in ''|' ')
    printf 'QUOTE_UNVERIFIED: %s: empty quote\n' "$1" >&2
    echo x >>"$_fail"; return;;
  esac
  _nl="$(uat_norm "$_line")"
  if uat_contains "$_nl" "$_nq"; then return; fi
  _nf="$(uat_norm "$_file")"
  if uat_contains "$_nf" "$_nq"; then
    printf 'LINE_MISMATCH: %s: quote not at %s:%s\n' "$1" "$_p" "$_l" >&2
  else
    printf 'QUOTE_UNVERIFIED: %s: quote not in %s at pinned commit\n' "$1" "$_p" >&2
  fi
  echo x >>"$_fail"
}

uat_check_artifact_line() { # $1=id $2=line
  _ap="$(uat_ev_art_path "$2")"; _as="$(uat_ev_art_sha "$2")"
  [ -f "$rdir/$_ap" ] || { printf 'ARTIFACT_MISSING: %s: %s\n' "$1" "$_ap" >&2; echo x >>"$_fail"; return; }
  # NOTE: this runs inside a `| while read` pipe subshell in callers such as
  # check-uat-evidence.sh — a bare `exit 1` here would kill only that
  # subshell and let the parent fall through to a false PASS (the exact
  # bug fixed in commit a21f319). Fail closed via the $_fail accumulator
  # file instead, same as every other violation in this function.
  _h="$(uat_sha256 "$rdir/$_ap")" \
    || { printf 'TOOL_MISSING: %s: sha256 of %s failed — cannot verify (fail closed)\n' "$1" "$_ap" >&2; echo x >>"$_fail"; return; }
  [ "$_h" = "$_as" ] || { printf 'ARTIFACT_HASH_MISMATCH: %s: %s\n' "$1" "$_ap" >&2; echo x >>"$_fail"; }
}

uat_check_search_line() { # $1=id $2=line $3=expect (zero|any)
  _lit="$(uat_srch_literal "$2")"; _rp="$(uat_srch_relpath "$2")"
  # W3 (D3-b): relpath "." means "search the whole tree" — the verifier
  # prompt explicitly encourages this for a broadened [C-absent] confirm.
  # `git cat-file -e <commit>:.` is NOT the root-tree syntax (a well-known
  # rev:path quirk: `.` fails with "path '.' exists on disk, but not in
  # '<commit>'", exit 128) even though `<commit>:` (empty suffix) IS the
  # root tree and the subsequent `git grep -- .` works fine either way.
  # Special-case the existence pre-check only; the search re-execution
  # below already passes `.` through to `git grep` unchanged (confirmed
  # working via plain git — see the characterization report, D3-b).
  if [ "$_rp" = "." ]; then
    git -C "$repo" cat-file -e "$commit:" 2>/dev/null \
      || { printf 'SEARCH_ERROR: %s: %s not in pinned commit\n' "$1" "$_rp" >&2; echo x >>"$_fail"; return; }
  else
    git -C "$repo" cat-file -e "$commit:$_rp" 2>/dev/null \
      || { printf 'SEARCH_ERROR: %s: %s not in pinned commit\n' "$1" "$_rp" >&2; echo x >>"$_fail"; return; }
  fi
  git -C "$repo" grep -Fn -e "$_lit" "$commit" -- "$_rp" >/dev/null 2>&1; _rc=$?
  [ "$_rc" -ge 2 ] && { printf 'SEARCH_ERROR: %s: git grep rc %s\n' "$1" "$_rc" >&2; echo x >>"$_fail"; return; }
  if [ "$3" = zero ] && [ "$_rc" -eq 0 ]; then
    printf 'SEARCH_DIVERGED: %s: "%s" found in %s\n' "$1" "$_lit" "$_rp" >&2; echo x >>"$_fail"
  fi
}
