use alloy_primitives::Signature;
use static_assertions::const_assert_eq;

use super::{
    Address, Amount, Asset, ClientQuoteId, Direction, Duration, Odds, OrderType, RequestId,
    Timestamp, UserTier,
};

/// Maximum RFQ leg count encoded by the fixed-size market-maker wire protocol.
///
/// A broadcast RFQ carries up to nine legs.
pub const MAX_RFQ_LEGS: usize = 9;

/// Current market-maker RFQ binary protocol version.
pub const RFQ_PROTOCOL_VERSION: u8 = 2;
pub const RFQ_LEG_TYPE_PRICE_STRIKE_TAG: u8 = 0;
/// Tag `1` belonged to the removed Mention engine and is deliberately retired.
/// Reusing it would let version-1 clients silently interpret Sports as Politics.
pub const RFQ_LEG_TYPE_BINARY_EVENT_TAG: u8 = 2;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RfqLegType {
    PriceStrike {
        asset: Asset,
        window: Duration,
    },
    /// Category is intentionally absent from RFQ bytes: it is display metadata,
    /// while this discriminator selects only stable quoting/settlement behavior.
    BinaryEvent,
}

impl Default for RfqLegType {
    fn default() -> Self {
        Self::PriceStrike {
            asset: Asset::BTC,
            window: Duration::FIVE_MINUTES,
        }
    }
}

impl RfqLegType {
    #[inline]
    pub const fn type_tag(self) -> u8 {
        match self {
            Self::PriceStrike { .. } => RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
            Self::BinaryEvent => RFQ_LEG_TYPE_BINARY_EVENT_TAG,
        }
    }

    #[inline]
    pub const fn is_price_strike(self) -> bool {
        matches!(self, Self::PriceStrike { .. })
    }

