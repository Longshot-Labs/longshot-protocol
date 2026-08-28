//! Public NFL hub config API response types.
//!
//! Mirrors the server's `GET /v1/nfl_hub_config` wire shapes (the admin
//! read-modify-write endpoints are intentionally out of protocol scope).

use serde::{Deserialize, Serialize};

/// One admin-picked featured NFL matchup, referenced by engine game id.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct NflFeaturedMatchup {
    /// Engine game id (e.g. "26SEP09NESEA").
    pub game_id: String,
}

/// One leg of the curated featured parlay.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct NflParlayLeg {
    /// Market ID for the leg.
    pub market_id: u64,
    /// Direction: "up" or "down".
    pub direction: String,
}

/// Admin-curated featured parlay shown on the NFL hub.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct NflFeaturedParlay {
    /// Display title.
    pub title: String,
    /// Optional supporting copy.
    #[serde(default)]
    pub copy: Option<String>,
    /// Parlay legs.
    pub legs: Vec<NflParlayLeg>,
}

/// Curated NFL hub content.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct NflHubConfigBody {
    /// Admin-picked featured games, by engine game id.
    #[serde(default)]
    pub featured_matchups: Vec<NflFeaturedMatchup>,
    /// Optional curated featured parlay.
    #[serde(default)]
    pub featured_parlay: Option<NflFeaturedParlay>,
    /// Kill switch for every player-prop surface on the NFL frontend.
    pub props_enabled: bool,
}

/// Public NFL hub config.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct NflHubConfigResponse {
    pub config: NflHubConfigBody,
}
