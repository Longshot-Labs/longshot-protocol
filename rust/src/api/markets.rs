//! Public market API request and response contracts.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::types::{MarketId, MarketStatus, MarketType, Outcome, TradingChannel};

/// Raw query parameters for the bounded `GET /v1/markets` catalog.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PublicMarketsRawQuery {
    /// Optional open category slug.
    pub market_type: Option<MarketType>,
    /// Optional source-adapter filter.
    pub source: Option<String>,
    /// Exact event identity (`source.event_id`); combine with `source` to scope one adapter.
    pub source_event_id: Option<String>,
    /// Optional trading-surface filter.
    pub trading_channel: Option<TradingChannel>,
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 500))]
    pub limit: Option<u32>,
    pub cursor: Option<String>,
    /// Market status filter, sent as one comma-separated `statuses` query value.
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        with = "status_list_query"
    )]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>))]
    pub statuses: Option<Vec<MarketStatus>>,
}

/// (De)serializes `Option<Vec<MarketStatus>>` as one comma-separated query
/// value, since form encoding cannot carry repeated keys through every client.
mod status_list_query {
    use serde::de::IntoDeserializer;
    use serde::{Deserialize, Deserializer, Serializer};

    use crate::types::MarketStatus;

    pub fn serialize<S: Serializer>(
        statuses: &Option<Vec<MarketStatus>>,
        serializer: S,
    ) -> Result<S::Ok, S::Error> {
        match statuses {
            None => serializer.serialize_none(),
            Some(statuses) => {
                let joined = statuses
                    .iter()
                    .map(|status| status.as_query_token())
                    .collect::<Vec<_>>()
                    .join(",");
                serializer.serialize_some(&joined)
            }
        }
    }

    pub fn deserialize<'de, D: Deserializer<'de>>(
        deserializer: D,
    ) -> Result<Option<Vec<MarketStatus>>, D::Error> {
        let Some(raw) = Option::<String>::deserialize(deserializer)? else {
            return Ok(None);
        };
        let statuses = raw
            .split(',')
            .map(str::trim)
            .filter(|token| !token.is_empty())
            .map(|token| MarketStatus::deserialize(token.into_deserializer()))
            .collect::<Result<Vec<_>, _>>()?;
        Ok((!statuses.is_empty()).then_some(statuses))
    }
}

/// Canonical source identity and adapter-owned attributes for an event contract.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct EventMarketSource {
    /// Adapter identity such as `kalshi` or `manual`.
    pub source: String,
    /// Provider event identity, when the source groups contracts into events.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub event_id: Option<String>,
    /// Provider market identities that resolve this canonical Longshot market.
    pub source_market_ids: Vec<String>,
    /// Source-specific metadata that cannot affect contract behavior.
    #[serde(default)]
    pub attributes: BTreeMap<String, serde_json::Value>,
}

/// Price-strike market returned by unified market reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PriceStrikeMarket {
    pub id: MarketId,
    pub market_type: MarketType,
    pub trading_channels: Vec<TradingChannel>,
    pub name: String,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub description: Option<String>,
    pub status: MarketStatus,
    pub tradeable: bool,
    pub category_tags: Vec<String>,
    /// Hard cutoff for accepting new bets, milliseconds since epoch.
    pub betting_closes_at_ms: u64,
    /// Scheduled resolution time for the bounded price window.
    pub resolution_time_ms: u64,
    /// Strike price captured at market open.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub open_strike_micros: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_outcome: Option<Outcome>,
    pub created_at_ms: u64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub opened_at_ms: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
}

/// Event market returned by unified market reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct EventMarket {
    pub id: MarketId,
    pub market_type: MarketType,
    pub trading_channels: Vec<TradingChannel>,
    /// Stable chat room for the source event shared by every market in that event.
    pub chat_id: String,
    pub name: String,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub description: Option<String>,
    /// Canonical rules used to resolve this binary-event contract.
    /// The serde default keeps additive rollouts readable against an older API.
    #[serde(default)]
    pub resolution_rules: String,
    pub status: MarketStatus,
    pub tradeable: bool,
    pub category_tags: Vec<String>,
    /// Scheduled time trading may open. This is distinct from actual lifecycle `opened_at_ms`.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub opens_at_ms: Option<u64>,
    /// Provider event start. This preserves source chronology and is distinct from Longshot's
    /// lifecycle `opens_at_ms`.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub source_starts_at_ms: Option<u64>,
    /// Hard cutoff for accepting new bets.
    pub betting_closes_at_ms: u64,
    /// End of the live event-observation window.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub live_ends_at_ms: Option<u64>,
    /// Scheduled resolution time for the event.
    pub resolution_time_ms: u64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_outcome: Option<Outcome>,
    pub created_at_ms: u64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub opened_at_ms: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_at_ms: Option<u64>,
    pub source: EventMarketSource,
    /// Configured live probability for manual event markets, in basis points.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub manual_probability_bps: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
}

