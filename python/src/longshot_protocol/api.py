# Hand-maintained Python mirror of rust/src/api/*.rs; parity is enforced by tests.
# Keep shared behavior in longshot_protocol.model and helper functions below.

from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from math import ceil, floor, isfinite
from typing import Any, Dict, List, Optional
from uuid import UUID

from ._serde_metadata import (
    DENY_UNKNOWN_TAGGED_UNIONS,
    STRUCT_INTEGER_FIELDS,
    STRUCT_REQUIRED_FIELDS,
    STRUCT_REQUIRED_NULLABLE_FIELDS,
    TAGGED_UNION_FIELDS,
)
from .model import LongshotModel, RustStringEnum, RustTaggedUnion, _install_serde_metadata
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

NOTIFICATION_LIST_DEFAULT_LIMIT = 30
NOTIFICATION_LIST_MAX_LIMIT = 100
NOTIFICATION_STREAM_BATCH_LIMIT = 50
MAX_CHART_POINTS = 512
MAX_MARKET_WINDOWS = 9
MAX_MARKET_WINDOW_PICKS = 3
MAX_TZ_OFFSET_MINUTES = 14 * 60
MAX_QUESTION_LEGS = 32
MAX_SUMMARY_STATS = 4
MAX_ROSTER_SHARE_PICKS = 10
MAX_EVENT_POSITION_SHARE_PICKS = 9
MAX_SURVIVOR_SHARE_PICKS = 64
MAX_SURVIVOR_SHARE_ROUNDS = 30
MAX_TEXT_LEN = 200

class ChatUserAvatarResponse(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "XAvatarUrl": "x_avatar_url",
            "Seed": "seed"
    }

    @classmethod
    def x_avatar_url(cls, payload: Any = None, **fields: Any) -> ChatUserAvatarResponse:
        return cls("XAvatarUrl", payload, **fields)

    @classmethod
    def seed(cls, payload: Any = None, **fields: Any) -> ChatUserAvatarResponse:
        return cls("Seed", payload, **fields)

@dataclass
class ChatAuthorResponse(LongshotModel):
    user_id: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[ChatUserAvatarResponse] = None

@dataclass
class ChatReactionResponse(LongshotModel):
    emoji_code: Optional[str] = None
    reactor: Optional[ChatAuthorResponse] = None

class ChatEmojiDisplayResponse(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "Url": "url",
            "Unicode": "unicode"
    }

    @classmethod
    def url(cls, payload: Any = None, **fields: Any) -> ChatEmojiDisplayResponse:
        return cls("Url", payload, **fields)

    @classmethod
    def unicode(cls, payload: Any = None, **fields: Any) -> ChatEmojiDisplayResponse:
        return cls("Unicode", payload, **fields)

@dataclass
class ChatEmojiResponse(LongshotModel):
    code: Optional[str] = None
    display: Optional[ChatEmojiDisplayResponse] = None

@dataclass
class ChatEmojisResponse(LongshotModel):
    emojis: Optional[List[ChatEmojiResponse]] = None

@dataclass
class ChatReactionUpdateResponse(LongshotModel):
    message_id: Optional[str] = None
    reaction_seq: Optional[int] = None
    reactions: Optional[List[ChatReactionResponse]] = None

class ChatGifProviderResponse(RustStringEnum):
    Giphy = "giphy"

@dataclass
class ChatGifAttachmentResponse(LongshotModel):
    provider: Optional[ChatGifProviderResponse] = None
    id: Optional[str] = None

@dataclass
class ChatMessageResponse(LongshotModel):
    __serde_skip_none__ = set(["gif", "parent"])
    message_id: Optional[str] = None
    author: Optional[ChatAuthorResponse] = None
    body: Optional[str] = None
    gif: Optional[ChatGifAttachmentResponse] = None
    parent: Optional[str] = None
    reactions: Optional[List[ChatReactionResponse]] = None
    edit_seq: Optional[int] = None
    reaction_seq: Optional[int] = None
    timestamp_ms: Optional[int] = None

@dataclass
class ChatMessageEditResponse(LongshotModel):
    __serde_renames__ = {}
    __serde_skip_none__ = set([])
    __serde_skip_empty__ = set([])
    message_id: Optional[str] = None
    body: Optional[str] = None
    edit_seq: Optional[int] = None
    timestamp_ms: Optional[int] = None

@dataclass
class ChatRecentMessagesResponse(LongshotModel):
    __serde_skip_none__ = set(["next_cursor"])
    messages: Optional[List[ChatMessageResponse]] = None
    next_cursor: Optional[str] = None
    writable: Optional[bool] = None

class ChatStreamErrorCode(RustStringEnum):
    SubscriberLagged = "subscriber_lagged"

@dataclass
class ChatStreamErrorEvent(LongshotModel):
    code: Optional[ChatStreamErrorCode] = None
    message: Optional[str] = None
    skipped: Optional[int] = None

@dataclass
class ListContestsQuery(LongshotModel):
    status: Optional[str] = None
    category: Optional[str] = None
    cursor: Optional[str] = None
    limit: Optional[int] = None

@dataclass
class ContestDetailQuery(LongshotModel):
    survivor_round_limit: Optional[int] = None
    survivor_round_before: Optional[int] = None

@dataclass
class ContestLeaderboardQuery(LongshotModel):
    cursor: Optional[str] = None
    limit: Optional[int] = None
    survivor_round_limit: Optional[int] = None
    survivor_round_before: Optional[int] = None

@dataclass
class ContestTopParticipantsQuery(LongshotModel):
    window_ms: Optional[str] = None
    limit: Optional[int] = None

class FeedFilter(RustStringEnum):
    All = "All"
    Resolved = "Resolved"
    Golden = "Golden"
    Won = "Won"

@dataclass
class FeedRawQuery(LongshotModel):
    filter: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None
    binary_event_market_ids: Optional[str] = None

@dataclass
class FeedEventResponse(LongshotModel):
    __serde_skip_none__ = set(["duration_label","primary_leg","user_handle","user_avatar_url"])
    event_type: Optional[str] = None
    position_id: Optional[str] = None
    market: Optional[str] = None
    duration_label: Optional[str] = None
    primary_leg: Optional[PrimaryLegIdentityResponse] = None
    legs_count: Optional[int] = None
    user_display_name: Optional[str] = None
    user_handle: Optional[str] = None
    user_avatar_seed: Optional[int] = None
    user_avatar_url: Optional[str] = None
    wager_micros: Optional[int] = None
    multiplier_bps: Optional[int] = None
    payout_micros: Optional[int] = None
    event_at_ms: Optional[int] = None

@dataclass
class FeedResponse(LongshotModel):
    __serde_skip_none__ = set(["next_cursor"])
    events: Optional[List[FeedEventResponse]] = None
    next_cursor: Optional[str] = None

class LeaderboardWindow(RustStringEnum):
    Day = "day"
    Week = "week"
    Month = "month"
    AllTime = "all_time"

@dataclass
class LeaderboardRawQuery(LongshotModel):
    period: Optional[str] = None
    scope: Optional[str] = None
    metric: Optional[str] = None
    limit: Optional[int] = None

@dataclass
class LeaderboardMeRawQuery(LongshotModel):
    metric: Optional[str] = None
    window: Optional[str] = None
    asset: Optional[str] = None

@dataclass
class HighlightsRawQuery(LongshotModel):
    sort: Optional[str] = None
    window: Optional[str] = None
    limit: Optional[int] = None

class LeaderboardMetricResponse(RustStringEnum):
    Pnl = "pnl"
    Volume = "volume"
    Roi = "roi"
    Wins = "wins"

class HighlightSortResponse(RustStringEnum):
    Payout = "payout"
    Multiplier = "multiplier"

class LeaderboardPeriod(RustStringEnum):
    Daily = "daily"
    Weekly = "weekly"
    Monthly = "monthly"
    AllTime = "all_time"

class LeaderboardScope(RustStringEnum):
    All = "all"
    Markets = "markets"
    Contests = "contests"

class LeaderboardMetric(RustStringEnum):
    Pnl = "pnl"
    Combo = "combo"

@dataclass
class LeaderboardPnlEntry(LongshotModel):
    rank: Optional[int] = None
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_avatar_url: Optional[str] = None
    entry_count: Optional[int] = None
    pnl_micros: Optional[int] = None

@dataclass
class LeaderboardComboEntry(LongshotModel):
    rank: Optional[int] = None
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_avatar_url: Optional[str] = None
    combo_legs: Optional[int] = None
    multiplier_bps: Optional[int] = None

