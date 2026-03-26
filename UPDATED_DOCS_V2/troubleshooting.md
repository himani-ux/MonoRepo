# Troubleshooting

## 1. Authentication Problems

### Symptom: Login fails for valid vessel credentials

Possible causes:

- `Ship_UsersLogin` record is inactive or deleted
- password hash mismatch or legacy password format mismatch
- onboarding record does not map to the expected vessel

Fix:

- verify crew ID and vessel onboarding data
- verify the custom authentication backend can read the unmanaged tables

### Symptom: Login works but API requests return 401

Possible causes:

- access token missing from local storage
- token expired and refresh token is also expired
- client did not register the auth store accessor

Fix:

- clear local auth state
- log in again
- inspect the Axios interceptor and auth store initialization path

## 2. Permission Problems

### Symptom: Office user cannot see a vessel

Possible causes:

- user has no vessel assignment in `master_RoleByVessel`
- user is not a global PIC/DPA reviewer

Fix:

- verify mapping tables
- verify the user's role/profile mapping

### Symptom: Vessel user cannot open a CAR or inspection detail

Possible causes:

- vessel ID mismatch in token
- the item belongs to a different vessel
- crew user is not assigned to the underlying deficiency/action

Fix:

- verify JWT claims
- verify vessel scope
- verify assignment fields on the deficiency or CAR

## 3. File Upload Problems

### Symptom: Inspection report upload fails

Possible causes:

- file type is not PDF/JPG/JPEG
- file exceeds 3MB
- upload path is not writable

Fix:

- confirm file constraints
- confirm upload directory permissions

### Symptom: Company logo upload fails

Possible causes:

- non-office user
- invalid image type
- file larger than 2MB

Fix:

- use office account
- upload PNG or JPG only

## 4. Sync Problems

### Symptom: Sync now does nothing while offline

Behavior:

- this is expected
- sync is blocked until connectivity returns

### Symptom: Sync push rejects checksum

Possible causes:

- event payload changed after checksum generation
- duplicate event IDs
- payload serialization mismatch

Fix:

- regenerate the sync checksum from the exact event array being sent

### Symptom: Conflict list is empty even though sync reported a conflict

Possible causes:

- query cache is stale
- sync conflict query has not been invalidated

Fix:

- refresh the conflict query
- re-run sync or invalidate the query after resolution

## 5. Inspection Workflow Problems

### Symptom: Cannot submit inspection

Possible causes:

- no report attached
- one or more deficiencies have no CAR
- inspection is not in draft status

Fix:

- attach a report
- ensure every deficiency auto-created a CAR

### Symptom: Follow-up wizard rejects the date

Possible causes:

- follow-up date is in the future
- follow-up date is before the original inspection

Fix:

- enter a valid date within the allowed range

## 6. CAR Workflow Problems

### Symptom: CAR cannot be edited

Possible causes:

- CAR is closed
- vessel user is not a master
- status is not editable for the selected role

Fix:

- confirm the current status and role matrix

### Symptom: Evidence upload is blocked

Possible causes:

- wrong role
- assigned-crew check failed

Fix:

- verify assignment ownership and CAR state

## 7. Circular / ORB Problems

### Symptom: Legacy module does not render

Possible causes:

- auth state not initialized
- legacy provider not mounted

Fix:

- ensure the route is inside the modern authenticated shell

### Symptom: ORB approved entries screen is blank

Possible causes:

- backend ORB API is unreachable
- user is not in the expected office role

Fix:

- verify ORB API connectivity
- verify the office role mapping

## 8. General Debugging Tips

- check backend logs first for permission and validation failures
- check browser network requests for 401/403/500 responses
- verify route constants before assuming a screen path changed
- remember that the backend uses custom user claims instead of Django auth user records

