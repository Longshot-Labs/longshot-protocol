# Longshot Protocol

Private source mirror for the transport-neutral Longshot contracts and
deterministic wire helpers for Rust, TypeScript, and Python.

This repository includes protocol changes from
[`Longshot-Labs/longshot#1595`](https://github.com/Longshot-Labs/longshot/pull/1595)
at `31476976682a7603133c75898734425fe21cd3c8` and
[`Longshot-Labs/longshot#1577`](https://github.com/Longshot-Labs/longshot/pull/1577)
at `fe87ac255d233881e29017b0f1470bbd27434eba`. The `longshot` monorepo is the
source of truth. Compatibility updates flow one way from its
`longshot-protocol/` directory into this repository, with the registry-package
exclusions documented below.

The initial protocol implementation was imported from
`Longshot-Labs/longshot-sdk@a3f049b20ad7c83bd60aa69b366f4016495900ff`.
Supported external API DTOs are synchronized with the pinned
`fixtures/api/openapi.json`. The full fixture remains private release input;
first-party presentation routes and fields, including community browsing,
Recent Winners, NFL hub curation, and featured market placement, are excluded
from registry packages. Shared fixtures under `fixtures/protocol` preserve
binary and signing compatibility with the production-pinned SDK revision.

Network clients are intentionally out of scope. The private SDK remains the
transport owner until the follow-up Vault client migration lands.

See the [custom client protocol guide](CUSTOM_CLIENTS.md) for the supported
JSON, signing, and binary-wire boundaries. Its TypeScript and Python examples
are executed by the package test suites.

## Layout

- `rust/` contains the `longshot-protocol` crate.
- `typescript/` contains the `longshot-protocol` package.
- `python/` contains the `longshot-protocol` distribution, imported as
  `longshot_protocol`.
- `fixtures/` contains the pinned OpenAPI contract and cross-language protocol
  parity vectors.

## Install

Version 0.2.0 is distributed through public package registries under the
included proprietary license:

```sh
cargo add longshot-protocol@0.2.0
python -m pip install longshot-protocol==0.2.0
npm install longshot-protocol@0.2.0
```

Public package archives exclude repository-only guides, fixtures, examples,
tests, and generators.

The checked-in Rust manifest blocks direct publication because Cargo can add
private repository metadata. Run `bash scripts/publish-rust.sh --check` to test
the Git-free release path. Release operators use the same script with
`--publish` only after review and approval.

## Validation

Run from the repository root:

```sh
cargo fmt --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-targets --all-features --locked

python python/tools/generate_serde_metadata.py --check
python python/tools/generate_api_stub.py --check
python -m pip install -e "python[test]"
python -m unittest discover -s python/tests

npm --prefix typescript ci
npm --prefix typescript test
git diff --exit-code -- typescript/src/serde.generated.ts
```