class LeaderboardEntry(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {"Pnl": "Pnl", "Combo": "Combo"}

    @classmethod
    def pnl(cls, payload: Any = None, **fields: Any) -> LeaderboardEntry:
        return cls("Pnl", payload, **fields)

    @classmethod
    def combo(cls, payload: Any = None, **fields: Any) -> LeaderboardEntry:
        return cls("Combo", payload, **fields)

@dataclass
class LeaderboardPnlCaller(LongshotModel):
    rank: Optional[int] = None
    entry_count: Optional[int] = None
    pnl_micros: Optional[int] = None

@dataclass
class LeaderboardComboCaller(LongshotModel):
    rank: Optional[int] = None
    combo_legs: Optional[int] = None
    multiplier_bps: Optional[int] = None

class LeaderboardCaller(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {"Pnl": "Pnl", "Combo": "Combo"}

    @classmethod
    def pnl(cls, payload: Any = None, **fields: Any) -> LeaderboardCaller:
        return cls("Pnl", payload, **fields)

    @classmethod
    def combo(cls, payload: Any = None, **fields: Any) -> LeaderboardCaller:
        return cls("Combo", payload, **fields)

@dataclass
class LegacyLeaderboardEntry(LongshotModel):
    __serde_skip_none__ = set(["handle","display_name","avatar_seed","x_handle","x_avatar_url"])
    rank: Optional[int] = None
    user_id: Optional[str] = None
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    created_at_ms: Optional[int] = None
    metric_value: Optional[int] = None
    total_positions: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    biggest_win_micros: Optional[int] = None
    highest_multiplier_bps: Optional[int] = None

@dataclass
class LeaderboardResponse(LongshotModel):
    period: Optional[LeaderboardPeriod] = None
    scope: Optional[LeaderboardScope] = None
    metric: Optional[LeaderboardMetric] = None
    period_start_ms: Optional[int] = None
    period_end_ms: Optional[int] = None
    entries: Optional[List[LeaderboardEntry]] = None
    caller: Optional[LeaderboardCaller] = None

@dataclass
class LeaderboardMyRankResponse(LongshotModel):
    entry: Optional[LegacyLeaderboardEntry] = None

@dataclass
class HighlightEntry(LongshotModel):
    __serde_skip_none__ = set(["display_name","avatar_seed","x_handle","x_avatar_url","duration_label","primary_leg"])
    position_id: Optional[str] = None
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    market: Optional[str] = None
    duration_label: Optional[str] = None
    primary_leg: Optional[PrimaryLegIdentityResponse] = None
    legs_count: Optional[int] = None
    wager_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    multiplier_bps: Optional[int] = None

@dataclass
class LeaderboardHighlightsResponse(LongshotModel):
    sort: Optional[HighlightSortResponse] = None
    window: Optional[LeaderboardWindow] = None
    highlights: Optional[List[HighlightEntry]] = None

@dataclass
class PublicMarketsRawQuery(LongshotModel):
    __serde_skip_none__ = set(["statuses"])
    __serde_query_csv__ = set(["statuses"])
    market_type: Optional[MarketType] = None
    source: Optional[str] = None
    source_event_id: Optional[str] = None
    trading_channel: Optional[TradingChannel] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None
    # Statuses use one CSV query value to match the Rust form adapter.
    statuses: Optional[List[MarketStatus]] = None

@dataclass
class EventMarketSource(LongshotModel):
    source: Optional[str] = None
    event_id: Optional[str] = None
    source_market_ids: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None

@dataclass
class PriceStrikeMarket(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    id: Optional[MarketId] = None
    market_type: Optional[MarketType] = None
    trading_channels: Optional[List[TradingChannel]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MarketStatus] = None
    tradeable: Optional[bool] = None
    category_tags: Optional[List[str]] = None
    betting_closes_at_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None
    open_strike_micros: Optional[int] = None
    resolved_outcome: Optional[Outcome] = None
    created_at_ms: Optional[int] = None
    opened_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    image_url: Optional[str] = None

@dataclass
class EventMarket(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    id: Optional[MarketId] = None
    market_type: Optional[MarketType] = None
    trading_channels: Optional[List[TradingChannel]] = None
    chat_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    resolution_rules: Optional[str] = None
    status: Optional[MarketStatus] = None
    tradeable: Optional[bool] = None
    category_tags: Optional[List[str]] = None
    opens_at_ms: Optional[int] = None
    # Provider event start, distinct from Longshot's lifecycle opens_at_ms.
    source_starts_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None
    live_ends_at_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None
    resolved_outcome: Optional[Outcome] = None
    created_at_ms: Optional[int] = None
    opened_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    source: Optional[EventMarketSource] = None
    manual_probability_bps: Optional[int] = None
    image_url: Optional[str] = None

class PublicMarket(RustTaggedUnion):
    __serde_tag__ = None
    __serde_untagged__ = True
    __serde_variants__ = {
            "Event": "Event",
            "PriceStrike": "PriceStrike"
    }

    @classmethod
    def event(cls, payload: Any = None, **fields: Any) -> PublicMarket:
        return cls("Event", payload, **fields)

    @classmethod
    def price_strike(cls, payload: Any = None, **fields: Any) -> PublicMarket:
        return cls("PriceStrike", payload, **fields)

@dataclass
class PublicMarketResponse(LongshotModel):
    market: Optional[PublicMarket] = None

@dataclass
class PublicMarketsResponse(LongshotModel):
    markets: Optional[List[PublicMarket]] = None
    next_cursor: Optional[str] = None

@dataclass
class MarketMetadataEntry(LongshotModel):
    market_id: Optional[int] = None
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    start_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None

@dataclass
class MarketLookupResponse(LongshotModel):
    market: Optional[MarketMetadataEntry] = None

@dataclass
class MarketLookupQuery(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    window_start_ms: Optional[int] = None

@dataclass
class MarketCurrentQuery(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None

@dataclass
class RecentResolutionsQuery(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    limit: Optional[int] = None

@dataclass
class RecentResolutionEntry(LongshotModel):
    market_id: Optional[int] = None
    outcome: Optional[str] = None
    window_start_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None

@dataclass
class RecentResolutionsResponse(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    resolutions: Optional[List[RecentResolutionEntry]] = None

@dataclass
class NotificationsRawQuery(LongshotModel):
    filter: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class NotificationStreamRawQuery(LongshotModel):
    after: Optional[str] = None

class NotificationPayload(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "BinaryEventStartSoon": "binary_event_start_soon",
            "FantasyStartSoon": "fantasy_start_soon",
            "StreakStartSoon": "streak_start_soon",
            "StreakExpiring": "streak_expiring",
            "BinaryEventWin": "binary_event_win",
            "PriceStrikeParlayWin": "price_strike_parlay_win",
            "RfqResult": "rfq_result",
            "FantasyResult": "fantasy_result",
            "PerfectSlate": "perfect_slate",
            "StreakWin": "streak_win",
            "StreakSettled": "streak_settled",
            "PayoutReview": "payout_review",
            "CreditsGranted": "credits_granted",
            "ChatMention": "chat_mention",
            "Unknown": "unknown"
    }

    @classmethod
    def binary_event_start_soon(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("BinaryEventStartSoon", payload, **fields)

    @classmethod
    def fantasy_start_soon(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("FantasyStartSoon", payload, **fields)

    @classmethod
    def streak_start_soon(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("StreakStartSoon", payload, **fields)

    @classmethod
    def streak_expiring(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("StreakExpiring", payload, **fields)

    @classmethod
    def binary_event_win(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("BinaryEventWin", payload, **fields)

    @classmethod
    def price_strike_parlay_win(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("PriceStrikeParlayWin", payload, **fields)

    @classmethod
    def rfq_result(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("RfqResult", payload, **fields)

    @classmethod
    def fantasy_result(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("FantasyResult", payload, **fields)

    @classmethod
    def perfect_slate(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("PerfectSlate", payload, **fields)

    @classmethod
    def streak_win(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("StreakWin", payload, **fields)

    @classmethod
    def streak_settled(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("StreakSettled", payload, **fields)

    @classmethod
    def payout_review(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("PayoutReview", payload, **fields)

    @classmethod
    def credits_granted(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("CreditsGranted", payload, **fields)

    @classmethod
    def chat_mention(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("ChatMention", payload, **fields)

    @classmethod
    def unknown(cls, payload: Any = None, **fields: Any) -> NotificationPayload:
        return cls("Unknown", payload, **fields)

@dataclass
class BinaryEventStartSoonNotificationPayload(LongshotModel):
    source: Optional[str] = None
    event_id: Optional[str] = None
    market_title: Optional[str] = None
    starts_at_ms: Optional[int] = None

@dataclass
class FantasyStartSoonNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_image_scope_id","contest_id","entry_index"])
    pool_image_scope_id: Optional[str] = None
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    contest_title: Optional[str] = None
    starts_at_ms: Optional[int] = None
    selection_count: Optional[int] = None

@dataclass
class StreakStartSoonNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_image_scope_id"])
    pool_image_scope_id: Optional[str] = None
    contest_title: Optional[str] = None
    market_title: Optional[str] = None
    starts_at_ms: Optional[int] = None

@dataclass
class StreakExpiringNotificationPayload(LongshotModel):
    contest_id: Optional[str] = None
    contest_title: Optional[str] = None
    entry_index: Optional[int] = None
    win_streak: Optional[int] = None
    expires_at_ms: Optional[int] = None

@dataclass
class BinaryEventWinNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["source","event_id"])
    __serde_skip_empty__ = set(["market_ids"])
    position_id: Optional[str] = None
    source: Optional[str] = None
    event_id: Optional[str] = None
    net_payout_micros: Optional[int] = None
    multiplier_bps: Optional[int] = None
    market_title: Optional[str] = None
    market_ids: Optional[List[int]] = None

@dataclass
class PriceStrikeParlayWinNotificationPayload(LongshotModel):
    position_id: Optional[str] = None
    net_payout_micros: Optional[int] = None
    multiplier_bps: Optional[int] = None
    leg_summary: Optional[str] = None
    is_multi_asset: Optional[bool] = None
    duration_secs: Optional[List[int]] = None

@dataclass
class RfqResultNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["final_wager_micros","payout_micros","odds"])
    request_id: Optional[str] = None
    status: Optional[RfqResultNotificationStatus] = None
    final_wager_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    odds: Optional[float] = None

class RfqResultNotificationStatus(RustStringEnum):
    Completed = "completed"
    Failed = "failed"
    Cancelled = "cancelled"
    Timeout = "timeout"

class FantasyResultGameType(RustStringEnum):
    Lineups = "lineups"
    Survivor = "survivor"
    Outcast = "outcast"
    Roster = "roster"

@dataclass
class FantasyResultBestEntry(LongshotModel):
    __serde_skip_none__ = set(["correct_count","selection_count"])
    entry_index: Optional[int] = None
    rank: Optional[int] = None
    correct_count: Optional[int] = None
    selection_count: Optional[int] = None

@dataclass
class FantasyResultNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_image_scope_id","best_entry","tiebreaker_result"])
    pool_image_scope_id: Optional[str] = None
    contest_id: Optional[str] = None
    game_index: Optional[int] = None
    game_type: Optional[FantasyResultGameType] = None
    contest_title: Optional[str] = None
    contest_terminal: Optional[bool] = None
    contest_refunded: Optional[bool] = None
    entry_count: Optional[int] = None
    successful_entry_count: Optional[int] = None
    held_entry_count: Optional[int] = None
    credited_payout_micros: Optional[int] = None
    held_payout_micros: Optional[int] = None
    best_entry: Optional[FantasyResultBestEntry] = None
    tiebreaker_result: Optional[int] = None

@dataclass
class PerfectSlateNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_micros","total_winning_entry_count"])
    contest_id: Optional[str] = None
    game_index: Optional[int] = None
    contest_title: Optional[str] = None
    winning_entry_count: Optional[int] = None
    entry_indexes: Optional[List[int]] = None
    payout_micros: Optional[int] = None
    held_entry_count: Optional[int] = None
    pool_micros: Optional[int] = None
    total_winning_entry_count: Optional[int] = None

@dataclass
class StreakWinNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_image_scope_id","contest_id","game_index","market_title","app_token_micros","is_app_token"])
    pool_image_scope_id: Optional[str] = None
    contest_id: Optional[str] = None
    game_index: Optional[int] = None
    contest_title: Optional[str] = None
    market_title: Optional[str] = None
    win_streak: Optional[int] = None
    payout_micros: Optional[int] = None
    app_token_micros: Optional[int] = None
    is_app_token: Optional[bool] = None
    outcome: Optional[StreakWinOutcome] = None

class StreakWinOutcome(RustStringEnum):
    Win = "win"
    WinAndReset = "win_and_reset"

@dataclass
class StreakSettledNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_image_scope_id","market_title"])
    pool_image_scope_id: Optional[str] = None
    contest_title: Optional[str] = None
    market_title: Optional[str] = None
    win_streak: Optional[int] = None
    outcome: Optional[StreakSettledOutcome] = None

class StreakSettledOutcome(RustStringEnum):
    Loss = "loss"

@dataclass
class PayoutReviewNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["pool_image_scope_id","contest_id","entry_index","app_token_micros","is_app_token"])
    pool_image_scope_id: Optional[str] = None
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    contest_title: Optional[str] = None
    payout_micros: Optional[int] = None
    app_token_micros: Optional[int] = None
    is_app_token: Optional[bool] = None
    status: Optional[PayoutReviewNotificationStatus] = None

class PayoutReviewNotificationStatus(RustStringEnum):
    Pending = "pending"
    Approved = "approved"
    Rejected = "rejected"

@dataclass
class CreditsGrantedNotificationPayload(LongshotModel):
    __serde_renames__ = {}
    __serde_skip_none__ = set(["contest_id","game_index"])
    __serde_skip_empty__ = set([])
    grant_id: Optional[str] = None
    amount_micros: Optional[int] = None
    contest_id: Optional[str] = None
    game_index: Optional[int] = None

@dataclass
class ChatMentionNotificationPayload(LongshotModel):
    __serde_skip_none__ = set(["chat_context","contest_id"])
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    chat_context: Optional[ChatMentionContext] = None
    contest_id: Optional[str] = None

class ChatMentionContext(RustStringEnum):
    Contest = "contest"
    CryptoMarket = "crypto_market"

@dataclass
class UnknownNotificationPayload(LongshotModel):
    pass

@dataclass
class NotificationResponse(LongshotModel):
    __serde_renames__ = {"notification_type":"type"}
    __serde_skip_none__ = set(["read_at_ms","image_url"])
    seq: Optional[int] = None
    id: Optional[str] = None
    notification_type: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    icon: Optional[str] = None
    payload: Optional[NotificationPayload] = None
    created_at_ms: Optional[int] = None
    read_at_ms: Optional[int] = None
    image_url: Optional[str] = None

@dataclass
class NotificationsResponse(LongshotModel):
    __serde_skip_none__ = set(["next_cursor"])
    notifications: Optional[List[NotificationResponse]] = None
    next_cursor: Optional[str] = None
    unread_count: Optional[int] = None

@dataclass
class NotificationMutationResponse(LongshotModel):
    notification: Optional[NotificationResponse] = None
    unread_count: Optional[int] = None

@dataclass
class NotificationBulkMutationResponse(LongshotModel):
    updated_count: Optional[int] = None
    unread_count: Optional[int] = None

@dataclass(frozen=True)
class PoolImageRawBytes:
    value: bytes = b""

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", bytes(self.value))

    def as_bytes(self) -> bytes:
        return self.value

    def __bytes__(self) -> bytes:
        return self.value

@dataclass
class PortfolioIntegrityErrorResponse(LongshotModel):
    __serde_skip_none__ = set(["leg_index"])
    position_id: Optional[str] = None
    leg_index: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None

@dataclass
class PortfolioStatsResponse(LongshotModel):
    total_positions: Optional[int] = None
    open_positions: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    win_rate_pct: Optional[float] = None
    total_pnl_micros: Optional[int] = None

class PnlHistoryQueryParseError(RustStringEnum):
    InvalidWindowRange = "InvalidWindowRange"

@dataclass
class PnlHistoryQuery(LongshotModel):
    __serde_renames__ = {"from_":"from"}
    from_: Optional[int] = None
    to: Optional[int] = None

@dataclass
class PnlEventResponse(LongshotModel):
    source: Optional[str] = None
    resolved_at_ms: Optional[int] = None
    position_id: Optional[str] = None
    contest_id: Optional[str] = None
    pnl_micros: Optional[int] = None
    cumulative_micros: Optional[int] = None

@dataclass
class PnlHistoryResponse(LongshotModel):
    events: Optional[List[PnlEventResponse]] = None

@dataclass
class FantasyEntriesQuery(LongshotModel):
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class PortfolioFantasyEntryResponse(LongshotModel):
    __serde_skip_none__ = set([
        "survivor_round_count",
        "current_game_index",
        "image_url",
        "survivor",
    ])
    contest_id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    game_type: Optional[ContestGameTypeResponse] = None
    survivor_round_count: Optional[int] = None
    current_game_index: Optional[int] = None
    bet_amount_micros: Optional[int] = None
    protocol_prize_pool_micros: Optional[int] = None
    total_pot_micros: Optional[int] = None
    entries_filled: Optional[int] = None
    entry_cap: Optional[int] = None
    entry_opens_at_ms: Optional[int] = None
    betting_closes_ms: Optional[int] = None
    live_ends_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    joined_at_ms: Optional[int] = None
    entry_index: Optional[int] = None
    open_leg_count: Optional[int] = None
    resolved_win_count: Optional[int] = None
    rank: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    refunded: Optional[bool] = None
    pnl_micros: Optional[int] = None
    image_url: Optional[str] = None
    survivor: Optional[SurvivorEntryStateResponse] = None
    selection_count: Optional[int] = None
    survivor_voided_round_count: Optional[int] = None
    betting_opens_ms: Optional[int] = None

@dataclass
class PortfolioFantasyEntriesResponse(LongshotModel):
    entries: Optional[List[PortfolioFantasyEntryResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class PositionsQuery(LongshotModel):
    status: Optional[str] = None
    sort: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

class PositionStatusQueryParam(RustStringEnum):
    Open = "open"
    Won = "won"
    Lost = "lost"
    Voided = "voided"

class PositionSortQueryParam(RustStringEnum):
    DateDesc = "date_desc"
    DateAsc = "date_asc"
    PnlDesc = "pnl_desc"
    PnlAsc = "pnl_asc"

class CursorParseError(RustStringEnum):
    InvalidFormat = "InvalidFormat"
    InvalidValue = "InvalidValue"
    ValueOutOfRange = "ValueOutOfRange"
    InvalidPositionId = "InvalidPositionId"

class PositionQueryParseError(RustStringEnum):
    InvalidStatus = "InvalidStatus"
    InvalidSort = "InvalidSort"

@dataclass
class PositionSummary(LongshotModel):
    id: Optional[str] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    refunded_app_token_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    legs_count: Optional[int] = None
    legs_summary: Optional[str] = None
    status: Optional[str] = None
    pnl_micros: Optional[int] = None
    created_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    has_binary_event_leg: Optional[bool] = None
    market_types: Optional[List[MarketType]] = None

@dataclass
class PositionsListResponse(LongshotModel):
    __serde_skip_empty__ = set(["errors"])
    positions: Optional[List[PositionSummary]] = None
    next_cursor: Optional[str] = None
    partial: Optional[bool] = None
    errors: Optional[List[PortfolioIntegrityErrorResponse]] = None

class ActivePositionStatus(RustStringEnum):
    Pending = "pending"
    Open = "open"

class PositionRole(RustStringEnum):
    Taker = "taker"
    Maker = "maker"

@dataclass
class ActivePosition(LongshotModel):
    """Active taker or maker position in a complete portfolio snapshot."""

    position_id: Optional[PositionId] = None
    status: Optional[ActivePositionStatus] = None
    role: Optional[PositionRole] = None
    taker_address: Optional[Address] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    legs: Optional[List[LegDetail]] = None

@dataclass
class ActivePositionsResponse(LongshotModel):
    positions: Optional[List[ActivePosition]] = None

@dataclass
class LegDetail(LongshotModel):
    __serde_skip_none__ = set(["market_type","label","asset","duration_secs","window_start_ms"])
    leg_index: Optional[int] = None
    market_id: Optional[int] = None
    market_type: Optional[MarketType] = None
    label: Optional[str] = None
    asset: Optional[str] = None
    direction: Optional[str] = None
    duration_secs: Optional[int] = None
    outcome: Optional[str] = None
    window_start_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None

@dataclass
class PositionDetailResponse(LongshotModel):
    id: Optional[str] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    refunded_app_token_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    legs_count: Optional[int] = None
    legs_summary: Optional[str] = None
    status: Optional[str] = None
    pnl_micros: Optional[int] = None
    created_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    legs: Optional[List[LegDetail]] = None

@dataclass
class PreferencesResponse(LongshotModel):
    notifications_enabled: Optional[bool] = None
    quote_tolerance: Optional[QuoteTolerancePreference] = None
    anonymous_mode_enabled: Optional[bool] = None

class QuoteTolerancePreference(RustStringEnum):
    Strict = "strict"
    Normal = "normal"
    Lenient = "lenient"

@dataclass
class UpdatePreferencesRequest(LongshotModel):
    notifications_enabled: Optional[bool] = None
    quote_tolerance: Optional[QuoteTolerancePreference] = None
    anonymous_mode_enabled: Optional[bool] = None

@dataclass
class PrimaryLegIdentityResponse(LongshotModel):
    __serde_skip_none__ = set(["asset","duration_secs","duration_label"])
    market_type: Optional[MarketType] = None
    market_id: Optional[int] = None
    label: Optional[str] = None
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    duration_label: Optional[str] = None

@dataclass
class CheckHandleQuery(LongshotModel):
    handle: Optional[str] = None

@dataclass
class ProfileResponse(LongshotModel):
    __serde_skip_none__ = set(["email","x_handle","x_avatar_url"])
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    email: Optional[str] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    created_at_ms: Optional[int] = None
    updated_at_ms: Optional[int] = None
    referral_code: Optional[str] = None

@dataclass
class PublicProfileResponse(LongshotModel):
    __serde_skip_none__ = set(["x_handle","x_avatar_url"])
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    created_at_ms: Optional[int] = None
    stats: Optional[PublicProfileStatsResponse] = None
    top_ten_finishes: Optional[int] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None

@dataclass
class PublicProfileStatsResponse(LongshotModel):
    total_positions: Optional[int] = None
    open_positions: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    win_rate_pct: Optional[float] = None
    total_pnl_micros: Optional[int] = None

@dataclass
class PublicProfilePnlEventResponse(LongshotModel):
    source: Optional[str] = None
    resolved_at_ms: Optional[int] = None
    position_id: Optional[str] = None
    contest_id: Optional[str] = None
    pnl_micros: Optional[int] = None
    cumulative_micros: Optional[int] = None

@dataclass
class PublicProfilePnlHistoryResponse(LongshotModel):
    events: Optional[List[PublicProfilePnlEventResponse]] = None

@dataclass
class PublicProfileFantasyEntryResponse(LongshotModel):
    __serde_skip_none__ = set([
        "survivor_round_count",
        "current_game_index",
        "image_url",
        "survivor",
    ])
    contest_id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    game_type: Optional[ContestGameTypeResponse] = None
    survivor_round_count: Optional[int] = None
    current_game_index: Optional[int] = None
    bet_amount_micros: Optional[int] = None
    protocol_prize_pool_micros: Optional[int] = None
    total_pot_micros: Optional[int] = None
    entries_filled: Optional[int] = None
    entry_cap: Optional[int] = None
    entry_opens_at_ms: Optional[int] = None
    betting_closes_ms: Optional[int] = None
    live_ends_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    joined_at_ms: Optional[int] = None
    entry_index: Optional[int] = None
    open_leg_count: Optional[int] = None
    resolved_win_count: Optional[int] = None
    rank: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    refunded: Optional[bool] = None
    pnl_micros: Optional[int] = None
    image_url: Optional[str] = None
    survivor: Optional[SurvivorEntryStateResponse] = None
    selection_count: Optional[int] = None
    survivor_voided_round_count: Optional[int] = None
    betting_opens_ms: Optional[int] = None

@dataclass
class PublicProfileFantasyEntriesResponse(LongshotModel):
    entries: Optional[List[PublicProfileFantasyEntryResponse]] = None
    next_cursor: Optional[str] = None

class PublicProfileContestOwnerEntryVisibilityResponse(RustStringEnum):
    HiddenWhileBettingOpen = "hidden_while_betting_open"
    Visible = "visible"

@dataclass
class PublicProfileContestOwnerResponse(LongshotModel):
    joined: Optional[bool] = None
    entry_visibility: Optional[PublicProfileContestOwnerEntryVisibilityResponse] = None
    entries: Optional[List[ContestUserEntryResponse]] = None

@dataclass
class PublicProfileContestDetailResponse(LongshotModel):
    __serde_flatten__ = set(["contest"])
    contest: Optional[PublicContestDetailResponse] = None
    profile_owner: Optional[PublicProfileContestOwnerResponse] = None

@dataclass
class PublicProfilePositionSummaryResponse(LongshotModel):
    id: Optional[str] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    refunded_app_token_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    legs_count: Optional[int] = None
    legs_summary: Optional[str] = None
    status: Optional[str] = None
    pnl_micros: Optional[int] = None
    created_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    has_binary_event_leg: Optional[bool] = None
    market_types: Optional[List[MarketType]] = None

@dataclass
class PublicProfilePositionsResponse(LongshotModel):
    positions: Optional[List[PublicProfilePositionSummaryResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class PublicProfilePositionDetailResponse(LongshotModel):
    id: Optional[str] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    refunded_app_token_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    legs_count: Optional[int] = None
    legs_summary: Optional[str] = None
    status: Optional[str] = None
    pnl_micros: Optional[int] = None
    created_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    legs: Optional[List[LegDetail]] = None

@dataclass
class UpdateProfileRequest(LongshotModel):
    handle: Optional[str] = None
    display_name: Optional[str] = None

@dataclass
class SyncXProfileRequest(LongshotModel):
    privy_token: Optional[str] = None

@dataclass
class CheckHandleResponse(LongshotModel):
    __serde_skip_none__ = set(["reason"])
    available: Optional[bool] = None
    reason: Optional[str] = None

@dataclass
class CreateSessionRequest(LongshotModel):
    __serde_skip_none__ = set(["auth_wallet_address", "referral_code"])
    privy_token: Optional[str] = None
    auth_wallet_address: Optional[str] = None
    referral_code: Optional[str] = None

@dataclass
class WalletAuthRequest(LongshotModel):
    __serde_skip_none__ = set(["referral_code"])
    address: Optional[str] = None
    signature: Optional[str] = None
    signed_at_ms: Optional[int] = None
    referral_code: Optional[str] = None

@dataclass
class ChatPostMessageRequest(LongshotModel):
    body: Optional[str] = None
    chat_id: Optional[str] = None
    parent: Optional[str] = None

@dataclass
class ChatEditMessageRequest(LongshotModel):
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    body: Optional[str] = None

@dataclass
class ChatEmojiReactRequest(LongshotModel):
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    emoji_code: Optional[str] = None

@dataclass
class ChatStreamQuery(LongshotModel):
    chat_id: Optional[str] = None

@dataclass
class ChatMentionCandidatesQuery(LongshotModel):
    chat_id: Optional[str] = None

@dataclass
class ChatRecentMessagesQuery(LongshotModel):
    chat_id: Optional[str] = None
    limit: Optional[int] = None
    before: Optional[str] = None

@dataclass
class UserSetReferrerRequest(LongshotModel):
    referral_code: Optional[str] = None

@dataclass
class UserCreateReferralCodeRequest(LongshotModel):
    code: Optional[str] = None

@dataclass
class PlaceContestBetSelectionRequest(LongshotModel):
    market_id: Optional[int] = None
    direction: Optional[str] = None

@dataclass
class PlaceRosterPickRequest(LongshotModel):
    __serde_renames__ = {}
    __serde_skip_none__ = set([])
    __serde_skip_empty__ = set([])
    tier_index: Optional[int] = None
    selection_index: Optional[int] = None

@dataclass
class PlaceContestBetRequest(LongshotModel):
    """Request to place contest picks.

    ``entry_index`` is a stable zero-based entry slot. It is optional for
    legacy single-entry and non-Survivor requests. For a new opening-round
    entry in a multi-entry Survivor contest, send the next contiguous index;
    reuse that same index for void replacements and later rounds.
    """
    contest_id: Optional[str] = None
    use_app_tokens: Optional[bool] = None
    entry_index: Optional[int] = None
    bets: Optional[List[PlaceContestBetSelectionRequest]] = None
    roster_picks: Optional[List[PlaceRosterPickRequest]] = None
    tiebreaker_guess: Optional[int] = None

@dataclass
class UserDepositRequest(LongshotModel):
    amount_micros: Optional[int] = None
    idempotency_key: Optional[str] = None

@dataclass
class UserWithdrawParams(LongshotModel):
    amount_micros: Optional[int] = None
    destination_address: Optional[str] = None
    idempotency_key: Optional[str] = None

class WithdrawalAuthorization(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "PrivyToken": "privy_token",
            "WalletSignature": "wallet_signature"
    }

    @classmethod
    def privy_token(cls, payload: Any = None, **fields: Any) -> WithdrawalAuthorization:
        return cls("PrivyToken", payload, **fields)

    @classmethod
    def wallet_signature(cls, payload: Any = None, **fields: Any) -> WithdrawalAuthorization:
        return cls("WalletSignature", payload, **fields)

@dataclass
class UserWithdrawRequest(LongshotModel):
    withdraw_params: Optional[UserWithdrawParams] = None
    authorization: Optional[WithdrawalAuthorization] = None

@dataclass
class OrderLegJson(LongshotModel):
    market_id: Optional[int] = None
    direction: Optional[str] = None

@dataclass
class SignedOrderJson(LongshotModel):
    user: Optional[str] = None
    wager_micros: Optional[int] = None
    min_odds: Optional[float] = None
    legs: Optional[List[OrderLegJson]] = None
    nonce: Optional[int] = None
    expires_at_ms: Optional[int] = None
    order_type: Optional[int] = None
    shield_on: Optional[bool] = None
    signature: Optional[str] = None

class CommunityPickMode(RustStringEnum):
    Tail = "tail"
    Fade = "fade"

@dataclass
class CommunityPickRequest(LongshotModel):
    source_position_id: Optional[PositionId] = None
    mode: Optional[CommunityPickMode] = None

@dataclass
class CreateRfqRequest(LongshotModel):
    order: Optional[SignedOrderJson] = None
    use_app_tokens: Optional[bool] = None

@dataclass
class UnsignedRfqOrderRequest(LongshotModel):
    wager_micros: Optional[int] = None
    min_odds: Optional[float] = None
    legs: Optional[List[OrderLegJson]] = None
    order_type: Optional[int] = None
    shield_on: Optional[bool] = None
    idempotency_key: Optional[str] = None

@dataclass
class CreateUnsignedRfqRequest(LongshotModel):
    __serde_skip_none__ = set(["community_pick"])
    privy_token: Optional[str] = None
    use_app_tokens: Optional[bool] = None
    rfq_params: Optional[UnsignedRfqOrderRequest] = None
    community_pick: Optional[CommunityPickRequest] = None

@dataclass
class ParsedOrderLeg(LongshotModel):
    market_id: Optional[MarketId] = None
    direction: Optional[Direction] = None

class OrderLegParseError(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "InvalidMarketId": "InvalidMarketId",
            "InvalidDirection": "InvalidDirection"
    }

    @classmethod
    def invalid_market_id(cls, payload: Any = None, **fields: Any) -> OrderLegParseError:
        return cls("InvalidMarketId", payload, **fields)

    @classmethod
    def invalid_direction(cls, payload: Any = None, **fields: Any) -> OrderLegParseError:
        return cls("InvalidDirection", payload, **fields)

class RfqOrderJsonError(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "InvalidAddress": "InvalidAddress",
            "InvalidMinOdds": "InvalidMinOdds",
            "MissingLegs": "MissingLegs",
            "TooManyLegs": "TooManyLegs",
            "InvalidOrderType": "InvalidOrderType",
            "InvalidSignatureFormat": "InvalidSignatureFormat",
            "InvalidIdempotencyKey": "InvalidIdempotencyKey",
            "InvalidLegMarketId": "InvalidLegMarketId",
            "InvalidLegDirection": "InvalidLegDirection"
    }

    @classmethod
    def invalid_address(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidAddress", payload, **fields)

    @classmethod
    def invalid_min_odds(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidMinOdds", payload, **fields)

    @classmethod
    def missing_legs(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("MissingLegs", payload, **fields)

    @classmethod
    def too_many_legs(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("TooManyLegs", payload, **fields)

    @classmethod
    def invalid_order_type(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidOrderType", payload, **fields)

    @classmethod
    def invalid_signature_format(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidSignatureFormat", payload, **fields)

    @classmethod
    def invalid_idempotency_key(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidIdempotencyKey", payload, **fields)

    @classmethod
    def invalid_leg_market_id(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidLegMarketId", payload, **fields)

    @classmethod
    def invalid_leg_direction(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidLegDirection", payload, **fields)

@dataclass
class AccessResponse(LongshotModel):
    __serde_skip_none__ = set(["reason_code"])
    position_opening_allowed: Optional[bool] = None
    reason_code: Optional[str] = None

@dataclass
class SessionResponse(LongshotModel):
    __serde_skip_none__ = set(["deposit_address","deposit_chain_id"])
    session_token: Optional[str] = None
    address: Optional[str] = None
    auth_wallet_address: Optional[str] = None
    deposit_address: Optional[str] = None
    deposit_chain_id: Optional[int] = None
    user_id: Optional[str] = None
    expires_at: Optional[int] = None
    account_created: Optional[bool] = False
    onboarding_completed: Optional[bool] = False

    def __repr__(self) -> str:
        session_token = "'<redacted>'" if self.session_token else "None"
        return (
            "SessionResponse("
            f"session_token={session_token}"
            f", address={self.address!r}"
            f", auth_wallet_address={self.auth_wallet_address!r}"
            f", deposit_address={self.deposit_address!r}"
            f", deposit_chain_id={self.deposit_chain_id!r}"
            f", user_id={self.user_id!r}"
            f", expires_at={self.expires_at!r}"
            f", account_created={self.account_created!r}"
            f", onboarding_completed={self.onboarding_completed!r})"
        )

class RfqStatus(RustStringEnum):
    Pending = "pending"
    Finalizing = "finalizing"
    Completed = "completed"
    Failed = "failed"
    Cancelled = "cancelled"
    Timeout = "timeout"

@dataclass
class RfqResponse(LongshotModel):
    __serde_skip_none__ = set(["payout_micros","error"])
    __serde_skip_non_finite__ = set(["odds"])
    request_id: Optional[UUID] = None
    status: Optional[RfqStatus] = None
    odds: Optional[float] = None
    payout_micros: Optional[int] = None
    error: Optional[str] = None
    quotes_received: Optional[int] = None

@dataclass
class CancelResponse(LongshotModel):
    request_id: Optional[str] = None
    cancelled: Optional[bool] = None
    message: Optional[str] = None

@dataclass
class UserDepositResponse(LongshotModel):
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    tx_hash: Optional[str] = None

@dataclass
class UserDepositWalletResponse(LongshotModel):
    __serde_skip_none__ = set(["chain_id"])
    address: Optional[str] = None
    chain_id: Optional[int] = None
    token_symbol: Optional[str] = None
    token_decimals: Optional[int] = None

@dataclass
class UserWithdrawResponse(LongshotModel):
    __serde_skip_none__ = set(["destination_address"])
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    destination_address: Optional[str] = None
    tx_hash: Optional[str] = None

class BalanceOperationStatus(RustStringEnum):
    Pending = "pending"
    Failed = "failed"
    Success = "success"
    Recovering = "recovering"

@dataclass
class BalanceOperationStatusResponse(LongshotModel):
    __serde_skip_none__ = set(["wallet_address"])
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    status: Optional[BalanceOperationStatus] = None
    wallet_address: Optional[str] = None

class DepositOperationResponse(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {
            "Completed": "Completed",
            "OperationStatus": "OperationStatus"
    }

    @classmethod
    def completed(cls, payload: Any = None, **fields: Any) -> DepositOperationResponse:
        return cls("Completed", payload, **fields)

    @classmethod
    def operation_status(cls, payload: Any = None, **fields: Any) -> DepositOperationResponse:
        return cls("OperationStatus", payload, **fields)

class WithdrawOperationResponse(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {
            "Completed": "Completed",
            "OperationStatus": "OperationStatus"
    }

    @classmethod
    def completed(cls, payload: Any = None, **fields: Any) -> WithdrawOperationResponse:
        return cls("Completed", payload, **fields)

    @classmethod
    def operation_status(cls, payload: Any = None, **fields: Any) -> WithdrawOperationResponse:
        return cls("OperationStatus", payload, **fields)

@dataclass
class AvailableBalanceResponse(LongshotModel):
    available_micros: Optional[int] = None

@dataclass
class ReservedBalanceResponse(LongshotModel):
    reserved_micros: Optional[int] = None

class UserTransactionCategory(RustStringEnum):
    Deposit = "deposit"
    Withdrawal = "withdrawal"
    Credits = "credits"
    Market = "market"
    Contest = "contest"

class UserTransactionStatus(RustStringEnum):
    Completed = "completed"
    Pending = "pending"
    Failed = "failed"
    Expired = "expired"
    Entered = "entered"
    Won = "won"

class UserTransactionUnit(RustStringEnum):
    Usdc = "usdc"
    Credits = "credits"

class UserTransactionFunding(RustStringEnum):
    Cash = "cash"
    Credits = "credits"
    CashAndCredits = "cash_and_credits"

@dataclass
class UserTransactionResponse(LongshotModel):
    __serde_skip_none__ = set(["detail","expires_at_ms","funding","network","reason","reference","source","tx_hash","wallet_address"])
    id: Optional[str] = None
    category: Optional[UserTransactionCategory] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    status: Optional[UserTransactionStatus] = None
    occurred_at_ms: Optional[int] = None
    amount_micros: Optional[int] = None
    unit: Optional[UserTransactionUnit] = None
    funding: Optional[UserTransactionFunding] = None
    network: Optional[str] = None
    wallet_address: Optional[str] = None
    tx_hash: Optional[str] = None
    source: Optional[str] = None
    expires_at_ms: Optional[int] = None
    reason: Optional[str] = None
    reference: Optional[str] = None

@dataclass
class UserTransactionsResponse(LongshotModel):
    items: Optional[List[UserTransactionResponse]] = None
    next_cursor: Optional[str] = None

class FeeScheduleTier(RustStringEnum):
    Standard = "standard"
    Silver = "silver"
    Gold = "gold"
    Platinum = "platinum"
    Vip = "vip"

@dataclass
class TierFeeRate(LongshotModel):
    tier: Optional[FeeScheduleTier] = None
    parlay_fee_bps: Optional[int] = None

@dataclass
class FeeScheduleResponse(LongshotModel):
    user_tier: Optional[FeeScheduleTier] = None
    parlay_fee_bps: Optional[int] = None
    spot_fee_bps: Optional[int] = None
    bonding_spot_fee_bps: Optional[int] = None
    shield_fee_multiplier: Optional[int] = None
    tiers: Optional[List[TierFeeRate]] = None

@dataclass
class PlaceContestBetResponse(LongshotModel):
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    reserved_micros: Optional[int] = None

class ContestCategoryResponse(RustStringEnum):
    Mentions = "mentions"
    Sports = "sports"
    Culture = "culture"

class ContestStatusResponse(RustStringEnum):
    Open = "open"
    Resolved = "resolved"
    Voided = "voided"

class ContestBetTypeResponse(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_content__ = "value"
    __serde_variants__ = {
            "NumBets": "num_bets",
            "BetsPerCategory": "bets_per_category"
    }

    @classmethod
    def num_bets(cls, payload: Any = None, **fields: Any) -> ContestBetTypeResponse:
        return cls("NumBets", payload, **fields)

    @classmethod
    def bets_per_category(cls, payload: Any = None, **fields: Any) -> ContestBetTypeResponse:
        return cls("BetsPerCategory", payload, **fields)

class ContestGameTypeResponse(RustStringEnum):
    Lineups = "lineups"
    Survivor = "survivor"
    Streak = "streak"
    Outcast = "outcast"
    Roster = "roster"

class SurvivorPhaseResponse(RustStringEnum):
    Scheduled = "scheduled"
    PickOpen = "pick_open"
    PickLocked = "pick_locked"
    Live = "live"
    RoundSettled = "round_settled"
    AwaitingNextRound = "awaiting_next_round"
    ContestSettled = "contest_settled"
    Voided = "voided"

class SurvivorRoundStatusResponse(RustStringEnum):
    Scheduled = "scheduled"
    PickOpen = "pick_open"
    PickLocked = "pick_locked"
    Live = "live"
    Settled = "settled"
    Voided = "voided"

class SurvivorEntryRoundResultResponse(RustStringEnum):
    Pending = "pending"
    Won = "won"
    Lost = "lost"
    Missed = "missed"
    Voided = "voided"

class SurvivorEliminationReasonResponse(RustStringEnum):
    IncorrectPick = "incorrect_pick"
    MissedDeadline = "missed_deadline"

class ContestDirectionResponse(RustStringEnum):
    Up = "up"
    Down = "down"

class ContestLegOutcome(RustStringEnum):
    Pending = "pending"
    Won = "won"
    Lost = "lost"
    Voided = "voided"

@dataclass
class ContestPerfectSlateResponse(LongshotModel):
    payout_micros: Optional[int] = None
    winner_count: Optional[int] = None

@dataclass
class PublicContestSummaryResponse(LongshotModel):
    __serde_skip_none__ = set([
        "game_type",
        "survivor_awaiting_replacement",
        "survivor_current_game_index",
        "image_url",
    ])
    contest_id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[ContestCategoryResponse] = None
    status: Optional[ContestStatusResponse] = None
    game_type: Optional[ContestGameTypeResponse] = None
    survivor_awaiting_replacement: Optional[bool] = None
    survivor_current_game_index: Optional[int] = None
    bet_amount_micros: Optional[int] = None
    protocol_prize_pool_micros: Optional[int] = None
    total_pot_micros: Optional[int] = None
    prize_pool_growth_starts_after_entries: Optional[int] = None
    perfect_slate: Optional[ContestPerfectSlateResponse] = None
    featured_slot: Optional[int] = None
    entries_filled: Optional[int] = None
    entry_cap: Optional[int] = None
    entry_opens_at_ms: Optional[int] = None
    betting_closes_ms: Optional[int] = None
    live_ends_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    created_at_ms: Optional[int] = None
    image_url: Optional[str] = None

@dataclass
class ContestCallerSummaryResponse(LongshotModel):
    joined: Optional[bool] = None
    entry_count: Optional[int] = None

@dataclass
class CallerContestSummaryResponse(LongshotModel):
    __serde_flatten__ = set(["contest"])
    contest: Optional[PublicContestSummaryResponse] = None
    caller: Optional[ContestCallerSummaryResponse] = None

@dataclass
class ContestLobbySummaryResponse(LongshotModel):
    __serde_flatten__ = set(["summary"])
    summary: Optional[CallerContestSummaryResponse] = None
    description: Optional[str] = None
    max_entries_per_player: Optional[int] = None
    protocol_prize_pool_pays_app_tokens: Optional[bool] = None

@dataclass
class CallerContestsListResponse(LongshotModel):
    contests: Optional[List[ContestLobbySummaryResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class ContestMarketResponse(LongshotModel):
    __serde_skip_none__ = set(["image_url", "opens_at_ms"])
    market_id: Optional[int] = None
    selection_group: Optional[str] = None
    market_type: Optional[MarketType] = None
    trading_channels: Optional[List[TradingChannel]] = None
    name: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    resolution_rules: Optional[str] = None
    status: Optional[MarketStatus] = None
    outcome: Optional[Outcome] = None
    source: Optional[EventMarketSource] = None
    betting_closes_at_ms: Optional[int] = None
    opens_at_ms: Optional[int] = None
    live_ends_at_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None
    manual_probability_bps: Optional[int] = None
    manual_live_state: Optional[Any] = None

@dataclass
class ContestUserPickResponse(LongshotModel):
    market_id: Optional[int] = None
    direction: Optional[ContestDirectionResponse] = None
    outcome: Optional[ContestLegOutcome] = None

class SurvivorRoundPicksResponse(RustTaggedUnion):
    __serde_tag__ = "visibility"
    __serde_variants__ = {
            "Hidden": "hidden",
            "Revealed": "revealed"
    }

    @classmethod
    def hidden(cls, payload: Any = None, **fields: Any) -> SurvivorRoundPicksResponse:
        return cls("Hidden", payload, **fields)

    @classmethod
    def revealed(cls, payload: Any = None, **fields: Any) -> SurvivorRoundPicksResponse:
        return cls("Revealed", payload, **fields)

@dataclass
class SurvivorMarketPickCountsResponse(LongshotModel):
    market_id: Optional[int] = None
    up_count: Optional[int] = None
    down_count: Optional[int] = None

@dataclass
class SurvivorRoundBreakdownResponse(LongshotModel):
    eligible_entry_count: Optional[int] = None
    submitted_entry_count: Optional[int] = None
    missed_entry_count: Optional[int] = None
    markets: Optional[List[SurvivorMarketPickCountsResponse]] = None

@dataclass
class SurvivorRoundResponse(LongshotModel):
    __serde_skip_none__ = set(["resolved_at_ms", "breakdown"])
    game_index: Optional[int] = None
    status: Optional[SurvivorRoundStatusResponse] = None
    required_pick_count: Optional[int] = None
    betting_opens_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    markets: Optional[List[ContestMarketResponse]] = None
    breakdown: Optional[SurvivorRoundBreakdownResponse] = None

@dataclass
class SurvivorEntryRoundResponse(LongshotModel):
    game_index: Optional[int] = None
    result: Optional[SurvivorEntryRoundResultResponse] = None
    picks: Optional[SurvivorRoundPicksResponse] = None

class SurvivorEntryStateResponse(RustTaggedUnion):
    __serde_tag__ = "status"
    __serde_variants__ = {
            "Alive": "alive",
            "Eliminated": "eliminated",
            "Winner": "winner",
            "Voided": "voided"
    }

    @classmethod
    def alive(cls, payload: Any = None, **fields: Any) -> SurvivorEntryStateResponse:
        return cls("Alive", payload, **fields)

    @classmethod
    def eliminated(cls, payload: Any = None, **fields: Any) -> SurvivorEntryStateResponse:
        return cls("Eliminated", payload, **fields)

    @classmethod
    def winner(cls, payload: Any = None, **fields: Any) -> SurvivorEntryStateResponse:
        return cls("Winner", payload, **fields)

    @classmethod
    def voided(cls, payload: Any = None, **fields: Any) -> SurvivorEntryStateResponse:
        return cls("Voided", payload, **fields)

@dataclass
class SurvivorContestResponse(LongshotModel):
    __serde_skip_none__ = set(["next_game_index", "rounds_next_cursor"])
    version: Optional[int] = None
    round_count: Optional[int] = None
    phase: Optional[SurvivorPhaseResponse] = None
    current_game_index: Optional[int] = None
    next_game_index: Optional[int] = None
    rounds: Optional[List[SurvivorRoundResponse]] = None
    rounds_next_cursor: Optional[int] = None
    revealed_game_indexes: Optional[List[int]] = None
    remaining_survivor_count: Optional[int] = None

@dataclass
class ContestRosterSelectionResponse(LongshotModel):
    selection_index: Optional[int] = None
    name: Optional[str] = None
    image_url: Optional[str] = None
    avg_points_milli: Optional[int] = None
    points_milli: Optional[int] = None
    final_points_milli: Optional[int] = None
    live_state: Optional[Any] = None
    metadata: Optional[Any] = None
    updated_at_ms: Optional[int] = None

@dataclass
class ContestRosterTierResponse(LongshotModel):
    tier_index: Optional[int] = None
    name: Optional[str] = None
    selections: Optional[List[ContestRosterSelectionResponse]] = None

@dataclass
class ContestRosterResponse(LongshotModel):
    tiers: Optional[List[ContestRosterTierResponse]] = None

@dataclass
class ContestRosterPickResponse(LongshotModel):
    tier_index: Optional[int] = None
    selection_index: Optional[int] = None

@dataclass
class SurvivorTeamUsageResponse(LongshotModel):
    source_team_id: Optional[str] = None
    used_game_index: Optional[int] = None

@dataclass
class ContestUserEntryResponse(LongshotModel):
    __serde_skip_none__ = set([
        "roster_picks",
        "roster_points_milli",
        "survivor",
        "survivor_team_usage",
    ])
    entry_index: Optional[int] = None
    created_at_ms: Optional[int] = None
    picks: Optional[List[ContestUserPickResponse]] = None
    open_leg_count: Optional[int] = None
    resolved_win_count: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    refunded: Optional[bool] = None
    rank: Optional[int] = None
    tiebreaker_guess: Optional[int] = None
    perfect_slate_won: Optional[bool] = None
    perfect_slate_payout_micros: Optional[int] = None
    roster_picks: Optional[List[ContestRosterPickResponse]] = None
    roster_points_milli: Optional[int] = None
    survivor: Optional[SurvivorEntryStateResponse] = None
    survivor_team_usage: Optional[List[SurvivorTeamUsageResponse]] = None

@dataclass
class ContestTiebreakerResponse(LongshotModel):
    enabled: Optional[bool] = None
    hint: Optional[str] = None
    result: Optional[int] = None

@dataclass
class PublicContestDetailResponse(LongshotModel):
    __serde_flatten__ = set(["summary"])
    __serde_skip_none__ = set(["roster", "survivor"])
    summary: Optional[PublicContestSummaryResponse] = None
    max_entries_per_player: Optional[int] = None
    description: Optional[str] = None
    bet_type: Optional[ContestBetTypeResponse] = None
    winning_split_bps: Optional[List[int]] = None
    protocol_winning_split_bps: Optional[List[int]] = None
    protocol_prize_pool_pays_app_tokens: Optional[bool] = None
    tiebreaker: Optional[ContestTiebreakerResponse] = None
    markets: Optional[List[ContestMarketResponse]] = None
    roster: Optional[ContestRosterResponse] = None
    survivor: Optional[SurvivorContestResponse] = None

@dataclass
class ContestCallerDetailResponse(LongshotModel):
    joined: Optional[bool] = None
    entries: Optional[List[ContestUserEntryResponse]] = None

@dataclass
class CallerContestDetailResponse(LongshotModel):
    __serde_flatten__ = set(["contest"])
    contest: Optional[PublicContestDetailResponse] = None
    caller: Optional[ContestCallerDetailResponse] = None

@dataclass
class ContestLeaderboardRowResponse(LongshotModel):
    __serde_skip_none__ = set(["roster_picks", "roster_points_milli", "survivor"])
    rank: Optional[int] = None
    user_id: Optional[str] = None
    entry_index: Optional[int] = None
    user_entry_count: Optional[int] = None
    handle: Optional[str] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    avatar_seed: Optional[int] = None
    resolved_win_count: Optional[int] = None
    open_leg_count: Optional[int] = None
    picks: Optional[List[ContestUserPickResponse]] = None
    tiebreaker_guess: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    perfect_slate_won: Optional[bool] = None
    perfect_slate_payout_micros: Optional[int] = None
    refunded: Optional[bool] = None
    roster_picks: Optional[List[ContestRosterPickResponse]] = None
    roster_points_milli: Optional[int] = None
    survivor: Optional[SurvivorEntryStateResponse] = None

@dataclass
class PublicContestLeaderboardResponse(LongshotModel):
    total_entries: Optional[int] = None
    entries: Optional[List[ContestLeaderboardRowResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class ContestCallerLeaderboardResponse(LongshotModel):
    rows: Optional[List[ContestLeaderboardRowResponse]] = None

@dataclass
class CallerContestLeaderboardResponse(LongshotModel):
    __serde_flatten__ = set(["leaderboard"])
    leaderboard: Optional[PublicContestLeaderboardResponse] = None
    caller: Optional[ContestCallerLeaderboardResponse] = None

@dataclass
class ContestTopParticipantRowResponse(LongshotModel):
    user_id: Optional[str] = None
    handle: Optional[str] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    avatar_seed: Optional[int] = None
    won_count: Optional[int] = None
    total_winnings_micros: Optional[int] = None

@dataclass
class ContestTopParticipantsResponse(LongshotModel):
    window_ms: Optional[int] = None
    participants: Optional[List[ContestTopParticipantRowResponse]] = None

@dataclass
class ContestPopularEntryMarketResponse(LongshotModel):
    market_id: Optional[int] = None
    yes_count: Optional[int] = None
    no_count: Optional[int] = None

@dataclass
class ContestPopularEntryResponse(LongshotModel):
    total_entries: Optional[int] = None
    markets: Optional[List[ContestPopularEntryMarketResponse]] = None

@dataclass
class UserReferralCodeResponse(LongshotModel):
    referral_code: Optional[str] = None
    max_referrals: Optional[int] = None
    referrals_used: Optional[int] = None
    referrals_remaining: Optional[int] = None
    ever_had_referral_capacity: Optional[bool] = None
    can_edit: Optional[bool] = None

@dataclass
class UserSetReferrerResponse(LongshotModel):
    pass

@dataclass
class UserReferralRatesResponse(LongshotModel):
    primary_kickback_bps: Optional[int] = None
    secondary_kickback_bps: Optional[int] = None

@dataclass
class UserReferralStatsResponse(LongshotModel):
    total_referred: Optional[int] = None
    total_rewards_micros: Optional[int] = None
    has_settled_referral_trade: Optional[bool] = None

class ReferralLevelLabel(RustStringEnum):
    First = "first"
    Second = "second"

@dataclass
class UserReferralEntryResponse(LongshotModel):
    __serde_skip_none__ = set(["x_handle","x_avatar_url"])
    user_id: Optional[UUID] = None
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    referred_at_ms: Optional[int] = None
    level: Optional[ReferralLevelLabel] = None
    total_volume_micros: Optional[int] = None
    total_fees_paid_micros: Optional[int] = None
    my_kickback_micros: Optional[int] = None

@dataclass
class UserReferralsListResponse(LongshotModel):
    entries: Optional[List[UserReferralEntryResponse]] = None
    total_count: Optional[int] = None

@dataclass
class ErrorResponse(LongshotModel):
    __serde_skip_none__ = set(["details"])
    error: Optional[str] = None
    code: Optional[str] = None
    details: Optional[str] = None

class ShareImageRef(RustTaggedUnion):
    __serde_tag__ = "source"
    __serde_variants__ = {
            "PoolImage": "pool_image"
    }

    @classmethod
    def pool_image(cls, payload: Any = None, **fields: Any) -> ShareImageRef:
        return cls("PoolImage", payload, **fields)

@dataclass
class ShareCardFooter(LongshotModel):
    handle: Optional[str] = None

@dataclass
class ShareStat(LongshotModel):
    value: Optional[str] = None
    label: Optional[str] = None

@dataclass
class StreakShareCard(LongshotModel):
    __serde_skip_none__ = set(["market_image","selection_date","prize_label"])
    streak_count: Optional[int] = None
    max_streak: Optional[int] = None
    market_title: Optional[str] = None
    market_image: Optional[ShareImageRef] = None
    selection: Optional[str] = None
    selection_date: Optional[str] = None
    prize_label: Optional[str] = None
    footer: Optional[ShareCardFooter] = None

class PriceState(RustStringEnum):
    Live = "live"
    Won = "won"
    Lost = "lost"

@dataclass
class PriceShareCard(LongshotModel):
    __serde_skip_none__ = set(["subtitle"])
    __serde_skip_empty__ = set(["summary"])
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    state: Optional[PriceState] = None
    question: Optional[str] = None
    subtitle: Optional[str] = None
    prediction: Optional[float] = None
    current_price: Optional[float] = None
    chart_prices: Optional[List[float]] = None
    summary: Optional[List[ShareStat]] = None
    footer: Optional[ShareCardFooter] = None

class QuestionsState(RustStringEnum):
    Pre = "pre"
    Live = "live"
    Won = "won"
    Lost = "lost"

class ContestType(RustStringEnum):
    Free = "free"
    Paid = "paid"

class LegGrade(RustStringEnum):
    Pending = "pending"
    Correct = "correct"
    Incorrect = "incorrect"

@dataclass
class QuestionLeg(LongshotModel):
    name: Optional[str] = None
    answer: Optional[str] = None
    grade: Optional[LegGrade] = None

@dataclass
class QuestionsShareCard(LongshotModel):
    __serde_skip_none__ = set(["topic_image"])
    __serde_skip_empty__ = set(["summary"])
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    state: Optional[QuestionsState] = None
    contest_type: Optional[ContestType] = None
    question: Optional[str] = None
    topic_image: Optional[ShareImageRef] = None
    legs: Optional[List[QuestionLeg]] = None
    summary: Optional[List[ShareStat]] = None
    footer: Optional[ShareCardFooter] = None

class MarketsState(RustStringEnum):
    Pre = "pre"
    Live = "live"
    Won = "won"
    Lost = "lost"

class MarketWindowOutcome(RustStringEnum):
    Pending = "pending"
    Live = "live"
    Won = "won"
    Lost = "lost"
    Voided = "voided"

@dataclass
class MarketWindowPick(LongshotModel):
    __serde_skip_none__ = set(["won", "pct_bps"])
    asset: Optional[str] = None
    direction: Optional[str] = None
    won: Optional[bool] = None
    pct_bps: Optional[int] = None

@dataclass
class MarketWindow(LongshotModel):
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    time_label: Optional[str] = None
    outcome: Optional[MarketWindowOutcome] = None
    picks: Optional[List[MarketWindowPick]] = None

@dataclass
class MarketChartSeries(LongshotModel):
    asset: Optional[str] = None
    prices: Optional[List[float]] = None

@dataclass
class MarketsShareCard(LongshotModel):
    __serde_skip_none__ = set(["tz_offset_minutes", "price_from", "price_to"])
    __serde_skip_empty__ = set(["chart"])
    position_id: Optional[str] = None
    tz_offset_minutes: Optional[int] = None
    state: Optional[MarketsState] = None
    multi_asset: Optional[bool] = None
    assets: Optional[List[str]] = None
    windows: Optional[List[MarketWindow]] = None
    date_label: Optional[str] = None
    wager_label: Optional[str] = None
    multiplier_label: Optional[str] = None
    payout_label: Optional[str] = None
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    chart: Optional[List[MarketChartSeries]] = None
    footer: Optional[ShareCardFooter] = None

class RosterShareState(RustStringEnum):
    Pre = "pre"
    Live = "live"
    Won = "won"
    Lost = "lost"
    Perfect = "perfect"

class RosterShareKind(RustStringEnum):
    X = "x"
    Nfl = "nfl"

@dataclass
class RosterSharePick(LongshotModel):
    __serde_skip_none__ = set(["points", "unit", "tip", "hit"])
    name: Optional[str] = None
    bg: Optional[str] = None
    fg: Optional[str] = None
    points: Optional[str] = None
    unit: Optional[str] = None
    tip: Optional[str] = None
    hit: Optional[bool] = None

@dataclass
class RosterShareCard(LongshotModel):
    __serde_skip_none__ = set(["bonus_label"])
    __serde_skip_empty__ = set(["summary"])
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    state: Optional[RosterShareState] = None
    contest_type: Optional[ContestType] = None
    kind: Optional[RosterShareKind] = None
    prompt: Optional[str] = None
    picks: Optional[List[RosterSharePick]] = None
    summary: Optional[List[ShareStat]] = None
    bonus_label: Optional[str] = None
    footer: Optional[ShareCardFooter] = None

class SurvivorShareState(RustStringEnum):
    Pre = "pre"
    Live = "live"
    Won = "won"
    Lost = "lost"
    Voided = "voided"

class SurvivorSharePresentation(RustStringEnum):
    Matchup = "matchup"
    Daily = "daily"

@dataclass
class SurvivorShareRound(LongshotModel):
    result: Optional[SurvivorEntryRoundResultResponse] = None
    pick_count: Optional[int] = None

@dataclass
class SurvivorShareCard(LongshotModel):
    __serde_skip_empty__ = set(["summary"])
    contest_id: Optional[str] = None
    entry_index: Optional[int] = None
    state: Optional[SurvivorShareState] = None
    contest_type: Optional[ContestType] = None
    presentation: Optional[SurvivorSharePresentation] = None
    title: Optional[str] = None
    rounds: Optional[List[SurvivorShareRound]] = None
    summary: Optional[List[ShareStat]] = None
    footer: Optional[ShareCardFooter] = None

class EventPositionShareState(RustStringEnum):
    Active = "active"
    Live = "live"
    Won = "won"
    Lost = "lost"
    Voided = "voided"

class EventPositionSharePickGrade(RustStringEnum):
    Pending = "pending"
    Correct = "correct"
    Incorrect = "incorrect"
    Voided = "voided"

@dataclass
class EventPositionSharePick(LongshotModel):
    __serde_skip_none__ = set(["odds_label", "result", "team_abbr"])
    market_id: Optional[int] = None
    label: Optional[str] = None
    side: Optional[str] = None
    grade: Optional[EventPositionSharePickGrade] = None
    odds_label: Optional[str] = None
    result: Optional[str] = None
    team_abbr: Optional[str] = None

@dataclass
class NflShareMeta(LongshotModel):
    away_abbr: Optional[str] = None
    home_abbr: Optional[str] = None
    combo: Optional[bool] = None

@dataclass
class EventPositionShareCard(LongshotModel):
    __serde_skip_none__ = set(["tz_offset_minutes", "market_kind", "meta_label", "market_image", "payout_label", "nfl"])
    position_id: Optional[str] = None
    tz_offset_minutes: Optional[int] = None
    market_kind: Optional[str] = None
    state: Optional[EventPositionShareState] = None
    title: Optional[str] = None
    meta_label: Optional[str] = None
    market_image: Optional[ShareImageRef] = None
    picks: Optional[List[EventPositionSharePick]] = None
    wager_label: Optional[str] = None
    multiplier_label: Optional[str] = None
    payout_label: Optional[str] = None
    nfl: Optional[NflShareMeta] = None
    footer: Optional[ShareCardFooter] = None

class ShareCardSnapshot(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "Streak": "streak",
            "Price": "price",
            "Questions": "questions",
            "Markets": "markets",
            "Roster": "roster",
            "Survivor": "survivor",
            "EventPosition": "event_position"
    }

    @classmethod
    def streak(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("Streak", payload, **fields)

    @classmethod
    def price(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("Price", payload, **fields)

    @classmethod
    def questions(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("Questions", payload, **fields)

    @classmethod
    def markets(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("Markets", payload, **fields)

    @classmethod
    def roster(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("Roster", payload, **fields)

    @classmethod
    def survivor(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("Survivor", payload, **fields)

    @classmethod
    def event_position(cls, payload: Any = None, **fields: Any) -> ShareCardSnapshot:
        return cls("EventPosition", payload, **fields)

@dataclass
class CreateShareCardResponse(LongshotModel):
    id: Optional[str] = None
    share_url: Optional[str] = None

class StreakRoundStatusResponse(RustStringEnum):
    Open = "open"
    Resolving = "resolving"
    Resolved = "resolved"

@dataclass
class StreakTierResponse(LongshotModel):
    streak: Optional[int] = None
    payout_micros: Optional[int] = None
    has_app_token: Optional[bool] = None

@dataclass
class StreakMarketResponse(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    market_id: Optional[int] = None
    selection_group: Optional[str] = None
    market_type: Optional[MarketType] = None
    trading_channels: Optional[List[TradingChannel]] = None
    name: Optional[str] = None
    status: Optional[MarketStatus] = None
    outcome: Optional[Outcome] = None
    source: Optional[EventMarketSource] = None
    resolution_time_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None
    image_url: Optional[str] = None
    juiced: Optional[bool] = False

@dataclass
class StreakUserPickResponse(LongshotModel):
    market_id: Optional[int] = None
    direction: Optional[ContestDirectionResponse] = None
    outcome: Optional[ContestLegOutcome] = None
    picked_at_ms: Optional[int] = None

@dataclass
class StreakCurrentRoundResponse(LongshotModel):
    game_index: Optional[int] = None
    status: Optional[StreakRoundStatusResponse] = None
    betting_opens_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    markets: Optional[List[StreakMarketResponse]] = None
    user_pick: Optional[StreakUserPickResponse] = None

@dataclass
class StreakUserStateResponse(LongshotModel):
    win_streak: Optional[int] = None
    games_won: Optional[int] = None
    games_lost: Optional[int] = None
    bets_won: Optional[int] = None
    bets_lost: Optional[int] = None

@dataclass
class StreakResponse(LongshotModel):
    contest_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tiers: Optional[List[StreakTierResponse]] = None
    max_streak: Optional[int] = None
    current_round: Optional[StreakCurrentRoundResponse] = None
    scheduled_round: Optional[StreakCurrentRoundResponse] = None
    user: Optional[StreakUserStateResponse] = None

class StreakPickRound(RustStringEnum):
    Current = "current"
    Scheduled = "scheduled"

@dataclass
class PlaceStreakPickRequest(LongshotModel):
    market_id: Optional[int] = None
    direction: Optional[str] = None
    use_app_tokens: Optional[bool] = None
    round: Optional[StreakPickRound] = None

@dataclass
class PlaceStreakPickResponse(LongshotModel):
    entry_index: Optional[int] = None
    picked_at_ms: Optional[int] = None

@dataclass
class UserTransactionsRawQuery(LongshotModel):
    category: Optional[str] = None
    from_ms: Optional[str] = None
    to_ms: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class ConfirmPositionQuery(LongshotModel):
    position_id: Optional[str] = None
    accept: Optional[bool] = None

@dataclass
class ReferralsListRawQuery(LongshotModel):
    page: Optional[int] = None
    limit: Optional[int] = None

def _direction_to_wire(direction: Direction) -> int:
    return 0 if direction is Direction.Up else 1

def _round_half_away_from_zero(value: float) -> int:
    return floor(value + 0.5) if value >= 0 else ceil(value - 0.5)

def _parse_min_odds_bps(min_odds_decimal: float) -> int:
    if not isfinite(min_odds_decimal):
        raise ValueError("invalid min odds")
    min_odds_bps = _round_half_away_from_zero(min_odds_decimal * 10_000)
    if min_odds_bps <= Odds.EVEN.value or min_odds_bps > Odds.MAX.value:
        raise ValueError("invalid min odds")
    return int(min_odds_bps)

def _order_leg_json_parse(self: OrderLegJson) -> ParsedOrderLeg:
    market_id = _canonical_u64(self.market_id, "market_id")
    if market_id == 0:
        raise ValueError("invalid market id")
    raw_direction = str(self.direction)
    if raw_direction.lower() == "up":
        direction = Direction.Up
    elif raw_direction.lower() == "down":
        direction = Direction.Down
    else:
        raise ValueError("invalid direction")
    return ParsedOrderLeg(market_id=MarketId(market_id), direction=direction)

def _order_leg_json_from_order_leg(cls, leg: OrderLeg) -> OrderLegJson:
    direction = Direction.from_u8(leg.direction)
    if direction is None:
        raise ValueError(f"invalid direction: {leg.direction}")
    raw_market_id = (
        leg.market_id.as_u64() if isinstance(leg.market_id, MarketId) else leg.market_id
    )
    market_id = _canonical_u64(raw_market_id, "market_id")
    return cls(market_id=market_id, direction=direction.name.lower())

def _signed_order_json_from_signed_order(cls, order: SignedOrder) -> SignedOrderJson:
    order.validate()
    user = order.user if isinstance(order.user, Address) else Address(order.user)
    return cls(
        user=user.to_checksum(),
        wager_micros=order.wager_micros,
        min_odds=order.min_odds_bps / 10_000,
        legs=[OrderLegJson.from_order_leg(leg) for leg in order.legs],
        nonce=order.nonce,
        expires_at_ms=order.expires_at_ms,
        order_type=int(order.order_type),
        shield_on=order.shield_on,
        signature=b64encode(order.signature).decode("ascii"),
    )

def _parse_order_legs(raw_legs: List[OrderLegJson]) -> List[OrderLeg]:
    legs = [leg.parse() if hasattr(leg, "parse") else OrderLegJson.from_dict(leg).parse() for leg in raw_legs]
    if not legs:
        raise ValueError("order must include at least one leg")
    if len(legs) > SignedOrder.MAX_LEGS:
        raise ValueError("too many legs")
    return [OrderLeg(market_id=leg.market_id, direction=_direction_to_wire(leg.direction)) for leg in legs]

def _parse_required_bool(value: object, field: str) -> bool:
    # Identity checks preserve Rust's exact bool contract; Python truthiness would turn "false" into true.
    if value is True:
        return True
    if value is False:
        return False
    raise ValueError(f"{field} must be bool")

def _signed_order_json_to_signed_order(self: SignedOrderJson) -> SignedOrder:
    signature = b64decode(self.signature, validate=True)
    if (
        len(signature) != 65
        or b64encode(signature).decode("ascii") != self.signature
    ):
        raise ValueError("invalid signature format")
    return SignedOrder(
        user=Address.from_hex(self.user),
        wager_micros=_canonical_u64(self.wager_micros, "wager_micros"),
        min_odds_bps=_parse_min_odds_bps(float(self.min_odds)),
        legs=_parse_order_legs(self.legs),
        nonce=_canonical_u64(self.nonce, "nonce"),
        expires_at_ms=_canonical_u64(self.expires_at_ms, "expires_at_ms"),
        order_type=_parse_order_type(self.order_type),
        shield_on=_parse_required_bool(self.shield_on, "shield_on"),
        signature=signature,
    )

def _create_rfq_request_from_signed_order(
    cls, order: SignedOrder, use_app_tokens: bool
) -> CreateRfqRequest:
    return cls(
        order=SignedOrderJson.from_signed_order(order),
        use_app_tokens=use_app_tokens,
    )

def _unsigned_rfq_parse_idempotency_key(self: UnsignedRfqOrderRequest) -> UUID:
    return UUID(str(self.idempotency_key).strip())

def _unsigned_rfq_into_signed_order_for_session(self: UnsignedRfqOrderRequest, user: Address, nonce: int, expires_at_ms: int) -> SignedOrder:
    return SignedOrder(
        user=user,
        wager_micros=_canonical_u64(self.wager_micros, "wager_micros"),
        min_odds_bps=_parse_min_odds_bps(float(self.min_odds)),
        legs=_parse_order_legs(self.legs),
        nonce=_canonical_u64(nonce, "nonce"),
        expires_at_ms=_canonical_u64(expires_at_ms, "expires_at_ms"),
        order_type=_parse_order_type(self.order_type),
        shield_on=_parse_required_bool(self.shield_on, "shield_on"),
        signature=bytes(65),
    )

def _canonical_u64(value: object, field: str) -> int:
    # Signed payloads must preserve exact integer inputs; int(value) would silently
    # turn booleans, floats, and numeric strings into a different order.
    if type(value) is not int or not 0 <= value <= (1 << 64) - 1:
        raise ValueError(f"{field} must fit in u64")
    return value

def _parse_order_type(value: object) -> OrderType:
    if value is None:
        return OrderType.FOK
    if type(value) is not int:
        raise ValueError("order_type must be int")
    return OrderType(value)

def build_wallet_authentication_message(
    domain: str,
    auth_address: Address | str,
    signed_at_ms: int,
) -> str:
    auth = Address.from_evm(auth_address)
    return "\n".join(
        [
            "Longshot Wallet Authentication",
            "",
            "Version: 1",
            f"Domain: {domain}",
            f"Auth Address: {auth.to_checksum()}",
            f"Timestamp: {_canonical_u64(signed_at_ms, 'signed_at_ms')}",
        ]
    )

def build_wallet_withdrawal_authorization_message(
    domain: str,
    chain_id: int,
    auth_address: Address | str,
    destination_address: Address | str,
    amount_micros: int,
    idempotency_key: UUID | str,
    signed_at_ms: int,
) -> str:
    auth = Address.from_evm(auth_address)
    destination = Address.from_evm(destination_address)
    canonical_idempotency_key = UUID(str(idempotency_key).strip())
    return "\n".join(
        [
            "Longshot Withdrawal Authorization",
            "",
            "Version: 1",
            f"Domain: {domain}",
            f"Chain ID: {_canonical_u64(chain_id, 'chain_id')}",
            f"Auth Address: {auth.to_checksum()}",
            f"Destination Address: {destination.to_checksum()}",
            f"Amount Micros: {_canonical_u64(amount_micros, 'amount_micros')}",
            f"Idempotency Key: {canonical_idempotency_key}",
            f"Timestamp: {_canonical_u64(signed_at_ms, 'signed_at_ms')}",
        ]
    )

def encode_wallet_signature(signature: bytes) -> str:
    if len(signature) != 65:
        raise ValueError("wallet signature must be 65 bytes")
    return b64encode(signature).decode("ascii")

def _error_response_new(cls, error: Any, code: Any) -> ErrorResponse:
    return cls(error=str(error), code=str(code), details=None)

def _error_response_with_details(self: ErrorResponse, details: Any) -> ErrorResponse:
    return type(self)(error=self.error, code=self.code, details=str(details))

def _payload_get(payload: Any, field: str, default: Any = None) -> Any:
    if isinstance(payload, dict):
        return payload.get(field, default)
    return getattr(payload, field, default)

def _check_share_text(value: Any, field: str) -> None:
    if not isinstance(value, str) or len(value) > MAX_TEXT_LEN:
        raise ValueError(field)

def _check_share_footer(footer: Any) -> None:
    _check_share_text(_payload_get(footer, "handle"), "footer.handle")

def _check_share_hex_color(value: Any, field: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 7
        or not value.startswith("#")
        or any(char not in "0123456789abcdefABCDEF" for char in value[1:])
    ):
        raise ValueError(field)

def _check_share_contest_id(value: Any) -> None:
    try:
        UUID(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("contest_id") from exc

def _check_share_summary(summary: Any) -> None:
    summary = summary or []
    if len(summary) > MAX_SUMMARY_STATS:
        raise ValueError("summary")
    for stat in summary:
        _check_share_text(_payload_get(stat, "value"), "summary.value")
        _check_share_text(_payload_get(stat, "label"), "summary.label")

def _share_card_snapshot_type_str(self: ShareCardSnapshot) -> str:
    return self.tag_value

def _share_card_snapshot_validate(self: ShareCardSnapshot) -> None:
    payload = self.payload
    if self.variant == "Streak":
        streak_count = _payload_get(payload, "streak_count")
        max_streak = _payload_get(payload, "max_streak")
        if max_streak == 0 or streak_count is None or max_streak is None or streak_count > max_streak:
            raise ValueError("streak_count")
        _check_share_text(_payload_get(payload, "market_title"), "market_title")
        _check_share_text(_payload_get(payload, "selection"), "selection")
        selection_date = _payload_get(payload, "selection_date")
        if selection_date is not None:
            _check_share_text(selection_date, "selection_date")
        prize_label = _payload_get(payload, "prize_label")
        if prize_label is not None:
            _check_share_text(prize_label, "prize_label")
        _check_share_footer(_payload_get(payload, "footer"))
        return

    if self.variant == "Price":
        _check_share_contest_id(_payload_get(payload, "contest_id"))
        chart_prices = _payload_get(payload, "chart_prices") or []
        if len(chart_prices) > MAX_CHART_POINTS:
            raise ValueError("chart_prices")
        prediction = _payload_get(payload, "prediction")
        current_price = _payload_get(payload, "current_price")
        if not isfinite(float(prediction)) or not isfinite(float(current_price)):
            raise ValueError("price")
        if any(not isfinite(float(price)) for price in chart_prices):
            raise ValueError("chart_prices")
        _check_share_text(_payload_get(payload, "question"), "question")
        subtitle = _payload_get(payload, "subtitle")
        if subtitle is not None:
            _check_share_text(subtitle, "subtitle")
        _check_share_summary(_payload_get(payload, "summary"))
        _check_share_footer(_payload_get(payload, "footer"))
        return

    if self.variant == "Markets":
        _check_share_contest_id(_payload_get(payload, "position_id"))
        tz_offset_minutes = _payload_get(payload, "tz_offset_minutes")
        if tz_offset_minutes is not None and abs(tz_offset_minutes) > MAX_TZ_OFFSET_MINUTES:
            raise ValueError("tz_offset_minutes")
        assets = _payload_get(payload, "assets") or []
        if len(assets) > MAX_MARKET_WINDOW_PICKS:
            raise ValueError("assets")
        for asset in assets:
            _check_share_text(asset, "assets")
        windows = _payload_get(payload, "windows") or []
        if len(windows) > MAX_MARKET_WINDOWS:
            raise ValueError("windows")
        for window in windows:
            _check_share_text(_payload_get(window, "time_label"), "windows.time_label")
            picks = _payload_get(window, "picks") or []
            if len(picks) > MAX_MARKET_WINDOW_PICKS:
                raise ValueError("windows.picks")
            for pick in picks:
                _check_share_text(_payload_get(pick, "asset"), "windows.picks.asset")
                _check_share_text(_payload_get(pick, "direction"), "windows.picks.direction")
        _check_share_text(_payload_get(payload, "date_label"), "date_label")
        _check_share_text(_payload_get(payload, "wager_label"), "wager_label")
        _check_share_text(_payload_get(payload, "multiplier_label"), "multiplier_label")
        _check_share_text(_payload_get(payload, "payout_label"), "payout_label")
        for value in (_payload_get(payload, "price_from"), _payload_get(payload, "price_to")):
            if value is not None and not isfinite(float(value)):
                raise ValueError("price")
        chart = _payload_get(payload, "chart") or []
        if len(chart) > MAX_MARKET_WINDOW_PICKS:
            raise ValueError("chart")
        for series in chart:
            _check_share_text(_payload_get(series, "asset"), "chart.asset")
            prices = _payload_get(series, "prices") or []
            if len(prices) > MAX_CHART_POINTS:
                raise ValueError("chart.prices")
            if any(not isfinite(float(price)) for price in prices):
                raise ValueError("chart.prices")
        _check_share_footer(_payload_get(payload, "footer"))
        return

    if self.variant == "Roster":
        _check_share_contest_id(_payload_get(payload, "contest_id"))
        _check_share_text(_payload_get(payload, "prompt"), "prompt")
        picks = _payload_get(payload, "picks") or []
        if not picks or len(picks) > MAX_ROSTER_SHARE_PICKS:
            raise ValueError("picks")
        for pick in picks:
            _check_share_text(_payload_get(pick, "name"), "picks.name")
            _check_share_hex_color(_payload_get(pick, "bg"), "picks.bg")
            _check_share_hex_color(_payload_get(pick, "fg"), "picks.fg")
            points = _payload_get(pick, "points")
            if points is not None:
                _check_share_text(points, "picks.points")
            unit = _payload_get(pick, "unit")
            if unit is not None:
                _check_share_text(unit, "picks.unit")
            tip = _payload_get(pick, "tip")
            if tip is not None:
                _check_share_text(tip, "picks.tip")
        _check_share_summary(_payload_get(payload, "summary"))
        bonus_label = _payload_get(payload, "bonus_label")
        if bonus_label is not None:
            _check_share_text(bonus_label, "bonus_label")
        _check_share_footer(_payload_get(payload, "footer"))
        return

    if self.variant == "Survivor":
        _check_share_contest_id(_payload_get(payload, "contest_id"))
        _check_share_text(_payload_get(payload, "title") or "", "title")
        rounds = _payload_get(payload, "rounds") or []
        if len(rounds) > MAX_SURVIVOR_SHARE_ROUNDS:
            raise ValueError("rounds")
        if sum(_payload_get(round_, "pick_count") or 0 for round_ in rounds) > MAX_SURVIVOR_SHARE_PICKS:
            raise ValueError("rounds.pick_count")
        _check_share_summary(_payload_get(payload, "summary"))
        _check_share_footer(_payload_get(payload, "footer"))
        return

    if self.variant == "EventPosition":
        try:
            _check_share_contest_id(_payload_get(payload, "position_id"))
        except ValueError as exc:
            raise ValueError("position_id") from exc
        _check_share_text(_payload_get(payload, "title") or "", "title")
        meta_label = _payload_get(payload, "meta_label")
        if meta_label is not None:
            _check_share_text(meta_label, "meta_label")
        picks = _payload_get(payload, "picks") or []
        if len(picks) > MAX_EVENT_POSITION_SHARE_PICKS:
            raise ValueError("picks")
        for pick in picks:
            _check_share_text(_payload_get(pick, "label"), "picks.label")
            if _payload_get(pick, "side") not in ("yes", "no"):
                raise ValueError("picks.side")
            odds_label = _payload_get(pick, "odds_label")
            if odds_label is not None:
                _check_share_text(odds_label, "picks.odds_label")
            result = _payload_get(pick, "result")
            if result is not None:
                _check_share_text(result, "picks.result")
        _check_share_text(_payload_get(payload, "wager_label") or "", "wager_label")
        _check_share_text(
            _payload_get(payload, "multiplier_label") or "", "multiplier_label"
        )
        payout_label = _payload_get(payload, "payout_label")
        if payout_label is not None:
            _check_share_text(payout_label, "payout_label")
        _check_share_footer(_payload_get(payload, "footer"))
        return

    if self.variant == "Questions":
        _check_share_contest_id(_payload_get(payload, "contest_id"))
        legs = _payload_get(payload, "legs") or []
        if not legs or len(legs) > MAX_QUESTION_LEGS:
            raise ValueError("legs")
        _check_share_text(_payload_get(payload, "question"), "question")
        for leg in legs:
            _check_share_text(_payload_get(leg, "name"), "legs.name")
            _check_share_text(_payload_get(leg, "answer"), "legs.answer")
        _check_share_summary(_payload_get(payload, "summary"))
        _check_share_footer(_payload_get(payload, "footer"))
        return

    raise ValueError("type")

@dataclass
class CreateEmbeddedWalletEnsureRequest(LongshotModel):
    privy_token: Optional[str] = None

class ReferralPromptRequest(RustStringEnum):
    PostWin = "post_win"
    FirstPick = "first_pick"

@dataclass
class ClaimReferralPromptRequest(LongshotModel):
    prompt: Optional[ReferralPromptRequest] = None

@dataclass
class AcknowledgeReferralPromptRequest(LongshotModel):
    prompt: Optional[ReferralPromptRequest] = None
    claim_token: Optional[UUID] = None
    shown: Optional[bool] = None

@dataclass
class ChatPostGifRequest(LongshotModel):
    gif_id: Optional[str] = None
    chat_id: Optional[str] = None
    parent: Optional[str] = None

@dataclass
class RfqEstimateRequest(LongshotModel):
    wager_micros: Optional[int] = None
    legs: Optional[List[OrderLegJson]] = None
    shield_on: Optional[bool] = False

@dataclass
class RfqEstimateBatchItemRequest(LongshotModel):
    key: Optional[str] = None
    leg: Optional[OrderLegJson] = None

@dataclass
class RfqEstimateBatchRequest(LongshotModel):
    wager_micros: Optional[int] = None
    estimates: Optional[List[RfqEstimateBatchItemRequest]] = None
    shield_on: Optional[bool] = False

class EmbeddedWalletEnsureStatus(RustStringEnum):
    Ready = "ready"
    Pending = "pending"
    NotRequired = "not_required"

@dataclass
class EmbeddedWalletEnsureResponse(LongshotModel):
    __serde_skip_none__ = set(["wallet_address"])
    status: Optional[EmbeddedWalletEnsureStatus] = None
    wallet_address: Optional[str] = None

@dataclass
class RfqEstimateResponse(LongshotModel):
    __serde_skip_none__ = set(["odds", "fillable_micros", "reason"])
    request_id: Optional[UUID] = None
    quotable: Optional[bool] = None
    odds: Optional[float] = None
    fillable_micros: Optional[int] = None
    quotes_received: Optional[int] = None
    quoted_at_ms: Optional[int] = None
    reason: Optional[str] = None

class RfqEstimateBatchItemStatus(RustStringEnum):
    Quoted = "quoted"
    Unavailable = "unavailable"

@dataclass
class RfqEstimateBatchItemResponse(LongshotModel):
    __serde_skip_none__ = set(["odds", "fillable_micros", "reason"])
    key: Optional[str] = None
    market_id: Optional[int] = None
    direction: Optional[str] = None
    status: Optional[RfqEstimateBatchItemStatus] = None
    request_id: Optional[UUID] = None
    quotable: Optional[bool] = None
    odds: Optional[float] = None
    fillable_micros: Optional[int] = None
    quotes_received: Optional[int] = None
    quoted_at_ms: Optional[int] = None
    reason: Optional[str] = None

@dataclass
class RfqEstimateBatchResponse(LongshotModel):
    wager_micros: Optional[int] = None
    estimates: Optional[List[RfqEstimateBatchItemResponse]] = None

@dataclass
class MmRfqStatusResponse(LongshotModel):
    request_id: Optional[str] = None
    status: Optional[RfqStatus] = None

@dataclass
class UserAvailableBalanceResponse(LongshotModel):
    available_micros: Optional[int] = None
    pending_custodial_deposit_micros: Optional[int] = None
    credited_custodial_deposit_micros: Optional[int] = None
    deposit_withdrawal_min_micros: Optional[int] = None

class WithdrawalDeliveryStatus(RustStringEnum):
    Queued = "queued"

@dataclass
class QueuedWithdrawalResponse(LongshotModel):
    __serde_skip_none__ = set(["destination_address"])
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    destination_address: Optional[str] = None
    delivery_status: Optional[WithdrawalDeliveryStatus] = None

class AcceptedWithdrawOperationResponse(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {
        "Queued": "Queued",
        "Recovery": "Recovery",
    }

    @classmethod
    def queued(cls, payload: Any = None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        return cls("Queued", payload, **fields)

    @classmethod
    def recovery(cls, payload: Any = None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        return cls("Recovery", payload, **fields)

class PublicReferralStatusResponse(RustStringEnum):
    Valid = "valid"
    Redeemed = "redeemed"
    Expired = "expired"

@dataclass
class PublicReferralInviterResponse(LongshotModel):
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    avatar_url: Optional[str] = None

@dataclass
class PublicReferralDepositMatchOffer(LongshotModel):
    match_limit_micros: Optional[int] = None
    duration_ms: Optional[int] = None

@dataclass
class PublicReferralCodeResponse(LongshotModel):
    __serde_skip_none__ = set(["inviter", "deposit_match"])
    status: Optional[PublicReferralStatusResponse] = None
    inviter: Optional[PublicReferralInviterResponse] = None
    deposit_match: Optional[PublicReferralDepositMatchOffer] = None

@dataclass
class ClaimReferralPromptResponse(LongshotModel):
    __serde_skip_none__ = set(["amount_micros", "claim_token", "retry_after_ms"])
    show: Optional[bool] = None
    amount_micros: Optional[int] = None
    claim_token: Optional[UUID] = None
    retry_after_ms: Optional[int] = None

@dataclass
class ObserverAccessResponse(LongshotModel):
    enabled: Optional[bool] = None

@dataclass
class MarketCategoryVisibilityResponse(LongshotModel):
    crypto: Optional[bool] = None
    mentions: Optional[bool] = None
    nfl: Optional[bool] = None
    culture: Optional[bool] = None

@dataclass
class UserFeaturesResponse(LongshotModel):
    markets_access: Optional[bool] = None

@dataclass
class ChatMarketRoomResponse(LongshotModel):
    chat_id: Optional[str] = None

@dataclass
class ChatMentionCandidateResponse(LongshotModel):
    user_id: Optional[str] = None
    handle: Optional[str] = None

@dataclass
class ChatMentionCandidatesResponse(LongshotModel):
    candidates: Optional[List[ChatMentionCandidateResponse]] = None

@dataclass
class FeedLegResponse(LongshotModel):
    __serde_skip_none__ = set(["window_start_ms", "duration_secs"])
    asset: Optional[str] = None
    direction: Optional[str] = None
    window_start_ms: Optional[int] = None
    duration_secs: Optional[int] = None

@dataclass
class FeedEventWithLegsResponse(LongshotModel):
    __serde_flatten__ = set(["event"])
    __serde_skip_empty__ = set(["legs"])
    event: Optional[FeedEventResponse] = None
    primary_asset: Optional[str] = None
    has_binary_event_leg: Optional[bool] = None
    legs: Optional[List[FeedLegResponse]] = None

@dataclass
class FeedWithLegsResponse(LongshotModel):
    __serde_skip_none__ = set(["next_cursor"])
    events: Optional[List[FeedEventWithLegsResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class PnlHistoryScopedQuery(LongshotModel):
    __serde_renames__ = {"from_": "from"}
    from_: Optional[int] = None
    to: Optional[int] = None
    scope: Optional[str] = None

@dataclass
class PortfolioSummaryRawQuery(LongshotModel):
    scope: Optional[str] = None

@dataclass
class PortfolioSummaryResponse(LongshotModel):
    scope: Optional[str] = None
    active_count: Optional[int] = None
    potential_payout_micros: Optional[int] = None
    realized_pnl_micros: Optional[int] = None
    biggest_win_micros: Optional[int] = None

@dataclass
class PositionsByMarketsQuery(LongshotModel):
    market_ids: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class PositionsByMarketsResponse(LongshotModel):
    positions: Optional[List[PositionDetailResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class ProfileUpdateQuery(LongshotModel):
    finalize_onboarding: Optional[bool] = False

@dataclass
class HandleAvailabilityQuery(LongshotModel):
    handle: Optional[str] = None
    finalize_onboarding: Optional[bool] = False

@dataclass
class PublicProfileSummaryResponse(LongshotModel):
    scope: Optional[str] = None
    active_count: Optional[int] = None
    potential_payout_micros: Optional[int] = None
    realized_pnl_micros: Optional[int] = None
    biggest_win_micros: Optional[int] = None

@dataclass
class UserReferralStatsRawQuery(LongshotModel):
    window: Optional[str] = None

@dataclass
class WebPushConfigResponse(LongshotModel):
    __serde_skip_none__ = set(["public_key"])
    enabled: Optional[bool] = None
    public_key: Optional[str] = None

@dataclass
class WebPushSubscriptionKeys(LongshotModel):
    p256dh: Optional[str] = None
    auth: Optional[str] = None

@dataclass
class UpsertWebPushSubscriptionRequest(LongshotModel):
    endpoint: Optional[str] = None
    expiration_time: Optional[int] = None
    keys: Optional[WebPushSubscriptionKeys] = None

@dataclass
class DeleteWebPushSubscriptionRequest(LongshotModel):
    endpoint: Optional[str] = None

@dataclass
class WebPushSubscriptionResponse(LongshotModel):
    subscribed: Optional[bool] = None

@dataclass
class StreakPicksRawQuery(LongshotModel):
    limit: Optional[int] = None
    cursor: Optional[str] = None
    contest_id: Optional[str] = None

@dataclass
class StreakHistoryRawQuery(LongshotModel):
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class StreakLeaderboardRawQuery(LongshotModel):
    limit: Optional[int] = None

@dataclass
class StreakPickHistoryItemResponse(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    game_index: Optional[int] = None
    market_id: Optional[int] = None
    market_title: Optional[str] = None
    market_category: Optional[str] = None
    market_outcome: Optional[Outcome] = None
    direction: Optional[ContestDirectionResponse] = None
    outcome: Optional[ContestLegOutcome] = None
    picked_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    image_url: Optional[str] = None

@dataclass
class StreakPicksResponse(LongshotModel):
    contest_id: Optional[str] = None
    title: Optional[str] = None
    picks: Optional[List[StreakPickHistoryItemResponse]] = None
    next_cursor: Optional[str] = None

class StreakPickVisibilityResponse(RustStringEnum):
    Visible = "visible"
    HiddenWhileBettingOpen = "hidden_while_betting_open"
    None_ = "none"

@dataclass
class PublicProfileStreakPicksResponse(LongshotModel):
    contest_id: Optional[str] = None
    title: Optional[str] = None
    picks: Optional[List[StreakPickHistoryItemResponse]] = None
    current_round_pick_visibility: Optional[StreakPickVisibilityResponse] = None
    next_cursor: Optional[str] = None

class StreakRunStatusResponse(RustStringEnum):
    Active = "active"
    Ended = "ended"
    Expired = "expired"
    Won = "won"

@dataclass
class StreakRunTierPayoutResponse(LongshotModel):
    streak: Optional[int] = None
    payout_micros: Optional[int] = None
    is_app_token: Optional[bool] = None
    game_index: Optional[int] = None
    won_at_ms: Optional[int] = None
    credited: Optional[bool] = None

@dataclass
class StreakRunResponse(LongshotModel):
    contest_id: Optional[str] = None
    title: Optional[str] = None
    max_streak: Optional[int] = None
    status: Optional[StreakRunStatusResponse] = None
    length: Optional[int] = None
    pick_count: Optional[int] = None
    start_game_index: Optional[int] = None
    end_game_index: Optional[int] = None
    started_at_ms: Optional[int] = None
    ended_at_ms: Optional[int] = None
    failed_pick_number: Optional[int] = None
    failed_pick: Optional[StreakPickHistoryItemResponse] = None
    cash_payout_micros: Optional[int] = None
    tier_payouts: Optional[List[StreakRunTierPayoutResponse]] = None

@dataclass
class StreakHistoryResponse(LongshotModel):
    runs: Optional[List[StreakRunResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class PublicProfileStreakHistoryResponse(LongshotModel):
    runs: Optional[List[StreakRunResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class StreakOnboardingRoundResponse(LongshotModel):
    game_index: Optional[int] = None
    target: Optional[StreakPickRound] = None
    betting_closes_at_ms: Optional[int] = None
    markets: Optional[List[StreakMarketResponse]] = None

@dataclass
class StreakOnboardingResponse(LongshotModel):
    contest_id: Optional[str] = None
    title: Optional[str] = None
    eligible: Optional[bool] = None
    round: Optional[StreakOnboardingRoundResponse] = None

@dataclass
class StreakPopularMarketResponse(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    market_id: Optional[int] = None
    market_title: Optional[str] = None
    market_category: Optional[str] = None
    betting_closes_at_ms: Optional[int] = None
    up_count: Optional[int] = None
    down_count: Optional[int] = None
    image_url: Optional[str] = None

@dataclass
class StreakPopularTodayResponse(LongshotModel):
    contest_id: Optional[str] = None
    game_index: Optional[int] = None
    total_picks: Optional[int] = None
    markets: Optional[List[StreakPopularMarketResponse]] = None

@dataclass
class StreakLeaderboardRowResponse(LongshotModel):
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    current_streak: Optional[int] = None
    picks: Optional[List[StreakPickHistoryItemResponse]] = None
    current_pick: Optional[StreakPickHistoryItemResponse] = None
    current_pick_visibility: Optional[StreakPickVisibilityResponse] = None

@dataclass
class StreakLeaderboardResponse(LongshotModel):
    contest_id: Optional[str] = None
    current_game_index: Optional[int] = None
    rows: Optional[List[StreakLeaderboardRowResponse]] = None

OrderLegJson.parse = _order_leg_json_parse
OrderLegJson.from_order_leg = classmethod(_order_leg_json_from_order_leg)
SignedOrderJson.from_signed_order = classmethod(_signed_order_json_from_signed_order)
SignedOrderJson.to_signed_order = _signed_order_json_to_signed_order
CreateRfqRequest.from_signed_order = classmethod(_create_rfq_request_from_signed_order)
UnsignedRfqOrderRequest.parse_idempotency_key = _unsigned_rfq_parse_idempotency_key
UnsignedRfqOrderRequest.into_signed_order_for_session = _unsigned_rfq_into_signed_order_for_session
ErrorResponse.new = classmethod(_error_response_new)
ErrorResponse.with_details = _error_response_with_details
ShareCardSnapshot.type_str = _share_card_snapshot_type_str
ShareCardSnapshot.validate = _share_card_snapshot_validate

_install_serde_metadata(
    globals(),
    STRUCT_INTEGER_FIELDS,
    STRUCT_REQUIRED_FIELDS,
    TAGGED_UNION_FIELDS,
    DENY_UNKNOWN_TAGGED_UNIONS,
    required_nullable_fields=STRUCT_REQUIRED_NULLABLE_FIELDS,
)

_DEFAULT_FIELDS = {
    "EventMarketSource": {"attributes": {}},
    "EventMarket": {"resolution_rules": ""},
    "ContestCallerSummaryResponse": {"entry_count": 0},
    "ContestLeaderboardRowResponse": {
        "perfect_slate_payout_micros": 0,
        "perfect_slate_won": False,
        "refunded": False,
        "user_entry_count": 1,
    },
    "ContestUserEntryResponse": {
        "perfect_slate_payout_micros": 0,
        "perfect_slate_won": False,
        "refunded": False,
    },
    "ContestLobbySummaryResponse": {"max_entries_per_player": 1},
    "PortfolioFantasyEntryResponse": {"refunded": False},
    "PublicContestDetailResponse": {"max_entries_per_player": 1},
    "PublicProfileFantasyEntryResponse": {"refunded": False},
    "SessionResponse": {"account_created": False, "onboarding_completed": False},
    "ActivePosition": {"app_token_wager_micros": 0},
    "PositionDetailResponse": {"app_token_wager_micros": 0},
    "PositionSummary": {"app_token_wager_micros": 0},
    "PositionsListResponse": {"errors": []},
    "RfqEstimateRequest": {"shield_on": False},
    "RfqEstimateBatchRequest": {"shield_on": False},
    "ProfileUpdateQuery": {"finalize_onboarding": False},
    "HandleAvailabilityQuery": {"finalize_onboarding": False},
    "StreakMarketResponse": {"juiced": False},
    "SignedOrderJson": {"order_type": 2},
    "UnsignedRfqOrderRequest": {"order_type": 2},
    "FeedEventWithLegsResponse": {"legs": []},
    "PriceShareCard": {"summary": []},
    "QuestionsShareCard": {"summary": []},
    "MarketsShareCard": {
        "state": MarketsState.Pre,
        "multi_asset": False,
        "assets": [],
        "windows": [],
        "date_label": "",
        "wager_label": "",
        "multiplier_label": "",
        "payout_label": "",
        "chart": [],
    },
    "RosterShareCard": {"summary": []},
    "SurvivorShareCard": {
        "state": SurvivorShareState.Pre,
        "contest_type": ContestType.Free,
        "presentation": SurvivorSharePresentation.Daily,
        "title": "",
        "rounds": [],
        "summary": [],
    },
    "EventPositionShareCard": {
        "state": EventPositionShareState.Active,
        "title": "",
        "picks": [],
        "wager_label": "",
        "multiplier_label": "",
    },
    "NflShareMeta": {
        "combo": False,
    },
    "BinaryEventWinNotificationPayload": {
        "market_ids": [],
    },
}

for _class_name, _field_defaults in _DEFAULT_FIELDS.items():
    globals()[_class_name].__serde_defaults__ = _field_defaults

DepositOperationResponse.__serde_untagged_payloads__ = {
    "Completed": UserDepositResponse,
    "OperationStatus": BalanceOperationStatusResponse,
}
DepositOperationResponse.__serde_untagged_required_fields__ = {
    "Completed": {"amount_micros", "operation_id", "tx_hash"},
    "OperationStatus": {"amount_micros", "operation_id", "status"},
}

WithdrawOperationResponse.__serde_untagged_payloads__ = {
    "Completed": UserWithdrawResponse,
    "OperationStatus": BalanceOperationStatusResponse,
}
WithdrawOperationResponse.__serde_untagged_required_fields__ = {
    "Completed": {"amount_micros", "operation_id", "tx_hash"},
    "OperationStatus": {"amount_micros", "operation_id", "status"},
}

AcceptedWithdrawOperationResponse.__serde_untagged_payloads__ = {
    "Queued": QueuedWithdrawalResponse,
    "Recovery": BalanceOperationStatusResponse,
}
AcceptedWithdrawOperationResponse.__serde_untagged_required_fields__ = {
    "Queued": {"amount_micros", "operation_id", "delivery_status"},
    "Recovery": {"amount_micros", "operation_id", "status"},
}

LeaderboardEntry.__serde_untagged_payloads__ = {
    "Pnl": LeaderboardPnlEntry,
    "Combo": LeaderboardComboEntry,
}
LeaderboardEntry.__serde_untagged_required_fields__ = {
    "Pnl": {"entry_count", "pnl_micros"},
    "Combo": {"combo_legs", "multiplier_bps"},
}

LeaderboardCaller.__serde_untagged_payloads__ = {
    "Pnl": LeaderboardPnlCaller,
    "Combo": LeaderboardComboCaller,
}
LeaderboardCaller.__serde_untagged_required_fields__ = {
    "Pnl": {"entry_count", "pnl_micros"},
    "Combo": {"combo_legs", "multiplier_bps"},
}

NotificationPayload.__serde_variant_payloads__ = {
    "BinaryEventStartSoon": BinaryEventStartSoonNotificationPayload,
    "FantasyStartSoon": FantasyStartSoonNotificationPayload,
    "StreakStartSoon": StreakStartSoonNotificationPayload,
    "StreakExpiring": StreakExpiringNotificationPayload,
    "BinaryEventWin": BinaryEventWinNotificationPayload,
    "PriceStrikeParlayWin": PriceStrikeParlayWinNotificationPayload,
    "RfqResult": RfqResultNotificationPayload,
    "FantasyResult": FantasyResultNotificationPayload,
    "PerfectSlate": PerfectSlateNotificationPayload,
    "StreakWin": StreakWinNotificationPayload,
    "StreakSettled": StreakSettledNotificationPayload,
    "PayoutReview": PayoutReviewNotificationPayload,
    "CreditsGranted": CreditsGrantedNotificationPayload,
    "ChatMention": ChatMentionNotificationPayload,
    "Unknown": UnknownNotificationPayload,
}

PublicMarket.__serde_untagged_payloads__ = {
    "Event": EventMarket,
    "PriceStrike": PriceStrikeMarket,
}
# Event must stay first: `source` is its unique structural selector, while the
# price variant is the strict fallback for otherwise valid market objects.
PublicMarket.__serde_untagged_required_fields__ = {
    "Event": {"source"},
    "PriceStrike": set(),
}

ShareCardSnapshot.__serde_variant_payloads__ = {
    "Streak": StreakShareCard,
    "Price": PriceShareCard,
    "Questions": QuestionsShareCard,
    "Markets": MarketsShareCard,
    "Roster": RosterShareCard,
    "Survivor": SurvivorShareCard,
    "EventPosition": EventPositionShareCard,
}

_DENY_UNKNOWN_FIELDS = {
    "CreateSessionRequest",
    "CreateEmbeddedWalletEnsureRequest",
    "ClaimReferralPromptRequest",
    "AcknowledgeReferralPromptRequest",
    "ChatPostGifRequest",
    "RfqEstimateRequest",
    "RfqEstimateBatchItemRequest",
    "RfqEstimateBatchRequest",
    "ListContestsQuery",
    "ContestDetailQuery",
    "ContestLeaderboardQuery",
    "ContestTopParticipantsQuery",
    "FeedRawQuery",
    "LeaderboardRawQuery",
    "LeaderboardMeRawQuery",
    "HighlightsRawQuery",
    "PublicMarketsRawQuery",
    "PriceStrikeMarket",
    "EventMarket",
    "PublicMarketResponse",
    "PublicMarketsResponse",
    "MarketLookupQuery",
    "MarketCurrentQuery",
    "RecentResolutionsQuery",
    "NotificationsRawQuery",
    "NotificationStreamRawQuery",
    "PnlHistoryQuery",
    "PnlHistoryScopedQuery",
    "PortfolioSummaryRawQuery",
    "FantasyEntriesQuery",
    "PositionsQuery",
    "PositionsByMarketsQuery",
    "UpdatePreferencesRequest",
    "UpdateProfileRequest",
    "SyncXProfileRequest",
    "ChatPostMessageRequest",
    "ChatEditMessageRequest",
    "ChatEmojiReactRequest",
    "ChatStreamQuery",
    "ChatMentionCandidatesQuery",
    "ChatRecentMessagesQuery",
    "WalletAuthRequest",
    "UserSetReferrerRequest",
    "UserCreateReferralCodeRequest",
    "PlaceContestBetSelectionRequest",
    "PlaceContestBetRequest",
    "PlaceRosterPickRequest",
    "UserDepositRequest",
    "UserWithdrawParams",
    "UserWithdrawRequest",
    "CreateRfqRequest",
    "CommunityPickRequest",
    "UnsignedRfqOrderRequest",
    "CreateUnsignedRfqRequest",
    "PlaceStreakPickRequest",
    "StreakPicksRawQuery",
    "StreakHistoryRawQuery",
    "StreakLeaderboardRawQuery",
    "UserTransactionsRawQuery",
    "ConfirmPositionQuery",
    "ReferralsListRawQuery",
    "UserReferralStatsRawQuery",
    "WebPushSubscriptionKeys",
    "UpsertWebPushSubscriptionRequest",
    "DeleteWebPushSubscriptionRequest",
}

for _class_name in _DENY_UNKNOWN_FIELDS:
    globals()[_class_name].__serde_deny_unknown__ = True

for _class_name in {
    "AcceptedWithdrawOperationResponse",
    "LeaderboardEntry",
    "LeaderboardCaller",
    "DepositOperationResponse",
    "WithdrawOperationResponse",
}:
    globals()[_class_name].__serde_tag__ = None


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
    "UserWithdrawParams",
    "WithdrawalAuthorization",
    "UserWithdrawRequest",
    "build_wallet_authentication_message",
    "build_wallet_withdrawal_authorization_message",
    "encode_wallet_signature",
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
    "UserWithdrawResponse",
    "BalanceOperationStatus",
    "BalanceOperationStatusResponse",
    "DepositOperationResponse",
    "WithdrawOperationResponse",
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
