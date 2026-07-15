# VIMS Certificates Module — Docsuite Coverage & Audit Report

**Generated:** 2026-05-13
**Scope:** Decision-coverage matrix (198 D-CERT-\* IDs × 12 canonical docs) + 5 audits (naming / folders / DB tables / permission IDs / FIELD_MAP completeness).
**Sources:** denominator extracted from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16 (D-CERT-001 → D-CERT-198, sequential, no gaps); numerator extracted from each of the 12 canonical docs under `VIMS-Certs-Module/`.
**Pattern:** Mirrors `../VIMS-Safety-Module/COVERAGE.md` (159/159 GREEN gate pattern that unlocked Phase 0 build).

---

## 1. Decision Coverage Matrix

One row per decision ID. `✓` = ID appears in that doc (any occurrence in body, table, code, or citation). `—` = ID absent. Doc abbreviations:

- **PRD** = `PRD.md`
- **APP** = `APP_FLOW.md`
- **TS** = `TECH_STACK.md`
- **DS** = `DESIGN_SYSTEM.md`
- **FG** = `FRONTEND_GUIDELINES.md`
- **BS** = `BACKEND_STRUCTURE.md`
- **IP** = `IMPLEMENTATION_PLAN.md`
- **VR** = `VALIDATION_RULES.md`
- **UG** = `USER_GUIDE.md`
- **FM** = `FIELD_MAP.md`
- **CL** = `CLAUDE.md`
- **LE** = `LESSONS.md` (scaffold; populates at Phase 0+)

