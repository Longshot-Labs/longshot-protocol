//! Activity feed request and response types.

use serde::{Deserialize, Serialize};

use super::position_identity::PrimaryLegIdentityResponse;

/// Feed filter mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FeedFilter {
    /// All activity: recent bets placed + recent resolved events.
    All,
    /// Only resolved feed events.
    Resolved,
    /// New bets plus winning resolutions.
    Golden,
    /// Only won positions.
    Won,
}

/// Raw query parameters for `GET /v1/feed`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct FeedRawQuery {
    pub filter: Option<String>,
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 50))]
    pub limit: Option<u32>,
    pub cursor: Option<String>,
    /// Comma-separated list of known Longshot binary-event market IDs.
    /// When present, the feed is restricted to positions that include at least
    /// one leg on one of the listed markets. Used by the per-event
    /// event activity feed; the set can come from child markets of one provider
    /// event, but the filter itself is category-agnostic.
    pub binary_event_market_ids: Option<String>,
}

/// A single activity feed event.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FeedEventResponse {
    /// Event type: `"place_bet"`, `"won"`, or `"lost"`.
    pub event_type: String,
    /// Position ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub position_id: String,
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
    /// User display name (falls back to handle or `"Anonymous"`).
    pub user_display_name: String,
    /// User handle for profile linking.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user_handle: Option<String>,
    /// Avatar seed for deterministic avatar generation.
    pub user_avatar_seed: i32,
    /// Twitter/X avatar URL (if linked).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user_avatar_url: Option<String>,
    /// Wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Multiplier in basis points (`payout / wager * 10_000`).
    pub multiplier_bps: i64,
    /// Potential (or realized) payout in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Event timestamp in Unix milliseconds.
    pub event_at_ms: i64,
}

/// Feed endpoint response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FeedResponse {
    pub events: Vec<FeedEventResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

/// One price leg attached to a feed event.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FeedLegResponse {
    pub asset: String,
    pub direction: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub window_start_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_secs: Option<i32>,
}

/// Feed event enriched with its price legs.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FeedEventWithLegsResponse {
    #[serde(flatten)]
    #[cfg_attr(feature = "openapi", schema(inline))]
    pub event: FeedEventResponse,
    /// Position-level asset identity. Present only when every leg is a price
    /// leg on the same asset; mixed and binary-event positions serialize null.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub primary_asset: Option<String>,
    /// True when any position leg is a binary event. Clients must use this
    /// position fact instead of classifying from the representative leg.
    pub has_binary_event_leg: bool,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub legs: Vec<FeedLegResponse>,
}

/// Feed response with leg-enriched events.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct FeedWithLegsResponse {
    pub events: Vec<FeedEventWithLegsResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::{FeedEventResponse, FeedEventWithLegsResponse};

    #[test]
    fn empty_feed_legs_round_trip_when_omitted() {
        let response = FeedEventWithLegsResponse {
            event: FeedEventResponse {
                event_type: "place_bet".to_owned(),
                position_id: "00000000-0000-0000-0000-000000000001".to_owned(),
                market: "test".to_owned(),
                duration_label: None,
                primary_leg: None,
                legs_count: 1,
                user_display_name: "Anonymous".to_owned(),
                user_handle: None,
                user_avatar_seed: 0,
                user_avatar_url: None,
                wager_micros: 500_000,
                multiplier_bps: 20_000,
                payout_micros: 1_000_000,
                event_at_ms: 1,
            },
            primary_asset: None,
            has_binary_event_leg: false,
            legs: Vec::new(),
        };

        let value = serde_json::to_value(response).expect("feed response serializes");
        assert!(value.get("legs").is_none());

        let decoded: FeedEventWithLegsResponse =
            serde_json::from_value(value).expect("omitted legs default to an empty list");
        assert!(decoded.legs.is_empty());
    }
}
