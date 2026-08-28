//! Market-maker WebSocket protocol messages.

use serde::{Deserialize, Serialize};
use std::sync::Arc;

use crate::types::{Asset, MarketId, MarketType, RequestId};

/// Terminal quote-result status sent to market makers over the WebSocket.
///
/// JSON values are `filled`, `not_filled`, `rejected`, and `selected_failed`.
/// `filled` creates a position, `not_filled` leaves the quote unfilled,
/// `rejected` fails quote validation, and `selected_failed` means the selected
/// quote could not be completed.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum QuoteResultStatus {
    Filled,
    NotFilled,
    Rejected,
    SelectedFailed,
}

/// A closed reason reported when a market maker intentionally declines an RFQ.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum QuoteDeclineReason {
    /// The sports provider does not support pricing this leg combination.
    SportsCombinationUnsupported,
}

/// RFQ subscription filter for a market-maker WebSocket connection.
///
/// The JSON shape is tagged by `type`; price-strike subscriptions carry the asset in
/// the `asset` content field.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", content = "asset", rename_all = "snake_case")]
pub enum RfqSubscription {
    /// Receive every RFQ.
    All,
    /// Receive RFQs containing at least one binary-event leg.
    BinaryEvent,
    /// Receive RFQs containing at least one price-strike leg for the asset.
    PriceStrike(Asset),
}

/// Client-to-server WebSocket messages used by market makers.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type")]
pub enum ClientMessage {
    /// Authentication request.
    #[serde(rename = "auth")]
    Auth,
    /// Authentication response for the server-issued challenge.
    #[serde(rename = "auth_response")]
    AuthResponse {
        /// Registered wallet address.
        wallet_address: String,
        /// Challenge signature encoded as hex.
        signature: String,
    },
    /// Quote submission. `data` is a base64-encoded `QuoteResponse`.
    #[serde(rename = "quote")]
    Quote {
        /// Quote data (binary, base64 encoded).
        data: String,
    },
    /// Explicitly decline an RFQ without fabricating a quote.
    #[serde(rename = "quote_decline")]
    QuoteDecline {
        /// RFQ request being declined.
        request_id: RequestId,
        /// Machine-readable decline reason.
        reason: QuoteDeclineReason,
    },
    /// Pong response to a server heartbeat.
    #[serde(rename = "pong")]
    Pong,
    /// Subscription update.
    #[serde(rename = "subscribe")]
    Subscribe {
        /// RFQ binary protocol understood by the client.
        protocol_version: u8,
        /// RFQ subscription filters to add to this connection.
        subscriptions: Vec<RfqSubscription>,
    },
}

/// Interpolation shape for a scheduled fair-value decay.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum MarketFairValueDecayType {
    /// Straight-line interpolation from the start odds to the end odds.
    Linear,
    /// Theta-style: the distance to the end odds shrinks with the square root
    /// of the window fraction remaining, the shape of at-the-money option
    /// time-value erosion (slow far out, accelerating into the end).
    Curved,
}

/// Longest window a single admin confirmation may schedule. A schedule quotes
/// unattended between confirmations, so it must not outlive plausible review.
pub const MAX_DECAY_WINDOW_MS: u64 = 30 * 24 * 60 * 60 * 1_000;

/// Shortest window a schedule may span. Below this the glide degenerates into a
/// step that can land inside one quote's evaluate-to-send gap, invisible to the
/// revision fence because the revision never moves.
pub const MIN_DECAY_WINDOW_MS: u64 = 60 * 1_000;

/// Admin-scheduled decay from a start odds to an end odds over a time window.
///
/// Unknown fields are accepted on purpose: this type also rides the
/// server-to-bot `market_fair_values` frame, where a bot on an older build must
/// ignore fields added later rather than reject the whole snapshot.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketFairValueDecay {
    /// Window start in Unix milliseconds; the fair value equals `start_odds_bps` here.
    #[cfg_attr(feature = "openapi", schema(minimum = 1))]
    pub start_ms: u64,
    /// Fair YES probability at the window start, in basis points.
    #[cfg_attr(feature = "openapi", schema(minimum = 0, maximum = 10000))]
    pub start_odds_bps: u16,
    /// Window end in Unix milliseconds; must be after `start_ms` by at least
    /// `MIN_DECAY_WINDOW_MS` and at most `MAX_DECAY_WINDOW_MS`.
    pub end_ms: u64,
    /// Fair YES probability at and after the window end, in basis points.
    #[cfg_attr(feature = "openapi", schema(minimum = 0, maximum = 10000))]
    pub end_odds_bps: u16,
    /// Interpolation shape between the start and end odds.
    pub decay_type: MarketFairValueDecayType,
}

