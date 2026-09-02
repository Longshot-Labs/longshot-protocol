//! Portfolio API request and response types.

use serde::{Deserialize, Serialize};

use crate::types::{Address, MarketType, PositionId};

/// User portfolio statistics.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PortfolioStatsResponse {
    /// Total positions ever created.
    pub total_positions: i32,
    /// Currently open positions.
    pub open_positions: i32,
    /// Total wins.
    pub wins: i32,
    /// Total losses.
    pub losses: i32,
    /// Win rate as percentage (0-100).
    pub win_rate_pct: f64,
    /// Total realized PNL in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub total_pnl_micros: i64,
}

/// PNL history query parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PnlHistoryQuery {
    /// Start timestamp in Unix milliseconds, inclusive.
    pub from: Option<i64>,
    /// End timestamp in Unix milliseconds, inclusive.
    pub to: Option<i64>,
}

/// Client query for scoped PNL routes.
///
/// The server parses optional strings to preserve custom query errors. This
/// transport-neutral contract exposes the integer values promised by OpenAPI.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PnlHistoryScopedQuery {
    pub from: Option<i64>,
    pub to: Option<i64>,
    pub scope: Option<String>,
}

/// PNL point for charting. Large histories may aggregate multiple raw events.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PnlEventResponse {
    /// Source product for this PNL point: `position`, `fantasy`, or `streak`.
    pub source: String,
    /// Timestamp when the event resolved, or the last event in an aggregated point, in Unix milliseconds.
    pub resolved_at_ms: i64,
    /// Position ID that resolved, or the last position represented by an aggregated point.
    pub position_id: Option<String>,
    /// Contest ID that resolved, or the last contest represented by an aggregated point.
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

/// PNL history response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PnlHistoryResponse {
    /// List of PNL events for charting.
    pub events: Vec<PnlEventResponse>,
}

/// Query for hydrated positions constrained to a supplied market set.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PositionsByMarketsQuery {
    pub market_ids: String,
    pub limit: Option<u32>,
    pub cursor: Option<String>,
}

/// Fully hydrated positions ordered newest first.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PositionsByMarketsResponse {
    pub positions: Vec<PositionDetailResponse>,
    pub next_cursor: Option<String>,
}

/// Position list query parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PositionsQuery {
    /// Filter by status: "open", "won", "lost", "voided".
    pub status: Option<String>,
    /// Sort order: "date_desc" (default), "date_asc", "pnl_desc", "pnl_asc".
    pub sort: Option<String>,
    /// Number of positions to return (default: 50, max: 100).
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 100))]
    pub limit: Option<u32>,
    /// Cursor for pagination (opaque string from previous response).
    pub cursor: Option<String>,
}

/// Canonical `status` query values for `/v1/positions`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum PositionStatusQueryParam {
    Open,
    Won,
    Lost,
    Voided,
}

/// Canonical `sort` query values for `/v1/positions`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum PositionSortQueryParam {
    DateDesc,
    DateAsc,
    PnlDesc,
    PnlAsc,
}

/// Position summary for list view.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PositionSummary {
    /// Position ID.
    pub id: String,
    /// Wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Portion of the wager funded by bonus credits, in micros. Included in
    /// `wager_micros`; subtract to get the cash principal.
    #[serde(default, with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub app_token_wager_micros: i64,
    /// Bonus credits actually returned when this position was voided. Expired
    /// credits reclaimed by the grantor are excluded; null for other states.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", nullable = true, required)
    )]
    pub refunded_app_token_micros: Option<i64>,
    /// Gross potential payout in micros (before fees).
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Realized net payout in micros after fees (null until resolved).
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", nullable = true, required)
    )]
    pub net_payout_micros: Option<i64>,
    /// Number of legs.
    pub legs_count: i16,
    /// Human-readable legs summary (e.g., "BTC↑ ETH↓").
    pub legs_summary: String,
    /// Position status: "open", "won", "lost", "pending", "cancelled", "voided".
    pub status: String,
    /// Realized PNL in micros (null if open).
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", nullable = true, required)
    )]
    pub pnl_micros: Option<i64>,
    /// Created timestamp in Unix milliseconds.
    pub created_at_ms: i64,
    /// Resolved timestamp in Unix milliseconds, null if open.
    pub resolved_at_ms: Option<i64>,
    /// True when at least one leg is a binary-event contract.
    pub has_binary_event_leg: bool,
    /// Sorted, distinct categories represented by the position's legs.
    pub market_types: Vec<MarketType>,
}

/// Positions list response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PositionsListResponse {
    /// List of positions.
    pub positions: Vec<PositionSummary>,
    /// Cursor for next page (null if no more pages).
    pub next_cursor: Option<String>,
    /// Whether the response is partial due to data integrity errors.
    pub partial: bool,
}

/// Status of a position returned by the active-position snapshot.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum ActivePositionStatus {
    Pending,
    Open,
}

/// The authenticated caller's role in an active position.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum PositionRole {
    Taker,
    Maker,
}

/// One active taker or maker position in a complete portfolio snapshot.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ActivePosition {
    /// Position ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub position_id: PositionId,
    /// Active lifecycle status.
    pub status: ActivePositionStatus,
    /// The authenticated caller's role in this position.
    pub role: PositionRole,
    /// Taker signer address when the originating order was not shielded.
    #[cfg_attr(
        feature = "openapi",
        schema(
            required,
            value_type = Option<String>,
            nullable = true,
            example = "0x1111111111111111111111111111111111111111"
        )
    )]
    pub taker_address: Option<Address>,
    /// Caller capital at risk in micros: filled wager for a taker, liability for a maker.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: u64,
    /// Portion of the wager funded by bonus credits, in micros. Included in
    /// `wager_micros`; always 0 for maker rows.
    #[serde(default, with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub app_token_wager_micros: u64,
    /// Gross potential caller payout in micros, including the caller's wager.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: u64,
    /// Canonical taker-selected legs and taker-relative outcomes.
    ///
    /// For maker rows, these describe the parlay being underwritten; the maker wins
    /// when the taker-relative parlay loses.
    pub legs: Vec<LegDetail>,
}