    #[inline]
    pub const fn is_binary_event(self) -> bool {
        matches!(self, Self::BinaryEvent)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RfqLeg {
    pub market_id: u64,
    pub start_at_ms: u64,
    pub leg_type: RfqLegType,
    pub direction: Direction,
    pub leg_index: u8,
}

impl Default for RfqLeg {
    fn default() -> Self {
        Self {
            market_id: 0,
            start_at_ms: 0,
            leg_type: RfqLegType::default(),
            direction: Direction::Up,
            leg_index: 0,
        }
    }
}

impl RfqLeg {
    #[inline]
    pub fn new_price_strike<M, A, D>(
        market_id: M,
        start_at_ms: u64,
        asset: A,
        direction: D,
        window: Duration,
        leg_index: u8,
    ) -> Self
    where
        M: Into<u64>,
        A: Into<Asset>,
        D: Into<Direction>,
    {
        Self {
            market_id: market_id.into(),
            start_at_ms,
            leg_type: RfqLegType::PriceStrike {
                asset: asset.into(),
                window,
            },
            direction: direction.into(),
            leg_index,
        }
    }

    #[inline]
    pub fn new_binary_event<M, D>(
        market_id: M,
        start_at_ms: u64,
        direction: D,
        leg_index: u8,
    ) -> Self
    where
        M: Into<u64>,
        D: Into<Direction>,
    {
        Self {
            market_id: market_id.into(),
            start_at_ms,
            leg_type: RfqLegType::BinaryEvent,
            direction: direction.into(),
            leg_index,
        }
    }

    #[inline]
    pub const fn price_asset(self) -> Option<Asset> {
        match self.leg_type {
            RfqLegType::PriceStrike { asset, .. } => Some(asset),
            RfqLegType::BinaryEvent => None,
        }
    }

    #[inline]
    pub const fn price_window(self) -> Option<Duration> {
        match self.leg_type {
            RfqLegType::PriceStrike { window, .. } => Some(window),
            RfqLegType::BinaryEvent => None,
        }
    }

    #[inline]
    pub const fn price_window_secs(self) -> Option<u32> {
        match self.leg_type {
            RfqLegType::PriceStrike { window, .. } => Some(window.as_secs()),
            RfqLegType::BinaryEvent => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[repr(C)]
/// Fixed-size RFQ leg encoding used on the market-maker wire protocol.
pub struct RfqLegWire {
    /// Market being quoted for this leg.
    pub market_id: u64,
    /// Leg start time in Unix milliseconds.
    pub start_at_ms: u64,
    /// Leg discriminator: 0 = price strike, 2 = binary event. Tag 1 is retired.
    pub type_tag: u8,
    /// Trade direction encoded by the RFQ protocol.
    pub direction: u8,
    /// Zero-based leg position inside the RFQ.
    pub leg_index: u8,
    /// For price-strike legs, the asset id. For binary-event legs, always 0.
    pub type_value: u8,
    /// For price-strike legs, the market window in seconds. For binary-event legs, always 0.
    pub price_window_secs: u32,
}

const_assert_eq!(std::mem::size_of::<RfqLegWire>(), 24);

impl RfqLegWire {
    pub const SIZE: usize = 24;

    /// Decode the protocol's fixed little-endian leg representation.
    #[inline]
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        Self {
            market_id: read_u64_le(bytes, 0),
            start_at_ms: read_u64_le(bytes, 8),
            type_tag: bytes[16],
            direction: bytes[17],
            leg_index: bytes[18],
            type_value: bytes[19],
            price_window_secs: read_u32_le(bytes, 20),
        }
    }

    /// Encode the protocol's fixed little-endian leg representation.
    #[inline]
    pub fn to_bytes(self) -> [u8; Self::SIZE] {
        let mut bytes = [0; Self::SIZE];
        write_u64_le(&mut bytes, 0, self.market_id);
        write_u64_le(&mut bytes, 8, self.start_at_ms);
        bytes[16] = self.type_tag;
        bytes[17] = self.direction;
        bytes[18] = self.leg_index;
        bytes[19] = self.type_value;
        write_u32_le(&mut bytes, 20, self.price_window_secs);
        bytes
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RfqLegWireDecodeError {
    InvalidTypeTag(u8),
    InvalidAsset(u8),
    InvalidDirection(u8),
    InvalidBinaryEventTypeValue(u8),
    InvalidPriceWindowSecs(u32),
    InvalidBinaryEventPriceWindowSecs(u32),
}

impl std::fmt::Display for RfqLegWireDecodeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidTypeTag(value) => write!(f, "invalid RFQ leg type tag: {value}"),
            Self::InvalidAsset(value) => write!(f, "invalid RFQ asset: {value}"),
            Self::InvalidDirection(value) => write!(f, "invalid RFQ direction: {value}"),
            Self::InvalidBinaryEventTypeValue(value) => {
                write!(f, "invalid RFQ binary-event type value: {value}")
            }
            Self::InvalidPriceWindowSecs(value) => {
                write!(f, "invalid RFQ price_window_secs: {value}")
            }
            Self::InvalidBinaryEventPriceWindowSecs(value) => {
                write!(f, "invalid RFQ binary-event price_window_secs: {value}")
            }
        }
    }
}

impl std::error::Error for RfqLegWireDecodeError {}

impl TryFrom<RfqLegWire> for RfqLeg {
    type Error = RfqLegWireDecodeError;

    fn try_from(wire: RfqLegWire) -> Result<Self, Self::Error> {
        let direction = Direction::from_u8(wire.direction)
            .ok_or(RfqLegWireDecodeError::InvalidDirection(wire.direction))?;
        let leg_type = match wire.type_tag {
            RFQ_LEG_TYPE_PRICE_STRIKE_TAG => RfqLegType::PriceStrike {
                asset: Asset::from_u8(wire.type_value)
                    .ok_or(RfqLegWireDecodeError::InvalidAsset(wire.type_value))?,
                window: Duration::from_secs(wire.price_window_secs).ok_or(
                    RfqLegWireDecodeError::InvalidPriceWindowSecs(wire.price_window_secs),
                )?,
            },
            RFQ_LEG_TYPE_BINARY_EVENT_TAG => {
                if wire.price_window_secs != 0 {
                    return Err(RfqLegWireDecodeError::InvalidBinaryEventPriceWindowSecs(
                        wire.price_window_secs,
                    ));
                }
                if wire.type_value != 0 {
                    return Err(RfqLegWireDecodeError::InvalidBinaryEventTypeValue(
                        wire.type_value,
                    ));
                }
                RfqLegType::BinaryEvent
            }
            other => return Err(RfqLegWireDecodeError::InvalidTypeTag(other)),
        };

        Ok(Self {
            market_id: wire.market_id,
            start_at_ms: wire.start_at_ms,
            leg_type,
            direction,
            leg_index: wire.leg_index,
        })
    }
}

impl From<RfqLeg> for RfqLegWire {
    fn from(leg: RfqLeg) -> Self {
        match leg.leg_type {
            RfqLegType::PriceStrike { asset, window } => Self {
                market_id: leg.market_id,
                start_at_ms: leg.start_at_ms,
                type_tag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
                direction: leg.direction as u8,
                leg_index: leg.leg_index,
                type_value: asset as u8,
                price_window_secs: window.as_secs(),
            },
            RfqLegType::BinaryEvent => Self {
                market_id: leg.market_id,
                start_at_ms: leg.start_at_ms,
                type_tag: RFQ_LEG_TYPE_BINARY_EVENT_TAG,
                direction: leg.direction as u8,
                leg_index: leg.leg_index,
                type_value: 0,
                price_window_secs: 0,
            },
        }
    }
}

/// Taker metadata sent with RFQs for market-maker pricing decisions.
///
/// Contains the taker tier and wallet address visible in RFQ broadcasts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(C)]
pub struct TakerMetadata {
    /// Taker tier for differentiated pricing.
    pub tier: u8,
    /// Taker wallet address.
    pub address: Address,
    /// Reserved padding for stable layout and future expansion.
    pub _reserved: [u8; 3],
}

const_assert_eq!(std::mem::size_of::<TakerMetadata>(), 24);

impl TakerMetadata {
    #[inline]
    pub fn new(tier: UserTier, address: Address) -> Self {
        Self {
            tier: tier as u8,
            address,
            _reserved: [0; 3],
        }
    }
}

impl Default for TakerMetadata {
    fn default() -> Self {
        Self {
            tier: UserTier::Standard as u8,
            address: Address::ZERO,
            _reserved: [0; 3],
        }
    }
}

#[derive(Debug, Clone, Copy)]
#[repr(C)]
struct WireTakerMetadata {
    pub option: u8,
    pub tier: u8,
    pub _reserved: [u8; 2],
    pub address: [u8; 20],
}

const_assert_eq!(std::mem::size_of::<WireTakerMetadata>(), 24);

/// RFQ broadcast payload delivered to market makers.
///
/// This fixed-size binary payload is carried in `ServerMessage::Rfq.data` after
/// base64 encoding.
#[derive(Debug, Clone, Copy)]
#[repr(C)]
pub struct BroadcastRfqRequest {
    /// Request ID (UUID bytes).
    pub request_id: [u8; 16],
    /// Wager amount in micro-units.
    pub wager_micros: u64,
    /// Expiry timestamp (ms since Unix epoch).
    pub expires_at_ms: u64,
    /// Optional taker metadata visible to market makers.
    taker_metadata: WireTakerMetadata,
    /// Order type discriminator.
    pub order_type: u8,
    /// Number of populated entries in `legs`.
    pub leg_count: u8,
    /// RFQ binary protocol version. This is independent of the auth signature domain version.
    pub protocol_version: u8,
    /// Reserved padding to align the leg array on an 8-byte boundary.
    pub _reserved: [u8; 5],
    /// Leg data. Only the first `leg_count` entries are active.
    pub legs: [RfqLegWire; MAX_RFQ_LEGS],
}

const_assert_eq!(std::mem::size_of::<BroadcastRfqRequest>(), 280);

#[inline]
fn decode_taker_metadata(wire: WireTakerMetadata) -> Option<TakerMetadata> {
    (wire.option != 0).then_some(TakerMetadata {
        tier: wire.tier,
        address: Address::from_slice(&wire.address),
        _reserved: [0; 3],
    })
}

impl BroadcastRfqRequest {
    pub const SIZE: usize = 64 + (MAX_RFQ_LEGS * RfqLegWire::SIZE);

    #[inline]
    pub fn request_id(&self) -> RequestId {
        RequestId::from_bytes(self.request_id)
    }

    #[inline]
    pub fn wager(&self) -> Amount {
        Amount::from_micro(self.wager_micros)
    }

    #[inline]
    pub fn expires_at(&self) -> Timestamp {
        Timestamp::from_millis(self.expires_at_ms)
    }

    #[inline]
    pub fn order_type(&self) -> Option<OrderType> {
        OrderType::from_u8(self.order_type)
    }

    #[inline]
    pub fn is_expired(&self) -> bool {
        Timestamp::now().as_millis() > self.expires_at_ms
    }

    #[inline]
    pub fn active_leg_wires(&self) -> &[RfqLegWire] {
        let leg_count = (self.leg_count as usize).min(MAX_RFQ_LEGS);
        &self.legs[..leg_count]
    }

    #[inline]
    pub fn leg_wire(&self, index: usize) -> Option<RfqLegWire> {
        let leg_count = (self.leg_count as usize).min(MAX_RFQ_LEGS);
        (index < leg_count).then(|| self.legs[index])
    }

    #[inline]
    pub fn iter_leg_wires(&self) -> impl Iterator<Item = RfqLegWire> + '_ {
        let leg_count = (self.leg_count as usize).min(MAX_RFQ_LEGS);
        (0..leg_count).map(move |i| self.legs[i])
    }

    #[inline]
    pub fn leg(&self, index: usize) -> Option<Result<RfqLeg, RfqLegWireDecodeError>> {
        self.leg_wire(index).map(RfqLeg::try_from)
    }

    #[inline]
    pub fn iter_legs(&self) -> impl Iterator<Item = Result<RfqLeg, RfqLegWireDecodeError>> + '_ {
        self.iter_leg_wires().map(RfqLeg::try_from)
    }

    #[inline]
    pub fn remaining_ms(&self) -> u64 {
        self.expires_at_ms
            .saturating_sub(Timestamp::now().as_millis())
    }

    #[inline]
    pub fn get_taker_metadata(&self) -> Option<TakerMetadata> {
        decode_taker_metadata(self.taker_metadata)
    }

    #[inline]
    pub fn taker_tier(&self) -> Option<UserTier> {
        self.get_taker_metadata()
            .and_then(|metadata| UserTier::from_u8(metadata.tier))
    }

    #[inline]
    pub fn taker_address(&self) -> Option<Address> {
        self.get_taker_metadata().map(|metadata| metadata.address)
    }

    #[inline]
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        let mut legs = [RfqLegWire::default(); MAX_RFQ_LEGS];
        for (index, leg) in legs.iter_mut().enumerate() {
            let offset = 64 + (index * RfqLegWire::SIZE);
            let leg_bytes: &[u8; RfqLegWire::SIZE] = bytes[offset..offset + RfqLegWire::SIZE]
                .try_into()
                .expect("RFQ leg slice has fixed size");
            *leg = RfqLegWire::from_bytes(leg_bytes);
        }
        Self {
            request_id: bytes[0..16]
                .try_into()
                .expect("request ID slice has fixed size"),
            wager_micros: read_u64_le(bytes, 16),
            expires_at_ms: read_u64_le(bytes, 24),
            taker_metadata: WireTakerMetadata {
                option: bytes[32],
                tier: bytes[33],
                _reserved: bytes[34..36]
                    .try_into()
                    .expect("taker metadata reserved slice has fixed size"),
                address: bytes[36..56]
                    .try_into()
                    .expect("taker address slice has fixed size"),
            },
            order_type: bytes[56],
            leg_count: bytes[57],
            protocol_version: bytes[58],
            _reserved: bytes[59..64]
                .try_into()
                .expect("broadcast reserved slice has fixed size"),
            legs,
        }
    }

