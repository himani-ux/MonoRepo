# TEST_SURFACE — public black-box contract (golden fixture)

## SURFACE: invoices_list
route: /invoices
allowed_selectors:
  - div.upload > button.primary
  - role=table[name="Invoices"]
  - testid=invoice-list
  - testid=upload-error
observable_states: [EMPTY, ERROR, SUCCESS]
public_api: [GET /invoices, POST /invoices/import]
