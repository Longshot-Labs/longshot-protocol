//! Community follow and pick contracts.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use super::profile::{PublicProfileContestDetailResponse, PublicProfilePositionDetailResponse};
use super::response::ContestGameTypeResponse;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct FollowingRawQuery {
    pub limit: Option<u32>,
    pub cursor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct CommunityPicksRawQuery {
    pub limit: Option<u32>,
}

/// Home Recent Winners query. The service deliberately caps this projection
/// at three cards; deeper winner browsing belongs to the Leaderboard.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct RecentWinnersRawQuery {
    /// Requested card count. Values above the Home capacity are clamped to 3.
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 3))]
    pub limit: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FollowStatusResponse {
    pub following: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CommunityProfileResponse {
    pub handle: String,
    pub display_name: String,
    pub avatar_seed: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    /// Whether the authenticated viewer follows this profile. Present on
    /// follower/following list rows when a session is provided; absent
    /// elsewhere.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub viewer_follows: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicProfileFollowingResponse {
    pub profiles: Vec<CommunityProfileResponse>,
    pub next_cursor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CommunityPickResponse {
    pub creator: CommunityProfileResponse,
    pub viewer_follows: bool,
    pub position: PublicProfilePositionDetailResponse,
    pub reactions: Vec<CommunityPickReactionResponse>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CommunityPickReactionResponse {
    pub emoji: String,
    pub count: i64,
    pub viewer_reacted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CommunityPicksResponse {
    pub picks: Vec<CommunityPickResponse>,
    /// Basis points credited to the creator from positive post-protocol copy profit.
    pub copy_fee_bps: u32,
    /// Resolved pool-image URL by Longshot market ID. A null value means the
    /// market has no configured image and clients should use their fallback.
    #[serde(default)]
    pub market_images: BTreeMap<String, Option<String>>,
    /// Render metadata keyed by Longshot market ID. This is additive to
    /// `market_images`, which remains available during the client rollout.
    #[serde(default)]
    pub market_contexts: BTreeMap<String, MarketDisplayContextResponse>,
}

/// NFL matchup identity used by matchup/team artwork clients.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SportsMarketDisplayContextResponse {
    pub league: String,
    pub product: String,
    pub game_id: String,
    pub away_team: String,
    pub home_team: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub kickoff_at_ms: Option<i64>,
}

/// Price-window identity used by crypto winner cards. `settled_change_bps`
/// is signed basis points from the canonical open to close when available.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PriceMarketDisplayContextResponse {
    pub asset: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_start_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_secs: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub settled_change_bps: Option<i32>,
}

/// Small, product-owned market presentation projection. Raw provider payloads
/// are intentionally not exposed.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketDisplayContextResponse {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_event_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub event_slug: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub event_title: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub sports: Option<SportsMarketDisplayContextResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub price: Option<PriceMarketDisplayContextResponse>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RecentMarketWinnerDetailRefResponse {
    pub handle: String,
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub position_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RecentContestWinnerDetailRefResponse {
    pub handle: String,
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub contest_id: String,
    pub entry_index: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum RecentMarketWinnerEntryTypeResponse {
    Single,
    Combo,
}

/// One render-ready Home winner. The Home feed currently emits only `Market`;
/// `Contest` remains in the wire type for backward-compatible deserialization.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum RecentWinnerResponse {
    Market {
        winner_id: String,
        settled_at_ms: i64,
        profile: CommunityProfileResponse,
        entry_type: RecentMarketWinnerEntryTypeResponse,
        /// Credited net payout divided by stake, in basis points.
        multiplier_bps: i64,
        position: PublicProfilePositionDetailResponse,
        detail_ref: RecentMarketWinnerDetailRefResponse,
        #[serde(default)]
        market_contexts: BTreeMap<String, MarketDisplayContextResponse>,
    },
    Contest {
        winner_id: String,
        settled_at_ms: i64,
        profile: CommunityProfileResponse,
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
        contest_id: String,
        entry_index: i32,
        title: String,
        category: String,
        game_type: ContestGameTypeResponse,
        /// Reveal-safe result and selections for immediate card rendering. The
        /// client still activates the card through `detail_ref` so normal
        /// loading/error states and fresh detail semantics are retained.
        contest: Box<PublicProfileContestDetailResponse>,
        detail_ref: RecentContestWinnerDetailRefResponse,
        image_url: Option<String>,
        #[serde(with = "crate::api::wire_int::i64_string")]
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
        stake_micros: i64,
        #[serde(with = "crate::api::wire_int::i64_string")]
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
        payout_micros: i64,
        #[serde(with = "crate::api::wire_int::i64_string")]
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
        net_payout_micros: i64,
        #[serde(with = "crate::api::wire_int::i64_string")]
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
        pnl_micros: i64,
        rank: Option<i32>,
        resolved_win_count: i32,
        selection_count: i32,
        #[serde(with = "crate::api::wire_int::option_i64_string")]
        #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64"))]
        roster_final_points_milli: Option<i64>,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RecentWinnersResponse {
    pub winners: Vec<RecentWinnerResponse>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn market_images_default_for_older_responses_and_preserve_null_fallbacks() {
        let older: CommunityPicksResponse = serde_json::from_value(serde_json::json!({
            "picks": [],
            "copy_fee_bps": 250
        }))
        .expect("deserialize older response");
        assert!(older.market_images.is_empty());
        assert!(older.market_contexts.is_empty());

        let response = CommunityPicksResponse {
            picks: Vec::new(),
            copy_fee_bps: 250,
            market_images: BTreeMap::from([
                (
                    "42".to_string(),
                    Some("/v1/pool-images/image-id/raw".to_string()),
                ),
                ("43".to_string(), None),
            ]),
            market_contexts: BTreeMap::new(),
        };
        let value = serde_json::to_value(response).expect("serialize response");
        assert_eq!(
            value["market_images"],
            serde_json::json!({
                "42": "/v1/pool-images/image-id/raw",
                "43": null
            })
        );
    }
}
