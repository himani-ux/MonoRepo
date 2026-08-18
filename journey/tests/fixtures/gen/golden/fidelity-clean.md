# JOURNEY_FIDELITY_REVIEW — golden clean review (no blocking findings)
#
# Produced by the refuter over the golden candidate. No `block:` lines, so the
# refuter gate in journey-gen-promote.sh does not veto promotion.

correct: JOURNEY-101 — oracle preserves FEAT-001 AC-1 and AC-2 — evidence: "the file appears in the invoice list immediately after upload" (bundle FEAT-001 AC-2)
correct: JOURNEY-101 — steps grounded in AFJ-001 — evidence: "observe status=ACCEPTED in the invoice list" (bundle AFJ-001 step 4)
correct: JOURNEY-102 — oracle preserves FEAT-002 AC-1 and AC-2 — evidence: "the status transitions from REJECTED to ACCEPTED" (bundle FEAT-002 AC-2)
