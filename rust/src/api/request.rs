//! API request types.

use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

use crate::taker::{OrderLeg, SignedOrder, SignedOrderError};
use crate::types::{Address, Direction, MarketId, Odds, OrderType, PositionId};

/// Request to authenticate with direct wallet signature.
#[derive(Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "signature": "base64-encoded-65-byte-evm-signature",
    "signed_at_ms": 1735430000000u64
})))]
#[serde(deny_unknown_fields)]
pub struct WalletAuthRequest {
    /// User's wallet address (hex, with or without 0x prefix).
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub address: String,

    /// EIP-191 signature over the server-reconstructed authentication message.
    pub signature: String,

    /// Unix timestamp in milliseconds bound into the signed message.
    pub signed_at_ms: u64,

    /// Referral slug for new account attribution.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub referral_code: Option<String>,
}

impl fmt::Debug for WalletAuthRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("WalletAuthRequest")
            .field("address", &self.address)
            .field("signature", &"<redacted>")
            .field("signed_at_ms", &self.signed_at_ms)
            .field("referral_code", &self.referral_code)
            .finish()
    }
}

/// Request body for `POST /v1/rfq/estimate`: a prospective order to price
/// without reserving or executing anything.
///
/// Estimates have no `min_odds`, `order_type`, or idempotency key because they
/// do not execute an order.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct RfqEstimateRequest {
    /// Wager in micros (e.g., 100000000 = $100.00). Quotes are size-aware, so
    /// this should be the real prospective wager.
    #[cfg_attr(feature = "openapi", schema(example = 100000000, minimum = 500000))]
    pub wager_micros: u64,
    /// Order legs (1-9 legs supported).
    #[cfg_attr(feature = "openapi", schema(min_items = 1, max_items = 9))]
    pub legs: Vec<OrderLegJson>,
    /// If true, do not personalize the estimate to the taker's identity.
    #[serde(default)]
    pub shield_on: bool,
}

/// Request to move funds from onchain settlement balance into the app balance.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "amount_micros": 1000000,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
})))]
#[serde(deny_unknown_fields)]
pub struct UserDepositRequest {
    /// Amount to post from the user's settlement balance, in USDC micros.
    #[cfg_attr(feature = "openapi", schema(example = 1000000, minimum = 1))]
    pub amount_micros: u64,
    /// Client-supplied idempotency key for replay-safe submission.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub idempotency_key: String,
}

/// Withdrawal parameters for moving app balance back into onchain settlement balance.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "amount_micros": 1000000,
    "destination_address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
})))]
#[serde(deny_unknown_fields)]
pub struct UserWithdrawParams {
    /// Amount to withdraw from the user's app balance, in USDC micros.
    #[cfg_attr(feature = "openapi", schema(example = 1000000, minimum = 1))]
    pub amount_micros: u64,
    /// EVM address that should receive the withdrawn USDC from settlement.
    ///
    /// When omitted, the server uses the authenticated session address. Custodial sessions must
    /// provide an explicit external destination.
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub destination_address: Option<String>,
    /// Client-supplied idempotency key for replay-safe submission.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub idempotency_key: String,
}

/// Fresh authorization supplied with a withdrawal request.
#[derive(Serialize, Deserialize, PartialEq, Eq)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub enum WithdrawalAuthorization {
    /// Fresh Privy identity proof for a withdrawal.
    PrivyToken {
        /// Fresh Privy identity token for the authenticated user.
        token: String,
    },
    /// Fresh EIP-191 proof for a wallet-authenticated withdrawal.
    WalletSignature {
        /// EIP-191 signature over the canonical withdrawal authorization message.
        signature: String,
        /// Unix timestamp in milliseconds bound into the signed message.
        signed_at_ms: u64,
    },
}

impl fmt::Debug for WithdrawalAuthorization {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::PrivyToken { .. } => f
                .debug_struct("PrivyToken")
                .field("token", &"<redacted>")
                .finish(),
            Self::WalletSignature { signed_at_ms, .. } => f
                .debug_struct("WalletSignature")
                .field("signature", &"<redacted>")
                .field("signed_at_ms", signed_at_ms)
                .finish(),
        }
    }
}

