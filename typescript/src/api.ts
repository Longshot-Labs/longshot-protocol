// Hand-maintained TypeScript mirror of rust/src/api/*.rs; parity is enforced by tests.
// Runtime serde behavior lives in model.ts; protocol behavior lives in rfq.ts and taker.ts.

import { Address, Direction, MarketId, Odds, OrderType, PositionId, UuidId } from "./types.js";
import type {
  MarketStatus,
  MarketType,
  Outcome,
  TradingChannel,
  WideInteger,
} from "./types.js";
import { OrderLeg, SignedOrder, SignedOrderError } from "./taker.js";
import { bytesFrom, checkU64, decodeBase64, encodeBase64 } from "./bytes.js";
import type { BytesLike } from "./bytes.js";

export interface PublicMarketsRawQuery {
  market_type?: MarketType | null;
  trading_channel?: TradingChannel | null;
  limit?: number | null;
  cursor?: string | null;
  /** Market statuses sent as one comma-separated query value. */
  statuses?: MarketStatus[] | null;
}

export function publicMarketsRawQueryToWire(query: PublicMarketsRawQuery): Record<string, unknown> {
  return { ...query, statuses: query.statuses?.join(",") };
}

export interface PriceStrikeMarket {
  id: MarketId;
  market_type: MarketType;
  trading_channels: TradingChannel[];
  name: string;
  description?: string | null;
  status: MarketStatus;
  tradeable: boolean;
  category_tags: string[];
  betting_closes_at_ms: WideInteger;
  resolution_time_ms: WideInteger;
  open_strike_micros?: WideInteger | null;
  resolved_outcome?: Outcome | null;
  created_at_ms: WideInteger;
  opened_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  image_url?: string | null;
}

export interface EventMarket {
  id: MarketId;
  market_type: MarketType;
  trading_channels: TradingChannel[];
  name: string;
  description?: string | null;
  resolution_rules?: string;
  status: MarketStatus;
  tradeable: boolean;
  category_tags: string[];
  opens_at_ms: WideInteger | null;
  /** Original event start, distinct from Longshot's lifecycle `opens_at_ms`. */
  source_starts_at_ms?: WideInteger | null;
  betting_closes_at_ms: WideInteger;
  resolution_time_ms: WideInteger;
  live_ends_at_ms?: WideInteger | null;
  resolved_outcome?: Outcome | null;
  created_at_ms: WideInteger;
  opened_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  display_probability_bps?: number | null;
  image_url?: string | null;
}

export type PublicMarket = EventMarket | PriceStrikeMarket;

export interface PublicMarketResponse {
  market: PublicMarket;
}

export interface PublicMarketsResponse {
  markets: PublicMarket[];
  next_cursor?: string | null;
}

export interface MarketMetadataEntry {
  market_id: WideInteger;
  asset: string;
  duration_secs: number;
  start_at_ms: WideInteger;
  betting_closes_at_ms: WideInteger;
}

export interface MarketLookupResponse {
  market: MarketMetadataEntry;
}

export interface MarketLookupQuery {
  asset: string;
  duration_secs: number;
  window_start_ms: WideInteger;
}

export interface MarketCurrentQuery {
  asset: string;
  duration_secs: number;
}

export interface RecentResolutionsQuery {
  asset: string;
  duration_secs: number;
  limit?: number | null;
}

export interface RecentResolutionEntry {
  market_id: WideInteger;
  outcome: string;
  window_start_ms: WideInteger;
  resolved_at_ms: WideInteger;
}

export interface RecentResolutionsResponse {
  asset: string;
  duration_secs: number;
  resolutions: RecentResolutionEntry[];
}

export interface ProfitCapOverrideResponse {
  market_type: MarketType;
  max_profit_micros: WideInteger;
}

export interface ProfitCapConfigResponse {
  default_max_profit_micros: WideInteger;
  overrides: ProfitCapOverrideResponse[];
}

export interface PortfolioStatsResponse {
  total_positions: number;
  open_positions: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  total_pnl_micros: string | number;
}

export interface PnlHistoryQuery {
  from_?: WideInteger | null;
  to?: WideInteger | null;
}

export interface PnlEventResponse {
  source: string;
  resolved_at_ms: WideInteger;
  position_id?: string | null;
  contest_id?: string | null;
  pnl_micros: string | number;
  cumulative_micros: string | number;
}

export interface PnlHistoryResponse {
  events: PnlEventResponse[];
}

