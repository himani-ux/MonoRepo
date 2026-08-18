# JOURNEY_COVERAGE_GAPS — golden expected output (Task-3 doc-set)
#
# The golden doc-set has NO unlinked P0/P1 FEAT or AFJ ids: every required anchor
# is represented by a JOURNEY-ID, so the frozen gap set is EMPTY (zero records).
#
# A §5.1 record — only when an id genuinely has no faithful journey — is a block of:
#   source_id:    FEAT-<n> | AFJ-<n>        (never a DOC_FORMAT token; those are blocking)
#   source_type:  FEAT | AFJ
#   reason:       why no faithful journey could be derived
#   owner:        who must resolve it
#   expiry:       date by which it must be resolved
#   reviewer:     who signed off on logging it as a gap