/// Request to move funds from the app balance back into onchain settlement balance.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "withdraw_params": {
        "amount_micros": 1000000,
        "destination_address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
        "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
    },
    "authorization": {
        "type": "wallet_signature",
        "signature": "base64-encoded-65-byte-evm-signature",
        "signed_at_ms": 1785529737000u64
    }
})))]
#[serde(deny_unknown_fields)]
pub struct UserWithdrawRequest {
    /// Exact withdrawal parameters to submit.
    pub withdraw_params: UserWithdrawParams,
    /// Fresh authorization matching the authenticated session method.
    pub authorization: WithdrawalAuthorization,
}

/// Build the exact EIP-191 personal-message text for direct wallet authentication.
pub fn build_wallet_authentication_message(
    domain: &str,
    auth_address: &Address,
    signed_at_ms: u64,
) -> String {
    format!(
        "Longshot Wallet Authentication\n\nVersion: 1\nDomain: {domain}\nAuth Address: {}\nTimestamp: {signed_at_ms}",
        auth_address.to_checksum(None),
    )
}

/// Build the exact EIP-191 personal-message text for a wallet-authorized withdrawal.
pub fn build_wallet_withdrawal_authorization_message(
    domain: &str,
    chain_id: u64,
    auth_address: &Address,
    destination_address: &Address,
    amount_micros: u64,
    idempotency_key: &Uuid,
    signed_at_ms: u64,
) -> String {
    format!(
        "Longshot Withdrawal Authorization\n\nVersion: 1\nDomain: {domain}\nChain ID: {chain_id}\nAuth Address: {}\nDestination Address: {}\nAmount Micros: {amount_micros}\nIdempotency Key: {idempotency_key}\nTimestamp: {signed_at_ms}",
        auth_address.to_checksum(None),
        destination_address.to_checksum(None),
    )
}

/// Encode a 65-byte EVM signature using the API's padded standard Base64 format.
pub fn encode_wallet_signature(signature: &[u8; 65]) -> String {
    STANDARD.encode(signature)
}

/// Order leg in JSON format.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({"market_id": 42, "direction": "up"})))]
pub struct OrderLegJson {
    /// Market ID for the leg.
    #[cfg_attr(feature = "openapi", schema(example = 42))]
    pub market_id: u64,

    /// Direction: "up" or "down".
    #[cfg_attr(feature = "openapi", schema(example = "up"))]
    pub direction: String,
}

/// Signed order in JSON format.
///
/// **Signature Computation**: The signature is computed over a binary representation
/// of the order plus the top-level `CreateRfqRequest::use_app_tokens` funding
/// choice, NOT the JSON. See [`SignedOrder::signing_bytes`] for the exact format
/// and [`crate::taker::sign_order`] for the protocol helper.
/// Key conversions for signing:
/// - `wager_micros` is encoded directly as micros
/// - `min_odds` → `min_odds_bps` (multiply by 10,000 and round)
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "user": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "wager_micros": 100000000,
    "min_odds": 2.5,
    "legs": [{"market_id": 42, "direction": "up"}],
    "nonce": 1234567890,
    "expires_at_ms": 1735430300000u64,
    "order_type": 2,
    "shield_on": false,
    "signature": "base64-encoded-ecdsa-signature"
})))]
pub struct SignedOrderJson {
    /// User's wallet address (hex, with or without 0x prefix).
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub user: String,

    /// Wager in micros (e.g., 100000000 = $100.00).
    #[serde(deserialize_with = "crate::api::wire_int::u64_string::deserialize")]
    #[cfg_attr(feature = "openapi", schema(example = 100000000, minimum = 500000))]
    pub wager_micros: u64,

    /// Minimum acceptable odds (e.g., 2.5 = 2.5x).
    #[cfg_attr(feature = "openapi", schema(example = 2.5))]
    pub min_odds: f64,

    /// Order legs (1-9 legs supported).
    #[cfg_attr(feature = "openapi", schema(min_items = 1, max_items = 9))]
    pub legs: Vec<OrderLegJson>,

    /// Unique nonce (prevents replay attacks).
    #[serde(deserialize_with = "crate::api::wire_int::u64_string::deserialize")]
    #[cfg_attr(feature = "openapi", schema(example = 1234567890))]
    pub nonce: u64,