impl MarketFairValueDecay {
    /// Checks the schedule invariants, naming the offending field on error.
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.start_odds_bps > 10_000 {
            return Err("decay.start_odds_bps");
        }
        if self.end_odds_bps > 10_000 {
            return Err("decay.end_odds_bps");
        }
        if self.start_ms == 0 {
            return Err("decay.start_ms");
        }
        let span_ms = self.end_ms.saturating_sub(self.start_ms);
        if !(MIN_DECAY_WINDOW_MS..=MAX_DECAY_WINDOW_MS).contains(&span_ms)
            || i64::try_from(self.end_ms).is_err()
        {
            return Err("decay.end_ms");
        }
        Ok(())
    }
}

/// Authoritative fair value and quote spread for one binary-event market.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketFairValue {
    /// Longshot market ID.
    pub market_id: MarketId,
    /// Fair probability for YES, in basis points.
    pub yes_fair_value_bps: u16,
    /// Full bid-ask spread, in whole cents.
    pub spread_cents: u16,
    /// Backend market category.
    pub market_type: MarketType,
    /// Market resolution time in Unix milliseconds.
    pub resolution_time_ms: u64,
    /// Monotonic row revision.
    pub revision: i64,
    /// Durable update time in Unix milliseconds.
    pub updated_at_ms: i64,
    /// Optional scheduled decay. Inside the window it overrides
    /// `yes_fair_value_bps`; before the window the static value applies.
    pub decay: Option<MarketFairValueDecay>,
}

/// Server-to-client WebSocket messages used by market makers.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type")]
pub enum ServerMessage {
    /// Authentication challenge.
    #[serde(rename = "auth_challenge")]
    AuthChallenge {
        /// Server-generated canonical lowercase UUIDv4.
        challenge_id: String,
        /// Server timestamp in Unix milliseconds.
        timestamp_ms: u64,
    },
    /// Authentication result.
    #[serde(rename = "auth_result")]
    AuthResult {
        /// Success flag.
        success: bool,
        /// Error message when authentication failed.
        error: Option<String>,
        /// Session token when authentication succeeded.
        session_token: Option<String>,
    },
    /// RFQ broadcast. `data` is a base64-encoded `BroadcastRfqRequest`.
    #[serde(rename = "rfq")]
    Rfq {
        /// RFQ data (binary, base64 encoded).
        data: Arc<String>,
    },
    /// Current or updated market fair values.
    #[serde(rename = "market_fair_values")]
    MarketFairValues {
        /// Fair-value rows.
        values: Vec<MarketFairValue>,
    },
    /// Subscription update accepted.
    #[serde(rename = "subscribed")]
    Subscribed {
        /// RFQ binary protocol selected for this session.
        protocol_version: u8,
    },
    /// Quote acknowledgment.
    #[serde(rename = "quote_ack")]
    QuoteAck {
        /// Request ID.
        request_id: String,
        /// Quote ID.
        quote_id: String,
        /// Maker-supplied quote correlation ID, when present in `QuoteResponse`.
        client_quote_id: Option<String>,
        /// True when the quote was accepted for an active RFQ session.
        accepted: bool,
        /// Error message when rejected.
        error: Option<String>,
    },
    /// Terminal quote result after RFQ completion.
    #[serde(rename = "quote_result")]
    QuoteResult {
        /// Original request ID.
        request_id: String,
        /// Quote ID whose terminal result is being reported.
        quote_id: String,
        /// Maker-supplied quote correlation ID, when present in `QuoteResponse`.
        client_quote_id: Option<String>,
        /// Terminal status.
        status: QuoteResultStatus,
        /// Position ID created for filled quotes.
        position_id: Option<String>,
        /// Amount filled from this quote (micro-units as string).
        fill_amount: Option<String>,
        /// Odds at which the fill occurred.
        fill_odds: Option<u32>,
        /// Timestamp when fill occurred (ms since epoch).
        filled_at_ms: Option<u64>,
        /// Terminal reason for non-filled results.
        reason: Option<String>,
    },
    /// Ping request.
    #[serde(rename = "ping")]
    Ping {
        /// Server timestamp.
        timestamp: u64,
    },
    /// Error message.
    #[serde(rename = "error")]
    Error {
        /// Error code.
        code: String,
        /// Error message.
        message: String,
    },
    /// Rate limit notification.
    #[serde(rename = "rate_limit")]
    RateLimit {
        /// Retry after (ms).
        retry_after_ms: u64,
    },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decay_validation_names_the_offending_field() {
        let valid = MarketFairValueDecay {
            start_ms: 1_000,
            start_odds_bps: 8_000,
            end_ms: 1_000 + MIN_DECAY_WINDOW_MS,
            end_odds_bps: 2_000,
            decay_type: MarketFairValueDecayType::Linear,
        };
        let field = |mutate: fn(&mut MarketFairValueDecay)| {
            let mut decay = valid;
            mutate(&mut decay);
            decay.validate()
        };
        assert_eq!(valid.validate(), Ok(()));
        assert_eq!(
            field(|d| d.start_odds_bps = 10_001),
            Err("decay.start_odds_bps")
        );
        assert_eq!(
            field(|d| d.end_odds_bps = 10_001),
            Err("decay.end_odds_bps")
        );
        assert_eq!(field(|d| d.start_ms = 0), Err("decay.start_ms"));
        assert_eq!(field(|d| d.end_ms = d.start_ms), Err("decay.end_ms"));
        // A window shorter than the minimum is a step, not a glide.
        assert_eq!(
            field(|d| d.end_ms = d.start_ms + MIN_DECAY_WINDOW_MS - 1),
            Err("decay.end_ms")
        );
        assert_eq!(
            field(|d| d.end_ms = d.start_ms + MAX_DECAY_WINDOW_MS),
            Ok(())
        );
        assert_eq!(
            field(|d| d.end_ms = d.start_ms + MAX_DECAY_WINDOW_MS + 1),
            Err("decay.end_ms")
        );
        assert_eq!(field(|d| d.end_ms = u64::MAX), Err("decay.end_ms"));
    }

