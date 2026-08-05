---
document_id: KB-005
title: API Credentials
updated: 2026-07-18
status: current
tags: [api, credentials, tokens, permissions, security]
---

# API Credentials

OrbitDesk uses workspace API credentials for server-to-server integrations. Only Owners and Admins can create or revoke credentials. Analysts and Viewers cannot create API credentials.

## Creating a Credential

An Owner or Admin can create a credential from **Settings > Developer > API credentials**. The secret is shown once at creation and cannot be revealed again. If the secret is lost, revoke the credential and create a replacement.

Each credential has:

- A display name
- One or more scopes
- A creation timestamp
- An optional expiration date
- A last-used timestamp

## Scope Guidance

Choose the narrowest scopes required by the integration. A credential with `dashboards:read` cannot create or edit dashboards. Creating a credential does not grant access beyond the permissions represented by its scopes.

## Security Rules

- Never ask a user to paste a credential secret into chat, logs or a recording.
- Never store a secret in source control.
- Revoke a credential immediately if exposure is suspected.
- Credential secrets cannot be recovered by support.

## Legacy Personal Tokens

Legacy personal API tokens were removed in OrbitDesk version 4.0. Guidance that tells an Analyst to create a token from **Profile > Personal token** is obsolete and must not be followed. Use a workspace credential created by an Owner or Admin instead.
