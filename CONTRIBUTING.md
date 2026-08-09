# Contributing

## Branch strategy

This repository uses a staged promotion flow:

`feat/*` or `feature/*` -> `development` -> `main` with `realse` tag

## Required merge path

- Create changes on a feature branch (`feat/*` or `feature/*`).
- Open a Pull Request from your feature branch to `development`.
- After validation in `development`, open a Pull Request from `development` to `main`.

## Protected branches

- Direct push to `development` is blocked.
- Direct push to `main` is blocked.
- Merges must happen through Pull Requests.

## Pull Request expectations

- CI checks must pass.
- At least one approval is required.
- PR description should include scope, risk, and rollback approach.
- Runtime-impacting changes should include test evidence (logs, screenshots, or command output).

## Required status checks

Configure branch rules so the following check is required:

- `Validate PR source policy / enforce-source-policy`

Recommended branch protection settings:

For `development`:
- Require a pull request before merging
- Require status checks to pass before merging
- Require at least one approval
- Dismiss stale approvals when new commits are pushed

For `main`:
- Require a pull request before merging
- Require status checks to pass before merging
- Require at least one approval
- Restrict who can push (or block direct pushes)
