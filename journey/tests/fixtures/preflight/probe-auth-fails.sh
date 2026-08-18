#!/bin/sh
# probe-auth-fails.sh KIND VALUE — the 401 archetype: reports every "auth"
# kind precondition as unmet (exit 1), everything else as met (exit 0).
# shellcheck shell=sh
[ "${1:-}" = "auth" ] && exit 1
exit 0