    /// Submission deadline in Unix milliseconds for this signed payload.
    #[serde(deserialize_with = "crate::api::wire_int::u64_string::deserialize")]
    #[cfg_attr(feature = "openapi", schema(example = 1735430300000u64))]
    pub expires_at_ms: u64,

    /// Order type: 1=IOC (Immediate-or-Cancel), 2=FOK (Fill-or-Kill, default).
    #[serde(default = "default_order_type")]
    #[cfg_attr(feature = "openapi", schema(example = 2, minimum = 1, maximum = 2))]
    pub order_type: u8,

    /// If true, suppress user tier and EVM address in MM-facing RFQs.
    #[cfg_attr(feature = "openapi", schema(example = false))]
    pub shield_on: bool,

    /// ECDSA signature (Base64 encoded, 65 bytes).
    pub signature: String,
}

/// How a community position is copied.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum CommunityPickMode {
    Tail,
    Fade,
}

impl CommunityPickMode {
    pub const fn to_u8(self) -> u8 {
        match self {
            Self::Tail => 0,
            Self::Fade => 1,
        }
    }
}

/// Optional community-position attribution for an RFQ.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct CommunityPickRequest {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub source_position_id: PositionId,
    pub mode: CommunityPickMode,
}

/// Request to create an RFQ.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct CreateRfqRequest {
    /// The signed order.
    pub order: SignedOrderJson,

    /// If true, spend eligible app tokens before cash.
    pub use_app_tokens: bool,
}

/// Unsigned RFQ order parameters supplied with the authenticated identity proof.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "wager_micros": 100000000,
    "min_odds": 2.5,
    "legs": [{"market_id": 42, "direction": "up"}],
    "order_type": 2,
    "shield_on": false,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
})))]
#[serde(deny_unknown_fields)]
pub struct UnsignedRfqOrderRequest {
    /// Wager in micros (e.g., 100000000 = $100.00).
    #[cfg_attr(feature = "openapi", schema(example = 100000000, minimum = 500000))]
    pub wager_micros: u64,

    /// Minimum acceptable odds (e.g., 2.5 = 2.5x).
    #[cfg_attr(feature = "openapi", schema(example = 2.5))]
    pub min_odds: f64,

    /// Order legs (1-9 legs supported).
    #[cfg_attr(feature = "openapi", schema(min_items = 1, max_items = 9))]
    pub legs: Vec<OrderLegJson>,

    /// Order type: 1=IOC (Immediate-or-Cancel), 2=FOK (Fill-or-Kill, default).
    #[serde(default = "default_order_type")]
    #[cfg_attr(feature = "openapi", schema(example = 2, minimum = 1, maximum = 2))]
    pub order_type: u8,

    /// If true, suppress user tier and EVM address in MM-facing RFQs.
    #[cfg_attr(feature = "openapi", schema(example = false))]
    pub shield_on: bool,

    /// Client-supplied idempotency key for replay-safe submission.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub idempotency_key: String,
}

/// Session-authenticated RFQ request that does not require a wallet signature.
#[derive(Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "privy_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "use_app_tokens": true,
    "rfq_params": {
        "wager_micros": 100000000,
        "min_odds": 2.5,
        "legs": [{"market_id": 42, "direction": "up"}],
        "order_type": 2,
        "shield_on": false,
        "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
    }
})))]
#[serde(deny_unknown_fields)]
pub struct CreateUnsignedRfqRequest {
    /// Fresh Privy identity token for the authenticated user.
    pub privy_token: String,

    /// If true, spend eligible app tokens before cash.
    pub use_app_tokens: bool,

    /// Exact unsigned RFQ parameters to create.
    pub rfq_params: UnsignedRfqOrderRequest,

    /// Community position being tailed or faded.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub community_pick: Option<CommunityPickRequest>,
}

impl fmt::Debug for CreateUnsignedRfqRequest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("CreateUnsignedRfqRequest")
            .field("privy_token", &"<redacted>")
            .field("use_app_tokens", &self.use_app_tokens)
            .field("rfq_params", &self.rfq_params)
            .field("community_pick", &self.community_pick)
            .finish()
    }
}

