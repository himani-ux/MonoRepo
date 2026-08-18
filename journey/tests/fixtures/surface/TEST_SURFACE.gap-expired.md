# TEST_SURFACE — valid structured gap fixture

## SURFACE: invoices_list
route: /invoices
allowed_selectors:
  - role=button[name="Upload invoice"]
observable_states: [EMPTY]
public_api: [GET /invoices]

## SURFACE-GAP: admin_console
gap:
  reason: "NOT_IMPLEMENTED"
  owner: "prince"
  reviewer: "prince"
  expires: "2020-01-01"
  evidence: "APP_FLOW SCR-002"
