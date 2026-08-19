//! User notification API request and response types.

pub const NOTIFICATION_LIST_DEFAULT_LIMIT: u32 = 30;
pub const NOTIFICATION_LIST_MAX_LIMIT: u32 = 100;
pub const NOTIFICATION_STREAM_BATCH_LIMIT: u32 = 50;

use serde::{Deserialize, Serialize};

/// Notification list query parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct NotificationsRawQuery {
    /// Filter: "all" (default) or "unread".
    pub filter: Option<String>,
    /// Number of notifications to return.
    pub limit: Option<u32>,
    /// Pagination cursor returned from a previous response.
    pub cursor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct NotificationStreamRawQuery {
    /// Cursor after which new notifications should be streamed.
    pub after: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum NotificationPayload {
    /// A binary-event position is approaching betting close.
    BinaryEventStartSoon(BinaryEventStartSoonNotificationPayload),
    /// A fantasy contest entry is approaching betting close.
    FantasyStartSoon(FantasyStartSoonNotificationPayload),
    /// A streak pick is approaching betting close.
    StreakStartSoon(StreakStartSoonNotificationPayload),
    /// A positive streak is approaching inactivity expiry.
    StreakExpiring(StreakExpiringNotificationPayload),
    /// A binary-event RFQ position won.
    BinaryEventWin(BinaryEventWinNotificationPayload),
    /// A price-strike parlay RFQ position won.
    PriceStrikeParlayWin(PriceStrikeParlayWinNotificationPayload),
    /// An RFQ request reached a terminal result.
    RfqResult(RfqResultNotificationPayload),
    /// Aggregate fantasy result for one user's entries in one game.
    FantasyResult(FantasyResultNotificationPayload),
    /// One or more of the user's entries won the Perfect Slate bonus.
    PerfectSlate(PerfectSlateNotificationPayload),
    /// A streak entry won or completed a streak.
    StreakWin(StreakWinNotificationPayload),
    /// A streak entry settled as a loss.
    StreakSettled(StreakSettledNotificationPayload),
    /// A contest payout was held for admin review or released after it.
    PayoutReview(PayoutReviewNotificationPayload),
    /// Bonus credits were granted to the user's available balance.
    CreditsGranted(CreditsGrantedNotificationPayload),
    /// Another user mentioned the recipient in chat.
    ChatMention(ChatMentionNotificationPayload),
    /// Unknown or malformed stored notifications remain visible through
    /// top-level title/body fields, but storage JSON is not exposed.
    Unknown(UnknownNotificationPayload),
}

/// Binary-event start-soon notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct BinaryEventStartSoonNotificationPayload {
    pub source: String,
    pub event_id: String,
    pub market_title: String,
    pub starts_at_ms: i64,
}

/// Fantasy contest start-soon notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FantasyStartSoonNotificationPayload {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_image_scope_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub contest_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub entry_index: Option<u32>,
    pub contest_title: String,
    pub starts_at_ms: i64,
    pub selection_count: u32,
}

/// Streak start-soon notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakStartSoonNotificationPayload {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_image_scope_id: Option<String>,
    pub contest_title: String,
    pub market_title: String,
    pub starts_at_ms: i64,
}

/// Streak inactivity-expiry warning notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakExpiringNotificationPayload {
    pub contest_id: String,
    pub contest_title: String,
    pub entry_index: u32,
    pub win_streak: u32,
    pub expires_at_ms: i64,
}

/// Binary-event win notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct BinaryEventWinNotificationPayload {
    pub position_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub event_id: Option<String>,
    pub net_payout_micros: i64,
    pub multiplier_bps: i64,
    pub market_title: String,
}

/// Price-strike parlay win notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PriceStrikeParlayWinNotificationPayload {
    pub position_id: String,
    pub net_payout_micros: i64,
    pub multiplier_bps: i64,
    pub leg_summary: String,
    pub is_multi_asset: bool,
    pub duration_secs: Vec<i32>,
}

/// RFQ terminal-result notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RfqResultNotificationPayload {
    pub request_id: String,
    pub status: RfqResultNotificationStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub final_wager_micros: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub payout_micros: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub odds: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum RfqResultNotificationStatus {
    Completed,
    Failed,
    Cancelled,
    Timeout,
}

/// Aggregate result for all of one user's entries in one fantasy game.
///
/// The API mapper guarantees that there is at least one entry, successful and
/// held counts do not exceed their enclosing counts, payout amounts are
/// nonnegative, and `correct_count` does not exceed `selection_count` when both
/// scores are present. This crate intentionally does not validate these invariants.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FantasyResultNotificationPayload {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_image_scope_id: Option<String>,
    pub contest_id: String,
    /// Zero-based index of the settled game within the contest.
    pub game_index: u32,
    pub game_type: FantasyResultGameType,
    pub contest_title: String,
    /// Whether the contest has no game after this result.
    pub contest_terminal: bool,
    /// Whether this result returned every entry's stake instead of producing
    /// winners and losers. Currently only used for whole-field Outcast ties.
    pub contest_refunded: bool,
    pub entry_count: u32,
    /// Successful entries: payout winners for Lineups, advancing or champion
    /// entries for Survivor, and entries that stayed with the pack for Outcast.
    pub successful_entry_count: u32,
    /// Successful entries whose payouts remain under review.
    pub held_entry_count: u32,
    /// Amount credited or granted immediately after reimbursements, excluding
    /// held payouts.
    pub credited_payout_micros: i64,
    /// Amount still pending review after applicable reimbursements.
    pub held_payout_micros: i64,
    /// Entry that supplied the reported rank and score, when available.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub best_entry: Option<FantasyResultBestEntry>,
    /// Aggregate tiebreaker result, when the game exposes one.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tiebreaker_result: Option<i64>,
}

