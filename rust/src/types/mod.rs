//! Shared public Longshot primitive and domain types.
//!
//! Higher-level HTTP contracts live under [`crate::api`]. Market-maker
//! WebSocket messages live under [`crate::ws`].

// EVM wallet/account address type used in request and session contracts.
pub use alloy_primitives::Address;

pub mod ids;
pub mod market;
pub mod primitives;
pub mod rfq;

pub use ids::{ClientQuoteId, ContestId, MarketId, PositionId, QuoteId, RequestId, UserId};
pub use market::{MarketStatus, MarketType, Outcome, TradingChannel};
pub use primitives::{
    Amount, Asset, Direction, Duration, MathError, Odds, OrderType, Timestamp, UserTier,
    MIN_BET_MICROS,
};
pub use rfq::{
    BroadcastRfqRequest, QuoteResponse, RfqLeg, RfqLegType, RfqLegWire, RfqLegWireDecodeError,
    TakerMetadata, MAX_RFQ_LEGS, RFQ_LEG_TYPE_BINARY_EVENT_TAG, RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
    RFQ_PROTOCOL_VERSION,
};