/// Parsed leg values with validated enums.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ParsedOrderLeg {
    pub market_id: MarketId,
    pub direction: Direction,
}

/// Errors that can occur while parsing an order leg.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OrderLegParseError {
    InvalidMarketId(u64),
    InvalidDirection(String),
}

/// Errors returned while converting API RFQ request JSON into protocol taker orders.
#[derive(Debug, Clone, PartialEq)]
pub enum RfqOrderJsonError {
    InvalidAddress,
    InvalidMinOdds,
    MissingLegs,
    TooManyLegs { max: usize, actual: usize },
    InvalidOrderType(u8),
    InvalidSignatureFormat,
    InvalidIdempotencyKey,
    InvalidLegMarketId { index: usize, market_id: u64 },
    InvalidLegDirection { index: usize, direction: String },
}

impl fmt::Display for RfqOrderJsonError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidAddress => write!(f, "invalid address"),
            Self::InvalidMinOdds => write!(f, "invalid min odds"),
            Self::MissingLegs => write!(f, "order must include at least one leg"),
            Self::TooManyLegs { max, actual } => {
                write!(f, "order has {actual} legs, maximum is {max}")
            }
            Self::InvalidOrderType(value) => write!(f, "invalid order type {value}"),
            Self::InvalidSignatureFormat => write!(f, "invalid signature format"),
            Self::InvalidIdempotencyKey => write!(f, "invalid idempotency key"),
            Self::InvalidLegMarketId { index, market_id } => {
                write!(f, "invalid market id {market_id} at legs[{index}]")
            }
            Self::InvalidLegDirection { index, direction } => {
                write!(f, "invalid direction {direction:?} at legs[{index}]")
            }
        }
    }
}

impl std::error::Error for RfqOrderJsonError {}

/// Default order type: FOK (Fill-or-Kill) for backwards compatibility.
fn default_order_type() -> u8 {
    2
}

#[inline]
fn direction_to_wire(direction: Direction) -> u8 {
    match direction {
        Direction::Up => 0,
        Direction::Down => 1,
    }
}

fn parse_min_odds_bps(min_odds_decimal: f64) -> Result<u32, RfqOrderJsonError> {
    if !min_odds_decimal.is_finite() {
        return Err(RfqOrderJsonError::InvalidMinOdds);
    }

    let min_odds_bps = (min_odds_decimal * 10_000.0).round();
    if min_odds_bps <= f64::from(Odds::EVEN.0) || min_odds_bps > f64::from(Odds::MAX.0) {
        return Err(RfqOrderJsonError::InvalidMinOdds);
    }

    Ok(min_odds_bps as u32)
}

impl OrderLegJson {
    /// Parse direction string to enum value.
    fn parse_direction(&self) -> Result<Direction, OrderLegParseError> {
        if self.direction.eq_ignore_ascii_case("up") {
            Ok(Direction::Up)
        } else if self.direction.eq_ignore_ascii_case("down") {
            Ok(Direction::Down)
        } else {
            Err(OrderLegParseError::InvalidDirection(self.direction.clone()))
        }
    }

    /// Parse into a validated leg payload.
    pub fn parse(&self) -> Result<ParsedOrderLeg, OrderLegParseError> {
        if self.market_id == 0 {
            return Err(OrderLegParseError::InvalidMarketId(self.market_id));
        }
        Ok(ParsedOrderLeg {
            market_id: MarketId::new(self.market_id),
            direction: self.parse_direction()?,
        })
    }
}

fn parse_order_legs(legs: &[OrderLegJson]) -> Result<Vec<OrderLeg>, RfqOrderJsonError> {
    if legs.is_empty() {
        return Err(RfqOrderJsonError::MissingLegs);
    }
    if legs.len() > SignedOrder::MAX_LEGS {
        return Err(RfqOrderJsonError::TooManyLegs {
            max: SignedOrder::MAX_LEGS,
            actual: legs.len(),
        });
    }

    legs.iter()
        .enumerate()
        .map(|(index, leg)| {
            let parsed = leg.parse().map_err(|err| match err {
                OrderLegParseError::InvalidMarketId(market_id) => {
                    RfqOrderJsonError::InvalidLegMarketId { index, market_id }
                }
                OrderLegParseError::InvalidDirection(direction) => {
                    RfqOrderJsonError::InvalidLegDirection { index, direction }
                }
            })?;
            Ok(OrderLeg {
                market_id: parsed.market_id,
                direction: direction_to_wire(parsed.direction),
            })
        })
        .collect()
}