/// Fantasy game whose result is summarized by the notification.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum FantasyResultGameType {
    Lineups,
    Survivor,
    Outcast,
    Roster,
}

/// Best entry selected for the aggregate fantasy result.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FantasyResultBestEntry {
    pub entry_index: u32,
    pub rank: u32,
    /// Missing score fields mean score details are unavailable or hidden.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub correct_count: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub selection_count: Option<u32>,
}

/// Aggregate Perfect Slate result for one user's winning entries in one game.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PerfectSlateNotificationPayload {
    pub contest_id: String,
    /// Zero-based index of the settled game within the contest.
    pub game_index: u32,
    pub contest_title: String,
    pub winning_entry_count: u32,
    /// Zero-based indexes of the user's entries that won the bonus.
    pub entry_indexes: Vec<u32>,
    /// Total Perfect Slate bonus across `entry_indexes`.
    pub payout_micros: i64,
    /// Winning entries whose full contest payout remains under review.
    pub held_entry_count: u32,
    /// Total configured Perfect Slate pool shared by all qualifying entries.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_micros: Option<i64>,
    /// Total number of qualifying entries across every user.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total_winning_entry_count: Option<u32>,
}

/// Streak win notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakWinNotificationPayload {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_image_scope_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub contest_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub game_index: Option<i64>,
    pub contest_title: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_title: Option<String>,
    pub win_streak: u32,
    pub payout_micros: i64,
    /// Portion of `payout_micros` denominated in bonus credits. Absent on
    /// notifications recorded before the field existed.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub app_token_micros: Option<i64>,
    /// Whether the entire settled payout was denominated in bonus credits.
    /// Mixed payouts report false; use `app_token_micros` for the split.
    /// Absent on notifications recorded before the field existed.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_app_token: Option<bool>,
    pub outcome: StreakWinOutcome,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum StreakWinOutcome {
    Win,
    WinAndReset,
}

/// Streak settled notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakSettledNotificationPayload {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_image_scope_id: Option<String>,
    pub contest_title: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_title: Option<String>,
    pub win_streak: u32,
    pub outcome: StreakSettledOutcome,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum StreakSettledOutcome {
    Loss,
}

/// Contest payout admin review notification payload, used when a payout is
/// first held (`payout_held`), released (`payout_released`), or declined
/// (`payout_rejected`).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PayoutReviewNotificationPayload {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pool_image_scope_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub contest_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub entry_index: Option<u32>,
    pub contest_title: String,
    pub payout_micros: i64,
    /// Portion of `payout_micros` denominated in bonus credits. Absent on
    /// notifications recorded before the field existed.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub app_token_micros: Option<i64>,
    /// Whether the entire payout is denominated in bonus credits. Mixed
    /// payouts report false; use `app_token_micros` for the split. Absent on
    /// notifications recorded before the field existed.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_app_token: Option<bool>,
    pub status: PayoutReviewNotificationStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum PayoutReviewNotificationStatus {
    Pending,
    Approved,
    Rejected,
}

/// Bonus-credits grant notification payload.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CreditsGrantedNotificationPayload {
    pub grant_id: String,
    pub amount_micros: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub contest_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub game_index: Option<i64>,
}

/// Deprecated product hint for clients that predate generic chat routes.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum ChatMentionContext {
    Contest,
    CryptoMarket,
}

/// Product-neutral chat mention destination.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChatMentionNotificationPayload {
    pub chat_id: String,
    pub message_id: String,
    /// Deprecated routing hint retained while older clients migrate to `chat_id`.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub chat_context: Option<ChatMentionContext>,
    /// Deprecated contest destination retained for stored legacy notifications.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub contest_id: Option<String>,
}

/// Minimal fallback for unknown or malformed persisted notification rows.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UnknownNotificationPayload {}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct NotificationResponse {
    /// Monotonic per-row sequence. Use as the `?after=` cursor on the
    /// SSE stream and as the value to advance pagination cursors with.
    pub seq: i64,
    pub id: String,
    #[serde(rename = "type")]
    pub notification_type: String,
    pub category: String,
    pub title: String,
    pub body: String,
    pub icon: String,
    pub payload: NotificationPayload,
    pub created_at_ms: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub read_at_ms: Option<i64>,
    /// Resolved image URL, if any. Binary-event notifications
    /// use the provider-neutral `source:event_id` key for explicit assignments
    /// and their event title for keyword fallback. For active Kalshi event
    /// markets, the explicit assignment key is `kalshi:<event_id>`. Fantasy notifications use
    /// their single-event pool image scope id for explicit assignments and
    /// contest title for keyword fallback.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct NotificationsResponse {
    pub notifications: Vec<NotificationResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
    pub unread_count: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct NotificationMutationResponse {
    pub notification: NotificationResponse,
    pub unread_count: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct NotificationBulkMutationResponse {
    pub updated_count: u64,
    pub unread_count: u64,
}