export interface PositionsQuery {
  status?: string | null;
  sort?: string | null;
  limit?: number | null;
  cursor?: string | null;
}

export const PositionStatusQueryParam = {
  Open: 'open',
  Won: 'won',
  Lost: 'lost',
  Voided: 'voided',
} as const;
export type PositionStatusQueryParam = (typeof PositionStatusQueryParam)[keyof typeof PositionStatusQueryParam];

export const PositionSortQueryParam = {
  DateDesc: 'date_desc',
  DateAsc: 'date_asc',
  PnlDesc: 'pnl_desc',
  PnlAsc: 'pnl_asc',
} as const;
export type PositionSortQueryParam = (typeof PositionSortQueryParam)[keyof typeof PositionSortQueryParam];

export interface PositionSummary {
  id: string;
  wager_micros: string | number;
  app_token_wager_micros?: string | number;
  refunded_app_token_micros: string | number | null;
  payout_micros: string | number;
  net_payout_micros: string | number | null;
  legs_count: number;
  legs_summary: string;
  status: string;
  pnl_micros: string | number | null;
  created_at_ms: WideInteger;
  resolved_at_ms?: WideInteger | null;
  has_binary_event_leg: boolean;
  market_types: MarketType[];
}

export interface PositionsListResponse {
  positions: PositionSummary[];
  next_cursor?: string | null;
  partial: boolean;
}

export const ActivePositionStatus = {
  Pending: 'pending',
  Open: 'open',
} as const;
export type ActivePositionStatus = (typeof ActivePositionStatus)[keyof typeof ActivePositionStatus];

export const PositionRole = {
  Taker: 'taker',
  Maker: 'maker',
} as const;
export type PositionRole = (typeof PositionRole)[keyof typeof PositionRole];

export interface ActivePosition {
  position_id: PositionId;
  status: ActivePositionStatus;
  role: PositionRole;
  taker_address?: Address | null;
  wager_micros: string | number;
  app_token_wager_micros?: string | number;
  payout_micros: string | number;
  legs: LegDetail[];
}

export interface ActivePositionsResponse {
  positions: ActivePosition[];
}

export interface LegDetail {
  leg_index: number;
  market_id: WideInteger;
  market_type?: MarketType | null;
  label?: string | null;
  asset?: string | null;
  direction: string;
  duration_secs?: number | null;
  outcome: string;
  window_start_ms?: WideInteger | null;
  resolution_time_ms: WideInteger;
}

export interface PositionDetailResponse {
  id: string;
  wager_micros: string | number;
  app_token_wager_micros?: string | number;
  refunded_app_token_micros: string | number | null;
  payout_micros: string | number;
  net_payout_micros: string | number | null;
  legs_count: number;
  legs_summary: string;
  status: string;
  pnl_micros: string | number | null;
  created_at_ms: WideInteger;
  resolved_at_ms?: WideInteger | null;
  legs: LegDetail[];
}

export interface PreferencesResponse {
  notifications_enabled: boolean;
  quote_tolerance: QuoteTolerancePreference;
  anonymous_mode_enabled: boolean;
}

export const QuoteTolerancePreference = {
  Strict: 'strict',
  Normal: 'normal',
  Lenient: 'lenient',
} as const;
export type QuoteTolerancePreference = (typeof QuoteTolerancePreference)[keyof typeof QuoteTolerancePreference];

export interface UpdatePreferencesRequest {
  notifications_enabled?: boolean | null;
  quote_tolerance?: QuoteTolerancePreference | null;
  anonymous_mode_enabled?: boolean | null;
}

export interface CheckHandleQuery {
  handle: string;
}

export interface ProfileResponse {
  handle: string;
  display_name: string;
  avatar_seed: number;
  email?: string | null;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  created_at_ms: WideInteger;
  updated_at_ms: WideInteger;
  referral_code?: string | null;
}

export interface UpdateProfileRequest {
  handle?: string | null;
  display_name?: string | null;
}

export interface CheckHandleResponse {
  available: boolean;
  reason?: string | null;
}

export interface WalletAuthRequest {
  address: string;
  signature: string;
  signed_at_ms: WideInteger;
  referral_code?: string | null;
}

export interface UserDepositRequest {
  amount_micros: WideInteger;
  idempotency_key: string;
}

export interface UserWithdrawParams {
  amount_micros: WideInteger;
  destination_address?: string | null;
  idempotency_key: string;
}

export type WithdrawalAuthorization =
  | { type: "privy_token"; token: string }
  | { type: "wallet_signature"; signature: string; signed_at_ms: WideInteger };

