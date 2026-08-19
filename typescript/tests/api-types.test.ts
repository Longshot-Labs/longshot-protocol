import assert from "node:assert/strict";
import test from "node:test";

import {
  Address,
  ActivePositionStatus,
  FantasyResultGameType,
  MarketType,
  PositionId,
  PositionRole,
} from "../src/index.js";
import type {
  ActivePosition,
  ChatEmojiDisplayResponse,
  ChatUserAvatarResponse,
  CheckHandleQuery,
  ContestBetTypeResponse,
  CreateRfqRequest,
  CreateSessionRequest,
  CreateUnsignedRfqRequest,
  NotificationPayload,
  PublicContestSummaryResponse,
  PortfolioFantasyEntryResponse,
  PlaceContestBetRequest,
  PublicProfileFantasyEntryResponse,
  RecentResolutionEntry,
  ShareImageRef,
  SignedOrderInput,
  UserWithdrawParams,
  SurvivorContestResponse,
  SurvivorEntryStateResponse,
  SurvivorRoundBreakdownResponse,
  SurvivorRoundPicksResponse,
  UserWithdrawRequest,
  VaultWithdrawalAmountRequest,
  WalletAuthRequest,
  WideInteger,
} from "../src/index.js";

const makerActivePosition: ActivePosition = {
  position_id: new PositionId("550e8400-e29b-41d4-a716-446655440000"),
  status: ActivePositionStatus.Open,
  role: PositionRole.Maker,
  taker_address: Address.fromHex("0x1111111111111111111111111111111111111111"),
  wager_micros: "1000000",
  app_token_wager_micros: "0",
  payout_micros: "1500000",
  legs: [],
};

const outcastFantasyResult: NotificationPayload = {
  type: "fantasy_result",
  contest_id: "contest-outcast",
  game_index: 2,
  game_type: FantasyResultGameType.Outcast,
  contest_title: "Stay With The Pack",
  contest_terminal: true,
  contest_refunded: true,
  entry_count: 3,
  successful_entry_count: 2,
  held_entry_count: 1,
  credited_payout_micros: 7_500_000,
  held_payout_micros: 2_500_000,
  best_entry: {
    entry_index: 1,
    rank: 3,
    correct_count: 5,
    selection_count: 6,
  },
  tiebreaker_result: 42,
};

const chatMention: NotificationPayload = {
  type: "chat_mention",
  chat_id: "55555555-5555-4555-8555-555555555555",
  chat_context: "contest",
  contest_id: "55555555-5555-4555-8555-555555555555",
  message_id: "66666666-6666-4666-8666-666666666666",
};

const marketChatMention: NotificationPayload = {
  type: "chat_mention",
  chat_id: "9187ca06-569d-5bc7-8aa1-cb4dd2da71ac",
  chat_context: "crypto_market",
  message_id: "77777777-7777-4777-8777-777777777777",
};

function fantasyCreditedPayout(payload: NotificationPayload): WideInteger | undefined {
  if (payload.type !== "fantasy_result") return undefined;
  return payload.credited_payout_micros;
}

function chatMentionMessageId(payload: NotificationPayload): string | undefined {
  if (payload.type !== "chat_mention") return undefined;
  return payload.message_id;
}

