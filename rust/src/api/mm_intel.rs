//! Public market-maker intel API request and response contracts.

use serde::{Deserialize, Serialize};

/// Query parameters for `GET /v1/mm/recent_resolutions`.
///
/// Reads recent price-market resolutions by asset ticker and price-window
/// duration.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct RecentResolutionsQuery {
    pub asset: String,
    pub duration_secs: u32,
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 50))]
    pub limit: Option<u32>,
}

/// Single recent price-market resolution row.
///
/// `outcome` is serialized as the wire string (`"YES"` or `"NO"`).
/// `window_start_ms` identifies the price window and is the canonical field
/// for ordering resolutions and checking that consecutive windows are
/// adjacent. `resolved_at_ms` records when settlement completed.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RecentResolutionEntry {
    pub market_id: u64,
    pub outcome: String,
    pub window_start_ms: i64,
    pub resolved_at_ms: i64,
}

/// Response for `GET /v1/mm/recent_resolutions`.
///
/// Contains recent resolutions for a specific `(asset, duration_secs)` price
/// market.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RecentResolutionsResponse {
    pub asset: String,
    pub duration_secs: u32,
    pub resolutions: Vec<RecentResolutionEntry>,
}
