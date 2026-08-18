# TEST_SURFACE — public black-box contract (golden fixture)

## SURFACE: invoices_list
allowed_selectors:
  - role=button[name="Upload invoice"]
  - role=table[name="Invoices"]
  - testid=invoice-list
  - testid=upload-error
observable_states: [EMPTY, ERROR, SUCCESS]
public_api: [GET /invoices, POST /invoices/import]