const sessionRequest: CreateSessionRequest = {
  privy_token: "privy-token",
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

// @ts-expect-error internal signed orders no longer accept ambiguous decimal-looking minOdds.
const legacyCamelOdds: SignedOrderInput = { ...signedOrderInput, minOdds: 2 };

// @ts-expect-error internal signed orders no longer accept the HTTP min_odds field.
const legacyWireOdds: SignedOrderInput = { ...signedOrderInput, min_odds: 2 };

// @ts-expect-error privy_token is required.
const missingSessionToken: CreateSessionRequest = {};

// @ts-expect-error privy_token is not nullable in the Rust request type.
const nullSessionToken: CreateSessionRequest = { privy_token: null };

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

const checkHandleQuery: CheckHandleQuery = {
  handle: "user",
};

// @ts-expect-error handle is required.
const missingHandleQuery: CheckHandleQuery = {};

const fullVaultWithdrawal: VaultWithdrawalAmountRequest = {
  type: "full",
  vault_id: "550e8400-e29b-41d4-a716-446655440000",
};

const partialVaultWithdrawal: VaultWithdrawalAmountRequest = {
  type: "partial",
  vault_id: "550e8400-e29b-41d4-a716-446655440000",
  amount_micros: 1000000,
};

// @ts-expect-error full withdrawal requests require vault_id.
const missingFullVaultId: VaultWithdrawalAmountRequest = { type: "full" };

// @ts-expect-error partial withdrawal requests require amount_micros.
const missingPartialAmount: VaultWithdrawalAmountRequest = {
  type: "partial",
  vault_id: "550e8400-e29b-41d4-a716-446655440000",
};

const avatarUrl: ChatUserAvatarResponse = {
  type: "x_avatar_url",
  url: "https://example.com/avatar.png",
};

const avatarSeed: ChatUserAvatarResponse = {
  type: "seed",
  seed: 7,
};

// @ts-expect-error x_avatar_url avatar responses require url.
const missingAvatarUrl: ChatUserAvatarResponse = { type: "x_avatar_url" };

// @ts-expect-error seed avatar responses require seed.
const missingAvatarSeed: ChatUserAvatarResponse = { type: "seed" };

const emojiUrl: ChatEmojiDisplayResponse = {
  type: "url",
  value: "https://example.com/emoji.png",
};

const emojiUnicode: ChatEmojiDisplayResponse = {
  type: "unicode",
  value: ":fire:",
};

// @ts-expect-error emoji display responses require value.
const missingEmojiValue: ChatEmojiDisplayResponse = { type: "url" };

const contestNumBets: ContestBetTypeResponse = {
  type: "num_bets",
  value: 3,
};

const contestBetsPerCategory: ContestBetTypeResponse = {
  type: "bets_per_category",
  value: 2,
};

const legacyContestBetRequest: PlaceContestBetRequest = {
  contest_id: "550e8400-e29b-41d4-a716-446655440000",
  use_app_tokens: false,
  bets: [{ market_id: 42, direction: "up" }],
};

const multiEntrySurvivorContestBetRequest: PlaceContestBetRequest = {
  ...legacyContestBetRequest,
  entry_index: 1,
};

const survivorRoundBreakdown: SurvivorRoundBreakdownResponse = {
  eligible_entry_count: 10,
  submitted_entry_count: 8,
  missed_entry_count: 2,
  markets: [{ market_id: 42, up_count: 5, down_count: 3 }],
};

const survivorContest: SurvivorContestResponse = {
  version: 1,
  round_count: 10,
  phase: "pick_open",
  current_game_index: 0,
  rounds: [{
    game_index: 0,
    status: "pick_open",
    required_pick_count: 3,
    betting_opens_at_ms: 1,
    betting_closes_at_ms: 2,
    resolved_at_ms: null,
    markets: [],
    breakdown: survivorRoundBreakdown,
  }],
  revealed_game_indexes: [],
  remaining_survivor_count: 10,
};

const survivorOrdinarySuccessorGap: SurvivorContestResponse = {
  ...survivorContest,
  phase: "awaiting_next_round",
  current_game_index: 0,
  next_game_index: 1,
  rounds: [{ ...survivorContest.rounds[0], status: "settled" }],
};

const survivorEmptyReplacementGap: SurvivorContestResponse = {
  ...survivorContest,
  phase: "awaiting_next_round",
  current_game_index: 0,
  next_game_index: 0,
  rounds: [],
};

const survivorReplacementGapWithScheduledSuccessor: SurvivorContestResponse = {
  ...survivorEmptyReplacementGap,
  rounds: [{
    ...survivorContest.rounds[0],
    game_index: 1,
    status: "scheduled",
    breakdown: null,
  }],
};

const survivorReplacementSummary: Pick<
  PublicContestSummaryResponse,
  "survivor_awaiting_replacement" | "survivor_current_game_index"
> = {
  survivor_awaiting_replacement: true,
  survivor_current_game_index: 0,
};

const survivorEntry: SurvivorEntryStateResponse = {
  status: "alive",
  eligible_for_current_game: true,
  rounds: [],
};

const survivorPortfolioMetadata: Pick<
  PortfolioFantasyEntryResponse,
  'game_type' | 'survivor_round_count' | 'current_game_index'
> = {
  game_type: 'survivor',
  survivor_round_count: 10,
  current_game_index: 9,
};

const survivorPublicProfileMetadata: Pick<
  PublicProfileFantasyEntryResponse,
  'game_type' | 'survivor_round_count' | 'current_game_index'
> = {
  game_type: 'survivor',
  survivor_round_count: 10,
  current_game_index: 9,
};

// @ts-expect-error Survivor wire version is fixed at 1.
const invalidSurvivorVersion: SurvivorContestResponse = { ...survivorContest, version: 2 };

// @ts-expect-error awaiting-next-round requires a next game index.
const missingSurvivorNextRound: SurvivorContestResponse = {
  ...survivorContest,
  phase: "awaiting_next_round",
};

const leakedHiddenPicks: SurvivorRoundPicksResponse = {
  visibility: "hidden",
  // @ts-expect-error hidden Survivor rounds structurally prohibit entrant picks.
  picks: [{ market_id: 1, direction: "up", outcome: "pending" }],
};

// @ts-expect-error contest bet type responses require value.
const missingContestBetValue: ContestBetTypeResponse = { type: "num_bets" };

const poolImageRef: ShareImageRef = {
  source: "pool_image",
  pool_image_id: "550e8400-e29b-41d4-a716-446655440003",
};

// @ts-expect-error pool_image refs require pool_image_id.
const missingPoolImageId: ShareImageRef = { source: "pool_image" };

const withdrawParams: UserWithdrawParams = {
  amount_micros: 1000000,
  idempotency_key: "550e8400-e29b-41d4-a716-446655440001",
};

const privyWithdrawRequest: UserWithdrawRequest = {
  withdraw_params: withdrawParams,
  authorization: { type: "privy_token", token: "privy-token" },
};

const walletAuthorizedWithdrawRequest: UserWithdrawRequest = {
  withdraw_params: {
    amount_micros: 1_000_000,
    destination_address: "0xde709f2102306220921060314715629080e2fb77",
    idempotency_key: "550e8400-e29b-41d4-a716-446655440000",
  },
  authorization: {
    type: "wallet_signature",
    signature: "base64-signature",
    signed_at_ms: 1_785_529_737_000,
  },
};

// @ts-expect-error idempotency_key is required for withdrawal parameters.
const missingWithdrawIdempotencyKey: UserWithdrawParams = {
  amount_micros: 1000000,
};

const unsignedRfqRequest: CreateUnsignedRfqRequest = {
  privy_token: "privy-token",
  use_app_tokens: true,
  rfq_params: {
    wager_micros: 1000000,
    min_odds: 2.5,
    legs: [{ market_id: 42, direction: "up" }],
    shield_on: false,
    idempotency_key: "550e8400-e29b-41d4-a716-446655440002",
  },
};

const signedRfqRequest: CreateRfqRequest = {
  use_app_tokens: true,
  order: {
    user: "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    wager_micros: 1000000,
    min_odds: 2.5,
    legs: [{ market_id: 42, direction: "up" }],
    nonce: 123,
    expires_at_ms: 1735430300000,
    shield_on: false,
    signature: "signature",
  },
};

const nullSignedOrderType: CreateRfqRequest = {
  use_app_tokens: true,
  order: {
    user: "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    wager_micros: 1000000,
    min_odds: 2.5,
    legs: [{ market_id: 42, direction: "up" }],
    nonce: 123,
    expires_at_ms: 1735430300000,
    // @ts-expect-error order_type defaults only when omitted; Rust rejects null.
    order_type: null,
    shield_on: false,
    signature: "signature",
  },
};

const nullUnsignedOrderType: CreateUnsignedRfqRequest = {
  privy_token: "privy-token",
  use_app_tokens: true,
  rfq_params: {
    wager_micros: 1000000,
    min_odds: 2.5,
    legs: [{ market_id: 42, direction: "up" }],
    // @ts-expect-error order_type defaults only when omitted; Rust rejects null.
    order_type: null,
    shield_on: false,
    idempotency_key: "550e8400-e29b-41d4-a716-446655440002",
  },
};

const missingUnsignedShield: CreateUnsignedRfqRequest = {
  privy_token: "privy-token",
  use_app_tokens: true,
  // @ts-expect-error shield_on is required in Rust UnsignedRfqOrderRequest.
  rfq_params: {
    wager_micros: 1000000,
    min_odds: 2.5,
    legs: [{ market_id: 42, direction: "up" }],
    idempotency_key: "550e8400-e29b-41d4-a716-446655440002",
  },
};

const recentResolution: RecentResolutionEntry = {
  market_id: 42,
  outcome: "YES",
  window_start_ms: 1_735_689_600_000,
  resolved_at_ms: 1_735_689_901_000,
};

// @ts-expect-error window_start_ms is required to verify market-window adjacency.
const missingResolutionWindowStart: RecentResolutionEntry = {
  market_id: 42,
  outcome: "YES",
  resolved_at_ms: 1_735_689_901_000,
};

test("request DTO parity checks compile", () => {
  assert.equal(makerActivePosition.role, "maker");
  assert.equal(fantasyCreditedPayout(outcastFantasyResult), 7_500_000);
  assert.equal(chatMentionMessageId(chatMention), "66666666-6666-4666-8666-666666666666");
  assert.equal(chatMentionMessageId(marketChatMention), "77777777-7777-4777-8777-777777777777");
  assert.ok(sessionRequest);
  assert.ok(signedOrderInput);
  assert.ok(legacyCamelOdds);
  assert.ok(legacyWireOdds);
  assert.ok(walletAuthRequest);
  assert.ok(checkHandleQuery);
  assert.ok(fullVaultWithdrawal);
  assert.ok(partialVaultWithdrawal);
  assert.ok(avatarUrl);
  assert.ok(avatarSeed);
  assert.ok(missingAvatarUrl);
  assert.ok(missingAvatarSeed);
  assert.ok(emojiUrl);
  assert.ok(emojiUnicode);
  assert.ok(missingEmojiValue);
  assert.ok(contestNumBets);
  assert.ok(contestBetsPerCategory);
  assert.ok(legacyContestBetRequest);
  assert.equal(multiEntrySurvivorContestBetRequest.entry_index, 1);
  assert.ok(survivorContest);
  assert.ok(survivorOrdinarySuccessorGap);
  assert.ok(survivorEmptyReplacementGap);
  assert.ok(survivorReplacementGapWithScheduledSuccessor);
  assert.ok(survivorReplacementSummary);
  assert.ok(survivorEntry);
  assert.ok(survivorPortfolioMetadata);
  assert.ok(survivorPublicProfileMetadata);
  assert.ok(invalidSurvivorVersion);
  assert.ok(missingSurvivorNextRound);
  assert.ok(leakedHiddenPicks);
  assert.ok(missingContestBetValue);
  assert.ok(poolImageRef);
  assert.ok(missingPoolImageId);
  assert.ok(privyWithdrawRequest);
  assert.ok(walletAuthorizedWithdrawRequest);
  assert.ok(unsignedRfqRequest);
  assert.ok(signedRfqRequest);
  assert.ok(nullSignedOrderType);
  assert.ok(nullUnsignedOrderType);
  assert.ok(missingUnsignedShield);
  assert.ok(recentResolution);
  assert.ok(missingResolutionWindowStart);
});

test("market type exposes category constants without closing the wire type", () => {
  assert.deepEqual(Object.values(MarketType), [
    "sports",
    "culture",
    "crypto",
    "politics",
    "earnings",
    "entertainment",
    "esports",
    "weather",
    "mentions",
    "extra",
    "other",
  ]);
  const forwardCompatibleCategory: MarketType = "new-category";
  assert.equal(forwardCompatibleCategory, "new-category");
});
