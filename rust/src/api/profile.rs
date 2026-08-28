//! Profile API request and response types.

use serde::{Deserialize, Serialize};

use super::portfolio::LegDetail;
use super::response::{
    ContestGameTypeResponse, ContestUserEntryResponse, PublicContestDetailResponse,
    SurvivorEntryStateResponse,
};
use crate::types::MarketType;

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
pub struct CheckHandleQuery {
    pub handle: String,
}

/// Query parameters for profile updates that may finalize onboarding.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ProfileUpdateQuery {
    #[serde(default)]
    pub finalize_onboarding: bool,
}

/// Query parameters for handle availability checks.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct HandleAvailabilityQuery {
    pub handle: String,
    #[serde(default)]
    pub finalize_onboarding: bool,
}

/// Profile response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ProfileResponse {
    pub handle: String,
    pub display_name: String,
    pub avatar_seed: i32,
    /// Verified email synced from Privy identity claims, if set.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub email: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    /// The user's vanity referral code, if they have created one.
    /// Always present in the response shape; `null` when unset.
    pub referral_code: Option<String>,
}

/// Public profile response (no email, includes stats).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileResponse {
    pub handle: String,
    pub display_name: String,
    pub avatar_seed: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    pub created_at_ms: i64,
    pub stats: PublicProfileStatsResponse,
    /// Settled, non-refunded rank 1-10 entries, excluding Outcast.
    pub top_ten_finishes: i32,
    /// Visible profiles following this user.
    pub follower_count: u32,
    /// Visible profiles this user follows.
    pub following_count: u32,
}

/// Public profile portfolio statistics.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileStatsResponse {
    /// Total public positions ever created.
    pub total_positions: i32,
    /// Currently open public positions.
    pub open_positions: i32,
    /// Total public wins.
    pub wins: i32,
    /// Total public losses.
    pub losses: i32,
    /// Public win rate as percentage (0-100).
    pub win_rate_pct: f64,
    /// Total realized public PNL in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub total_pnl_micros: i64,
}

/// Scope-filtered headline statistics for a public portfolio.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileSummaryResponse {
    pub scope: String,
    pub active_count: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub potential_payout_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub realized_pnl_micros: i64,
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(
            value_type = Option<String>,
            format = "int64",
            nullable = true,
            required
        )
    )]
    pub biggest_win_micros: Option<i64>,
}

/// Public profile PNL point for charting.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfilePnlEventResponse {
    /// Source product for this PNL point: "position" or "fantasy".
    pub source: String,
    /// Timestamp when the event resolved, or the last event in an aggregated point, in Unix milliseconds.
    pub resolved_at_ms: i64,
    /// Position ID that resolved, or the last position represented by an aggregated point.
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid"))]
    pub position_id: Option<String>,
    /// Contest ID that resolved, or the last contest represented by an aggregated point.
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid"))]
    pub contest_id: Option<String>,
    /// PNL from this event or aggregated point in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub pnl_micros: i64,
    /// Cumulative PNL after this resolution or aggregated point in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub cumulative_micros: i64,
}

/// Public profile PNL history response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfilePnlHistoryResponse {
    /// List of public PNL events for charting.
    pub events: Vec<PublicProfilePnlEventResponse>,
}

/// Public fantasy contest entry on a profile.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileFantasyEntryResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub contest_id: String,
    pub title: String,
    pub category: String,
    pub status: String,
    /// Contest game type for this public-profile entry.
    pub game_type: ContestGameTypeResponse,
    /// Immutable Survivor round count, absent for other contest types.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 32767))]
    pub survivor_round_count: Option<u32>,
    /// Authoritative Survivor round cursor, absent for other contest types.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[cfg_attr(feature = "openapi", schema(minimum = 0, maximum = 32766))]
    pub current_game_index: Option<u32>,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub bet_amount_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub protocol_prize_pool_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub total_pot_micros: i64,
    pub entries_filled: i64,
    pub entry_cap: i32,
    pub entry_opens_at_ms: Option<i64>,
    pub betting_closes_ms: i64,
    pub live_ends_at_ms: Option<i64>,
    pub resolved_at_ms: Option<i64>,
    pub joined_at_ms: i64,
    pub entry_index: i32,
    pub open_leg_count: i32,
    pub resolved_win_count: i32,
    pub rank: Option<i32>,
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub payout_micros: Option<i64>,
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub net_payout_micros: Option<i64>,
    /// Whether settlement returned this entry's stake without a win or loss.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required, default = false))]
    pub refunded: bool,
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub pnl_micros: Option<i64>,
    /// Resolved image URL, if any.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
    /// Reveal-safe Survivor state for this public profile entry, when applicable.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor: Option<SurvivorEntryStateResponse>,
    /// Authoritative submitted-pick count for this entry.
    pub selection_count: i32,
    /// Settled Survivor rounds voided for this entry.
    pub survivor_voided_round_count: Option<i32>,
    /// Contest betting-open timestamp when one is scheduled.
    pub betting_opens_ms: Option<i64>,
}

