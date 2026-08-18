# MANIFEST — check-extraction-coverage_test.sh golden fixture

Prose narrative (Step 0's prose manifest; this gate never parses prose, only
the machine block below).

EXTRACTION-MANIFEST BEGIN
manifest_version: 1
extraction_commit: 1111111111111111111111111111111111111111
feat: FEAT-014 | behaviors=3 | states_filled=8 | grade_counts=C:5,I:1,G:2,X:0
feat: FEAT-020 | behaviors=1 | states_filled=2 | grade_counts=C:1,I:0,G:0,X:0
feat: FEAT-099 | behaviors=0 | states_filled=0 | grade_counts=C:0,I:0,G:0,X:0
screen: SCR-login | route=/login | flows=AFJ-001
screen: SCR-checkout | route=/checkout | flows=AFJ-002
screen: SCR-dashboard | route=/dashboard
e2e_test: tests/e2e/invoice-resubmit.spec.ts | framework=playwright
EXTRACTION-MANIFEST END
