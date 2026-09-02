# Custom client protocol guide

`longshot-protocol` provides transport-neutral request, response, WebSocket,
binary-wire, and signing helpers. It does not choose an API origin, open HTTP or
WebSocket connections, persist bearer tokens, or implement retries. A custom
client owns those transport concerns and uses this package at every serialization
and signing boundary described below.

Production uses `https://api.longshot.xyz` for HTTP and
`wss://api.longshot.xyz/ws` for the market-maker WebSocket. Other deployments
can use different origins, authentication domains, and chain IDs.

Use the helpers instead of reconstructing messages or binary layouts. The server
rebuilds the same payloads and rejects signatures over different bytes, field
values, domains, or encodings.

## Signing and encoding matrix

| Workflow | Payload signed with EIP-191 | TypeScript helper | Python helper | Wire encoding |
| --- | --- | --- | --- | --- |
| Direct-wallet login | UTF-8 text from the wallet-auth message builder | `buildWalletAuthenticationMessage` | `build_wallet_authentication_message` | Padded standard Base64 of the 65-byte signature |
| Signed RFQ | Binary signed-order bytes, including `use_app_tokens` | `signOrder` | `sign_order` | Padded standard Base64 inside `SignedOrderJson.signature` |
| MM WebSocket authentication | UTF-8 text containing the server challenge | `authResponseMessage` | `auth_response_message` | 130 hexadecimal characters without a `0x` prefix |
| MM quote | Binary `QuoteResponse.signedDataBytes()` / `signed_data_bytes()` | `signedQuoteResponse` | `signed_quote_response` | The complete fixed-size quote record in unpadded standard Base64 |
| Direct-wallet withdrawal | UTF-8 text from the withdrawal message builder | `buildWalletWithdrawalAuthorizationMessage` | `build_wallet_withdrawal_authorization_message` | Padded standard Base64 of the 65-byte signature |

The Rust equivalents live in `longshot_protocol::api::request`,
`longshot_protocol::taker`, and `longshot_protocol::mm`.

## Configuration and time inputs

- Obtain the direct-wallet authentication domain from the target deployment.
  The server reads `WALLET_AUTH_DOMAIN` and currently defaults it to
  `longshot.xyz`. No public response currently exposes this value, so provide it
  through client configuration; do not infer it from the API URL or substitute
  the MM domain constant.
- MM WebSocket authentication always uses the exported `AUTH_DOMAIN`, currently
  `longshot.xyz`. The helper inserts it into the signed message.
- Use the deployment's settlement chain ID for withdrawals. The authenticated
  `GET /v1/users/deposit-wallet` response exposes it as `chain_id`; a custodial
  session may also expose it as `deposit_chain_id`. Do not use the wallet
  application's currently selected network as an implicit replacement.
- Wallet login and withdrawal messages use a fresh client Unix timestamp in
  milliseconds. The current server default accepts messages up to 60 seconds old,
  permits at most 30 seconds of future clock skew, and can configure the age
  window only within `1..=120` seconds.
- MM authentication must sign the `challenge_id` and `timestamp_ms` sent by the
  server. The connection authentication timeout is 10 seconds, so respond
  immediately rather than generating a new timestamp.
- A signed RFQ must arrive before `expires_at_ms`, and the server rejects a first
  submission whose deadline is more than 15 minutes in the future. Generate the
  deadline near submission time rather than treating it as a long-lived order.

The sections below state the current server constraints that affect external
wallet, RFQ, and withdrawal clients. Treat an API error as authoritative if a
deployment uses a stricter policy.

## Direct-wallet login

1. Obtain the deployment's wallet-auth domain.
2. Set `signed_at_ms` to the current Unix time in milliseconds.
3. Build the exact message with `buildWalletAuthenticationMessage()` or
   `build_wallet_authentication_message()` using the signing EOA.
4. Sign that UTF-8 message with EIP-191 personal signing.
5. Encode the 65-byte `r || s || v` signature with
   `encodeWalletSignature()` or `encode_wallet_signature()`.
6. Send `WalletAuthRequest` to `POST /v1/auth/wallet`:

   ```json
   {
     "address": "0x...",
     "signature": "<padded-standard-base64>",
     "signed_at_ms": 1785529737000,
     "referral_code": null
   }
   ```

Use the returned `session_token` as a bearer token. For identity and later
signing, use `auth_wallet_address`; `address` and `deposit_address` may refer to a
Longshot-controlled custodial wallet instead.

Never submit the message text, a hex signature, URL-safe Base64, or unpadded
Base64 to this endpoint. The request contains only the address, encoded
signature, timestamp, and an optional referral code.

## Signed RFQ submission

1. Construct `SignedOrder` with the authenticated EOA, a unique `nonce`, a near
   deadline in `expires_at_ms`, and one to nine legs.
2. Supply odds to the binary type as integer basis points:
   `minOddsBps = 25_000` / `min_odds_bps = 25_000` means decimal odds `2.5x`.
   The HTTP DTO uses `min_odds: 2.5`. The server multiplies HTTP odds by
   10,000 and rounds to the nearest integer; the result must be from 10,001
   through the protocol `Odds.MAX` value, inclusive.
3. Choose `use_app_tokens` before signing. Pass that exact Boolean to
   `signOrder()` / `sign_order()` and later to
   `createRfqRequestFromSignedOrder()` /
   `CreateRfqRequest.from_signed_order()`.
4. Optionally verify the completed order locally with `verifySignature()` /
   `verify_signature()` using the same funding choice.
