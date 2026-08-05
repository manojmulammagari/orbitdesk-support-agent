---
document_id: KB-009
title: Audit Logs
updated: 2026-07-05
status: current
tags: [audit, events, history, timezone, security]
---

# Audit Logs

Owners and Admins can view workspace audit logs from **Settings > Audit log**. Analysts and Viewers do not have access to the audit-log page.

## Recorded Events

OrbitDesk records events for:

- Member invitations and role changes
- Workspace-setting changes
- Connection creation, reauthorization and disablement
- Export-schedule creation, update, pause and deletion
- API credential creation and revocation

Secret values and exported file contents are never stored in the audit log.

## Time and Retention

Audit events are stored in UTC and displayed using the viewer's selected locale. Changing the workspace timezone does not rewrite historical audit timestamps. Audit events are retained for 90 days.

## Troubleshooting

When comparing an audit event with a scheduled run, include the displayed timezone or convert both timestamps to UTC. A timezone display difference does not by itself indicate that an event occurred at the wrong time.

OrbitDesk support cannot restore events after the retention period. Do not claim that absence from the audit log proves an action never occurred if the relevant time is more than 90 days ago.