    /// Encode the fixed broadcast layout using the protocol's little-endian integers.
    #[inline]
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        let mut bytes = [0; Self::SIZE];
        bytes[0..16].copy_from_slice(&self.request_id);
        write_u64_le(&mut bytes, 16, self.wager_micros);
        write_u64_le(&mut bytes, 24, self.expires_at_ms);
        bytes[32] = self.taker_metadata.option;
        bytes[33] = self.taker_metadata.tier;
        bytes[34..36].copy_from_slice(&self.taker_metadata._reserved);
        bytes[36..56].copy_from_slice(&self.taker_metadata.address);
        bytes[56] = self.order_type;
        bytes[57] = self.leg_count;
        bytes[58] = self.protocol_version;
        bytes[59..64].copy_from_slice(&self._reserved);
        for (index, leg) in self.legs.iter().enumerate() {
            let offset = 64 + (index * RfqLegWire::SIZE);
            bytes[offset..offset + RfqLegWire::SIZE].copy_from_slice(&leg.to_bytes());
        }
        bytes
    }
}

/// Quote response submitted by a market maker.
///
/// This is the fixed-size binary payload carried in `ClientMessage::Quote.data`
/// after base64 decoding.
#[derive(Debug, Clone, Copy)]
#[repr(C, packed)]
pub struct QuoteResponse {
    /// Original RFQ request ID.
    pub request_id: [u8; 16],
    /// Offered odds in basis points.
    pub odds: u32,
    /// Maximum fill size in micro-units.
    pub max_fill_micros: u64,
    /// Optional maker-supplied correlation ID. All zero bytes mean absent.
    pub client_quote_id: [u8; 16],
    /// Reserved padding for stable layout.
    pub _reserved: [u8; 4],
    /// secp256k1 signature (65 bytes, r/s/v).
    pub signature: [u8; 65],
}

