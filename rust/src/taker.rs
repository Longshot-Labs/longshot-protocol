//! Taker order signing types.

use alloy_primitives::Signature;
use alloy_signer::{Error as SignerError, SignerSync};
use alloy_signer_local::PrivateKeySigner;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;
use std::{error::Error, fmt};

use crate::types::{Address, Direction, MarketId, OrderType, MAX_RFQ_LEGS};

// =============================================================================
// ORDER LEG
// =============================================================================

/// Order leg for signing.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct OrderLeg {
    /// Market identifier.
    pub market_id: MarketId,
    /// Direction (0=Up, 1=Down).
    ///
    /// For markets this encodes the boolean prediction:
    /// Up == price higher than strike, Down == price not higher than strike.
    pub direction: u8,
}

impl OrderLeg {
    /// Serialize leg to bytes for signing.
    pub fn to_bytes(&self) -> [u8; 9] {
        let mut bytes = [0u8; 9];
        bytes[..8].copy_from_slice(&self.market_id.as_u64().to_le_bytes());
        bytes[8] = self.direction;
        bytes
    }
}

// =============================================================================
// SIGNED ORDER
// =============================================================================

/// An order signed by the user's wallet.
///
/// This represents the user's commitment to a trade. The signature authorizes
/// the API to fill at or above `min_odds_bps`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(bound = "")]
pub struct SignedOrder {
    // === Order Data ===
    /// User's wallet address (signer).
    pub user: Address,

    /// Wager amount in micro-dollars.
    pub wager_micros: u64,

    /// Minimum acceptable odds in basis points (`25_000 = 2.5x`).
    pub min_odds_bps: u32,

    /// Order legs.
    pub legs: Vec<OrderLeg>,

    /// Unique nonce to prevent replay.
    pub nonce: u64,

    /// Submission deadline in milliseconds since Unix epoch.
    pub expires_at_ms: u64,

    /// Order type: IOC or FOK.
    pub order_type: OrderType,

    /// If true, hide tier/address metadata from market makers.
    pub shield_on: bool,

    // === Signature ===
    /// ECDSA signature (65 bytes: r, s, v).
    #[serde(with = "signature_hex")]
    pub signature: [u8; 65],
}

mod signature_hex {
    use serde::{Deserialize, Deserializer, Serializer};

    pub fn serialize<S>(signature: &[u8; 65], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&hex::encode(signature))
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 65], D::Error>
    where
        D: Deserializer<'de>,
    {
        let mut value = String::deserialize(deserializer)?;
        if let Some(stripped) = value.strip_prefix("0x") {
            value = stripped.to_string();
        }

        let bytes = hex::decode(&value).map_err(serde::de::Error::custom)?;
        bytes
            .try_into()
            .map_err(|_| serde::de::Error::custom("expected 65-byte hex signature"))
    }
}

/// Invalid signed-order data.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SignedOrderError {
    MissingLegs,
    TooManyLegs { max: usize, actual: usize },
    InvalidLegDirection { index: usize, direction: u8 },
}

impl fmt::Display for SignedOrderError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::MissingLegs => write!(f, "order must include at least one leg"),
            Self::TooManyLegs { max, actual } => {
                write!(f, "order has {actual} legs, maximum is {max}")
            }
            Self::InvalidLegDirection { index, direction } => {
                write!(f, "invalid direction {direction} at legs[{index}]")
            }
        }
    }
}

impl Error for SignedOrderError {}

#[derive(Debug)]
pub enum TakerSignError {
    Order(SignedOrderError),
    Signer(SignerError),
}

impl fmt::Display for TakerSignError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Order(err) => write!(f, "{err}"),
            Self::Signer(err) => write!(f, "{err}"),
        }
    }
}

impl Error for TakerSignError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Order(err) => Some(err),
            Self::Signer(err) => Some(err),
        }
    }
}

impl From<SignedOrderError> for TakerSignError {
    fn from(err: SignedOrderError) -> Self {
        Self::Order(err)
    }
}

impl From<SignerError> for TakerSignError {
    fn from(err: SignerError) -> Self {
        Self::Signer(err)
    }
}

impl SignedOrder {
    /// Maximum number of legs in an order.
    pub const MAX_LEGS: usize = MAX_RFQ_LEGS;

    pub(crate) fn validate_legs(&self) -> Result<(), SignedOrderError> {
        if self.legs.is_empty() {
            return Err(SignedOrderError::MissingLegs);
        }
        if self.legs.len() > Self::MAX_LEGS {
            return Err(SignedOrderError::TooManyLegs {
                max: Self::MAX_LEGS,
                actual: self.legs.len(),
            });
        }
        for (index, leg) in self.legs.iter().enumerate() {
            if Direction::from_u8(leg.direction).is_none() {
                return Err(SignedOrderError::InvalidLegDirection {
                    index,
                    direction: leg.direction,
                });
            }
        }
        Ok(())
    }

    /// Try to serialize the funding-neutral order identity used for replay keying.
    ///
    /// This intentionally excludes the RFQ funding choice so attempts to reuse
    /// the same order with a different funding choice resolve to the same replay
    /// key and can be rejected as conflicting retries.
    ///
    /// Wire format:
    /// - `bytes[0..20]`: user address
    /// - `bytes[20..28]`: wager_micros (u64 LE)
    /// - `bytes[28..32]`: min_odds_bps (u32 LE)
    /// - `bytes[32..40]`: nonce (u64 LE)
    /// - `bytes[40..48]`: expires_at_ms (u64 LE)
    /// - `bytes[48]`: order_type (u8) - 1=IOC, 2=FOK
    /// - `bytes[49]`: shield_on (u8)
    /// - `bytes[50]`: leg_count (u8)
    /// - `bytes[51..]`: legs (9 bytes each)
    pub fn try_replay_bytes(&self) -> Result<SmallVec<[u8; 128]>, SignedOrderError> {
        self.try_order_bytes(None)
    }

