import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { privateKeyToAccount } from "viem/accounts";

import {
  Address,
  Amount,
  Asset,
  BroadcastRfqRequest,
  Direction,
  Duration,
  MAX_RFQ_LEGS,
  MarketId,
  MmDecodeError,
  Odds,
  OrderType,
  QuoteResponse,
  QuoteDeclineReason,
  RequestId,
  RfqLeg,
  RfqLegWire,
  RfqLegWireDecodeError,
  RfqRequest,
  RfqRequestError,
  RfqSubscription,
  RFQ_PROTOCOL_VERSION,
  SerdeDecodeError,
  SignedOrder,
  SignedOrderError,
  TakerMetadata,
  Timestamp,
  U64_MAX,
  UserId,
  UserTier,
  authResponseMessage,
  buildAuthMessage,
  buildWalletAuthenticationMessage,
  buildWalletWithdrawalAuthorizationMessage,
  bytesToHex,
  decodeBroadcastRfq,
  decodeBase64,
  decodeBase64NoPad,
  encodeBase64,
  encodeWalletSignature,
  createRfqRequestFromSignedOrder,
  decodeApiJson,
  encodeBase64NoPad,
  parseOrderLegJson,
  parseAuthChallengeId,
  parseUnsignedRfqIdempotencyKey,
  encodeQuoteResponse,
  quoteResponseMessage,
  signAuthResponse,
  signedOrderJsonToSignedOrder,
  signedQuoteResponse,
  stringifySerde,
  toSerdeValue,
  ClientMessage,
  type ConfirmPositionQuery,
  type EventPositionShareCard,
  type EventMarket,
  type EventMarketSource,
  type FeedEventWithLegsResponse,
  type MarketLookupQuery,
  type MarketsShareCard,
  type PortfolioSummaryResponse,
  type PositionSummary,
  type RecentResolutionEntry,
  type SurvivorShareCard,
  type UserTransactionsRawQuery,
  type UserTransactionsResponse,
  unsignedRfqOrderRequestToSignedOrderForSession,
} from "../src/index.js";
import { OrderLeg, signOrder, signedOrder } from "../src/taker.js";

const fixture = JSON.parse(
  readFileSync(join(process.cwd(), "../fixtures/protocol/parity.json"), "utf8"),
) as any;
function requestId(): RequestId {
  return RequestId.fromString("00112233-4455-6677-8899-aabbccddeeff") as RequestId;
}

function takerId(): UserId {
  return UserId.fromString("ffeeddcc-bbaa-9988-7766-554433221100") as UserId;
}

test("public JSON boundary preserves unsafe API integers", () => {
  const json =
    '{"market_id":9007199254740993,"outcome":"up","window_start_ms":1,"resolved_at_ms":2}';
  const decoded = decodeApiJson<RecentResolutionEntry>(json, "RecentResolutionEntry");

  assert.equal(decoded.market_id, 9007199254740993n);
  assert.equal(stringifySerde(decoded), json);
  assert.throws(() => decodeApiJson("{}", "MissingSchema"), SerdeDecodeError);
});

test("user transactions preserve wire amounts and query strictness", () => {
  const response = decodeApiJson<UserTransactionsResponse>(
    '{"items":[{"id":"ledger-event","category":"withdrawal","title":"Withdrawal","status":"completed","occurred_at_ms":1700000000000,"amount_micros":"-9007199254740993","unit":"usdc","tx_hash":"0xabc"}],"next_cursor":null}',
    "UserTransactionsResponse",
  );
  assert.equal(response.items[0]?.amount_micros, "-9007199254740993");
  assert.equal(response.items[0]?.category, "withdrawal");
  assert.equal(response.next_cursor, null);

  const query: UserTransactionsRawQuery = {
    category: "withdrawal",
    from_ms: "1",
    to_ms: "2",
    limit: 25,
  };
  assert.deepEqual(
    decodeApiJson<UserTransactionsRawQuery>(JSON.stringify(query), "UserTransactionsRawQuery"),
    query,
  );
  assert.throws(
    () => decodeApiJson('{"limit":25,"unexpected":true}', "UserTransactionsRawQuery"),
    SerdeDecodeError,
  );
});

test("client query DTOs enforce required semantic route values", () => {
  const marketQuery: MarketLookupQuery = {
    asset: "BTC",
    duration_secs: 300,
    window_start_ms: 1,
  };
  const confirmation: ConfirmPositionQuery = { position_id: "position", accept: true };

  assert.doesNotThrow(() =>
    decodeApiJson<MarketLookupQuery>(JSON.stringify(marketQuery), "MarketLookupQuery"));
  assert.doesNotThrow(() =>
    decodeApiJson<ConfirmPositionQuery>(JSON.stringify(confirmation), "ConfirmPositionQuery"));

  for (const schema of [
    "ChatMentionCandidatesQuery",
    "MarketLookupQuery",
    "MarketCurrentQuery",
    "TopOfBookHistoryQuery",
    "PositionsByMarketsQuery",
    "ConfirmPositionQuery",
    "VaultIdQuery",
    "VaultPnlHistoryQuery",
    "VaultPositionsQuery",
    "VaultEventsQuery",
    "VaultContributorsQuery",
  ]) {
    assert.throws(() => decodeApiJson("{}", schema), SerdeDecodeError);
  }

  assert.throws(
    () => decodeApiJson(
      '{"asset":"BTC","duration_secs":"300","window_start_ms":1}',
      "MarketLookupQuery",
    ),
    SerdeDecodeError,
  );
  assert.throws(
    () => decodeApiJson('{"position_id":"position","accept":"true"}', "ConfirmPositionQuery"),
    SerdeDecodeError,
  );
  assert.throws(
    () => decodeApiJson('{"from":"1"}', "PnlHistoryScopedQuery"),
    SerdeDecodeError,
  );
});

