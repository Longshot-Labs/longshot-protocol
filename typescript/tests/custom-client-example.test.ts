import assert from "node:assert/strict";
import test from "node:test";
import { privateKeyToAccount } from "viem/accounts";

import {
  Direction,
  OrderType,
  decodeApiJson,
  type CreateRfqRequest,
  type UserWithdrawRequest,
  type WalletAuthRequest,
} from "../src/index.js";
import {
  buildMmAuthResponse,
  buildMmQuoteMessage,
  buildSignedRfqBody,
  buildWalletAuthBody,
  buildWalletWithdrawalBody,
  decodeRecentResolution,
} from "../examples/custom-client.js";

const SIGNING_KEY = `0x${"01".repeat(32)}` as const;
const ADDRESS = privateKeyToAccount(SIGNING_KEY).address;
const UUID = "550e8400-e29b-41d4-a716-446655440000";

test("custom-client example preserves wide response integers", () => {
  const resolution = decodeRecentResolution(
    '{"market_id":9007199254740993,"outcome":"up","window_start_ms":1,"resolved_at_ms":2}',
  );

  assert.equal(resolution.market_id, 9_007_199_254_740_993n);
});

test("custom-client example builds a valid signed RFQ wire body", async () => {
  const body = await buildSignedRfqBody({
    signingKey: SIGNING_KEY,
    marketId: 9_007_199_254_740_993n,
    direction: Direction.Up,
    wagerMicros: 1_000_000,
    minOddsBps: 25_000,
    nonce: 7,
    expiresAtMs: 1_735_430_300_000,
    orderType: OrderType.FOK,
    shieldOn: false,
    useAppTokens: true,
  });
  const request = decodeApiJson<CreateRfqRequest>(body, "CreateRfqRequest");

  assert.equal(request.use_app_tokens, true);
  assert.equal(request.order.user, ADDRESS);
  assert.equal(request.order.min_odds, 2.5);
  assert.equal(request.order.legs[0]?.market_id, 9_007_199_254_740_993n);
  assert.match(request.order.signature, /^[A-Za-z0-9+/]{87}=$/u);
});

test("custom-client example builds wallet auth and withdrawal wire bodies", async () => {
  const authBody = await buildWalletAuthBody({
    signingKey: SIGNING_KEY,
    domain: "preview.longshot.xyz",
    signedAtMs: 1_785_529_737_000,
  });
  const auth = decodeApiJson<WalletAuthRequest>(authBody, "WalletAuthRequest");

  assert.equal(auth.address, ADDRESS);
  assert.match(auth.signature, /^[A-Za-z0-9+/]{87}=$/u);

  const withdrawalBody = await buildWalletWithdrawalBody({
    signingKey: SIGNING_KEY,
    domain: "preview.longshot.xyz",
    chainId: 84_532,
    destinationAddress: ADDRESS,
    amountMicros: 1_000_000,
    idempotencyKey: UUID,
    signedAtMs: 1_785_529_737_000,
  });
  const withdrawal = decodeApiJson<UserWithdrawRequest>(
    withdrawalBody,
    "UserWithdrawRequest",
  );

  assert.equal(withdrawal.withdraw_params.idempotency_key, UUID);
  assert.equal(withdrawal.authorization.type, "wallet_signature");
  assert.match(withdrawal.authorization.signature, /^[A-Za-z0-9+/]{87}=$/u);
});

test("custom-client example builds MM authentication and quote messages", async () => {
  const auth = await buildMmAuthResponse(UUID, 1_735_430_000_000, SIGNING_KEY);
  const quote = await buildMmQuoteMessage({
    signingKey: SIGNING_KEY,
    requestId: UUID,
    oddsBps: 25_000,
    maxFillMicros: 1_000_000,
  });

  assert.equal(auth.type, "auth_response");
  assert.equal(auth.wallet_address, ADDRESS);
  assert.match(auth.signature, /^[0-9a-f]{130}$/u);
  assert.equal(quote.type, "quote");
  assert.match(quote.data, /^[A-Za-z0-9+/]+$/u);
  assert.doesNotMatch(quote.data, /=/u);
});
