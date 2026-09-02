//! API response types.

use std::fmt;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct AccessResponse {
    pub position_opening_allowed: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason_code: Option<String>,
}

impl AccessResponse {
    /// Create an access response while accepting borrowed or owned reason codes.
    pub fn new<S>(position_opening_allowed: bool, reason_code: Option<S>) -> Self
    where
        S: Into<String>,
    {
        Self {
            position_opening_allowed,
            reason_code: reason_code.map(Into::into),
        }
    }
}

/// Response after successful session creation.
#[derive(Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "session_token": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "deposit_address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "deposit_chain_id": 84532,
    "user_id": "8d3f6b4a-a79a-4b4d-8e38-64c2d8f7b9a1",
    "expires_at": 1735516400,
    "account_created": true
})))]
pub struct SessionResponse {
    /// Bearer token for authenticated API requests.
    pub session_token: String,

    /// User's wallet address.
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub address: String,

    /// EVM wallet that authenticated or controls this account. This may differ
    /// from `address` for custodial Privy sessions.
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x1111111111111111111111111111111111111111")
    )]
    pub auth_wallet_address: String,

    /// Longshot-controlled deposit wallet address for this user.
    #[serde(skip_serializing_if = "Option::is_none")]
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub deposit_address: Option<String>,

    /// EVM chain ID for the deposit wallet, when custodial deposits are enabled.
    #[serde(skip_serializing_if = "Option::is_none")]
    #[cfg_attr(feature = "openapi", schema(example = 84532))]
    pub deposit_chain_id: Option<i64>,

    /// Stable Longshot user ID, encoded as a UUID string.
    #[cfg_attr(
        feature = "openapi",
        schema(example = "8d3f6b4a-a79a-4b4d-8e38-64c2d8f7b9a1")
    )]
    pub user_id: String,

    /// Session expiry (Unix timestamp in seconds).
    #[cfg_attr(feature = "openapi", schema(example = 1735516400))]
    pub expires_at: u64,

    /// True only when this request's provisioning transaction created the
    /// user account; false for sessions resolved onto an existing account.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required, default = false))]
    pub account_created: bool,
}

impl fmt::Debug for SessionResponse {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("SessionResponse")
            .field("session_token", &"<redacted>")
            .field("address", &self.address)
            .field("auth_wallet_address", &self.auth_wallet_address)
            .field("deposit_address", &self.deposit_address)
            .field("deposit_chain_id", &self.deposit_chain_id)
            .field("user_id", &self.user_id)
            .field("expires_at", &self.expires_at)
            .field("account_created", &self.account_created)
            .finish()
    }
}

/// RFQ lifecycle status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum RfqStatus {
    Pending,
    Finalizing,
    Completed,
    Failed,
    Cancelled,
    Timeout,
}

/// RFQ response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "odds": 2.5,
    "payout_micros": "250000000",
    "quotes_received": 3
})))]
pub struct RfqResponse {
    /// Request ID (UUID).
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub request_id: Uuid,

    /// Status: "pending", "finalizing", "completed", "failed", "cancelled", "timeout".
    #[cfg_attr(feature = "openapi", schema(example = "completed"))]
    pub status: RfqStatus,

    /// Effective odds (if filled), e.g., 2.5 for 2.5x.
    /// Non-finite values are omitted at serialization boundaries.
    #[serde(skip_serializing_if = "odds_is_none_or_non_finite")]
    #[cfg_attr(feature = "openapi", schema(example = 2.5))]
    pub odds: Option<f64>,

    /// Expected payout in micros (if filled).
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        with = "crate::api::wire_int::option_u64_string"
    )]
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "int64", example = "250000000"))]
    pub payout_micros: Option<u64>,

    /// Error message (if failed).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,

    /// Number of quotes received.
    #[cfg_attr(feature = "openapi", schema(example = 3))]
    pub quotes_received: u32,
}

fn odds_is_none_or_non_finite(odds: &Option<f64>) -> bool {
    match odds {
        Some(value) => !value.is_finite(),
        None => true,
    }
}

/// Cancel response.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "cancelled": true,
    "message": "RFQ cancelled"
})))]
pub struct CancelResponse {
    /// Request ID.
    #[cfg_attr(
        feature = "openapi",
        schema(example = "550e8400-e29b-41d4-a716-446655440000")
    )]
    pub request_id: String,

    /// Whether cancellation succeeded.
    pub cancelled: bool,

    /// Status message.
    #[cfg_attr(feature = "openapi", schema(example = "RFQ cancelled"))]
    pub message: String,
}

