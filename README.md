# Longshot Protocol

Private, transport-neutral Longshot contracts and deterministic wire helpers
for Rust, TypeScript, and Python.

This repository is a standalone snapshot of
[`Longshot-Labs/longshot`](https://github.com/Longshot-Labs/longshot) commit
`6353e7e2423aedc4c36f34eb76ac3c787a3c856d`. The `longshot` monorepo is the
source of truth, and compatibility updates flow one way from its
`longshot-protocol/` directory into this repository.

The initial protocol implementation was imported from
`Longshot-Labs/longshot-sdk@a3f049b20ad7c83bd60aa69b366f4016495900ff`.
Public API DTOs are synchronized with the pinned
`fixtures/api/openapi.json`. Shared fixtures under `fixtures/protocol` preserve
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

## Clone and use

The packages are proprietary and are not published to public package
registries. Clone this private repository and use the language package
directly:

```sh
git clone https://github.com/Longshot-Labs/longshot-protocol.git

cargo add longshot-protocol --path ./longshot-protocol/rust
python -m pip install ./longshot-protocol/python
npm install ./longshot-protocol/typescript
```

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
