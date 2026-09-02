# Longshot Protocol

Transport-neutral Longshot contracts and deterministic wire helpers for Rust,
TypeScript, and Python. This directory is the source of truth for the language
packages.

Public package archives contain the runtime source, package README, custom client
guide, and license. Fixtures, examples, tests, and generators are excluded.

The checked-in Rust and TypeScript manifests block direct publication from the
monorepo. Use the release scripts with `--check` to build and inspect the
registry archives without publishing them:

- `bash scripts/publish-rust.sh --check`
- `bash scripts/publish-typescript.sh --check`
- `bash scripts/publish-python.sh --check`

Release automation must pass the protected downstream gate before it uses the
same scripts with `--publish`. TypeScript and Python publish the exact audited
archives. Cargo rebuilds the Rust upload from the same isolated audited source.

The initial implementation was imported from
`Longshot-Labs/longshot-sdk@a3f049b20ad7c83bd60aa69b366f4016495900ff`.
Public API DTOs are synchronized with the public-pruned
`fixtures/api/openapi.json`; the TypeScript serde generator rejects missing or
drifted supported schemas and route-bound query DTOs that OpenAPI cannot name.
Shared fixtures under
`fixtures/protocol` continue to preserve binary and signing compatibility with
the production-pinned SDK revision.

Only supported external taker and market-maker contracts ship. Server and
first-party contracts remain private. Tail and Fade attribution, signed taker
orders, broadcast RFQs, quotes, and market-maker authentication remain public.

Network clients are intentionally out of scope.

See the [custom client protocol guide](CUSTOM_CLIENTS.md) for the supported JSON,
signing, and binary-wire boundaries. Its TypeScript and Python examples are
executed by the package test suites.
