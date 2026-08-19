//! Request and response types for the public `/v1/streak` API.

use serde::{Deserialize, Serialize};

use super::{
    markets::EventMarketSource,
    response::{ContestDirectionResponse, ContestLegOutcome},
};
use crate::types::{MarketStatus, MarketType, Outcome, TradingChannel};

/// Streak round lifecycle. Mirrors `contest_games.status` semantically:
/// `open` while the round still accepts picks, `resolving` after betting
/// closes but before all legs settle, and `resolved` once per-entry
/// streak math has been applied.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum StreakRoundStatusResponse {
    Open,
    Resolving,
    Resolved,
}

/// A configured payout tier. `streak` is the consecutive-round-win count
/// at which the payout fires; `payout_micros` is the dollar payout
/// (USDC micros); `has_app_token` flags whether the tier also grants an
/// `AppTokenConfig` kickback. (The token config itself is intentionally
/// not echoed — the streak card only needs to render the dollar headline.)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakTierResponse {
    pub streak: u32,
    pub payout_micros: u64,
    pub has_app_token: bool,
}

/// One market entry in today's pick slate.
///
/// `name` is the headline; the source tuple identifies the upstream market.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakMarketResponse {
    pub market_id: u64,
    pub selection_group: String,
    pub market_type: MarketType,
    pub trading_channels: Vec<TradingChannel>,
    pub name: String,
    pub status: MarketStatus,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub outcome: Option<Outcome>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub source: Option<EventMarketSource>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolution_time_ms: Option<u64>,
    /// Per-market cutoff for staggered rounds. The round closes at the latest
    /// cutoff; each card uses its own value for the countdown.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub betting_closes_at_ms: Option<u64>,
    /// Resolved image URL for this market, if any.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
    /// Whether this is the first-pick boosted-odds onboarding market.
    #[serde(default)]
    pub juiced: bool,
}

/// Caller's pick in the current round, if they have one.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakUserPickResponse {
    pub market_id: u64,
    pub direction: ContestDirectionResponse,
    pub outcome: ContestLegOutcome,
    pub picked_at_ms: u64,
}

/// The current round of the active Streak contest — today's slate,
/// the betting deadline, and the caller's pick if submitted.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakCurrentRoundResponse {
    pub game_index: u32,
    pub status: StreakRoundStatusResponse,
    pub betting_opens_at_ms: u64,
    pub betting_closes_at_ms: u64,
    pub resolved_at_ms: Option<u64>,
    pub markets: Vec<StreakMarketResponse>,
    pub user_pick: Option<StreakUserPickResponse>,
}

/// Caller's persistent streak state across all rounds of this
/// contest. Returned only when the caller has placed at least one
/// pick; first-time visitors get `user = null`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakUserStateResponse {
    pub win_streak: u32,
    pub games_won: u32,
    pub games_lost: u32,
    pub bets_won: u32,
    pub bets_lost: u32,
}

/// Full payload for `GET /v1/streak`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub contest_id: String,
    pub title: String,
    pub description: Option<String>,
    pub tiers: Vec<StreakTierResponse>,
    pub max_streak: u32,
    pub current_round: Option<StreakCurrentRoundResponse>,
    /// Pre-staged round at `current_round.game_index + 1`, if one exists.
    /// Same shape as `current_round`. Null until the next round is scheduled,
    /// then null again once it becomes the current round.
    pub scheduled_round: Option<StreakCurrentRoundResponse>,
    pub user: Option<StreakUserStateResponse>,
}

/// Which round a pick targets. Defaults to `current`. `scheduled`
/// requires a pre-staged round to exist; otherwise the API returns
/// `STREAK_NO_SCHEDULED_ROUND`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum StreakPickRound {
    #[default]
    Current,
    Scheduled,
}

/// Request body for `POST /v1/streak/pick`.
///
/// Exactly one market plus direction. The API chooses `entry_index`
/// automatically based on whether the caller already has an entry in the active
/// Streak contest. The optional `round` field targets either the current round
/// (default) or a pre-scheduled round when one exists. The one-pick-per-cycle
/// rule applies: a user with a pick already locked on either round is rejected
/// with `CONTEST_BET_ALREADY_PLACED`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PlaceStreakPickRequest {
    pub market_id: u64,
    /// `"up"` for Yes, `"down"` for No.
    #[cfg_attr(feature = "openapi", schema(example = "up"))]
    pub direction: String,
    /// If true, spend eligible app tokens before cash when creating the entry.
    pub use_app_tokens: bool,
    /// Defaults to `current` when omitted.
    #[serde(default)]
    pub round: Option<StreakPickRound>,
}

/// Response body for `POST /v1/streak/pick`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PlaceStreakPickResponse {
    pub entry_index: u32,
    pub picked_at_ms: u64,
}

