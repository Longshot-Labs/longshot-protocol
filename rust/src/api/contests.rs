//! Public contest API query contracts.

use serde::{Deserialize, Serialize};

/// Query params for `GET /v1/contests`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct ListContestsQuery {
    /// Filter to contests currently accepting entries or waiting for
    /// settlement (`open`), fully settled (`resolved`), or voided (`voided`).
    #[serde(default)]
    pub status: Option<String>,
    /// Restrict to a single contest category.
    #[serde(default)]
    pub category: Option<String>,
    /// Opaque cursor echoed back from a prior response's `next_cursor`.
    #[serde(default)]
    pub cursor: Option<String>,
    /// Max rows to return. Server clamps to 1..=50 regardless.
    #[serde(default)]
    pub limit: Option<u32>,
}

/// Query params for `GET /v1/contests/:id`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct ContestDetailQuery {
    /// Survivor rounds per page. Server accepts 1..=7 and defaults to 7.
    #[serde(default)]
    pub survivor_round_limit: Option<u32>,
    /// Exclusive Survivor game-index cursor. Server accepts 1..=32767.
    #[serde(default)]
    pub survivor_round_before: Option<u32>,
}

/// Query params for `GET /v1/contests/:id/leaderboard`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct ContestLeaderboardQuery {
    /// Opaque cursor echoed back from a prior response's `next_cursor`.
    #[serde(default)]
    pub cursor: Option<String>,
    /// Max rows to return. Server clamps to 1..=100.
    #[serde(default)]
    pub limit: Option<u32>,
    /// Survivor rounds per entry. Server accepts 1..=7 and defaults to 7.
    #[serde(default)]
    pub survivor_round_limit: Option<u32>,
    /// Exclusive Survivor game-index cursor shared by every entry.
    #[serde(default)]
    pub survivor_round_before: Option<u32>,
}

/// Query params for `GET /v1/contests/:id/top-participants`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct ContestTopParticipantsQuery {
    /// Lookback window in milliseconds. Defaults to 7 days.
    #[serde(default)]
    pub window_ms: Option<String>,
    /// Max rows to return. Server clamps to 1..=25.
    #[serde(default)]
    pub limit: Option<u32>,
}