5. Convert the signed binary order to `CreateRfqRequest` and send it to
   `POST /v1/rfq` with the bearer token.

`use_app_tokens`, `order_type`, `shield_on`, and every order field are part of
the signed payload. Changing any of them after signing invalidates the
signature. The signature covers the deterministic binary layout, not the JSON
request body. The conversion helper performs the `min_odds_bps / 10_000`
conversion and emits the padded Base64 signature.

`community_pick` is not part of the signed-order bytes, so `POST /v1/rfq`
does not accept it. Tail and Fade clients must send `CreateUnsignedRfqRequest`
through `POST /v1/rfq/unsigned`. The community attribution is an optional
nested field, not the top-level request:

```json
{
  "privy_token": "<fresh-privy-identity-token>",
  "use_app_tokens": false,
  "rfq_params": {
    "wager_micros": 1000000,
    "min_odds": 2.5,
    "legs": [{"market_id": 42, "direction": "up"}],
    "order_type": 2,
    "shield_on": false,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
  },
  "community_pick": {
    "source_position_id": "550e8400-e29b-41d4-a716-446655440001",
    "mode": "tail"
  }
}
```

The server additionally checks freshness, replay identity, signer/session
identity, wager and odds bounds, account status, balance, market state, trading
windows, and settlement availability. Local signature verification does not
predict acceptance by those server-owned policies.

## Market-maker WebSocket

Use the typed `ClientMessage` and `ServerMessage` shapes around the following
state machine:

1. Connect to the deployment's MM WebSocket endpoint and send
   `ClientMessage.auth()` / `ClientMessage.auth().to_dict()`.
2. On `auth_challenge`, pass its canonical lowercase UUIDv4 `challenge_id` and
   server-supplied `timestamp_ms` to `authResponseMessage()` /
   `auth_response_message()`. Send the resulting `auth_response` JSON.
3. Wait for a successful `auth_result`. Its `session_token` is the bearer token
   minted for MM-authorized API routes.
4. Send a `subscribe` message with the exported `RFQ_PROTOCOL_VERSION` and the
   desired `RfqSubscription` values. Do not hardcode a protocol version.
5. On `rfq`, decode the unpadded Base64 `data` field with
   `decodeBroadcastRfq()` / `decode_broadcast_rfq()`.
6. Build a quote with the received request ID, integer protocol odds, and maximum
   fill amount. Use `signedQuoteResponse()` / `signed_quote_response()`, then
   `quoteResponseMessage()` / `quote_response_message()`, and send the resulting
   `quote` JSON.
7. Treat `quote_ack.accepted` as receipt and public collector validation, not as
   a fill. The terminal outcome arrives in `quote_result`.
8. Reply to every `ping` with `ClientMessage.pong()` /
   `ClientMessage.pong().to_dict()`.

MM authentication signs exact text and sends a hex signature. MM quotes sign the
fixed binary quote prefix and send the entire fixed-size signed quote as
unpadded Base64. These encodings are intentionally different.

## Profit-cap discovery

Call public `GET /v1/mm/profit_caps` before quoting and refresh it while the
maker is running. `default_max_profit_micros` applies when `overrides` has no
entry for a market's open `market_type` slug; each override replaces that
default for its category. Values are taker net profit (and therefore maker
liability) per RFQ in protocol micro-units.

For an RFQ spanning categories, enforce the lowest applicable cap. The live
engine remains authoritative and can reject a quote whose profit exceeds its
current policy, so clients must still handle `ProfitExceedsMaximum` after
locally clamping `max_fill`.

## Direct-wallet withdrawal

1. Reuse the authenticated session's `auth_wallet_address` as the signing EOA.
2. Call authenticated `GET /v1/user/available_balance`; choose exact
   `amount_micros` in the inclusive range
   `deposit_withdrawal_min_micros <= amount_micros <= available_micros`, a
   destination address, and a canonical UUID `idempotency_key`. Do not use the
   schema example as the minimum. An omitted destination is the signing EOA;
   include it in the signed message.
3. Obtain the same wallet-auth domain and settlement chain ID used by the server.
4. Set a fresh `signed_at_ms` and build the exact message with
   `buildWalletWithdrawalAuthorizationMessage()` or
   `build_wallet_withdrawal_authorization_message()`.
5. Sign the UTF-8 message with EIP-191, then use
   `encodeWalletSignature()` / `encode_wallet_signature()`.
6. Send `UserWithdrawRequest` to `POST /v1/users/withdraw`:

   ```json
   {
     "withdraw_params": {
       "amount_micros": 1000000,
       "destination_address": "0x...",
       "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
     },
     "authorization": {
       "type": "wallet_signature",
       "signature": "<padded-standard-base64>",
       "signed_at_ms": 1785529737000
     }
   }
   ```

The domain, chain ID, addresses, amount, idempotency key, and timestamp are all
signed. Do not modify the request after signing. A withdrawal signature is
operation-specific and cannot be replaced with the wallet-login signature.

## Lossless JSON boundary

TypeScript custom clients must use `stringifySerde()` for request bodies and
pass untouched response text to `decodeApiJson()` with the expected schema name.
Native `JSON.stringify()` throws on `bigint`, and native `JSON.parse()` can round
bare Rust `i64`/`u64` values before validation sees them.

Python integers and Rust integers preserve the API's full integer range. Python
clients should still use each DTO's `to_dict()` and `from_dict()` boundary so
tagged unions, enums, optional fields, and validation follow the Rust contract.
