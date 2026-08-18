# Application Flow

## Overview

This document describes the core user flows through the invoice-processing
system from the perspective of the ops user and the finance reviewer.

## User Journeys

### AFJ-001 — "Corrected invoice upload"
covers_features: FEAT-001
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error displayed inline
  3. fix the CSV locally, re-upload corrected.csv
  4. observe status=ACCEPTED in the invoice list
states: [EMPTY, ERROR, SUCCESS]

### AFJ-002 — "Invoice retry workflow"
covers_features: FEAT-002
steps:
  1. land on /invoices with an existing REJECTED row
  2. click Retry on the rejected row
  3. upload a corrected version of the file
  4. observe the status transition: REJECTED -> ACCEPTED
states: [REJECTED, ACCEPTED]

## Screens

### SCR-001 — "invoices_list"
route: /invoices
states: [EMPTY, LOADING, ERROR, SUCCESS]
