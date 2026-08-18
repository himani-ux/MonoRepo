# EXTRACTED_GAPS — extraction coverage gaps ONLY (never doc-derived gaps,
# never PERSONA_COVERAGE_GAPS — this is check-extraction-coverage.sh's own
# artifact, spec §14 Q3). Grammar and expiry mechanics are IDENTICAL to
# journey/bin/check-persona-coverage.sh's PERSONA_COVERAGE_GAPS.md, with
# source_type widened to FEAT | SCREEN (this gate's anchors span both).

source_id: FEAT-020
source_type: FEAT
reason: retry-flow candidate deferred until Stage 4b's next extraction pass
owner: prince
reviewer: prince
expires: 2099-12-31
