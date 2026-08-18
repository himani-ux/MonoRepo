#!/bin/sh
# check-uat-preconditions.sh PATH_TO_MAP — the UAT run preflight (spec G1).
#
# Field-run motivation: a whole browser-UAT pass burned wall-clock time on
# 401s because an existing dev-auth bridge was unconfigured — nothing
# checked declared preconditions before the run. This gate is that check.
#
# Composes lint-journey-map.sh FIRST (as an executable, never
# re-implemented — the same composition style journey/bin/uat-report-promote.sh
# uses for its own sub-gates): the `preconditions:` GRAMMAR is that gate's
# job (Check 8); this gate trusts a lint-clean map and re-parses the same
# blocks using journey/lib/journey-lib.sh accessors plus the identical
# awk block-extraction idiom lint-journey-map.sh Check 8 uses, so the two
# can never disagree about what a `preconditions:` block contains.
#
# Every `preconditions:` entry is `  - <kind>: <value>`, kind in
# {auth, env, data, state} (see journey/JOURNEY_MAP.template.md).
#
#   - `env` entries are STATIC: always checked, no opt-in required. The
#     named environment variable must be set and non-empty in this gate's
#     own environment.
#   - `auth` / `data` / `state` entries are PROBE-checked, opt-in only:
#       * RUN_UAT_PREFLIGHT unset or != 1 (default): no live probe is run.
#         An explicit SKIP line is printed naming how many entries went
#         unprobed — never a silent pass.
#       * RUN_UAT_PREFLIGHT=1: opt-in is explicit, so a missing probe
#         dependency FAILS LOUD rather than silently skipping. Probe
#         contract: UAT_PREFLIGHT_PROBE must name a single executable
#         file, invoked once per entry as
#           "$UAT_PREFLIGHT_PROBE" <kind> <value>
#         exit 0 = precondition met; non-zero = unmet.
#
# Anti-vacuous law (matches NO_SURFACE_BLOCKS / NO_CLAIMS elsewhere in this
# framework): an invoked gate never passes vacuously. Zero preconditions
# declared anywhere in the whole map is itself a failure (NO_PRECONDITIONS),
# not a silent green.
#
# TRUST STATEMENT: this gate checks DECLARED preconditions only. A journey
# with no `preconditions:` block at all is invisible to it — the anti-
# vacuous NO_PRECONDITIONS check above is the only backstop for a map that
# should have declared preconditions but doesn't.
#
# Codes (closed enum):
#   LINT_FAILED               — journey map failed lint-journey-map.sh
#   NO_PRECONDITIONS          — zero preconditions entries anywhere in the
#                                map (anti-vacuous; nothing to preflight)
#   PRECONDITION_ENV_UNSET: <id>: <name>
#                              — an `env:` entry's named variable is unset
#                                or empty in this gate's environment
#   PROBE_MISSING              — RUN_UAT_PREFLIGHT=1 but UAT_PREFLIGHT_PROBE
#                                is not set, or not an executable file
#   PRECONDITION_UNMET: <id>: <kind>: <value>
#                              — the probe reported this entry as unmet
#                                (non-zero exit)
# Usage error / missing map file: exit 2 (matches lint-journey-map.sh).
#
# shellcheck shell=sh
set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB="$_here/../lib/journey-lib.sh"

