//! Public market-data API request and response contracts.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(as = PriceSource))]
#[serde(rename_all = "snake_case")]
pub enum PriceSourceResponse {
    Binance,
    Polymarket,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct MarketCandlesQuery {
    pub asset: Option<String>,
    pub timeframe_secs: Option<i64>,
    pub past_slots: Option<i64>,
    pub now_ms: Option<i64>,
    pub before_ms: Option<i64>,
    pub max_points: Option<usize>,
    pub ohlc_resolution_secs: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct MarketTicksStreamQuery {
    pub assets: Option<String>,
    pub timeframe_secs: Option<i64>,
    pub since_ms: Option<i64>,
    pub since_seq: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct ExternalOddsSourceQuery {
    /// Special crypto-only query shape. `assets` combines with `timeframe_secs`
    /// and `window_start_ms`; every stored non-crypto category uses `market_ids`.
    pub assets: Option<String>,
    pub timeframe_secs: Option<i64>,
    pub window_start_ms: Option<String>,
    pub market_ids: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ChartPoint {
    pub timestamp_ms: i64,
    pub price: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct OhlcCandle {
    pub time_ms: i64,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketTickStreamEvent {
    pub asset: String,
    pub price_source: PriceSourceResponse,
    pub timestamp_ms: i64,
    pub price: f64,
    pub source_trade_id: i64,
    pub seq: u64,
    pub slot_start_ms: i64,
    pub sample_interval_ms: i64,
    pub is_synthetic: bool,
    pub emitted_at_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum MarketTickStreamErrorCode {
    PublisherSeedCursorFailed,
    PublisherIncrementalQueryFailed,
    PublisherFallbackQueryFailed,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketTickStreamErrorEvent {
    pub asset: String,
    pub price_source: PriceSourceResponse,
    pub code: MarketTickStreamErrorCode,
    pub retry_after_ms: i64,
    pub emitted_at_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct TopOfBookStreamQuery {
    pub assets: Option<String>,
    pub timeframe_secs: Option<i64>,
    pub window_start_ms: Option<String>,
    pub market_ids: Option<String>,
    pub since_seq: Option<u64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ExternalOddsSourceStatus {
    Ok,
    Partial,
    Pending,
    EmptyBook,
    /// Public JSON value: `missing_tokens`.
    #[serde(rename = "missing_tokens")]
    MissingBinding,
    UpstreamError,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ExternalOddsSourceKind {
    /// Public JSON value: `clob_ws`.
    #[serde(rename = "clob_ws")]
    PolymarketWs,
    KalshiRest,
    ManifoldRest,
    Cache,
    None,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ExternalOddsSourceRow {
    pub key: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub asset: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub timeframe_secs: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_start_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_end_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_id: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_market_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub yes_ask_cents: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub no_ask_cents: Option<f64>,
    pub status: ExternalOddsSourceStatus,
    pub updated_at_ms: i64,
    pub source: ExternalOddsSourceKind,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ExternalOddsSourceResponse {
    pub rows: Vec<ExternalOddsSourceRow>,
}

/// Top-of-book SSE payload with a monotonic replay sequence.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct TopOfBookStreamEvent {
    pub key: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub asset: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub timeframe_secs: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_start_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_end_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub market_id: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_market_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub yes_ask_cents: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub no_ask_cents: Option<f64>,
    pub status: ExternalOddsSourceStatus,
    pub source: ExternalOddsSourceKind,
    pub updated_at_ms: i64,
    pub seq: u64,
    pub emitted_at_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum TopOfBookStreamErrorCode {
    SubscriberDisconnected,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct TopOfBookStreamErrorEvent {
    pub code: TopOfBookStreamErrorCode,
    pub retry_after_ms: i64,
    pub emitted_at_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct TopOfBookHistoryQuery {
    pub market_ids: String,
}

/// One replayed provider-book observation. Ask semantics mirror
/// [`ExternalOddsSourceRow`] so clients derive implied probability from
/// history with the same rules as the live snapshot and stream.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct TopOfBookHistoryPoint {
    pub timestamp_ms: i64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub yes_ask_cents: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub no_ask_cents: Option<f64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum TopOfBookHistoryStatus {
    Ok,
    /// The market has no provider binding that serves replayable history.
    Unsupported,
    UpstreamError,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct TopOfBookHistoryMarket {
    pub market_id: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_market_id: Option<String>,
    pub status: TopOfBookHistoryStatus,
    /// Ascending by `timestamp_ms`; buckets without provider activity are
    /// omitted rather than zero-filled.
    pub points: Vec<TopOfBookHistoryPoint>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct TopOfBookHistoryResponse {
    /// Provider sampling bucket for `points`. Coarse by contract: history
    /// replays provider candles, not tick-level book updates.
    pub bucket_secs: i64,
    /// Inclusive lower bound of the served history window.
    pub window_start_ms: i64,
    pub generated_at_ms: i64,
    pub markets: Vec<TopOfBookHistoryMarket>,
}

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketCandlesResponse {
    pub asset: String,
    pub timeframe_secs: i64,
    pub past_slots: i64,
    pub requested_before_ms: Option<i64>,
    pub next_before_ms: Option<i64>,
    pub has_more_before: bool,
    pub store_ready: bool,
    pub timescale_enabled: bool,
    pub cagg_enabled: bool,
    pub source: String,
    pub price_source: PriceSourceResponse,
    pub generated_at_ms: i64,
    pub slot_ms: i64,
    pub candle_bucket_ms: i64,
    pub current_slot_start_ms: i64,
    pub current_slot_end_ms: i64,
    pub domain_start_ms: i64,
    pub domain_end_ms: i64,
    pub latest_price: Option<f64>,
    pub latest_price_timestamp_ms: Option<i64>,
    pub candle_count: usize,
    pub points: Vec<ChartPoint>,
    pub ohlc: Vec<OhlcCandle>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct ReferencePriceQuery {
    pub asset: Option<String>,
    pub timeframe_secs: Option<i64>,
}

/// State of the locally resolved current-slot open from stored `open_strike_micros`; the API does not infer or expose external source provenance.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SourceStatus {
    /// A current-slot market exists and its stored open strike is available.
    Ok,
    /// A current-slot market exists locally, but its open strike has not been
    /// persisted yet.
    Pending,
    /// No current-slot market exists, or the slot cannot be resolved locally.
    Unavailable,
}

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ReferencePriceResponse {
    /// Asset symbol after shared parsing/defaulting.
    pub asset: String,
    /// Requested market window in seconds.
    pub timeframe_secs: i64,
    /// Current-slot boundary resolved locally for this request.
    pub current_slot_start_ms: i64,
    /// Stored current-slot open in dollars. `null` while the current slot is
    /// still `pending` or `unavailable`.
    pub window_open_price: Option<f64>,
    /// Contract state for the local current-slot open lookup.
    pub source_status: SourceStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::IntoParams))]
#[serde(deny_unknown_fields)]
pub struct WindowResultsQuery {
    pub timeframe_secs: Option<i64>,
    pub past_windows: Option<i64>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum WindowDirection {
    Up,
    Down,
}

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct WindowAssetResult {
    pub asset: String,
    pub open_price: f64,
    pub close_price: f64,
    pub direction: WindowDirection,
    pub price_source: PriceSourceResponse,
}

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct WindowResult {
    pub slot_start_ms: i64,
    pub slot_end_ms: i64,
    pub assets: Vec<WindowAssetResult>,
}

#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct WindowResultsResponse {
    pub timeframe_secs: i64,
    pub past_windows: i64,
    pub price_source: PriceSourceResponse,
    pub generated_at_ms: i64,
    pub windows: Vec<WindowResult>,
}

#[cfg(test)]
mod tests {
    use super::{ExternalOddsSourceKind, ExternalOddsSourceStatus};

    #[test]
    fn external_odds_source_keeps_deployed_wire_values() {
        assert_eq!(
            serde_json::to_value(ExternalOddsSourceKind::PolymarketWs).unwrap(),
            serde_json::json!("clob_ws")
        );
        assert_eq!(
            serde_json::to_value(ExternalOddsSourceStatus::MissingBinding).unwrap(),
            serde_json::json!("missing_tokens")
        );
    }
}
