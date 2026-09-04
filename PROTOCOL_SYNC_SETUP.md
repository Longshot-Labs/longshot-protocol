# Protocol sync and release setup

This repository is a deterministic output of `Longshot-Labs/longshot`. The
code fails closed until an organization owner completes the controls below.
Do not add a token to a pull request workflow.

## Required parent input

The upstream monorepo must contain the checked public-pruned OpenAPI fixture at
`longshot-protocol/fixtures/api/openapi.json`. The exporter does not fall back
to `fixtures/api/openapi.json` at the monorepo root. A missing public fixture
stops the export.

Upstream `Protocol Export` runs the public OpenAPI pruner in `--check` mode.
The pruner and its private exclusion contract are upstream-only. The public
allowlist is exported because the serde generator imports it. Downstream CI
verifies the pruned fixture through provenance and the serde metadata check.

## Real code owners

Choose verified Longshot organization users or teams. No owner identity is
provided by the generated files.

Add these exact upstream patterns to the monorepo `.github/CODEOWNERS`:

```text
/.github/CODEOWNERS <verified-owner>
/.github/workflows/ <verified-owner>
/longshot-protocol/ <verified-owner>
/scripts/protocol_sync/ <verified-owner>
```

Add these exact downstream patterns to the canonical upstream overlay at
`scripts/protocol_sync/downstream/.github/CODEOWNERS`, then add that file to
`scripts/protocol_sync/export-map.json`:

```text
/.github/CODEOWNERS <verified-owner>
/.github/workflows/ <verified-owner>
/SOURCE.json <verified-owner>
/scripts/ <verified-owner>
```

The gates stop if either file or any exact pattern is absent. They also use
GitHub's CODEOWNERS error endpoint to reject invalid patterns or owners.

## Protect both main branches

Create classic branch protection for `main` in both repositories. The current
gate does not accept a ruleset as a substitute. Require all of these settings:

- Changes enter through a pull request.
- At least one approval is required.
- Code-owner review is required.
- Stale approvals are dismissed.
- The most recent push needs approval from another person.
- Administrators follow the rule.
- No user, team, or application can bypass the pull request rule.
- Required checks must pass on an up-to-date branch.
- Each required check is app-bound to GitHub Actions, not a legacy unbound
  status context.
- Force pushes and branch deletion are blocked.

Require `Protocol Export` upstream. Require `provenance`, `rust`, `python`, and
`typescript` downstream. Do not give the sync application a bypass.

Enable automatic deletion of head branches after pull requests merge in the
downstream repository. The bot refuses to overwrite its fixed branch unless
that branch still has one open pull request created by the same GitHub App.

## Create the downstream write application

Create a dedicated GitHub App for sync. Install it only on
`Longshot-Labs/longshot-protocol`. Grant only metadata read, contents write,
pull requests write, and workflows write. Workflows write is required because
the deterministic export owns downstream CI and release workflow files.
This write App and the read-only App below must be separate GitHub Apps with
different positive ASCII-decimal application IDs.

Create the upstream `protocol-sync` environment. Allow protected branches
only, disable administrator bypass, and do not add a required reviewer because
this environment runs after protected main CI. Set:

- Environment variable `PROTOCOL_SYNC_ENABLED=true`.
- Environment variable `PROTOCOL_SYNC_ENVIRONMENT_CONFIGURED=v1`.
- Environment variable `LONGSHOT_PROTOCOL_READ_APP_ID` to the read-only
  application ID described below.
- Environment secret `LONGSHOT_PROTOCOL_READ_APP_PRIVATE_KEY` to the read-only
  application private key.
- Environment variable `LONGSHOT_PROTOCOL_SYNC_APP_ID` to the application ID.
- Environment secret `LONGSHOT_PROTOCOL_SYNC_APP_PRIVATE_KEY` to its private
  key.

After the local source and double-export checks, the workflow requests a
read-only token for only `longshot`. It checks classic branch protection and
the environment, then requests a write token for only the downstream
repository. It never runs for a pull request event and never checks out pull
request code in the privileged job.

## Create the read-only settings and release application

Create a separate GitHub App for settings and release verification. Install it
only on the two Longshot repositories. Grant metadata read plus Actions read,
administration read, checks read, contents read, and pull requests read. It has
no write permission. The sync workflow scopes this application's token to
`longshot`; the release workflow scopes its token to both repositories.

Create the downstream `protocol-release` environment. Require at least one
human reviewer, prevent self-review, allow protected branches only, and disable
administrator bypass. Set:

- Environment variable `PROTOCOL_RELEASE_ENABLED=true`.
- Environment variable `PROTOCOL_RELEASE_ENVIRONMENT_CONFIGURED=v1`.
- Environment variable `LONGSHOT_PROTOCOL_READ_APP_ID` to the application ID.
- Environment secret `LONGSHOT_PROTOCOL_READ_APP_PRIVATE_KEY` to its private
  key.

The release workflow replays the source commit recorded in `SOURCE.json`, then
renders current upstream `main`. It requires an exact recorded-source match and
an exact latest payload match. It also checks that the recorded source is in
protected `main` history, both branch protections, current downstream CI, the
release environment, code owners, versions, and the absence of an open sync
pull request.

## Package publication remains disabled

The release workflow checks readiness only. It does not hold registry
credentials, invoke a helper with `--publish`, or publish a package. The Rust,
Python, and TypeScript helpers each support `--check` and `--publish` so a
future workflow can publish the exact archives produced by the shared package
audit. Their source manifests block direct package-manager publication paths.

Add a separate reviewed registry workflow only after registry ownership and
trusted publishing are configured. Keep registry credentials and trusted
publisher authority restricted to that gated workflow and the
`protocol-release` environment. That workflow, not the readiness workflow,
must invoke the three helpers with `--publish`. Every publish job must depend
on the readiness gate for the same commit and version. Repository code cannot
prevent a registry owner from publishing by another method.

## Enable the bot

First resolve any older manually maintained downstream sync pull request. Then
complete the controls above and enable the application variables and secrets.
The bot owns `automation/sync-from-longshot-main` and opens or updates one pull
request. Keep automatic head-branch deletion enabled so a merged bot pull
request cannot leave a stale fixed branch. The bot does not approve or merge
its pull request.

Pin every action to a full commit SHA. After all existing workflows are pinned,
enable the repository setting that requires full action SHA pinning.
