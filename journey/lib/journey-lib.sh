# shellcheck shell=sh
# Parser for JOURNEY_MAP.md intent blocks. A block starts at a heading
# "## JOURNEY-NNN ..." and runs until the next "## " or EOF.
: "${JOURNEY_MAP:=JOURNEY_MAP.md}"

journey_ids() {
  awk '/^## JOURNEY-[0-9]+/ {
    if (match($0, /JOURNEY-[0-9]+/)) print substr($0, RSTART, RLENGTH)
  }' "$JOURNEY_MAP"
}

journey_block() { # ID
  awk -v id="$1" '
    $0 ~ ("^## " id "([^0-9]|$)") { inblk = 1; print; next }
    /^## / && inblk { exit }
    inblk { print }
  ' "$JOURNEY_MAP"
}

journey_field() { # ID KEY -> value (exit 1 if key absent in block)
  v="$(journey_block "$1" | awk -v key="$2" '
    $0 ~ ("^" key ":") { sub("^" key ":[ \t]*", ""); sub(/[ \t]+$/, ""); print; found = 1; exit }
    END { if (!found) exit 3 }
  ')"
  ec=$?
  [ "$ec" -eq 0 ] || return 1
  printf '%s\n' "$v"
}

# ---------------------------------------------------------------------------
# inbox_ids / inbox_block / inbox_field — same parsing idiom as
# journey_ids / journey_block / journey_field above, applied to a
# JOURNEY_INBOX.md file's "## INBOX-<n> ..." headings instead of a
# JOURNEY_MAP.md file's "## JOURNEY-<n> ..." headings. Shared here (not
# forked into lint-journey-inbox.sh) so the map lint and the inbox lint can
# never disagree about how a block/field is extracted.
# ---------------------------------------------------------------------------
: "${JOURNEY_INBOX:=JOURNEY_INBOX.md}"

inbox_ids() {
  awk '/^## INBOX-[0-9]+/ {
    if (match($0, /INBOX-[0-9]+/)) print substr($0, RSTART, RLENGTH)
  }' "$JOURNEY_INBOX"
}

inbox_block() { # ID
  awk -v id="$1" '
    $0 ~ ("^## " id "([^0-9]|$)") { inblk = 1; print; next }
    /^## / && inblk { exit }
    inblk { print }
  ' "$JOURNEY_INBOX"
}

inbox_field() { # ID KEY -> value (exit 1 if key absent in block)
  v="$(inbox_block "$1" | awk -v key="$2" '
    $0 ~ ("^" key ":") { sub("^" key ":[ \t]*", ""); sub(/[ \t]+$/, ""); print; found = 1; exit }
    END { if (!found) exit 3 }
  ')"
  ec=$?
  [ "$ec" -eq 0 ] || return 1
  printf '%s\n' "$v"
}

# ---------------------------------------------------------------------------
# split_and STRING — print one literal-` AND `-separated clause per line,
# verbatim (no trimming — the ` AND ` grammar already carries its own single
# surrounding spaces, so a clause's own text never starts/ends with one). A
# blank/empty STRING prints nothing at all (0 clauses via `wc -l`). Shared by
# lint-journey-map.sh (Check 9) and check-uat-oracle-scope.sh so the two
# parse the `oracle:` / `oracle_classes:` AND-grammar identically and can
# never disagree about a clause count or a positional clause/class.
#
# Splitting on the literal string " AND " (not a bare /AND/ pattern) is
# deliberate: it will not fire on lowercase "and" embedded in words (e.g.
# "understand", "sandbox", "brand") or on "AND" glued to other letters (e.g.
# "STANDARD") — only an isolated, space-delimited, uppercase "AND" ends a
# clause.
# ---------------------------------------------------------------------------
split_and() {
  printf '%s' "$1" | awk '{n = split($0, a, " AND "); for (i = 1; i <= n; i++) print a[i]}'
}

# ---------------------------------------------------------------------------
# extracted_ids / extracted_block / extracted_field — same parsing idiom as
# journey_ids / journey_block / journey_field (and inbox_ids / inbox_block /
# inbox_field) above, applied to a JOURNEY_EXTRACTED.md file's
# "## EXTRACTED-<n> ..." headings instead of "## JOURNEY-<n>" /
# "## INBOX-<n>". Shared here (not forked into lint-journey-extracted.sh) so
# every gate that reads the staging file uses the identical block-extraction
# code and can never disagree about how a block/field is extracted (E1
# spec §4.2, §5 — mirrors the inbox trio's digit-boundary guard).
# ---------------------------------------------------------------------------
: "${JOURNEY_EXTRACTED:=JOURNEY_EXTRACTED.md}"

extracted_ids() {
  awk '/^## EXTRACTED-[0-9]+/ {
    if (match($0, /EXTRACTED-[0-9]+/)) print substr($0, RSTART, RLENGTH)
  }' "$JOURNEY_EXTRACTED"
}

extracted_block() { # ID
  awk -v id="$1" '
    $0 ~ ("^## " id "([^0-9]|$)") { inblk = 1; print; next }
    /^## / && inblk { exit }
    inblk { print }
  ' "$JOURNEY_EXTRACTED"
}

extracted_field() { # ID KEY -> value (exit 1 if key absent in block)
  v="$(extracted_block "$1" | awk -v key="$2" '
    $0 ~ ("^" key ":") { sub("^" key ":[ \t]*", ""); sub(/[ \t]+$/, ""); print; found = 1; exit }
    END { if (!found) exit 3 }
  ')"
  ec=$?
  [ "$ec" -eq 0 ] || return 1
  printf '%s\n' "$v"
}

# ---------------------------------------------------------------------------
# norm_covers STRING -> canonical sorted, DEDUPED, comma-joined token list.
#   sort -u (not bare sort — V-T2 F1 / L15): a candidate whose covers repeats
#   a token ("FEAT-001, FEAT-001") must normalize to the same SET as
#   "FEAT-001", or the repeated token becomes a one-way dedup evasion. -u can
#   only close that miss, never cause a false refusal: two genuinely
#   different sets never collapse equal under it.
# norm_oracle STRING -> whitespace-collapsed, trimmed string.
#
# Shared by journey-inbox-triage.sh (dedup: ACCEPTED candidates vs the
# existing map, and vs each other) and journey-reality-intake.sh (dedup:
# REALITY entry vs the existing map) so every dedup pass in the framework
# normalizes covers/oracle identically — extracted here (not forked) so the
# two gates can never disagree about what counts as a duplicate.
# ---------------------------------------------------------------------------
norm_covers() {
  printf '%s\n' "$1" | awk -F',' '{
    for (i = 1; i <= NF; i++) {
      t = $i
      gsub(/^[ \t]+|[ \t]+$/, "", t)
      if (t != "") print t
    }
  }' | sort -u | tr '\n' ','
}
norm_oracle() {
  printf '%s' "$1" | awk '{ gsub(/[ \t]+/, " "); gsub(/^ +| +$/, ""); print }'
}