export interface UserWithdrawRequest {
  withdraw_params: UserWithdrawParams;
  authorization: WithdrawalAuthorization;
}

export function buildWalletAuthenticationMessage(
  domain: string,
  authAddress: Address | string,
  signedAtMs: WideInteger,
): string {
  const auth = Address.fromEvm(authAddress);
  return [
    "Longshot Wallet Authentication",
    "",
    "Version: 1",
    `Domain: ${domain}`,
    `Auth Address: ${auth.toChecksum()}`,
    `Timestamp: ${checkU64(signedAtMs, "signed_at_ms")}`,
  ].join("\n");
}

export function buildWalletWithdrawalAuthorizationMessage(
  domain: string,
  chainId: WideInteger,
  authAddress: Address | string,
  destinationAddress: Address | string,
  amountMicros: WideInteger,
  idempotencyKey: UuidId | string,
  signedAtMs: WideInteger,
): string {
  const auth = Address.fromEvm(authAddress);
  const destination = Address.fromEvm(destinationAddress);
  const canonicalIdempotencyKey =
    idempotencyKey instanceof UuidId
      ? idempotencyKey.toString()
      : UuidId.fromString(idempotencyKey.trim()).toString();

  return [
    "Longshot Withdrawal Authorization",
    "",
    "Version: 1",
    `Domain: ${domain}`,
    `Chain ID: ${checkU64(chainId, "chain_id")}`,
    `Auth Address: ${auth.toChecksum()}`,
    `Destination Address: ${destination.toChecksum()}`,
    `Amount Micros: ${checkU64(amountMicros, "amount_micros")}`,
    `Idempotency Key: ${canonicalIdempotencyKey}`,
    `Timestamp: ${checkU64(signedAtMs, "signed_at_ms")}`,
  ].join("\n");
}

export function encodeWalletSignature(signature: BytesLike): string {
  return encodeBase64(bytesFrom(signature, 65, "wallet signature"));
}

export interface OrderLegJson {
  market_id: WideInteger;
  direction: string;
}

export interface SignedOrderJson {
  user: string;
  wager_micros: number | string;
  min_odds: number;
  legs: OrderLegJson[];
  nonce: number | string;
  expires_at_ms: number | string;
  order_type?: number;
  shield_on: boolean;
  signature: string;
}

export type CommunityPickMode = 'tail' | 'fade';

export interface CommunityPickRequest {
  source_position_id: PositionId;
  mode: CommunityPickMode;
}

export interface CreateRfqRequest {
  order: SignedOrderJson;
  use_app_tokens: boolean;
}

export interface UnsignedRfqOrderRequest {
  wager_micros: WideInteger;
  min_odds: number;
  legs: OrderLegJson[];
  order_type?: number;
  shield_on: boolean;
  idempotency_key: string;
}

export interface CreateUnsignedRfqRequest {
  privy_token: string;
  use_app_tokens: boolean;
  rfq_params: UnsignedRfqOrderRequest;
  community_pick?: CommunityPickRequest | null;
}

export interface ParsedOrderLeg {
  market_id: MarketId;
  direction: Direction;
}

export type OrderLegParseError =
  | { type: 'InvalidMarketId'; [key: string]: unknown }
  | { type: 'InvalidDirection'; [key: string]: unknown };

export type RfqOrderJsonError =
  | { type: 'InvalidAddress'; [key: string]: unknown }
  | { type: 'InvalidMinOdds'; [key: string]: unknown }
  | { type: 'MissingLegs'; [key: string]: unknown }
  | { type: 'TooManyLegs'; [key: string]: unknown }
  | { type: 'InvalidOrderType'; [key: string]: unknown }
  | { type: 'InvalidSignatureFormat'; [key: string]: unknown }
  | { type: 'InvalidIdempotencyKey'; [key: string]: unknown }
  | { type: 'InvalidLegMarketId'; [key: string]: unknown }
  | { type: 'InvalidLegDirection'; [key: string]: unknown };

export interface AccessResponse {
  position_opening_allowed: boolean;
  reason_code?: string | null;
}

export interface SessionResponse {
  session_token: string;
  address: string;
  auth_wallet_address: string;
  deposit_address?: string | null;
  deposit_chain_id?: WideInteger | null;
  user_id: string;
  expires_at: WideInteger;
  account_created?: boolean;
}