    /// Serialize the funding-neutral order identity used for replay keying.
    ///
    /// Panics if the order is invalid. Use
    /// [`try_replay_bytes`](Self::try_replay_bytes) when handling externally
    /// constructed or mutated orders.
    #[inline]
    pub fn replay_bytes(&self) -> SmallVec<[u8; 128]> {
        self.try_replay_bytes().expect("invalid signed order")
    }

    /// Try to serialize order data and its funding choice to bytes for signing.
    ///
    /// Wallet signatures are EIP-191 signatures over these bytes, not over the
    /// JSON request payload. Use [`sign_order`] or [`signed_order`] to apply the
    /// same signing scheme as the server verifies.
    ///
    /// Wire format:
    /// - `bytes[0..20]`: user address
    /// - `bytes[20..28]`: wager_micros (u64 LE)
    /// - `bytes[28..32]`: min_odds_bps (u32 LE)
    /// - `bytes[32..40]`: nonce (u64 LE)
    /// - `bytes[40..48]`: expires_at_ms (u64 LE)
    /// - `bytes[48]`: order_type (u8) - 1=IOC, 2=FOK
    /// - `bytes[49]`: shield_on (u8)
    /// - `bytes[50]`: use_app_tokens (u8)
    /// - `bytes[51]`: leg_count (u8)
    /// - `bytes[52..]`: legs (9 bytes each)
    ///
    /// SECURITY: `order_type` is included in the signature to prevent replay
    /// attacks where an attacker could submit a signed FOK order as IOC.
    pub fn try_signing_bytes(
        &self,
        use_app_tokens: bool,
    ) -> Result<SmallVec<[u8; 128]>, SignedOrderError> {
        self.try_order_bytes(Some(use_app_tokens))
    }

    fn try_order_bytes(
        &self,
        use_app_tokens: Option<bool>,
    ) -> Result<SmallVec<[u8; 128]>, SignedOrderError> {
        self.validate_legs()?;
        let mut bytes = SmallVec::with_capacity(
            51 + usize::from(use_app_tokens.is_some()) + self.legs.len() * 9,
        );

        // User address (20 bytes)
        bytes.extend_from_slice(self.user.as_slice());

        // Wager (8 bytes LE)
        bytes.extend_from_slice(&self.wager_micros.to_le_bytes());

        // Min odds (4 bytes LE)
        bytes.extend_from_slice(&self.min_odds_bps.to_le_bytes());

        // Nonce (8 bytes LE)
        bytes.extend_from_slice(&self.nonce.to_le_bytes());

        // Submission expiry (8 bytes LE)
        bytes.extend_from_slice(&self.expires_at_ms.to_le_bytes());

        // Order type (1 byte)
        bytes.push(self.order_type as u8);

        // Shield flag (1 byte)
        bytes.push(u8::from(self.shield_on));

        // App-token funding flag (1 byte, signing payload only)
        if let Some(use_app_tokens) = use_app_tokens {
            bytes.push(u8::from(use_app_tokens));
        }

        // Leg count (1 byte)
        bytes.push(self.legs.len() as u8);

        // Legs (9 bytes each)
        for leg in &self.legs {
            bytes.extend_from_slice(&leg.to_bytes());
        }

        Ok(bytes)
    }

    /// Serialize order data to bytes for signing.
    ///
    /// Panics if the order is invalid. Use [`try_signing_bytes`](Self::try_signing_bytes)
    /// when handling externally constructed or mutated orders.
    #[inline]
    pub fn signing_bytes(&self, use_app_tokens: bool) -> SmallVec<[u8; 128]> {
        self.try_signing_bytes(use_app_tokens)
            .expect("invalid signed order")
    }

    /// Verify this order's signature and funding choice against `self.user`.
    pub fn verify_signature(&self, use_app_tokens: bool) -> bool {
        let Ok(signing_bytes) = self.try_signing_bytes(use_app_tokens) else {
            return false;
        };
        Signature::from_raw_array(&self.signature)
            .ok()
            .map(|signature| signature.normalized_s())
            .and_then(|signature| signature.recover_address_from_msg(&signing_bytes).ok())
            .is_some_and(|recovered| recovered == self.user)
    }
}

/// Sign a taker order with EIP-191 over [`SignedOrder::try_signing_bytes`].
pub fn sign_order(
    order: &mut SignedOrder,
    use_app_tokens: bool,
    signing_key: &PrivateKeySigner,
) -> Result<(), TakerSignError> {
    let signing_bytes = order.try_signing_bytes(use_app_tokens)?;
    order.signature = signing_key.sign_message_sync(&signing_bytes)?.into();
    Ok(())
}

/// Return a signed taker order, preserving all order fields and replacing the signature.
pub fn signed_order(
    mut order: SignedOrder,
    use_app_tokens: bool,
    signing_key: &PrivateKeySigner,
) -> Result<SignedOrder, TakerSignError> {
    sign_order(&mut order, use_app_tokens, signing_key)?;
    Ok(order)
}
