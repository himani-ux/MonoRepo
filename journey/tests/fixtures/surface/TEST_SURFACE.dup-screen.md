# TEST_SURFACE — public black-box contract (golden fixture)

## SURFACE: invoices_list
route: /invoices
allowed_selectors:
  - role=button[name="Upload invoice"]
  - role=table[name="Invoices"]
  - testid=invoice-list
  - testid=upload-error
observable_states: [EMPTY, ERROR, SUCCESS]
public_api: [GET /invoices, POST /invoices/import]

## SURFACE: invoices_list
route: /dup
allowed_selectors:
  - testid=x
observable_states: [EMPTY]
public_api: []