test("API decoder rejects inherited object names as unknown fields", () => {
  const fields =
    '"address":"0x0000000000000000000000000000000000000000","signature":"x","signed_at_ms":1';

  for (const key of ["constructor", "toString", "__proto__"]) {
    const json = `{${fields},${JSON.stringify(key)}:"smuggled"}`;
    assert.throws(
      () => decodeApiJson(json, "WalletAuthRequest"),
      (error) =>
        error instanceof SerdeDecodeError && error.message.includes(`unknown fields ${key}`),
    );
  }
});

test("API decoder rejects duplicate Rust struct fields before JSON collapse", () => {
  const duplicateAddress =
    '{"address":"first","address":"second","signature":"x","signed_at_ms":1}';
  assert.throws(
    () => decodeApiJson(duplicateAddress, "WalletAuthRequest"),
    /duplicate field address/u,
  );

  const source = decodeApiJson<EventMarketSource>(
    '{"source":"manual","source_market_ids":[],"attributes":{"rank":1,"rank":2}}',
    "EventMarketSource",
  );
  assert.deepEqual(source.attributes, { rank: 2 });
});

test("RFQ subscription constructor emits only server-valid assets", () => {
  for (const asset of Asset.ALL) {
    const subscription = RfqSubscription.priceStrike(asset);
    assert.deepEqual(
      decodeApiJson(stringifySerde(subscription), "RfqSubscription"),
      subscription,
    );
  }

  assert.deepEqual(RfqSubscription.priceStrike(" btc "), {
    type: "price_strike",
    asset: "BTC",
  });
  assert.throws(() => RfqSubscription.priceStrike("DOGE"), /unsupported asset/);
  assert.throws(
    () => RfqSubscription.priceStrike(Asset.COUNT as Asset),
    /unsupported asset/,
  );
});

test("feed decoder defaults omitted legs to an empty array", () => {
  const decoded = decodeApiJson<FeedEventWithLegsResponse>(
    JSON.stringify({
      event_type: "won",
      position_id: "00000000-0000-0000-0000-000000000001",
      market: "test",
      legs_count: 0,
      user_display_name: "Anonymous",
      user_avatar_seed: 0,
      wager_micros: "0",
      multiplier_bps: 0,
      payout_micros: "0",
      event_at_ms: 1,
      primary_asset: null,
      has_binary_event_leg: false,
    }),
    "FeedEventWithLegsResponse",
  );

  assert.deepEqual(decoded.legs, []);
  assert.equal(decoded.event.event_type, "won");
  assert.equal(decoded.primary_asset, null);
  assert.equal(decoded.has_binary_event_leg, false);
});

test("API decoder materializes Rust map, wire-integer, and enum defaults", () => {
  const source = decodeApiJson<EventMarketSource>(
    JSON.stringify({ source: "kalshi", source_market_ids: ["KX-1"] }),
    "EventMarketSource",
  );
  assert.deepEqual(source.attributes, {});

  const featuredMarketWire = {
    id: 42,
    market_type: "culture",
    trading_channels: ["rfq"],
    chat_id: "culture-event",
    name: "Culture event",
    status: "OPEN",
    tradeable: true,
    featured_slot: 2,
    category_tags: ["culture"],
    betting_closes_at_ms: 1_000,
    resolution_time_ms: 2_000,
    created_at_ms: 500,
    source: { source: "kalshi", source_market_ids: ["KX-1"] },
  };
  const featuredMarket = decodeApiJson<EventMarket>(
    JSON.stringify(featuredMarketWire),
    "EventMarket",
  );
  assert.equal(featuredMarket.featured_slot, 2);
  const legacySafeMarketWire = { ...featuredMarketWire, featured_slot: undefined };
  const legacySafeMarket = decodeApiJson<EventMarket>(
    JSON.stringify(legacySafeMarketWire),
    "EventMarket",
  );
  assert.equal(legacySafeMarket.featured_slot, undefined);

  const position = decodeApiJson<PositionSummary>(
    JSON.stringify({
      id: "position",
      wager_micros: "1000000",
      refunded_app_token_micros: null,
      payout_micros: "2000000",
      net_payout_micros: null,
      legs_count: 1,
      legs_summary: "BTC up",
      status: "open",
      pnl_micros: null,
      created_at_ms: 1,
      has_binary_event_leg: false,
      market_types: [],
    }),
    "PositionSummary",
  );
  assert.equal(position.app_token_wager_micros, 0);

  const footer = { handle: "alice" };
  const markets = decodeApiJson<MarketsShareCard>(
    JSON.stringify({ position_id: "position", footer }),
    "MarketsShareCard",
  );
  assert.deepEqual(
    {
      state: markets.state,
      assets: markets.assets,
      windows: markets.windows,
      chart: markets.chart,
    },
    { state: "pre", assets: [], windows: [], chart: [] },
  );

  const survivor = decodeApiJson<SurvivorShareCard>(
    JSON.stringify({ contest_id: "contest", entry_index: 0, footer }),
    "SurvivorShareCard",
  );
  assert.deepEqual(
    {
      state: survivor.state,
      contest_type: survivor.contest_type,
      presentation: survivor.presentation,
    },
    { state: "pre", contest_type: "free", presentation: "daily" },
  );

  const eventPosition = decodeApiJson<EventPositionShareCard>(
    JSON.stringify({ position_id: "position", footer }),
    "EventPositionShareCard",
  );
  assert.equal(eventPosition.state, "active");
});

