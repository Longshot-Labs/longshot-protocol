//! API request types.

use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

use crate::taker::{OrderLeg, SignedOrder, SignedOrderError};
use crate::types::{Address, Direction, MarketId, Odds, OrderType, PositionId};

/// Request to create a session from Privy token.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct CreateSessionRequest {
    /// Privy JWT supplied by the client.
    pub privy_token: String,

    /// Linked EVM wallet selected by the completed Privy authentication flow.
    /// The server accepts this untrusted hint only when it matches the verified
    /// identity token's linked-account claims.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub auth_wallet_address: Option<String>,

    /// Referral slug used for signup attribution.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub referral_code: Option<String>,
}

/// Request to verify or idempotently start embedded-wallet provisioning.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct CreateEmbeddedWalletEnsureRequest {
    pub privy_token: String,
}

/// Referral prompt whose eligibility should be leased or acknowledged.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ReferralPromptRequest {
    PostWin,
    FirstPick,
}

/// Request a short lease for an eligible referral prompt.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct ClaimReferralPromptRequest {
    pub prompt: ReferralPromptRequest,
}

/// Complete or release a leased referral prompt.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct AcknowledgeReferralPromptRequest {
    pub prompt: ReferralPromptRequest,
    pub claim_token: Uuid,
    /// True after presentation; false releases an unshown lease for retry.
    pub shown: bool,
}

/// Authenticated request to post a GIPHY GIF to chat.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct ChatPostGifRequest {
    pub gif_id: String,
    pub chat_id: Option<String>,
    pub parent: Option<String>,
}

/// Request to authenticate with direct wallet signature.
#[derive(Debug, Serialize, Deserialize)]
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

    /// Referral slug used for signup attribution.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub referral_code: Option<String>,
}

/// Prospective order priced by the live maker pipeline without execution.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct RfqEstimateRequest {
    /// Prospective wager size in micros.
    pub wager_micros: u64,
    /// Order legs to price.
    pub legs: Vec<OrderLegJson>,
    /// Price the order without sharing taker identity with makers.
    #[serde(default)]
    pub shield_on: bool,
}

/// One correlated single-contract estimate in a bounded indicative batch.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct RfqEstimateBatchItemRequest {
    /// Caller-defined correlation key, unique within the batch.
    #[cfg_attr(feature = "openapi", schema(max_length = 80))]
    pub key: String,
    /// Exactly one market/direction contract to quote.
    pub leg: OrderLegJson,
}

/// Bounded batch of independent single-leg indicative RFQ estimates.
///
/// Every item uses the same probe wager so both sides of several contracts can
/// be compared consistently. The handler processes each item independently.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct RfqEstimateBatchRequest {
    pub wager_micros: u64,
    pub estimates: Vec<RfqEstimateBatchItemRequest>,
    #[serde(default)]
    pub shield_on: bool,
}

/// Authenticated request to post a chat message.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "body": "hello chat",
    "chat_id": null,
    "parent": null
})))]
#[serde(deny_unknown_fields)]
pub struct ChatPostMessageRequest {
    #[cfg_attr(feature = "openapi", schema(max_length = 500, example = "hello chat"))]
    pub body: String,
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub chat_id: Option<String>,
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub parent: Option<String>,
}

/// Authenticated request to edit a chat message body.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "chat_id": null,
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "body": "edited chat"
})))]
#[serde(deny_unknown_fields)]
pub struct ChatEditMessageRequest {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub chat_id: Option<String>,
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub message_id: String,
    #[cfg_attr(feature = "openapi", schema(max_length = 500, example = "edited chat"))]
    pub body: String,
}

/// Authenticated request to add an emoji reaction to a chat message.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "chat_id": null,
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "emoji_code": ":rocket:"
})))]
#[serde(deny_unknown_fields)]
pub struct ChatEmojiReactRequest {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub chat_id: Option<String>,
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub message_id: String,
    #[cfg_attr(feature = "openapi", schema(example = ":rocket:"))]
    pub emoji_code: String,
}

/// Query parameters for the authenticated chat SSE stream.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct ChatStreamQuery {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub chat_id: Option<String>,
}

/// Query parameters for `GET /v1/chat/mention_candidates`.
///
/// The SSE stream permits the main room by omitting `chat_id`, but mention
/// candidates are always room-scoped. Keep this route-specific client contract
/// required even though the server reuses a permissive raw extractor.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct ChatMentionCandidatesQuery {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub chat_id: String,
}

/// Query parameters for the authenticated recent chat messages endpoint.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct ChatRecentMessagesQuery {
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub chat_id: Option<String>,
    #[cfg_attr(feature = "openapi", schema(example = 100, minimum = 1))]
    pub limit: Option<u32>,
    #[cfg_attr(feature = "openapi", schema(example = "eyJiZWZvcmVfc2VxIjoxMjN9"))]
    pub before: Option<String>,
}

/// Request to set the authenticated user's referrer by referral code.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "referral_code": "jyrtx2"
})))]
#[serde(deny_unknown_fields)]
pub struct UserSetReferrerRequest {
    /// Vanity referral code of the referrer (lowercase alphanumeric, 4-16).
    #[cfg_attr(feature = "openapi", schema(value_type = String, example = "jyrtx2"))]
    pub referral_code: String,
}

/// Request for the authenticated user to create their own vanity referral code.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({ "code": "jyrtx2" })))]
#[serde(deny_unknown_fields)]
pub struct UserCreateReferralCodeRequest {
    /// Desired referral code. Must be 4-16 lowercase alphanumeric chars.
    /// Mixed-case input is normalized to lowercase.
    #[cfg_attr(feature = "openapi", schema(value_type = String, example = "jyrtx2"))]
    pub code: String,
}

