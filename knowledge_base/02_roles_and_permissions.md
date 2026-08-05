---
document_id: KB-002
title: Roles and Permissions
updated: 2026-07-01
status: current
tags: [roles, permissions, owner, admin, analyst, viewer]
---

# Roles and Permissions

OrbitDesk has four workspace roles. Permissions apply only within the workspace where the role is assigned.

## Owner

An Owner can manage billing, transfer workspace ownership, delete the workspace, manage members, create workspace API credentials and perform all Admin and Analyst actions. Each workspace must have at least one Owner.

## Admin

An Admin can manage members except Owners, manage workspace settings, create or revoke workspace API credentials, manage connections and perform all Analyst actions. An Admin cannot manage billing, transfer ownership or delete the workspace.

## Analyst

An Analyst can create and edit dashboards, run manual exports, create export schedules and view non-secret connection settings. An Analyst cannot invite members, change workspace settings, reveal stored secrets or create API credentials.

## Viewer

A Viewer has read-only access to dashboards shared with them. A Viewer can download an export when the dashboard owner has enabled downloads. A Viewer cannot edit dashboards, create schedules, manage connections, change workspace settings or create API credentials.

## Permission Failures

If a user sees `permission_denied`, first identify their workspace role and the action they attempted. Do not recommend changing the user to Owner unless the action specifically requires ownership. For API credential creation, either an Owner or Admin is sufficient.
