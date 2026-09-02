//! Market-maker WebSocket protocol messages.

use serde::{Deserialize, Serialize};
use std::fmt;
use std::sync::Arc;

use crate::types::Asset;

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
#[derive(Clone, Serialize, Deserialize)]
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

impl fmt::Debug for ClientMessage {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Auth => f.write_str("Auth"),
            Self::AuthResponse { wallet_address, .. } => f
                .debug_struct("AuthResponse")
                .field("wallet_address", wallet_address)
                .field("signature", &"<redacted>")
                .finish(),
            Self::Quote { data } => f.debug_struct("Quote").field("data", data).finish(),
            Self::Pong => f.write_str("Pong"),
            Self::Subscribe {
                protocol_version,
                subscriptions,
            } => f
                .debug_struct("Subscribe")
                .field("protocol_version", protocol_version)
                .field("subscriptions", subscriptions)
                .finish(),
        }
    }
}

/// Server-to-client WebSocket messages used by market makers.
#[derive(Clone, Serialize, Deserialize)]
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

impl fmt::Debug for ServerMessage {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::AuthChallenge {
                challenge_id,
                timestamp_ms,
            } => f
                .debug_struct("AuthChallenge")
                .field("challenge_id", challenge_id)
                .field("timestamp_ms", timestamp_ms)
                .finish(),
            Self::AuthResult { success, error, .. } => f
                .debug_struct("AuthResult")
                .field("success", success)
                .field("error", error)
                .field("session_token", &"<redacted>")
                .finish(),
            Self::Rfq { data } => f.debug_struct("Rfq").field("data", data).finish(),
            Self::Subscribed { protocol_version } => f
                .debug_struct("Subscribed")
                .field("protocol_version", protocol_version)
                .finish(),
            Self::QuoteAck {
                request_id,
                quote_id,
                client_quote_id,
                accepted,
                error,
            } => f
                .debug_struct("QuoteAck")
                .field("request_id", request_id)
                .field("quote_id", quote_id)
                .field("client_quote_id", client_quote_id)
                .field("accepted", accepted)
                .field("error", error)
                .finish(),
            Self::QuoteResult {
                request_id,
                quote_id,
                client_quote_id,
                status,
                position_id,
                fill_amount,
                fill_odds,
                filled_at_ms,
                reason,
            } => f
                .debug_struct("QuoteResult")
                .field("request_id", request_id)
                .field("quote_id", quote_id)
                .field("client_quote_id", client_quote_id)
                .field("status", status)
                .field("position_id", position_id)
                .field("fill_amount", fill_amount)
                .field("fill_odds", fill_odds)
                .field("filled_at_ms", filled_at_ms)
                .field("reason", reason)
                .finish(),
            Self::Ping { timestamp } => f
                .debug_struct("Ping")
                .field("timestamp", timestamp)
                .finish(),
            Self::Error { code, message } => f
                .debug_struct("Error")
                .field("code", code)
                .field("message", message)
                .finish(),
            Self::RateLimit { retry_after_ms } => f
                .debug_struct("RateLimit")
                .field("retry_after_ms", retry_after_ms)
                .finish(),
        }
    }
}