/// Rich public market detail selected by its strict specification shape.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(untagged)]
pub enum PublicMarket {
    // Event must remain first: its required `source` field is the structural
    // selector used by generated clients for this untagged union.
    Event(EventMarket),
    PriceStrike(PriceStrikeMarket),
}

impl PublicMarket {
    pub fn market_type(&self) -> &MarketType {
        match self {
            Self::Event(market) => &market.market_type,
            Self::PriceStrike(market) => &market.market_type,
        }
    }
}

/// Response returned by `GET /v1/markets/{id}`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PublicMarketResponse {
    pub market: PublicMarket,
}

/// Bounded page returned by `GET /v1/markets`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PublicMarketsResponse {
    pub markets: Vec<PublicMarket>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub next_cursor: Option<String>,
}

/// Single price-market metadata entry returned by bounded lookup endpoints.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketMetadataEntry {
    pub market_id: u64,
    pub asset: String,
    pub duration_secs: u32,
    pub start_at_ms: i64,
    pub betting_closes_at_ms: i64,
}

/// Response for bounded price-market lookup endpoints.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketLookupResponse {
    pub market: MarketMetadataEntry,
}

/// Client query parameters for `GET /v1/price-markets/lookup`.
///
/// Server handlers retain optional string extractors to produce precise 400s;
/// clients instead get the route's required semantic types here.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct MarketLookupQuery {
    pub asset: String,
    pub duration_secs: u32,
    pub window_start_ms: u64,
}

/// Client query parameters for `GET /v1/price-markets/current`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct MarketCurrentQuery {
    pub asset: String,
    pub duration_secs: u32,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn event_json(market_type: &str) -> serde_json::Value {
        serde_json::json!({
            "id": 42,
            "market_type": market_type,
            "trading_channels": ["rfq", "contest"],
            "chat_id": "9187ca06-569d-5bc7-8aa1-cb4dd2da71ac",
            "name": "Lakers vs Celtics",
            "description": null,
            "status": "OPEN",
            "tradeable": true,
            "category_tags": ["nba"],
            "opens_at_ms": null,
            "source_starts_at_ms": 1_700_000_500_000u64,
            "betting_closes_at_ms": 1_700_000_000_000u64,
            "live_ends_at_ms": 1_700_003_600_000u64,
            "resolution_time_ms": 1_700_003_600_000u64,
            "resolved_outcome": null,
            "created_at_ms": 1_699_999_000_000u64,
            "opened_at_ms": 1_699_999_100_000u64,
            "resolved_at_ms": null,
            "source": {
                "source": "kalshi",
                "event_id": "KXNBAGAME-26OCT20LALBOS",
                "source_market_ids": ["KXNBAGAME-26OCT20LALBOS-LAL"],
                "attributes": {"sport": "basketball", "league": "nba"}
            },
            "manual_probability_bps": null
        })
    }

    #[test]
    fn public_market_preserves_unknown_category() {
        let future = event_json("future_category");
        let parsed: PublicMarket = serde_json::from_value(future).unwrap();
        assert_eq!(parsed.market_type().as_str(), "future_category");
    }

    #[test]
    fn sports_event_can_advertise_rfq_and_contest_channels() {
        let parsed: PublicMarket = serde_json::from_value(event_json("sports")).unwrap();
        let PublicMarket::Event(market) = parsed else {
            panic!("expected event market");
        };
        assert_eq!(
            market.trading_channels,
            vec![TradingChannel::Rfq, TradingChannel::Contest]
        );
        assert_eq!(market.chat_id, "9187ca06-569d-5bc7-8aa1-cb4dd2da71ac");
    }

    #[test]
    fn provider_start_is_distinct_from_lifecycle_open() {
        let parsed: PublicMarket = serde_json::from_value(event_json("mentions")).unwrap();
        let PublicMarket::Event(market) = parsed else {
            panic!("expected event market");
        };
        assert_eq!(market.opens_at_ms, None);
        assert_eq!(market.source_starts_at_ms, Some(1_700_000_500_000));
    }

    #[test]
    fn public_markets_query_statuses_round_trip_as_csv() {
        let query = PublicMarketsRawQuery {
            market_type: Some(MarketType::from("sports")),
            source: Some("kalshi".to_string()),
            source_event_id: Some("KXGAME-1".to_string()),
            trading_channel: Some(TradingChannel::Rfq),
            limit: Some(100),
            cursor: None,
            statuses: Some(vec![MarketStatus::Pending, MarketStatus::Open]),
        };
        let value = serde_json::to_value(&query).unwrap();
        assert_eq!(value["statuses"], "PENDING,OPEN");
        let parsed: PublicMarketsRawQuery = serde_json::from_value(value).unwrap();
        assert_eq!(
            parsed.market_type.as_ref().map(MarketType::as_str),
            Some("sports")
        );
        assert_eq!(parsed.statuses, query.statuses);
    }
}