test("API decoder requires nullable fields that Rust serde requires", () => {
  const summary = {
    scope: "all",
    active_count: 0,
    potential_payout_micros: "0",
    realized_pnl_micros: "0",
  };

  assert.throws(
    () => decodeApiJson(JSON.stringify(summary), "PortfolioSummaryResponse"),
    /missing required field biggest_win_micros/u,
  );
  assert.equal(
    decodeApiJson<PortfolioSummaryResponse>(
      JSON.stringify({ ...summary, biggest_win_micros: null }),
      "PortfolioSummaryResponse",
    ).biggest_win_micros,
    null,
  );
  assert.equal(
    decodeApiJson<PortfolioSummaryResponse>(
      JSON.stringify({ ...summary, biggest_win_micros: "1250000" }),
      "PortfolioSummaryResponse",
    ).biggest_win_micros,
    "1250000",
  );
});

test("schema decoder accepts Rust unit enums with explicit discriminants", () => {
  const variants = [
    ["Asset", ["BTC", "ETH", "SOL", "XRP", "HYPE"]],
    ["Direction", ["Up", "Down"]],
    ["OrderType", ["IOC", "FOK"]],
    ["UserTier", ["Standard", "Silver", "Gold", "Platinum", "VIP"]],
  ] as const;
  for (const [schema, values] of variants) {
    for (const value of values) {
      assert.equal(decodeApiJson<string>(JSON.stringify(value), schema), value);
    }
  }

  const subscribe = {
    type: "subscribe",
    protocol_version: RFQ_PROTOCOL_VERSION,
    subscriptions: [{ type: "price_strike", asset: "BTC" }],
  } as const;
  assert.deepEqual(
    decodeApiJson<ClientMessage>(JSON.stringify(subscribe), "ClientMessage"),
    subscribe,
  );
});

test("quote decline preserves the typed request ID and closed reason", () => {
  const decline = ClientMessage.quoteDecline(
    requestId(),
    QuoteDeclineReason.SportsCombinationUnsupported,
  );
  const wire = {
    type: "quote_decline",
    request_id: "00112233-4455-6677-8899-aabbccddeeff",
    reason: "sports_combination_unsupported",
  };

  assert.deepEqual(decline, wire);
  assert.deepEqual(decodeApiJson(JSON.stringify(wire), "ClientMessage"), wire);
});

type FixtureRfqLeg = {
  market_id: number;
  start_at_ms: number;
  direction: Direction;
  leg_index: number;
  price_window_secs: number;
} & ({ type_tag: 0; asset: Asset } | { type_tag: 2 });

function fixtureRfqLeg(row: FixtureRfqLeg): RfqLeg {
  if (row.type_tag === 0) {
    return RfqLeg.newPriceStrike(
      row.market_id,
      row.start_at_ms,
      row.asset,
      row.direction,
      Duration.fromSecs(row.price_window_secs)!,
      row.leg_index,
    );
  }
  return RfqLeg.newBinaryEvent(
    row.market_id,
    row.start_at_ms,
    row.direction,
    row.leg_index,
  );
}

test("RFQ leg builder rejects boolean enum inputs", () => {
  const booleanAsset = true as unknown as Asset;
  const booleanDirection = true as unknown as Direction;

  assert.throws(
    () =>
      RfqLeg.priceStrike(
        1,
        0,
        booleanAsset,
        Direction.Up,
        Duration.ONE_MINUTE,
        0,
      ),
    /asset must be an unsigned integer/,
  );
  assert.throws(
    () =>
      RfqLeg.priceStrike(
        1,
        0,
        Asset.BTC,
        booleanDirection,
        Duration.ONE_MINUTE,
        0,
      ),
    /direction must be an unsigned integer/,
  );
});

test("RFQ constructors reject coerced byte-sized enum inputs", () => {
  const leg = RfqLeg.binaryEvent(1, 0, Direction.Up, 0);

  for (const invalid of [true, "1"]) {
    const direction = invalid as unknown as Direction;
    const tier = invalid as unknown as UserTier;
    const orderType = invalid as unknown as OrderType;

    assert.throws(
      () => new RfqLegWire({ direction }),
      /direction must be an unsigned integer/,
    );
    assert.throws(
      () => new TakerMetadata(tier, fixture.mm_signing.wallet_address),
      /tier must be an unsigned integer/,
    );
    assert.throws(
      () =>
        new RfqRequest({
          requestId: requestId(),
          takerId: takerId(),
          orderType,
          legs: [leg],
        }),
      /order_type must be an unsigned integer/,
    );
    assert.throws(
      () =>
        new BroadcastRfqRequest({
          requestId: requestId(),
          orderType,
        }),
      /order_type must be an unsigned integer/,
    );
  }
});

