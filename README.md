# Longshot Protocol

Types, serializers, and signing helpers for the [Longshot](https://longshot.xyz)
API, published for Rust, TypeScript, and Python. The packages cover the
public HTTP contracts, the market maker WebSocket messages, the fixed binary
RFQ and quote layouts, and the EIP-191 signing rules for wallet sign in,
signed orders, quotes, and withdrawal authorizations. They contain no HTTP or
WebSocket client; bring your own.

| Language | Package | Install |
| --- | --- | --- |
| Rust | [`rust/`](rust) | `longshot-protocol = "0.2"` |
| TypeScript | [`typescript/`](typescript) | `npm install longshot-protocol@0.2.0` |
| Python | [`python/`](python) | `pip install longshot-protocol==0.2.0` |

## Documentation

- [API documentation](https://docs.longshot.xyz/api-reference): quickstart,
  guides, and the full route reference.
- [CUSTOM_CLIENTS.md](CUSTOM_CLIENTS.md): production origins, request shapes,
  signing and encoding rules, and the market maker WebSocket flow. The same
  file ships inside each package.
- [Market maker quickstart](https://docs.longshot.xyz/protocol/market-maker-quickstart).
  Market maker accounts are allowlisted by Longshot.

## Repository layout

- `rust/`, `typescript/`, `python/`: the three packages, each with its own
  README and tests.
- `fixtures/api/openapi.json`: the public OpenAPI document the packages are
  generated against.
- `fixtures/protocol/parity.json`: cross language signing and binary layout
  test vectors.

This repository is a generated export of the protocol sources in the Longshot
monorepo. Pull requests are not accepted here; report problems through
[ops@longshot.xyz](mailto:ops@longshot.xyz).

## License

See [LICENSE.txt](rust/LICENSE.txt).
