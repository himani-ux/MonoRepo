#!/bin/sh
# Runs every *_test.sh in this dir; exits non-zero if any assertion failed.
set -u
here="$(dirname "$0")"
ASSERT_FAILS=0; export ASSERT_FAILS
for t in "$here"/*_test.sh; do
  printf '\n--- %s ---\n' "$(basename "$t")"
  # shellcheck disable=SC1090
  ASSERT_FAILS=0; . "$t"; total=$((${total:-0} + ASSERT_FAILS))
done
if [ "${total:-0}" -ne 0 ]; then printf '\n%s assertion(s) failed\n' "$total"; exit 1; fi
printf '\nall assertions passed\n'