/// Current odds estimate for a prospective RFQ. The estimate reflects the odds
/// the caller would receive by submitting the same order now; nothing is
/// reserved or executed.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RfqEstimateResponse {
    /// Server-generated estimate request ID (UUID).
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub request_id: Uuid,
    /// True when the collected quotes fully cover the requested wager.
    pub quotable: bool,
    /// Estimated decimal odds multiplier (e.g. 2.5 = 2.5x). Present whenever
    /// at least one quote was collected, even if the wager is only partially
    /// fillable.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub odds: Option<f64>,
    /// Wager amount (micros) the collected quotes could fill.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fillable_micros: Option<u64>,
    /// Number of maker quotes collected for this estimate.
    pub quotes_received: u32,
    /// Wall-clock time (ms) the estimate completed.
    pub quoted_at_ms: u64,
    /// Why the order is not (fully) quotable: `no_quotes`,
    /// `insufficient_liquidity`, `profit_exceeds_maximum`, `no_valid_quotes`,
    /// `estimate_timeout`, or `sports_combination_unsupported`.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}

/// Minimal RFQ lifecycle response for authenticated market makers.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MmRfqStatusResponse {
    /// RFQ request ID (UUID).
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub request_id: String,
    /// Current persisted RFQ lifecycle status.
    pub status: RfqStatus,
}

/// Available cash balance plus the funding policy needed by clients.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserAvailableBalanceResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "1000000")
    )]
    pub available_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "500000")
    )]
    pub pending_custodial_deposit_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "5000000")
    )]
    pub credited_custodial_deposit_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "1000000")
    )]
    pub deposit_withdrawal_min_micros: u64,
}

/// Response after successfully crediting a user deposit.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "amount_micros": "1000000",
    "operation_id": "550e8400-e29b-41d4-a716-446655440000",
    "tx_hash": "0xabc123"
})))]
pub struct UserDepositResponse {
    /// Amount posted from the user's settlement balance, in USDC micros.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "1000000"))]
    pub amount_micros: u64,

    /// Operation ID used for idempotency/recovery correlation.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub operation_id: Uuid,

    /// Transaction hash for the successful `LongshotSettlement.deposit()` or
    /// `LongshotSettlement.protocolDeposit()` call.
    #[cfg_attr(feature = "openapi", schema(example = "0xabc123"))]
    pub tx_hash: String,
}

/// Deposit wallet metadata for the signed-in user.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "chain_id": 84532,
    "token_symbol": "USDC",
    "token_decimals": 6
})))]
pub struct UserDepositWalletResponse {
    /// Longshot-controlled wallet address for user deposits.
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub address: String,

    /// EVM chain ID for this deposit wallet.
    #[cfg_attr(feature = "openapi", schema(example = 84532))]
    pub chain_id: i64,

    /// Token users should send to this deposit wallet.
    #[cfg_attr(feature = "openapi", schema(example = "USDC"))]
    pub token_symbol: String,

    /// Token decimals.
    #[cfg_attr(feature = "openapi", schema(example = 6))]
    pub token_decimals: u8,
}

/// Response after successfully debiting app balance and withdrawing to settlement.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "amount_micros": "1000000",
    "operation_id": "550e8400-e29b-41d4-a716-446655440000",
    "destination_address": "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1",
    "tx_hash": "0xabc123"
})))]
pub struct UserWithdrawResponse {
    /// Amount withdrawn back into the user's settlement balance, in USDC micros.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "1000000"))]
    pub amount_micros: u64,

    /// Operation ID used for idempotency/recovery correlation.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub operation_id: Uuid,

    /// EVM address that received the withdrawn USDC.
    #[serde(skip_serializing_if = "Option::is_none")]
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub destination_address: Option<String>,

    /// Transaction hash for the successful `LongshotSettlement.withdraw()` or
    /// `LongshotSettlement.protocolWithdraw()` call.
    #[cfg_attr(feature = "openapi", schema(example = "0xabc123"))]
    pub tx_hash: String,
}

/// Durable status for a balance operation that may still be finalized by recovery.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum BalanceOperationStatus {
    Pending,
    Failed,
    Success,
    Recovering,
}

