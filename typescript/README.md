# Longshot Protocol for TypeScript

Standalone TypeScript contracts and deterministic Longshot protocol helpers.
The package contains no HTTP, SSE, or WebSocket transport client.

The shared [custom client protocol guide](../CUSTOM_CLIENTS.md) documents wallet
authentication, signed RFQs, MM WebSocket messages, withdrawals, configuration,
and server-owned validation. The runnable example is
[`examples/custom-client.ts`](examples/custom-client.ts).

## Lossless API JSON

Use `stringifySerde()` for request bodies and pass the original response text to
`decodeApiJson()` with its exported contract name. This is the supported JSON
boundary for custom HTTP clients:

```ts
import {
  decodeApiJson,
  stringifySerde,
} from "longshot-protocol";

async function postApi<T>(
  url: string,
  request: unknown,
  responseSchema: string,
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: stringifySerde(request),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return decodeApiJson<T>(await response.text(), responseSchema);
}
```

JavaScript numbers cannot exactly represent every Rust `i64` or `u64` value.
`decodeApiJson()` validates the selected schema and returns bare integers outside
JavaScript's safe range as `bigint`; it must receive the raw text because
`JSON.parse()` may already have rounded those values. `stringifySerde()` emits
`bigint` values as exact bare JSON integers, whereas `JSON.stringify()` throws
when it encounters a `bigint`.

## Signed-order odds units

`SignedOrder.minOddsBps` is the integer value committed to the binary signature:
`25_000` means `2.5x`. The HTTP DTO intentionally uses decimal odds instead, so
`SignedOrderJson.min_odds` carries `2.5` for the same order.

```ts
import {
  Address,
  Direction,
  MarketId,
  OrderLeg,
  OrderType,
  SignedOrder,
  createRfqRequestFromSignedOrder,
} from "longshot-protocol";

const signedOrder = new SignedOrder({
  user: Address.ZERO,
  wagerMicros: 1_000_000,
  minOddsBps: 25_000,
  legs: [new OrderLeg({ marketId: MarketId.new(42), direction: Direction.Up })],
  nonce: 1,
  expiresAtMs: 1_735_430_300_000,
  orderType: OrderType.FOK,
  shieldOn: false,
});
const request = createRfqRequestFromSignedOrder(signedOrder, false);
console.assert(request.order.min_odds === 2.5);
```

Valid HTTP odds are greater than `1.0x` and no greater than the protocol maximum.
When a DTO is converted into a signed order, its decimal odds are multiplied by
10,000 and `.5` ties round upward—Rust's half-away-from-zero rule on the valid
domain. For example, `2.00005` becomes `20_001` basis points.

Run the package tests from this directory:

```bash
npm install
npm test
```