test("EVM address parsing accepts bare and prefixed hex like Rust", () => {
  const prefixed = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1";
  const bare = prefixed.slice(2);
  const uppercase = `0x${bare.toUpperCase()}`;
  const nonChecksummedMixed = prefixed.replace("d", "D");

  assert.equal(Address.fromHex(bare).toChecksum(), prefixed);
  assert.equal(Address.fromHex(prefixed).toChecksum(), prefixed);
  assert.equal(Address.fromHex(uppercase).toChecksum(), prefixed);
  assert.equal(Address.fromHex(nonChecksummedMixed).toChecksum(), prefixed);
  for (const invalid of [prefixed.slice(0, -1), `${prefixed.slice(0, -1)}g`]) {
    assert.throws(() => Address.fromHex(invalid), /invalid EVM address/);
  }
  Address.ZERO.bytes.fill(0xff);
  assert.equal(Address.zero().hex(), `0x${"00".repeat(20)}`);
  const source = new Uint8Array(20);
  const address = Address.fromSlice(source.buffer);
  source.fill(0xff);
  assert.equal(address.hex(), `0x${"00".repeat(20)}`);
  for (const bytes of [[-1], [1.5], [256], Array<number>(20)]) {
    assert.throws(() => Address.fromSlice(bytes), /0 to 255/);
  }

  const order = new SignedOrder({
    user: bare,
    wager_micros: 1_000_000,
    minOddsBps: 20_000,
    legs: [new OrderLeg({ market_id: 42, direction: Direction.Up })],
    nonce: 123,
    expires_at_ms: 1735430300000,
    order_type: OrderType.FOK,
  });
  const metadata = TakerMetadata.new(UserTier.Gold, bare);

  assert.equal(order.user.toChecksum(), prefixed);
  assert.equal(metadata.address.toChecksum(), prefixed);
  assert.equal(MarketId.new(42).toString(), "42");
  assert.equal(MarketId.new(42).serdeValue(), 42);
});

test("duration display uses compact labels for all valid fixed windows", () => {
  assert.equal(Duration.FIFTEEN_MINUTES.toString(), "15m");
  assert.equal(Duration.FOUR_HOURS.toString(), "4h");
  assert.equal(Duration.ONE_DAY.toString(), "1d");
});

test("auth message matches shared fixture", () => {
  const auth = fixture.auth_message;
  const message = buildAuthMessage(
    fixture.mm_signing.wallet_address,
    auth.challenge_id,
    auth.timestamp_ms,
  );

  assert.equal(message, auth.message);
  assert.equal(bytesToHex(new TextEncoder().encode(message)), auth.message_hex);
});

test("auth challenge IDs require canonical RFC 4122 UUIDv4 text", () => {
  assert.equal(
    parseAuthChallengeId("550e8400-e29b-41d4-a716-446655440000"),
    "550e8400-e29b-41d4-a716-446655440000",
  );
  for (const invalid of [
    "550E8400-E29B-41D4-A716-446655440000",
    "550e8400e29b41d4a716446655440000",
    "550e8400-e29b-11d4-a716-446655440000",
    "550e8400-e29b-41d4-0716-446655440000",
    "not-a-uuid",
  ]) {
    assert.throws(() => parseAuthChallengeId(invalid), /challenge ID/);
  }
});

test("base64 helpers round trip without Node runtime dependencies", () => {
  const bytes = Uint8Array.from([0, 1, 2, 253, 254, 255]);

  assert.equal(encodeBase64(bytes), "AAEC/f7/");
  assert.deepEqual(Array.from(decodeBase64("AAEC/f7/")), Array.from(bytes));
  assert.equal(encodeBase64NoPad(Uint8Array.from([0, 0])), "AAA");
  assert.deepEqual(Array.from(decodeBase64NoPad("AAA")), [0, 0]);
  assert.throws(() => decodeBase64NoPad("A"), /base64/);
  assert.throws(() => decodeBase64NoPad("/x"), /base64/);
  for (const noncanonical of ["AB==", "AAB="]) {
    assert.throws(() => decodeBase64(noncanonical), /base64/);
  }
});

test("taker signing bytes match shared fixture", () => {
  const row = fixture.taker_signed_order;
  const input = {
    user: Address.fromHex(row.user),
    wager_micros: row.wager_micros,
    minOddsBps: row.min_odds_bps,
    legs: [
      new OrderLeg({ market_id: 42, direction: Direction.Down }),
      new OrderLeg({ market_id: 99, direction: Direction.Up }),
    ],
    nonce: row.nonce,
    expires_at_ms: row.expires_at_ms,
    order_type: OrderType.FOK,
    shield_on: row.shield_on,
  };
  const order = new SignedOrder(input);

  assert.equal(bytesToHex(order.signingBytes(row.use_app_tokens)), row.signing_bytes_hex);
  const invalidOrders = [
    new SignedOrder({ ...input, legs: [] }),
    new SignedOrder({ ...input, legs: [new OrderLeg({ market_id: 42, direction: 2 })] }),
    new SignedOrder({
      ...input,
      legs: Array(SignedOrder.MAX_LEGS + 1).fill(input.legs[0]),
    }),
    new SignedOrder({ ...input, order_type: 3 }),
  ];
  for (const invalid of invalidOrders) {
    assert.throws(() => invalid.signingBytes(row.use_app_tokens), SignedOrderError);
    assert.throws(() => createRfqRequestFromSignedOrder(invalid, true), SignedOrderError);
  }
  const overflow = new SignedOrder({ ...input, wager_micros: U64_MAX + 1n });
  assert.throws(() => overflow.signingBytes(row.use_app_tokens), /fit in u64/);
  assert.throws(() => createRfqRequestFromSignedOrder(overflow, true), /fit in u64/);

  for (const shieldOn of ["false", null]) {
    const invalidShield = new SignedOrder({
      ...input,
      shield_on: shieldOn as unknown as boolean,
    });
    assert.throws(() => invalidShield.signingBytes(false), /shield_on must be bool/);
    assert.throws(
      () => createRfqRequestFromSignedOrder(invalidShield, false),
      /shield_on must be bool/,
    );
  }

  const invalidUseAppTokens = "false" as unknown as boolean;
  assert.throws(() => order.signingBytes(invalidUseAppTokens), /use_app_tokens must be bool/);
  assert.throws(
    () => createRfqRequestFromSignedOrder(order, invalidUseAppTokens),
    /use_app_tokens must be bool/,
  );
});