export const RfqStatus = {
  Pending: 'pending',
  Finalizing: 'finalizing',
  Completed: 'completed',
  Failed: 'failed',
  Cancelled: 'cancelled',
  Timeout: 'timeout',
} as const;
export type RfqStatus = (typeof RfqStatus)[keyof typeof RfqStatus];

export interface RfqResponse {
  request_id: string;
  status: RfqStatus;
  odds?: number | null;
  payout_micros?: string | number | null;
  error?: string | null;
  quotes_received: number;
}

export interface CancelResponse {
  request_id: string;
  cancelled: boolean;
  message: string;
}

export interface UserDepositResponse {
  amount_micros: string | number;
  operation_id: string;
  tx_hash: string;
}

export interface UserDepositWalletResponse {
  address: string;
  chain_id: WideInteger;
  token_symbol: string;
  token_decimals: number;
}

export interface UserWithdrawResponse {
  amount_micros: string | number;
  operation_id: string;
  destination_address?: string | null;
  tx_hash: string;
  withdrawal_stage?: WithdrawalStage | null;
  available_at_ms?: WideInteger | null;
  submission_tx_hash?: string | null;
}

export const WithdrawalStage = {
  Processing: 'processing',
  Held: 'held',
  OnchainQueued: 'onchain_queued',
  Completed: 'completed',
  Failed: 'failed',
} as const;
export type WithdrawalStage = (typeof WithdrawalStage)[keyof typeof WithdrawalStage];

export const BalanceOperationStatus = {
  Pending: 'pending',
  Failed: 'failed',
  Success: 'success',
  Recovering: 'recovering',
} as const;
export type BalanceOperationStatus = (typeof BalanceOperationStatus)[keyof typeof BalanceOperationStatus];

export interface BalanceOperationStatusResponse {
  amount_micros: string | number;
  operation_id: string;
  status: BalanceOperationStatus;
  wallet_address?: string | null;
  withdrawal_stage?: WithdrawalStage | null;
  available_at_ms?: WideInteger | null;
  submission_tx_hash?: string | null;
  tx_hash?: string | null;
}

export type DepositOperationResponse = UserDepositResponse | BalanceOperationStatusResponse;

export type WithdrawOperationResponse = UserWithdrawResponse | BalanceOperationStatusResponse;

export interface ReservedBalanceResponse {
  reserved_micros: string | number;
}

export const UserTransactionCategory = {
  Deposit: 'deposit',
  Withdrawal: 'withdrawal',
  Credits: 'credits',
  Market: 'market',
  Contest: 'contest',
} as const;
export type UserTransactionCategory =
  (typeof UserTransactionCategory)[keyof typeof UserTransactionCategory];

export const UserTransactionStatus = {
  Completed: 'completed',
  Pending: 'pending',
  Failed: 'failed',
  Expired: 'expired',
  Entered: 'entered',
  Won: 'won',
} as const;
export type UserTransactionStatus =
  (typeof UserTransactionStatus)[keyof typeof UserTransactionStatus];

export const UserTransactionUnit = {
  Usdc: 'usdc',
  Credits: 'credits',
} as const;
export type UserTransactionUnit =
  (typeof UserTransactionUnit)[keyof typeof UserTransactionUnit];

export const UserTransactionFunding = {
  Cash: 'cash',
  Credits: 'credits',
  CashAndCredits: 'cash_and_credits',
} as const;
export type UserTransactionFunding =
  (typeof UserTransactionFunding)[keyof typeof UserTransactionFunding];

export interface UserTransactionResponse {
  id: string;
  category: UserTransactionCategory;
  title: string;
  detail?: string | null;
  status: UserTransactionStatus;
  occurred_at_ms: WideInteger;
  amount_micros: string | number;
  unit: UserTransactionUnit;
  funding?: UserTransactionFunding | null;
  network?: string | null;
  wallet_address?: string | null;
  tx_hash?: string | null;
  source?: string | null;
  expires_at_ms?: WideInteger | null;
  reason?: string | null;
  reference?: string | null;
  withdrawal_stage?: WithdrawalStage | null;
  available_at_ms?: WideInteger | null;
  submission_tx_hash?: string | null;
}

export interface UserTransactionsResponse {
  items: UserTransactionResponse[];
  next_cursor?: string | null;
}

export const FeeScheduleTier = {
  Standard: 'standard',
  Silver: 'silver',
  Gold: 'gold',
  Platinum: 'platinum',
  Vip: 'vip',
} as const;
export type FeeScheduleTier = (typeof FeeScheduleTier)[keyof typeof FeeScheduleTier];

