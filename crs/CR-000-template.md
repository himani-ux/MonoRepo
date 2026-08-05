# CR-000 - Change Record Template

Use this template for Tier 2 and Tier 3 changes. Copy it to the next sequential file, for example `crs/CR-001.md`, before coding.

## What & why

One paragraph in plain language.

## Tier + triggers

State the tier and objective trigger(s).

## Domains touched

List affected Step 1 domain numbers. These drive mini-interrogation and doc cascade.

## Decisions

List new decision IDs and any supersessions explicitly. Use the same decision ID scheme as the SSOT.

## Doc cascade

List every canonical doc updated and what changed.

Docs not updated that a reviewer might expect:
- `<doc>` - unchanged because `<reason>`.

## Tests

List regression or new tests added.

## Fidelity check

For Tier 2 and Tier 3, re-read mini-interrogation answers against doc updates side by side and list anything missing or weakened.

If there are no gaps, write:

```text
no deltas
```

## Exemptions

List any `DOCS-EXEMPT`, `TEST-EXEMPT`, or `STATES-EXEMPT` used, with reason and repayment plan.

If none, write:

```text
none
```