test("taker signing helper signs EIP-191 preimage", async () => {
  const row = fixture.taker_signed_order;
  const signing = fixture.mm_signing;
  const account = privateKeyToAccount(signing.private_key);
  const order = new SignedOrder({
    user: account.address,
    wager_micros: row.wager_micros,
    minOddsBps: row.min_odds_bps,
    legs: [new OrderLeg({ market_id: 42, direction: Direction.Down })],
    nonce: row.nonce,
    expires_at_ms: row.expires_at_ms,
    order_type: OrderType.FOK,
    shield_on: row.shield_on,
  });

  const signed = await signOrder(order, row.use_app_tokens, signing.private_key);
  const built = await signedOrder(order, row.use_app_tokens, signing.private_key);
  const directSignature = await account.signMessage({
    message: {
      raw: bytesToHex(order.signingBytes(row.use_app_tokens), true) as `0x${string}`,
    },
  });

  assert.deepEqual(signed, built);
  assert.equal(bytesToHex(signed.signature, true), directSignature);
  assert.notDeepEqual(Array.from(signed.signature), Array(65).fill(0));
  assert.equal(await signed.verifySignature(row.use_app_tokens), true);
  assert.equal(await signed.verifySignature(!row.use_app_tokens), false);

  const tamperedSignature = new Uint8Array(signed.signature);
  tamperedSignature[0] ^= 1;
  assert.equal(
    await new SignedOrder({ ...signed, signature: tamperedSignature }).verifySignature(
      row.use_app_tokens,
    ),
    false,
  );
  assert.equal(
    await new SignedOrder({
      ...signed,
      wagerMicros: BigInt(signed.wagerMicros) + 1n,
    }).verifySignature(row.use_app_tokens),
    false,
  );
  assert.equal(
    await new SignedOrder({ ...signed, legs: [] }).verifySignature(row.use_app_tokens),
    false,
  );
});

test("taker signing rejects more than max legs", () => {
  const row = fixture.taker_signed_order;
  const order = new SignedOrder({
    user: row.user,
    wager_micros: row.wager_micros,
    minOddsBps: row.min_odds_bps,
    legs: Array.from(
      { length: SignedOrder.MAX_LEGS },
      () => new OrderLeg({ market_id: 42, direction: Direction.Down }),
    ),
    nonce: row.nonce,
    expires_at_ms: row.expires_at_ms,
    order_type: OrderType.FOK,
    shield_on: row.shield_on,
  });
  assert.equal(SignedOrder.MAX_LEGS, 9);
  order.signingBytes(row.use_app_tokens);
  order.legs.push(new OrderLeg({ market_id: 99, direction: Direction.Up }));

  assert.throws(() => order.signingBytes(row.use_app_tokens), /order legs exceed MAX_LEGS/);
});

test("quote response matches shared fixture", () => {
  const row = fixture.quote_response;
  const quote = QuoteResponse.new(
    requestId(),
    new Odds(row.odds),
    Amount.fromMicro(row.max_fill_micros),
  );

  assert.equal(bytesToHex(quote.toBytes()), row.bytes_hex);
  assert.equal(bytesToHex(quote.signedDataBytes()), row.signed_data_hex);
  assert.equal(encodeQuoteResponse(quote), row.base64);
});

test("odds arithmetic saturates at Rust u64 boundaries", () => {
  const wager = U64_MAX / 2n + 1n;
  const twoX = Odds.fromDecimal(2, 0);
  assert.equal(twoX.checkedCalculatePayout(wager), undefined);
  assert.equal(twoX.calculatePayout(wager), U64_MAX);
  assert.equal(twoX.checkedCalculateProfit(wager), wager);
  assert.equal(twoX.checkedCalculateMmLiability(wager), wager);
  assert.equal(Odds.fromDecimal(3, 0).calculateProfit(wager), U64_MAX);
});

test("timestamp arithmetic matches Rust checked u64 boundaries", () => {
  const maxSeconds = U64_MAX / 1000n;

  assert.equal(Timestamp.fromSecs(maxSeconds)?.asMillis(), maxSeconds * 1000n);
  assert.equal(Timestamp.fromSecs(U64_MAX), undefined);
  assert.equal(Timestamp.fromMillis(U64_MAX).addMillis(0)?.asMillis(), U64_MAX);
  assert.equal(Timestamp.fromMillis(U64_MAX).addMillis(1), undefined);
});

test("broadcast RFQ matches shared fixture", () => {
  const row = fixture.broadcast_rfq;
  const legs = (row.legs as FixtureRfqLeg[]).map(fixtureRfqLeg);
  const request = RfqRequest.new(
    requestId(),
    takerId(),
    Amount.fromMicro(row.wager_micros),
    OrderType.IOC,
    new Odds(row.min_odds),
    TakerMetadata.new(UserTier.Gold, Address.fromHex(row.taker_metadata.address)),
    legs,
  );
  request.setExpiresAtMs(row.expires_at_ms);

  const bytes = request.toBroadcastBytes();
  const decoded = decodeBroadcastRfq(row.base64);

  assert.equal(bytesToHex(bytes), row.bytes_hex);
  assert.equal(encodeBase64NoPad(bytes), row.base64);
  assert.deepEqual(decoded.toBytes(), bytes);
  assert.deepEqual(request.activeLegs(), legs);
  assert.equal(decoded.legCount, MAX_RFQ_LEGS);
  assert.equal(decoded.activeLegWires().length, MAX_RFQ_LEGS);
  assert.deepEqual(decoded.leg(MAX_RFQ_LEGS - 1), legs[MAX_RFQ_LEGS - 1]);
  assert.equal(decoded.legWire(MAX_RFQ_LEGS), undefined);
});