const_assert_eq!(std::mem::size_of::<QuoteResponse>(), 113);

impl QuoteResponse {
    /// Size of the pre-signature payload.
    pub const SIGNED_DATA_SIZE: usize = 48;
    /// Total encoded size of `QuoteResponse`.
    pub const SIZE: usize = 113;

    /// Create a new unsigned quote response.
    pub fn new(request_id: RequestId, odds: Odds, max_fill: Amount) -> Self {
        Self::new_with_client_quote_id(request_id, odds, max_fill, ClientQuoteId::nil())
    }

    /// Create a new unsigned quote response with a maker-supplied correlation ID.
    pub fn new_with_client_quote_id(
        request_id: RequestId,
        odds: Odds,
        max_fill: Amount,
        client_quote_id: ClientQuoteId,
    ) -> Self {
        Self {
            request_id: *request_id.as_bytes(),
            odds: odds.0,
            max_fill_micros: max_fill.as_micros(),
            client_quote_id: *client_quote_id.as_bytes(),
            _reserved: [0; 4],
            signature: [0; 65],
        }
    }

    /// Return the exact bytes covered by the quote signature.
    #[inline]
    pub fn signed_data_bytes(&self) -> [u8; Self::SIGNED_DATA_SIZE] {
        let full = self.to_bytes();
        let mut result = [0u8; Self::SIGNED_DATA_SIZE];
        result.copy_from_slice(&full[..Self::SIGNED_DATA_SIZE]);
        result
    }