/// Public fantasy contest entries on a profile.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileFantasyEntriesResponse {
    pub entries: Vec<PublicProfileFantasyEntryResponse>,
    pub next_cursor: Option<String>,
}

/// Visibility policy applied to a public profile owner's contest entries.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum PublicProfileContestOwnerEntryVisibilityResponse {
    /// Betting is still open, so profile-owner picks are withheld.
    HiddenWhileBettingOpen,
    /// Betting has closed, so profile-owner picks are immutable and visible.
    Visible,
}

/// Profile-owner-scoped fields on public profile contest detail.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileContestOwnerResponse {
    /// True when the public profile owner has entered this contest.
    pub joined: bool,
    /// Whether `entries` is allowed to contain profile-owner picks.
    pub entry_visibility: PublicProfileContestOwnerEntryVisibilityResponse,
    /// Entries for the public profile owner. Empty while live picks are hidden,
    /// even when `joined` is true.
    pub entries: Vec<ContestUserEntryResponse>,
}

/// Public profile contest detail response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileContestDetailResponse {
    #[serde(flatten)]
    pub contest: PublicContestDetailResponse,
    pub profile_owner: PublicProfileContestOwnerResponse,
}

/// Public position summary on a profile.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfilePositionSummaryResponse {
    /// Position ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub id: String,
    /// Wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Portion of the wager funded by bonus credits, in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub app_token_wager_micros: i64,
    /// Bonus credits actually returned when this position was voided. Expired
    /// credits reclaimed by the grantor are excluded; null for other states.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub refunded_app_token_micros: Option<i64>,
    /// Gross potential payout in micros before fees.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Realized net payout in micros after fees.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub net_payout_micros: Option<i64>,
    pub legs_count: i16,
    pub legs_summary: String,
    /// Position status: "open", "won", "lost", "pending", "cancelled", or "voided".
    pub status: String,
    /// Realized PNL in micros.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub pnl_micros: Option<i64>,
    pub created_at_ms: i64,
    pub resolved_at_ms: Option<i64>,
    /// True when at least one leg is a binary-event contract.
    pub has_binary_event_leg: bool,
    /// Sorted, distinct categories represented by the position's legs.
    pub market_types: Vec<MarketType>,
}

/// Public positions list on a profile.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfilePositionsResponse {
    pub positions: Vec<PublicProfilePositionSummaryResponse>,
    pub next_cursor: Option<String>,
}

/// Public position detail on a profile.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfilePositionDetailResponse {
    /// Position ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub id: String,
    /// Wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Portion of the wager funded by bonus credits, in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub app_token_wager_micros: i64,
    /// Bonus credits actually returned when this position was voided. Expired
    /// credits reclaimed by the grantor are excluded; null for other states.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub refunded_app_token_micros: Option<i64>,
    /// Gross potential payout in micros before fees.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Realized net payout in micros after fees.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub net_payout_micros: Option<i64>,
    pub legs_count: i16,
    pub legs_summary: String,
    /// Position status: "open", "won", "lost", "pending", "cancelled", or "voided".
    pub status: String,
    /// Realized PNL in micros.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
    pub pnl_micros: Option<i64>,
    pub created_at_ms: i64,
    pub resolved_at_ms: Option<i64>,
    /// All legs with their outcomes.
    pub legs: Vec<LegDetail>,
}

/// Update profile request.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct UpdateProfileRequest {
    /// New handle (3-30 chars, alphanumeric + underscore).
    pub handle: Option<String>,
    /// New display name (1-50 chars).
    pub display_name: Option<String>,
}

/// Request to sync the caller's X/Twitter profile from a verified Privy identity token.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct SyncXProfileRequest {
    /// Fresh Privy identity token for the authenticated caller.
    pub privy_token: String,
}

/// Handle availability check response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CheckHandleResponse {
    pub available: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}