/// User contest-bet selection entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PlaceContestBetSelectionRequest {
    pub market_id: u64,
    #[cfg_attr(feature = "openapi", schema(example = "up"))]
    pub direction: String,
}

/// User contest-bet request.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PlaceContestBetRequest {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub contest_id: String,
    /// If true, spend eligible app tokens before cash.
    pub use_app_tokens: bool,
    /// Stable zero-based entry slot. Optional for legacy single-entry and
    /// non-Survivor requests. For a new opening-round entry in a multi-entry
    /// Survivor contest, send the next contiguous index; reuse that same index
    /// for void replacements and later rounds.
    #[serde(default)]
    pub entry_index: Option<u32>,
    pub bets: Vec<PlaceContestBetSelectionRequest>,
    /// Roster contests only: exactly one pick per tier. Mutually exclusive
    /// with `bets` (which must be empty).
    #[serde(default)]
    pub roster_picks: Option<Vec<PlaceRosterPickRequest>>,
    #[serde(default)]
    pub tiebreaker_guess: Option<i64>,
}

/// A roster pick: one selection in one tier.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(deny_unknown_fields)]
pub struct PlaceRosterPickRequest {
    pub tier_index: u16,
    pub selection_index: u16,
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

/// Request to move funds from available app balance into the vault.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "vault_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount_micros": 1000000,
    "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
})))]
#[serde(deny_unknown_fields)]
pub struct UserDepositVaultRequest {
    /// Vault user ID to deposit into.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub vault_id: String,
    /// Amount to move from the user's available balance into the vault, in USDC micros.
    #[cfg_attr(feature = "openapi", schema(example = 1000000, minimum = 1))]
    pub amount_micros: u64,
    /// Client-supplied idempotency key scoped to the depositing LP identity.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
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
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
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

/// Tagged wire format for vault withdrawal requests.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum VaultWithdrawalAmountRequest {
    Full {
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
        vault_id: String,
    },
    Partial {
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
        vault_id: String,
        #[cfg_attr(feature = "openapi", schema(example = 1000000, minimum = 1))]
        amount_micros: u64,
    },
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
/// - `min_odds` → `min_odds_bps` (multiply by 10,000)
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
    #[cfg_attr(feature = "openapi", schema(example = 100000000))]
    pub wager_micros: u64,

    /// Minimum acceptable odds (e.g., 2.5 = 2.5x).
    #[cfg_attr(feature = "openapi", schema(example = 2.5))]
    pub min_odds: f64,

    /// Order legs (1-9 legs supported).
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

/// Unsigned RFQ order parameters, before adding the prepare token required for creation.
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
    #[cfg_attr(feature = "openapi", schema(example = 100000000))]
    pub wager_micros: u64,

    /// Minimum acceptable odds (e.g., 2.5 = 2.5x).
    #[cfg_attr(feature = "openapi", schema(example = 2.5))]
    pub min_odds: f64,

    /// Order legs (1-9 legs supported).
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
#[derive(Debug, Serialize, Deserialize)]
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

/// Parsed leg values with validated enums.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
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

    pub fn into_signed_order_for_session(
        self,
        user: Address,
        nonce: u64,
        expires_at_ms: u64,
    ) -> Result<SignedOrder, RfqOrderJsonError> {
        let min_odds_bps = parse_min_odds_bps(self.min_odds)?;
        let legs = parse_order_legs(&self.legs)?;
        let order_type = OrderType::from_u8(self.order_type)
            .ok_or(RfqOrderJsonError::InvalidOrderType(self.order_type))?;

        Ok(SignedOrder {
            user,
            wager_micros: self.wager_micros,
            min_odds_bps,
            legs,
            nonce,
            expires_at_ms,
            order_type,
            shield_on: self.shield_on,
            signature: [0u8; 65],
        })
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

    #[test]
    fn contest_entry_index_remains_wire_optional() {
        let request: PlaceContestBetRequest = serde_json::from_value(serde_json::json!({
            "contest_id": "550e8400-e29b-41d4-a716-446655440000",
            "use_app_tokens": false,
            "bets": [{ "market_id": 42, "direction": "up" }]
        }))
        .unwrap();

        assert_eq!(request.entry_index, None);
    }

    #[cfg(feature = "openapi")]
    #[test]
    fn contest_entry_index_openapi_documents_survivor_contract() {
        use utoipa::ToSchema;

        let (_, schema) = PlaceContestBetRequest::schema();
        let schema = serde_json::to_value(schema).unwrap();
        let description = schema["properties"]["entry_index"]["description"]
            .as_str()
            .unwrap();
        assert!(description.contains("next contiguous index"));
        assert!(description.contains("reuse that same index"));
        assert!(!schema["required"]
            .as_array()
            .unwrap()
            .contains(&serde_json::json!("entry_index")));
    }

    #[cfg(feature = "openapi")]
    #[test]
    fn chat_message_request_body_openapi_limits_match_server_limit() {
        assert_body_max_length::<ChatPostMessageRequest>(500);
        assert_body_max_length::<ChatEditMessageRequest>(500);
    }

    #[cfg(feature = "openapi")]
    fn assert_body_max_length<T>(expected: u64)
    where
        T: utoipa::ToSchema<'static>,
    {
        let (_, schema) = T::schema();
        let schema = serde_json::to_value(schema).unwrap();
        let body_max_length = schema
            .pointer("/properties/body/maxLength")
            .and_then(serde_json::Value::as_u64);

        assert_eq!(body_max_length, Some(expected));
    }
}