    /// Verify the signature against the market maker wallet address.
    ///
    /// This uses Alloy's primitive signature recovery.
    pub fn verify_signature(&self, wallet_address: &Address) -> bool {
        Signature::from_raw_array(&self.signature)
            .ok()
            .map(|signature| signature.normalized_s())
            .and_then(|signature| {
                signature
                    .recover_address_from_msg(self.signed_data_bytes())
                    .ok()
            })
            .is_some_and(|recovered| &recovered == wallet_address)
    }

    /// Get request ID.
    #[inline]
    pub fn request_id(&self) -> RequestId {
        RequestId::from_bytes(self.request_id)
    }

    /// Get offered odds.
    #[inline]
    pub fn odds(&self) -> Odds {
        Odds(self.odds)
    }

    /// Get maximum fill size.
    #[inline]
    pub fn max_fill(&self) -> Amount {
        Amount::from_micro(self.max_fill_micros)
    }

    /// Get the optional maker-supplied correlation ID.
    #[inline]
    pub fn client_quote_id(&self) -> Option<ClientQuoteId> {
        let id = ClientQuoteId::from_bytes(self.client_quote_id);
        (!id.is_nil()).then_some(id)
    }

    /// Check if odds meet minimum requirement.
    #[inline]
    pub fn meets_min_odds(&self, min_odds: Odds) -> bool {
        self.odds >= min_odds.0
    }

