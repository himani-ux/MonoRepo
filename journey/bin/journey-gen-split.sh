#!/bin/sh
# shellcheck shell=sh
# journey-gen-split.sh MERGE_OUT OUTDIR — deterministic splitter for the
# sentinel-delimited merge-backend output (post-merge review C1/C2).
#
# The merge prompt contract requires the backend to emit EXACTLY three
# artifacts on stdout, each wrapped in sentinels, with nothing else:
#
#   === FILE: JOURNEY_MAP.generated.md ===
#   ...content...
#   === END FILE ===
#   === FILE: JOURNEY_COVERAGE_MANIFEST.json ===
#   ...
#   === END FILE ===
#   === FILE: JOURNEY_COVERAGE_GAPS.md ===
#   ...
#   === END FILE ===
#
# FAIL CLOSED (exit non-zero, write NOTHING into OUTDIR) on: unreadable input,
# unknown artifact name, duplicate section, nested/unterminated section, any
# non-blank text outside sections (backend preamble/apology), or fewer than
# all three artifacts. Artifact materialization must never depend on model
# initiative — this splitter is the only writer.
#
# Deps: POSIX sh + awk.

set -u
_SELF="$0"
_die() { printf '%s: %s\n' "$_SELF" "$1" >&2; exit 1; }

[ $# -eq 2 ] || _die "usage: journey-gen-split.sh MERGE_OUT OUTDIR"
MERGE_OUT="$1"; OUTDIR="$2"
[ -r "$MERGE_OUT" ] || _die "merge output not readable: $MERGE_OUT (fail closed)"
[ -d "$OUTDIR" ] || _die "OUTDIR is not a directory: $OUTDIR (fail closed)"

_TMPD=$(mktemp -d "${TMPDIR:-/tmp}/journey-split-XXXXXXXX") \
  || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_TMPD"' EXIT INT TERM

# Parse + validate into the temp dir first; OUTDIR is touched only on success.
awk -v out="$_TMPD" '
  function fatal(msg) { print msg > "/dev/stderr"; err = 1; exit 1 }
  BEGIN {
    allowed["JOURNEY_MAP.generated.md"] = 1
    allowed["JOURNEY_COVERAGE_MANIFEST.json"] = 1
    allowed["JOURNEY_COVERAGE_GAPS.md"] = 1
    cur = ""
  }
  /^=== FILE: .* ===$/ {
    if (cur != "") fatal("nested FILE sentinel at line " NR " (fail closed)")
    name = $0
    sub(/^=== FILE: /, "", name); sub(/ ===$/, "", name)
    if (!(name in allowed))
      fatal("unknown artifact in FILE sentinel: [" name "] (fail closed)")
    if (name in seen)
      fatal("duplicate FILE section: " name " (fail closed)")
    seen[name] = 1; cur = name
    printf "" > (out "/" cur)   # materialize even if the section is empty
    next
  }
  /^=== END FILE ===$/ {
    if (cur == "") fatal("END FILE without an open section at line " NR " (fail closed)")
    close(out "/" cur); cur = ""
    next
  }
  {
    if (cur == "") {
      if ($0 ~ /^[[:space:]]*$/) next
      fatal("text outside FILE sections at line " NR ": [" $0 "] (fail closed)")
    }
    print $0 >> (out "/" cur)
  }
  END {
    if (err) exit 1
    if (cur != "") { print "unterminated FILE section: " cur " (fail closed)" > "/dev/stderr"; exit 1 }
    n = 0; for (k in seen) n++
    if (n != 3) { print "expected exactly 3 artifacts, found " n " (fail closed)" > "/dev/stderr"; exit 1 }
  }
' "$MERGE_OUT" || _die "sentinel split failed; no artifacts written to OUTDIR"

for _a in JOURNEY_MAP.generated.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md; do
  [ -f "$_TMPD/$_a" ] || _die "artifact section missing after split: $_a (fail closed)"
done
for _a in JOURNEY_MAP.generated.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md; do
  mv "$_TMPD/$_a" "$OUTDIR/$_a" || _die "cannot write $OUTDIR/$_a"
done

exit 0