usage() { printf 'Usage: check-uat-preconditions.sh PATH_TO_MAP\n' >&2; exit 2; }
[ $# -ne 1 ] && usage

MAP="$1"
[ ! -f "$MAP" ] && {
  printf 'check-uat-preconditions: file not found: %s\n' "$MAP" >&2
  exit 2
}

# ── compose lint-journey-map.sh first — grammar is its job, not ours ──────
/bin/sh "$_here/lint-journey-map.sh" "$MAP"
_lint_rc=$?
if [ "$_lint_rc" -ne 0 ]; then
  printf 'LINT_FAILED: journey map failed lint-journey-map.sh\n' >&2
  exit 1
fi

JOURNEY_MAP="$MAP"
export JOURNEY_MAP
# shellcheck disable=SC1090
. "$LIB"

errors=0
total_entries=0
env_total=0
probe_total=0
_njourneys=0
# Newline-separated "id<TAB>kind<TAB>value" for every auth/data/state entry,
# built up across a plain `for` loop (no pipe subshell — see house rule:
# counters mutated inside `... | while read` are lost; heredoc/for-loop
# redirection is not a pipe and does not fork a subshell).
_probe_entries=""

ids="$(journey_ids | sort -u)"

for id in $ids; do
  block="$(journey_block "$id")"
  printf '%s\n' "$block" | grep -qE '^preconditions:' || continue
  _njourneys=$((_njourneys + 1))

  # Same block-extraction idiom as lint-journey-map.sh Check 8.
  _precond="$(printf '%s\n' "$block" | awk '
    /^preconditions:/{ins=1; next}
    ins && /^[a-z_]+:/{exit}
    ins && /^## /{exit}
    ins{print}
  ')"

  while IFS= read -r _pline; do
    case "$_pline" in
      '  - '*)
        _pc_body="${_pline#  - }"
        _pc_kind="${_pc_body%%:*}"
        _pc_value="${_pc_body#*: }"
        total_entries=$((total_entries + 1))
        if [ "$_pc_kind" = "env" ]; then
          env_total=$((env_total + 1))
          # Use printenv (not eval/${!x}) — an env: value may legally
          # contain '.', '/', '-' per the grammar, which is not safe to
          # splice into an eval'd parameter expansion (bash 3.2's
          # ${x/.../...} pattern-substitution syntax collides with '/').
          _env_val="$(printenv "$_pc_value" 2>/dev/null)"
          if [ -z "$_env_val" ]; then
            printf 'PRECONDITION_ENV_UNSET: %s: %s\n' "$id" "$_pc_value" >&2
            errors=$((errors + 1))
          fi
        else
          probe_total=$((probe_total + 1))
          _probe_entries="${_probe_entries}${id}	${_pc_kind}	${_pc_value}
"
        fi
        ;;
    esac
  done << _PRECOND_EOF_
$_precond
_PRECOND_EOF_
done

# ── anti-vacuous law: zero declared entries anywhere is itself a failure ──
if [ "$total_entries" -eq 0 ]; then
  printf 'NO_PRECONDITIONS: no journey declares preconditions; nothing to preflight\n' >&2
  exit 1
fi

# ── PROBE checks (auth/data/state) — opt-in only ───────────────────────────
if [ "${RUN_UAT_PREFLIGHT:-}" != "1" ]; then
  printf 'SKIP: live probes not run (RUN_UAT_PREFLIGHT not set); %s auth/state/data precondition(s) UNPROBED\n' "$probe_total"
else
  _probe="${UAT_PREFLIGHT_PROBE:-}"
  if [ -z "$_probe" ] || [ ! -x "$_probe" ]; then
    printf 'PROBE_MISSING: RUN_UAT_PREFLIGHT=1 but UAT_PREFLIGHT_PROBE not set or not executable\n' >&2
    exit 1
  fi
  while IFS= read -r _peline; do
    [ -z "$_peline" ] && continue
    _pe_id="${_peline%%	*}"
    _pe_rest="${_peline#*	}"
    _pe_kind="${_pe_rest%%	*}"
    _pe_value="${_pe_rest#*	}"
    if ! "$_probe" "$_pe_kind" "$_pe_value"; then
      printf 'PRECONDITION_UNMET: %s: %s: %s\n' "$_pe_id" "$_pe_kind" "$_pe_value" >&2
      errors=$((errors + 1))
    fi
  done << _PROBE_EOF_
$_probe_entries
_PROBE_EOF_
fi

[ "$errors" -gt 0 ] && exit 1

printf 'OK: %s journey(s) with declared preconditions, %s entries checked (%s env static, %s auth/state/data)\n' \
  "$_njourneys" "$total_entries" "$env_total" "$probe_total"
exit 0
