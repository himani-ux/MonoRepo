# JOURNEY_COVERAGE_GAPS — structured coverage gaps (machine-parseable)
# DEFECT: FEAT-003 gap is missing the required `owner:` field (malformed → no credit).

source_id:    FEAT-003
source_type:  FEAT
reason:       bulk export flow cannot be faithfully rendered without the archive-format spec
expiry:       2026-09-01
reviewer:     bob

source_id:    AFJ-003
source_type:  AFJ
reason:       export journey depends on an unspecified download surface
owner:        alice
expiry:       2026-09-01
reviewer:     bob