    #[test]
    fn market_fair_values_round_trip() {
        let expected_values = vec![MarketFairValue {
            market_id: MarketId::new(7),
            yes_fair_value_bps: 6_250,
            spread_cents: 4,
            market_type: MarketType::from("culture"),
            resolution_time_ms: 1_800_000_100_000,
            revision: 3,
            updated_at_ms: 1_800_000_000_000,
            decay: Some(MarketFairValueDecay {
                start_ms: 1_800_000_000_000,
                start_odds_bps: 8_000,
                end_ms: 1_800_000_100_000,
                end_odds_bps: 2_000,
                decay_type: MarketFairValueDecayType::Curved,
            }),
        }];
        let message = ServerMessage::MarketFairValues {
            values: expected_values.clone(),
        };
        let json = serde_json::to_value(&message).unwrap();

        assert_eq!(
            json,
            serde_json::json!({
                "type": "market_fair_values",
                "values": [{
                    "market_id": 7,
                    "yes_fair_value_bps": 6250,
                    "spread_cents": 4,
                    "market_type": "culture",
                    "resolution_time_ms": 1800000100000_u64,
                    "revision": 3,
                    "updated_at_ms": 1800000000000_i64,
                    "decay": {
                        "start_ms": 1800000000000_u64,
                        "start_odds_bps": 8000,
                        "end_ms": 1800000100000_u64,
                        "end_odds_bps": 2000,
                        "decay_type": "curved"
                    }
                }]
            })
        );
        let ServerMessage::MarketFairValues { values } =
            serde_json::from_value(json.clone()).unwrap()
        else {
            panic!("expected market fair values");
        };
        assert_eq!(values, expected_values);

        // Payloads produced before the decay schedule existed omit the field.
        let mut legacy = json;
        legacy["values"][0].as_object_mut().unwrap().remove("decay");
        let ServerMessage::MarketFairValues { values } = serde_json::from_value(legacy).unwrap()
        else {
            panic!("expected market fair values");
        };
        assert_eq!(values[0].decay, None);
    }
}