| Decision ID | PRD | APP | TS | DS | FG | BS | IP | VR | UG | FM | CL | LE |
|-------------|-----|-----|----|----|----|----|----|----|----|----|----|----|
| D-CERT-001 | ✓ | — | — | — | — | — | — | — | ✓ | — | ✓ | — |
| D-CERT-002 | ✓ | — | — | ✓ | — | — | — | — | — | — | ✓ | — |
| D-CERT-003 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-004 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-005 | ✓ | — | ✓ | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-006 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-007 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-008 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | ✓ | — |
| D-CERT-009 | ✓ | ✓ | — | — | — | ✓ | — | — | ✓ | — | ✓ | — |
| D-CERT-010 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-011 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-012 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-013 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-014 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-015 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-016 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-017 | ✓ | ✓ | — | — | — | ✓ | ✓ | — | — | ✓ | — | — |
| D-CERT-018 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | — | — | ✓ | — |
| D-CERT-019 | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | — | — | — | — | — |
| D-CERT-020 | ✓ | — | — | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-021 | ✓ | ✓ | ✓ | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-022 | ✓ | — | ✓ | — | — | ✓ | — | — | — | — | ✓ | — |
| D-CERT-023 | ✓ | — | — | — | — | — | ✓ | — | — | — | — | — |
| D-CERT-024 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-025 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-026 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-027 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-028 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-029 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-030 | ✓ | — | — | — | — | — | ✓ | — | — | — | — | — |
| D-CERT-031 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-032 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-033 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-034 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-035 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-036 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-037 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-038 | ✓ | — | — | — | — | ✓ | — | — | ✓ | — | — | — |
| D-CERT-039 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-040 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-041 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-042 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-043 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-044 | ✓ | ✓ | — | — | — | ✓ | ✓ | — | ✓ | ✓ | — | — |
| D-CERT-045 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-046 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-047 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-048 | ✓ | — | ✓ | — | — | — | ✓ | — | — | — | ✓ | — |
| D-CERT-049 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-049a | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-050 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-051 | ✓ | — | ✓ | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-052 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-053 | ✓ | — | — | — | — | — | — | ✓ | — | — | — | — |
| D-CERT-054 | ✓ | — | ✓ | — | — | — | — | — | — | — | — | — |
| D-CERT-055 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-056 | ✓ | — | — | — | — | ✓ | — | ✓ | — | — | — | — |
| D-CERT-057 | ✓ | — | ✓ | — | — | ✓ | ✓ | — | — | — | ✓ | — |
| D-CERT-058 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-059 | ✓ | — | — | — | — | ✓ | ✓ | ✓ | — | — | — | — |
| D-CERT-060 | ✓ | — | — | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-061 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-062 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-063 | ✓ | ✓ | ✓ | — | — | ✓ | — | — | — | ✓ | ✓ | — |
| D-CERT-064 | ✓ | — | ✓ | — | — | ✓ | — | — | — | — | ✓ | — |
| D-CERT-065 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-066 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-067 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-068 | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| D-CERT-069 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-070 | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| D-CERT-071 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-072 | ✓ | — | — | — | — | — | — | — | — | ✓ | — | — |
| D-CERT-073 | ✓ | ✓ | — | — | — | ✓ | ✓ | — | — | ✓ | — | — |
| D-CERT-074 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-075 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-076 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | — | ✓ | ✓ | — |
| D-CERT-077 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-078 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-079 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | ✓ | — | — | — |
| D-CERT-080 | ✓ | — | — | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-081 | ✓ | — | — | — | ✓ | — | ✓ | — | ✓ | — | ✓ | — |
| D-CERT-082 | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | — |
| D-CERT-083 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-084 | ✓ | — | — | ✓ | — | — | — | — | — | — | — | — |
| D-CERT-085 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-086 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-087 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-088 | ✓ | — | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-089 | ✓ | — | — | — | — | ✓ | ✓ | — | ✓ | — | — | — |
| D-CERT-090 | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | — | ✓ | ✓ | — |
| D-CERT-091 | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-092 | ✓ | ✓ | — | — | — | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| D-CERT-093 | ✓ | ✓ | — | — | — | ✓ | ✓ | — | ✓ | ✓ | — | — |
| D-CERT-094 | ✓ | ✓ | — | — | — | ✓ | — | — | ✓ | ✓ | — | — |
| D-CERT-095 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-096 | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-097 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-098 | ✓ | ✓ | — | — | — | ✓ | — | — | ✓ | ✓ | — | — |
| D-CERT-099 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-100 | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| D-CERT-101 | ✓ | ✓ | ✓ | — | — | ✓ | — | — | — | ✓ | ✓ | — |
| D-CERT-102 | ✓ | — | — | — | — | — | — | — | — | — | — | ✓ |
| D-CERT-103 | ✓ | — | — | — | — | — | ✓ | — | — | — | ✓ | — |
| D-CERT-104 | ✓ | ✓ | ✓ | — | — | ✓ | — | — | ✓ | ✓ | ✓ | — |
| D-CERT-105 | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | ✓ | — | ✓ | ✓ | — |
| D-CERT-106 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-107 | ✓ | — | — | — | — | — | ✓ | — | — | — | — | — |
| D-CERT-108 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-109 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-110 | ✓ | ✓ | — | — | — | ✓ | — | — | ✓ | — | ✓ | — |
| D-CERT-111 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-112 | ✓ | ✓ | — | — | — | — | — | ✓ | — | — | — | — |
| D-CERT-113 | ✓ | ✓ | — | ✓ | — | ✓ | — | ✓ | ✓ | ✓ | — | — |
| D-CERT-114 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-115 | ✓ | ✓ | — | — | ✓ | ✓ | — | ✓ | ✓ | ✓ | — | — |
| D-CERT-116 | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-117 | ✓ | ✓ | ✓ | — | — | ✓ | — | ✓ | — | ✓ | — | — |
| D-CERT-118 | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-119 | ✓ | ✓ | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-120 | ✓ | ✓ | — | — | — | — | — | — | ✓ | — | ✓ | — |
| D-CERT-121 | ✓ | ✓ | — | ✓ | — | — | — | ✓ | ✓ | — | — | — |
| D-CERT-122 | ✓ | ✓ | — | — | — | — | — | ✓ | — | — | — | — |
| D-CERT-123 | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — | — | — | — | — |
| D-CERT-124 | ✓ | ✓ | — | — | — | — | ✓ | — | — | — | — | — |
| D-CERT-125 | ✓ | — | ✓ | ✓ | — | ✓ | — | — | — | — | ✓ | — |
| D-CERT-126 | ✓ | — | — | ✓ | — | — | — | — | — | — | — | — |
| D-CERT-127 | ✓ | — | — | ✓ | — | ✓ | — | — | — | — | ✓ | — |
| D-CERT-128 | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — | ✓ | ✓ | — |
| D-CERT-129 | ✓ | — | — | ✓ | — | — | — | — | — | — | — | — |
| D-CERT-130 | ✓ | — | — | ✓ | — | — | — | — | — | — | ✓ | — |
| D-CERT-131 | ✓ | — | — | ✓ | — | — | — | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-132 | ✓ | ✓ | — | ✓ | — | — | — | — | ✓ | ✓ | ✓ | — |
| D-CERT-133 | ✓ | — | — | ✓ | — | — | — | — | — | — | — | — |
| D-CERT-134 | ✓ | — | — | ✓ | — | — | — | — | — | — | — | — |
| D-CERT-135 | ✓ | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-136 | ✓ | ✓ | — | ✓ | — | — | — | — | — | — | ✓ | — |
| D-CERT-137 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-138 | ✓ | ✓ | — | ✓ | — | ✓ | ✓ | — | — | — | ✓ | — |
| D-CERT-139 | ✓ | — | — | ✓ | — | — | — | — | — | — | — | — |
| D-CERT-140 | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| D-CERT-141 | ✓ | ✓ | ✓ | — | — | — | — | — | — | — | — | — |
| D-CERT-142 | ✓ | ✓ | — | — | — | — | — | — | — | — | — | — |
| D-CERT-143 | ✓ | ✓ | — | — | — | — | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-144 | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — | — | — | — | — |
| D-CERT-145 | ✓ | ✓ | ✓ | — | — | ✓ | — | — | ✓ | ✓ | — | — |
| D-CERT-146 | ✓ | — | — | — | — | — | — | — | ✓ | — | — | — |
| D-CERT-147 | ✓ | — | ✓ | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-148 | ✓ | ✓ | — | — | — | — | — | — | — | ✓ | — | — |
| D-CERT-149 | ✓ | ✓ | — | — | ✓ | ✓ | — | — | — | — | — | — |
| D-CERT-150 | ✓ | — | — | ✓ | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| D-CERT-151 | ✓ | ✓ | ✓ | — | — | ✓ | — | — | — | ✓ | ✓ | — |
| D-CERT-152 | ✓ | — | ✓ | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-153 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-154 | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | — | ✓ | — | — | — |
| D-CERT-155 | ✓ | ✓ | — | — | — | ✓ | ✓ | — | — | ✓ | — | — |
| D-CERT-156 | ✓ | ✓ | ✓ | — | ✓ | — | — | — | — | — | ✓ | — |
| D-CERT-157 | ✓ | — | — | — | — | — | — | — | ✓ | — | ✓ | — |
| D-CERT-158 | ✓ | — | — | — | — | ✓ | ✓ | — | — | — | — | — |
| D-CERT-159 | ✓ | ✓ | — | — | — | ✓ | ✓ | ✓ | — | ✓ | — | — |
| D-CERT-160 | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | — |
| D-CERT-161 | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | — |
| D-CERT-162 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-163 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-164 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-165 | ✓ | — | — | — | — | — | — | ✓ | — | — | ✓ | — |
| D-CERT-166 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | ✓ | — |
| D-CERT-167 | ✓ | — | — | — | — | — | — | ✓ | — | — | — | — |
| D-CERT-168 | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-169 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-170 | ✓ | ✓ | — | — | — | ✓ | — | — | ✓ | — | — | — |
| D-CERT-171 | ✓ | ✓ | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-172 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-173 | ✓ | ✓ | — | — | — | ✓ | ✓ | — | — | — | — | — |
| D-CERT-174 | ✓ | — | — | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-175 | ✓ | — | — | — | — | ✓ | — | ✓ | — | ✓ | ✓ | — |
| D-CERT-176 | ✓ | — | — | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-177 | ✓ | — | — | — | — | ✓ | — | — | ✓ | — | ✓ | — |
| D-CERT-178 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-179 | ✓ | — | — | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-180 | ✓ | ✓ | — | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-181 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-182 | ✓ | ✓ | — | — | — | ✓ | — | — | — | ✓ | — | — |
| D-CERT-183 | ✓ | ✓ | — | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-184 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
| D-CERT-185 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-186 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-187 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-188 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-189 | ✓ | — | ✓ | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-190 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-191 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-192 | ✓ | — | — | — | — | — | — | — | — | — | — | — |
| D-CERT-193 | ✓ | — | — | — | — | ✓ | — | — | — | — | — | — |
| D-CERT-194 | ✓ | ✓ | ✓ | — | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-195 | ✓ | ✓ | — | — | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | — |
| D-CERT-196 | ✓ | ✓ | — | — | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| D-CERT-197 | ✓ | — | — | — | — | — | — | ✓ | — | — | — | — |
| D-CERT-198 | ✓ | — | — | — | — | — | — | — | — | — | ✓ | — |
**Coverage totals:** 198 / 198 D-CERT-\* IDs appear in **at least one** doc (PRD as the canonical anchor). **GREEN.**

