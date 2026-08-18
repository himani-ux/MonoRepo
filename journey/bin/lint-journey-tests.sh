#!/bin/sh
# shellcheck shell=sh
# lint-journey-tests.sh SPEC_FILE AUTHOR_BUNDLE
#
# Blindness + oracle-discipline lint for ONE journey spec (Increment 2).
# The AUTHOR BUNDLE is the spec's entire allowance — selectors, routes, and
# APIs beyond it are blindness violations. Generated specs are executable
# code, so this is the strictest gate in the layer.
#
# Violations (all accumulated; exit 1 if any):
#   FORBIDDEN_IMPORT        — any import other than '@playwright/test'
#                             (incl. fs/child_process/src/dynamic import/require)
#   EVALUATE_FORBIDDEN      — page.evaluate (private-state escape hatch)
#   RAW_LOCATOR             — page.locator(...) / xpath= (CSS/XPath bypass)
#   SELECTOR_OUT_OF_SURFACE — getByTestId/getByRole outside allowed_selectors
#   ROUTE_OUT_OF_SURFACE    — page.goto to a route the bundle does not allow
#   API_OUT_OF_SURFACE      — page.request.* to a path not in public_api
#   RUNTIME_FIELD           — runtime-truth ledger keys in a spec
#   ORACLE_COMMENT_MISSING / ORACLE_TEXT_MISMATCH — the spec must carry
#                             '// ORACLE: <exact oracle text from the bundle>'
#   ORACLE_ASSERTION_MISSING— no `await expect(` within 4 lines after ORACLE
#   ZERO_ASSERTIONS         — a spec with no assertions is not a proof
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -eq 2 ] || _die "usage: lint-journey-tests.sh SPEC_FILE AUTHOR_BUNDLE"
SPEC="$1"; BUNDLE="$2"
[ -r "$SPEC" ]   || _die "lint-journey-tests: spec not readable: $SPEC"
[ -r "$BUNDLE" ] || _die "lint-journey-tests: author bundle not readable: $BUNDLE"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }

