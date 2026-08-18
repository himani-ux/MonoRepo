# JOURNEY_FIDELITY_REVIEW — golden blocking review (one blocking finding)
#
# The refuter caught an oracle dilution. The `block:` line MUST veto promotion in
# journey-gen-promote.sh even when every other gate passes and --approve is given.

block: JOURNEY-101 — oracle dropped FEAT-001 AC-2 (still present in the source bundle) — evidence: "the file appears in the invoice list immediately after upload" (bundle FEAT-001 AC-2)
correct: JOURNEY-102 — faithful to FEAT-002 + AFJ-002 — evidence: "the status transitions from REJECTED to ACCEPTED" (bundle FEAT-002 AC-2)
