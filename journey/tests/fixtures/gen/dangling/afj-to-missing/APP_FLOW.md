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

### AFJ-005 — "Document metadata editor"
covers_features: FEAT-999
steps:
  1. open a document record
  2. edit metadata fields
  3. save and observe confirmation
states: [EDITING, SAVED]