    /// Parse from bytes.
    #[inline]
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        Self {
            request_id: bytes[0..16]
                .try_into()
                .expect("request ID slice has fixed size"),
            odds: read_u32_le(bytes, 16),
            max_fill_micros: read_u64_le(bytes, 20),
            client_quote_id: bytes[28..44]
                .try_into()
                .expect("client quote ID slice has fixed size"),
            _reserved: bytes[44..48]
                .try_into()
                .expect("quote reserved slice has fixed size"),
            signature: bytes[48..113]
                .try_into()
                .expect("quote signature slice has fixed size"),
        }
    }

    /// Parse from a byte slice.
    #[inline]
    pub fn from_slice(bytes: &[u8]) -> Option<Self> {
        let bytes: &[u8; Self::SIZE] = bytes.try_into().ok()?;
        Some(Self::from_bytes(bytes))
    }

    /// Encode the fixed quote layout using the protocol's little-endian integers.
    #[inline]
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        let mut bytes = [0; Self::SIZE];
        bytes[0..16].copy_from_slice(&self.request_id);
        write_u32_le(&mut bytes, 16, self.odds);
        write_u64_le(&mut bytes, 20, self.max_fill_micros);
        bytes[28..44].copy_from_slice(&self.client_quote_id);
        bytes[44..48].copy_from_slice(&self._reserved);
        bytes[48..113].copy_from_slice(&self.signature);
        bytes
    }
}

// The RFQ wire contract is little-endian across languages. Keep these explicit
// conversions instead of copying native integer storage from the repr(C) structs.
#[inline]
fn read_u32_le(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(
        bytes[offset..offset + 4]
            .try_into()
            .expect("u32 wire slice has fixed size"),
    )
}

#[inline]
fn read_u64_le(bytes: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(
        bytes[offset..offset + 8]
            .try_into()
            .expect("u64 wire slice has fixed size"),
    )
}

#[inline]
fn write_u32_le(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}

