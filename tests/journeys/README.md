# Audit Journey Tests

These are first-pass executable Playwright journeys for the VIMS Audit module.
They are intentionally environment-driven and do not hardcode live credentials.

## Run

Install the journey Playwright island once:

```sh
cd journey/surface-check
npm install
```

Start the backend and frontend, then run:

```sh
cd journey/surface-check
APP_BASE_URL=http://localhost:5173 \
JOURNEY_USERNAME=<user> \
JOURNEY_PASSWORD=<password> \
JOURNEY_TESTS_DIR=../../tests/journeys \
npx playwright test
```

PowerShell equivalent:

```powershell
cd journey\surface-check
$env:APP_BASE_URL = "http://localhost:5173"
$env:JOURNEY_USERNAME = "<user>"
$env:JOURNEY_PASSWORD = "<password>"
$env:JOURNEY_TESTS_DIR = "..\..\tests\journeys"
npx playwright test
```

Optional IDs unlock the record-specific closure journeys:

```sh
JOURNEY_AUDIT_ID=<audit_uuid>
JOURNEY_NC_FINDING_ID=<finding_uuid>
JOURNEY_OBS_FINDING_ID=<finding_uuid>
JOURNEY_EXTERNAL_AUDIT_ID=<audit_uuid>
JOURNEY_ACTING_HOD_ROUTE=<route_if_implemented>
```

These tests prove that the documented journeys are now executable drafts. A
real GREEN journey claim still requires stable sample data, a trusted ledger,
and DPA/senior confirmation of the business outcomes.
