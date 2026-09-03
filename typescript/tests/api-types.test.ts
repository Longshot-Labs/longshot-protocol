import assert from "node:assert/strict";
import test from "node:test";

import {
  Address,
  ActivePositionStatus,
  MarketType,
  PositionId,
  PositionRole,
} from "../src/index.js";
import type {
  ActivePosition,
  CheckHandleQuery,
  CreateRfqRequest,
  ProfitCapConfigResponse,
  RecentResolutionEntry,
  SignedOrderInput,
  UserWithdrawParams,
  UserWithdrawRequest,
  WalletAuthRequest,
} from "../src/index.js";

const activePosition: ActivePosition = {
  position_id: new PositionId("550e8400-e29b-41d4-a716-446655440000"),
  status: ActivePositionStatus.Open,
  role: PositionRole.Maker,
  taker_address: Address.fromHex("0x1111111111111111111111111111111111111111"),
  wager_micros: "1000000",
  app_token_wager_micros: "0",
  payout_micros: "1500000",
  legs: [],
};

const signedOrderInput: SignedOrderInput = {
  user: Address.ZERO,
  wagerMicros: 1_000_000,
  minOddsBps: 25_000,
  legs: [],
  nonce: 1,
  expiresAtMs: 1_735_430_300_000,
  orderType: 2,
};

// @ts-expect-error signed orders do not accept ambiguous decimal-looking odds.
const legacyCamelOdds: SignedOrderInput = { ...signedOrderInput, minOdds: 2 };

const walletAuthRequest: WalletAuthRequest = {
  address: "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
  signature: "signature",
  signed_at_ms: 1_735_430_000_000,
};

// @ts-expect-error signature is required.
const missingWalletSignature: WalletAuthRequest = {
  address: "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
  signed_at_ms: 1_735_430_000_000,
};

const checkHandleQuery: CheckHandleQuery = { handle: "user" };

// @ts-expect-error handle is required.
const missingHandleQuery: CheckHandleQuery = {};

const withdrawParams: UserWithdrawParams = {
  amount_micros: 1_000_000,
  idempotency_key: "550e8400-e29b-41d4-a716-446655440001",
};

const withdrawRequest: UserWithdrawRequest = {
  withdraw_params: withdrawParams,
  authorization: {
    type: "wallet_signature",
    signature: "base64-signature",
    signed_at_ms: 1_785_529_737_000,
  },
};

const signedRfqRequest: CreateRfqRequest = {
  use_app_tokens: true,
  order: {
    user: "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    wager_micros: 1_000_000,
    min_odds: 2.5,
    legs: [{ market_id: 42, direction: "up" }],
    nonce: 123,
    expires_at_ms: 1_735_430_300_000,
    shield_on: false,
    signature: "signature",
  },
};

const recentResolution: RecentResolutionEntry = {
  market_id: 42,
  outcome: "YES",
  window_start_ms: 1_735_689_600_000,
  resolved_at_ms: 1_735_689_901_000,
};

const profitCaps: ProfitCapConfigResponse = {
  default_max_profit_micros: 75_000_000,
  overrides: [{ market_type: "sports", max_profit_micros: 500_000_000 }],
};

test("public request and response DTOs compile", () => {
  assert.equal(activePosition.role, "maker");
  assert.ok(signedOrderInput);
  assert.ok(legacyCamelOdds);
  assert.ok(walletAuthRequest);
  assert.ok(missingWalletSignature);
  assert.ok(checkHandleQuery);
  assert.ok(missingHandleQuery);
  assert.ok(withdrawRequest);
  assert.ok(signedRfqRequest);
  assert.equal(recentResolution.market_id, 42);
  assert.equal(profitCaps.overrides[0]?.market_type, "sports");
});

test("market type remains an open category slug", () => {
  const forwardCompatibleCategory: MarketType = "new-category";
  assert.equal(forwardCompatibleCategory, "new-category");
});
