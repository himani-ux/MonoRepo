# TEST_SURFACE — public black-box contract (golden fixture)
# resolve = attached in the DOM on screen load (not necessarily visible);
# visibility at the right moment is the journey specs' job.

## SURFACE: invoices_list
route: /invoices
allowed_selectors:
  - role=button[name="Upload invoice"]
  - role=button[name="Retry"]
  - role=table[name="Invoices"]
  - testid=invoice-list
  - testid=invoice-status
  - testid=upload-error
  - testid=upload-input
observable_states: [EMPTY, ERROR, SUCCESS]
public_api: [GET /invoices, POST /invoices/import]