/// Response for an existing or asynchronously recoverable balance operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct BalanceOperationStatusResponse {
    /// Amount associated with the operation, in USDC micros.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "1000000"))]
    pub amount_micros: u64,

    /// Operation ID used for idempotency/recovery correlation.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000"))]
    pub operation_id: Uuid,

    /// Current durable operation status.
    #[cfg_attr(feature = "openapi", schema(example = "pending"))]
    pub status: BalanceOperationStatus,

    /// Destination/source wallet address associated with the balance operation.
    #[serde(skip_serializing_if = "Option::is_none")]
    #[cfg_attr(
        feature = "openapi",
        schema(example = "0x742d35cC6634C0532925A3B844Bc9e7595F8B2A1")
    )]
    pub wallet_address: Option<String>,
}

/// Delivery status returned when a newly submitted withdrawal is queued onchain.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum WithdrawalDeliveryStatus {
    Queued,
}

/// First-attempt response for a withdrawal accepted into the onchain queue.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct QueuedWithdrawalResponse {
    /// Amount committed to the onchain withdrawal queue, in USDC micros.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "1000000")
    )]
    pub amount_micros: u64,
    /// Operation ID used for idempotency and recovery correlation.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub operation_id: Uuid,
    /// EVM address that will receive the queued USDC.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub destination_address: Option<String>,
    /// Confirmed onchain delivery disposition for this submission attempt.
    pub delivery_status: WithdrawalDeliveryStatus,
}

/// Response for a withdrawal accepted without immediate delivery.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(untagged)]
pub enum AcceptedWithdrawOperationResponse {
    Queued(QueuedWithdrawalResponse),
    Recovery(BalanceOperationStatusResponse),
}

/// Response for deposit endpoints.
///
/// Freshly completed operations return a `UserDepositResponse` with a tx hash.
/// Idempotency replays and asynchronous recovery paths return a durable
/// operation status response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(untagged)]
pub enum DepositOperationResponse {
    Completed(UserDepositResponse),
    OperationStatus(BalanceOperationStatusResponse),
}

/// Response for withdrawal endpoints.
///
/// Freshly completed operations return a `UserWithdrawResponse` with a tx hash.
/// Idempotency replays and asynchronous recovery paths return a durable
/// operation status response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(untagged)]
pub enum WithdrawOperationResponse {
    Completed(UserWithdrawResponse),
    OperationStatus(BalanceOperationStatusResponse),
}

/// Response containing the user's currently reserved balance.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "reserved_micros": "250000"
})))]
pub struct ReservedBalanceResponse {
    /// Currently reserved user balance in USDC micros.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "250000"))]
    pub reserved_micros: u64,
}

/// User-facing transaction category.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum UserTransactionCategory {
    Deposit,
    Withdrawal,
    Credits,
    Market,
    Contest,
}

/// User-facing transaction status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum UserTransactionStatus {
    Completed,
    Pending,
    Failed,
    Expired,
    Entered,
    Won,
}

/// Unit used by a transaction amount.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum UserTransactionUnit {
    Usdc,
    Credits,
}

/// Funding sources combined into a transaction.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum UserTransactionFunding {
    Cash,
    Credits,
    CashAndCredits,
}

/// One user-facing transaction-history row.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserTransactionResponse {
    /// Stable opaque identifier for this user-visible transaction row.
    pub id: String,
    pub category: UserTransactionCategory,
    pub title: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
    pub status: UserTransactionStatus,
    pub occurred_at_ms: i64,
    /// Signed amount in micros: positive = money in, negative = money out.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub amount_micros: i64,
    pub unit: UserTransactionUnit,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub funding: Option<UserTransactionFunding>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub network: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub wallet_address: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tx_hash: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expires_at_ms: Option<i64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reference: Option<String>,
}

/// Paginated user transaction-history response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserTransactionsResponse {
    pub items: Vec<UserTransactionResponse>,
    /// Opaque keyset cursor. Clients must key "done" off this being absent,
    /// not off short pages: category filters can legitimately return fewer
    /// than `limit` items while more pages remain.
    pub next_cursor: Option<String>,
}

/// User tier identifier for fee display.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum FeeScheduleTier {
    Standard,
    Silver,
    Gold,
    Platinum,
    Vip,
}

/// Fee rate entry for a single tier.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct TierFeeRate {
    /// Tier name.
    pub tier: FeeScheduleTier,
    /// Parlay (multi-leg) fee rate in basis points.
    #[cfg_attr(feature = "openapi", schema(example = 250))]
    pub parlay_fee_bps: u32,
}

