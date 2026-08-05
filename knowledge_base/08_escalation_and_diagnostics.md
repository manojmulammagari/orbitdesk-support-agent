---
document_id: KB-008
title: Escalation and Diagnostic Information
updated: 2026-07-20
status: current
tags: [support, escalation, diagnostics, privacy, logs]
---

# Escalation and Diagnostic Information

Escalate only after completing the documented checks for the affected feature or when the request requires an action that the support assistant cannot perform.

## Information to Collect

Include only information relevant to the failure:

- Workspace ID
- Affected object ID, such as a schedule, dashboard, connection or credential ID
- Exact error code and visible error message
- Timestamps with timezone
- Relevant run, refresh or request IDs
- Reproduction steps
- Expected and observed behaviour
- Troubleshooting steps already attempted

## Information Never to Collect

Do not request or include:

- Passwords
- API credential secrets
- OAuth access or refresh tokens
- Full exported customer datasets
- Payment-card numbers
- Session cookies

Screenshots are optional and should be cropped to remove unrelated customer information.

## Escalation Conditions

- Two consecutive `render_failed` events for the same dashboard after documented checks
- Two repeated `connector_internal_error` failures
- Suspected credential exposure
- Billing actions, ownership disputes or legal requests
- A reproducible error not described in the current knowledge base

An escalation response should summarize the evidence and identify the appropriate human team. It must not promise a resolution time unless a supplied document states one.