export interface TierFeeRate {
  tier: FeeScheduleTier;
  parlay_fee_bps: number;
}

export interface FeeScheduleResponse {
  user_tier: FeeScheduleTier;
  parlay_fee_bps: number;
  spot_fee_bps: number;
  bonding_spot_fee_bps: number;
  shield_fee_multiplier: number;
  tiers: TierFeeRate[];
}

export interface ErrorResponse {
  error: string;
  code: string;
  details?: string | null;
}

export interface UserTransactionsRawQuery {
  category?: string | null;
  from_ms?: string | null;
  to_ms?: string | null;
  limit?: number | null;
  cursor?: string | null;
}

export interface ConfirmPositionQuery {
  position_id: string;
  accept: boolean;
}

export interface RfqEstimateRequest {
  wager_micros: WideInteger;
  legs: OrderLegJson[];
  shield_on?: boolean;
}

export interface RfqEstimateResponse {
  request_id: string;
  quotable: boolean;
  odds?: number | null;
  fillable_micros?: WideInteger | null;
  quotes_received: number;
  quoted_at_ms: WideInteger;
  reason?: string | null;
}

export interface MmRfqStatusResponse {
  request_id: string;
  status: RfqStatus;
}

export interface UserAvailableBalanceResponse {
  available_micros: string | number;
  pending_custodial_deposit_micros: string | number;
  credited_custodial_deposit_micros: string | number;
  deposit_withdrawal_min_micros: string | number;
  withdrawal_max_micros: string | number;
}

export const WithdrawalDeliveryStatus = {
  Queued: 'queued',
} as const;
export type WithdrawalDeliveryStatus = (typeof WithdrawalDeliveryStatus)[keyof typeof WithdrawalDeliveryStatus];

export interface QueuedWithdrawalResponse {
  amount_micros: string | number;
  operation_id: string;
  destination_address?: string | null;
  delivery_status: WithdrawalDeliveryStatus;
  withdrawal_stage: WithdrawalStage;
  available_at_ms: WideInteger;
  submission_tx_hash: string;
}

export interface ActiveWithdrawalResponse {
  operation_id: string;
  amount_micros: string | number;
  destination_address?: string | null;
  withdrawal_stage: WithdrawalStage;
  created_at_ms: WideInteger;
  available_at_ms?: WideInteger | null;
  submission_tx_hash?: string | null;
}

export interface UserWithdrawalStateResponse {
  withdrawals_available: boolean;
  hold_trigger_amount_micros: string | number;
  hold_threshold_micros: string | number;
  hold_window_ms: WideInteger;
  hold_duration_ms: WideInteger;
  active_withdrawals: ActiveWithdrawalResponse[];
}

export type AcceptedWithdrawOperationResponse = QueuedWithdrawalResponse | BalanceOperationStatusResponse;

export const PublicReferralStatusResponse = {
  Valid: 'valid',
  Redeemed: 'redeemed',
  Expired: 'expired',
} as const;
export type PublicReferralStatusResponse = (typeof PublicReferralStatusResponse)[keyof typeof PublicReferralStatusResponse];

export interface PublicReferralInviterResponse {
  display_name: string;
  avatar_seed: number;
  avatar_url?: string | null;
}

export interface PublicReferralDepositMatchOffer {
  match_limit_micros: string | number;
  duration_ms: WideInteger;
}

export interface PublicReferralCodeResponse {
  status: PublicReferralStatusResponse;
  inviter?: PublicReferralInviterResponse | null;
  deposit_match?: PublicReferralDepositMatchOffer | null;
}

export interface PnlHistoryScopedQuery {
  from_?: WideInteger | null;
  to?: WideInteger | null;
  scope?: string | null;
}

export interface PositionsByMarketsQuery {
  market_ids: string;
  limit?: number | null;
  cursor?: string | null;
}

export interface PositionsByMarketsResponse {
  positions: PositionDetailResponse[];
  next_cursor?: string | null;
}

export interface HandleAvailabilityQuery {
  handle: string;
}

export function pnlHistoryScopedQueryToWire(
  query: PnlHistoryScopedQuery,
): Record<string, unknown> {
  const { from_, ...rest } = query as PnlHistoryScopedQuery & Record<string, unknown>;
  return from_ === undefined ? rest : { ...rest, from: from_ };
}

export function orderLegJsonFromOrderLeg(leg: OrderLeg): OrderLegJson {
  const raw = leg.serdeValue();
  return { market_id: raw.market_id, direction: raw.direction === Direction.Up ? "up" : "down" };
}