impl TryFrom<&SignedOrder> for SignedOrderJson {
    type Error = SignedOrderError;

    fn try_from(order: &SignedOrder) -> Result<Self, Self::Error> {
        order.validate_legs()?;
        Ok(Self {
            user: order.user.to_checksum(None),
            wager_micros: order.wager_micros,
            min_odds: order.min_odds_bps as f64 / 10_000.0,
            legs: order
                .legs
                .iter()
                .map(|leg| OrderLegJson {
                    market_id: leg.market_id.as_u64(),
                    direction: match leg.direction {
                        0 => "up",
                        1 => "down",
                        _ => unreachable!("validated above"),
                    }
                    .to_string(),
                })
                .collect(),
            nonce: order.nonce,
            expires_at_ms: order.expires_at_ms,
            order_type: u8::from(order.order_type),
            shield_on: order.shield_on,
            signature: STANDARD.encode(order.signature),
        })
    }
}

impl TryFrom<SignedOrderJson> for SignedOrder {
    type Error = RfqOrderJsonError;

    fn try_from(json: SignedOrderJson) -> Result<Self, Self::Error> {
        let user = json
            .user
            .parse::<Address>()
            .map_err(|_| RfqOrderJsonError::InvalidAddress)?;

        let min_odds_bps = parse_min_odds_bps(json.min_odds)?;
        let legs = parse_order_legs(&json.legs)?;
        let order_type = OrderType::from_u8(json.order_type)
            .ok_or(RfqOrderJsonError::InvalidOrderType(json.order_type))?;

        let mut signature = [0u8; 65];
        let decoded_len = STANDARD
            .decode_slice(json.signature.as_bytes(), &mut signature)
            .map_err(|_| RfqOrderJsonError::InvalidSignatureFormat)?;
        if decoded_len != 65 {
            return Err(RfqOrderJsonError::InvalidSignatureFormat);
        }

        Ok(SignedOrder {
            user,
            wager_micros: json.wager_micros,
            min_odds_bps,
            legs,
            nonce: json.nonce,
            expires_at_ms: json.expires_at_ms,
            order_type,
            shield_on: json.shield_on,
            signature,
        })
    }
}

impl CreateRfqRequest {
    /// Build an RFQ creation request from a signed order.
    pub fn from_signed_order(
        order: &SignedOrder,
        use_app_tokens: bool,
    ) -> Result<Self, SignedOrderError> {
        Ok(Self {
            order: SignedOrderJson::try_from(order)?,
            use_app_tokens,
        })
    }
}

