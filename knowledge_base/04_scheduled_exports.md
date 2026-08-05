---
document_id: KB-004
title: Scheduled Exports
updated: 2026-07-15
status: current
tags: [exports, schedule, delivery, email, storage, troubleshooting]
---

# Scheduled Exports

OrbitDesk can render a dashboard as PDF or CSV on a recurring or one-time schedule. Analysts, Admins and Owners can create schedules. Viewers cannot create or edit schedules.

## Schedule States

- **Active:** Eligible to run at the next scheduled time.
- **Paused:** Will not run until resumed.
- **Needs attention:** A required dashboard, connection or destination is unavailable.
- **Running:** Rendering or delivery is in progress.

## Run Sequence

At the scheduled time, OrbitDesk performs these steps:

1. Confirms that the schedule is active.
2. Confirms that the dashboard still exists and the schedule owner still has access.
3. Waits for required data-source refreshes for up to 15 minutes.
4. Renders the requested format.
5. Delivers the file to the configured email or storage destination.

## Troubleshooting a Missed Export

Check the following in order:

1. Confirm the schedule state and next-run time.
2. If the workspace timezone recently changed, follow `KB-003` and resave the schedule.
3. Open **Schedule > Run history** and note the latest run status and error code.
4. Confirm that the dashboard exists and that the schedule owner can still open it.
5. Confirm that all required connections are active.
6. Confirm that the destination is verified and enabled.

## Common Error Codes

- `source_refresh_timeout`: A required connection did not finish refreshing within 15 minutes. The export is not retried automatically.
- `destination_unverified`: Delivery is blocked until the destination is verified.
- `owner_access_revoked`: The schedule owner no longer has access to the dashboard.
- `render_failed`: Rendering failed after the data checks completed.

Use **Run now** after correcting the cause. A manual run does not alter the recurring schedule's next-run time.

Escalate after two consecutive `render_failed` events for the same dashboard. Include the schedule ID, dashboard ID, run IDs and timestamps. Never include exported customer data in an escalation note.