test("broadcast RFQ preserves taker metadata wire bytes", () => {
  const raw = decodeBase64NoPad(fixture.broadcast_rfq.base64);
  raw[32] = 2;
  raw[34] = 0xaa;
  raw[35] = 0xbb;

  const decoded = decodeBroadcastRfq(encodeBase64NoPad(raw));

  assert.deepEqual(decoded.toBytes(), raw);
});

test("RFQ leg wire decoder round-trips inactive padding without typed validation", () => {
  const wire = RfqLegWire.default();
  const bytes = wire.toBytes();

  assert.deepEqual(RfqLegWire.fromBytes(bytes).toBytes(), bytes);
  assert.throws(() => RfqLeg.fromWireBytes(bytes), RfqLegWireDecodeError);
});

test("market-maker decoder rejects wrong-size RFQs", () => {
  assert.throws(
    () =>
      decodeBroadcastRfq(
        encodeBase64NoPad(new Uint8Array(BroadcastRfqRequest.SIZE - 1)),
      ),
    (error) =>
      error instanceof MmDecodeError &&
      error.kind === "broadcast RFQ" &&
      error.expected === BroadcastRfqRequest.SIZE &&
      error.actual === BroadcastRfqRequest.SIZE - 1,
  );
});

test("raw RFQ parser preserves invalid counts but public decoder rejects them", () => {
  for (const legCount of [0, MAX_RFQ_LEGS + 1]) {
    const raw = decodeBase64NoPad(fixture.broadcast_rfq.base64);
    raw[57] = legCount;

    const parsed = BroadcastRfqRequest.fromBytes(raw);
    assert.equal(parsed.legCount, legCount);
    assert.deepEqual(parsed.toBytes(), raw);

    assert.throws(
      () => decodeBroadcastRfq(encodeBase64NoPad(raw)),
      (error) =>
        error instanceof MmDecodeError &&
        error.message.includes(`expected 1..=${MAX_RFQ_LEGS}`),
    );
  }
});

test("market-maker decoder rejects RFQ protocol version one", () => {
  const raw = decodeBase64NoPad(fixture.broadcast_rfq.base64);
  raw[58] = 1;

  assert.throws(
    () => decodeBroadcastRfq(encodeBase64NoPad(raw)),
    (error) =>
      error instanceof MmDecodeError &&
      error.expected === RFQ_PROTOCOL_VERSION &&
      error.actual === 1,
  );
});

test("RFQ request rejects unsupported leg counts", () => {
  const row = fixture.broadcast_rfq;
  const leg = fixtureRfqLeg(row.legs[0] as FixtureRfqLeg);
  const request = (legCount: number) =>
    RfqRequest.new(
      requestId(),
      takerId(),
      Amount.fromMicro(row.wager_micros),
      OrderType.IOC,
      new Odds(row.min_odds),
      undefined,
      Array.from({ length: legCount }, () => leg),
    );

  assert.throws(() => request(0), /at least one leg/);
  assert.throws(() => request(MAX_RFQ_LEGS + 1), RfqRequestError);
});

test("market-maker signing matches shared fixture", async () => {
  const auth = fixture.auth_message;
  const quoteCase = fixture.quote_response;
  const row = fixture.mm_signing;
  const authSignature = await signAuthResponse(
    auth.challenge_id,
    auth.timestamp_ms,
    row.private_key,
  );
  const authMessage = await authResponseMessage(
    auth.challenge_id,
    auth.timestamp_ms,
    row.private_key,
  );
  const signedQuote = await signedQuoteResponse(
    requestId(),
    new Odds(quoteCase.odds),
    Amount.fromMicro(quoteCase.max_fill_micros),
    row.private_key,
  );
  const quoteMessage = quoteResponseMessage(signedQuote);

  assert.equal(bytesToHex(authSignature), row.auth_signature_hex);
  assert.deepEqual(authMessage, {
    type: "auth_response",
    wallet_address: row.wallet_address,
    signature: row.auth_signature_hex,
  });
  assert.equal(bytesToHex(signedQuote.signature), row.quote_signature_hex);
  assert.equal(bytesToHex(signedQuote.toBytes()), row.signed_quote_bytes_hex);
  assert.deepEqual(quoteMessage, { type: "quote", data: row.signed_quote_base64 });
  assert.equal(await signedQuote.verifySignature(Address.fromHex(row.wallet_address)), true);
});

test("signed order JSON conversion matches Rust helper semantics", () => {
  const row = fixture.taker_signed_order;
  const order = new SignedOrder({
    user: Address.fromHex(row.user),
    wager_micros: row.wager_micros,
    minOddsBps: row.min_odds_bps,
    legs: [
      new OrderLeg({ market_id: 42, direction: Direction.Down }),
      new OrderLeg({ market_id: 99, direction: Direction.Up }),
    ],
    nonce: row.nonce,
    expires_at_ms: row.expires_at_ms,
    order_type: OrderType.FOK,
    shield_on: row.shield_on,
  });

  assert.deepEqual(createRfqRequestFromSignedOrder(order, true), {
    use_app_tokens: true,
    order: {
      user: Address.fromHex(row.user).toChecksum(),
      wager_micros: row.wager_micros,
      min_odds: 2.5,
      legs: [
        { market_id: 42, direction: "down" },
        { market_id: 99, direction: "up" },
      ],
      nonce: row.nonce,
      expires_at_ms: row.expires_at_ms,
      order_type: 2,
      shield_on: false,
      signature: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    },
  });
});