/// Complete snapshot of the authenticated caller's active positions.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ActivePositionsResponse {
    pub positions: Vec<ActivePosition>,
}

/// Leg detail for position views.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct LegDetail {
    /// Leg index (0-8).
    pub leg_index: i16,
    /// Longshot market ID for this leg.
    pub market_id: u64,
    /// Canonical product category for this leg's market.
    ///
    /// This is distinct from the structural price-strike/binary-event contract
    /// kind and remains optional while clients roll across the additive field.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub market_type: Option<MarketType>,
    /// Human-readable leg label when available.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,
    /// Asset being traded for price-strike legs.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub asset: Option<String>,
    /// Selection direction: "up" or "down".
    pub direction: String,
    /// Duration in seconds for price-strike legs.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_secs: Option<i32>,
    /// Leg outcome: "pending", "won", "lost", or "voided".
    pub outcome: String,
    /// Window start time in milliseconds when this is a fixed price window.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_start_ms: Option<i64>,
    /// Scheduled resolution time, milliseconds since epoch.
    pub resolution_time_ms: u64,
}

/// Position detail response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PositionDetailResponse {
    /// Position ID.
    pub id: String,
    /// Wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Portion of the wager funded by bonus credits, in micros. Included in
    /// `wager_micros`; subtract to get the cash principal.
    #[serde(default, with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub app_token_wager_micros: i64,
    /// Bonus credits actually returned when this position was voided. Expired
    /// credits reclaimed by the grantor are excluded; null for other states.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", nullable = true, required)
    )]
    pub refunded_app_token_micros: Option<i64>,
    /// Gross potential payout in micros (before fees).
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Realized net payout in micros after fees (null until resolved).
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", nullable = true, required)
    )]
    pub net_payout_micros: Option<i64>,
    /// Number of legs.
    pub legs_count: i16,
    /// Human-readable legs summary.
    pub legs_summary: String,
    /// Position status: "open", "won", "lost", "pending", "cancelled", "voided".
    pub status: String,
    /// Realized PNL in micros (null if open).
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", nullable = true, required)
    )]
    pub pnl_micros: Option<i64>,
    /// Created timestamp in Unix milliseconds.
    pub created_at_ms: i64,
    /// Resolved timestamp in Unix milliseconds, null if open.
    pub resolved_at_ms: Option<i64>,
    /// All legs with their outcomes.
    pub legs: Vec<LegDetail>,
}

/// User preferences response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PreferencesResponse {
    /// Whether notifications are enabled.
    pub notifications_enabled: bool,
    /// Quote tolerance preference for new bets.
    pub quote_tolerance: QuoteTolerancePreference,
    /// Whether anonymous mode is enabled for new bets.
    pub anonymous_mode_enabled: bool,
}

/// Quote tolerance preference.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "openapi", schema(rename_all = "snake_case"))]
pub enum QuoteTolerancePreference {
    Strict,
    Normal,
    Lenient,
}

/// Update preferences request.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct UpdatePreferencesRequest {
    /// Whether notifications are enabled (optional).
    pub notifications_enabled: Option<bool>,
    /// Quote tolerance preference for new bets (optional).
    pub quote_tolerance: Option<QuoteTolerancePreference>,
    /// Whether anonymous mode is enabled for new bets (optional).
    pub anonymous_mode_enabled: Option<bool>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use uuid::Uuid;

    #[test]
    fn active_position_round_trips_exact_money_and_typed_fields() {
        let position_id =
            PositionId::from_uuid(Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap());
        let position = ActivePosition {
            position_id,
            status: ActivePositionStatus::Open,
            role: PositionRole::Maker,
            taker_address: Some(
                "0x1111111111111111111111111111111111111111"
                    .parse()
                    .unwrap(),
            ),
            wager_micros: 9_007_199_254_740_993,
            app_token_wager_micros: 0,
            payout_micros: 9_007_199_254_741_993,
            legs: vec![LegDetail {
                leg_index: 0,
                market_id: 42,
                market_type: Some(MarketType::from(MarketType::SPORTS)),
                label: Some("Will it happen?".to_string()),
                asset: None,
                direction: "up".to_string(),
                duration_secs: None,
                outcome: "pending".to_string(),
                window_start_ms: None,
                resolution_time_ms: 1_750_000_000_000,
            }],
        };

        let json = serde_json::to_value(&position).unwrap();
        assert_eq!(json["position_id"], position_id.to_string());
        assert_eq!(json["status"], "open");
        assert_eq!(json["role"], "maker");
        assert_eq!(
            json["taker_address"],
            "0x1111111111111111111111111111111111111111"
        );
        assert_eq!(json["wager_micros"], "9007199254740993");
        assert_eq!(json["payout_micros"], "9007199254741993");
        assert_eq!(json["legs"][0]["market_type"], "sports");
        assert_eq!(json["legs"][0]["resolution_time_ms"], 1_750_000_000_000u64);

        let decoded: ActivePosition = serde_json::from_value(json).unwrap();
        assert_eq!(decoded.position_id, position_id);
        assert_eq!(decoded.status, ActivePositionStatus::Open);
        assert_eq!(decoded.role, PositionRole::Maker);
        assert_eq!(decoded.taker_address, position.taker_address);
        assert_eq!(decoded.wager_micros, 9_007_199_254_740_993);
        assert_eq!(decoded.payout_micros, 9_007_199_254_741_993);
    }
}
