# Longshot Protocol for Python

Python DTOs and deterministic Longshot protocol helpers.

The package exposes API and WebSocket contracts, fixed binary RFQ layouts,
EVM address handling, and canonical order, authentication, and quote signing.
It intentionally contains no HTTP, SSE, or WebSocket transport client.

The installed `longshot_protocol` package includes `CUSTOM_CLIENTS.md` with the
production origins, HTTP request shapes, WebSocket flow, and signing boundaries.

```bash
python -m pip install longshot-protocol==0.2.0
```

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