test("signed order JSON conversion preserves unsafe u64 fields as strings", () => {
  const order = new SignedOrder({
    user: Address.ZERO,
    wager_micros: 9007199254740993n,
    minOddsBps: 25_000,
    legs: [new OrderLeg({ market_id: 42, direction: Direction.Up })],
    nonce: 9007199254740994n,
    expires_at_ms: 9007199254740995n,
    order_type: OrderType.FOK,
    shield_on: false,
  });

  assert.deepEqual(createRfqRequestFromSignedOrder(order, false), {
    use_app_tokens: false,
    order: {
      user: Address.ZERO.toChecksum(),
      wager_micros: "9007199254740993",
      min_odds: 2.5,
      legs: [{ market_id: 42, direction: "up" }],
      nonce: "9007199254740994",
      expires_at_ms: "9007199254740995",
      order_type: 2,
      shield_on: false,
      signature: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    },
  });
});

test("signed order serde value matches Longshot wire DTO", () => {
  const order = new SignedOrder({
    user: Address.ZERO,
    wager_micros: 9007199254740993n,
    minOddsBps: 25_000,
    legs: [
      new OrderLeg({ market_id: 42, direction: Direction.Down }),
      new OrderLeg({ market_id: 99, direction: Direction.Up }),
    ],
    nonce: 9007199254740994n,
    expires_at_ms: 9007199254740995n,
    order_type: OrderType.FOK,
    shield_on: false,
  });

  assert.deepEqual(toSerdeValue(order), {
    user: Address.ZERO.toChecksum(),
    wager_micros: "9007199254740993",
    min_odds: 2.5,
    legs: [
      { market_id: 42, direction: "down" },
      { market_id: 99, direction: "up" },
    ],
    nonce: "9007199254740994",
    expires_at_ms: "9007199254740995",
    order_type: 2,
    shield_on: false,
    signature: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
  });
});

test("signed order JSON parses back into signed order semantics", () => {
  const json = {
    user: "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    wager_micros: "9007199254740993",
    min_odds: 2.5,
    legs: [
      { market_id: 42, direction: "DOWN" },
      { market_id: 99, direction: "up" },
    ],
    nonce: "9007199254740994",
    expires_at_ms: "9007199254740995",
    shield_on: true,
    signature: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
  };

  const order = signedOrderJsonToSignedOrder(json);

  assert.equal(order.user.toChecksum(), json.user);
  assert.equal(order.wagerMicros, json.wager_micros);
  assert.equal(order.minOddsBps, 25_000);
  assert.deepEqual(
    order.legs.map((leg) => leg.serdeValue()),
    [
      { market_id: 42, direction: Direction.Down },
      { market_id: 99, direction: Direction.Up },
    ],
  );
  assert.equal(order.nonce, json.nonce);
  assert.equal(order.expiresAtMs, json.expires_at_ms);
  assert.equal(order.orderType, OrderType.FOK);
  assert.equal(order.shieldOn, true);
  assert.equal(bytesToHex(order.signature), "00".repeat(65));
});

test("unsigned RFQ request parses UUID and builds session signed order", () => {
  const request = {
    wager_micros: 1_500_000,
    min_odds: 1.75,
    legs: [{ market_id: 7, direction: "down" }],
    shield_on: false,
    idempotency_key: " 00112233-4455-6677-8899-aabbccddeeff ",
  };

  const canonicalId = "00112233-4455-6677-8899-aabbccddeeff";
  for (const idempotencyKey of [
    ` ${canonicalId} `,
    "00112233445566778899AABBCCDDEEFF",
    "{00112233-4455-6677-8899-AABBCCDDEEFF}",
    "urn:uuid:00112233-4455-6677-8899-AABBCCDDEEFF",
  ]) {
    assert.equal(
      parseUnsignedRfqIdempotencyKey({ ...request, idempotency_key: idempotencyKey }).asUuid(),
      canonicalId,
    );
  }

  const order = unsignedRfqOrderRequestToSignedOrderForSession(
    request,
    Address.ZERO,
    123n,
    456n,
  );

  assert.equal(order.user.toChecksum(), Address.ZERO.toChecksum());
  assert.equal(order.wagerMicros, request.wager_micros);
  assert.equal(order.minOddsBps, 17_500);
  assert.deepEqual(order.legs.map((leg) => leg.serdeValue()), [
    { market_id: 7, direction: Direction.Down },
  ]);
  assert.equal(order.nonce, 123n);
  assert.equal(order.expiresAtMs, 456n);
  assert.equal(order.orderType, OrderType.FOK);
  assert.equal(bytesToHex(order.signature), "00".repeat(65));
});

test("wallet withdrawal authorization message and signature encoding are canonical", () => {
  const authenticationMessage = buildWalletAuthenticationMessage(
    "longshot.xyz",
    "0x52908400098527886e0f7030069857d2e4169ee7",
    1_735_430_000_000,
  );
  assert.equal(
    authenticationMessage,
    "Longshot Wallet Authentication\n\nVersion: 1\nDomain: longshot.xyz\nAuth Address: 0x52908400098527886E0F7030069857D2E4169EE7\nTimestamp: 1735430000000",
  );

  const message = buildWalletWithdrawalAuthorizationMessage(
    "longshot.xyz",
    8453,
    "0x52908400098527886e0f7030069857d2e4169ee7",
    "0xde709f2102306220921060314715629080e2fb77",
    1_000_000,
    "550E8400-E29B-41D4-A716-446655440000",
    1_785_529_737_000,
  );

  assert.equal(
    message,
    "Longshot Withdrawal Authorization\n\nVersion: 1\nDomain: longshot.xyz\nChain ID: 8453\nAuth Address: 0x52908400098527886E0F7030069857D2E4169EE7\nDestination Address: 0xde709f2102306220921060314715629080e2fb77\nAmount Micros: 1000000\nIdempotency Key: 550e8400-e29b-41d4-a716-446655440000\nTimestamp: 1785529737000",
  );
  assert.equal(encodeWalletSignature(new Uint8Array(65).fill(7)), "BwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwc=");
  assert.throws(() => encodeWalletSignature(new Uint8Array(64)), /65 bytes/);
});

