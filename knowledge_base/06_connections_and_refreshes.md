---
document_id: KB-006
title: Connections and Data Refreshes
updated: 2026-07-11
status: current
tags: [connections, sync, refresh, data, troubleshooting]
---

# Connections and Data Refreshes

OrbitDesk dashboards may depend on one or more data connections. Owners and Admins can create and edit connections. Analysts can view non-secret settings and start a manual refresh when the connection allows it.

## Connection States

- **Active:** Available for queries and scheduled refreshes.
- **Refreshing:** A refresh is currently running.
- **Reauthorization required:** The external authorization has expired or been revoked.
- **Disabled:** An Owner or Admin has disabled the connection.
- **Error:** The most recent refresh failed.

## Refresh Behaviour

Only one refresh can run for a connection at a time. A second request returns `refresh_already_running`. Scheduled exports wait up to 15 minutes for required refreshes. If a refresh takes longer, the export run ends with `source_refresh_timeout` even if the refresh later succeeds.

## Troubleshooting

The phrase “sync is not working” is not specific enough to diagnose a connection problem. Ask for:

- Workspace ID
- Connection name or ID
- Current connection state
- Last successful refresh time
- Latest error code
- Whether manual and scheduled refreshes are both affected

Do not ask for database passwords, OAuth tokens or API secrets.

For `reauthorization_required`, an Owner or Admin must reconnect the data source. For repeated `connector_internal_error` failures, escalate with the connection ID, refresh job IDs and timestamps after two failed attempts.