/// Query for streak pick history.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct StreakPicksRawQuery {
    pub limit: Option<u32>,
    pub cursor: Option<String>,
    pub contest_id: Option<String>,
}

/// Query for derived streak-run history.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct StreakHistoryRawQuery {
    pub limit: Option<u32>,
    pub cursor: Option<String>,
}

/// Query for the live streak leaderboard.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct StreakLeaderboardRawQuery {
    pub limit: Option<u32>,
}

/// One streak pick with its current market context.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakPickHistoryItemResponse {
    pub game_index: i16,
    pub market_id: u64,
    pub market_title: String,
    pub market_category: String,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub market_outcome: Option<Outcome>,
    pub direction: ContestDirectionResponse,
    pub outcome: ContestLegOutcome,
    pub picked_at_ms: i64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub betting_closes_at_ms: Option<i64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_at_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
}

/// Own pick history in the active streak contest.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakPicksResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true, required))]
    pub contest_id: Option<String>,
    pub title: Option<String>,
    pub picks: Vec<StreakPickHistoryItemResponse>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub next_cursor: Option<String>,
}

/// Visibility of the current round's pick on a public surface.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum StreakPickVisibilityResponse {
    Visible,
    HiddenWhileBettingOpen,
    None,
}

/// Public pick history with anti-copy-trading visibility state.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileStreakPicksResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true, required))]
    pub contest_id: Option<String>,
    pub title: Option<String>,
    pub picks: Vec<StreakPickHistoryItemResponse>,
    pub current_round_pick_visibility: StreakPickVisibilityResponse,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub next_cursor: Option<String>,
}

/// Derived lifecycle of one streak run.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum StreakRunStatusResponse {
    Active,
    Ended,
    Expired,
    Won,
}

/// One payout tier crossed during a streak run.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakRunTierPayoutResponse {
    pub streak: u32,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    pub is_app_token: bool,
    pub game_index: i16,
    pub won_at_ms: i64,
    pub credited: bool,
}

/// One historical or active streak run.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakRunResponse {
    pub contest_id: String,
    pub title: String,
    pub max_streak: u32,
    pub status: StreakRunStatusResponse,
    pub length: u32,
    pub pick_count: u32,
    pub start_game_index: i16,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub end_game_index: Option<i16>,
    pub started_at_ms: i64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub ended_at_ms: Option<i64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub failed_pick_number: Option<u32>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub failed_pick: Option<StreakPickHistoryItemResponse>,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub cash_payout_micros: i64,
    pub tier_payouts: Vec<StreakRunTierPayoutResponse>,
}

/// Derived streak-run history for the authenticated caller.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakHistoryResponse {
    pub runs: Vec<StreakRunResponse>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub next_cursor: Option<String>,
}

/// Public twin of the derived streak-run history response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileStreakHistoryResponse {
    pub runs: Vec<StreakRunResponse>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub next_cursor: Option<String>,
}

/// Round used by the one-time first-pick onboarding offer.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakOnboardingRoundResponse {
    pub game_index: u32,
    pub target: StreakPickRound,
    pub betting_closes_at_ms: u64,
    pub markets: Vec<StreakMarketResponse>,
}

/// One-time first-pick onboarding offer.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakOnboardingResponse {
    pub contest_id: String,
    pub title: String,
    pub eligible: bool,
    pub round: Option<StreakOnboardingRoundResponse>,
}

/// Aggregate pick counts for one market of the active round.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakPopularMarketResponse {
    pub market_id: u64,
    pub market_title: String,
    pub market_category: String,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub betting_closes_at_ms: Option<i64>,
    pub up_count: i64,
    pub down_count: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
}

/// Crowd-level pick counts for the active round.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakPopularTodayResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true, required))]
    pub contest_id: Option<String>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub game_index: Option<i16>,
    pub total_picks: i64,
    pub markets: Vec<StreakPopularMarketResponse>,
}

/// One entrant on the live streak leaderboard.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakLeaderboardRowResponse {
    pub handle: Option<String>,
    pub display_name: Option<String>,
    pub avatar_seed: i32,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub x_handle: Option<String>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub x_avatar_url: Option<String>,
    pub current_streak: i32,
    pub picks: Vec<StreakPickHistoryItemResponse>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub current_pick: Option<StreakPickHistoryItemResponse>,
    pub current_pick_visibility: StreakPickVisibilityResponse,
}

/// Longest live streaks with public pick history.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct StreakLeaderboardResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true, required))]
    pub contest_id: Option<String>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub current_game_index: Option<i16>,
    pub rows: Vec<StreakLeaderboardRowResponse>,
}