test("wallet canonical message builders enforce the Rust u64 domain", () => {
  const domain = "longshot.xyz";
  const authAddress = "0x52908400098527886e0f7030069857d2e4169ee7";
  const destinationAddress = "0xde709f2102306220921060314715629080e2fb77";
  const idempotencyKey = "550e8400-e29b-41d4-a716-446655440000";

  assert.doesNotThrow(() => buildWalletAuthenticationMessage(domain, authAddress, U64_MAX));
  assert.doesNotThrow(() =>
    buildWalletWithdrawalAuthorizationMessage(
      domain,
      U64_MAX,
      authAddress,
      destinationAddress,
      U64_MAX,
      idempotencyKey,
      U64_MAX,
    ),
  );

  for (const invalid of [-1n, U64_MAX + 1n]) {
    assert.throws(
      () => buildWalletAuthenticationMessage(domain, authAddress, invalid),
      /signed_at_ms must fit in u64/,
    );
    assert.throws(
      () =>
        buildWalletWithdrawalAuthorizationMessage(
          domain,
          invalid,
          authAddress,
          destinationAddress,
          1,
          idempotencyKey,
          1,
        ),
      /chain_id must fit in u64/,
    );
    assert.throws(
      () =>
        buildWalletWithdrawalAuthorizationMessage(
          domain,
          1,
          authAddress,
          destinationAddress,
          invalid,
          idempotencyKey,
          1,
        ),
      /amount_micros must fit in u64/,
    );
    assert.throws(
      () =>
        buildWalletWithdrawalAuthorizationMessage(
          domain,
          1,
          authAddress,
          destinationAddress,
          1,
          idempotencyKey,
          invalid,
        ),
      /signed_at_ms must fit in u64/,
    );
  }
});

test("RFQ JSON helpers reject invalid Rust parity cases", () => {
  assert.throws(() => parseOrderLegJson({ market_id: 0, direction: "up" }), /invalid market id/);
  assert.throws(() => parseOrderLegJson({ market_id: 1, direction: "flat" }), /invalid direction/);

  const valid = {
    user: Address.ZERO.toChecksum(),
    wager_micros: 1_000_000,
    min_odds: 2,
    legs: [{ market_id: 1, direction: "up" }],
    nonce: 1,
    expires_at_ms: 2,
    order_type: OrderType.FOK,
    shield_on: false,
    signature: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
  };

  assert.throws(() => signedOrderJsonToSignedOrder({ ...valid, min_odds: 1 }), /invalid min odds/);
  assert.throws(() => signedOrderJsonToSignedOrder({ ...valid, legs: [] }), /at least one leg/);
  assert.throws(
    () =>
      signedOrderJsonToSignedOrder({
        ...valid,
        legs: Array(SignedOrder.MAX_LEGS + 1).fill(valid.legs[0]),
      }),
    /too many legs/,
  );
  assert.throws(() => signedOrderJsonToSignedOrder({ ...valid, order_type: 9 }), /invalid order type/);
  const nullOrderType = null as unknown as number;
  assert.throws(
    () => signedOrderJsonToSignedOrder({ ...valid, order_type: nullOrderType }),
    /invalid order type/,
  );
  assert.throws(
    () =>
      unsignedRfqOrderRequestToSignedOrderForSession(
        {
          wager_micros: 1,
          min_odds: 2,
          legs: [{ market_id: 1, direction: "up" }],
          order_type: nullOrderType,
          shield_on: false,
          idempotency_key: "00112233-4455-6677-8899-aabbccddeeff",
        },
        Address.ZERO,
        1,
        2,
      ),
    /invalid order type/,
  );
  assert.throws(() => signedOrderJsonToSignedOrder({ ...valid, signature: "not-base64" }), /base64/);
  for (const shieldOn of [undefined, null, "false"]) {
    const invalidShieldOn = shieldOn as unknown as boolean;
    assert.throws(
      () => signedOrderJsonToSignedOrder({ ...valid, shield_on: invalidShieldOn }),
      /shield_on must be bool/,
    );
    assert.throws(
      () =>
        unsignedRfqOrderRequestToSignedOrderForSession(
          {
            wager_micros: 1,
            min_odds: 2,
            legs: [{ market_id: 1, direction: "up" }],
            shield_on: invalidShieldOn,
            idempotency_key: "00112233-4455-6677-8899-aabbccddeeff",
          },
          Address.ZERO,
          1,
          2,
        ),
      /shield_on must be bool/,
    );
  }
  assert.throws(
    () =>
      parseUnsignedRfqIdempotencyKey({
        wager_micros: 1,
        min_odds: 2,
        legs: [{ market_id: 1, direction: "up" }],
        shield_on: false,
        idempotency_key: "not-a-uuid",
      }),
    /invalid UUID/,
  );
  for (const idempotencyKey of [
    "{00112233445566778899aabbccddeeff}",
    "urn:uuid:00112233445566778899aabbccddeeff",
    "URN:UUID:00112233-4455-6677-8899-aabbccddeeff",
  ]) {
    assert.throws(
      () =>
        parseUnsignedRfqIdempotencyKey({
          wager_micros: 1,
          min_odds: 2,
          legs: [{ market_id: 1, direction: "up" }],
          shield_on: false,
          idempotency_key: idempotencyKey,
        }),
      /invalid UUID/,
    );
  }
});
