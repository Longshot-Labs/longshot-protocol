# Longshot Protocol for Python

Standalone Python DTOs and deterministic Longshot protocol helpers.

The package exposes API and WebSocket contracts, fixed binary RFQ layouts,
EVM address handling, and canonical order, authentication, and quote signing.
It intentionally contains no HTTP, SSE, or WebSocket transport client.

The shared [custom client protocol guide](../CUSTOM_CLIENTS.md) documents wallet
authentication, signed RFQs, MM WebSocket messages, withdrawals, configuration,
and server-owned validation. The runnable example is
[`examples/custom_client.py`](examples/custom_client.py).

```python
from longshot_protocol import Amount, Odds, RequestId, signed_quote_response
```

## Signed-order odds units

`SignedOrder.min_odds_bps` is the integer value committed to the binary signature:
`25_000` means `2.5x`. The HTTP DTO intentionally uses decimal odds instead, so
`SignedOrderJson.min_odds` carries `2.5` for the same order.

```python
from longshot_protocol import (
    Address,
    CreateRfqRequest,
    MarketId,
    OrderLeg,
    OrderType,
    SignedOrder,
)

signed_order = SignedOrder(
    user=Address.ZERO,
    wager_micros=1_000_000,
    min_odds_bps=25_000,
    legs=[OrderLeg(market_id=MarketId(42), direction=0)],
    nonce=1,
    expires_at_ms=1_735_430_300_000,
    order_type=OrderType.FOK,
    shield_on=False,
)
request = CreateRfqRequest.from_signed_order(signed_order, use_app_tokens=False)
assert request.to_dict()["order"]["min_odds"] == 2.5
```

Valid HTTP odds are greater than `1.0x` and no greater than the protocol maximum.
When a DTO is converted into a signed order, its decimal odds are multiplied by
10,000 and `.5` ties round upward—Rust's half-away-from-zero rule on the valid
domain. For example, `2.00005` becomes `20_001` basis points.

Run the cross-language compatibility tests from this directory:

```bash
python -m pip install -e ".[test]"
python -m unittest discover -s tests
```

When the Rust API contracts change, regenerate the runtime serde metadata and
the static constructor signatures before running the tests:

```bash
python tools/generate_serde_metadata.py
python tools/generate_api_stub.py
```
