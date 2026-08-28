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

export const NOTIFICATION_LIST_DEFAULT_LIMIT = 30 as const;
export const NOTIFICATION_LIST_MAX_LIMIT = 100 as const;
export const NOTIFICATION_STREAM_BATCH_LIMIT = 50 as const;
export const MAX_CHART_POINTS = 512 as const;
export const MAX_MARKET_WINDOWS = 9 as const;
export const MAX_MARKET_WINDOW_PICKS = 3 as const;
export const MAX_TZ_OFFSET_MINUTES = 840 as const;
export const MAX_QUESTION_LEGS = 32 as const;
export const MAX_SUMMARY_STATS = 4 as const;
export const MAX_ROSTER_SHARE_PICKS = 10 as const;
export const MAX_EVENT_POSITION_SHARE_PICKS = 9 as const;
export const MAX_SURVIVOR_SHARE_PICKS = 64 as const;
export const MAX_SURVIVOR_SHARE_ROUNDS = 30 as const;
export const MAX_TEXT_LEN = 200 as const;

export type ChatUserAvatarResponse =
  | { type: 'x_avatar_url'; url: string }
  | { type: 'seed'; seed: number };

export interface ChatAuthorResponse {
  user_id: string;
  name: string;
  avatar: ChatUserAvatarResponse;
}

export interface ChatReactionResponse {
  emoji_code: string;
  reactor: ChatAuthorResponse;
}

export type ChatEmojiDisplayResponse =
  | { type: 'url'; value: string }
  | { type: 'unicode'; value: string };

export interface ChatEmojiResponse {
  code: string;
  display: ChatEmojiDisplayResponse;
}

export interface ChatEmojisResponse {
  emojis: ChatEmojiResponse[];
}

export interface ChatReactionUpdateResponse {
  message_id: string;
  reaction_seq: WideInteger;
  reactions: ChatReactionResponse[];
}

export const ChatGifProviderResponse = {
  Giphy: 'giphy',
} as const;
export type ChatGifProviderResponse = (typeof ChatGifProviderResponse)[keyof typeof ChatGifProviderResponse];

export interface ChatGifAttachmentResponse {
  provider: ChatGifProviderResponse;
  id: string;
}

export interface ChatMessageResponse {
  message_id: string;
  author: ChatAuthorResponse;
  body: string;
  gif?: ChatGifAttachmentResponse | null;
  parent?: string | null;
  reactions: ChatReactionResponse[];
  edit_seq: WideInteger;
  reaction_seq: WideInteger;
  timestamp_ms: WideInteger;
}

export interface ChatMessageEditResponse {
  message_id: string;
  body: string;
  edit_seq: WideInteger;
  timestamp_ms: WideInteger;
}

export interface ChatRecentMessagesResponse {
  messages: ChatMessageResponse[];
  next_cursor?: string | null;
  writable: boolean;
}

export const ChatStreamErrorCode = {
  SubscriberLagged: 'subscriber_lagged',
} as const;
export type ChatStreamErrorCode = (typeof ChatStreamErrorCode)[keyof typeof ChatStreamErrorCode];

export interface ChatStreamErrorEvent {
  code: ChatStreamErrorCode;
  message: string;
  skipped: WideInteger;
}

export interface ListContestsQuery {
  status?: string | null;
  category?: string | null;
  cursor?: string | null;
  limit?: number | null;
}

export interface ContestDetailQuery {
  survivor_round_limit?: number | null;
  survivor_round_before?: number | null;
}

export interface ContestLeaderboardQuery {
  cursor?: string | null;
  limit?: number | null;
  survivor_round_limit?: number | null;
  survivor_round_before?: number | null;
}

export interface ContestTopParticipantsQuery {
  window_ms?: string | null;
  limit?: number | null;
}

export const FeedFilter = {
  All: 'All',
  Resolved: 'Resolved',
  Golden: 'Golden',
  Won: 'Won',
} as const;
export type FeedFilter = (typeof FeedFilter)[keyof typeof FeedFilter];

export interface FeedRawQuery {
  filter?: string | null;
  limit?: number | null;
  cursor?: string | null;
  binary_event_market_ids?: string | null;
}

export interface FeedEventResponse {
  event_type: string;
  position_id: string;
  market: string;
  duration_label?: string | null;
  primary_leg?: PrimaryLegIdentityResponse | null;
  legs_count: number;
  user_display_name: string;
  user_handle?: string | null;
  user_avatar_seed: number;
  user_avatar_url?: string | null;
  wager_micros: string | number;
  multiplier_bps: WideInteger;
  payout_micros: string | number;
  event_at_ms: WideInteger;
}

export interface FeedResponse {
  events: FeedEventResponse[];
  next_cursor?: string | null;
}

export const LeaderboardWindow = {
  Day: 'day',
  Week: 'week',
  Month: 'month',
  AllTime: 'all_time',
} as const;
export type LeaderboardWindow = (typeof LeaderboardWindow)[keyof typeof LeaderboardWindow];

export interface LeaderboardRawQuery {
  period?: string | null;
  scope?: string | null;
  metric?: string | null;
  limit?: number | null;
}

export interface LeaderboardMeRawQuery {
  metric?: string | null;
  window?: string | null;
  asset?: string | null;
}

export interface HighlightsRawQuery {
  sort?: string | null;
  window?: string | null;
  limit?: number | null;
}

export const LeaderboardMetricResponse = {
  Pnl: 'pnl',
  Volume: 'volume',
  Roi: 'roi',
  Wins: 'wins',
} as const;
export type LeaderboardMetricResponse = (typeof LeaderboardMetricResponse)[keyof typeof LeaderboardMetricResponse];

export const HighlightSortResponse = {
  Payout: 'payout',
  Multiplier: 'multiplier',
} as const;
export type HighlightSortResponse = (typeof HighlightSortResponse)[keyof typeof HighlightSortResponse];

export const LeaderboardPeriod = {
  Daily: 'daily',
  Weekly: 'weekly',
  Monthly: 'monthly',
  AllTime: 'all_time',
} as const;
export type LeaderboardPeriod = (typeof LeaderboardPeriod)[keyof typeof LeaderboardPeriod];

export const LeaderboardScope = {
  All: 'all',
  Markets: 'markets',
  Contests: 'contests',
} as const;
export type LeaderboardScope = (typeof LeaderboardScope)[keyof typeof LeaderboardScope];

export const LeaderboardMetric = {
  Pnl: 'pnl',
  Combo: 'combo',
} as const;
export type LeaderboardMetric = (typeof LeaderboardMetric)[keyof typeof LeaderboardMetric];

export interface LeaderboardPnlEntry {
  rank: number;
  handle?: string | null;
  display_name?: string | null;
  avatar_seed?: number | null;
  x_avatar_url?: string | null;
  entry_count: WideInteger;
  pnl_micros: string | number;
}

export interface LeaderboardComboEntry {
  rank: number;
  handle?: string | null;
  display_name?: string | null;
  avatar_seed?: number | null;
  x_avatar_url?: string | null;
  combo_legs: WideInteger;
  multiplier_bps: WideInteger;
}

export type LeaderboardEntry = LeaderboardPnlEntry | LeaderboardComboEntry;

export interface LeaderboardPnlCaller {
  rank: number;
  entry_count: WideInteger;
  pnl_micros: string | number;
}

export interface LeaderboardComboCaller {
  rank: number;
  combo_legs: WideInteger;
  multiplier_bps: WideInteger;
}

export type LeaderboardCaller = LeaderboardPnlCaller | LeaderboardComboCaller;

export interface LegacyLeaderboardEntry {
  rank: number;
  user_id: string;
  handle?: string | null;
  display_name?: string | null;
  avatar_seed?: number | null;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  created_at_ms: WideInteger;
  metric_value: string | number;
  total_positions: WideInteger;
  wins: WideInteger;
  losses: WideInteger;
  biggest_win_micros: string | number;
  highest_multiplier_bps: WideInteger;
}

export interface LeaderboardResponse {
  period: LeaderboardPeriod;
  scope: LeaderboardScope;
  metric: LeaderboardMetric;
  period_start_ms: WideInteger;
  period_end_ms: WideInteger;
  entries: LeaderboardEntry[];
  caller?: LeaderboardCaller | null;
}

export interface LeaderboardMyRankResponse {
  entry?: LegacyLeaderboardEntry | null;
}

export interface HighlightEntry {
  position_id: string;
  user_id: string;
  display_name?: string | null;
  avatar_seed?: number | null;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  market: string;
  duration_label?: string | null;
  primary_leg?: PrimaryLegIdentityResponse | null;
  legs_count: number;
  wager_micros: string | number;
  payout_micros: string | number;
  multiplier_bps: WideInteger;
}

export interface LeaderboardHighlightsResponse {
  sort: HighlightSortResponse;
  window: LeaderboardWindow;
  highlights: HighlightEntry[];
}

export const PriceSourceResponse = {
  Binance: 'binance',
  Polymarket: 'polymarket',
} as const;
export type PriceSourceResponse = (typeof PriceSourceResponse)[keyof typeof PriceSourceResponse];

export interface MarketCandlesQuery {
  asset?: string | null;
  timeframe_secs?: WideInteger | null;
  past_slots?: WideInteger | null;
  now_ms?: WideInteger | null;
  before_ms?: WideInteger | null;
  max_points?: WideInteger | null;
  ohlc_resolution_secs?: WideInteger | null;
}

export interface MarketTicksStreamQuery {
  assets?: string | null;
  timeframe_secs?: WideInteger | null;
  since_ms?: WideInteger | null;
  since_seq?: WideInteger | null;
}

export interface ExternalOddsSourceQuery {
  assets?: string | null;
  timeframe_secs?: WideInteger | null;
  window_start_ms?: string | null;
  market_ids?: string | null;
}