#[inline]
fn write_u64_le(bytes: &mut [u8], offset: usize, value: u64) {
    bytes[offset..offset + 8].copy_from_slice(&value.to_le_bytes());
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{Duration, MarketId};

    #[test]
    fn rfq_leg_wire_size_is_stable() {
        assert_eq!(std::mem::size_of::<RfqLegWire>(), 24);
    }

    #[test]
    fn rfq_wire_integers_use_explicit_little_endian_bytes() {
        let leg = RfqLegWire {
            market_id: 0x0102_0304_0506_0708,
            start_at_ms: 0x1112_1314_1516_1718,
            type_tag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
            direction: Direction::Up as u8,
            leg_index: 2,
            type_value: Asset::BTC as u8,
            price_window_secs: 0x2122_2324,
        };
        let leg_bytes = leg.to_bytes();
        assert_eq!(
            &leg_bytes[0..8],
            &[0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01]
        );
        assert_eq!(
            &leg_bytes[8..16],
            &[0x18, 0x17, 0x16, 0x15, 0x14, 0x13, 0x12, 0x11]
        );
        assert_eq!(&leg_bytes[20..24], &[0x24, 0x23, 0x22, 0x21]);
        assert_eq!(RfqLegWire::from_bytes(&leg_bytes), leg);

        let broadcast = BroadcastRfqRequest {
            request_id: [0; 16],
            wager_micros: 0x3132_3334_3536_3738,
            expires_at_ms: 0x4142_4344_4546_4748,
            taker_metadata: WireTakerMetadata {
                option: 0,
                tier: 0,
                _reserved: [0; 2],
                address: [0; 20],
            },
            order_type: OrderType::FOK as u8,
            leg_count: 1,
            protocol_version: RFQ_PROTOCOL_VERSION,
            _reserved: [0; 5],
            legs: [leg; MAX_RFQ_LEGS],
        };
        let broadcast_bytes = broadcast.to_bytes();
        assert_eq!(
            &broadcast_bytes[16..24],
            &[0x38, 0x37, 0x36, 0x35, 0x34, 0x33, 0x32, 0x31]
        );
        assert_eq!(
            &broadcast_bytes[24..32],
            &[0x48, 0x47, 0x46, 0x45, 0x44, 0x43, 0x42, 0x41]
        );
        assert_eq!(
            BroadcastRfqRequest::from_bytes(&broadcast_bytes).to_bytes(),
            broadcast_bytes
        );

        let quote = QuoteResponse {
            request_id: [0; 16],
            odds: 0x5152_5354,
            max_fill_micros: 0x6162_6364_6566_6768,
            client_quote_id: [0; 16],
            _reserved: [0; 4],
            signature: [0; 65],
        };
        let quote_bytes = quote.to_bytes();
        assert_eq!(&quote_bytes[16..20], &[0x54, 0x53, 0x52, 0x51]);
        assert_eq!(
            &quote_bytes[20..28],
            &[0x68, 0x67, 0x66, 0x65, 0x64, 0x63, 0x62, 0x61]
        );
        assert_eq!(
            QuoteResponse::from_bytes(&quote_bytes).to_bytes(),
            quote_bytes
        );
    }

    #[test]
    fn broadcast_rfq_request_size_is_stable() {
        assert_eq!(BroadcastRfqRequest::SIZE, 280);
    }

    #[test]
    fn quote_response_size_is_stable() {
        assert_eq!(QuoteResponse::SIZE, 113);
        assert_eq!(std::mem::size_of::<QuoteResponse>(), QuoteResponse::SIZE);
    }

    #[test]
    fn corrupted_leg_counts_clamp_instead_of_panicking() {
        // Broadcasts decode from untrusted bytes, so leg accessors must clamp
        // an oversized count instead of panicking.
        let mut broadcast = BroadcastRfqRequest::from_bytes(&[0; BroadcastRfqRequest::SIZE]);

        broadcast.leg_count = u8::MAX;
        assert!(broadcast.leg_wire(MAX_RFQ_LEGS).is_none());
        assert_eq!(broadcast.active_leg_wires().len(), MAX_RFQ_LEGS);
        assert_eq!(broadcast.iter_leg_wires().count(), MAX_RFQ_LEGS);
    }

    #[test]
    fn price_rfq_leg_round_trips_through_wire() {
        let leg = RfqLeg::new_price_strike(
            42u64,
            123_456,
            Asset::SOL,
            Direction::Down,
            Duration::FIFTEEN_MINUTES,
            3,
        );
        let wire = RfqLegWire::from(leg);

        assert_eq!(wire.type_tag, RFQ_LEG_TYPE_PRICE_STRIKE_TAG);
        assert_eq!(wire.type_value, 2);
        assert_eq!(wire.price_window_secs, 900);
        assert_eq!(RfqLeg::try_from(wire), Ok(leg));
    }

    #[test]
    fn price_rfq_leg_decodes_supported_windows() {
        for window in [
            Duration::ONE_MINUTE,
            Duration::FIVE_MINUTES,
            Duration::FIFTEEN_MINUTES,
            Duration::ONE_HOUR,
            Duration::FOUR_HOURS,
            Duration::ONE_DAY,
        ] {
            let wire = RfqLegWire {
                type_tag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
                type_value: Asset::BTC as u8,
                price_window_secs: window.as_secs(),
                ..RfqLegWire::default()
            };

            let leg = RfqLeg::try_from(wire).unwrap();
            assert_eq!(leg.price_window(), Some(window));
            assert_eq!(leg.price_window_secs(), Some(window.as_secs()));
        }
    }

    #[test]
    fn binary_event_rfq_leg_round_trips_through_wire() {
        let leg = RfqLeg::new_binary_event(42u64, 123_456, Direction::Down, 3);
        let wire = RfqLegWire::from(leg);

        assert_eq!(wire.type_tag, RFQ_LEG_TYPE_BINARY_EVENT_TAG);
        assert_eq!(wire.type_value, 0);
        assert_eq!(wire.price_window_secs, 0);
        assert_eq!(RfqLeg::try_from(wire), Ok(leg));
    }

    #[test]
    fn price_rfq_leg_rejects_unknown_asset() {
        let wire = RfqLegWire {
            type_tag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
            type_value: 99,
            ..RfqLegWire::default()
        };

        assert_eq!(
            RfqLeg::try_from(wire),
            Err(RfqLegWireDecodeError::InvalidAsset(99))
        );
    }

    #[test]
    fn rfq_leg_rejects_unknown_direction() {
        let wire = RfqLegWire {
            type_tag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
            direction: 99,
            ..RfqLegWire::default()
        };

        assert_eq!(
            RfqLeg::try_from(wire),
            Err(RfqLegWireDecodeError::InvalidDirection(99))
        );
    }

    #[test]
    fn price_rfq_leg_rejects_unsupported_window() {
        let wire = RfqLegWire {
            type_tag: RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
            type_value: Asset::BTC as u8,
            price_window_secs: 1,
            ..RfqLegWire::default()
        };

        assert_eq!(
            RfqLeg::try_from(wire),
            Err(RfqLegWireDecodeError::InvalidPriceWindowSecs(1))
        );
    }

    #[test]
    fn binary_event_rfq_leg_rejects_nonzero_price_window_secs() {
        let wire = RfqLegWire {
            type_tag: RFQ_LEG_TYPE_BINARY_EVENT_TAG,
            type_value: 0,
            price_window_secs: 1,
            ..RfqLegWire::default()
        };

        assert_eq!(
            RfqLeg::try_from(wire),
            Err(RfqLegWireDecodeError::InvalidBinaryEventPriceWindowSecs(1))
        );
    }

    #[test]
    fn binary_event_rfq_leg_rejects_nonzero_reserved_type_value() {
        let wire = RfqLegWire {
            type_tag: RFQ_LEG_TYPE_BINARY_EVENT_TAG,
            type_value: 99,
            ..RfqLegWire::default()
        };

        assert_eq!(
            RfqLeg::try_from(wire),
            Err(RfqLegWireDecodeError::InvalidBinaryEventTypeValue(99))
        );
    }

    #[test]
    fn active_leg_accessors_skip_inactive_slots() {
        let active_leg = RfqLeg::new_price_strike(
            MarketId::new(1),
            0,
            Asset::BTC,
            Direction::Up,
            Duration::FIFTEEN_MINUTES,
            0,
        );
        let inactive_leg = RfqLeg::new_binary_event(MarketId::new(99), 123, Direction::Down, 7);
        let mut parsed = BroadcastRfqRequest::from_bytes(&[0; BroadcastRfqRequest::SIZE]);
        parsed.leg_count = 1;
        parsed.legs[0] = RfqLegWire::from(active_leg);
        parsed.legs[1] = RfqLegWire::from(inactive_leg);

        assert_eq!(parsed.active_leg_wires(), &[RfqLegWire::from(active_leg)]);
        assert_eq!(parsed.leg_wire(1), None);
        assert_eq!(
            parsed.iter_leg_wires().collect::<Vec<_>>(),
            vec![RfqLegWire::from(active_leg)]
        );
    }

    #[test]
    fn broadcast_rfq_round_trip_preserves_shielded_metadata_absence() {
        let parsed = BroadcastRfqRequest::from_bytes(&[0; BroadcastRfqRequest::SIZE]);

        assert!(parsed.get_taker_metadata().is_none());
        assert!(parsed.taker_tier().is_none());
        assert!(parsed.taker_address().is_none());
    }

    #[test]
    fn quote_response_from_slice_requires_exact_size() {
        let quote = QuoteResponse::new(RequestId::new(), Odds::EVEN, Amount::from_dollars(1));
        let bytes = quote.to_bytes();

        assert_eq!(
            QuoteResponse::from_slice(&bytes).unwrap().to_bytes(),
            QuoteResponse::from_bytes(&bytes).to_bytes(),
        );
        assert!(QuoteResponse::from_slice(&bytes[..QuoteResponse::SIZE - 1]).is_none());

        let mut oversized = bytes.to_vec();
        oversized.push(0);
        assert!(QuoteResponse::from_slice(&oversized).is_none());
    }
}