# ── allowances from the bundle ────────────────────────────────────────────────
awk '/^allowed_selectors:/ { insel = 1; next }
     /^[a-z_]+:/ && insel  { insel = 0 }
     insel && /^[[:space:]]*-[[:space:]]*/ {
       sub(/^[[:space:]]*-[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); print }
' "$BUNDLE" | sort -u > "$_tmp/allowed-selectors.txt"

grep -E '^route:' "$BUNDLE" | sed 's/^route:[[:space:]]*//;s/[[:space:]]*$//' | sort -u > "$_tmp/allowed-routes.txt"

grep -E '^public_api:' "$BUNDLE" | sed 's/^public_api:[[:space:]]*\[//;s/\][[:space:]]*$//' \
  | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | awk 'NF' | sort -u > "$_tmp/allowed-api.txt"

_oracle=$(awk '/^oracle:/ { sub(/^oracle:[ \t]*/, ""); sub(/[ \t]+$/, ""); print; exit }' "$BUNDLE")
[ -n "$_oracle" ] || _die "lint-journey-tests: bundle carries no oracle: line (fail closed)"

# ── imports: ONLY '@playwright/test' ─────────────────────────────────────────
grep -nE "^[[:space:]]*import[[:space:]]" "$SPEC" | while IFS= read -r _line; do
  printf '%s\n' "$_line" | grep -qE "from[[:space:]]+'@playwright/test'" || \
    printf 'FORBIDDEN_IMPORT: %s\n' "$_line" >> "$_tmp/viol.txt"
done
grep -nE "require\(|await import\(|[^a-zA-Z]import\(" "$SPEC" | while IFS= read -r _line; do
  printf 'FORBIDDEN_IMPORT: dynamic import/require: %s\n' "$_line" >> "$_tmp/viol.txt"
done
grep -nE "child_process|node:fs|'fs'|\"fs\"|process\.env" "$SPEC" | while IFS= read -r _line; do
  printf 'FORBIDDEN_IMPORT: node runtime access: %s\n' "$_line" >> "$_tmp/viol.txt"
done
grep -nE "[^a-zA-Z_]eval\(" "$SPEC" | while IFS= read -r _line; do
  printf 'FORBIDDEN_IMPORT: eval: %s\n' "$_line" >> "$_tmp/viol.txt"
done

# ── private-state and raw-locator escapes ─────────────────────────────────────
grep -qE "page\.evaluate|\.evaluate\(" "$SPEC" && \
  printf 'EVALUATE_FORBIDDEN: page.evaluate asserts private state — journeys assert the public surface only\n' >> "$_tmp/viol.txt"
grep -qE "\.locator\(|xpath=" "$SPEC" && \
  printf 'RAW_LOCATOR: page.locator()/xpath= bypasses the role=/testid= surface grammar\n' >> "$_tmp/viol.txt"

# ── runtime truth never appears in a spec ─────────────────────────────────────
grep -qE "ci_status|last_run|ci_run_id|ci_artifact|failure_summary" "$SPEC" && \
  printf 'RUNTIME_FIELD: spec references runtime-truth ledger keys (runtime truth lives only in the CI-owned ledger)\n' >> "$_tmp/viol.txt"

# ── selectors used ⊆ allowed ──────────────────────────────────────────────────
grep -oE "getByTestId\('[^']+'\)" "$SPEC" | sed "s/getByTestId('//;s/')//" | sort -u | while IFS= read -r _tid; do
  grep -qxF "testid=$_tid" "$_tmp/allowed-selectors.txt" || \
    printf 'SELECTOR_OUT_OF_SURFACE: testid=%s is not in the bundle allowed_selectors (blindness violation)\n' "$_tid" >> "$_tmp/viol.txt"
done
grep -oE "getByRole\('[^']+'(,[[:space:]]*\{[^}]*\})?\)" "$SPEC" > "$_tmp/roles.txt" || true
while IFS= read -r _rcall; do
  [ -n "$_rcall" ] || continue
  _role=$(printf '%s' "$_rcall" | sed "s/getByRole('//;s/'.*//")
  _rname=$(printf '%s' "$_rcall" | sed -n "s/.*name:[[:space:]]*'\([^']*\)'.*/\1/p")
  if [ -n "$_rname" ]; then _want="role=${_role}[name=\"${_rname}\"]"; else _want="role=${_role}"; fi
  grep -qxF "$_want" "$_tmp/allowed-selectors.txt" || \
    printf 'SELECTOR_OUT_OF_SURFACE: %s is not in the bundle allowed_selectors (blindness violation)\n' "$_want" >> "$_tmp/viol.txt"
done < "$_tmp/roles.txt"

# ── routes used ⊆ allowed (query strings on an allowed route are fine) ────────
grep -oE "goto\('[^']+'\)" "$SPEC" | sed "s/goto('//;s/')//" | sort -u | while IFS= read -r _rt; do
  _path=$(printf '%s' "$_rt" | sed 's/[?#].*$//')
  grep -qxF "$_path" "$_tmp/allowed-routes.txt" || \
    printf 'ROUTE_OUT_OF_SURFACE: %s is not a bundle route (blindness violation)\n' "$_rt" >> "$_tmp/viol.txt"
done

# ── APIs used ⊆ public_api ────────────────────────────────────────────────────
grep -oE "request\.(get|post|put|delete|patch)\('[^']+'" "$SPEC" | while IFS= read -r _call; do
  _m=$(printf '%s' "$_call" | sed 's/request\.//;s/(.*//' | tr 'a-z' 'A-Z')
  _u=$(printf '%s' "$_call" | sed "s/.*('//;s/'.*//" | sed 's/[?#].*$//')
  grep -qixF "$_m $_u" "$_tmp/allowed-api.txt" || \
    printf 'API_OUT_OF_SURFACE: %s %s is not in the bundle public_api (blindness violation)\n' "$_m" "$_u" >> "$_tmp/viol.txt"
done

# ── oracle discipline ─────────────────────────────────────────────────────────
if ! grep -qF '// ORACLE:' "$SPEC"; then
  printf 'ORACLE_COMMENT_MISSING: the spec must carry "// ORACLE: <exact oracle text>" adjacent to its oracle assertion\n' >> "$_tmp/viol.txt"
else
  grep -qF "// ORACLE: $_oracle" "$SPEC" || \
    printf 'ORACLE_TEXT_MISMATCH: the ORACLE comment must quote the journey oracle VERBATIM: [%s]\n' "$_oracle" >> "$_tmp/viol.txt"
  awk '
    /\/\/ ORACLE:/ { w = 5; found = 0; next }
    w > 0 { w--; if (/await expect\(/) found = 1; if (w == 0 && !found) miss = 1 }
    END { if (w > 0 && !found) miss = 1; exit miss }
  ' "$SPEC" || \
    printf 'ORACLE_ASSERTION_MISSING: no `await expect(` within 4 lines after the ORACLE comment\n' >> "$_tmp/viol.txt"
fi

grep -qE 'await expect\(' "$SPEC" || \
  printf 'ZERO_ASSERTIONS: a spec with no assertions is not a proof\n' >> "$_tmp/viol.txt"

if [ -s "$_tmp/viol.txt" ]; then
  cat "$_tmp/viol.txt"
  printf 'lint-journey-tests: %d violation(s) in %s (fail closed)\n' "$(wc -l < "$_tmp/viol.txt" | tr -d ' ')" "$SPEC"
  exit 1
fi
exit 0
