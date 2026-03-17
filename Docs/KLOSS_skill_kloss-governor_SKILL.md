---
name: kloss-governor
description: Enforce Kloss standards: read the referenced spec file first, execute only the requested phase, cite repo evidence for every claim, and stop on missing inputs. Use when the user says "Kloss", "phase-wise", "no guesswork", or references docs/* spec files.
---

# Kloss Governor (non-negotiable)

## Core behavior
1) Always read the user-specified spec file first (typically under docs/). If not found, stop and report the missing path.
2) Execute ONLY the phase explicitly requested by the user. Do not proceed to later phases.
3) No guesswork: every claim must be supported by repo evidence (file paths + line refs where possible).
4) If a required artifact is missing (example: template Excel), stop and report "MISSING" with exact expected path.
5) Do not modify existing behavior unless the phase explicitly requires it.

## Evidence standards
For each conclusion, cite:
- file path(s)
- symbol name (function/class/component) where applicable
- line numbers if available in your environment

## Phase gating defaults
- Phase 1: audit only (no migrations, no new endpoints, no UI changes)
- Phase 2+: only execute when the user explicitly requests that phase

## Output format
Match the phase’s required output sections exactly as defined in the spec file.
