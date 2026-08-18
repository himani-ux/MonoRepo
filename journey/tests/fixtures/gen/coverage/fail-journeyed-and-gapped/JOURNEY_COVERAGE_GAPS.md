# JOURNEY_COVERAGE_GAPS — structured coverage gaps (machine-parseable)
# DEFECT: FEAT-001 is journeyed by JOURNEY-101 AND logged as a gap. An id cannot
# be both covered and admitted-uncoverable — contradictory accounting.

source_id:    FEAT-001
source_type:  FEAT
reason:       contradictory: this feature is also covered by JOURNEY-101
owner:        alice
expiry:       2026-09-01
reviewer:     bob

source_id:    FEAT-003
source_type:  FEAT
reason:       bulk export flow cannot be faithfully rendered without the archive-format spec
owner:        alice
expiry:       2026-09-01
reviewer:     bob

source_id:    AFJ-003
source_type:  AFJ
reason:       export journey depends on an unspecified download surface
owner:        alice
expiry:       2026-09-01
reviewer:     bob
