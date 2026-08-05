---
document_id: KB-007
title: Export Delivery Destinations
updated: 2026-06-29
status: current
tags: [exports, email, storage, destination, verification]
---

# Export Delivery Destinations

Scheduled exports can be delivered by email or to a configured cloud-storage destination.

## Email Destinations

The first export to a new external email domain requires destination verification by an Owner or Admin. Until verification is complete, run history shows `destination_unverified`. Verification links expire after 24 hours and can be resent from **Settings > Export destinations**.

A schedule may contain up to 20 email recipients. OrbitDesk records delivery acceptance by the receiving mail server but cannot confirm that a recipient opened the message.

## Storage Destinations

Storage destinations can enter `reauthorization_required` if the external provider revokes access. An Owner or Admin must reconnect the destination. Analysts can view the destination state but cannot update its secret configuration.

## Safe Troubleshooting

Confirm the destination name, type and state. Do not ask the user to share access keys or authorization tokens. If delivery was accepted but the recipient cannot find the message, recommend checking spam filtering and allow-listing `exports@orbitdesk.example`.

OrbitDesk cannot resend the exact historical file after its seven-day retention window. The user may run the dashboard again, but the regenerated file may contain newer data.
