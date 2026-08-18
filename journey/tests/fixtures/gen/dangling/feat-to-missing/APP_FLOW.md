# Application Flow

## User Journeys

### AFJ-001 — "Corrected invoice upload"
covers_features: FEAT-001
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error displayed inline
  3. fix the CSV locally, re-upload corrected.csv
  4. observe status=ACCEPTED in the invoice list
states: [EMPTY, ERROR, SUCCESS]
