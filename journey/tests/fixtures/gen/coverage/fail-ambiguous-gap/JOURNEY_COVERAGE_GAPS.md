# JOURNEY_COVERAGE_GAPS — structured coverage gaps (machine-parseable)
# DEFECT: FEAT-003 appears in two gap records (ambiguous / duplicate coverage
# accounting). Two owners/expiries/reviewers for one id weakens determinism.

source_id:    FEAT-003
source_type:  FEAT
reason:       bulk export flow cannot be faithfully rendered without the archive-format spec
owner:        alice
expiry:       2026-09-01
reviewer:     bob

source_id:    FEAT-003
source_type:  FEAT
reason:       duplicate accounting for the same feature
owner:        carol
expiry:       2026-10-01
reviewer:     dave

source_id:    AFJ-003
source_type:  AFJ
reason:       export journey depends on an unspecified download surface
owner:        alice
expiry:       2026-09-01
reviewer:     bob
