"""Generated public API typing contracts. Do not edit by hand."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from .model import LongshotModel, RustStringEnum, RustTaggedUnion
from .taker import OrderLeg, SignedOrder
from .types import (
    Address,
    Direction,
    MarketId,
    MarketStatus,
    MarketType,
    Odds,
    OrderType,
    Outcome,
    PositionId,
    TradingChannel,
)

# Runtime dataclasses remain permissive for decoding, but Rust-required fields
# must be supplied by typed callers; nullable fields retain Optional annotations.

NOTIFICATION_LIST_DEFAULT_LIMIT = 30

NOTIFICATION_LIST_MAX_LIMIT = 100

NOTIFICATION_STREAM_BATCH_LIMIT = 50

MAX_CHART_POINTS = 512

MAX_QUESTION_LEGS = 32

MAX_MARKET_WINDOWS = 9

MAX_MARKET_WINDOW_PICKS = 3

MAX_TZ_OFFSET_MINUTES = 14 * 60

MAX_SUMMARY_STATS = 4

MAX_TEXT_LEN = 200

class ChatUserAvatarResponse(RustTaggedUnion):
    @classmethod
    def x_avatar_url(cls, payload: Any=None, **fields: Any) -> ChatUserAvatarResponse:
        ...
    @classmethod
    def seed(cls, payload: Any=None, **fields: Any) -> ChatUserAvatarResponse:
        ...

class ChatAuthorResponse(LongshotModel):
    user_id: str
    name: str
    avatar: ChatUserAvatarResponse
    def __init__(self, *, user_id: str, name: str, avatar: ChatUserAvatarResponse) -> None: ...

class ChatReactionResponse(LongshotModel):
    emoji_code: str
    reactor: ChatAuthorResponse
    def __init__(self, *, emoji_code: str, reactor: ChatAuthorResponse) -> None: ...

class ChatEmojiDisplayResponse(RustTaggedUnion):
    @classmethod
    def url(cls, payload: Any=None, **fields: Any) -> ChatEmojiDisplayResponse:
        ...
    @classmethod
    def unicode(cls, payload: Any=None, **fields: Any) -> ChatEmojiDisplayResponse:
        ...

class ChatEmojiResponse(LongshotModel):
    code: str
    display: ChatEmojiDisplayResponse
    def __init__(self, *, code: str, display: ChatEmojiDisplayResponse) -> None: ...

class ChatEmojisResponse(LongshotModel):
    emojis: List[ChatEmojiResponse]
    def __init__(self, *, emojis: List[ChatEmojiResponse]) -> None: ...

class ChatReactionUpdateResponse(LongshotModel):
    message_id: str
    reaction_seq: int
    reactions: List[ChatReactionResponse]
    def __init__(self, *, message_id: str, reaction_seq: int, reactions: List[ChatReactionResponse]) -> None: ...

class ChatMessageResponse(LongshotModel):
    message_id: str
    author: ChatAuthorResponse
    body: str
    gif: Optional[ChatGifAttachmentResponse]
    parent: Optional[str]
    reactions: List[ChatReactionResponse]
    edit_seq: int
    reaction_seq: int
    timestamp_ms: int
    def __init__(self, *, message_id: str, author: ChatAuthorResponse, body: str, gif: Optional[ChatGifAttachmentResponse] = ..., parent: Optional[str] = ..., reactions: List[ChatReactionResponse], edit_seq: int, reaction_seq: int, timestamp_ms: int) -> None: ...

class ChatMessageEditResponse(LongshotModel):
    message_id: str
    body: str
    edit_seq: int
    timestamp_ms: int
    def __init__(self, *, message_id: str, body: str, edit_seq: int, timestamp_ms: int) -> None: ...

class ChatRecentMessagesResponse(LongshotModel):
    messages: List[ChatMessageResponse]
    next_cursor: Optional[str]
    writable: bool
    def __init__(self, *, messages: List[ChatMessageResponse], next_cursor: Optional[str] = ..., writable: bool) -> None: ...

class ChatStreamErrorCode(RustStringEnum):
    SubscriberLagged = 'subscriber_lagged'

class ChatStreamErrorEvent(LongshotModel):
    code: ChatStreamErrorCode
    message: str
    skipped: int
    def __init__(self, *, code: ChatStreamErrorCode, message: str, skipped: int) -> None: ...

class ListContestsQuery(LongshotModel):
    status: Optional[str]
    category: Optional[str]
    cursor: Optional[str]
    limit: Optional[int]
    def __init__(self, *, status: Optional[str] = ..., category: Optional[str] = ..., cursor: Optional[str] = ..., limit: Optional[int] = ...) -> None: ...

class ContestDetailQuery(LongshotModel):
    survivor_round_limit: Optional[int]
    survivor_round_before: Optional[int]
    def __init__(self, *, survivor_round_limit: Optional[int] = ..., survivor_round_before: Optional[int] = ...) -> None: ...

class ContestLeaderboardQuery(LongshotModel):
    cursor: Optional[str]
    limit: Optional[int]
    survivor_round_limit: Optional[int]
    survivor_round_before: Optional[int]
    def __init__(self, *, cursor: Optional[str] = ..., limit: Optional[int] = ..., survivor_round_limit: Optional[int] = ..., survivor_round_before: Optional[int] = ...) -> None: ...

class ContestTopParticipantsQuery(LongshotModel):
    window_ms: Optional[str]
    limit: Optional[int]
    def __init__(self, *, window_ms: Optional[str] = ..., limit: Optional[int] = ...) -> None: ...

class FeedFilter(RustStringEnum):
    All = 'All'
    Resolved = 'Resolved'
    Golden = 'Golden'
    Won = 'Won'

class FeedRawQuery(LongshotModel):
    filter: Optional[str]
    limit: Optional[int]
    cursor: Optional[str]
    binary_event_market_ids: Optional[str]
    def __init__(self, *, filter: Optional[str] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ..., binary_event_market_ids: Optional[str] = ...) -> None: ...

class FeedEventResponse(LongshotModel):
    event_type: str
    position_id: str
    market: str
    duration_label: Optional[str]
    primary_leg: Optional[PrimaryLegIdentityResponse]
    legs_count: int
    user_display_name: str
    user_handle: Optional[str]
    user_avatar_seed: int
    user_avatar_url: Optional[str]
    wager_micros: int
    multiplier_bps: int
    payout_micros: int
    event_at_ms: int
    def __init__(self, *, event_type: str, position_id: str, market: str, duration_label: Optional[str] = ..., primary_leg: Optional[PrimaryLegIdentityResponse] = ..., legs_count: int, user_display_name: str, user_handle: Optional[str] = ..., user_avatar_seed: int, user_avatar_url: Optional[str] = ..., wager_micros: int, multiplier_bps: int, payout_micros: int, event_at_ms: int) -> None: ...

class FeedResponse(LongshotModel):
    events: List[FeedEventResponse]
    next_cursor: Optional[str]
    def __init__(self, *, events: List[FeedEventResponse], next_cursor: Optional[str] = ...) -> None: ...

class LeaderboardWindow(RustStringEnum):
    Day = 'day'
    Week = 'week'
    Month = 'month'
    AllTime = 'all_time'

class LeaderboardRawQuery(LongshotModel):
    period: Optional[str]
    scope: Optional[str]
    metric: Optional[str]
    limit: Optional[int]
    def __init__(self, *, period: Optional[str] = ..., scope: Optional[str] = ..., metric: Optional[str] = ..., limit: Optional[int] = ...) -> None: ...

class LeaderboardMeRawQuery(LongshotModel):
    metric: Optional[str]
    window: Optional[str]
    asset: Optional[str]
    def __init__(self, *, metric: Optional[str] = ..., window: Optional[str] = ..., asset: Optional[str] = ...) -> None: ...

class HighlightsRawQuery(LongshotModel):
    sort: Optional[str]
    window: Optional[str]
    limit: Optional[int]
    def __init__(self, *, sort: Optional[str] = ..., window: Optional[str] = ..., limit: Optional[int] = ...) -> None: ...

class LeaderboardMetricResponse(RustStringEnum):
    Pnl = 'pnl'
    Volume = 'volume'
    Roi = 'roi'
    Wins = 'wins'

class HighlightSortResponse(RustStringEnum):
    Payout = 'payout'
    Multiplier = 'multiplier'

class LeaderboardEntry(RustTaggedUnion):
    @classmethod
    def pnl(cls, payload: Any=None, **fields: Any) -> LeaderboardEntry:
        ...
    @classmethod
    def combo(cls, payload: Any=None, **fields: Any) -> LeaderboardEntry:
        ...

class LeaderboardResponse(LongshotModel):
    period: LeaderboardPeriod
    scope: LeaderboardScope
    metric: LeaderboardMetric
    period_start_ms: int
    period_end_ms: int
    entries: List[LeaderboardEntry]
    caller: Optional[LeaderboardCaller]
    def __init__(self, *, period: LeaderboardPeriod, scope: LeaderboardScope, metric: LeaderboardMetric, period_start_ms: int, period_end_ms: int, entries: List[LeaderboardEntry], caller: Optional[LeaderboardCaller] = ...) -> None: ...

class LeaderboardMyRankResponse(LongshotModel):
    entry: Optional[LegacyLeaderboardEntry]
    def __init__(self, *, entry: Optional[LegacyLeaderboardEntry] = ...) -> None: ...

class HighlightEntry(LongshotModel):
    position_id: str
    user_id: str
    display_name: Optional[str]
    avatar_seed: Optional[int]
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    market: str
    duration_label: Optional[str]
    primary_leg: Optional[PrimaryLegIdentityResponse]
    legs_count: int
    wager_micros: int
    payout_micros: int
    multiplier_bps: int
    def __init__(self, *, position_id: str, user_id: str, display_name: Optional[str] = ..., avatar_seed: Optional[int] = ..., x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., market: str, duration_label: Optional[str] = ..., primary_leg: Optional[PrimaryLegIdentityResponse] = ..., legs_count: int, wager_micros: int, payout_micros: int, multiplier_bps: int) -> None: ...

class LeaderboardHighlightsResponse(LongshotModel):
    sort: HighlightSortResponse
    window: LeaderboardWindow
    highlights: List[HighlightEntry]
    def __init__(self, *, sort: HighlightSortResponse, window: LeaderboardWindow, highlights: List[HighlightEntry]) -> None: ...

class PriceSourceResponse(RustStringEnum):
    Binance = 'binance'
    Polymarket = 'polymarket'

class MarketCandlesQuery(LongshotModel):
    asset: Optional[str]
    timeframe_secs: Optional[int]
    past_slots: Optional[int]
    now_ms: Optional[int]
    before_ms: Optional[int]
    max_points: Optional[int]
    ohlc_resolution_secs: Optional[int]
    def __init__(self, *, asset: Optional[str] = ..., timeframe_secs: Optional[int] = ..., past_slots: Optional[int] = ..., now_ms: Optional[int] = ..., before_ms: Optional[int] = ..., max_points: Optional[int] = ..., ohlc_resolution_secs: Optional[int] = ...) -> None: ...

class MarketTicksStreamQuery(LongshotModel):
    assets: Optional[str]
    timeframe_secs: Optional[int]
    since_ms: Optional[int]
    since_seq: Optional[int]
    def __init__(self, *, assets: Optional[str] = ..., timeframe_secs: Optional[int] = ..., since_ms: Optional[int] = ..., since_seq: Optional[int] = ...) -> None: ...

class ExternalOddsSourceQuery(LongshotModel):
    assets: Optional[str]
    timeframe_secs: Optional[int]
    window_start_ms: Optional[str]
    market_ids: Optional[str]
    def __init__(self, *, assets: Optional[str] = ..., timeframe_secs: Optional[int] = ..., window_start_ms: Optional[str] = ..., market_ids: Optional[str] = ...) -> None: ...

class ChartPoint(LongshotModel):
    timestamp_ms: int
    price: float
    def __init__(self, *, timestamp_ms: int, price: float) -> None: ...

class OhlcCandle(LongshotModel):
    time_ms: int
    open: float
    high: float
    low: float
    close: float
    def __init__(self, *, time_ms: int, open: float, high: float, low: float, close: float) -> None: ...

class MarketTickStreamEvent(LongshotModel):
    asset: str
    price_source: PriceSourceResponse
    timestamp_ms: int
    price: float
    source_trade_id: int
    seq: int
    slot_start_ms: int
    sample_interval_ms: int
    is_synthetic: bool
    emitted_at_ms: int
    def __init__(self, *, asset: str, price_source: PriceSourceResponse, timestamp_ms: int, price: float, source_trade_id: int, seq: int, slot_start_ms: int, sample_interval_ms: int, is_synthetic: bool, emitted_at_ms: int) -> None: ...

class MarketTickStreamErrorCode(RustStringEnum):
    PublisherSeedCursorFailed = 'publisher_seed_cursor_failed'
    PublisherIncrementalQueryFailed = 'publisher_incremental_query_failed'
    PublisherFallbackQueryFailed = 'publisher_fallback_query_failed'

class MarketTickStreamErrorEvent(LongshotModel):
    asset: str
    price_source: PriceSourceResponse
    code: MarketTickStreamErrorCode
    retry_after_ms: int
    emitted_at_ms: int
    def __init__(self, *, asset: str, price_source: PriceSourceResponse, code: MarketTickStreamErrorCode, retry_after_ms: int, emitted_at_ms: int) -> None: ...

class TopOfBookStreamQuery(LongshotModel):
    assets: Optional[str]
    timeframe_secs: Optional[int]
    window_start_ms: Optional[str]
    market_ids: Optional[str]
    since_seq: Optional[int]
    def __init__(self, *, assets: Optional[str] = ..., timeframe_secs: Optional[int] = ..., window_start_ms: Optional[str] = ..., market_ids: Optional[str] = ..., since_seq: Optional[int] = ...) -> None: ...

class ExternalOddsSourceStatus(RustStringEnum):
    Ok = 'ok'
    Partial = 'partial'
    Pending = 'pending'
    EmptyBook = 'empty_book'
    MissingBinding = 'missing_tokens'
    UpstreamError = 'upstream_error'

class ExternalOddsSourceKind(RustStringEnum):
    PolymarketWs = 'clob_ws'
    KalshiRest = 'kalshi_rest'
    ManifoldRest = 'manifold_rest'
    Cache = 'cache'
    None_ = 'none'

class ExternalOddsSourceRow(LongshotModel):
    key: str
    asset: Optional[str]
    timeframe_secs: Optional[int]
    window_start_ms: Optional[int]
    window_end_ms: Optional[int]
    market_id: Optional[int]
    source_market_id: Optional[str]
    yes_ask_cents: Optional[float]
    no_ask_cents: Optional[float]
    status: ExternalOddsSourceStatus
    updated_at_ms: int
    source: ExternalOddsSourceKind
    def __init__(self, *, key: str, asset: Optional[str] = ..., timeframe_secs: Optional[int] = ..., window_start_ms: Optional[int] = ..., window_end_ms: Optional[int] = ..., market_id: Optional[int] = ..., source_market_id: Optional[str] = ..., yes_ask_cents: Optional[float] = ..., no_ask_cents: Optional[float] = ..., status: ExternalOddsSourceStatus, updated_at_ms: int, source: ExternalOddsSourceKind) -> None: ...

class ExternalOddsSourceResponse(LongshotModel):
    rows: List[ExternalOddsSourceRow]
    def __init__(self, *, rows: List[ExternalOddsSourceRow]) -> None: ...

class TopOfBookStreamEvent(LongshotModel):
    key: str
    asset: Optional[str]
    timeframe_secs: Optional[int]
    window_start_ms: Optional[int]
    window_end_ms: Optional[int]
    market_id: Optional[int]
    source_market_id: Optional[str]
    yes_ask_cents: Optional[float]
    no_ask_cents: Optional[float]
    status: ExternalOddsSourceStatus
    source: ExternalOddsSourceKind
    updated_at_ms: int
    seq: int
    emitted_at_ms: int
    def __init__(self, *, key: str, asset: Optional[str] = ..., timeframe_secs: Optional[int] = ..., window_start_ms: Optional[int] = ..., window_end_ms: Optional[int] = ..., market_id: Optional[int] = ..., source_market_id: Optional[str] = ..., yes_ask_cents: Optional[float] = ..., no_ask_cents: Optional[float] = ..., status: ExternalOddsSourceStatus, source: ExternalOddsSourceKind, updated_at_ms: int, seq: int, emitted_at_ms: int) -> None: ...

class TopOfBookStreamErrorCode(RustStringEnum):
    SubscriberDisconnected = 'subscriber_disconnected'

class TopOfBookStreamErrorEvent(LongshotModel):
    code: TopOfBookStreamErrorCode
    retry_after_ms: int
    emitted_at_ms: int
    def __init__(self, *, code: TopOfBookStreamErrorCode, retry_after_ms: int, emitted_at_ms: int) -> None: ...

class TopOfBookHistoryQuery(LongshotModel):
    market_ids: str
    def __init__(self, *, market_ids: str) -> None: ...

class TopOfBookHistoryPoint(LongshotModel):
    timestamp_ms: int
    yes_ask_cents: Optional[float]
    no_ask_cents: Optional[float]
    def __init__(self, *, timestamp_ms: int, yes_ask_cents: Optional[float] = ..., no_ask_cents: Optional[float] = ...) -> None: ...

class TopOfBookHistoryStatus(RustStringEnum):
    Ok = 'ok'
    Unsupported = 'unsupported'
    UpstreamError = 'upstream_error'

class TopOfBookHistoryMarket(LongshotModel):
    market_id: int
    source_market_id: Optional[str]
    status: TopOfBookHistoryStatus
    points: List[TopOfBookHistoryPoint]
    def __init__(self, *, market_id: int, source_market_id: Optional[str] = ..., status: TopOfBookHistoryStatus, points: List[TopOfBookHistoryPoint]) -> None: ...

class TopOfBookHistoryResponse(LongshotModel):
    bucket_secs: int
    window_start_ms: int
    generated_at_ms: int
    markets: List[TopOfBookHistoryMarket]
    def __init__(self, *, bucket_secs: int, window_start_ms: int, generated_at_ms: int, markets: List[TopOfBookHistoryMarket]) -> None: ...

class MarketCandlesResponse(LongshotModel):
    asset: str
    timeframe_secs: int
    past_slots: int
    requested_before_ms: Optional[int]
    next_before_ms: Optional[int]
    has_more_before: bool
    store_ready: bool
    timescale_enabled: bool
    cagg_enabled: bool
    source: str
    price_source: PriceSourceResponse
    generated_at_ms: int
    slot_ms: int
    candle_bucket_ms: int
    current_slot_start_ms: int
    current_slot_end_ms: int
    domain_start_ms: int
    domain_end_ms: int
    latest_price: Optional[float]
    latest_price_timestamp_ms: Optional[int]
    candle_count: int
    points: List[ChartPoint]
    ohlc: List[OhlcCandle]
    def __init__(self, *, asset: str, timeframe_secs: int, past_slots: int, requested_before_ms: Optional[int] = ..., next_before_ms: Optional[int] = ..., has_more_before: bool, store_ready: bool, timescale_enabled: bool, cagg_enabled: bool, source: str, price_source: PriceSourceResponse, generated_at_ms: int, slot_ms: int, candle_bucket_ms: int, current_slot_start_ms: int, current_slot_end_ms: int, domain_start_ms: int, domain_end_ms: int, latest_price: Optional[float] = ..., latest_price_timestamp_ms: Optional[int] = ..., candle_count: int, points: List[ChartPoint], ohlc: List[OhlcCandle]) -> None: ...

class ReferencePriceQuery(LongshotModel):
    asset: Optional[str]
    timeframe_secs: Optional[int]
    def __init__(self, *, asset: Optional[str] = ..., timeframe_secs: Optional[int] = ...) -> None: ...

class SourceStatus(RustStringEnum):
    Ok = 'ok'
    Pending = 'pending'
    Unavailable = 'unavailable'

class ReferencePriceResponse(LongshotModel):
    asset: str
    timeframe_secs: int
    current_slot_start_ms: int
    window_open_price: Optional[float]
    source_status: SourceStatus
    def __init__(self, *, asset: str, timeframe_secs: int, current_slot_start_ms: int, window_open_price: Optional[float] = ..., source_status: SourceStatus) -> None: ...

class WindowResultsQuery(LongshotModel):
    timeframe_secs: Optional[int]
    past_windows: Optional[int]
    def __init__(self, *, timeframe_secs: Optional[int] = ..., past_windows: Optional[int] = ...) -> None: ...

class WindowDirection(RustStringEnum):
    Up = 'up'
    Down = 'down'

class WindowAssetResult(LongshotModel):
    asset: str
    open_price: float
    close_price: float
    direction: WindowDirection
    price_source: PriceSourceResponse
    def __init__(self, *, asset: str, open_price: float, close_price: float, direction: WindowDirection, price_source: PriceSourceResponse) -> None: ...

class WindowResult(LongshotModel):
    slot_start_ms: int
    slot_end_ms: int
    assets: List[WindowAssetResult]
    def __init__(self, *, slot_start_ms: int, slot_end_ms: int, assets: List[WindowAssetResult]) -> None: ...

class WindowResultsResponse(LongshotModel):
    timeframe_secs: int
    past_windows: int
    price_source: PriceSourceResponse
    generated_at_ms: int
    windows: List[WindowResult]
    def __init__(self, *, timeframe_secs: int, past_windows: int, price_source: PriceSourceResponse, generated_at_ms: int, windows: List[WindowResult]) -> None: ...

class PublicMarketsRawQuery(LongshotModel):
    market_type: Optional[MarketType]
    source: Optional[str]
    source_event_id: Optional[str]
    trading_channel: Optional[TradingChannel]
    limit: Optional[int]
    cursor: Optional[str]
    statuses: Optional[List[MarketStatus]]
    def __init__(self, *, market_type: Optional[MarketType] = ..., source: Optional[str] = ..., source_event_id: Optional[str] = ..., trading_channel: Optional[TradingChannel] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ..., statuses: Optional[List[MarketStatus]] = ...) -> None: ...

class EventMarketSource(LongshotModel):
    source: str
    event_id: Optional[str]
    source_market_ids: List[str]
    attributes: Optional[Dict[str, Any]]
    def __init__(self, *, source: str, event_id: Optional[str] = ..., source_market_ids: List[str], attributes: Optional[Dict[str, Any]] = ...) -> None: ...

class PriceStrikeMarket(LongshotModel):
    id: MarketId
    market_type: MarketType
    trading_channels: List[TradingChannel]
    name: str
    description: Optional[str]
    status: MarketStatus
    tradeable: bool
    category_tags: List[str]
    betting_closes_at_ms: int
    resolution_time_ms: int
    open_strike_micros: Optional[int]
    resolved_outcome: Optional[Outcome]
    created_at_ms: int
    opened_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    image_url: Optional[str]
    def __init__(self, *, id: MarketId, market_type: MarketType, trading_channels: List[TradingChannel], name: str, description: Optional[str] = ..., status: MarketStatus, tradeable: bool, category_tags: List[str], betting_closes_at_ms: int, resolution_time_ms: int, open_strike_micros: Optional[int] = ..., resolved_outcome: Optional[Outcome] = ..., created_at_ms: int, opened_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., image_url: Optional[str] = ...) -> None: ...

class EventMarket(LongshotModel):
    id: MarketId
    market_type: MarketType
    trading_channels: List[TradingChannel]
    chat_id: str
    name: str
    description: Optional[str]
    resolution_rules: Optional[str]
    status: MarketStatus
    tradeable: bool
    category_tags: List[str]
    opens_at_ms: Optional[int]
    source_starts_at_ms: Optional[int]
    betting_closes_at_ms: int
    live_ends_at_ms: Optional[int]
    resolution_time_ms: int
    resolved_outcome: Optional[Outcome]
    created_at_ms: int
    opened_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    source: EventMarketSource
    manual_probability_bps: Optional[int]
    image_url: Optional[str]
    def __init__(self, *, id: MarketId, market_type: MarketType, trading_channels: List[TradingChannel], chat_id: str, name: str, description: Optional[str] = ..., resolution_rules: Optional[str] = ..., status: MarketStatus, tradeable: bool, category_tags: List[str], opens_at_ms: Optional[int] = ..., source_starts_at_ms: Optional[int] = ..., betting_closes_at_ms: int, live_ends_at_ms: Optional[int] = ..., resolution_time_ms: int, resolved_outcome: Optional[Outcome] = ..., created_at_ms: int, opened_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., source: EventMarketSource, manual_probability_bps: Optional[int] = ..., image_url: Optional[str] = ...) -> None: ...

class PublicMarket(RustTaggedUnion):
    @classmethod
    def event(cls, payload: Any=None, **fields: Any) -> PublicMarket:
        ...
    @classmethod
    def price_strike(cls, payload: Any=None, **fields: Any) -> PublicMarket:
        ...

class PublicMarketResponse(LongshotModel):
    market: PublicMarket
    def __init__(self, *, market: PublicMarket) -> None: ...

class PublicMarketsResponse(LongshotModel):
    markets: List[PublicMarket]
    next_cursor: Optional[str]
    def __init__(self, *, markets: List[PublicMarket], next_cursor: Optional[str] = ...) -> None: ...

class MarketMetadataEntry(LongshotModel):
    market_id: int
    asset: str
    duration_secs: int
    start_at_ms: int
    betting_closes_at_ms: int
    def __init__(self, *, market_id: int, asset: str, duration_secs: int, start_at_ms: int, betting_closes_at_ms: int) -> None: ...

class MarketLookupResponse(LongshotModel):
    market: MarketMetadataEntry
    def __init__(self, *, market: MarketMetadataEntry) -> None: ...

class MarketLookupQuery(LongshotModel):
    asset: str
    duration_secs: int
    window_start_ms: int
    def __init__(self, *, asset: str, duration_secs: int, window_start_ms: int) -> None: ...

class MarketCurrentQuery(LongshotModel):
    asset: str
    duration_secs: int
    def __init__(self, *, asset: str, duration_secs: int) -> None: ...

class RecentResolutionsQuery(LongshotModel):
    asset: str
    duration_secs: int
    limit: Optional[int]
    def __init__(self, *, asset: str, duration_secs: int, limit: Optional[int] = ...) -> None: ...

class RecentResolutionEntry(LongshotModel):
    market_id: int
    outcome: str
    window_start_ms: int
    resolved_at_ms: int
    def __init__(self, *, market_id: int, outcome: str, window_start_ms: int, resolved_at_ms: int) -> None: ...

class RecentResolutionsResponse(LongshotModel):
    asset: str
    duration_secs: int
    resolutions: List[RecentResolutionEntry]
    def __init__(self, *, asset: str, duration_secs: int, resolutions: List[RecentResolutionEntry]) -> None: ...

class NotificationsRawQuery(LongshotModel):
    filter: Optional[str]
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, filter: Optional[str] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class NotificationStreamRawQuery(LongshotModel):
    after: Optional[str]
    def __init__(self, *, after: Optional[str] = ...) -> None: ...

class NotificationPayload(RustTaggedUnion):
    @classmethod
    def binary_event_start_soon(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def fantasy_start_soon(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def streak_start_soon(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def streak_expiring(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def binary_event_win(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def price_strike_parlay_win(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def rfq_result(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def fantasy_result(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def perfect_slate(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def streak_win(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def streak_settled(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def payout_review(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def credits_granted(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def chat_mention(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...
    @classmethod
    def unknown(cls, payload: Any=None, **fields: Any) -> NotificationPayload:
        ...

class BinaryEventStartSoonNotificationPayload(LongshotModel):
    source: str
    event_id: str
    market_title: str
    starts_at_ms: int
    def __init__(self, *, source: str, event_id: str, market_title: str, starts_at_ms: int) -> None: ...

class FantasyStartSoonNotificationPayload(LongshotModel):
    pool_image_scope_id: Optional[str]
    contest_id: Optional[str]
    entry_index: Optional[int]
    contest_title: str
    starts_at_ms: int
    selection_count: int
    def __init__(self, *, pool_image_scope_id: Optional[str] = ..., contest_id: Optional[str] = ..., entry_index: Optional[int] = ..., contest_title: str, starts_at_ms: int, selection_count: int) -> None: ...

class StreakStartSoonNotificationPayload(LongshotModel):
    pool_image_scope_id: Optional[str]
    contest_title: str
    market_title: str
    starts_at_ms: int
    def __init__(self, *, pool_image_scope_id: Optional[str] = ..., contest_title: str, market_title: str, starts_at_ms: int) -> None: ...

class StreakExpiringNotificationPayload(LongshotModel):
    contest_id: str
    contest_title: str
    entry_index: int
    win_streak: int
    expires_at_ms: int
    def __init__(self, *, contest_id: str, contest_title: str, entry_index: int, win_streak: int, expires_at_ms: int) -> None: ...

class BinaryEventWinNotificationPayload(LongshotModel):
    position_id: str
    source: Optional[str]
    event_id: Optional[str]
    net_payout_micros: int
    multiplier_bps: int
    market_title: str
    market_ids: Optional[List[int]]
    def __init__(self, *, position_id: str, source: Optional[str] = ..., event_id: Optional[str] = ..., net_payout_micros: int, multiplier_bps: int, market_title: str, market_ids: Optional[List[int]] = ...) -> None: ...

class NflShareMeta(LongshotModel):
    away_abbr: str
    home_abbr: str
    combo: Optional[bool]
    def __init__(self, *, away_abbr: str, home_abbr: str, combo: Optional[bool] = ...) -> None: ...

class PriceStrikeParlayWinNotificationPayload(LongshotModel):
    position_id: str
    net_payout_micros: int
    multiplier_bps: int
    leg_summary: str
    is_multi_asset: bool
    duration_secs: List[int]
    def __init__(self, *, position_id: str, net_payout_micros: int, multiplier_bps: int, leg_summary: str, is_multi_asset: bool, duration_secs: List[int]) -> None: ...

class RfqResultNotificationPayload(LongshotModel):
    request_id: str
    status: RfqResultNotificationStatus
    final_wager_micros: Optional[int]
    payout_micros: Optional[int]
    odds: Optional[float]
    def __init__(self, *, request_id: str, status: RfqResultNotificationStatus, final_wager_micros: Optional[int] = ..., payout_micros: Optional[int] = ..., odds: Optional[float] = ...) -> None: ...

class RfqResultNotificationStatus(RustStringEnum):
    Completed = 'completed'
    Failed = 'failed'
    Cancelled = 'cancelled'
    Timeout = 'timeout'

class FantasyResultNotificationPayload(LongshotModel):
    pool_image_scope_id: Optional[str]
    contest_id: str
    game_index: int
    game_type: FantasyResultGameType
    contest_title: str
    contest_terminal: bool
    contest_refunded: bool
    entry_count: int
    successful_entry_count: int
    held_entry_count: int
    credited_payout_micros: int
    held_payout_micros: int
    best_entry: Optional[FantasyResultBestEntry]
    tiebreaker_result: Optional[int]
    def __init__(self, *, pool_image_scope_id: Optional[str] = ..., contest_id: str, game_index: int, game_type: FantasyResultGameType, contest_title: str, contest_terminal: bool, contest_refunded: bool, entry_count: int, successful_entry_count: int, held_entry_count: int, credited_payout_micros: int, held_payout_micros: int, best_entry: Optional[FantasyResultBestEntry] = ..., tiebreaker_result: Optional[int] = ...) -> None: ...

class FantasyResultGameType(RustStringEnum):
    Lineups = 'lineups'
    Survivor = 'survivor'
    Outcast = 'outcast'
    Roster = 'roster'

class FantasyResultBestEntry(LongshotModel):
    entry_index: int
    rank: int
    correct_count: Optional[int]
    selection_count: Optional[int]
    def __init__(self, *, entry_index: int, rank: int, correct_count: Optional[int] = ..., selection_count: Optional[int] = ...) -> None: ...

class PerfectSlateNotificationPayload(LongshotModel):
    contest_id: str
    game_index: int
    contest_title: str
    winning_entry_count: int
    entry_indexes: List[int]
    payout_micros: int
    held_entry_count: int
    pool_micros: Optional[int]
    total_winning_entry_count: Optional[int]
    def __init__(self, *, contest_id: str, game_index: int, contest_title: str, winning_entry_count: int, entry_indexes: List[int], payout_micros: int, held_entry_count: int, pool_micros: Optional[int] = ..., total_winning_entry_count: Optional[int] = ...) -> None: ...

class StreakWinNotificationPayload(LongshotModel):
    pool_image_scope_id: Optional[str]
    contest_id: Optional[str]
    game_index: Optional[int]
    contest_title: str
    market_title: Optional[str]
    win_streak: int
    payout_micros: int
    app_token_micros: Optional[int]
    is_app_token: Optional[bool]
    outcome: StreakWinOutcome
    def __init__(self, *, pool_image_scope_id: Optional[str] = ..., contest_id: Optional[str] = ..., game_index: Optional[int] = ..., contest_title: str, market_title: Optional[str] = ..., win_streak: int, payout_micros: int, app_token_micros: Optional[int] = ..., is_app_token: Optional[bool] = ..., outcome: StreakWinOutcome) -> None: ...

class StreakWinOutcome(RustStringEnum):
    Win = 'win'
    WinAndReset = 'win_and_reset'

class StreakSettledNotificationPayload(LongshotModel):
    pool_image_scope_id: Optional[str]
    contest_title: str
    market_title: Optional[str]
    win_streak: int
    outcome: StreakSettledOutcome
    def __init__(self, *, pool_image_scope_id: Optional[str] = ..., contest_title: str, market_title: Optional[str] = ..., win_streak: int, outcome: StreakSettledOutcome) -> None: ...

class StreakSettledOutcome(RustStringEnum):
    Loss = 'loss'

class PayoutReviewNotificationPayload(LongshotModel):
    pool_image_scope_id: Optional[str]
    contest_id: Optional[str]
    entry_index: Optional[int]
    contest_title: str
    payout_micros: int
    app_token_micros: Optional[int]
    is_app_token: Optional[bool]
    status: PayoutReviewNotificationStatus
    def __init__(self, *, pool_image_scope_id: Optional[str] = ..., contest_id: Optional[str] = ..., entry_index: Optional[int] = ..., contest_title: str, payout_micros: int, app_token_micros: Optional[int] = ..., is_app_token: Optional[bool] = ..., status: PayoutReviewNotificationStatus) -> None: ...

class PayoutReviewNotificationStatus(RustStringEnum):
    Pending = 'pending'
    Approved = 'approved'
    Rejected = 'rejected'

class CreditsGrantedNotificationPayload(LongshotModel):
    grant_id: str
    amount_micros: int
    contest_id: Optional[str]
    game_index: Optional[int]
    def __init__(self, *, grant_id: str, amount_micros: int, contest_id: Optional[str] = ..., game_index: Optional[int] = ...) -> None: ...

class ChatMentionNotificationPayload(LongshotModel):
    chat_id: str
    message_id: str
    chat_context: Optional[ChatMentionContext]
    contest_id: Optional[str]
    def __init__(self, *, chat_id: str, message_id: str, chat_context: Optional[ChatMentionContext] = ..., contest_id: Optional[str] = ...) -> None: ...

class ChatMentionContext(RustStringEnum):
    Contest = 'contest'
    CryptoMarket = 'crypto_market'

class UnknownNotificationPayload(LongshotModel):
    def __init__(self) -> None: ...

class NotificationResponse(LongshotModel):
    seq: int
    id: str
    notification_type: str
    category: str
    title: str
    body: str
    icon: str
    payload: NotificationPayload
    created_at_ms: int
    read_at_ms: Optional[int]
    image_url: Optional[str]
    def __init__(self, *, seq: int, id: str, notification_type: str, category: str, title: str, body: str, icon: str, payload: NotificationPayload, created_at_ms: int, read_at_ms: Optional[int] = ..., image_url: Optional[str] = ...) -> None: ...

class NotificationsResponse(LongshotModel):
    notifications: List[NotificationResponse]
    next_cursor: Optional[str]
    unread_count: int
    def __init__(self, *, notifications: List[NotificationResponse], next_cursor: Optional[str] = ..., unread_count: int) -> None: ...

class NotificationMutationResponse(LongshotModel):
    notification: NotificationResponse
    unread_count: int
    def __init__(self, *, notification: NotificationResponse, unread_count: int) -> None: ...

class NotificationBulkMutationResponse(LongshotModel):
    updated_count: int
    unread_count: int
    def __init__(self, *, updated_count: int, unread_count: int) -> None: ...

class PoolImageRawBytes:
    value: bytes
    def __init__(self, value: bytes = ...) -> None: ...
    def __post_init__(self) -> None:
        ...
    def as_bytes(self) -> bytes:
        ...
    def __bytes__(self) -> bytes:
        ...

class PortfolioIntegrityErrorResponse(LongshotModel):
    position_id: str
    leg_index: Optional[int]
    code: str
    message: str
    def __init__(self, *, position_id: str, leg_index: Optional[int] = ..., code: str, message: str) -> None: ...

class PortfolioStatsResponse(LongshotModel):
    total_positions: int
    open_positions: int
    wins: int
    losses: int
    win_rate_pct: float
    total_pnl_micros: int
    def __init__(self, *, total_positions: int, open_positions: int, wins: int, losses: int, win_rate_pct: float, total_pnl_micros: int) -> None: ...

class PnlHistoryQueryParseError(RustStringEnum):
    InvalidWindowRange = 'InvalidWindowRange'

class PnlHistoryQuery(LongshotModel):
    from_: Optional[int]
    to: Optional[int]
    def __init__(self, *, from_: Optional[int] = ..., to: Optional[int] = ...) -> None: ...

class PnlEventResponse(LongshotModel):
    source: str
    resolved_at_ms: int
    position_id: Optional[str]
    contest_id: Optional[str]
    pnl_micros: int
    cumulative_micros: int
    def __init__(self, *, source: str, resolved_at_ms: int, position_id: Optional[str] = ..., contest_id: Optional[str] = ..., pnl_micros: int, cumulative_micros: int) -> None: ...

class PnlHistoryResponse(LongshotModel):
    events: List[PnlEventResponse]
    def __init__(self, *, events: List[PnlEventResponse]) -> None: ...

class FantasyEntriesQuery(LongshotModel):
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class PortfolioFantasyEntryResponse(LongshotModel):
    contest_id: str
    title: str
    category: str
    status: str
    game_type: ContestGameTypeResponse
    survivor_round_count: Optional[int]
    current_game_index: Optional[int]
    bet_amount_micros: int
    protocol_prize_pool_micros: int
    total_pot_micros: int
    entries_filled: int
    entry_cap: int
    entry_opens_at_ms: Optional[int]
    betting_closes_ms: int
    live_ends_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    joined_at_ms: int
    entry_index: int
    open_leg_count: int
    resolved_win_count: int
    rank: Optional[int]
    payout_micros: Optional[int]
    net_payout_micros: Optional[int]
    refunded: Optional[bool]
    pnl_micros: Optional[int]
    image_url: Optional[str]
    survivor: Optional[SurvivorEntryStateResponse]
    selection_count: int
    survivor_voided_round_count: Optional[int]
    betting_opens_ms: Optional[int]
    def __init__(self, *, contest_id: str, title: str, category: str, status: str, game_type: ContestGameTypeResponse, survivor_round_count: Optional[int] = ..., current_game_index: Optional[int] = ..., bet_amount_micros: int, protocol_prize_pool_micros: int, total_pot_micros: int, entries_filled: int, entry_cap: int, entry_opens_at_ms: Optional[int] = ..., betting_closes_ms: int, live_ends_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., joined_at_ms: int, entry_index: int, open_leg_count: int, resolved_win_count: int, rank: Optional[int] = ..., payout_micros: Optional[int], net_payout_micros: Optional[int], refunded: Optional[bool] = ..., pnl_micros: Optional[int], image_url: Optional[str] = ..., survivor: Optional[SurvivorEntryStateResponse] = ..., selection_count: int, survivor_voided_round_count: Optional[int] = ..., betting_opens_ms: Optional[int] = ...) -> None: ...

class PortfolioFantasyEntriesResponse(LongshotModel):
    entries: List[PortfolioFantasyEntryResponse]
    next_cursor: Optional[str]
    def __init__(self, *, entries: List[PortfolioFantasyEntryResponse], next_cursor: Optional[str] = ...) -> None: ...

class PositionsQuery(LongshotModel):
    status: Optional[str]
    sort: Optional[str]
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, status: Optional[str] = ..., sort: Optional[str] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class PositionStatusQueryParam(RustStringEnum):
    Open = 'open'
    Won = 'won'
    Lost = 'lost'
    Voided = 'voided'

class PositionSortQueryParam(RustStringEnum):
    DateDesc = 'date_desc'
    DateAsc = 'date_asc'
    PnlDesc = 'pnl_desc'
    PnlAsc = 'pnl_asc'

class CursorParseError(RustStringEnum):
    InvalidFormat = 'InvalidFormat'
    InvalidValue = 'InvalidValue'
    ValueOutOfRange = 'ValueOutOfRange'
    InvalidPositionId = 'InvalidPositionId'

class PositionQueryParseError(RustStringEnum):
    InvalidStatus = 'InvalidStatus'
    InvalidSort = 'InvalidSort'

class PositionSummary(LongshotModel):
    id: str
    wager_micros: int
    app_token_wager_micros: Optional[int]
    refunded_app_token_micros: Optional[int]
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    has_binary_event_leg: bool
    market_types: List[MarketType]
    def __init__(self, *, id: str, wager_micros: int, app_token_wager_micros: Optional[int] = ..., refunded_app_token_micros: Optional[int], payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., has_binary_event_leg: bool, market_types: List[MarketType]) -> None: ...

class PositionsListResponse(LongshotModel):
    positions: List[PositionSummary]
    next_cursor: Optional[str]
    partial: bool
    errors: Optional[List[PortfolioIntegrityErrorResponse]]
    def __init__(self, *, positions: List[PositionSummary], next_cursor: Optional[str] = ..., partial: bool, errors: Optional[List[PortfolioIntegrityErrorResponse]] = ...) -> None: ...

class ActivePositionStatus(RustStringEnum):
    Pending = 'pending'
    Open = 'open'

class PositionRole(RustStringEnum):
    Taker = 'taker'
    Maker = 'maker'

class ActivePosition(LongshotModel):
    position_id: PositionId
    status: ActivePositionStatus
    role: PositionRole
    taker_address: Optional[Address]
    wager_micros: int
    app_token_wager_micros: Optional[int]
    payout_micros: int
    legs: List[LegDetail]
    def __init__(self, *, position_id: PositionId, status: ActivePositionStatus, role: PositionRole, taker_address: Optional[Address] = ..., wager_micros: int, app_token_wager_micros: Optional[int] = ..., payout_micros: int, legs: List[LegDetail]) -> None: ...

class ActivePositionsResponse(LongshotModel):
    positions: List[ActivePosition]
    def __init__(self, *, positions: List[ActivePosition]) -> None: ...

class LegDetail(LongshotModel):
    leg_index: int
    market_id: int
    market_type: Optional[MarketType]
    label: Optional[str]
    asset: Optional[str]
    direction: str
    duration_secs: Optional[int]
    outcome: str
    window_start_ms: Optional[int]
    resolution_time_ms: int
    def __init__(self, *, leg_index: int, market_id: int, market_type: Optional[MarketType] = ..., label: Optional[str] = ..., asset: Optional[str] = ..., direction: str, duration_secs: Optional[int] = ..., outcome: str, window_start_ms: Optional[int] = ..., resolution_time_ms: int) -> None: ...

class PositionDetailResponse(LongshotModel):
    id: str
    wager_micros: int
    app_token_wager_micros: Optional[int]
    refunded_app_token_micros: Optional[int]
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    legs: List[LegDetail]
    def __init__(self, *, id: str, wager_micros: int, app_token_wager_micros: Optional[int] = ..., refunded_app_token_micros: Optional[int], payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., legs: List[LegDetail]) -> None: ...

class PreferencesResponse(LongshotModel):
    notifications_enabled: bool
    quote_tolerance: QuoteTolerancePreference
    anonymous_mode_enabled: bool
    def __init__(self, *, notifications_enabled: bool, quote_tolerance: QuoteTolerancePreference, anonymous_mode_enabled: bool) -> None: ...

class QuoteTolerancePreference(RustStringEnum):
    Strict = 'strict'
    Normal = 'normal'
    Lenient = 'lenient'

class UpdatePreferencesRequest(LongshotModel):
    notifications_enabled: Optional[bool]
    quote_tolerance: Optional[QuoteTolerancePreference]
    anonymous_mode_enabled: Optional[bool]
    def __init__(self, *, notifications_enabled: Optional[bool] = ..., quote_tolerance: Optional[QuoteTolerancePreference] = ..., anonymous_mode_enabled: Optional[bool] = ...) -> None: ...

class PrimaryLegIdentityResponse(LongshotModel):
    market_type: MarketType
    market_id: int
    label: str
    asset: Optional[str]
    duration_secs: Optional[int]
    duration_label: Optional[str]
    def __init__(self, *, market_type: MarketType, market_id: int, label: str, asset: Optional[str] = ..., duration_secs: Optional[int] = ..., duration_label: Optional[str] = ...) -> None: ...

class CheckHandleQuery(LongshotModel):
    handle: str
    def __init__(self, *, handle: str) -> None: ...

class ProfileResponse(LongshotModel):
    handle: str
    display_name: str
    avatar_seed: int
    email: Optional[str]
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    created_at_ms: int
    updated_at_ms: int
    referral_code: Optional[str]
    def __init__(self, *, handle: str, display_name: str, avatar_seed: int, email: Optional[str] = ..., x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., created_at_ms: int, updated_at_ms: int, referral_code: Optional[str] = ...) -> None: ...

class PublicProfileResponse(LongshotModel):
    handle: str
    display_name: str
    avatar_seed: int
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    created_at_ms: int
    stats: PublicProfileStatsResponse
    top_ten_finishes: int
    follower_count: int
    following_count: int
    def __init__(self, *, handle: str, display_name: str, avatar_seed: int, x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., created_at_ms: int, stats: PublicProfileStatsResponse, top_ten_finishes: int, follower_count: int, following_count: int) -> None: ...

class PublicProfileStatsResponse(LongshotModel):
    total_positions: int
    open_positions: int
    wins: int
    losses: int
    win_rate_pct: float
    total_pnl_micros: int
    def __init__(self, *, total_positions: int, open_positions: int, wins: int, losses: int, win_rate_pct: float, total_pnl_micros: int) -> None: ...

class PublicProfilePnlEventResponse(LongshotModel):
    source: str
    resolved_at_ms: int
    position_id: Optional[str]
    contest_id: Optional[str]
    pnl_micros: int
    cumulative_micros: int
    def __init__(self, *, source: str, resolved_at_ms: int, position_id: Optional[str] = ..., contest_id: Optional[str] = ..., pnl_micros: int, cumulative_micros: int) -> None: ...

class PublicProfilePnlHistoryResponse(LongshotModel):
    events: List[PublicProfilePnlEventResponse]
    def __init__(self, *, events: List[PublicProfilePnlEventResponse]) -> None: ...

class PublicProfileFantasyEntryResponse(LongshotModel):
    contest_id: str
    title: str
    category: str
    status: str
    game_type: ContestGameTypeResponse
    survivor_round_count: Optional[int]
    current_game_index: Optional[int]
    bet_amount_micros: int
    protocol_prize_pool_micros: int
    total_pot_micros: int
    entries_filled: int
    entry_cap: int
    entry_opens_at_ms: Optional[int]
    betting_closes_ms: int
    live_ends_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    joined_at_ms: int
    entry_index: int
    open_leg_count: int
    resolved_win_count: int
    rank: Optional[int]
    payout_micros: Optional[int]
    net_payout_micros: Optional[int]
    refunded: Optional[bool]
    pnl_micros: Optional[int]
    image_url: Optional[str]
    survivor: Optional[SurvivorEntryStateResponse]
    selection_count: int
    survivor_voided_round_count: Optional[int]
    betting_opens_ms: Optional[int]
    def __init__(self, *, contest_id: str, title: str, category: str, status: str, game_type: ContestGameTypeResponse, survivor_round_count: Optional[int] = ..., current_game_index: Optional[int] = ..., bet_amount_micros: int, protocol_prize_pool_micros: int, total_pot_micros: int, entries_filled: int, entry_cap: int, entry_opens_at_ms: Optional[int] = ..., betting_closes_ms: int, live_ends_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., joined_at_ms: int, entry_index: int, open_leg_count: int, resolved_win_count: int, rank: Optional[int] = ..., payout_micros: Optional[int], net_payout_micros: Optional[int], refunded: Optional[bool] = ..., pnl_micros: Optional[int], image_url: Optional[str] = ..., survivor: Optional[SurvivorEntryStateResponse] = ..., selection_count: int, survivor_voided_round_count: Optional[int] = ..., betting_opens_ms: Optional[int] = ...) -> None: ...

class PublicProfileFantasyEntriesResponse(LongshotModel):
    entries: List[PublicProfileFantasyEntryResponse]
    next_cursor: Optional[str]
    def __init__(self, *, entries: List[PublicProfileFantasyEntryResponse], next_cursor: Optional[str] = ...) -> None: ...

class PublicProfileContestOwnerEntryVisibilityResponse(RustStringEnum):
    HiddenWhileBettingOpen = 'hidden_while_betting_open'
    Visible = 'visible'

class PublicProfileContestOwnerResponse(LongshotModel):
    joined: bool
    entry_visibility: PublicProfileContestOwnerEntryVisibilityResponse
    entries: List[ContestUserEntryResponse]
    def __init__(self, *, joined: bool, entry_visibility: PublicProfileContestOwnerEntryVisibilityResponse, entries: List[ContestUserEntryResponse]) -> None: ...

class PublicProfileContestDetailResponse(LongshotModel):
    contest: PublicContestDetailResponse
    profile_owner: PublicProfileContestOwnerResponse
    def __init__(self, *, contest: PublicContestDetailResponse, profile_owner: PublicProfileContestOwnerResponse) -> None: ...

class PublicProfilePositionSummaryResponse(LongshotModel):
    id: str
    wager_micros: int
    app_token_wager_micros: int
    refunded_app_token_micros: Optional[int]
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    has_binary_event_leg: bool
    market_types: List[MarketType]
    def __init__(self, *, id: str, wager_micros: int, app_token_wager_micros: int, refunded_app_token_micros: Optional[int], payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., has_binary_event_leg: bool, market_types: List[MarketType]) -> None: ...

class PublicProfilePositionsResponse(LongshotModel):
    positions: List[PublicProfilePositionSummaryResponse]
    next_cursor: Optional[str]
    def __init__(self, *, positions: List[PublicProfilePositionSummaryResponse], next_cursor: Optional[str] = ...) -> None: ...

class PublicProfilePositionDetailResponse(LongshotModel):
    id: str
    wager_micros: int
    app_token_wager_micros: int
    refunded_app_token_micros: Optional[int]
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    legs: List[LegDetail]
    def __init__(self, *, id: str, wager_micros: int, app_token_wager_micros: int, refunded_app_token_micros: Optional[int], payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., legs: List[LegDetail]) -> None: ...

class UpdateProfileRequest(LongshotModel):
    handle: Optional[str]
    display_name: Optional[str]
    def __init__(self, *, handle: Optional[str] = ..., display_name: Optional[str] = ...) -> None: ...

class SyncXProfileRequest(LongshotModel):
    privy_token: str
    def __init__(self, *, privy_token: str) -> None: ...

class CheckHandleResponse(LongshotModel):
    available: bool
    reason: Optional[str]
    def __init__(self, *, available: bool, reason: Optional[str] = ...) -> None: ...

class CreateSessionRequest(LongshotModel):
    privy_token: str
    auth_wallet_address: Optional[str]
    referral_code: Optional[str]
    def __init__(self, *, privy_token: str, auth_wallet_address: Optional[str] = ..., referral_code: Optional[str] = ...) -> None: ...

class WalletAuthRequest(LongshotModel):
    address: str
    signature: str
    signed_at_ms: int
    referral_code: Optional[str]
    def __init__(self, *, address: str, signature: str, signed_at_ms: int, referral_code: Optional[str] = ...) -> None: ...

class ChatPostMessageRequest(LongshotModel):
    body: str
    chat_id: Optional[str]
    parent: Optional[str]
    def __init__(self, *, body: str, chat_id: Optional[str] = ..., parent: Optional[str] = ...) -> None: ...

class ChatEditMessageRequest(LongshotModel):
    chat_id: Optional[str]
    message_id: str
    body: str
    def __init__(self, *, chat_id: Optional[str] = ..., message_id: str, body: str) -> None: ...

class ChatEmojiReactRequest(LongshotModel):
    chat_id: Optional[str]
    message_id: str
    emoji_code: str
    def __init__(self, *, chat_id: Optional[str] = ..., message_id: str, emoji_code: str) -> None: ...

class ChatStreamQuery(LongshotModel):
    chat_id: Optional[str]
    def __init__(self, *, chat_id: Optional[str] = ...) -> None: ...

class ChatMentionCandidatesQuery(LongshotModel):
    chat_id: str
    def __init__(self, *, chat_id: str) -> None: ...

class ChatRecentMessagesQuery(LongshotModel):
    chat_id: Optional[str]
    limit: Optional[int]
    before: Optional[str]
    def __init__(self, *, chat_id: Optional[str] = ..., limit: Optional[int] = ..., before: Optional[str] = ...) -> None: ...

class UserSetReferrerRequest(LongshotModel):
    referral_code: str
    def __init__(self, *, referral_code: str) -> None: ...

class UserCreateReferralCodeRequest(LongshotModel):
    code: str
    def __init__(self, *, code: str) -> None: ...

class PlaceContestBetSelectionRequest(LongshotModel):
    market_id: int
    direction: str
    def __init__(self, *, market_id: int, direction: str) -> None: ...

class PlaceContestBetRequest(LongshotModel):
    contest_id: str
    use_app_tokens: bool
    entry_index: Optional[int]
    bets: List[PlaceContestBetSelectionRequest]
    roster_picks: Optional[List[PlaceRosterPickRequest]]
    tiebreaker_guess: Optional[int]
    def __init__(self, *, contest_id: str, use_app_tokens: bool, entry_index: Optional[int] = ..., bets: List[PlaceContestBetSelectionRequest], roster_picks: Optional[List[PlaceRosterPickRequest]] = ..., tiebreaker_guess: Optional[int] = ...) -> None: ...

class UserDepositRequest(LongshotModel):
    amount_micros: int
    idempotency_key: str
    def __init__(self, *, amount_micros: int, idempotency_key: str) -> None: ...

class UserDepositVaultRequest(LongshotModel):
    vault_id: str
    amount_micros: int
    idempotency_key: str
    def __init__(self, *, vault_id: str, amount_micros: int, idempotency_key: str) -> None: ...

class UserWithdrawParams(LongshotModel):
    amount_micros: int
    destination_address: Optional[str]
    idempotency_key: str
    def __init__(self, *, amount_micros: int, destination_address: Optional[str] = ..., idempotency_key: str) -> None: ...

class WithdrawalAuthorization(RustTaggedUnion):
    @classmethod
    def privy_token(cls, payload: Any=None, **fields: Any) -> WithdrawalAuthorization:
        ...
    @classmethod
    def wallet_signature(cls, payload: Any=None, **fields: Any) -> WithdrawalAuthorization:
        ...

class UserWithdrawRequest(LongshotModel):
    withdraw_params: UserWithdrawParams
    authorization: WithdrawalAuthorization
    def __init__(self, *, withdraw_params: UserWithdrawParams, authorization: WithdrawalAuthorization) -> None: ...

def build_wallet_authentication_message(domain: str, auth_address: Address | str, signed_at_ms: int) -> str:
    ...

def build_wallet_withdrawal_authorization_message(domain: str, chain_id: int, auth_address: Address | str, destination_address: Address | str, amount_micros: int, idempotency_key: UUID | str, signed_at_ms: int) -> str:
    ...

def encode_wallet_signature(signature: bytes) -> str:
    ...

class VaultWithdrawalAmountRequest(RustTaggedUnion):
    @classmethod
    def full(cls, payload: Any=None, **fields: Any) -> VaultWithdrawalAmountRequest:
        ...
    @classmethod
    def partial(cls, payload: Any=None, **fields: Any) -> VaultWithdrawalAmountRequest:
        ...

class OrderLegJson(LongshotModel):
    market_id: int
    direction: str
    def __init__(self, *, market_id: int, direction: str) -> None: ...
    def parse(self: OrderLegJson) -> ParsedOrderLeg:
        ...
    @classmethod
    def from_order_leg(cls, leg: OrderLeg) -> OrderLegJson:
        ...

class SignedOrderJson(LongshotModel):
    user: str
    wager_micros: int
    min_odds: float
    legs: List[OrderLegJson]
    nonce: int
    expires_at_ms: int
    order_type: Optional[int]
    shield_on: bool
    signature: str
    def __init__(self, *, user: str, wager_micros: int, min_odds: float, legs: List[OrderLegJson], nonce: int, expires_at_ms: int, order_type: Optional[int] = ..., shield_on: bool, signature: str) -> None: ...
    @classmethod
    def from_signed_order(cls, order: SignedOrder) -> SignedOrderJson:
        ...
    def to_signed_order(self: SignedOrderJson) -> SignedOrder:
        ...

class CreateRfqRequest(LongshotModel):
    order: SignedOrderJson
    use_app_tokens: bool
    def __init__(self, *, order: SignedOrderJson, use_app_tokens: bool) -> None: ...
    @classmethod
    def from_signed_order(cls, order: SignedOrder, use_app_tokens: bool) -> CreateRfqRequest:
        ...

class CommunityPickMode(RustStringEnum):
    Tail = 'tail'
    Fade = 'fade'

class CommunityPickRequest(LongshotModel):
    source_position_id: PositionId
    mode: CommunityPickMode
    def __init__(self, *, source_position_id: PositionId, mode: CommunityPickMode) -> None: ...

class UnsignedRfqOrderRequest(LongshotModel):
    wager_micros: int
    min_odds: float
    legs: List[OrderLegJson]
    order_type: Optional[int]
    shield_on: bool
    idempotency_key: str
    def __init__(self, *, wager_micros: int, min_odds: float, legs: List[OrderLegJson], order_type: Optional[int] = ..., shield_on: bool, idempotency_key: str) -> None: ...
    def parse_idempotency_key(self: UnsignedRfqOrderRequest) -> UUID:
        ...
    def into_signed_order_for_session(self: UnsignedRfqOrderRequest, user: Address, nonce: int, expires_at_ms: int) -> SignedOrder:
        ...

class CreateUnsignedRfqRequest(LongshotModel):
    privy_token: str
    use_app_tokens: bool
    rfq_params: UnsignedRfqOrderRequest
    community_pick: Optional[CommunityPickRequest]
    def __init__(self, *, privy_token: str, use_app_tokens: bool, rfq_params: UnsignedRfqOrderRequest, community_pick: Optional[CommunityPickRequest] = ...) -> None: ...

class ParsedOrderLeg(LongshotModel):
    market_id: Optional[MarketId]
    direction: Optional[Direction]
    def __init__(self, *, market_id: Optional[MarketId] = ..., direction: Optional[Direction] = ...) -> None: ...

class OrderLegParseError(RustTaggedUnion):
    @classmethod
    def invalid_market_id(cls, payload: Any=None, **fields: Any) -> OrderLegParseError:
        ...
    @classmethod
    def invalid_direction(cls, payload: Any=None, **fields: Any) -> OrderLegParseError:
        ...

class RfqOrderJsonError(RustTaggedUnion):
    @classmethod
    def invalid_address(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_min_odds(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def missing_legs(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def too_many_legs(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_order_type(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_signature_format(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_idempotency_key(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_leg_market_id(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_leg_direction(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...

class AccessResponse(LongshotModel):
    position_opening_allowed: bool
    reason_code: Optional[str]
    def __init__(self, *, position_opening_allowed: bool, reason_code: Optional[str] = ...) -> None: ...

class SessionResponse(LongshotModel):
    session_token: str
    address: str
    auth_wallet_address: str
    deposit_address: Optional[str]
    deposit_chain_id: Optional[int]
    user_id: str
    expires_at: int
    account_created: Optional[bool]
    onboarding_completed: Optional[bool]
    def __init__(self, *, session_token: str, address: str, auth_wallet_address: str, deposit_address: Optional[str] = ..., deposit_chain_id: Optional[int] = ..., user_id: str, expires_at: int, account_created: Optional[bool] = ..., onboarding_completed: Optional[bool] = ...) -> None: ...
    def __repr__(self) -> str:
        ...

class RfqStatus(RustStringEnum):
    Pending = 'pending'
    Finalizing = 'finalizing'
    Completed = 'completed'
    Failed = 'failed'
    Cancelled = 'cancelled'
    Timeout = 'timeout'

class RfqResponse(LongshotModel):
    request_id: UUID
    status: RfqStatus
    odds: Optional[float]
    payout_micros: Optional[int]
    error: Optional[str]
    quotes_received: int
    def __init__(self, *, request_id: UUID, status: RfqStatus, odds: Optional[float] = ..., payout_micros: Optional[int] = ..., error: Optional[str] = ..., quotes_received: int) -> None: ...

class CancelResponse(LongshotModel):
    request_id: str
    cancelled: bool
    message: str
    def __init__(self, *, request_id: str, cancelled: bool, message: str) -> None: ...

class UserDepositResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    tx_hash: str
    def __init__(self, *, amount_micros: int, operation_id: UUID, tx_hash: str) -> None: ...

class UserDepositWalletResponse(LongshotModel):
    address: str
    chain_id: Optional[int]
    token_symbol: str
    token_decimals: int
    def __init__(self, *, address: str, chain_id: Optional[int] = ..., token_symbol: str, token_decimals: int) -> None: ...

class UserDepositVaultResponse(LongshotModel):
    def __init__(self) -> None: ...

class UserWithdrawResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    destination_address: Optional[str]
    tx_hash: str
    def __init__(self, *, amount_micros: int, operation_id: UUID, destination_address: Optional[str] = ..., tx_hash: str) -> None: ...

class BalanceOperationStatus(RustStringEnum):
    Pending = 'pending'
    Failed = 'failed'
    Success = 'success'
    Recovering = 'recovering'

class BalanceOperationStatusResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    status: BalanceOperationStatus
    wallet_address: Optional[str]
    def __init__(self, *, amount_micros: int, operation_id: UUID, status: BalanceOperationStatus, wallet_address: Optional[str] = ...) -> None: ...

class DepositOperationResponse(RustTaggedUnion):
    @classmethod
    def completed(cls, payload: Any=None, **fields: Any) -> DepositOperationResponse:
        ...
    @classmethod
    def operation_status(cls, payload: Any=None, **fields: Any) -> DepositOperationResponse:
        ...

class WithdrawOperationResponse(RustTaggedUnion):
    @classmethod
    def completed(cls, payload: Any=None, **fields: Any) -> WithdrawOperationResponse:
        ...
    @classmethod
    def operation_status(cls, payload: Any=None, **fields: Any) -> WithdrawOperationResponse:
        ...

class UserRequestWithdrawalVaultResponse(LongshotModel):
    queued: bool
    def __init__(self, *, queued: bool) -> None: ...

class VaultClaimFeesResponse(LongshotModel):
    claimed_micros: int
    def __init__(self, *, claimed_micros: int) -> None: ...

class VaultWithdrawalAmountResponse(RustTaggedUnion):
    @classmethod
    def full(cls, payload: Any=None, **fields: Any) -> VaultWithdrawalAmountResponse:
        ...
    @classmethod
    def partial(cls, payload: Any=None, **fields: Any) -> VaultWithdrawalAmountResponse:
        ...

class PendingVaultWithdrawalResponse(LongshotModel):
    user_id: str
    requested_amount: VaultWithdrawalAmountResponse
    withdrawal_time_ms: int
    def __init__(self, *, user_id: str, requested_amount: VaultWithdrawalAmountResponse, withdrawal_time_ms: int) -> None: ...

class VaultWithdrawalQueueResponse(LongshotModel):
    withdrawal_queue: List[PendingVaultWithdrawalResponse]
    def __init__(self, *, withdrawal_queue: List[PendingVaultWithdrawalResponse]) -> None: ...

class VaultLiquidityProviderResponse(LongshotModel):
    user_id: str
    liquidity_micros: int
    def __init__(self, *, user_id: str, liquidity_micros: int) -> None: ...

class PositionVaultResponse(LongshotModel):
    total_deposit_micros: int
    liquidity_providers: List[VaultLiquidityProviderResponse]
    def __init__(self, *, total_deposit_micros: int, liquidity_providers: List[VaultLiquidityProviderResponse]) -> None: ...

class VaultPositionVaultResponse(LongshotModel):
    position_vault: PositionVaultResponse
    def __init__(self, *, position_vault: PositionVaultResponse) -> None: ...

class VaultConfigsResponse(LongshotModel):
    max_position_value_bps: int
    min_deposit_age_ms: int
    withdrawal_window_ms: int
    binary_event_utilization_cap_bps: int
    price_strike_utilization_cap_bps: int
    vault_manager_fee_bps: int
    external_deposits_enabled: bool
    making_enabled: bool
    taking_enabled: bool
    fee_receiver: Optional[str]
    def __init__(self, *, max_position_value_bps: int, min_deposit_age_ms: int, withdrawal_window_ms: int, binary_event_utilization_cap_bps: int, price_strike_utilization_cap_bps: int, vault_manager_fee_bps: int, external_deposits_enabled: bool, making_enabled: bool, taking_enabled: bool, fee_receiver: Optional[str] = ...) -> None: ...

class VaultAmountResponse(LongshotModel):
    total_deposit_micros: int
    def __init__(self, *, total_deposit_micros: int) -> None: ...

class VaultAggregateAmountResponse(LongshotModel):
    amount_micros: int
    def __init__(self, *, amount_micros: int) -> None: ...

class VaultResponse(LongshotModel):
    configs: VaultConfigsResponse
    unallocated: VaultAmountResponse
    allocated: VaultAmountResponse
    binary_event_allocation: VaultAggregateAmountResponse
    price_strike_allocation: VaultAggregateAmountResponse
    total_fees: VaultAggregateAmountResponse
    unclaimed_fees: VaultAggregateAmountResponse
    def __init__(self, *, configs: VaultConfigsResponse, unallocated: VaultAmountResponse, allocated: VaultAmountResponse, binary_event_allocation: VaultAggregateAmountResponse, price_strike_allocation: VaultAggregateAmountResponse, total_fees: VaultAggregateAmountResponse, unclaimed_fees: VaultAggregateAmountResponse) -> None: ...

class VaultStatsResponse(LongshotModel):
    tvl_micros: int
    allocated_micros: int
    unallocated_micros: int
    all_time_pnl_micros: int
    trading_volume_micros: int
    past_month_apr_bps: int
    all_time_apr_bps: int
    def __init__(self, *, tvl_micros: int, allocated_micros: int, unallocated_micros: int, all_time_pnl_micros: int, trading_volume_micros: int, past_month_apr_bps: int, all_time_apr_bps: int) -> None: ...

class VaultPnlHistoryPoint(LongshotModel):
    t_ms: int
    value_micros: int
    def __init__(self, *, t_ms: int, value_micros: int) -> None: ...

class VaultPnlHistoryResponse(LongshotModel):
    series: List[VaultPnlHistoryPoint]
    def __init__(self, *, series: List[VaultPnlHistoryPoint]) -> None: ...

class VaultPositionResponse(LongshotModel):
    position_id: str
    legs_summary: str
    wager_micros: int
    multiplier_bps: int
    potential_payout_micros: int
    mark_value_micros: int
    created_at_ms: int
    resolved_at_ms: Optional[int]
    def __init__(self, *, position_id: str, legs_summary: str, wager_micros: int, multiplier_bps: int, potential_payout_micros: int, mark_value_micros: int, created_at_ms: int, resolved_at_ms: Optional[int] = ...) -> None: ...

class VaultPositionsResponse(LongshotModel):
    items: List[VaultPositionResponse]
    next_cursor: Optional[str]
    def __init__(self, *, items: List[VaultPositionResponse], next_cursor: Optional[str] = ...) -> None: ...

class PublicVaultPositionDetailResponse(LongshotModel):
    id: str
    wager_micros: int
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    legs: List[LegDetail]
    def __init__(self, *, id: str, wager_micros: int, payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., legs: List[LegDetail]) -> None: ...

class PublicVaultActivityEventResponse(LongshotModel):
    event_type: str
    user_id: str
    user_display_name: str
    user_handle: Optional[str]
    user_avatar_seed: Optional[int]
    user_x_avatar_url: Optional[str]
    amount_micros: int
    position_id: Optional[str]
    event_at_ms: int
    def __init__(self, *, event_type: str, user_id: str, user_display_name: str, user_handle: Optional[str] = ..., user_avatar_seed: Optional[int] = ..., user_x_avatar_url: Optional[str] = ..., amount_micros: int, position_id: Optional[str] = ..., event_at_ms: int) -> None: ...

class PublicVaultActivityResponse(LongshotModel):
    items: List[PublicVaultActivityEventResponse]
    next_cursor: Optional[str]
    def __init__(self, *, items: List[PublicVaultActivityEventResponse], next_cursor: Optional[str] = ...) -> None: ...

class PublicVaultContributorLeaderboardRowResponse(LongshotModel):
    user_id: str
    user_display_name: str
    user_handle: Optional[str]
    user_avatar_seed: Optional[int]
    user_x_avatar_url: Optional[str]
    total_deposits_micros: int
    all_time_earned_micros: int
    all_time_pnl_micros: int
    unrealized_pnl_micros: int
    def __init__(self, *, user_id: str, user_display_name: str, user_handle: Optional[str] = ..., user_avatar_seed: Optional[int] = ..., user_x_avatar_url: Optional[str] = ..., total_deposits_micros: int, all_time_earned_micros: int, all_time_pnl_micros: int, unrealized_pnl_micros: int) -> None: ...

class PublicVaultContributorLeaderboardResponse(LongshotModel):
    items: List[PublicVaultContributorLeaderboardRowResponse]
    next_cursor: Optional[str]
    def __init__(self, *, items: List[PublicVaultContributorLeaderboardRowResponse], next_cursor: Optional[str] = ...) -> None: ...

class VaultUserPerformanceResponse(LongshotModel):
    current_balance_micros: int
    unallocated_micros: int
    allocated_micros: int
    lifetime_deposits_micros: int
    all_time_earned_micros: int
    all_time_pnl_micros: int
    unrealized_pnl_micros: int
    latest_deposit_time_ms: Optional[int]
    pending_withdrawal: Optional[PendingVaultWithdrawalResponse]
    def __init__(self, *, current_balance_micros: int, unallocated_micros: int, allocated_micros: int, lifetime_deposits_micros: int, all_time_earned_micros: int, all_time_pnl_micros: int, unrealized_pnl_micros: int, latest_deposit_time_ms: Optional[int] = ..., pending_withdrawal: Optional[PendingVaultWithdrawalResponse] = ...) -> None: ...

class AvailableBalanceResponse(LongshotModel):
    available_micros: int
    def __init__(self, *, available_micros: int) -> None: ...

class ReservedBalanceResponse(LongshotModel):
    reserved_micros: int
    def __init__(self, *, reserved_micros: int) -> None: ...

class UserTransactionCategory(RustStringEnum):
    Deposit = 'deposit'
    Withdrawal = 'withdrawal'
    Credits = 'credits'
    Market = 'market'
    Contest = 'contest'

class UserTransactionStatus(RustStringEnum):
    Completed = 'completed'
    Pending = 'pending'
    Failed = 'failed'
    Expired = 'expired'
    Entered = 'entered'
    Won = 'won'

class UserTransactionUnit(RustStringEnum):
    Usdc = 'usdc'
    Credits = 'credits'

class UserTransactionFunding(RustStringEnum):
    Cash = 'cash'
    Credits = 'credits'
    CashAndCredits = 'cash_and_credits'

class UserTransactionResponse(LongshotModel):
    id: str
    category: UserTransactionCategory
    title: str
    detail: Optional[str]
    status: UserTransactionStatus
    occurred_at_ms: int
    amount_micros: int
    unit: UserTransactionUnit
    funding: Optional[UserTransactionFunding]
    network: Optional[str]
    wallet_address: Optional[str]
    tx_hash: Optional[str]
    source: Optional[str]
    expires_at_ms: Optional[int]
    reason: Optional[str]
    reference: Optional[str]
    def __init__(self, *, id: str, category: UserTransactionCategory, title: str, detail: Optional[str] = ..., status: UserTransactionStatus, occurred_at_ms: int, amount_micros: int, unit: UserTransactionUnit, funding: Optional[UserTransactionFunding] = ..., network: Optional[str] = ..., wallet_address: Optional[str] = ..., tx_hash: Optional[str] = ..., source: Optional[str] = ..., expires_at_ms: Optional[int] = ..., reason: Optional[str] = ..., reference: Optional[str] = ...) -> None: ...

class UserTransactionsResponse(LongshotModel):
    items: List[UserTransactionResponse]
    next_cursor: Optional[str]
    def __init__(self, *, items: List[UserTransactionResponse], next_cursor: Optional[str] = ...) -> None: ...

class FeeScheduleTier(RustStringEnum):
    Standard = 'standard'
    Silver = 'silver'
    Gold = 'gold'
    Platinum = 'platinum'
    Vip = 'vip'

class TierFeeRate(LongshotModel):
    tier: FeeScheduleTier
    parlay_fee_bps: int
    def __init__(self, *, tier: FeeScheduleTier, parlay_fee_bps: int) -> None: ...

class FeeScheduleResponse(LongshotModel):
    user_tier: FeeScheduleTier
    parlay_fee_bps: int
    spot_fee_bps: int
    bonding_spot_fee_bps: int
    shield_fee_multiplier: int
    tiers: List[TierFeeRate]
    def __init__(self, *, user_tier: FeeScheduleTier, parlay_fee_bps: int, spot_fee_bps: int, bonding_spot_fee_bps: int, shield_fee_multiplier: int, tiers: List[TierFeeRate]) -> None: ...

class PlaceContestBetResponse(LongshotModel):
    contest_id: str
    entry_index: int
    reserved_micros: int
    def __init__(self, *, contest_id: str, entry_index: int, reserved_micros: int) -> None: ...

class ContestCategoryResponse(RustStringEnum):
    Mentions = 'mentions'
    Sports = 'sports'
    Culture = 'culture'

class ContestStatusResponse(RustStringEnum):
    Open = 'open'
    Resolved = 'resolved'
    Voided = 'voided'

class ContestBetTypeResponse(RustTaggedUnion):
    @classmethod
    def num_bets(cls, payload: Any=None, **fields: Any) -> ContestBetTypeResponse:
        ...
    @classmethod
    def bets_per_category(cls, payload: Any=None, **fields: Any) -> ContestBetTypeResponse:
        ...

class ContestGameTypeResponse(RustStringEnum):
    Lineups = 'lineups'
    Survivor = 'survivor'
    Streak = 'streak'
    Outcast = 'outcast'
    Roster = 'roster'

class ContestRosterResponse(LongshotModel):
    tiers: List[ContestRosterTierResponse]
    def __init__(self, *, tiers: List[ContestRosterTierResponse]) -> None: ...

class ContestRosterTierResponse(LongshotModel):
    tier_index: int
    name: str
    selections: List[ContestRosterSelectionResponse]
    def __init__(self, *, tier_index: int, name: str, selections: List[ContestRosterSelectionResponse]) -> None: ...

class ContestRosterSelectionResponse(LongshotModel):
    selection_index: int
    name: str
    image_url: Optional[str]
    avg_points_milli: Optional[int]
    points_milli: int
    final_points_milli: Optional[int]
    live_state: Optional[Any]
    metadata: Optional[Any]
    updated_at_ms: int
    def __init__(self, *, selection_index: int, name: str, image_url: Optional[str] = ..., avg_points_milli: Optional[int] = ..., points_milli: int, final_points_milli: Optional[int] = ..., live_state: Optional[Any] = ..., metadata: Optional[Any] = ..., updated_at_ms: int) -> None: ...

class ContestRosterPickResponse(LongshotModel):
    tier_index: int
    selection_index: int
    def __init__(self, *, tier_index: int, selection_index: int) -> None: ...

class PlaceRosterPickRequest(LongshotModel):
    tier_index: int
    selection_index: int
    def __init__(self, *, tier_index: int, selection_index: int) -> None: ...

class SurvivorPhaseResponse(RustStringEnum):
    Scheduled = 'scheduled'
    PickOpen = 'pick_open'
    PickLocked = 'pick_locked'
    Live = 'live'
    RoundSettled = 'round_settled'
    AwaitingNextRound = 'awaiting_next_round'
    ContestSettled = 'contest_settled'
    Voided = 'voided'

class SurvivorRoundStatusResponse(RustStringEnum):
    Scheduled = 'scheduled'
    PickOpen = 'pick_open'
    PickLocked = 'pick_locked'
    Live = 'live'
    Settled = 'settled'
    Voided = 'voided'

class SurvivorEntryRoundResultResponse(RustStringEnum):
    Pending = 'pending'
    Won = 'won'
    Lost = 'lost'
    Missed = 'missed'
    Voided = 'voided'

class SurvivorEliminationReasonResponse(RustStringEnum):
    IncorrectPick = 'incorrect_pick'
    MissedDeadline = 'missed_deadline'

class ContestDirectionResponse(RustStringEnum):
    Up = 'up'
    Down = 'down'

class ContestLegOutcome(RustStringEnum):
    Pending = 'pending'
    Won = 'won'
    Lost = 'lost'
    Voided = 'voided'

class ContestPerfectSlateResponse(LongshotModel):
    payout_micros: int
    winner_count: int
    def __init__(self, *, payout_micros: int, winner_count: int) -> None: ...

class PublicContestSummaryResponse(LongshotModel):
    contest_id: str
    title: str
    category: ContestCategoryResponse
    status: ContestStatusResponse
    game_type: Optional[ContestGameTypeResponse]
    survivor_awaiting_replacement: Optional[bool]
    survivor_current_game_index: Optional[int]
    bet_amount_micros: int
    protocol_prize_pool_micros: int
    total_pot_micros: int
    prize_pool_growth_starts_after_entries: Optional[int]
    perfect_slate: Optional[ContestPerfectSlateResponse]
    featured_slot: Optional[int]
    entries_filled: int
    entry_cap: int
    entry_opens_at_ms: Optional[int]
    betting_closes_ms: int
    live_ends_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    created_at_ms: int
    image_url: Optional[str]
    def __init__(self, *, contest_id: str, title: str, category: ContestCategoryResponse, status: ContestStatusResponse, game_type: Optional[ContestGameTypeResponse] = ..., survivor_awaiting_replacement: Optional[bool] = ..., survivor_current_game_index: Optional[int] = ..., bet_amount_micros: int, protocol_prize_pool_micros: int, total_pot_micros: int, prize_pool_growth_starts_after_entries: Optional[int] = ..., perfect_slate: Optional[ContestPerfectSlateResponse] = ..., featured_slot: Optional[int] = ..., entries_filled: int, entry_cap: int, entry_opens_at_ms: Optional[int] = ..., betting_closes_ms: int, live_ends_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., created_at_ms: int, image_url: Optional[str] = ...) -> None: ...

class ContestCallerSummaryResponse(LongshotModel):
    joined: bool
    entry_count: Optional[int]
    def __init__(self, *, joined: bool, entry_count: Optional[int] = ...) -> None: ...

class CallerContestSummaryResponse(LongshotModel):
    contest: PublicContestSummaryResponse
    caller: Optional[ContestCallerSummaryResponse]
    def __init__(self, *, contest: PublicContestSummaryResponse, caller: Optional[ContestCallerSummaryResponse] = ...) -> None: ...

class CallerContestsListResponse(LongshotModel):
    contests: List[ContestLobbySummaryResponse]
    next_cursor: Optional[str]
    def __init__(self, *, contests: List[ContestLobbySummaryResponse], next_cursor: Optional[str] = ...) -> None: ...

class ContestMarketResponse(LongshotModel):
    market_id: int
    selection_group: str
    market_type: MarketType
    trading_channels: List[TradingChannel]
    name: str
    image_url: Optional[str]
    description: Optional[str]
    resolution_rules: Optional[str]
    status: MarketStatus
    outcome: Optional[Outcome]
    source: Optional[EventMarketSource]
    betting_closes_at_ms: Optional[int]
    opens_at_ms: Optional[int]
    live_ends_at_ms: Optional[int]
    resolution_time_ms: Optional[int]
    manual_probability_bps: Optional[int]
    manual_live_state: Optional[Any]
    def __init__(self, *, market_id: int, selection_group: str, market_type: MarketType, trading_channels: List[TradingChannel], name: str, image_url: Optional[str] = ..., description: Optional[str] = ..., resolution_rules: Optional[str] = ..., status: MarketStatus, outcome: Optional[Outcome] = ..., source: Optional[EventMarketSource] = ..., betting_closes_at_ms: Optional[int] = ..., opens_at_ms: Optional[int] = ..., live_ends_at_ms: Optional[int] = ..., resolution_time_ms: Optional[int] = ..., manual_probability_bps: Optional[int] = ..., manual_live_state: Optional[Any] = ...) -> None: ...

class ContestUserPickResponse(LongshotModel):
    market_id: int
    direction: ContestDirectionResponse
    outcome: ContestLegOutcome
    def __init__(self, *, market_id: int, direction: ContestDirectionResponse, outcome: ContestLegOutcome) -> None: ...

class SurvivorRoundPicksResponse(RustTaggedUnion):
    @classmethod
    def hidden(cls, payload: Any=None, **fields: Any) -> SurvivorRoundPicksResponse:
        ...
    @classmethod
    def revealed(cls, payload: Any=None, **fields: Any) -> SurvivorRoundPicksResponse:
        ...

class SurvivorMarketPickCountsResponse(LongshotModel):
    market_id: int
    up_count: int
    down_count: int
    def __init__(self, *, market_id: int, up_count: int, down_count: int) -> None: ...

class SurvivorRoundBreakdownResponse(LongshotModel):
    eligible_entry_count: int
    submitted_entry_count: int
    missed_entry_count: int
    markets: List[SurvivorMarketPickCountsResponse]
    def __init__(self, *, eligible_entry_count: int, submitted_entry_count: int, missed_entry_count: int, markets: List[SurvivorMarketPickCountsResponse]) -> None: ...

class SurvivorRoundResponse(LongshotModel):
    game_index: int
    status: SurvivorRoundStatusResponse
    required_pick_count: int
    betting_opens_at_ms: int
    betting_closes_at_ms: int
    resolved_at_ms: Optional[int]
    markets: List[ContestMarketResponse]
    breakdown: Optional[SurvivorRoundBreakdownResponse]
    def __init__(self, *, game_index: int, status: SurvivorRoundStatusResponse, required_pick_count: int, betting_opens_at_ms: int, betting_closes_at_ms: int, resolved_at_ms: Optional[int] = ..., markets: List[ContestMarketResponse], breakdown: Optional[SurvivorRoundBreakdownResponse] = ...) -> None: ...

class SurvivorEntryRoundResponse(LongshotModel):
    game_index: int
    result: SurvivorEntryRoundResultResponse
    picks: SurvivorRoundPicksResponse
    def __init__(self, *, game_index: int, result: SurvivorEntryRoundResultResponse, picks: SurvivorRoundPicksResponse) -> None: ...

class SurvivorEntryStateResponse(RustTaggedUnion):
    @classmethod
    def alive(cls, payload: Any=None, **fields: Any) -> SurvivorEntryStateResponse:
        ...
    @classmethod
    def eliminated(cls, payload: Any=None, **fields: Any) -> SurvivorEntryStateResponse:
        ...
    @classmethod
    def winner(cls, payload: Any=None, **fields: Any) -> SurvivorEntryStateResponse:
        ...
    @classmethod
    def voided(cls, payload: Any=None, **fields: Any) -> SurvivorEntryStateResponse:
        ...

class SurvivorContestResponse(LongshotModel):
    version: int
    round_count: int
    phase: SurvivorPhaseResponse
    current_game_index: int
    next_game_index: Optional[int]
    rounds: List[SurvivorRoundResponse]
    rounds_next_cursor: Optional[int]
    revealed_game_indexes: List[int]
    remaining_survivor_count: int
    def __init__(self, *, version: int, round_count: int, phase: SurvivorPhaseResponse, current_game_index: int, next_game_index: Optional[int] = ..., rounds: List[SurvivorRoundResponse], rounds_next_cursor: Optional[int] = ..., revealed_game_indexes: List[int], remaining_survivor_count: int) -> None: ...

class SurvivorTeamUsageResponse(LongshotModel):
    source_team_id: str
    used_game_index: int
    def __init__(self, *, source_team_id: str, used_game_index: int) -> None: ...

class ContestUserEntryResponse(LongshotModel):
    entry_index: int
    created_at_ms: int
    picks: List[ContestUserPickResponse]
    open_leg_count: int
    resolved_win_count: int
    payout_micros: Optional[int]
    net_payout_micros: Optional[int]
    refunded: Optional[bool]
    rank: Optional[int]
    tiebreaker_guess: Optional[int]
    perfect_slate_won: Optional[bool]
    perfect_slate_payout_micros: Optional[int]
    roster_picks: Optional[List[ContestRosterPickResponse]]
    roster_points_milli: Optional[int]
    survivor: Optional[SurvivorEntryStateResponse]
    survivor_team_usage: Optional[List[SurvivorTeamUsageResponse]]
    def __init__(self, *, entry_index: int, created_at_ms: int, picks: List[ContestUserPickResponse], open_leg_count: int, resolved_win_count: int, payout_micros: Optional[int] = ..., net_payout_micros: Optional[int] = ..., refunded: Optional[bool] = ..., rank: Optional[int] = ..., tiebreaker_guess: Optional[int] = ..., perfect_slate_won: Optional[bool] = ..., perfect_slate_payout_micros: Optional[int] = ..., roster_picks: Optional[List[ContestRosterPickResponse]] = ..., roster_points_milli: Optional[int] = ..., survivor: Optional[SurvivorEntryStateResponse] = ..., survivor_team_usage: Optional[List[SurvivorTeamUsageResponse]] = ...) -> None: ...

class ContestTiebreakerResponse(LongshotModel):
    enabled: bool
    hint: str
    result: Optional[int]
    def __init__(self, *, enabled: bool, hint: str, result: Optional[int] = ...) -> None: ...

class PublicContestDetailResponse(LongshotModel):
    summary: PublicContestSummaryResponse
    max_entries_per_player: Optional[int]
    description: Optional[str]
    bet_type: ContestBetTypeResponse
    winning_split_bps: List[int]
    protocol_winning_split_bps: List[int]
    protocol_prize_pool_pays_app_tokens: bool
    tiebreaker: Optional[ContestTiebreakerResponse]
    markets: List[ContestMarketResponse]
    roster: Optional[ContestRosterResponse]
    survivor: Optional[SurvivorContestResponse]
    def __init__(self, *, summary: PublicContestSummaryResponse, max_entries_per_player: Optional[int] = ..., description: Optional[str] = ..., bet_type: ContestBetTypeResponse, winning_split_bps: List[int], protocol_winning_split_bps: List[int], protocol_prize_pool_pays_app_tokens: bool, tiebreaker: Optional[ContestTiebreakerResponse] = ..., markets: List[ContestMarketResponse], roster: Optional[ContestRosterResponse] = ..., survivor: Optional[SurvivorContestResponse] = ...) -> None: ...

class ContestCallerDetailResponse(LongshotModel):
    joined: bool
    entries: List[ContestUserEntryResponse]
    def __init__(self, *, joined: bool, entries: List[ContestUserEntryResponse]) -> None: ...

class CallerContestDetailResponse(LongshotModel):
    contest: PublicContestDetailResponse
    caller: Optional[ContestCallerDetailResponse]
    def __init__(self, *, contest: PublicContestDetailResponse, caller: Optional[ContestCallerDetailResponse] = ...) -> None: ...

class ContestLeaderboardRowResponse(LongshotModel):
    rank: int
    user_id: str
    entry_index: int
    user_entry_count: Optional[int]
    handle: Optional[str]
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    avatar_seed: int
    resolved_win_count: int
    open_leg_count: int
    picks: Optional[List[ContestUserPickResponse]]
    tiebreaker_guess: Optional[int]
    payout_micros: Optional[int]
    net_payout_micros: Optional[int]
    perfect_slate_won: Optional[bool]
    perfect_slate_payout_micros: Optional[int]
    refunded: Optional[bool]
    roster_picks: Optional[List[ContestRosterPickResponse]]
    roster_points_milli: Optional[int]
    survivor: Optional[SurvivorEntryStateResponse]
    def __init__(self, *, rank: int, user_id: str, entry_index: int, user_entry_count: Optional[int] = ..., handle: Optional[str] = ..., x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., avatar_seed: int, resolved_win_count: int, open_leg_count: int, picks: Optional[List[ContestUserPickResponse]] = ..., tiebreaker_guess: Optional[int] = ..., payout_micros: Optional[int] = ..., net_payout_micros: Optional[int] = ..., perfect_slate_won: Optional[bool] = ..., perfect_slate_payout_micros: Optional[int] = ..., refunded: Optional[bool] = ..., roster_picks: Optional[List[ContestRosterPickResponse]] = ..., roster_points_milli: Optional[int] = ..., survivor: Optional[SurvivorEntryStateResponse] = ...) -> None: ...

class PublicContestLeaderboardResponse(LongshotModel):
    total_entries: int
    entries: List[ContestLeaderboardRowResponse]
    next_cursor: Optional[str]
    def __init__(self, *, total_entries: int, entries: List[ContestLeaderboardRowResponse], next_cursor: Optional[str] = ...) -> None: ...

class ContestCallerLeaderboardResponse(LongshotModel):
    rows: List[ContestLeaderboardRowResponse]
    def __init__(self, *, rows: List[ContestLeaderboardRowResponse]) -> None: ...

class CallerContestLeaderboardResponse(LongshotModel):
    leaderboard: PublicContestLeaderboardResponse
    caller: Optional[ContestCallerLeaderboardResponse]
    def __init__(self, *, leaderboard: PublicContestLeaderboardResponse, caller: Optional[ContestCallerLeaderboardResponse] = ...) -> None: ...

class ContestTopParticipantRowResponse(LongshotModel):
    user_id: str
    handle: Optional[str]
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    avatar_seed: int
    won_count: int
    total_winnings_micros: int
    def __init__(self, *, user_id: str, handle: Optional[str] = ..., x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., avatar_seed: int, won_count: int, total_winnings_micros: int) -> None: ...

class ContestTopParticipantsResponse(LongshotModel):
    window_ms: int
    participants: List[ContestTopParticipantRowResponse]
    def __init__(self, *, window_ms: int, participants: List[ContestTopParticipantRowResponse]) -> None: ...

class ContestPopularEntryMarketResponse(LongshotModel):
    market_id: int
    yes_count: int
    no_count: int
    def __init__(self, *, market_id: int, yes_count: int, no_count: int) -> None: ...

class ContestPopularEntryResponse(LongshotModel):
    total_entries: int
    markets: List[ContestPopularEntryMarketResponse]
    def __init__(self, *, total_entries: int, markets: List[ContestPopularEntryMarketResponse]) -> None: ...

class UserReferralCodeResponse(LongshotModel):
    referral_code: str
    max_referrals: Optional[int]
    referrals_used: int
    referrals_remaining: Optional[int]
    ever_had_referral_capacity: bool
    can_edit: bool
    def __init__(self, *, referral_code: str, max_referrals: Optional[int] = ..., referrals_used: int, referrals_remaining: Optional[int] = ..., ever_had_referral_capacity: bool, can_edit: bool) -> None: ...

class UserSetReferrerResponse(LongshotModel):
    def __init__(self) -> None: ...

class UserReferralRatesResponse(LongshotModel):
    primary_kickback_bps: int
    secondary_kickback_bps: int
    def __init__(self, *, primary_kickback_bps: int, secondary_kickback_bps: int) -> None: ...

class UserReferralStatsResponse(LongshotModel):
    total_referred: int
    total_rewards_micros: int
    has_settled_referral_trade: bool
    def __init__(self, *, total_referred: int, total_rewards_micros: int, has_settled_referral_trade: bool) -> None: ...

class ReferralLevelLabel(RustStringEnum):
    First = 'first'
    Second = 'second'

class UserReferralEntryResponse(LongshotModel):
    user_id: UUID
    handle: str
    display_name: str
    avatar_seed: int
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    referred_at_ms: int
    level: ReferralLevelLabel
    total_volume_micros: int
    total_fees_paid_micros: int
    my_kickback_micros: int
    def __init__(self, *, user_id: UUID, handle: str, display_name: str, avatar_seed: int, x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., referred_at_ms: int, level: ReferralLevelLabel, total_volume_micros: int, total_fees_paid_micros: int, my_kickback_micros: int) -> None: ...

class UserReferralsListResponse(LongshotModel):
    entries: List[UserReferralEntryResponse]
    total_count: int
    def __init__(self, *, entries: List[UserReferralEntryResponse], total_count: int) -> None: ...

class ErrorResponse(LongshotModel):
    error: str
    code: str
    details: Optional[str]
    def __init__(self, *, error: str, code: str, details: Optional[str] = ...) -> None: ...
    @classmethod
    def new(cls, error: Any, code: Any) -> ErrorResponse:
        ...
    def with_details(self: ErrorResponse, details: Any) -> ErrorResponse:
        ...

class ShareImageRef(RustTaggedUnion):
    @classmethod
    def pool_image(cls, payload: Any=None, **fields: Any) -> ShareImageRef:
        ...

class ShareCardFooter(LongshotModel):
    handle: str
    def __init__(self, *, handle: str) -> None: ...

class ShareStat(LongshotModel):
    value: str
    label: str
    def __init__(self, *, value: str, label: str) -> None: ...

class StreakShareCard(LongshotModel):
    streak_count: int
    max_streak: int
    market_title: str
    market_image: Optional[ShareImageRef]
    selection: str
    selection_date: Optional[str]
    prize_label: Optional[str]
    footer: ShareCardFooter
    def __init__(self, *, streak_count: int, max_streak: int, market_title: str, market_image: Optional[ShareImageRef] = ..., selection: str, selection_date: Optional[str] = ..., prize_label: Optional[str] = ..., footer: ShareCardFooter) -> None: ...

class PriceState(RustStringEnum):
    Live = 'live'
    Won = 'won'
    Lost = 'lost'

class PriceShareCard(LongshotModel):
    contest_id: str
    entry_index: int
    state: PriceState
    question: str
    subtitle: Optional[str]
    prediction: float
    current_price: float
    chart_prices: List[float]
    summary: Optional[List[ShareStat]]
    footer: ShareCardFooter
    def __init__(self, *, contest_id: str, entry_index: int, state: PriceState, question: str, subtitle: Optional[str] = ..., prediction: float, current_price: float, chart_prices: List[float], summary: Optional[List[ShareStat]] = ..., footer: ShareCardFooter) -> None: ...

class QuestionsState(RustStringEnum):
    Pre = 'pre'
    Live = 'live'
    Won = 'won'
    Lost = 'lost'

class ContestType(RustStringEnum):
    Free = 'free'
    Paid = 'paid'

class LegGrade(RustStringEnum):
    Pending = 'pending'
    Correct = 'correct'
    Incorrect = 'incorrect'

class QuestionLeg(LongshotModel):
    name: str
    answer: str
    grade: LegGrade
    def __init__(self, *, name: str, answer: str, grade: LegGrade) -> None: ...

class QuestionsShareCard(LongshotModel):
    contest_id: str
    entry_index: int
    state: QuestionsState
    contest_type: ContestType
    question: str
    topic_image: Optional[ShareImageRef]
    legs: List[QuestionLeg]
    summary: Optional[List[ShareStat]]
    footer: ShareCardFooter
    def __init__(self, *, contest_id: str, entry_index: int, state: QuestionsState, contest_type: ContestType, question: str, topic_image: Optional[ShareImageRef] = ..., legs: List[QuestionLeg], summary: Optional[List[ShareStat]] = ..., footer: ShareCardFooter) -> None: ...

class MarketsState(RustStringEnum):
    Pre = 'pre'
    Live = 'live'
    Won = 'won'
    Lost = 'lost'

class MarketWindowOutcome(RustStringEnum):
    Pending = 'pending'
    Live = 'live'
    Won = 'won'
    Lost = 'lost'
    Voided = 'voided'

class MarketWindowPick(LongshotModel):
    asset: str
    direction: str
    won: Optional[bool]
    pct_bps: Optional[int]
    def __init__(self, *, asset: str, direction: str, won: Optional[bool] = ..., pct_bps: Optional[int] = ...) -> None: ...

class MarketWindow(LongshotModel):
    start_ms: int
    end_ms: int
    time_label: str
    outcome: MarketWindowOutcome
    picks: List[MarketWindowPick]
    def __init__(self, *, start_ms: int, end_ms: int, time_label: str, outcome: MarketWindowOutcome, picks: List[MarketWindowPick]) -> None: ...

class MarketChartSeries(LongshotModel):
    asset: str
    prices: List[float]
    def __init__(self, *, asset: str, prices: List[float]) -> None: ...

class MarketsShareCard(LongshotModel):
    position_id: str
    tz_offset_minutes: Optional[int]
    state: Optional[MarketsState]
    multi_asset: Optional[bool]
    assets: Optional[List[str]]
    windows: Optional[List[MarketWindow]]
    date_label: Optional[str]
    wager_label: Optional[str]
    multiplier_label: Optional[str]
    payout_label: Optional[str]
    price_from: Optional[float]
    price_to: Optional[float]
    chart: Optional[List[MarketChartSeries]]
    footer: ShareCardFooter
    def __init__(self, *, position_id: str, tz_offset_minutes: Optional[int] = ..., state: Optional[MarketsState] = ..., multi_asset: Optional[bool] = ..., assets: Optional[List[str]] = ..., windows: Optional[List[MarketWindow]] = ..., date_label: Optional[str] = ..., wager_label: Optional[str] = ..., multiplier_label: Optional[str] = ..., payout_label: Optional[str] = ..., price_from: Optional[float] = ..., price_to: Optional[float] = ..., chart: Optional[List[MarketChartSeries]] = ..., footer: ShareCardFooter) -> None: ...

MAX_MARKET_WINDOWS = 9

MAX_MARKET_WINDOW_PICKS = 3

MAX_TZ_OFFSET_MINUTES = 14 * 60

class RosterShareState(RustStringEnum):
    Pre = 'pre'
    Live = 'live'
    Won = 'won'
    Lost = 'lost'
    Perfect = 'perfect'

class RosterShareKind(RustStringEnum):
    X = 'x'
    Nfl = 'nfl'

class RosterSharePick(LongshotModel):
    name: str
    bg: str
    fg: str
    points: Optional[str]
    unit: Optional[str]
    tip: Optional[str]
    hit: Optional[bool]
    def __init__(self, *, name: str, bg: str, fg: str, points: Optional[str] = ..., unit: Optional[str] = ..., tip: Optional[str] = ..., hit: Optional[bool] = ...) -> None: ...

class RosterShareCard(LongshotModel):
    contest_id: str
    entry_index: int
    state: RosterShareState
    contest_type: ContestType
    kind: RosterShareKind
    prompt: str
    picks: List[RosterSharePick]
    summary: Optional[List[ShareStat]]
    bonus_label: Optional[str]
    footer: ShareCardFooter
    def __init__(self, *, contest_id: str, entry_index: int, state: RosterShareState, contest_type: ContestType, kind: RosterShareKind, prompt: str, picks: List[RosterSharePick], summary: Optional[List[ShareStat]] = ..., bonus_label: Optional[str] = ..., footer: ShareCardFooter) -> None: ...

MAX_ROSTER_SHARE_PICKS = 10

class SurvivorShareState(RustStringEnum):
    Pre = 'pre'
    Live = 'live'
    Won = 'won'
    Lost = 'lost'
    Voided = 'voided'

class SurvivorSharePresentation(RustStringEnum):
    Matchup = 'matchup'
    Daily = 'daily'

class SurvivorShareRound(LongshotModel):
    result: SurvivorEntryRoundResultResponse
    pick_count: int
    def __init__(self, *, result: SurvivorEntryRoundResultResponse, pick_count: int) -> None: ...

class SurvivorShareCard(LongshotModel):
    contest_id: str
    entry_index: int
    state: Optional[SurvivorShareState]
    contest_type: Optional[ContestType]
    presentation: Optional[SurvivorSharePresentation]
    title: Optional[str]
    rounds: Optional[List[SurvivorShareRound]]
    summary: Optional[List[ShareStat]]
    footer: ShareCardFooter
    def __init__(self, *, contest_id: str, entry_index: int, state: Optional[SurvivorShareState] = ..., contest_type: Optional[ContestType] = ..., presentation: Optional[SurvivorSharePresentation] = ..., title: Optional[str] = ..., rounds: Optional[List[SurvivorShareRound]] = ..., summary: Optional[List[ShareStat]] = ..., footer: ShareCardFooter) -> None: ...

MAX_SURVIVOR_SHARE_PICKS = 64

MAX_SURVIVOR_SHARE_ROUNDS = 30

class EventPositionShareState(RustStringEnum):
    Active = 'active'
    Live = 'live'
    Won = 'won'
    Lost = 'lost'
    Voided = 'voided'

class EventPositionSharePickGrade(RustStringEnum):
    Pending = 'pending'
    Correct = 'correct'
    Incorrect = 'incorrect'
    Voided = 'voided'

class EventPositionSharePick(LongshotModel):
    market_id: int
    label: str
    side: str
    grade: EventPositionSharePickGrade
    odds_label: Optional[str]
    result: Optional[str]
    team_abbr: Optional[str]
    def __init__(self, *, market_id: int, label: str, side: str, grade: EventPositionSharePickGrade, odds_label: Optional[str] = ..., result: Optional[str] = ..., team_abbr: Optional[str] = ...) -> None: ...

class EventPositionShareCard(LongshotModel):
    position_id: str
    tz_offset_minutes: Optional[int]
    market_kind: Optional[str]
    state: Optional[EventPositionShareState]
    title: Optional[str]
    meta_label: Optional[str]
    market_image: Optional[ShareImageRef]
    picks: Optional[List[EventPositionSharePick]]
    wager_label: Optional[str]
    multiplier_label: Optional[str]
    payout_label: Optional[str]
    nfl: Optional[NflShareMeta]
    footer: ShareCardFooter
    def __init__(self, *, position_id: str, tz_offset_minutes: Optional[int] = ..., market_kind: Optional[str] = ..., state: Optional[EventPositionShareState] = ..., title: Optional[str] = ..., meta_label: Optional[str] = ..., market_image: Optional[ShareImageRef] = ..., picks: Optional[List[EventPositionSharePick]] = ..., wager_label: Optional[str] = ..., multiplier_label: Optional[str] = ..., payout_label: Optional[str] = ..., nfl: Optional[NflShareMeta] = ..., footer: ShareCardFooter) -> None: ...

MAX_EVENT_POSITION_SHARE_PICKS = 9

class ShareCardSnapshot(RustTaggedUnion):
    @classmethod
    def streak(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    @classmethod
    def price(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    @classmethod
    def questions(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    @classmethod
    def markets(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    @classmethod
    def roster(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    @classmethod
    def survivor(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    @classmethod
    def event_position(cls, payload: Any=None, **fields: Any) -> ShareCardSnapshot:
        ...
    def type_str(self: ShareCardSnapshot) -> str:
        ...
    def validate(self: ShareCardSnapshot) -> None:
        ...

class CreateShareCardResponse(LongshotModel):
    id: str
    share_url: str
    def __init__(self, *, id: str, share_url: str) -> None: ...

class StreakRoundStatusResponse(RustStringEnum):
    Open = 'open'
    Resolving = 'resolving'
    Resolved = 'resolved'

class StreakTierResponse(LongshotModel):
    streak: int
    payout_micros: int
    has_app_token: bool
    def __init__(self, *, streak: int, payout_micros: int, has_app_token: bool) -> None: ...

class StreakMarketResponse(LongshotModel):
    market_id: int
    selection_group: str
    market_type: MarketType
    trading_channels: List[TradingChannel]
    name: str
    status: MarketStatus
    outcome: Optional[Outcome]
    source: Optional[EventMarketSource]
    resolution_time_ms: Optional[int]
    betting_closes_at_ms: Optional[int]
    image_url: Optional[str]
    juiced: Optional[bool]
    def __init__(self, *, market_id: int, selection_group: str, market_type: MarketType, trading_channels: List[TradingChannel], name: str, status: MarketStatus, outcome: Optional[Outcome] = ..., source: Optional[EventMarketSource] = ..., resolution_time_ms: Optional[int] = ..., betting_closes_at_ms: Optional[int] = ..., image_url: Optional[str] = ..., juiced: Optional[bool] = ...) -> None: ...

class StreakUserPickResponse(LongshotModel):
    market_id: int
    direction: ContestDirectionResponse
    outcome: ContestLegOutcome
    picked_at_ms: int
    def __init__(self, *, market_id: int, direction: ContestDirectionResponse, outcome: ContestLegOutcome, picked_at_ms: int) -> None: ...

class StreakCurrentRoundResponse(LongshotModel):
    game_index: int
    status: StreakRoundStatusResponse
    betting_opens_at_ms: int
    betting_closes_at_ms: int
    resolved_at_ms: Optional[int]
    markets: List[StreakMarketResponse]
    user_pick: Optional[StreakUserPickResponse]
    def __init__(self, *, game_index: int, status: StreakRoundStatusResponse, betting_opens_at_ms: int, betting_closes_at_ms: int, resolved_at_ms: Optional[int] = ..., markets: List[StreakMarketResponse], user_pick: Optional[StreakUserPickResponse] = ...) -> None: ...

class StreakUserStateResponse(LongshotModel):
    win_streak: int
    games_won: int
    games_lost: int
    bets_won: int
    bets_lost: int
    def __init__(self, *, win_streak: int, games_won: int, games_lost: int, bets_won: int, bets_lost: int) -> None: ...

class StreakResponse(LongshotModel):
    contest_id: str
    title: str
    description: Optional[str]
    tiers: List[StreakTierResponse]
    max_streak: int
    current_round: Optional[StreakCurrentRoundResponse]
    scheduled_round: Optional[StreakCurrentRoundResponse]
    user: Optional[StreakUserStateResponse]
    def __init__(self, *, contest_id: str, title: str, description: Optional[str] = ..., tiers: List[StreakTierResponse], max_streak: int, current_round: Optional[StreakCurrentRoundResponse] = ..., scheduled_round: Optional[StreakCurrentRoundResponse] = ..., user: Optional[StreakUserStateResponse] = ...) -> None: ...

class StreakPickRound(RustStringEnum):
    Current = 'current'
    Scheduled = 'scheduled'

class PlaceStreakPickRequest(LongshotModel):
    market_id: int
    direction: str
    use_app_tokens: bool
    round: Optional[StreakPickRound]
    def __init__(self, *, market_id: int, direction: str, use_app_tokens: bool, round: Optional[StreakPickRound] = ...) -> None: ...

class PlaceStreakPickResponse(LongshotModel):
    entry_index: int
    picked_at_ms: int
    def __init__(self, *, entry_index: int, picked_at_ms: int) -> None: ...

class UserTransactionsRawQuery(LongshotModel):
    category: Optional[str]
    from_ms: Optional[str]
    to_ms: Optional[str]
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, category: Optional[str] = ..., from_ms: Optional[str] = ..., to_ms: Optional[str] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class ConfirmPositionQuery(LongshotModel):
    position_id: str
    accept: bool
    def __init__(self, *, position_id: str, accept: bool) -> None: ...

class ReferralsListRawQuery(LongshotModel):
    page: Optional[int]
    limit: Optional[int]
    def __init__(self, *, page: Optional[int] = ..., limit: Optional[int] = ...) -> None: ...

class VaultIdQuery(LongshotModel):
    vault_id: str
    def __init__(self, *, vault_id: str) -> None: ...

class VaultPnlHistoryQuery(LongshotModel):
    vault_id: str
    range: Optional[str]
    metric: Optional[str]
    def __init__(self, *, vault_id: str, range: Optional[str] = ..., metric: Optional[str] = ...) -> None: ...

class VaultPositionsQuery(LongshotModel):
    vault_id: str
    status: Optional[str]
    cursor: Optional[str]
    limit: Optional[int]
    def __init__(self, *, vault_id: str, status: Optional[str] = ..., cursor: Optional[str] = ..., limit: Optional[int] = ...) -> None: ...

class VaultEventsQuery(LongshotModel):
    vault_id: str
    cursor: Optional[str]
    limit: Optional[int]
    event_type: Optional[str]
    def __init__(self, *, vault_id: str, cursor: Optional[str] = ..., limit: Optional[int] = ..., event_type: Optional[str] = ...) -> None: ...

class VaultContributorsQuery(LongshotModel):
    vault_id: str
    cursor: Optional[str]
    limit: Optional[int]
    sort: Optional[str]
    def __init__(self, *, vault_id: str, cursor: Optional[str] = ..., limit: Optional[int] = ..., sort: Optional[str] = ...) -> None: ...

class CreateEmbeddedWalletEnsureRequest(LongshotModel):
    privy_token: str
    def __init__(self, *, privy_token: str) -> None: ...

class ReferralPromptRequest(RustStringEnum):
    PostWin = 'post_win'
    FirstPick = 'first_pick'

class ClaimReferralPromptRequest(LongshotModel):
    prompt: ReferralPromptRequest
    def __init__(self, *, prompt: ReferralPromptRequest) -> None: ...

class AcknowledgeReferralPromptRequest(LongshotModel):
    prompt: ReferralPromptRequest
    claim_token: UUID
    shown: bool
    def __init__(self, *, prompt: ReferralPromptRequest, claim_token: UUID, shown: bool) -> None: ...

class ChatPostGifRequest(LongshotModel):
    gif_id: str
    chat_id: Optional[str]
    parent: Optional[str]
    def __init__(self, *, gif_id: str, chat_id: Optional[str] = ..., parent: Optional[str] = ...) -> None: ...

class RfqEstimateRequest(LongshotModel):
    wager_micros: int
    legs: List[OrderLegJson]
    shield_on: Optional[bool]
    def __init__(self, *, wager_micros: int, legs: List[OrderLegJson], shield_on: Optional[bool] = ...) -> None: ...

class RfqEstimateBatchItemRequest(LongshotModel):
    key: str
    leg: OrderLegJson
    def __init__(self, *, key: str, leg: OrderLegJson) -> None: ...

class RfqEstimateBatchRequest(LongshotModel):
    wager_micros: int
    estimates: List[RfqEstimateBatchItemRequest]
    shield_on: Optional[bool]
    def __init__(self, *, wager_micros: int, estimates: List[RfqEstimateBatchItemRequest], shield_on: Optional[bool] = ...) -> None: ...

class EmbeddedWalletEnsureStatus(RustStringEnum):
    Ready = 'ready'
    Pending = 'pending'
    NotRequired = 'not_required'

class EmbeddedWalletEnsureResponse(LongshotModel):
    status: EmbeddedWalletEnsureStatus
    wallet_address: Optional[str]
    def __init__(self, *, status: EmbeddedWalletEnsureStatus, wallet_address: Optional[str] = ...) -> None: ...

class RfqEstimateResponse(LongshotModel):
    request_id: UUID
    quotable: bool
    odds: Optional[float]
    fillable_micros: Optional[int]
    quotes_received: int
    quoted_at_ms: int
    reason: Optional[str]
    def __init__(self, *, request_id: UUID, quotable: bool, odds: Optional[float] = ..., fillable_micros: Optional[int] = ..., quotes_received: int, quoted_at_ms: int, reason: Optional[str] = ...) -> None: ...

class RfqEstimateBatchItemStatus(RustStringEnum):
    Quoted = 'quoted'
    Unavailable = 'unavailable'

class RfqEstimateBatchItemResponse(LongshotModel):
    key: str
    market_id: int
    direction: str
    status: RfqEstimateBatchItemStatus
    request_id: Optional[UUID]
    quotable: bool
    odds: Optional[float]
    fillable_micros: Optional[int]
    quotes_received: int
    quoted_at_ms: Optional[int]
    reason: Optional[str]
    def __init__(self, *, key: str, market_id: int, direction: str, status: RfqEstimateBatchItemStatus, request_id: Optional[UUID] = ..., quotable: bool, odds: Optional[float] = ..., fillable_micros: Optional[int] = ..., quotes_received: int, quoted_at_ms: Optional[int] = ..., reason: Optional[str] = ...) -> None: ...

class RfqEstimateBatchResponse(LongshotModel):
    wager_micros: int
    estimates: List[RfqEstimateBatchItemResponse]
    def __init__(self, *, wager_micros: int, estimates: List[RfqEstimateBatchItemResponse]) -> None: ...

class MmRfqStatusResponse(LongshotModel):
    request_id: str
    status: RfqStatus
    def __init__(self, *, request_id: str, status: RfqStatus) -> None: ...

class UserAvailableBalanceResponse(LongshotModel):
    available_micros: int
    pending_custodial_deposit_micros: int
    credited_custodial_deposit_micros: int
    deposit_withdrawal_min_micros: int
    def __init__(self, *, available_micros: int, pending_custodial_deposit_micros: int, credited_custodial_deposit_micros: int, deposit_withdrawal_min_micros: int) -> None: ...

class WithdrawalDeliveryStatus(RustStringEnum):
    Queued = 'queued'

class QueuedWithdrawalResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    destination_address: Optional[str]
    delivery_status: WithdrawalDeliveryStatus
    def __init__(self, *, amount_micros: int, operation_id: UUID, destination_address: Optional[str] = ..., delivery_status: WithdrawalDeliveryStatus) -> None: ...

class AcceptedWithdrawOperationResponse(RustTaggedUnion):
    @classmethod
    def queued(cls, payload: Any=None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        ...
    @classmethod
    def recovery(cls, payload: Any=None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        ...

class PublicReferralStatusResponse(RustStringEnum):
    Valid = 'valid'
    Redeemed = 'redeemed'
    Expired = 'expired'

class PublicReferralInviterResponse(LongshotModel):
    display_name: str
    avatar_seed: int
    avatar_url: Optional[str]
    def __init__(self, *, display_name: str, avatar_seed: int, avatar_url: Optional[str] = ...) -> None: ...

class PublicReferralDepositMatchOffer(LongshotModel):
    match_limit_micros: int
    duration_ms: int
    def __init__(self, *, match_limit_micros: int, duration_ms: int) -> None: ...

class PublicReferralCodeResponse(LongshotModel):
    status: PublicReferralStatusResponse
    inviter: Optional[PublicReferralInviterResponse]
    deposit_match: Optional[PublicReferralDepositMatchOffer]
    def __init__(self, *, status: PublicReferralStatusResponse, inviter: Optional[PublicReferralInviterResponse] = ..., deposit_match: Optional[PublicReferralDepositMatchOffer] = ...) -> None: ...

class ClaimReferralPromptResponse(LongshotModel):
    show: bool
    amount_micros: Optional[int]
    claim_token: Optional[UUID]
    retry_after_ms: Optional[int]
    def __init__(self, *, show: bool, amount_micros: Optional[int] = ..., claim_token: Optional[UUID] = ..., retry_after_ms: Optional[int] = ...) -> None: ...

class ObserverAccessResponse(LongshotModel):
    enabled: bool
    def __init__(self, *, enabled: bool) -> None: ...

class MarketCategoryVisibilityResponse(LongshotModel):
    crypto: bool
    mentions: bool
    nfl: bool
    culture: bool
    def __init__(self, *, crypto: bool, mentions: bool, nfl: bool, culture: bool) -> None: ...

class UserFeaturesResponse(LongshotModel):
    markets_access: bool
    def __init__(self, *, markets_access: bool) -> None: ...

class ChatMarketRoomResponse(LongshotModel):
    chat_id: str
    def __init__(self, *, chat_id: str) -> None: ...

class ChatMentionCandidateResponse(LongshotModel):
    user_id: str
    handle: str
    def __init__(self, *, user_id: str, handle: str) -> None: ...

class ChatMentionCandidatesResponse(LongshotModel):
    candidates: List[ChatMentionCandidateResponse]
    def __init__(self, *, candidates: List[ChatMentionCandidateResponse]) -> None: ...

class FeedLegResponse(LongshotModel):
    asset: str
    direction: str
    window_start_ms: Optional[int]
    duration_secs: Optional[int]
    def __init__(self, *, asset: str, direction: str, window_start_ms: Optional[int] = ..., duration_secs: Optional[int] = ...) -> None: ...

class FeedEventWithLegsResponse(LongshotModel):
    event: FeedEventResponse
    primary_asset: Optional[str]
    has_binary_event_leg: bool
    legs: Optional[List[FeedLegResponse]]
    def __init__(self, *, event: FeedEventResponse, primary_asset: Optional[str] = ..., has_binary_event_leg: bool, legs: Optional[List[FeedLegResponse]] = ...) -> None: ...

class FeedWithLegsResponse(LongshotModel):
    events: List[FeedEventWithLegsResponse]
    next_cursor: Optional[str]
    def __init__(self, *, events: List[FeedEventWithLegsResponse], next_cursor: Optional[str] = ...) -> None: ...

class PnlHistoryScopedQuery(LongshotModel):
    from_: Optional[int]
    to: Optional[int]
    scope: Optional[str]
    def __init__(self, *, from_: Optional[int] = ..., to: Optional[int] = ..., scope: Optional[str] = ...) -> None: ...

class PortfolioSummaryRawQuery(LongshotModel):
    scope: Optional[str]
    def __init__(self, *, scope: Optional[str] = ...) -> None: ...

class PortfolioSummaryResponse(LongshotModel):
    scope: str
    active_count: int
    potential_payout_micros: int
    realized_pnl_micros: int
    biggest_win_micros: Optional[int]
    def __init__(self, *, scope: str, active_count: int, potential_payout_micros: int, realized_pnl_micros: int, biggest_win_micros: Optional[int]) -> None: ...

class PositionsByMarketsQuery(LongshotModel):
    market_ids: str
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, market_ids: str, limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class PositionsByMarketsResponse(LongshotModel):
    positions: List[PositionDetailResponse]
    next_cursor: Optional[str]
    def __init__(self, *, positions: List[PositionDetailResponse], next_cursor: Optional[str] = ...) -> None: ...

class ProfileUpdateQuery(LongshotModel):
    finalize_onboarding: Optional[bool]
    def __init__(self, *, finalize_onboarding: Optional[bool] = ...) -> None: ...

class HandleAvailabilityQuery(LongshotModel):
    handle: str
    finalize_onboarding: Optional[bool]
    def __init__(self, *, handle: str, finalize_onboarding: Optional[bool] = ...) -> None: ...

class PublicProfileSummaryResponse(LongshotModel):
    scope: str
    active_count: int
    potential_payout_micros: int
    realized_pnl_micros: int
    biggest_win_micros: Optional[int]
    def __init__(self, *, scope: str, active_count: int, potential_payout_micros: int, realized_pnl_micros: int, biggest_win_micros: Optional[int]) -> None: ...

class UserReferralStatsRawQuery(LongshotModel):
    window: Optional[str]
    def __init__(self, *, window: Optional[str] = ...) -> None: ...

class WebPushConfigResponse(LongshotModel):
    enabled: bool
    public_key: Optional[str]
    def __init__(self, *, enabled: bool, public_key: Optional[str] = ...) -> None: ...

class WebPushSubscriptionKeys(LongshotModel):
    p256dh: str
    auth: str
    def __init__(self, *, p256dh: str, auth: str) -> None: ...

class UpsertWebPushSubscriptionRequest(LongshotModel):
    endpoint: str
    expiration_time: Optional[int]
    keys: WebPushSubscriptionKeys
    def __init__(self, *, endpoint: str, expiration_time: Optional[int] = ..., keys: WebPushSubscriptionKeys) -> None: ...

class DeleteWebPushSubscriptionRequest(LongshotModel):
    endpoint: str
    def __init__(self, *, endpoint: str) -> None: ...

class WebPushSubscriptionResponse(LongshotModel):
    subscribed: bool
    def __init__(self, *, subscribed: bool) -> None: ...

class StreakPicksRawQuery(LongshotModel):
    limit: Optional[int]
    cursor: Optional[str]
    contest_id: Optional[str]
    def __init__(self, *, limit: Optional[int] = ..., cursor: Optional[str] = ..., contest_id: Optional[str] = ...) -> None: ...

class StreakHistoryRawQuery(LongshotModel):
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class StreakLeaderboardRawQuery(LongshotModel):
    limit: Optional[int]
    def __init__(self, *, limit: Optional[int] = ...) -> None: ...

class StreakPickHistoryItemResponse(LongshotModel):
    game_index: int
    market_id: int
    market_title: str
    market_category: str
    market_outcome: Optional[Outcome]
    direction: ContestDirectionResponse
    outcome: ContestLegOutcome
    picked_at_ms: int
    betting_closes_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    image_url: Optional[str]
    def __init__(self, *, game_index: int, market_id: int, market_title: str, market_category: str, market_outcome: Optional[Outcome] = ..., direction: ContestDirectionResponse, outcome: ContestLegOutcome, picked_at_ms: int, betting_closes_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., image_url: Optional[str] = ...) -> None: ...

class StreakPicksResponse(LongshotModel):
    contest_id: Optional[str]
    title: Optional[str]
    picks: List[StreakPickHistoryItemResponse]
    next_cursor: Optional[str]
    def __init__(self, *, contest_id: Optional[str] = ..., title: Optional[str] = ..., picks: List[StreakPickHistoryItemResponse], next_cursor: Optional[str] = ...) -> None: ...

class StreakPickVisibilityResponse(RustStringEnum):
    Visible = 'visible'
    HiddenWhileBettingOpen = 'hidden_while_betting_open'
    None_ = 'none'

class PublicProfileStreakPicksResponse(LongshotModel):
    contest_id: Optional[str]
    title: Optional[str]
    picks: List[StreakPickHistoryItemResponse]
    current_round_pick_visibility: StreakPickVisibilityResponse
    next_cursor: Optional[str]
    def __init__(self, *, contest_id: Optional[str] = ..., title: Optional[str] = ..., picks: List[StreakPickHistoryItemResponse], current_round_pick_visibility: StreakPickVisibilityResponse, next_cursor: Optional[str] = ...) -> None: ...

class StreakRunStatusResponse(RustStringEnum):
    Active = 'active'
    Ended = 'ended'
    Expired = 'expired'
    Won = 'won'

class StreakRunTierPayoutResponse(LongshotModel):
    streak: int
    payout_micros: int
    is_app_token: bool
    game_index: int
    won_at_ms: int
    credited: bool
    def __init__(self, *, streak: int, payout_micros: int, is_app_token: bool, game_index: int, won_at_ms: int, credited: bool) -> None: ...

class StreakRunResponse(LongshotModel):
    contest_id: str
    title: str
    max_streak: int
    status: StreakRunStatusResponse
    length: int
    pick_count: int
    start_game_index: int
    end_game_index: Optional[int]
    started_at_ms: int
    ended_at_ms: Optional[int]
    failed_pick_number: Optional[int]
    failed_pick: Optional[StreakPickHistoryItemResponse]
    cash_payout_micros: int
    tier_payouts: List[StreakRunTierPayoutResponse]
    def __init__(self, *, contest_id: str, title: str, max_streak: int, status: StreakRunStatusResponse, length: int, pick_count: int, start_game_index: int, end_game_index: Optional[int] = ..., started_at_ms: int, ended_at_ms: Optional[int] = ..., failed_pick_number: Optional[int] = ..., failed_pick: Optional[StreakPickHistoryItemResponse] = ..., cash_payout_micros: int, tier_payouts: List[StreakRunTierPayoutResponse]) -> None: ...

class StreakHistoryResponse(LongshotModel):
    runs: List[StreakRunResponse]
    next_cursor: Optional[str]
    def __init__(self, *, runs: List[StreakRunResponse], next_cursor: Optional[str] = ...) -> None: ...

class PublicProfileStreakHistoryResponse(LongshotModel):
    runs: List[StreakRunResponse]
    next_cursor: Optional[str]
    def __init__(self, *, runs: List[StreakRunResponse], next_cursor: Optional[str] = ...) -> None: ...

class StreakOnboardingRoundResponse(LongshotModel):
    game_index: int
    target: StreakPickRound
    betting_closes_at_ms: int
    markets: List[StreakMarketResponse]
    def __init__(self, *, game_index: int, target: StreakPickRound, betting_closes_at_ms: int, markets: List[StreakMarketResponse]) -> None: ...

class StreakOnboardingResponse(LongshotModel):
    contest_id: str
    title: str
    eligible: bool
    round: Optional[StreakOnboardingRoundResponse]
    def __init__(self, *, contest_id: str, title: str, eligible: bool, round: Optional[StreakOnboardingRoundResponse] = ...) -> None: ...

class StreakPopularMarketResponse(LongshotModel):
    market_id: int
    market_title: str
    market_category: str
    betting_closes_at_ms: Optional[int]
    up_count: int
    down_count: int
    image_url: Optional[str]
    def __init__(self, *, market_id: int, market_title: str, market_category: str, betting_closes_at_ms: Optional[int] = ..., up_count: int, down_count: int, image_url: Optional[str] = ...) -> None: ...

class StreakPopularTodayResponse(LongshotModel):
    contest_id: Optional[str]
    game_index: Optional[int]
    total_picks: int
    markets: List[StreakPopularMarketResponse]
    def __init__(self, *, contest_id: Optional[str] = ..., game_index: Optional[int] = ..., total_picks: int, markets: List[StreakPopularMarketResponse]) -> None: ...

class StreakLeaderboardRowResponse(LongshotModel):
    handle: Optional[str]
    display_name: Optional[str]
    avatar_seed: int
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    current_streak: int
    picks: List[StreakPickHistoryItemResponse]
    current_pick: Optional[StreakPickHistoryItemResponse]
    current_pick_visibility: StreakPickVisibilityResponse
    def __init__(self, *, handle: Optional[str] = ..., display_name: Optional[str] = ..., avatar_seed: int, x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., current_streak: int, picks: List[StreakPickHistoryItemResponse], current_pick: Optional[StreakPickHistoryItemResponse] = ..., current_pick_visibility: StreakPickVisibilityResponse) -> None: ...

class StreakLeaderboardResponse(LongshotModel):
    contest_id: Optional[str]
    current_game_index: Optional[int]
    rows: List[StreakLeaderboardRowResponse]
    def __init__(self, *, contest_id: Optional[str] = ..., current_game_index: Optional[int] = ..., rows: List[StreakLeaderboardRowResponse]) -> None: ...

class LeaderboardPeriod(RustStringEnum):
    Daily = 'daily'
    Weekly = 'weekly'
    Monthly = 'monthly'
    AllTime = 'all_time'

class LeaderboardScope(RustStringEnum):
    All = 'all'
    Markets = 'markets'
    Contests = 'contests'

class LeaderboardMetric(RustStringEnum):
    Pnl = 'pnl'
    Combo = 'combo'

class LegacyLeaderboardEntry(LongshotModel):
    rank: int
    user_id: str
    handle: Optional[str]
    display_name: Optional[str]
    avatar_seed: Optional[int]
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    created_at_ms: int
    metric_value: int
    total_positions: int
    wins: int
    losses: int
    biggest_win_micros: int
    highest_multiplier_bps: int
    def __init__(self, *, rank: int, user_id: str, handle: Optional[str] = ..., display_name: Optional[str] = ..., avatar_seed: Optional[int] = ..., x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., created_at_ms: int, metric_value: int, total_positions: int, wins: int, losses: int, biggest_win_micros: int, highest_multiplier_bps: int) -> None: ...

class LeaderboardPnlEntry(LongshotModel):
    rank: int
    handle: Optional[str]
    display_name: Optional[str]
    avatar_seed: Optional[int]
    x_avatar_url: Optional[str]
    entry_count: int
    pnl_micros: int
    def __init__(self, *, rank: int, handle: Optional[str] = ..., display_name: Optional[str] = ..., avatar_seed: Optional[int] = ..., x_avatar_url: Optional[str] = ..., entry_count: int, pnl_micros: int) -> None: ...

class LeaderboardComboEntry(LongshotModel):
    rank: int
    handle: Optional[str]
    display_name: Optional[str]
    avatar_seed: Optional[int]
    x_avatar_url: Optional[str]
    combo_legs: int
    multiplier_bps: int
    def __init__(self, *, rank: int, handle: Optional[str] = ..., display_name: Optional[str] = ..., avatar_seed: Optional[int] = ..., x_avatar_url: Optional[str] = ..., combo_legs: int, multiplier_bps: int) -> None: ...

class LeaderboardPnlCaller(LongshotModel):
    rank: int
    entry_count: int
    pnl_micros: int
    def __init__(self, *, rank: int, entry_count: int, pnl_micros: int) -> None: ...

class LeaderboardComboCaller(LongshotModel):
    rank: int
    combo_legs: int
    multiplier_bps: int
    def __init__(self, *, rank: int, combo_legs: int, multiplier_bps: int) -> None: ...

class LeaderboardCaller(RustTaggedUnion):
    @classmethod
    def pnl(cls, payload: Any=None, **fields: Any) -> LeaderboardCaller:
        ...
    @classmethod
    def combo(cls, payload: Any=None, **fields: Any) -> LeaderboardCaller:
        ...

class ChatGifProviderResponse(RustStringEnum):
    Giphy = 'giphy'

class ChatGifAttachmentResponse(LongshotModel):
    provider: ChatGifProviderResponse
    id: str
    def __init__(self, *, provider: ChatGifProviderResponse, id: str) -> None: ...

class ContestLobbySummaryResponse(LongshotModel):
    summary: CallerContestSummaryResponse
    description: Optional[str]
    max_entries_per_player: Optional[int]
    protocol_prize_pool_pays_app_tokens: bool
    def __init__(self, *, summary: CallerContestSummaryResponse, description: Optional[str] = ..., max_entries_per_player: Optional[int] = ..., protocol_prize_pool_pays_app_tokens: bool) -> None: ...

__all__ = [
    "NOTIFICATION_LIST_DEFAULT_LIMIT",
    "NOTIFICATION_LIST_MAX_LIMIT",
    "NOTIFICATION_STREAM_BATCH_LIMIT",
    "MAX_CHART_POINTS",
    "MAX_QUESTION_LEGS",
    "MAX_MARKET_WINDOWS",
    "MAX_MARKET_WINDOW_PICKS",
    "MAX_TZ_OFFSET_MINUTES",
    "MAX_SUMMARY_STATS",
    "MAX_TEXT_LEN",
    "ChatUserAvatarResponse",
    "ChatAuthorResponse",
    "ChatReactionResponse",
    "ChatEmojiDisplayResponse",
    "ChatEmojiResponse",
    "ChatEmojisResponse",
    "ChatReactionUpdateResponse",
    "ChatMessageResponse",
    "ChatMessageEditResponse",
    "ChatRecentMessagesResponse",
    "ChatStreamErrorCode",
    "ChatStreamErrorEvent",
    "ListContestsQuery",
    "ContestDetailQuery",
    "ContestLeaderboardQuery",
    "ContestTopParticipantsQuery",
    "FeedFilter",
    "FeedRawQuery",
    "FeedEventResponse",
    "FeedResponse",
    "LeaderboardWindow",
    "LeaderboardRawQuery",
    "LeaderboardMeRawQuery",
    "HighlightsRawQuery",
    "LeaderboardMetricResponse",
    "HighlightSortResponse",
    "LeaderboardEntry",
    "LeaderboardResponse",
    "LeaderboardMyRankResponse",
    "HighlightEntry",
    "LeaderboardHighlightsResponse",
    "PriceSourceResponse",
    "MarketCandlesQuery",
    "MarketTicksStreamQuery",
    "ExternalOddsSourceQuery",
    "ChartPoint",
    "OhlcCandle",
    "MarketTickStreamEvent",
    "MarketTickStreamErrorCode",
    "MarketTickStreamErrorEvent",
    "TopOfBookStreamQuery",
    "ExternalOddsSourceStatus",
    "ExternalOddsSourceKind",
    "ExternalOddsSourceRow",
    "ExternalOddsSourceResponse",
    "TopOfBookStreamEvent",
    "TopOfBookStreamErrorCode",
    "TopOfBookStreamErrorEvent",
    "TopOfBookHistoryQuery",
    "TopOfBookHistoryPoint",
    "TopOfBookHistoryStatus",
    "TopOfBookHistoryMarket",
    "TopOfBookHistoryResponse",
    "MarketCandlesResponse",
    "ReferencePriceQuery",
    "SourceStatus",
    "ReferencePriceResponse",
    "WindowResultsQuery",
    "WindowDirection",
    "WindowAssetResult",
    "WindowResult",
    "WindowResultsResponse",
    "PublicMarketsRawQuery",
    "EventMarketSource",
    "PriceStrikeMarket",
    "EventMarket",
    "PublicMarket",
    "PublicMarketResponse",
    "PublicMarketsResponse",
    "MarketMetadataEntry",
    "MarketLookupResponse",
    "MarketLookupQuery",
    "MarketCurrentQuery",
    "RecentResolutionsQuery",
    "RecentResolutionEntry",
    "RecentResolutionsResponse",
    "NotificationsRawQuery",
    "NotificationStreamRawQuery",
    "NotificationPayload",
    "BinaryEventStartSoonNotificationPayload",
    "FantasyStartSoonNotificationPayload",
    "StreakStartSoonNotificationPayload",
    "StreakExpiringNotificationPayload",
    "BinaryEventWinNotificationPayload",
    "NflShareMeta",
    "PriceStrikeParlayWinNotificationPayload",
    "RfqResultNotificationPayload",
    "RfqResultNotificationStatus",
    "FantasyResultNotificationPayload",
    "FantasyResultGameType",
    "FantasyResultBestEntry",
    "PerfectSlateNotificationPayload",
    "StreakWinNotificationPayload",
    "StreakWinOutcome",
    "StreakSettledNotificationPayload",
    "StreakSettledOutcome",
    "PayoutReviewNotificationPayload",
    "PayoutReviewNotificationStatus",
    "CreditsGrantedNotificationPayload",
    "ChatMentionNotificationPayload",
    "ChatMentionContext",
    "UnknownNotificationPayload",
    "NotificationResponse",
    "NotificationsResponse",
    "NotificationMutationResponse",
    "NotificationBulkMutationResponse",
    "PoolImageRawBytes",
    "PortfolioIntegrityErrorResponse",
    "PortfolioStatsResponse",
    "PnlHistoryQueryParseError",
    "PnlHistoryQuery",
    "PnlEventResponse",
    "PnlHistoryResponse",
    "FantasyEntriesQuery",
    "PortfolioFantasyEntryResponse",
    "PortfolioFantasyEntriesResponse",
    "PositionsQuery",
    "PositionStatusQueryParam",
    "PositionSortQueryParam",
    "CursorParseError",
    "PositionQueryParseError",
    "PositionSummary",
    "PositionsListResponse",
    "ActivePositionStatus",
    "PositionRole",
    "ActivePosition",
    "ActivePositionsResponse",
    "LegDetail",
    "PositionDetailResponse",
    "PreferencesResponse",
    "QuoteTolerancePreference",
    "UpdatePreferencesRequest",
    "PrimaryLegIdentityResponse",
    "CheckHandleQuery",
    "ProfileResponse",
    "PublicProfileResponse",
    "PublicProfileStatsResponse",
    "PublicProfilePnlEventResponse",
    "PublicProfilePnlHistoryResponse",
    "PublicProfileFantasyEntryResponse",
    "PublicProfileFantasyEntriesResponse",
    "PublicProfileContestOwnerEntryVisibilityResponse",
    "PublicProfileContestOwnerResponse",
    "PublicProfileContestDetailResponse",
    "PublicProfilePositionSummaryResponse",
    "PublicProfilePositionsResponse",
    "PublicProfilePositionDetailResponse",
    "UpdateProfileRequest",
    "SyncXProfileRequest",
    "CheckHandleResponse",
    "CreateSessionRequest",
    "WalletAuthRequest",
    "ChatPostMessageRequest",
    "ChatEditMessageRequest",
    "ChatEmojiReactRequest",
    "ChatStreamQuery",
    "ChatMentionCandidatesQuery",
    "ChatRecentMessagesQuery",
    "UserSetReferrerRequest",
    "UserCreateReferralCodeRequest",
    "PlaceContestBetSelectionRequest",
    "PlaceContestBetRequest",
    "UserDepositRequest",
    "UserDepositVaultRequest",
    "UserWithdrawParams",
    "WithdrawalAuthorization",
    "UserWithdrawRequest",
    "build_wallet_authentication_message",
    "build_wallet_withdrawal_authorization_message",
    "encode_wallet_signature",
    "VaultWithdrawalAmountRequest",
    "OrderLegJson",
    "SignedOrderJson",
    "CreateRfqRequest",
    "CommunityPickMode",
    "CommunityPickRequest",
    "UnsignedRfqOrderRequest",
    "CreateUnsignedRfqRequest",
    "ParsedOrderLeg",
    "OrderLegParseError",
    "RfqOrderJsonError",
    "AccessResponse",
    "SessionResponse",
    "RfqStatus",
    "RfqResponse",
    "CancelResponse",
    "UserDepositResponse",
    "UserDepositWalletResponse",
    "UserDepositVaultResponse",
    "UserWithdrawResponse",
    "BalanceOperationStatus",
    "BalanceOperationStatusResponse",
    "DepositOperationResponse",
    "WithdrawOperationResponse",
    "UserRequestWithdrawalVaultResponse",
    "VaultClaimFeesResponse",
    "VaultWithdrawalAmountResponse",
    "PendingVaultWithdrawalResponse",
    "VaultWithdrawalQueueResponse",
    "VaultLiquidityProviderResponse",
    "PositionVaultResponse",
    "VaultPositionVaultResponse",
    "VaultConfigsResponse",
    "VaultAmountResponse",
    "VaultAggregateAmountResponse",
    "VaultResponse",
    "VaultStatsResponse",
    "VaultPnlHistoryPoint",
    "VaultPnlHistoryResponse",
    "VaultPositionResponse",
    "VaultPositionsResponse",
    "PublicVaultPositionDetailResponse",
    "PublicVaultActivityEventResponse",
    "PublicVaultActivityResponse",
    "PublicVaultContributorLeaderboardRowResponse",
    "PublicVaultContributorLeaderboardResponse",
    "VaultUserPerformanceResponse",
    "AvailableBalanceResponse",
    "ReservedBalanceResponse",
    "UserTransactionCategory",
    "UserTransactionStatus",
    "UserTransactionUnit",
    "UserTransactionFunding",
    "UserTransactionResponse",
    "UserTransactionsResponse",
    "FeeScheduleTier",
    "TierFeeRate",
    "FeeScheduleResponse",
    "PlaceContestBetResponse",
    "ContestCategoryResponse",
    "ContestStatusResponse",
    "ContestBetTypeResponse",
    "ContestGameTypeResponse",
    "ContestRosterResponse",
    "ContestRosterTierResponse",
    "ContestRosterSelectionResponse",
    "ContestRosterPickResponse",
    "PlaceRosterPickRequest",
    "SurvivorPhaseResponse",
    "SurvivorRoundStatusResponse",
    "SurvivorEntryRoundResultResponse",
    "SurvivorEliminationReasonResponse",
    "ContestDirectionResponse",
    "ContestLegOutcome",
    "ContestPerfectSlateResponse",
    "PublicContestSummaryResponse",
    "ContestCallerSummaryResponse",
    "CallerContestSummaryResponse",
    "CallerContestsListResponse",
    "ContestMarketResponse",
    "ContestUserPickResponse",
    "SurvivorRoundPicksResponse",
    "SurvivorMarketPickCountsResponse",
    "SurvivorRoundBreakdownResponse",
    "SurvivorRoundResponse",
    "SurvivorEntryRoundResponse",
    "SurvivorEntryStateResponse",
    "SurvivorContestResponse",
    "SurvivorTeamUsageResponse",
    "ContestUserEntryResponse",
    "ContestTiebreakerResponse",
    "PublicContestDetailResponse",
    "ContestCallerDetailResponse",
    "CallerContestDetailResponse",
    "ContestLeaderboardRowResponse",
    "PublicContestLeaderboardResponse",
    "ContestCallerLeaderboardResponse",
    "CallerContestLeaderboardResponse",
    "ContestTopParticipantRowResponse",
    "ContestTopParticipantsResponse",
    "ContestPopularEntryMarketResponse",
    "ContestPopularEntryResponse",
    "UserReferralCodeResponse",
    "UserSetReferrerResponse",
    "UserReferralRatesResponse",
    "UserReferralStatsResponse",
    "ReferralLevelLabel",
    "UserReferralEntryResponse",
    "UserReferralsListResponse",
    "ErrorResponse",
    "ShareImageRef",
    "ShareCardFooter",
    "ShareStat",
    "StreakShareCard",
    "PriceState",
    "PriceShareCard",
    "QuestionsState",
    "ContestType",
    "LegGrade",
    "QuestionLeg",
    "QuestionsShareCard",
    "MarketsState",
    "MarketWindowOutcome",
    "MarketWindowPick",
    "MarketWindow",
    "MarketChartSeries",
    "MarketsShareCard",
    "MAX_MARKET_WINDOWS",
    "MAX_MARKET_WINDOW_PICKS",
    "MAX_TZ_OFFSET_MINUTES",
    "RosterShareState",
    "RosterShareKind",
    "RosterSharePick",
    "RosterShareCard",
    "MAX_ROSTER_SHARE_PICKS",
    "SurvivorShareState",
    "SurvivorSharePresentation",
    "SurvivorShareRound",
    "SurvivorShareCard",
    "MAX_SURVIVOR_SHARE_PICKS",
    "MAX_SURVIVOR_SHARE_ROUNDS",
    "EventPositionShareState",
    "EventPositionSharePickGrade",
    "EventPositionSharePick",
    "EventPositionShareCard",
    "MAX_EVENT_POSITION_SHARE_PICKS",
    "ShareCardSnapshot",
    "CreateShareCardResponse",
    "StreakRoundStatusResponse",
    "StreakTierResponse",
    "StreakMarketResponse",
    "StreakUserPickResponse",
    "StreakCurrentRoundResponse",
    "StreakUserStateResponse",
    "StreakResponse",
    "StreakPickRound",
    "PlaceStreakPickRequest",
    "PlaceStreakPickResponse",
    "UserTransactionsRawQuery",
    "ConfirmPositionQuery",
    "ReferralsListRawQuery",
    "VaultIdQuery",
    "VaultPnlHistoryQuery",
    "VaultPositionsQuery",
    "VaultEventsQuery",
    "VaultContributorsQuery",
    "CreateEmbeddedWalletEnsureRequest",
    "ReferralPromptRequest",
    "ClaimReferralPromptRequest",
    "AcknowledgeReferralPromptRequest",
    "ChatPostGifRequest",
    "RfqEstimateRequest",
    "RfqEstimateBatchItemRequest",
    "RfqEstimateBatchRequest",
    "EmbeddedWalletEnsureStatus",
    "EmbeddedWalletEnsureResponse",
    "RfqEstimateResponse",
    "RfqEstimateBatchItemStatus",
    "RfqEstimateBatchItemResponse",
    "RfqEstimateBatchResponse",
    "MmRfqStatusResponse",
    "UserAvailableBalanceResponse",
    "WithdrawalDeliveryStatus",
    "QueuedWithdrawalResponse",
    "AcceptedWithdrawOperationResponse",
    "PublicReferralStatusResponse",
    "PublicReferralInviterResponse",
    "PublicReferralDepositMatchOffer",
    "PublicReferralCodeResponse",
    "ClaimReferralPromptResponse",
    "ObserverAccessResponse",
    "MarketCategoryVisibilityResponse",
    "UserFeaturesResponse",
    "ChatMarketRoomResponse",
    "ChatMentionCandidateResponse",
    "ChatMentionCandidatesResponse",
    "FeedLegResponse",
    "FeedEventWithLegsResponse",
    "FeedWithLegsResponse",
    "PnlHistoryScopedQuery",
    "PortfolioSummaryRawQuery",
    "PortfolioSummaryResponse",
    "PositionsByMarketsQuery",
    "PositionsByMarketsResponse",
    "ProfileUpdateQuery",
    "HandleAvailabilityQuery",
    "PublicProfileSummaryResponse",
    "UserReferralStatsRawQuery",
    "WebPushConfigResponse",
    "WebPushSubscriptionKeys",
    "UpsertWebPushSubscriptionRequest",
    "DeleteWebPushSubscriptionRequest",
    "WebPushSubscriptionResponse",
    "StreakPicksRawQuery",
    "StreakHistoryRawQuery",
    "StreakLeaderboardRawQuery",
    "StreakPickHistoryItemResponse",
    "StreakPicksResponse",
    "StreakPickVisibilityResponse",
    "PublicProfileStreakPicksResponse",
    "StreakRunStatusResponse",
    "StreakRunTierPayoutResponse",
    "StreakRunResponse",
    "StreakHistoryResponse",
    "PublicProfileStreakHistoryResponse",
    "StreakOnboardingRoundResponse",
    "StreakOnboardingResponse",
    "StreakPopularMarketResponse",
    "StreakPopularTodayResponse",
    "StreakLeaderboardRowResponse",
    "StreakLeaderboardResponse",
    "LeaderboardPeriod",
    "LeaderboardScope",
    "LeaderboardMetric",
    "LegacyLeaderboardEntry",
    "LeaderboardPnlEntry",
    "LeaderboardComboEntry",
    "LeaderboardPnlCaller",
    "LeaderboardComboCaller",
    "LeaderboardCaller",
    "ChatGifProviderResponse",
    "ChatGifAttachmentResponse",
    "ContestLobbySummaryResponse",
]
