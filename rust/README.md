# Longshot Protocol for Rust

Transport-neutral Longshot contracts and deterministic wire helpers.

The crate exposes API and WebSocket contracts, fixed binary RFQ layouts, EVM
address handling, and canonical order, authentication, and quote signing. It
does not contain an HTTP, SSE, or WebSocket transport client.

```toml
[dependencies]
longshot-protocol = "0.2"
```

```rust
use longshot_protocol::types::{Amount, Odds, RequestId};
```

See the custom client guide at
<https://github.com/Longshot-Labs/longshot-protocol/blob/main/CUSTOM_CLIENTS.md>
for the production origins, HTTP request shapes, WebSocket flow, and signing
boundaries. The same file ships inside the crate archive as `CUSTOM_CLIENTS.md`.
