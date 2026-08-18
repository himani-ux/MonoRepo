# JOURNEY_COVERAGE_GAPS — structured coverage gaps (machine-parseable)
# DEFECT: a DOC_FORMAT diagnostic is logged as a gap. It is a blocking format
# failure, never a coverage credit — its presence alone must fail the gate even
# though every FEAT/AFJ id is otherwise journeyed or well-formed-gapped.

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

source_id:    APP_FLOW_UNIDDED
source_type:  DOC_FORMAT
reason:       an APP_FLOW user-journey heading carries no AFJ-id
owner:        alice
expiry:       2026-09-01
reviewer:     bob