export interface ChartPoint {
  timestamp_ms: WideInteger;
  price: number;
}

export interface OhlcCandle {
  time_ms: WideInteger;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MarketTickStreamEvent {
  asset: string;
  price_source: PriceSourceResponse;
  timestamp_ms: WideInteger;
  price: number;
  source_trade_id: WideInteger;
  seq: WideInteger;
  slot_start_ms: WideInteger;
  sample_interval_ms: WideInteger;
  is_synthetic: boolean;
  emitted_at_ms: WideInteger;
}

export const MarketTickStreamErrorCode = {
  PublisherSeedCursorFailed: 'publisher_seed_cursor_failed',
  PublisherIncrementalQueryFailed: 'publisher_incremental_query_failed',
  PublisherFallbackQueryFailed: 'publisher_fallback_query_failed',
} as const;
export type MarketTickStreamErrorCode = (typeof MarketTickStreamErrorCode)[keyof typeof MarketTickStreamErrorCode];

export interface MarketTickStreamErrorEvent {
  asset: string;
  price_source: PriceSourceResponse;
  code: MarketTickStreamErrorCode;
  retry_after_ms: WideInteger;
  emitted_at_ms: WideInteger;
}

export interface TopOfBookStreamQuery {
  assets?: string | null;
  timeframe_secs?: WideInteger | null;
  window_start_ms?: string | null;
  market_ids?: string | null;
  since_seq?: WideInteger | null;
}

export const ExternalOddsSourceStatus = {
  Ok: 'ok',
  Partial: 'partial',
  Pending: 'pending',
  EmptyBook: 'empty_book',
  MissingBinding: 'missing_tokens',
  UpstreamError: 'upstream_error',
} as const;
export type ExternalOddsSourceStatus = (typeof ExternalOddsSourceStatus)[keyof typeof ExternalOddsSourceStatus];

export const ExternalOddsSourceKind = {
  PolymarketWs: 'clob_ws',
  KalshiRest: 'kalshi_rest',
  ManifoldRest: 'manifold_rest',
  Cache: 'cache',
  None_: 'none',
} as const;
export type ExternalOddsSourceKind = (typeof ExternalOddsSourceKind)[keyof typeof ExternalOddsSourceKind];

export interface ExternalOddsSourceRow {
  key: string;
  asset?: string | null;
  timeframe_secs?: WideInteger | null;
  window_start_ms?: WideInteger | null;
  window_end_ms?: WideInteger | null;
  market_id?: WideInteger | null;
  source_market_id?: string | null;
  yes_ask_cents?: number | null;
  no_ask_cents?: number | null;
  status: ExternalOddsSourceStatus;
  updated_at_ms: WideInteger;
  source: ExternalOddsSourceKind;
}

export interface ExternalOddsSourceResponse {
  rows: ExternalOddsSourceRow[];
}

export interface TopOfBookStreamEvent {
  key: string;
  asset?: string | null;
  timeframe_secs?: WideInteger | null;
  window_start_ms?: WideInteger | null;
  window_end_ms?: WideInteger | null;
  market_id?: WideInteger | null;
  source_market_id?: string | null;
  yes_ask_cents?: number | null;
  no_ask_cents?: number | null;
  status: ExternalOddsSourceStatus;
  source: ExternalOddsSourceKind;
  updated_at_ms: WideInteger;
  seq: WideInteger;
  emitted_at_ms: WideInteger;
}

export const TopOfBookStreamErrorCode = {
  SubscriberDisconnected: 'subscriber_disconnected',
} as const;
export type TopOfBookStreamErrorCode = (typeof TopOfBookStreamErrorCode)[keyof typeof TopOfBookStreamErrorCode];

export interface TopOfBookStreamErrorEvent {
  code: TopOfBookStreamErrorCode;
  retry_after_ms: WideInteger;
  emitted_at_ms: WideInteger;
}

export interface TopOfBookHistoryQuery {
  market_ids: string;
}

export interface TopOfBookHistoryPoint {
  timestamp_ms: WideInteger;
  yes_ask_cents?: number | null;
  no_ask_cents?: number | null;
}

export const TopOfBookHistoryStatus = {
  Ok: 'ok',
  Unsupported: 'unsupported',
  UpstreamError: 'upstream_error',
} as const;
export type TopOfBookHistoryStatus = (typeof TopOfBookHistoryStatus)[keyof typeof TopOfBookHistoryStatus];

export interface TopOfBookHistoryMarket {
  market_id: WideInteger;
  source_market_id?: string | null;
  status: TopOfBookHistoryStatus;
  points: TopOfBookHistoryPoint[];
}

export interface TopOfBookHistoryResponse {
  bucket_secs: WideInteger;
  window_start_ms: WideInteger;
  generated_at_ms: WideInteger;
  markets: TopOfBookHistoryMarket[];
}

export interface MarketCandlesResponse {
  asset: string;
  timeframe_secs: WideInteger;
  past_slots: WideInteger;
  requested_before_ms?: WideInteger | null;
  next_before_ms?: WideInteger | null;
  has_more_before: boolean;
  store_ready: boolean;
  timescale_enabled: boolean;
  cagg_enabled: boolean;
  source: string;
  price_source: PriceSourceResponse;
  generated_at_ms: WideInteger;
  slot_ms: WideInteger;
  candle_bucket_ms: WideInteger;
  current_slot_start_ms: WideInteger;
  current_slot_end_ms: WideInteger;
  domain_start_ms: WideInteger;
  domain_end_ms: WideInteger;
  latest_price?: number | null;
  latest_price_timestamp_ms?: WideInteger | null;
  candle_count: WideInteger;
  points: ChartPoint[];
  ohlc: OhlcCandle[];
}

export interface ReferencePriceQuery {
  asset?: string | null;
  timeframe_secs?: WideInteger | null;
}

export const SourceStatus = {
  Ok: 'ok',
  Pending: 'pending',
  Unavailable: 'unavailable',
} as const;
export type SourceStatus = (typeof SourceStatus)[keyof typeof SourceStatus];

export interface ReferencePriceResponse {
  asset: string;
  timeframe_secs: WideInteger;
  current_slot_start_ms: WideInteger;
  window_open_price?: number | null;
  source_status: SourceStatus;
}

export interface WindowResultsQuery {
  timeframe_secs?: WideInteger | null;
  past_windows?: WideInteger | null;
}

export const WindowDirection = {
  Up: 'up',
  Down: 'down',
} as const;
export type WindowDirection = (typeof WindowDirection)[keyof typeof WindowDirection];

export interface WindowAssetResult {
  asset: string;
  open_price: number;
  close_price: number;
  direction: WindowDirection;
  price_source: PriceSourceResponse;
}

export interface WindowResult {
  slot_start_ms: WideInteger;
  slot_end_ms: WideInteger;
  assets: WindowAssetResult[];
}

export interface WindowResultsResponse {
  timeframe_secs: WideInteger;
  past_windows: WideInteger;
  price_source: PriceSourceResponse;
  generated_at_ms: WideInteger;
  windows: WindowResult[];
}

export interface PublicMarketsRawQuery {
  market_type?: MarketType | null;
  source?: string | null;
  source_event_id?: string | null;
  include_featured?: boolean | null;
  featured_only?: boolean | null;
  trading_channel?: TradingChannel | null;
  limit?: number | null;
  cursor?: string | null;
  /** Market statuses sent as one comma-separated query value. */
  statuses?: MarketStatus[] | null;
}

export function publicMarketsRawQueryToWire(query: PublicMarketsRawQuery): Record<string, unknown> {
  return { ...query, statuses: query.statuses?.join(",") };
}

export interface EventMarketSource {
  source: string;
  event_id?: string | null;
  source_market_ids: string[];
  attributes?: Record<string, unknown>;
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
  /** Stable chat room for the source event shared by every market in that event. */
  chat_id: string;
  name: string;
  description?: string | null;
  resolution_rules?: string;
  status: MarketStatus;
  tradeable: boolean;
  /** Explicit Home placement shared by this source event: 1 is left, 2 is right. */
  featured_slot?: number | null;
  category_tags: string[];
  opens_at_ms?: WideInteger | null;
  /** Provider event start, distinct from Longshot's lifecycle `opens_at_ms`. */
  source_starts_at_ms?: WideInteger | null;
  betting_closes_at_ms: WideInteger;
  resolution_time_ms: WideInteger;
  live_ends_at_ms?: WideInteger | null;
  resolved_outcome?: Outcome | null;
  created_at_ms: WideInteger;
  opened_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  source: EventMarketSource;
  manual_probability_bps?: number | null;
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

export interface NotificationsRawQuery {
  filter?: string | null;
  limit?: number | null;
  cursor?: string | null;
}

export interface NotificationStreamRawQuery {
  after?: string | null;
}

export type NotificationPayload =
  | ({type: 'binary_event_start_soon'} & BinaryEventStartSoonNotificationPayload)
  | ({type: 'fantasy_start_soon'} & FantasyStartSoonNotificationPayload)
  | ({type: 'streak_start_soon'} & StreakStartSoonNotificationPayload)
  | ({type: 'streak_expiring'} & StreakExpiringNotificationPayload)
  | ({type: 'binary_event_win'} & BinaryEventWinNotificationPayload)
  | ({type: 'price_strike_parlay_win'} & PriceStrikeParlayWinNotificationPayload)
  | ({type: 'rfq_result'} & RfqResultNotificationPayload)
  | ({type: 'fantasy_result'} & FantasyResultNotificationPayload)
  | ({type: 'perfect_slate'} & PerfectSlateNotificationPayload)
  | ({type: 'streak_win'} & StreakWinNotificationPayload)
  | ({type: 'streak_settled'} & StreakSettledNotificationPayload)
  | ({type: 'payout_review'} & PayoutReviewNotificationPayload)
  | ({type: 'credits_granted'} & CreditsGrantedNotificationPayload)
  | ({type: 'chat_mention'} & ChatMentionNotificationPayload)
  | ({type: 'unknown'} & UnknownNotificationPayload);

export interface BinaryEventStartSoonNotificationPayload {
  source: string;
  event_id: string;
  market_title: string;
  starts_at_ms: WideInteger;
}

export interface FantasyStartSoonNotificationPayload {
  pool_image_scope_id?: string | null;
  contest_id?: string | null;
  entry_index?: number | null;
  contest_title: string;
  starts_at_ms: WideInteger;
  selection_count: number;
}

export interface StreakStartSoonNotificationPayload {
  pool_image_scope_id?: string | null;
  contest_title: string;
  market_title: string;
  starts_at_ms: WideInteger;
}

export interface StreakExpiringNotificationPayload {
  contest_id: string;
  contest_title: string;
  entry_index: number;
  win_streak: number;
  expires_at_ms: WideInteger;
}

export interface NflFeaturedMatchup {
  game_id: string;
}

export interface NflParlayLeg {
  market_id: WideInteger;
  direction: string;
}

export interface NflFeaturedParlay {
  title: string;
  copy?: string | null;
  legs: NflParlayLeg[];
}

export interface NflHubConfigBody {
  featured_matchups?: NflFeaturedMatchup[];
  featured_parlay?: NflFeaturedParlay | null;
  props_enabled: boolean;
}

export interface NflHubConfigResponse {
  config: NflHubConfigBody;
}

export interface BinaryEventWinNotificationPayload {
  position_id: string;
  source?: string | null;
  event_id?: string | null;
  net_payout_micros: WideInteger;
  multiplier_bps: WideInteger;
  market_title: string;
  /** Longshot market ids for every leg, so clients can resolve identity (e.g. NFL). Empty/absent on legacy rows. */
  market_ids?: WideInteger[];
}

export interface PriceStrikeParlayWinNotificationPayload {
  position_id: string;
  net_payout_micros: WideInteger;
  multiplier_bps: WideInteger;
  leg_summary: string;
  is_multi_asset: boolean;
  duration_secs: number[];
}

export interface RfqResultNotificationPayload {
  request_id: string;
  status: RfqResultNotificationStatus;
  final_wager_micros?: WideInteger | null;
  payout_micros?: WideInteger | null;
  odds?: number | null;
}

export const RfqResultNotificationStatus = {
  Completed: 'completed',
  Failed: 'failed',
  Cancelled: 'cancelled',
  Timeout: 'timeout',
} as const;
export type RfqResultNotificationStatus = (typeof RfqResultNotificationStatus)[keyof typeof RfqResultNotificationStatus];

export interface FantasyResultNotificationPayload {
  pool_image_scope_id?: string | null;
  contest_id: string;
  game_index: number;
  game_type: FantasyResultGameType;
  contest_title: string;
  contest_terminal: boolean;
  contest_refunded: boolean;
  entry_count: number;
  successful_entry_count: number;
  held_entry_count: number;
  credited_payout_micros: WideInteger;
  held_payout_micros: WideInteger;
  best_entry?: FantasyResultBestEntry | null;
  tiebreaker_result?: WideInteger | null;
}

export const FantasyResultGameType = {
  Lineups: 'lineups',
  Survivor: 'survivor',
  Outcast: 'outcast',
  Roster: 'roster',
} as const;
export type FantasyResultGameType = (typeof FantasyResultGameType)[keyof typeof FantasyResultGameType];

export interface FantasyResultBestEntry {
  entry_index: number;
  rank: number;
  correct_count?: number | null;
  selection_count?: number | null;
}

export interface PerfectSlateNotificationPayload {
  contest_id: string;
  game_index: number;
  contest_title: string;
  winning_entry_count: number;
  entry_indexes: number[];
  payout_micros: WideInteger;
  held_entry_count: number;
  pool_micros?: WideInteger | null;
  total_winning_entry_count?: number | null;
}

export interface StreakWinNotificationPayload {
  pool_image_scope_id?: string | null;
  contest_id?: string | null;
  game_index?: WideInteger | null;
  contest_title: string;
  market_title?: string | null;
  win_streak: number;
  payout_micros: WideInteger;
  app_token_micros?: WideInteger | null;
  is_app_token?: boolean | null;
  outcome: StreakWinOutcome;
}

export const StreakWinOutcome = {
  Win: 'win',
  WinAndReset: 'win_and_reset',
} as const;
export type StreakWinOutcome = (typeof StreakWinOutcome)[keyof typeof StreakWinOutcome];

export interface StreakSettledNotificationPayload {
  pool_image_scope_id?: string | null;
  contest_title: string;
  market_title?: string | null;
  win_streak: number;
  outcome: StreakSettledOutcome;
}

export const StreakSettledOutcome = {
  Loss: 'loss',
} as const;
export type StreakSettledOutcome = (typeof StreakSettledOutcome)[keyof typeof StreakSettledOutcome];

export interface PayoutReviewNotificationPayload {
  pool_image_scope_id?: string | null;
  contest_id?: string | null;
  entry_index?: number | null;
  contest_title: string;
  payout_micros: WideInteger;
  app_token_micros?: WideInteger | null;
  is_app_token?: boolean | null;
  status: PayoutReviewNotificationStatus;
}

export interface CreditsGrantedNotificationPayload {
  grant_id: string;
  amount_micros: WideInteger;
  contest_id?: string | null;
  game_index?: WideInteger | null;
}

export interface ChatMentionNotificationPayload {
  chat_id: string;
  message_id: string;
  /** @deprecated Use chat_id. */
  chat_context?: ChatMentionContext | null;
  /** @deprecated Use chat_id. */
  contest_id?: string | null;
}

/** @deprecated Use chat_id and a generic chat route. */
export const ChatMentionContext = {
  Contest: 'contest',
  CryptoMarket: 'crypto_market',
} as const;
export type ChatMentionContext = (typeof ChatMentionContext)[keyof typeof ChatMentionContext];

export const PayoutReviewNotificationStatus = {
  Pending: 'pending',
  Approved: 'approved',
  Rejected: 'rejected',
} as const;
export type PayoutReviewNotificationStatus = (typeof PayoutReviewNotificationStatus)[keyof typeof PayoutReviewNotificationStatus];

export interface UnknownNotificationPayload {
}

export interface NotificationResponse {
  seq: WideInteger;
  id: string;
  type: string;
  category: string;
  title: string;
  body: string;
  icon: string;
  payload: NotificationPayload;
  created_at_ms: WideInteger;
  read_at_ms?: WideInteger | null;
  image_url?: string | null;
}

export interface NotificationsResponse {
  notifications: NotificationResponse[];
  next_cursor?: string | null;
  unread_count: WideInteger;
}

export interface NotificationMutationResponse {
  notification: NotificationResponse;
  unread_count: WideInteger;
}

export interface NotificationBulkMutationResponse {
  updated_count: WideInteger;
  unread_count: WideInteger;
}

export type PoolImageRawBytes = Uint8Array;

export interface PortfolioIntegrityErrorResponse {
  position_id: string;
  leg_index?: number | null;
  code: string;
  message: string;
}

export interface PortfolioStatsResponse {
  total_positions: number;
  open_positions: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  total_pnl_micros: string | number;
}

export const PnlHistoryQueryParseError = {
  InvalidWindowRange: 'InvalidWindowRange',
} as const;
export type PnlHistoryQueryParseError = (typeof PnlHistoryQueryParseError)[keyof typeof PnlHistoryQueryParseError];

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

export interface FantasyEntriesQuery {
  limit?: number | null;
  cursor?: string | null;
}

export interface PortfolioFantasyEntryResponse {
  contest_id: string;
  title: string;
  category: string;
  status: string;
  game_type: ContestGameTypeResponse;
  survivor_round_count?: number | null;
  current_game_index?: number | null;
  bet_amount_micros: string | number;
  protocol_prize_pool_micros: string | number;
  total_pot_micros: string | number;
  entries_filled: WideInteger;
  entry_cap: number;
  entry_opens_at_ms?: WideInteger | null;
  betting_closes_ms: WideInteger;
  live_ends_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  joined_at_ms: WideInteger;
  entry_index: number;
  open_leg_count: number;
  resolved_win_count: number;
  rank?: number | null;
  payout_micros: string | number | null;
  net_payout_micros: string | number | null;
  refunded?: boolean;
  pnl_micros: string | number | null;
  image_url?: string | null;
  survivor?: SurvivorEntryStateResponse | null;
  selection_count: number;
  survivor_voided_round_count?: number | null;
  betting_opens_ms?: WideInteger | null;
}

export interface PortfolioFantasyEntriesResponse {
  entries: PortfolioFantasyEntryResponse[];
  next_cursor?: string | null;
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

export const CursorParseError = {
  InvalidFormat: 'InvalidFormat',
  InvalidValue: 'InvalidValue',
  ValueOutOfRange: 'ValueOutOfRange',
  InvalidPositionId: 'InvalidPositionId',
} as const;
export type CursorParseError = (typeof CursorParseError)[keyof typeof CursorParseError];

export const PositionQueryParseError = {
  InvalidStatus: 'InvalidStatus',
  InvalidSort: 'InvalidSort',
} as const;
export type PositionQueryParseError = (typeof PositionQueryParseError)[keyof typeof PositionQueryParseError];

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
  errors?: PortfolioIntegrityErrorResponse[];
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

export interface PrimaryLegIdentityResponse {
  market_type: MarketType;
  market_id: WideInteger;
  label: string;
  asset?: string | null;
  duration_secs?: number | null;
  duration_label?: string | null;
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

export interface PublicProfileResponse {
  handle: string;
  display_name: string;
  avatar_seed: number;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  created_at_ms: WideInteger;
  stats: PublicProfileStatsResponse;
  top_ten_finishes: number;
  follower_count: number;
  following_count: number;
}

export interface PublicProfileStatsResponse {
  total_positions: number;
  open_positions: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  total_pnl_micros: string | number;
}

export interface PublicProfilePnlEventResponse {
  source: string;
  resolved_at_ms: WideInteger;
  position_id?: string | null;
  contest_id?: string | null;
  pnl_micros: string | number;
  cumulative_micros: string | number;
}

export interface PublicProfilePnlHistoryResponse {
  events: PublicProfilePnlEventResponse[];
}

export interface PublicProfileFantasyEntryResponse {
  contest_id: string;
  title: string;
  category: string;
  status: string;
  game_type: ContestGameTypeResponse;
  survivor_round_count?: number | null;
  current_game_index?: number | null;
  bet_amount_micros: string | number;
  protocol_prize_pool_micros: string | number;
  total_pot_micros: string | number;
  entries_filled: WideInteger;
  entry_cap: number;
  entry_opens_at_ms?: WideInteger | null;
  betting_closes_ms: WideInteger;
  live_ends_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  joined_at_ms: WideInteger;
  entry_index: number;
  open_leg_count: number;
  resolved_win_count: number;
  rank?: number | null;
  payout_micros: string | number | null;
  net_payout_micros: string | number | null;
  refunded?: boolean;
  pnl_micros: string | number | null;
  image_url?: string | null;
  survivor?: SurvivorEntryStateResponse | null;
  selection_count: number;
  survivor_voided_round_count?: number | null;
  betting_opens_ms?: WideInteger | null;
}

export interface PublicProfileFantasyEntriesResponse {
  entries: PublicProfileFantasyEntryResponse[];
  next_cursor?: string | null;
}

export const PublicProfileContestOwnerEntryVisibilityResponse = {
  HiddenWhileBettingOpen: 'hidden_while_betting_open',
  Visible: 'visible',
} as const;
export type PublicProfileContestOwnerEntryVisibilityResponse = (typeof PublicProfileContestOwnerEntryVisibilityResponse)[keyof typeof PublicProfileContestOwnerEntryVisibilityResponse];

export interface PublicProfileContestOwnerResponse {
  joined: boolean;
  entry_visibility: PublicProfileContestOwnerEntryVisibilityResponse;
  entries: ContestUserEntryResponse[];
}

interface PublicProfileContestDetailResponseSerdeShape {
  contest: PublicContestDetailResponse;
  profile_owner: PublicProfileContestOwnerResponse;
}

export interface PublicProfileContestDetailResponse
  extends PublicContestDetailResponse,
    Omit<PublicProfileContestDetailResponseSerdeShape, 'contest'> {}

export interface PublicProfilePositionSummaryResponse {
  id: string;
  wager_micros: string | number;
  app_token_wager_micros: string | number;
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

export interface PublicProfilePositionsResponse {
  positions: PublicProfilePositionSummaryResponse[];
  next_cursor?: string | null;
}

export interface PublicProfilePositionDetailResponse {
  id: string;
  wager_micros: string | number;
  app_token_wager_micros: string | number;
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

export interface FollowingRawQuery {
  limit?: number | null;
  cursor?: string | null;
}

export interface CommunityPicksRawQuery {
  limit?: number | null;
}

export interface RecentWinnersRawQuery {
  limit?: number | null;
}

export interface FollowStatusResponse {
  following: boolean;
}

export interface CommunityProfileResponse {
  handle: string;
  display_name: string;
  avatar_seed: number;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  viewer_follows?: boolean | null;
}

export interface PublicProfileFollowingResponse {
  profiles: CommunityProfileResponse[];
  next_cursor?: string | null;
}

export interface CommunityPickReactionResponse {
  emoji: string;
  count: WideInteger;
  viewer_reacted: boolean;
}

export interface CommunityPickResponse {
  creator: CommunityProfileResponse;
  viewer_follows: boolean;
  position: PublicProfilePositionDetailResponse;
  reactions: CommunityPickReactionResponse[];
}

export interface CommunityPicksResponse {
  picks: CommunityPickResponse[];
  copy_fee_bps: number;
  market_images?: Record<string, string | null>;
  market_contexts?: Record<string, MarketDisplayContextResponse>;
}

export interface SportsMarketDisplayContextResponse {
  league: string;
  product: string;
  game_id: string;
  away_team: string;
  home_team: string;
  kickoff_at_ms?: WideInteger | null;
}

export interface PriceMarketDisplayContextResponse {
  asset: string;
  window_start_ms?: WideInteger | null;
  duration_secs?: number | null;
  settled_change_bps?: number | null;
}

export interface MarketDisplayContextResponse {
  source?: string | null;
  source_event_id?: string | null;
  event_slug?: string | null;
  event_title?: string | null;
  image_url?: string | null;
  sports?: SportsMarketDisplayContextResponse | null;
  price?: PriceMarketDisplayContextResponse | null;
}

export interface RecentMarketWinnerDetailRefResponse {
  handle: string;
  position_id: string;
}

export interface RecentContestWinnerDetailRefResponse {
  handle: string;
  contest_id: string;
  entry_index: number;
}

export const RecentMarketWinnerEntryTypeResponse = {
  Single: 'single',
  Combo: 'combo',
} as const;
export type RecentMarketWinnerEntryTypeResponse =
  (typeof RecentMarketWinnerEntryTypeResponse)[keyof typeof RecentMarketWinnerEntryTypeResponse];

export type RecentWinnerResponse =
  | {
      type: 'market';
      winner_id: string;
      settled_at_ms: WideInteger;
      profile: CommunityProfileResponse;
      entry_type: RecentMarketWinnerEntryTypeResponse;
      multiplier_bps: WideInteger;
      position: PublicProfilePositionDetailResponse;
      detail_ref: RecentMarketWinnerDetailRefResponse;
      market_contexts?: Record<string, MarketDisplayContextResponse>;
    }
  | {
      type: 'contest';
      winner_id: string;
      settled_at_ms: WideInteger;
      profile: CommunityProfileResponse;
      contest_id: string;
      entry_index: number;
      title: string;
      category: string;
      game_type: ContestGameTypeResponse;
      contest: PublicProfileContestDetailResponse;
      detail_ref: RecentContestWinnerDetailRefResponse;
      image_url: string | null;
      stake_micros: string | number;
      payout_micros: string | number;
      net_payout_micros: string | number;
      pnl_micros: string | number;
      rank: number | null;
      resolved_win_count: number;
      selection_count: number;
      roster_final_points_milli: string | number | null;
    };

export interface RecentWinnersResponse {
  winners: RecentWinnerResponse[];
}

export interface UpdateProfileRequest {
  handle?: string | null;
  display_name?: string | null;
}

export interface SyncXProfileRequest {
  privy_token: string;
}

export interface CheckHandleResponse {
  available: boolean;
  reason?: string | null;
}

export interface CreateSessionRequest {
  privy_token: string;
  auth_wallet_address?: string | null;
  referral_code?: string | null;
}

export interface WalletAuthRequest {
  address: string;
  signature: string;
  signed_at_ms: WideInteger;
  referral_code?: string | null;
}

export interface ChatPostMessageRequest {
  body: string;
  chat_id?: string | null;
  parent?: string | null;
}

export interface ChatEditMessageRequest {
  chat_id?: string | null;
  message_id: string;
  body: string;
}

export interface ChatEmojiReactRequest {
  chat_id?: string | null;
  message_id: string;
  emoji_code: string;
}

export interface ChatStreamQuery {
  chat_id?: string | null;
}

export interface ChatMentionCandidatesQuery {
  chat_id: string;
}

export interface ChatRecentMessagesQuery {
  chat_id?: string | null;
  limit?: number | null;
  before?: string | null;
}

export interface UserSetReferrerRequest {
  referral_code: string;
}

export interface UserCreateReferralCodeRequest {
  code: string;
}

export interface PlaceContestBetSelectionRequest {
  market_id: WideInteger;
  direction: string;
}

export interface PlaceRosterPickRequest {
  tier_index: number;
  selection_index: number;
}

export interface PlaceContestBetRequest {
  contest_id: string;
  use_app_tokens: boolean;
  /**
   * Stable zero-based entry slot. Optional for legacy single-entry and
   * non-Survivor requests. For a new opening-round entry in a multi-entry
   * Survivor contest, send the next contiguous index; reuse that same index
   * for void replacements and later rounds.
   */
  entry_index?: number | null;
  bets: PlaceContestBetSelectionRequest[];
  roster_picks?: PlaceRosterPickRequest[] | null;
  tiebreaker_guess?: WideInteger | null;
}

export interface UserDepositRequest {
  amount_micros: WideInteger;
  idempotency_key: string;
}

export interface UserDepositVaultRequest {
  vault_id: string;
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

export type VaultWithdrawalAmountRequest =
  | { type: 'full'; vault_id: string }
  | { type: 'partial'; vault_id: string; amount_micros: WideInteger };

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
  onboarding_completed?: boolean;
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
  chain_id?: WideInteger | null;
  token_symbol: string;
  token_decimals: number;
}

export interface UserDepositVaultResponse {
}

export interface UserWithdrawResponse {
  amount_micros: string | number;
  operation_id: string;
  destination_address?: string | null;
  tx_hash: string;
}

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
}

export type DepositOperationResponse = UserDepositResponse | BalanceOperationStatusResponse;

export type WithdrawOperationResponse = UserWithdrawResponse | BalanceOperationStatusResponse;

export interface UserRequestWithdrawalVaultResponse {
  queued: boolean;
}

export interface VaultClaimFeesResponse {
  claimed_micros: string | number;
}

export type VaultWithdrawalAmountResponse =
  | { type: 'full' }
  | { type: 'partial'; amount_micros: string | number };

export interface PendingVaultWithdrawalResponse {
  user_id: string;
  requested_amount: VaultWithdrawalAmountResponse;
  withdrawal_time_ms: WideInteger;
}

export interface VaultWithdrawalQueueResponse {
  withdrawal_queue: PendingVaultWithdrawalResponse[];
}

export interface VaultLiquidityProviderResponse {
  user_id: string;
  liquidity_micros: string | number;
}

export interface PositionVaultResponse {
  total_deposit_micros: string | number;
  liquidity_providers: VaultLiquidityProviderResponse[];
}

export interface VaultPositionVaultResponse {
  position_vault: PositionVaultResponse;
}

export interface VaultConfigsResponse {
  max_position_value_bps: number;
  min_deposit_age_ms: WideInteger;
  withdrawal_window_ms: WideInteger;
  binary_event_utilization_cap_bps: number;
  price_strike_utilization_cap_bps: number;
  vault_manager_fee_bps: number;
  external_deposits_enabled: boolean;
  making_enabled: boolean;
  taking_enabled: boolean;
  fee_receiver?: string | null;
}

export interface VaultAmountResponse {
  total_deposit_micros: string | number;
}

export interface VaultAggregateAmountResponse {
  amount_micros: string | number;
}

export interface VaultResponse {
  configs: VaultConfigsResponse;
  unallocated: VaultAmountResponse;
  allocated: VaultAmountResponse;
  binary_event_allocation: VaultAggregateAmountResponse;
  price_strike_allocation: VaultAggregateAmountResponse;
  total_fees: VaultAggregateAmountResponse;
  unclaimed_fees: VaultAggregateAmountResponse;
}

export interface VaultStatsResponse {
  tvl_micros: string | number;
  allocated_micros: string | number;
  unallocated_micros: string | number;
  all_time_pnl_micros: string | number;
  trading_volume_micros: string | number;
  past_month_apr_bps: WideInteger;
  all_time_apr_bps: WideInteger;
}

export interface VaultPnlHistoryPoint {
  t_ms: WideInteger;
  value_micros: string | number;
}

export interface VaultPnlHistoryResponse {
  series: VaultPnlHistoryPoint[];
}

export interface VaultPositionResponse {
  position_id: string;
  legs_summary: string;
  wager_micros: string | number;
  multiplier_bps: WideInteger;
  potential_payout_micros: string | number;
  mark_value_micros: string | number;
  created_at_ms: WideInteger;
  resolved_at_ms?: WideInteger | null;
}

export interface VaultPositionsResponse {
  items: VaultPositionResponse[];
  next_cursor?: string | null;
}

export interface PublicVaultPositionDetailResponse {
  id: string;
  wager_micros: string | number;
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

export interface PublicVaultActivityEventResponse {
  event_type: string;
  user_id: string;
  user_display_name: string;
  user_handle?: string | null;
  user_avatar_seed?: number | null;
  user_x_avatar_url?: string | null;
  amount_micros: string | number;
  position_id?: string | null;
  event_at_ms: WideInteger;
}

export interface PublicVaultActivityResponse {
  items: PublicVaultActivityEventResponse[];
  next_cursor?: string | null;
}

export interface PublicVaultContributorLeaderboardRowResponse {
  user_id: string;
  user_display_name: string;
  user_handle?: string | null;
  user_avatar_seed?: number | null;
  user_x_avatar_url?: string | null;
  total_deposits_micros: string | number;
  all_time_earned_micros: string | number;
  all_time_pnl_micros: string | number;
  unrealized_pnl_micros: string | number;
}

export interface PublicVaultContributorLeaderboardResponse {
  items: PublicVaultContributorLeaderboardRowResponse[];
  next_cursor?: string | null;
}

export interface VaultUserPerformanceResponse {
  current_balance_micros: string | number;
  unallocated_micros: string | number;
  allocated_micros: string | number;
  lifetime_deposits_micros: string | number;
  all_time_earned_micros: string | number;
  all_time_pnl_micros: string | number;
  unrealized_pnl_micros: string | number;
  latest_deposit_time_ms?: WideInteger | null;
  pending_withdrawal?: PendingVaultWithdrawalResponse | null;
}

export interface AvailableBalanceResponse {
  available_micros: string | number;
}

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

export interface PlaceContestBetResponse {
  contest_id: string;
  entry_index: number;
  reserved_micros: string | number;
}

export const ContestCategoryResponse = {
  Mentions: 'mentions',
  Sports: 'sports',
  Culture: 'culture',
} as const;
export type ContestCategoryResponse = (typeof ContestCategoryResponse)[keyof typeof ContestCategoryResponse];

export const ContestStatusResponse = {
  Open: 'open',
  Resolved: 'resolved',
  Voided: 'voided',
} as const;
export type ContestStatusResponse = (typeof ContestStatusResponse)[keyof typeof ContestStatusResponse];

export type ContestBetTypeResponse =
  | { type: 'num_bets'; value: WideInteger }
  | { type: 'bets_per_category'; value: WideInteger };

export const ContestGameTypeResponse = {
  Lineups: 'lineups',
  Survivor: 'survivor',
  Streak: 'streak',
  Outcast: 'outcast',
  Roster: 'roster',
} as const;
export type ContestGameTypeResponse = (typeof ContestGameTypeResponse)[keyof typeof ContestGameTypeResponse];

export const ContestDirectionResponse = {
  Up: 'up',
  Down: 'down',
} as const;
export type ContestDirectionResponse = (typeof ContestDirectionResponse)[keyof typeof ContestDirectionResponse];

export const ContestLegOutcome = {
  Pending: 'pending',
  Won: 'won',
  Lost: 'lost',
  Voided: 'voided',
} as const;
export type ContestLegOutcome = (typeof ContestLegOutcome)[keyof typeof ContestLegOutcome];

export interface ContestPerfectSlateResponse {
  payout_micros: WideInteger;
  winner_count: number;
}

export const SurvivorPhaseResponse = {
  /** The current round exists, but its pick window has not opened yet. */
  Scheduled: 'scheduled',
  PickOpen: 'pick_open',
  PickLocked: 'pick_locked',
  Live: 'live',
  RoundSettled: 'round_settled',
  /** Transitional gap before an ordinary successor or same-index void replacement. */
  AwaitingNextRound: 'awaiting_next_round',
  ContestSettled: 'contest_settled',
  Voided: 'voided',
} as const;
export type SurvivorPhaseResponse = (typeof SurvivorPhaseResponse)[keyof typeof SurvivorPhaseResponse];

export const SurvivorRoundStatusResponse = {
  Scheduled: 'scheduled',
  PickOpen: 'pick_open',
  PickLocked: 'pick_locked',
  Live: 'live',
  Settled: 'settled',
  Voided: 'voided',
} as const;
export type SurvivorRoundStatusResponse = (typeof SurvivorRoundStatusResponse)[keyof typeof SurvivorRoundStatusResponse];

export const SurvivorEntryRoundResultResponse = {
  Pending: 'pending',
  Won: 'won',
  Lost: 'lost',
  Missed: 'missed',
  Voided: 'voided',
} as const;
export type SurvivorEntryRoundResultResponse = (typeof SurvivorEntryRoundResultResponse)[keyof typeof SurvivorEntryRoundResultResponse];

export const SurvivorEliminationReasonResponse = {
  IncorrectPick: 'incorrect_pick',
  MissedDeadline: 'missed_deadline',
} as const;
export type SurvivorEliminationReasonResponse = (typeof SurvivorEliminationReasonResponse)[keyof typeof SurvivorEliminationReasonResponse];

export type SurvivorGameIndexResponse = number;
export type SurvivorRequiredPickCountResponse = number;

export interface PublicContestSummaryResponse {
  contest_id: string;
  title: string;
  category: ContestCategoryResponse;
  status: ContestStatusResponse;
  game_type?: ContestGameTypeResponse | null;
  /** True only while a voided Survivor round awaits same-index replacement. */
  survivor_awaiting_replacement?: boolean | null;
  /** Zero-based round cursor for a Survivor contest. */
  survivor_current_game_index?: number | null;
  bet_amount_micros: WideInteger;
  protocol_prize_pool_micros: WideInteger;
  total_pot_micros: WideInteger;
  prize_pool_growth_starts_after_entries?: number | null;
  perfect_slate?: ContestPerfectSlateResponse | null;
  featured_slot?: number | null;
  entries_filled: number;
  entry_cap: number;
  entry_opens_at_ms?: WideInteger | null;
  betting_closes_ms: WideInteger;
  live_ends_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  created_at_ms: WideInteger;
  image_url?: string | null;
}

export interface ContestCallerSummaryResponse {
  joined: boolean;
  entry_count?: number;
}

export interface CallerContestSummaryResponse {
  contest: PublicContestSummaryResponse;
  caller?: ContestCallerSummaryResponse | null;
}

export interface ContestLobbySummaryResponse {
  summary: CallerContestSummaryResponse;
  /** Marker-free public display copy, capped at 160 characters. */
  description?: string | null;
  max_entries_per_player?: number;
  protocol_prize_pool_pays_app_tokens: boolean;
}

export interface CallerContestsListResponse {
  contests: ContestLobbySummaryResponse[];
  next_cursor?: string | null;
}

export interface ContestMarketResponse {
  market_id: WideInteger;
  selection_group: string;
  market_type: MarketType;
  trading_channels: TradingChannel[];
  name: string;
  /** Resolved event image for this market, when assigned. */
  image_url?: string | null;
  description?: string | null;
  resolution_rules?: string | null;
  status: MarketStatus;
  outcome?: Outcome | null;
  source?: EventMarketSource | null;
  betting_closes_at_ms?: WideInteger | null;
  /** Scheduled event start; separates Survivor pick-locked and live phases. */
  opens_at_ms?: WideInteger | null;
  live_ends_at_ms?: WideInteger | null;
  resolution_time_ms?: WideInteger | null;
  manual_probability_bps?: number | null;
  manual_live_state?: unknown | null;
}

export interface ContestUserPickResponse {
  market_id: WideInteger;
  direction: ContestDirectionResponse;
  outcome: ContestLegOutcome;
}

export interface ContestRosterSelectionResponse {
  selection_index: number;
  name: string;
  image_url?: string | null;
  avg_points_milli?: WideInteger | null;
  points_milli: WideInteger;
  final_points_milli?: WideInteger | null;
  live_state?: unknown | null;
  metadata?: unknown | null;
  updated_at_ms: WideInteger;
}

export interface ContestRosterTierResponse {
  tier_index: number;
  name: string;
  selections: ContestRosterSelectionResponse[];
}

export interface ContestRosterResponse {
  tiers: ContestRosterTierResponse[];
}

export interface ContestRosterPickResponse {
  tier_index: number;
  selection_index: number;
}

export type SurvivorRoundPicksResponse =
  | { visibility: 'hidden'; picks: null }
  | { visibility: 'revealed'; picks: ContestUserPickResponse[] };

/** Reveal-safe direction counts for one market in a Survivor round. */
export interface SurvivorMarketPickCountsResponse {
  market_id: WideInteger;
  up_count: number;
  down_count: number;
}

/**
 * Aggregate participation for a locked Survivor round. Eligibility is fixed at
 * round open; submitted entries have an accepted submission by lock, and all
 * other eligible entries are missed. Markets are bounded to the persisted slate.
 */
export interface SurvivorRoundBreakdownResponse {
  eligible_entry_count: number;
  submitted_entry_count: number;
  missed_entry_count: number;
  markets: SurvivorMarketPickCountsResponse[];
}

export interface SurvivorRoundResponse {
  game_index: number;
  status: SurvivorRoundStatusResponse;
  required_pick_count: number;
  betting_opens_at_ms: WideInteger;
  betting_closes_at_ms: WideInteger;
  resolved_at_ms?: WideInteger | null;
  markets: ContestMarketResponse[];
  /** Reveal-safe aggregate counts; absent until picks lock. */
  breakdown?: SurvivorRoundBreakdownResponse | null;
}

export interface SurvivorEntryRoundResponse {
  game_index: number;
  result: SurvivorEntryRoundResultResponse;
  picks: SurvivorRoundPicksResponse;
}

export type SurvivorEntryStateResponse =
  | {
      status: 'alive';
      eligible_for_current_game: boolean;
      rounds_next_cursor?: SurvivorGameIndexResponse | null;
      rounds: SurvivorEntryRoundResponse[];
    }
  | {
      status: 'eliminated';
      eliminated_game_index: SurvivorGameIndexResponse;
      elimination_reason: SurvivorEliminationReasonResponse;
      rounds_next_cursor?: SurvivorGameIndexResponse | null;
      rounds: SurvivorEntryRoundResponse[];
    }
  | {
      status: 'winner';
      rounds_next_cursor?: SurvivorGameIndexResponse | null;
      rounds: SurvivorEntryRoundResponse[];
    }
  | {
      status: 'voided';
      rounds_next_cursor?: SurvivorGameIndexResponse | null;
      rounds: SurvivorEntryRoundResponse[];
    };

interface SurvivorContestResponseSerdeShape {
  version: number;
  round_count: number;
  phase: SurvivorPhaseResponse;
  current_game_index: number;
  next_game_index?: number | null;
  /**
   * Sorted, unique game indexes. These ordinarily form a contiguous prefix.
   * During same-index replacement, the current index is the sole permitted
   * hole and a pre-scheduled successor may remain. A round-zero gap may be empty.
   */
  rounds: SurvivorRoundResponse[];
  /** Exclusive cursor for the next older contest-round page. */
  rounds_next_cursor?: number | null;
  revealed_game_indexes: number[];
  remaining_survivor_count: number;
}

type SurvivorContestResponseBase = Omit<
  SurvivorContestResponseSerdeShape,
  'version' | 'phase' | 'current_game_index' | 'next_game_index'
> & { version: 1 };

/**
 * `next_game_index` advances by one normally, or equals `current_game_index`
 * while a voided round awaits a same-index replacement.
 */
type SurvivorAwaitingNextRoundCursor = {
  current_game_index: SurvivorGameIndexResponse;
  next_game_index: SurvivorGameIndexResponse;
};

export type SurvivorContestResponse =
  | (SurvivorContestResponseBase & {
      phase: 'pick_open' | 'pick_locked' | 'live' | 'round_settled';
      current_game_index: SurvivorGameIndexResponse;
      next_game_index?: never;
    })
  | (SurvivorContestResponseBase &
      SurvivorAwaitingNextRoundCursor & {
        phase: 'awaiting_next_round';
      })
  | (SurvivorContestResponseBase & {
      phase: 'contest_settled' | 'voided';
      current_game_index: SurvivorGameIndexResponse;
      next_game_index?: never;
    });

export interface ContestUserEntryResponse {
  entry_index: number;
  created_at_ms: WideInteger;
  picks: ContestUserPickResponse[];
  open_leg_count: number;
  resolved_win_count: number;
  payout_micros?: WideInteger | null;
  net_payout_micros?: WideInteger | null;
  refunded?: boolean;
  rank?: number | null;
  tiebreaker_guess?: WideInteger | null;
  perfect_slate_won?: boolean;
  perfect_slate_payout_micros?: WideInteger;
  roster_picks?: ContestRosterPickResponse[] | null;
  roster_points_milli?: WideInteger | null;
  survivor?: SurvivorEntryStateResponse | null;
  survivor_team_usage?: SurvivorTeamUsageResponse[] | null;
}

export interface SurvivorTeamUsageResponse {
  source_team_id: string;
  used_game_index: number;
}

export interface ContestTiebreakerResponse {
  enabled: boolean;
  hint: string;
  result?: WideInteger | null;
}

export interface PublicContestDetailResponse {
  summary: PublicContestSummaryResponse;
  max_entries_per_player?: number;
  description?: string | null;
  bet_type: ContestBetTypeResponse;
  winning_split_bps: WideInteger[];
  protocol_winning_split_bps: WideInteger[];
  protocol_prize_pool_pays_app_tokens: boolean;
  tiebreaker?: ContestTiebreakerResponse | null;
  markets: ContestMarketResponse[];
  roster?: ContestRosterResponse | null;
  survivor?: SurvivorContestResponse | null;
}

export interface ContestCallerDetailResponse {
  joined: boolean;
  entries: ContestUserEntryResponse[];
}

export interface CallerContestDetailResponse {
  contest: PublicContestDetailResponse;
  caller?: ContestCallerDetailResponse | null;
}

export interface ContestLeaderboardRowResponse {
  rank: number;
  user_id: string;
  entry_index: number;
  user_entry_count?: number;
  handle?: string | null;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  avatar_seed: number;
  resolved_win_count: number;
  open_leg_count: number;
  picks?: ContestUserPickResponse[] | null;
  tiebreaker_guess?: WideInteger | null;
  payout_micros?: WideInteger | null;
  net_payout_micros?: WideInteger | null;
  perfect_slate_won?: boolean;
  perfect_slate_payout_micros?: WideInteger;
  refunded?: boolean;
  roster_picks?: ContestRosterPickResponse[] | null;
  roster_points_milli?: WideInteger | null;
  survivor?: SurvivorEntryStateResponse | null;
}

export interface PublicContestLeaderboardResponse {
  total_entries: number;
  entries: ContestLeaderboardRowResponse[];
  next_cursor?: string | null;
}

export interface ContestCallerLeaderboardResponse {
  rows: ContestLeaderboardRowResponse[];
}

export interface CallerContestLeaderboardResponse {
  leaderboard: PublicContestLeaderboardResponse;
  caller?: ContestCallerLeaderboardResponse | null;
}

export interface ContestTopParticipantRowResponse {
  user_id: string;
  handle?: string | null;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  avatar_seed: number;
  won_count: number;
  total_winnings_micros: WideInteger;
}

export interface ContestTopParticipantsResponse {
  window_ms: WideInteger;
  participants: ContestTopParticipantRowResponse[];
}

export interface ContestPopularEntryMarketResponse {
  market_id: WideInteger;
  yes_count: number;
  no_count: number;
}

export interface ContestPopularEntryResponse {
  total_entries: number;
  markets: ContestPopularEntryMarketResponse[];
}

export interface UserReferralCodeResponse {
  referral_code: string;
  max_referrals?: number | null;
  referrals_used: number;
  referrals_remaining?: number | null;
  ever_had_referral_capacity: boolean;
  can_edit: boolean;
}

export interface UserSetReferrerResponse {
}

export interface UserReferralRatesResponse {
  primary_kickback_bps: number;
  secondary_kickback_bps: number;
}

export interface UserReferralStatsResponse {
  total_referred: number;
  total_rewards_micros: string | number;
  has_settled_referral_trade: boolean;
}

export const ReferralLevelLabel = {
  First: 'first',
  Second: 'second',
} as const;
export type ReferralLevelLabel = (typeof ReferralLevelLabel)[keyof typeof ReferralLevelLabel];

export interface UserReferralEntryResponse {
  user_id: string;
  handle: string;
  display_name: string;
  avatar_seed: number;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  referred_at_ms: WideInteger;
  level: ReferralLevelLabel;
  total_volume_micros: string | number;
  total_fees_paid_micros: string | number;
  my_kickback_micros: string | number;
}

export interface UserReferralsListResponse {
  entries: UserReferralEntryResponse[];
  total_count: WideInteger;
}

export interface ErrorResponse {
  error: string;
  code: string;
  details?: string | null;
}

export type ShareImageRef =
  | { source: 'pool_image'; pool_image_id: string };

export interface ShareCardFooter {
  handle: string;
}

export interface ShareStat {
  value: string;
  label: string;
}

export interface StreakShareCard {
  streak_count: number;
  max_streak: number;
  market_title: string;
  market_image?: ShareImageRef | null;
  selection: string;
  selection_date?: string | null;
  prize_label?: string | null;
  footer: ShareCardFooter;
}

export const PriceState = {
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
} as const;
export type PriceState = (typeof PriceState)[keyof typeof PriceState];

export interface PriceShareCard {
  contest_id: string;
  entry_index: number;
  state: PriceState;
  question: string;
  subtitle?: string | null;
  prediction: number;
  current_price: number;
  chart_prices: number[];
  summary?: ShareStat[];
  footer: ShareCardFooter;
}

export const QuestionsState = {
  Pre: 'pre',
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
} as const;
export type QuestionsState = (typeof QuestionsState)[keyof typeof QuestionsState];

export const ContestType = {
  Free: 'free',
  Paid: 'paid',
} as const;
export type ContestType = (typeof ContestType)[keyof typeof ContestType];

export const LegGrade = {
  Pending: 'pending',
  Correct: 'correct',
  Incorrect: 'incorrect',
} as const;
export type LegGrade = (typeof LegGrade)[keyof typeof LegGrade];

export interface QuestionLeg {
  name: string;
  answer: string;
  grade: LegGrade;
}

export interface QuestionsShareCard {
  contest_id: string;
  entry_index: number;
  state: QuestionsState;
  contest_type: ContestType;
  question: string;
  topic_image?: ShareImageRef | null;
  legs: QuestionLeg[];
  summary?: ShareStat[];
  footer: ShareCardFooter;
}

export const MarketsState = {
  Pre: 'pre',
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
} as const;
export type MarketsState = (typeof MarketsState)[keyof typeof MarketsState];

export const MarketWindowOutcome = {
  Pending: 'pending',
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
  Voided: 'voided',
} as const;
export type MarketWindowOutcome = (typeof MarketWindowOutcome)[keyof typeof MarketWindowOutcome];

export interface MarketWindowPick {
  asset: string;
  direction: string;
  won?: boolean | null;
  pct_bps?: number | null;
}

export interface MarketWindow {
  start_ms: WideInteger;
  end_ms: WideInteger;
  time_label: string;
  outcome: MarketWindowOutcome;
  picks: MarketWindowPick[];
}

export interface MarketChartSeries {
  asset: string;
  prices: number[];
}

export interface MarketsShareCard {
  position_id: string;
  tz_offset_minutes?: number | null;
  state?: MarketsState;
  multi_asset?: boolean;
  assets?: string[];
  windows?: MarketWindow[];
  date_label?: string;
  wager_label?: string;
  multiplier_label?: string;
  payout_label?: string;
  price_from?: number | null;
  price_to?: number | null;
  chart?: MarketChartSeries[];
  footer: ShareCardFooter;
}

export const RosterShareState = {
  Pre: 'pre',
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
  Perfect: 'perfect',
} as const;
export type RosterShareState = (typeof RosterShareState)[keyof typeof RosterShareState];

export const RosterShareKind = {
  X: 'x',
  Nfl: 'nfl',
} as const;
export type RosterShareKind = (typeof RosterShareKind)[keyof typeof RosterShareKind];

export interface RosterSharePick {
  name: string;
  bg: string;
  fg: string;
  points?: string | null;
  unit?: string | null;
  tip?: string | null;
  hit?: boolean | null;
}

export interface RosterShareCard {
  contest_id: string;
  entry_index: number;
  state: RosterShareState;
  contest_type: ContestType;
  kind: RosterShareKind;
  prompt: string;
  picks: RosterSharePick[];
  summary?: ShareStat[];
  bonus_label?: string | null;
  footer: ShareCardFooter;
}

export const SurvivorShareState = {
  Pre: 'pre',
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
  Voided: 'voided',
} as const;
export type SurvivorShareState = (typeof SurvivorShareState)[keyof typeof SurvivorShareState];

export const SurvivorSharePresentation = {
  Matchup: 'matchup',
  Daily: 'daily',
} as const;
export type SurvivorSharePresentation =
  (typeof SurvivorSharePresentation)[keyof typeof SurvivorSharePresentation];

export interface SurvivorShareRound {
  result: SurvivorEntryRoundResultResponse;
  pick_count: number;
}

export interface SurvivorShareCard {
  contest_id: string;
  entry_index: number;
  state?: SurvivorShareState;
  contest_type?: ContestType;
  presentation?: SurvivorSharePresentation;
  title?: string;
  rounds?: SurvivorShareRound[];
  summary?: ShareStat[];
  footer: ShareCardFooter;
}

export const EventPositionShareState = {
  Active: 'active',
  Live: 'live',
  Won: 'won',
  Lost: 'lost',
  Voided: 'voided',
} as const;
export type EventPositionShareState = (typeof EventPositionShareState)[keyof typeof EventPositionShareState];

export const EventPositionSharePickGrade = {
  Pending: 'pending',
  Correct: 'correct',
  Incorrect: 'incorrect',
  Voided: 'voided',
} as const;
export type EventPositionSharePickGrade =
  (typeof EventPositionSharePickGrade)[keyof typeof EventPositionSharePickGrade];

export interface EventPositionSharePick {
  market_id: WideInteger;
  label: string;
  side: string;
  grade: EventPositionSharePickGrade;
  odds_label?: string | null;
  result?: string | null;
  /** NFL only: team tricode for the pick's chip (game-wide markets omit it). */
  team_abbr?: string | null;
}

export interface EventPositionShareCard {
  position_id: string;
  tz_offset_minutes?: number | null;
  market_kind?: string | null;
  state?: EventPositionShareState;
  title?: string;
  meta_label?: string | null;
  market_image?: ShareImageRef | null;
  picks?: EventPositionSharePick[];
  wager_label?: string;
  multiplier_label?: string;
  payout_label?: string | null;
  /** NFL only: matchup identity for team chips + combo/prediction heading. */
  nfl?: NflShareMeta | null;
  footer: ShareCardFooter;
}

export interface NflShareMeta {
  away_abbr: string;
  home_abbr: string;
  combo?: boolean;
}

export type ShareCardSnapshot =
  | ({type: 'streak'} & StreakShareCard)
  | ({type: 'price'} & PriceShareCard)
  | ({type: 'questions'} & QuestionsShareCard)
  | ({type: 'markets'} & MarketsShareCard)
  | ({type: 'roster'} & RosterShareCard)
  | ({type: 'survivor'} & SurvivorShareCard)
  | ({type: 'event_position'} & EventPositionShareCard);

export interface CreateShareCardResponse {
  id: string;
  share_url: string;
}

export const StreakRoundStatusResponse = {
  Open: 'open',
  Resolving: 'resolving',
  Resolved: 'resolved',
} as const;
export type StreakRoundStatusResponse = (typeof StreakRoundStatusResponse)[keyof typeof StreakRoundStatusResponse];

export interface StreakTierResponse {
  streak: number;
  payout_micros: WideInteger;
  has_app_token: boolean;
}

export interface StreakMarketResponse {
  market_id: WideInteger;
  selection_group: string;
  market_type: MarketType;
  trading_channels: TradingChannel[];
  name: string;
  status: MarketStatus;
  outcome?: Outcome | null;
  source?: EventMarketSource | null;
  resolution_time_ms?: WideInteger | null;
  betting_closes_at_ms?: WideInteger | null;
  image_url?: string | null;
  juiced?: boolean;
}

export interface StreakUserPickResponse {
  market_id: WideInteger;
  direction: ContestDirectionResponse;
  outcome: ContestLegOutcome;
  picked_at_ms: WideInteger;
}

export interface StreakCurrentRoundResponse {
  game_index: number;
  status: StreakRoundStatusResponse;
  betting_opens_at_ms: WideInteger;
  betting_closes_at_ms: WideInteger;
  resolved_at_ms?: WideInteger | null;
  markets: StreakMarketResponse[];
  user_pick?: StreakUserPickResponse | null;
}

export interface StreakUserStateResponse {
  win_streak: number;
  games_won: number;
  games_lost: number;
  bets_won: number;
  bets_lost: number;
}

export interface StreakResponse {
  contest_id: string;
  title: string;
  description?: string | null;
  tiers: StreakTierResponse[];
  max_streak: number;
  current_round?: StreakCurrentRoundResponse | null;
  scheduled_round?: StreakCurrentRoundResponse | null;
  user?: StreakUserStateResponse | null;
}

export const StreakPickRound = {
  Current: 'current',
  Scheduled: 'scheduled',
} as const;
export type StreakPickRound = (typeof StreakPickRound)[keyof typeof StreakPickRound];

export interface PlaceStreakPickRequest {
  market_id: WideInteger;
  direction: string;
  use_app_tokens: boolean;
  round?: StreakPickRound | null;
}

export interface PlaceStreakPickResponse {
  entry_index: number;
  picked_at_ms: WideInteger;
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

export interface ReferralsListRawQuery {
  page?: number | null;
  limit?: number | null;
}

export interface VaultIdQuery {
  vault_id: string;
}

export interface VaultPnlHistoryQuery {
  vault_id: string;
  range?: string | null;
  metric?: string | null;
}

export interface VaultPositionsQuery {
  vault_id: string;
  status?: string | null;
  cursor?: string | null;
  limit?: number | null;
}

export interface VaultEventsQuery {
  vault_id: string;
  cursor?: string | null;
  limit?: number | null;
  event_type?: string | null;
}

export interface VaultContributorsQuery {
  vault_id: string;
  cursor?: string | null;
  limit?: number | null;
  sort?: string | null;
}

export interface CreateEmbeddedWalletEnsureRequest {
  privy_token: string;
}

export const ReferralPromptRequest = {
  PostWin: 'post_win',
  FirstPick: 'first_pick',
} as const;
export type ReferralPromptRequest = (typeof ReferralPromptRequest)[keyof typeof ReferralPromptRequest];

export interface ClaimReferralPromptRequest {
  prompt: ReferralPromptRequest;
}

export interface AcknowledgeReferralPromptRequest {
  prompt: ReferralPromptRequest;
  claim_token: string;
  shown: boolean;
}

export interface ChatPostGifRequest {
  gif_id: string;
  chat_id?: string | null;
  parent?: string | null;
}

export interface RfqEstimateRequest {
  wager_micros: WideInteger;
  legs: OrderLegJson[];
  shield_on?: boolean;
}

export interface RfqEstimateBatchItemRequest {
  key: string;
  leg: OrderLegJson;
}

export interface RfqEstimateBatchRequest {
  wager_micros: WideInteger;
  estimates: RfqEstimateBatchItemRequest[];
  shield_on?: boolean;
}

export const EmbeddedWalletEnsureStatus = {
  Ready: 'ready',
  Pending: 'pending',
  NotRequired: 'not_required',
} as const;
export type EmbeddedWalletEnsureStatus = (typeof EmbeddedWalletEnsureStatus)[keyof typeof EmbeddedWalletEnsureStatus];

export interface EmbeddedWalletEnsureResponse {
  status: EmbeddedWalletEnsureStatus;
  wallet_address?: string | null;
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

export const RfqEstimateBatchItemStatus = {
  Quoted: 'quoted',
  Unavailable: 'unavailable',
} as const;
export type RfqEstimateBatchItemStatus =
  (typeof RfqEstimateBatchItemStatus)[keyof typeof RfqEstimateBatchItemStatus];

export interface RfqEstimateBatchItemResponse {
  key: string;
  market_id: WideInteger;
  direction: string;
  status: RfqEstimateBatchItemStatus;
  request_id?: string | null;
  quotable: boolean;
  odds?: number | null;
  fillable_micros?: WideInteger | null;
  quotes_received: number;
  quoted_at_ms?: WideInteger | null;
  reason?: string | null;
}

export interface RfqEstimateBatchResponse {
  wager_micros: WideInteger;
  estimates: RfqEstimateBatchItemResponse[];
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

export interface ClaimReferralPromptResponse {
  show: boolean;
  amount_micros?: string | number | null;
  claim_token?: string | null;
  retry_after_ms?: number | null;
}

export interface ObserverAccessResponse {
  enabled: boolean;
}

export interface MarketCategoryVisibilityResponse {
  crypto: boolean;
  mentions: boolean;
  nfl: boolean;
  culture: boolean;
}

export interface UserFeaturesResponse {
  markets_access: boolean;
}

export interface ChatMarketRoomResponse {
  chat_id: string;
}

export interface ChatMentionCandidateResponse {
  user_id: string;
  handle: string;
}

export interface ChatMentionCandidatesResponse {
  candidates: ChatMentionCandidateResponse[];
}

export interface FeedLegResponse {
  asset: string;
  direction: string;
  window_start_ms?: WideInteger | null;
  duration_secs?: number | null;
}

export interface FeedEventWithLegsResponse {
  event: FeedEventResponse;
  primary_asset?: string | null;
  has_binary_event_leg: boolean;
  legs?: FeedLegResponse[];
}

export interface FeedWithLegsResponse {
  events: FeedEventWithLegsResponse[];
  next_cursor?: string | null;
}

export interface PnlHistoryScopedQuery {
  from_?: WideInteger | null;
  to?: WideInteger | null;
  scope?: string | null;
}

export interface PortfolioSummaryRawQuery {
  scope?: string | null;
}

export interface PortfolioSummaryResponse {
  scope: string;
  active_count: WideInteger;
  potential_payout_micros: string | number;
  realized_pnl_micros: string | number;
  biggest_win_micros: string | number | null;
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

export interface ProfileUpdateQuery {
  finalize_onboarding?: boolean;
}

export interface HandleAvailabilityQuery {
  handle: string;
  finalize_onboarding?: boolean;
}

export interface PublicProfileSummaryResponse {
  scope: string;
  active_count: WideInteger;
  potential_payout_micros: string | number;
  realized_pnl_micros: string | number;
  biggest_win_micros: string | number | null;
}

export interface UserReferralStatsRawQuery {
  window?: string | null;
}

export interface WebPushConfigResponse {
  enabled: boolean;
  public_key?: string | null;
}

export interface WebPushSubscriptionKeys {
  p256dh: string;
  auth: string;
}

export interface UpsertWebPushSubscriptionRequest {
  endpoint: string;
  expiration_time?: WideInteger | null;
  keys: WebPushSubscriptionKeys;
}

export interface DeleteWebPushSubscriptionRequest {
  endpoint: string;
}

export interface WebPushSubscriptionResponse {
  subscribed: boolean;
}

export interface StreakPicksRawQuery {
  limit?: number | null;
  cursor?: string | null;
  contest_id?: string | null;
}

export interface StreakHistoryRawQuery {
  limit?: number | null;
  cursor?: string | null;
}

export interface StreakLeaderboardRawQuery {
  limit?: number | null;
}

export interface StreakPickHistoryItemResponse {
  game_index: number;
  market_id: WideInteger;
  market_title: string;
  market_category: string;
  market_outcome?: Outcome | null;
  direction: ContestDirectionResponse;
  outcome: ContestLegOutcome;
  picked_at_ms: WideInteger;
  betting_closes_at_ms?: WideInteger | null;
  resolved_at_ms?: WideInteger | null;
  image_url?: string | null;
}

export interface StreakPicksResponse {
  contest_id?: string | null;
  title?: string | null;
  picks: StreakPickHistoryItemResponse[];
  next_cursor?: string | null;
}

export const StreakPickVisibilityResponse = {
  Visible: 'visible',
  HiddenWhileBettingOpen: 'hidden_while_betting_open',
  None: 'none',
} as const;
export type StreakPickVisibilityResponse = (typeof StreakPickVisibilityResponse)[keyof typeof StreakPickVisibilityResponse];

export interface PublicProfileStreakPicksResponse {
  contest_id?: string | null;
  title?: string | null;
  picks: StreakPickHistoryItemResponse[];
  current_round_pick_visibility: StreakPickVisibilityResponse;
  next_cursor?: string | null;
}

export const StreakRunStatusResponse = {
  Active: 'active',
  Ended: 'ended',
  Expired: 'expired',
  Won: 'won',
} as const;
export type StreakRunStatusResponse = (typeof StreakRunStatusResponse)[keyof typeof StreakRunStatusResponse];

export interface StreakRunTierPayoutResponse {
  streak: number;
  payout_micros: string | number;
  is_app_token: boolean;
  game_index: number;
  won_at_ms: WideInteger;
  credited: boolean;
}

export interface StreakRunResponse {
  contest_id: string;
  title: string;
  max_streak: number;
  status: StreakRunStatusResponse;
  length: number;
  pick_count: number;
  start_game_index: number;
  end_game_index?: number | null;
  started_at_ms: WideInteger;
  ended_at_ms?: WideInteger | null;
  failed_pick_number?: number | null;
  failed_pick?: StreakPickHistoryItemResponse | null;
  cash_payout_micros: string | number;
  tier_payouts: StreakRunTierPayoutResponse[];
}

export interface StreakHistoryResponse {
  runs: StreakRunResponse[];
  next_cursor?: string | null;
}

export interface PublicProfileStreakHistoryResponse {
  runs: StreakRunResponse[];
  next_cursor?: string | null;
}

export interface StreakOnboardingRoundResponse {
  game_index: number;
  target: StreakPickRound;
  betting_closes_at_ms: WideInteger;
  markets: StreakMarketResponse[];
}

export interface StreakOnboardingResponse {
  contest_id: string;
  title: string;
  eligible: boolean;
  round?: StreakOnboardingRoundResponse | null;
}

export interface StreakPopularMarketResponse {
  market_id: WideInteger;
  market_title: string;
  market_category: string;
  betting_closes_at_ms?: WideInteger | null;
  up_count: WideInteger;
  down_count: WideInteger;
  image_url?: string | null;
}

export interface StreakPopularTodayResponse {
  contest_id?: string | null;
  game_index?: number | null;
  total_picks: WideInteger;
  markets: StreakPopularMarketResponse[];
}

export interface StreakLeaderboardRowResponse {
  handle?: string | null;
  display_name?: string | null;
  avatar_seed: number;
  x_handle?: string | null;
  x_avatar_url?: string | null;
  current_streak: number;
  picks: StreakPickHistoryItemResponse[];
  current_pick?: StreakPickHistoryItemResponse | null;
  current_pick_visibility: StreakPickVisibilityResponse;
}

export interface StreakLeaderboardResponse {
  contest_id?: string | null;
  current_game_index?: number | null;
  rows: StreakLeaderboardRowResponse[];
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

export function unsignedRfqOrderRequestToSignedOrderForSession(
  request: UnsignedRfqOrderRequest,
  user: Address | string | Uint8Array,
  nonce: number | bigint | string,
  expiresAtMs: number | bigint | string,
): SignedOrder {
  return signedOrderFromJsonFields({
    user: Address.fromEvm(user),
    wagerMicros: request.wager_micros,
    minOddsDecimal: request.min_odds,
    legs: request.legs,
    nonce,
    expiresAtMs,
    orderType: request.order_type,
    shieldOn: request.shield_on,
    signature: new Uint8Array(65),
  });
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
