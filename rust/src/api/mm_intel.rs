//! Public market-maker intel API request and response contracts.

use serde::{Deserialize, Serialize};

use crate::types::MarketType;

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
    /// Requested row count. The server clamps this to 1-50; the default is 8.
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

/// One category-specific profit-cap override.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ProfitCapOverrideResponse {
    pub market_type: MarketType,
    pub max_profit_micros: u64,
}

/// Response for `GET /v1/mm/profit_caps`.
///
/// Each cap bounds taker profit (and therefore maker liability) per RFQ — the
/// payout net of the taker's returned stake — in the protocol's base
/// micro-unit.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ProfitCapConfigResponse {
    pub default_max_profit_micros: u64,
    pub overrides: Vec<ProfitCapOverrideResponse>,
}
