# shellcheck shell=sh
: "${ASSERT_FAILS:=0}"
assert_eq() { # EXPECTED ACTUAL MSG
  if [ "$1" = "$2" ]; then printf 'ok: %s\n' "$3"; else
    printf 'FAIL: %s\n  expected: [%s]\n  actual:   [%s]\n' "$3" "$1" "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
assert_contains() { # HAYSTACK NEEDLE MSG
  case "$1" in *"$2"*) printf 'ok: %s\n' "$3" ;;
    *) printf 'FAIL: %s\n  [%s] does not contain [%s]\n' "$3" "$1" "$2"
       ASSERT_FAILS=$((ASSERT_FAILS + 1)) ;; esac
}
assert_not_contains() { # HAYSTACK NEEDLE MSG
  case "$1" in *"$2"*)
    printf 'FAIL: %s\n  [%s] should not contain [%s]\n' "$3" "$1" "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)) ;;
    *) printf 'ok: %s\n' "$3" ;; esac
}
assert_exit() { # EXPECTED_CODE CMD...
  ec_exp="$1"; shift; "$@" >/dev/null 2>&1; ec=$?
  assert_eq "$ec_exp" "$ec" "exit code of: $*"
}
