# Audit Response 6 - Four Open Items

1. Authoritative commit:
   Use the latest `main` commit in `https://github.com/himani-ux/VIMS_Audit.git` after pull. Do not use `a2f308127f1e9b03137408deb08c5fe1a7e6ad52` or `a87176d`. The repo now includes `QUALITY_GATE_STAMP.json` and `audit_docsuite/AUDIT_RUNTIME_GAPS.md` for direct review.

2. Rerun list:
   `JOURNEY-11` is back on the rerun list. `JOURNEY-1` and `JOURNEY-9` are also treated as unvalidated until rerun with raw evidence. No earlier narrative pass is being claimed as final evidence.

3. UAT report format:
   Going forward, every journey result will be packaged as `UAT_REPORT_<date>.md` using `journey/docs/uat-report-format.md`, with path:line evidence, raw command output/logs, route tested, account/persona used, record IDs, and artifact hashes or screenshots where manual evidence is used.

4. Credential rotation:
   Credential rotation remains a separate account-admin item. No plaintext passwords are included in this repo response. Code/evidence review can continue in parallel, but closure needs one-line confirmation from the account owner with the rotated accounts and rotation date.