export function parseOrderLegJson(leg: OrderLegJson): ParsedOrderLeg {
  const marketId = MarketId.new(leg.market_id);
  if (marketId.asU64() === 0n) {
    throw new Error("invalid market id");
  }
  const direction = parseOrderLegDirection(leg.direction);
  return { market_id: marketId, direction };
}

export function signedOrderJsonFromSignedOrder(order: SignedOrder): SignedOrderJson {
  return order.serdeValue();
}

export function signedOrderJsonToSignedOrder(order: SignedOrderJson): SignedOrder {
  return signedOrderFromJsonFields({
    user: Address.fromHex(order.user),
    wagerMicros: order.wager_micros,
    minOddsDecimal: order.min_odds,
    legs: order.legs,
    nonce: order.nonce,
    expiresAtMs: order.expires_at_ms,
    orderType: order.order_type,
    shieldOn: order.shield_on,
    signature: decodeSignature(order.signature),
  });
}

export function createRfqRequestFromSignedOrder(
  order: SignedOrder,
  useAppTokens: boolean,
): CreateRfqRequest {
  if (typeof useAppTokens !== "boolean") {
    throw new SignedOrderError("use_app_tokens must be bool");
  }
  return {
    order: signedOrderJsonFromSignedOrder(order),
    use_app_tokens: useAppTokens,
  };
}

export function parseUnsignedRfqIdempotencyKey(request: UnsignedRfqOrderRequest): UuidId {
  return UuidId.fromString(request.idempotency_key.trim());
}

function signedOrderFromJsonFields(fields: {
  user: Address;
  wagerMicros: number | bigint | string;
  minOddsDecimal: number;
  legs: OrderLegJson[];
  nonce: number | bigint | string;
  expiresAtMs: number | bigint | string;
  orderType?: number | null;
  shieldOn: boolean;
  signature: Uint8Array;
}): SignedOrder {
  if (typeof fields.shieldOn !== "boolean") {
    throw new SignedOrderError("shield_on must be bool");
  }
  if (fields.legs.length === 0) {
    throw new Error("order must include at least one leg");
  }
  if (fields.legs.length > SignedOrder.MAX_LEGS) {
    throw new Error("too many legs");
  }
  return new SignedOrder({
    user: fields.user,
    wagerMicros: fields.wagerMicros,
    minOddsBps: parseMinOddsBps(fields.minOddsDecimal),
    legs: fields.legs.map((leg) => {
      const parsed = parseOrderLegJson(leg);
      if (parsed.market_id == null || parsed.direction == null) {
        throw new Error("invalid order leg");
      }
      return new OrderLeg({
        marketId: parsed.market_id,
        direction: directionToWire(parsed.direction),
      });
    }),
    nonce: fields.nonce,
    expiresAtMs: fields.expiresAtMs,
    orderType: parseOrderType(fields.orderType),
    shieldOn: fields.shieldOn,
    signature: fields.signature,
  });
}

function parseMinOddsBps(minOddsDecimal: number): number {
  if (!Number.isFinite(minOddsDecimal)) {
    throw new Error("invalid min odds");
  }
  // HTTP decimal odds are positive, so Math.round matches Rust's half-away-from-zero rule.
  const minOddsBps = Math.round(minOddsDecimal * 10_000);
  if (minOddsBps <= Odds.EVEN.value || minOddsBps > Odds.MAX.value) {
    throw new Error("invalid min odds");
  }
  return minOddsBps;
}

function parseOrderLegDirection(direction: string): Direction {
  const normalized = direction.toLowerCase();
  if (normalized === "up") return Direction.Up;
  if (normalized === "down") return Direction.Down;
  throw new Error("invalid direction");
}

function directionToWire(direction: Direction): number {
  return direction === Direction.Up ? 0 : 1;
}

function parseOrderType(orderType: number | null | undefined): OrderType {
  // Rust defaults only an omitted field; explicit JSON null is invalid for this u8 contract.
  if (orderType === null) {
    throw new Error("invalid order type");
  }
  const parsed = OrderType.fromU8(orderType === undefined ? OrderType.FOK : orderType);
  if (parsed === undefined) {
    throw new Error("invalid order type");
  }
  return parsed;
}

function decodeSignature(signature: string): Uint8Array {
  const decoded = decodeBase64(signature);
  if (decoded.length !== 65) {
    throw new Error("invalid signature format");
  }
  return decoded;
}
