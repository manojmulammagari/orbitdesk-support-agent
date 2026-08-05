---
document_id: KB-003
title: Workspace Settings and Timezones
updated: 2026-07-08
status: current
tags: [workspace, settings, timezone, locale, schedules]
---

# Workspace Settings and Timezones

Owners and Admins can change workspace settings from **Settings > Workspace**. The workspace timezone controls how dates are displayed and how new recurring schedules interpret local time.

## Changing the Timezone

Changing the workspace timezone does not immediately rewrite existing recurring export schedules. Existing schedules retain the timezone stored when they were last saved and display a `Timezone update pending` notice.

To apply the new workspace timezone to an existing recurring schedule:

1. Open the schedule.
2. Review the displayed next-run time.
3. Select **Save schedule**, even if no other field changes.
4. Confirm that the `Timezone update pending` notice disappears.

Resaving changes future run times only. It does not create a replacement run for an export that was already missed.

## Other Time-related Behaviour

- New recurring schedules use the current workspace timezone.
- One-time exports store an absolute timestamp and do not move when the workspace timezone changes.
- Audit-log events are stored in UTC and displayed in the viewer's selected locale.
- Daylight-saving changes are applied using the timezone stored on the schedule.

If the schedule still does not run after being resaved, continue with the checks in `KB-004 Scheduled Exports`.
