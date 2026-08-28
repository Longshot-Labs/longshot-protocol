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