impl UnsignedRfqOrderRequest {
    pub fn parse_idempotency_key(&self) -> Result<Uuid, RfqOrderJsonError> {
        Uuid::parse_str(self.idempotency_key.trim())
            .map_err(|_| RfqOrderJsonError::InvalidIdempotencyKey)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wallet_authentication_message_is_canonical() {
        let auth_address = "0x52908400098527886e0f7030069857d2e4169ee7"
            .parse::<Address>()
            .unwrap();

        let message =
            build_wallet_authentication_message("longshot.xyz", &auth_address, 1_735_430_000_000);

        assert_eq!(
            message,
            "Longshot Wallet Authentication\n\nVersion: 1\nDomain: longshot.xyz\nAuth Address: 0x52908400098527886E0F7030069857D2E4169EE7\nTimestamp: 1735430000000"
        );
    }

    #[test]
    fn wallet_withdrawal_authorization_message_is_canonical() {
        let auth_address = "0x52908400098527886e0f7030069857d2e4169ee7"
            .parse::<Address>()
            .unwrap();
        let destination_address = "0xde709f2102306220921060314715629080e2fb77"
            .parse::<Address>()
            .unwrap();
        let idempotency_key = Uuid::parse_str("550E8400-E29B-41D4-A716-446655440000").unwrap();

        let message = build_wallet_withdrawal_authorization_message(
            "longshot.xyz",
            8453,
            &auth_address,
            &destination_address,
            1_000_000,
            &idempotency_key,
            1_785_529_737_000,
        );

        assert_eq!(
            message,
            "Longshot Withdrawal Authorization\n\nVersion: 1\nDomain: longshot.xyz\nChain ID: 8453\nAuth Address: 0x52908400098527886E0F7030069857D2E4169EE7\nDestination Address: 0xde709f2102306220921060314715629080e2fb77\nAmount Micros: 1000000\nIdempotency Key: 550e8400-e29b-41d4-a716-446655440000\nTimestamp: 1785529737000"
        );
    }

    #[test]
    fn withdrawal_request_uses_tagged_authorization() {
        let request = serde_json::from_value::<UserWithdrawRequest>(serde_json::json!({
            "withdraw_params": {
                "amount_micros": 1_000_000,
                "destination_address": "0xde709f2102306220921060314715629080e2fb77",
                "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
            },
            "authorization": {
                "type": "wallet_signature",
                "signature": STANDARD.encode([7u8; 65]),
                "signed_at_ms": 1_785_529_737_000u64
            }
        }))
        .unwrap();

        assert_eq!(request.withdraw_params.amount_micros, 1_000_000);
        assert_eq!(
            request.authorization,
            WithdrawalAuthorization::WalletSignature {
                signature: STANDARD.encode([7u8; 65]),
                signed_at_ms: 1_785_529_737_000,
            }
        );

        let request = serde_json::from_value::<UserWithdrawRequest>(serde_json::json!({
            "withdraw_params": {
                "amount_micros": 1_000_000,
                "destination_address": "0xde709f2102306220921060314715629080e2fb77",
                "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
            },
            "authorization": {
                "type": "privy_token",
                "token": "privy-token"
            }
        }))
        .unwrap();

        assert_eq!(
            request.authorization,
            WithdrawalAuthorization::PrivyToken {
                token: "privy-token".to_string(),
            }
        );
    }

    #[test]
    fn sensitive_request_debug_redacts_public_tokens() {
        const SECRET: &str = "identity-token-that-must-not-be-logged";

        let wallet_auth = WalletAuthRequest {
            address: "0x0000000000000000000000000000000000000000".to_string(),
            signature: SECRET.to_string(),
            signed_at_ms: 1,
            referral_code: None,
        };
        let withdrawal = WithdrawalAuthorization::PrivyToken {
            token: SECRET.to_string(),
        };
        let unsigned_rfq = CreateUnsignedRfqRequest {
            privy_token: SECRET.to_string(),
            use_app_tokens: false,
            rfq_params: UnsignedRfqOrderRequest {
                wager_micros: 1_000_000,
                min_odds: 2.0,
                legs: vec![OrderLegJson {
                    market_id: 42,
                    direction: "up".to_string(),
                }],
                order_type: 2,
                shield_on: false,
                idempotency_key: "550e8400-e29b-41d4-a716-446655440000".to_string(),
            },
            community_pick: None,
        };

        for debug in [
            format!("{wallet_auth:?}"),
            format!("{withdrawal:?}"),
            format!("{unsigned_rfq:?}"),
        ] {
            assert!(!debug.contains(SECRET));
            assert!(debug.contains("<redacted>"));
        }
    }

    #[test]
    fn signed_order_json_accepts_string_encoded_u64_fields() {
        let json = serde_json::json!({
            "user": "0x0000000000000000000000000000000000000000",
            "wager_micros": "9007199254740993",
            "min_odds": 2.5,
            "legs": [{ "market_id": 42, "direction": "up" }],
            "nonce": "9007199254740994",
            "expires_at_ms": "9007199254740995",
            "order_type": 2,
            "shield_on": false,
            "signature": STANDARD.encode([0u8; 65]),
        });

        let order: SignedOrderJson = serde_json::from_value(json).unwrap();

        assert_eq!(order.wager_micros, 9_007_199_254_740_993);
        assert_eq!(order.nonce, 9_007_199_254_740_994);
        assert_eq!(order.expires_at_ms, 9_007_199_254_740_995);
    }
}