Per-doc coverage (count of D-CERT IDs each doc cites, mechanically re-grep'd 2026-05-13):
- PRD: 199/199 (anchor — every D-CERT mapped to a FEAT-CERT-\*)
- APP: 92
- TS: 35
- DS: 23
- FG: 15
- BS: 117
- IP: 23
- VR: 48
- UG: 35
- FM: 75
- CL: 66
- LE: 7 (L-001 lesson references 7 D-CERT-* IDs; scaffold grows from Phase 0+)

(Counts are mechanically re-grep'd as of 2026-05-13 via `scripts/verify_coverage.py`. Re-run the script after any doc edit; the matrix above is regenerated from doc content, not from author memory.)

**Decisions explicitly out of scope:** D-CERT-169 (class portal API — never built); D-CERT-102 (superseded by D-CERT-103); D-CERT-100 (partially superseded by D-CERT-104); D-CERT-022 (amended by D-CERT-176). All covered in PRD §19.

---

## 2. Audit 1 — Naming Convention

| Check | Expected | Found | Status |
|-------|----------|-------|--------|
| All Certs DB tables prefixed `vims_certs_` | yes | 18/18 tables in BACKEND §3 | ✅ PASS |
| Master tables prefixed `master_` | yes (shared) | `master_vessel`, `master_user`, `master_role`, `master_RoleByVessel`, `master_notification`, `Mapping_CrewAssReviewers` cited | ✅ PASS |
| Bare `certs_*` (no prefix) | none | 0 occurrences | ✅ PASS |
| Feature IDs use `FEAT-CERT-<domain>-<NNN>` | yes | All 145 V1 features in PRD §3 follow pattern | ✅ PASS |
| Domains used | CAT, TRK, OCR, REC, RBAC, WIZ, PRT, NOTIF, AUDIT, EXT, MIG, LIFE, BLOB, XMOD, DASH | all present in PRD §3 | ✅ PASS |
| Permission Form IDs `CERT_F_*` | yes | CERT_F_001 → CERT_F_008 | ✅ PASS |
| Permission Process IDs `CERT_P_*` | yes | CERT_P_001 → CERT_P_010 | ✅ PASS |
| React component prefix `Cert*` | yes | All components in DESIGN_SYSTEM §9 + APP_FLOW + FRONTEND_GUIDELINES | ✅ PASS |
| Django app path `apps/certs/` | yes | BACKEND §1, CLAUDE §3 | ✅ PASS |
| API base `/api/certs/` | yes | BACKEND §5 | ✅ PASS |
| Frontend route base `/certs/` | yes | APP_FLOW §1, FRONTEND_GUIDELINES §1 | ✅ PASS |

**Audit 1 result: ✅ PASS**

---

## 3. Audit 2 — Folder Structure

| Required path | Present | Status |
|---------------|---------|--------|
| `VIMS-Certs-Module/` | yes | ✅ |
| `VIMS-Certs-Module/CLAUDE.md` | yes | ✅ |
| `VIMS-Certs-Module/PRD.md` | yes | ✅ |
| `VIMS-Certs-Module/APP_FLOW.md` | yes | ✅ |
| `VIMS-Certs-Module/TECH_STACK.md` | yes | ✅ |
| `VIMS-Certs-Module/DESIGN_SYSTEM.md` | yes | ✅ |
| `VIMS-Certs-Module/FRONTEND_GUIDELINES.md` | yes | ✅ |
| `VIMS-Certs-Module/BACKEND_STRUCTURE.md` | yes | ✅ |
| `VIMS-Certs-Module/IMPLEMENTATION_PLAN.md` | yes | ✅ |
| `VIMS-Certs-Module/VALIDATION_RULES.md` | yes | ✅ |
| `VIMS-Certs-Module/USER_GUIDE.md` | yes | ✅ |
| `VIMS-Certs-Module/FIELD_MAP.md` | yes | ✅ (NEW per Prince 2026-05-13) |
| `VIMS-Certs-Module/LESSONS.md` | yes | ✅ (scaffold) |
| `VIMS-Certs-Module/COVERAGE.md` | yes | ✅ (this file) |
| `VIMS-Certs-Module/progress.txt` | yes | ✅ |
| `VIMS-Certs-Module/tasks/todo.md` | yes | ✅ |

**Audit 2 result: ✅ PASS**

---

## 4. Audit 3 — Database Tables

Per BACKEND §3, the 18 `vims_certs_*` tables:

1. `vims_certs_catalog_section` ✅
2. `vims_certs_catalog_row` ✅
3. `vims_certs_class_code_mapping` ✅
4. `vims_certs_tracked_item` ✅
5. `vims_certs_pdf_blob` ✅
6. `vims_certs_class_status_snapshot` ✅
7. `vims_certs_reconciliation_run` ✅
8. `vims_certs_reconciliation_flag` ✅
9. `vims_certs_audit_log` ✅
10. `vims_certs_alert_config` ✅
11. `vims_certs_approval_event` ✅
12. `vims_certs_notification_meta` ✅
13. `vims_certs_print_artifact` ✅
14. `vims_certs_external_auditor_access` ✅
15. `vims_certs_batch_ingest` ✅
16. `vims_certs_vessel_config` ✅
17. `vims_certs_modification_event` ✅
18. `vims_certs_settings` ✅

All schemas defined in BACKEND §3; FIELD_MAP §1–§18 traces every column.

**DB role separation:** `vims_app` INSERT+SELECT only on `vims_certs_audit_log` and Certs rows in `master_notification`. `vims_admin` for migrations. (D-CERT-179, BACKEND §2.) ✅

**Audit 3 result: ✅ PASS**

---

## 5. Audit 4 — Permission IDs

Form IDs (8):
- CERT_F_001 (Catalog Mgmt)
- CERT_F_002 (Tracked Items)
- CERT_F_003 (Reconciliation)
- CERT_F_004 (Print/Export)
- CERT_F_005 (Onboarding Wizard)
- CERT_F_006 (Notification Config)
- CERT_F_007 (External Auditor Provisioning)
- CERT_F_008 (Audit Log)

Process IDs (10):
- CERT_P_001 (Create)
- CERT_P_002 (Submit)
- CERT_P_003 (Approve)
- CERT_P_004 (Reject)
- CERT_P_005 (Print)
- CERT_P_006 (Export Bundle)
- CERT_P_007 (Provision Auditor)
- CERT_P_008 (Catalog Edit)
- CERT_P_009 (Bulk Action)
- CERT_P_010 (Rollback)

Stored in shared `msc_profiles` (D-CERT-090); seeded by `seed_certs_permissions` mgmt command (Phase 0.5, IMPLEMENTATION_PLAN.md). All endpoints in BACKEND §5 cite their `(form_id, process_id)` requirement.

**Audit 4 result: ✅ PASS**

---

## 6. Audit 5 — FIELD_MAP Completeness (NEW)

Per Prince's 2026-05-13 directive: every BACKEND column has a FIELD_MAP row.

| Table | BS rows | FM rows | Status | Notes |
|-------|--------:|--------:|--------|-------|
| `vims_certs_catalog_section` | 5 | 5 | ✅ | Audit block collapsed to 1 row in both (standardized 2026-05-13 per GAP-019 fix) |
| `vims_certs_catalog_row` | 28 | 28 | ✅ | Audit block collapsed to 1 row in both (standardized 2026-05-13 per GAP-019 fix) |
| `vims_certs_class_code_mapping` | 9 | 9 | ✅ | Audit block collapsed to 1 row in both |
| `vims_certs_tracked_item` | 41 | 41 | ✅ | Audit block collapsed to 1 row in both |
| `vims_certs_pdf_blob` | 20 | 18 | ✅ notation OK | FM collapses 2 related cols into 1 row for UI brevity; same DB columns, no missing |
| `vims_certs_class_status_snapshot` | 18 | 16 | ✅ notation OK | FM collapses 2 related cols for UI brevity; same DB columns |
| `vims_certs_reconciliation_run` | 14 | 8 | ✅ notation OK | FM collapses 7 bucket-count cols (`matches_count` … `unmapped_low_confidence_count`) into 1 row for UI brevity |
| `vims_certs_reconciliation_flag` | 11 | 10 | ✅ notation OK | FM collapses related cols for UI brevity |
| `vims_certs_audit_log` | 15 | 15 | ✅ | Aligned |
| `vims_certs_alert_config` | 15 | 15 | ✅ | Audit block collapsed to 1 row in both |
| `vims_certs_approval_event` | 8 | 6 | ✅ notation OK | FM collapses related cols for UI brevity |
| `vims_certs_notification_meta` | 16 | 16 | ✅ | Aligned |
| `vims_certs_print_artifact` | 19 | 18 | ✅ notation OK | FM collapses 2 related cols for UI brevity |
| `vims_certs_external_auditor_access` | 12 | 12 | ✅ | Aligned |
| `vims_certs_batch_ingest` | 17 | 14 | ✅ notation OK | FM collapses related cols for UI brevity |
| `vims_certs_vessel_config` | 17 | 17 | ✅ | Audit block collapsed to 1 row in both |
| `vims_certs_modification_event` | 6 | 5 | ✅ notation OK | FM collapses related cols for UI brevity |
| `vims_certs_settings` | 0 | 0 | ⚠️ Phase 0 build-time flag | Single-row config; final shape deferred to Phase 0 |

**Notation convention (locked 2026-05-13 per audit GAP-019 fix):**
- Audit block `(created_at, created_by, updated_at, updated_by)` is rendered as **1 collapsed row** in both BACKEND §3.x and FIELD_MAP §N. Previously BS had it expanded as 2–4 rows for some tables; collapsed for `catalog_section` and `catalog_row` as part of this fix.
- Where BS row count differs from FM row count (`pdf_blob`, `class_status_snapshot`, `reconciliation_run`, `reconciliation_flag`, `approval_event`, `print_artifact`, `batch_ingest`, `modification_event`), FM has collapsed a group of related columns (bucket counts, dimension pairs) into 1 row for readability. The underlying DB column set is identical and matches BACKEND §3 column-by-column. No column is missing from FIELD_MAP.

**Status legend distribution across FIELD_MAP rows:**
- ✅ Built (column → API → component → role): majority
- 🔧 Internal (justified non-surface): IDs, version-tracking, server-only computation fields
- 🔒 RBAC-redacted (visible to some roles, redacted to others): free-text reason fields per D-CERT-180
- ⚠️ Missing UI / build-time flag: only `vims_certs_settings` (final shape deferred to Phase 0); `linked_pms_component_id` on catalog row (cross-module fetch deferred per D-CERT-176 — value stored only)

**Audit 5 result: ✅ PASS** with 2 documented Phase 0 deferrals.

---

## 7. Final Gate

| Gate | Status |
|------|--------|
| 198 / 198 D-CERT-\* covered (each in ≥1 doc; PRD as anchor) | ✅ GREEN |
| Naming convention | ✅ PASS |
| Folder structure | ✅ PASS |
| DB tables | ✅ PASS |
| Permission IDs | ✅ PASS |
| FIELD_MAP completeness | ✅ PASS (2 documented Phase 0 deferrals) |

**OVERALL: ✅ DOCSUITE GREEN — READY FOR PHASE 0 BUILD.**

Mirrors VIMS-Safety-Module's 159/159 GREEN gate that unlocked Phase 0 build.

---

## 8. What This Unlocks

Phase 0 build can begin per IMPLEMENTATION_PLAN.md sequence. State will live in `progress.txt` post-lock; `LESSONS.md` populates as corrections accumulate.

Per CLAUDE.md completion checklist, every Phase 0+ PR that adds a column or API field must add the matching FIELD_MAP row, or the merge is blocked. This is how we prevent the "backend done, UI missing" failure mode that prompted the FIELD_MAP doc creation in the first place.

---

*End of COVERAGE v1.0. Re-run this report whenever a doc is updated or a new D-CERT-\* is added.*