/// Fee schedule for the authenticated user.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "user_tier": "standard",
    "parlay_fee_bps": 250,
    "spot_fee_bps": 75,
    "bonding_spot_fee_bps": 25,
    "shield_fee_multiplier": 2,
    "tiers": [
        { "tier": "standard", "parlay_fee_bps": 250 },
        { "tier": "silver", "parlay_fee_bps": 200 },
        { "tier": "gold", "parlay_fee_bps": 175 },
        { "tier": "platinum", "parlay_fee_bps": 150 },
        { "tier": "vip", "parlay_fee_bps": 100 }
    ]
})))]
pub struct FeeScheduleResponse {
    /// User's current tier.
    pub user_tier: FeeScheduleTier,

    /// Parlay fee rate (multi-leg) for the user's tier, in basis points.
    #[cfg_attr(feature = "openapi", schema(example = 250))]
    pub parlay_fee_bps: u32,

    /// Spot fee rate (single-leg, below bonding threshold) in basis points.
    /// Same for all tiers.
    #[cfg_attr(feature = "openapi", schema(example = 75))]
    pub spot_fee_bps: u32,

    /// Spot fee rate (single-leg, at or above bonding odds threshold) in basis points.
    /// Same for all tiers.
    #[cfg_attr(feature = "openapi", schema(example = 25))]
    pub bonding_spot_fee_bps: u32,

    /// Multiplier applied to all fees when shield is enabled (e.g., 2 means 2x fees).
    #[cfg_attr(feature = "openapi", schema(example = 2))]
    pub shield_fee_multiplier: u32,

    /// Full fee schedule across all tiers (for display).
    pub tiers: Vec<TierFeeRate>,
}

/// Public status of a referral link.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum PublicReferralStatusResponse {
    Valid,
    Redeemed,
    Expired,
}

/// Public identity of the inviter behind a referral link.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicReferralInviterResponse {
    pub display_name: String,
    pub avatar_seed: i32,
    pub avatar_url: Option<String>,
}

/// Deposit-match offer configured for a referral link. The opportunity is
/// granted only by atomic Privy signup with a linked X account; direct wallet
/// signup and later referral attribution intentionally do not qualify.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicReferralDepositMatchOffer {
    /// Maximum matched amount in USD micros, as a decimal string.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "10000000")
    )]
    pub match_limit_micros: i64,
    /// Validity window of the granted opportunity in milliseconds.
    #[cfg_attr(feature = "openapi", schema(example = 2592000000i64, minimum = 1))]
    pub duration_ms: i64,
}

/// Public referral-link state.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicReferralCodeResponse {
    pub status: PublicReferralStatusResponse,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub inviter: Option<PublicReferralInviterResponse>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub deposit_match: Option<PublicReferralDepositMatchOffer>,
}

/// Error response.
#[derive(Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "error": "Invalid session token",
    "code": "INVALID_SESSION",
    "details": null
})))]
pub struct ErrorResponse {
    /// Human-readable error message.
    #[cfg_attr(feature = "openapi", schema(example = "Invalid session token"))]
    pub error: String,

    /// Error code for programmatic handling.
    #[cfg_attr(feature = "openapi", schema(example = "INVALID_SESSION"))]
    pub code: String,

    /// Additional details (optional).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<String>,
}

impl ErrorResponse {
    /// Create a new error response.
    pub fn new(error: impl Into<String>, code: impl Into<String>) -> Self {
        Self {
            error: error.into(),
            code: code.into(),
            details: None,
        }
    }

    /// Add details.
    pub fn with_details(mut self, details: impl Into<String>) -> Self {
        self.details = Some(details.into());
        self
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::{AccessResponse, SessionResponse};

    #[test]
    fn access_response_new_accepts_borrowed_reason_code() {
        let response = AccessResponse::new(false, Some("GEO_BLOCKED"));

        assert!(!response.position_opening_allowed);
        assert_eq!(response.reason_code.as_deref(), Some("GEO_BLOCKED"));
    }

    #[test]
    fn session_response_defaults_compatible_fields_and_redacts_secrets() {
        let compatible: SessionResponse = serde_json::from_value(json!({
            "session_token": "compatible-token",
            "address": "0x0000000000000000000000000000000000000000",
            "auth_wallet_address": "0x1111111111111111111111111111111111111111",
            "user_id": "user-1",
            "expires_at": 123
        }))
        .expect("deserialize compatible session response");

        assert!(!compatible.account_created);
        let debug = format!("{compatible:?}");
        assert!(!debug.contains("compatible-token"));
        assert!(debug.contains("<redacted>"));
    }
}
