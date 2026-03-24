# Sync Module

## Path

- `psc-backend/apps/sync/`

## Purpose

This module owns offline synchronization between vessel devices and the server. It tracks sync runs, processes queued mutations, detects conflicts, issues attachment upload tokens, and records sync state per vessel.

## Owns

- Pull API for delta sync
- Push API for queued vessel mutations
- Upload token flow for attachment files
- Conflict creation, listing, and resolution
- Sync logs, log details, conflicts, and sync tokens

## Main Files

- `models.py`: sync log, detail, conflict, token models
- `sync_service.py`: pull/push orchestration
- `conflict_resolver.py`: conflict diffing and resolution side effects
- `views.py`: API wrapper layer
- `serializers.py`: payload contracts

## Workflow

1. Vessel client sends `pull` with `last_server_version` and optional sync token.
2. Server returns changed inspections, deficiencies, CARs, actions, evidence metadata, activity history, and master data.
3. Vessel client stores changes in IndexedDB and updates local sync token/version.
4. Vessel client later sends queued `push` events and attachment metadata.
5. Server applies create/update/delete operations or records conflicts when client version lags server version.
6. Office users can resolve conflicts with `KEEP_SERVER`, `KEEP_VESSEL`, or `REOPEN_FOR_MERGE`.

## Dependencies

- `apps.inspection` and `apps.car` entity models
- `apps.notifications` for conflict detected/resolved alerts
- Frontend `lib/db`, `lib/sync`, and sync status UI

## Notes

- The sync contract assumes monotonically increasing `sync_version` on mutable entities.
- Attachments are a two-step flow: push metadata first, then upload file bytes through tokenized upload URLs.
