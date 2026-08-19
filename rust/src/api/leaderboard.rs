//! Leaderboard API request and response types.

use serde::{Deserialize, Serialize};

use super::position_identity::PrimaryLegIdentityResponse;

/// Time window for leaderboard filtering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum LeaderboardWindow {
    Day,
    Week,
    Month,
    AllTime,
}

/// Raw query params for GET /v1/leaderboard.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct LeaderboardRawQuery {
    pub period: Option<String>,
    pub scope: Option<String>,
    pub metric: Option<String>,
    pub limit: Option<u32>,
}

/// Raw query params for GET /v1/leaderboard/me.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct LeaderboardMeRawQuery {
    pub metric: Option<String>,
    pub window: Option<String>,
    pub asset: Option<String>,
}

/// Raw query params for GET /v1/leaderboard/highlights.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct HighlightsRawQuery {
    pub sort: Option<String>,
    pub window: Option<String>,
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 100))]
    pub limit: Option<u32>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(as = LeaderboardMetric))]
#[serde(rename_all = "snake_case")]
pub enum LeaderboardMetricResponse {
    Pnl,
    Volume,
    Roi,
    Wins,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(as = HighlightSort))]
#[serde(rename_all = "snake_case")]
pub enum HighlightSortResponse {
    Payout,
    Multiplier,
}

/// Calendar period for the current global leaderboard.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum LeaderboardPeriod {
    Daily,
    Weekly,
    Monthly,
    AllTime,
}

/// Product scope included in the current global leaderboard.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum LeaderboardScope {
    All,
    Markets,
    Contests,
}

/// Ranking metric used by the current global leaderboard.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum LeaderboardMetric {
    Pnl,
    Combo,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardPnlEntry {
    pub rank: u32,
    pub handle: Option<String>,
    pub display_name: Option<String>,
    pub avatar_seed: Option<i32>,
    pub x_avatar_url: Option<String>,
    pub entry_count: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub pnl_micros: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardComboEntry {
    pub rank: u32,
    pub handle: Option<String>,
    pub display_name: Option<String>,
    pub avatar_seed: Option<i32>,
    pub x_avatar_url: Option<String>,
    pub combo_legs: i64,
    pub multiplier_bps: i64,
}

/// A row has one of two shapes selected by `metric` on the response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(untagged)]
pub enum LeaderboardEntry {
    Pnl(LeaderboardPnlEntry),
    Combo(LeaderboardComboEntry),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardPnlCaller {
    pub rank: u32,
    pub entry_count: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub pnl_micros: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardComboCaller {
    pub rank: u32,
    pub combo_legs: i64,
    pub multiplier_bps: i64,
}

/// Authenticated caller standing in the metric-specific shape.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(untagged)]
pub enum LeaderboardCaller {
    Pnl(LeaderboardPnlCaller),
    Combo(LeaderboardComboCaller),
}

/// Legacy paginated leaderboard row retained for the older rank endpoints.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "rank": 1,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "handle": "willow",
    "display_name": "Willow",
    "avatar_seed": 42,
    "x_handle": "willow_x",
    "created_at_ms": 1701388800000_i64,
    "metric_value": "123456789",
    "total_positions": 769,
    "wins": 500,
    "losses": 269,
    "biggest_win_micros": "1234511000",
    "highest_multiplier_bps": 39000
})))]
pub struct LegacyLeaderboardEntry {
    /// 1-indexed rank within the current query.
    pub rank: u32,
    /// User ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    /// User handle (may be null for users who haven't set one).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub handle: Option<String>,
    /// Display name.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    /// Avatar seed for deterministic avatar generation.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avatar_seed: Option<i32>,
    /// X/Twitter handle (if linked).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    /// X/Twitter avatar URL (if linked).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    /// Account creation timestamp (ms).
    pub created_at_ms: i64,
    /// The value for the selected metric (micros for pnl/volume, bps for roi, count for wins).
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub metric_value: i64,
    /// Total resolved positions.
    pub total_positions: i64,
    /// Total wins.
    pub wins: i64,
    /// Total losses.
    pub losses: i64,
    /// Biggest single-position win in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub biggest_win_micros: i64,
    /// Highest single-position multiplier in basis points (e.g., 39000 = 3.9x).
    pub highest_multiplier_bps: i64,
}

/// GET /v1/leaderboard response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardResponse {
    pub period: LeaderboardPeriod,
    pub scope: LeaderboardScope,
    pub metric: LeaderboardMetric,
    pub period_start_ms: i64,
    pub period_end_ms: i64,
    pub entries: Vec<LeaderboardEntry>,
    pub caller: Option<LeaderboardCaller>,
}

/// GET /v1/leaderboard/me response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardMyRankResponse {
    /// The requesting user's leaderboard entry, or null if they have no qualifying positions.
    pub entry: Option<LegacyLeaderboardEntry>,
}

/// Single highlight entry (top position).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "position_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "660e8400-e29b-41d4-a716-446655440001",
    "display_name": "Willow",
    "avatar_seed": 42,
    "x_handle": "willow_x",
    "market": "BTC",
    "duration_label": "15 mins",
    "legs_count": 1,
    "wager_micros": "12345678000",
    "payout_micros": "67901229000",
    "multiplier_bps": 55000
})))]
pub struct HighlightEntry {
    /// Position ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub position_id: String,
    /// User ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    /// Display name.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    /// Avatar seed.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avatar_seed: Option<i32>,
    /// X/Twitter handle.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    /// X/Twitter avatar URL.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    /// Human-readable market label for the position.
    pub market: String,
    /// Human-readable timeframe from a price primary leg.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_label: Option<String>,
    /// Structured primary-leg identity for market-agnostic clients.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub primary_leg: Option<PrimaryLegIdentityResponse>,
    /// Number of legs in the position.
    pub legs_count: i16,
    /// Wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Payout amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Multiplier in basis points (e.g., 55000 = 5.5x).
    pub multiplier_bps: i64,
}

/// GET /v1/leaderboard/highlights response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LeaderboardHighlightsResponse {
    /// Selected sort.
    pub sort: HighlightSortResponse,
    /// Selected window.
    pub window: LeaderboardWindow,
    /// Top positions.
    pub highlights: Vec<HighlightEntry>,
}
