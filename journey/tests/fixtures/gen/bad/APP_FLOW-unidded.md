# Application Flow

## User Journeys

### Corrected invoice upload
covers_features: FEAT-001
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error
  3. re-upload corrected.csv
  4. observe ACCEPTED
states: [EMPTY, ERROR, SUCCESS]
