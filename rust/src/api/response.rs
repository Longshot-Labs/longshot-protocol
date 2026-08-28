//! API response types.

use std::fmt;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use uuid::Uuid;

use super::{markets::EventMarketSource, portfolio::LegDetail};
use crate::types::{MarketStatus, MarketType, Outcome, TradingChannel};

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
    "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

    /// Durable server-owned onboarding state used for client routing.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required, default = false))]
    pub onboarding_completed: bool,
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
            .field("onboarding_completed", &self.onboarding_completed)
            .finish()
    }
}

/// Embedded-wallet provisioning state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum EmbeddedWalletEnsureStatus {
    Ready,
    Pending,
    NotRequired,
}

/// Result of the side-effect-isolated embedded-wallet ensure endpoint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct EmbeddedWalletEnsureResponse {
    pub status: EmbeddedWalletEnsureStatus,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub wallet_address: Option<String>,
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

/// Live maker-pipeline estimate for a prospective RFQ.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RfqEstimateResponse {
    pub request_id: Uuid,
    pub quotable: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub odds: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fillable_micros: Option<u64>,
    pub quotes_received: u32,
    pub quoted_at_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}

/// Availability of one item in an indicative estimate batch.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum RfqEstimateBatchItemStatus {
    Quoted,
    Unavailable,
}

/// Correlated result for one independently priced contract.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RfqEstimateBatchItemResponse {
    pub key: String,
    pub market_id: u64,
    pub direction: String,
    pub status: RfqEstimateBatchItemStatus,
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "uuid", nullable = true)
    )]
    pub request_id: Option<Uuid>,
    pub quotable: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub odds: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub fillable_micros: Option<u64>,
    pub quotes_received: u32,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub quoted_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reason: Option<String>,
}

/// Results for a bounded batch of independent indicative estimates.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct RfqEstimateBatchResponse {
    pub wager_micros: u64,
    pub estimates: Vec<RfqEstimateBatchItemResponse>,
}

/// Minimal RFQ lifecycle response for authenticated market makers.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MmRfqStatusResponse {
    pub request_id: String,
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

    /// EVM chain ID for this deposit wallet, when configured.
    #[serde(skip_serializing_if = "Option::is_none")]
    #[cfg_attr(feature = "openapi", schema(example = 84532))]
    pub chain_id: Option<i64>,

    /// Token users should send to this deposit wallet.
    #[cfg_attr(feature = "openapi", schema(example = "USDC"))]
    pub token_symbol: String,

    /// Token decimals.
    #[cfg_attr(feature = "openapi", schema(example = 6))]
    pub token_decimals: u8,
}

/// Response after successfully moving available app balance into the vault.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({})))]
pub struct UserDepositVaultResponse {}

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

/// Delivery status returned when a newly submitted withdrawal is queued.
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
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "1000000")
    )]
    pub amount_micros: u64,
    pub operation_id: Uuid,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub destination_address: Option<String>,
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

/// Response after successfully queueing a vault withdrawal request.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "queued": true
})))]
pub struct UserRequestWithdrawalVaultResponse {
    pub queued: bool,
}

/// Response after successfully claiming vault manager fees.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "claimed_micros": "1000000"
})))]
pub struct VaultClaimFeesResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "1000000"))]
    pub claimed_micros: u64,
}

/// Tagged wire format for vault withdrawal amounts exposed over the API.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum VaultWithdrawalAmountResponse {
    Full,
    Partial {
        #[serde(with = "crate::api::wire_int::u64_string")]
        #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "500000"))]
        amount_micros: u64,
    },
}

/// Queue entry returned by the vault withdrawal-queue API.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "requested_amount": {
        "type": "partial",
        "amount_micros": "500000"
    },
    "withdrawal_time_ms": 1712345978901_u64
})))]
pub struct PendingVaultWithdrawalResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    pub requested_amount: VaultWithdrawalAmountResponse,
    pub withdrawal_time_ms: u64,
}

/// Response containing the persisted vault withdrawal queue.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "withdrawal_queue": [{
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "requested_amount": {
            "type": "full"
        },
        "withdrawal_time_ms": 1712345678901_u64
    }]
})))]
pub struct VaultWithdrawalQueueResponse {
    pub withdrawal_queue: Vec<PendingVaultWithdrawalResponse>,
}

/// Liquidity-provider share exposed by vault APIs.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "liquidity_micros": "250000"
})))]
pub struct VaultLiquidityProviderResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "250000"))]
    pub liquidity_micros: u64,
}

/// Vault snapshot attached to a position response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "total_deposit_micros": "500000",
    "liquidity_providers": [{
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "liquidity_micros": "500000"
    }]
})))]
pub struct PositionVaultResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "500000"))]
    pub total_deposit_micros: u64,
    pub liquidity_providers: Vec<VaultLiquidityProviderResponse>,
}

/// Wrapped response for a vault position-vault read.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "position_vault": {
        "total_deposit_micros": "500000",
        "liquidity_providers": [{
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "liquidity_micros": "500000"
        }]
    }
})))]
pub struct VaultPositionVaultResponse {
    pub position_vault: PositionVaultResponse,
}

/// Vault configuration timings and limits.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "max_position_value_bps": 8000,
    "min_deposit_age_ms": 0,
    "withdrawal_window_ms": 0,
    "binary_event_utilization_cap_bps": 10000,
    "price_strike_utilization_cap_bps": 10000,
    "vault_manager_fee_bps": 1000,
    "external_deposits_enabled": true,
    "making_enabled": true,
    "taking_enabled": true,
    "fee_receiver": "550e8400-e29b-41d4-a716-446655440000"
})))]
pub struct VaultConfigsResponse {
    pub max_position_value_bps: u32,
    pub min_deposit_age_ms: u64,
    pub withdrawal_window_ms: u64,
    pub binary_event_utilization_cap_bps: u32,
    pub price_strike_utilization_cap_bps: u32,
    pub vault_manager_fee_bps: u32,
    pub external_deposits_enabled: bool,
    pub making_enabled: bool,
    pub taking_enabled: bool,
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid", nullable = true))]
    pub fee_receiver: Option<String>,
}

/// Aggregate vault liquidity bucket.
///
/// Public vault overview responses expose vault-wide totals only. Caller-level
/// allocation details are available from authenticated user vault endpoints.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "total_deposit_micros": "500000"
})))]
pub struct VaultAmountResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "500000"))]
    pub total_deposit_micros: u64,
}

/// Provider-free vault amount.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "amount_micros": "500000"
})))]
pub struct VaultAggregateAmountResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "500000"))]
    pub amount_micros: u64,
}

/// Public vault overview.
///
/// This response contains aggregate vault state. Caller-specific fields such as
/// `latest_deposit_time_ms` and `pending_withdrawal` are returned by the
/// authenticated `GET /v1/user/vault/performance` endpoint.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "configs": {
        "max_position_value_bps": 8000
    },
    "unallocated": {
        "total_deposit_micros": "500000"
    },
    "allocated": {
        "total_deposit_micros": "0"
    },
    "binary_event_allocation": {
        "amount_micros": "0"
    },
    "price_strike_allocation": {
        "amount_micros": "0"
    },
    "total_fees": {
        "amount_micros": "0"
    },
    "unclaimed_fees": {
        "amount_micros": "0"
    }
})))]
pub struct VaultResponse {
    pub configs: VaultConfigsResponse,
    pub unallocated: VaultAmountResponse,
    pub allocated: VaultAmountResponse,
    pub binary_event_allocation: VaultAggregateAmountResponse,
    pub price_strike_allocation: VaultAggregateAmountResponse,
    pub total_fees: VaultAggregateAmountResponse,
    pub unclaimed_fees: VaultAggregateAmountResponse,
}

/// Aggregate stats for a vault, backing the vault screen header.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "tvl_micros": "1000000",
    "allocated_micros": "300000",
    "unallocated_micros": "700000",
    "all_time_pnl_micros": "50000",
    "trading_volume_micros": "500000",
    "past_month_apr_bps": 1_200,
    "all_time_apr_bps": 1_800
})))]
pub struct VaultStatsResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "1000000"))]
    pub tvl_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "300000"))]
    pub allocated_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "700000"))]
    pub unallocated_micros: u64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "50000"))]
    pub all_time_pnl_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "500000"))]
    pub trading_volume_micros: i64,
    pub past_month_apr_bps: i64,
    pub all_time_apr_bps: i64,
}

/// Single point on the vault's PnL / account-value time series.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct VaultPnlHistoryPoint {
    /// End-of-day timestamp in unix milliseconds.
    pub t_ms: i64,
    /// Cumulative metric value in micros as of `t_ms`.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "5000"))]
    pub value_micros: i64,
}

/// Time series returned by `GET /v1/vault/pnl_history`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "series": [
        { "t_ms": 1_712_448_000_000_i64, "value_micros": "0" },
        { "t_ms": 1_712_534_400_000_i64, "value_micros": "5000" }
    ]
})))]
pub struct VaultPnlHistoryResponse {
    pub series: Vec<VaultPnlHistoryPoint>,
}

/// Row in the paginated vault positions listing.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct VaultPositionResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub position_id: String,
    pub legs_summary: String,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    pub multiplier_bps: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub potential_payout_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub mark_value_micros: i64,
    pub created_at_ms: i64,
    #[cfg_attr(feature = "openapi", schema(nullable = true))]
    pub resolved_at_ms: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct VaultPositionsResponse {
    pub items: Vec<VaultPositionResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

/// Public detail for a vault-backed position.
///
/// Served by unauthenticated `GET /v1/vault/positions/{id}` for vault-backed
/// positions. Contains only fields intended for the public vault view.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicVaultPositionDetailResponse {
    /// Position ID.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub id: String,
    /// Taker wager amount in micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub wager_micros: i64,
    /// Gross potential payout in micros before fees.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub payout_micros: i64,
    /// Realized net payout in micros after fees.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", required)
    )]
    pub net_payout_micros: Option<i64>,
    pub legs_count: i16,
    pub legs_summary: String,
    /// Position status: "open", "won", "lost", "pending", "cancelled", or "voided".
    pub status: String,
    /// Realized PNL in micros.
    #[serde(with = "crate::api::wire_int::option_i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64", required)
    )]
    pub pnl_micros: Option<i64>,
    pub created_at_ms: i64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_at_ms: Option<i64>,
    /// Product-aware public leg details.
    pub legs: Vec<LegDetail>,
}

/// Row in the public paginated vault activity feed.
///
/// User identity fields, position IDs, and exact signed amounts are part of the
/// unauthenticated public activity contract. Profile handles are included so
/// clients can link rows to public profiles when present.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicVaultActivityEventResponse {
    /// `"deposit"`, `"withdrawal_requested"`, `"withdrawal_filled"`, `"settled"`, or `"fee_claimed"`.
    pub event_type: String,
    /// Public user UUID for the activity row.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    /// Display name if the user has a profile, else their UUID prefix.
    pub user_display_name: String,
    /// Profile handle if the user has set one. Use this (not display_name)
    /// when building `/portfolio/:handle` links, which is what the public
    /// profile route expects.
    #[cfg_attr(feature = "openapi", schema(nullable = true))]
    pub user_handle: Option<String>,
    pub user_avatar_seed: Option<i32>,
    /// X (Twitter) avatar URL, when linked.
    #[cfg_attr(feature = "openapi", schema(nullable = true))]
    pub user_x_avatar_url: Option<String>,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub amount_micros: i64,
    #[cfg_attr(feature = "openapi", schema(value_type = Option<String>, format = "uuid"))]
    pub position_id: Option<String>,
    pub event_at_ms: i64,
}

/// Public paginated vault activity feed response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicVaultActivityResponse {
    pub items: Vec<PublicVaultActivityEventResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

/// Per-user aggregate row in the public vault contributors leaderboard.
///
/// User identity fields and exact aggregate amounts are intentional public
/// leaderboard data for the unauthenticated vault contributors surface.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicVaultContributorLeaderboardRowResponse {
    /// Public user UUID for the leaderboard row.
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    pub user_display_name: String,
    /// Profile handle if the user has set one. Use this (not display_name)
    /// when building `/portfolio/:handle` links, which is what the public
    /// profile route expects.
    #[cfg_attr(feature = "openapi", schema(nullable = true))]
    pub user_handle: Option<String>,
    pub user_avatar_seed: Option<i32>,
    /// X (Twitter) avatar URL, when linked.
    #[cfg_attr(feature = "openapi", schema(nullable = true))]
    pub user_x_avatar_url: Option<String>,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub total_deposits_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub all_time_earned_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub all_time_pnl_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub unrealized_pnl_micros: i64,
}

/// Public paginated vault contributors leaderboard response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicVaultContributorLeaderboardResponse {
    pub items: Vec<PublicVaultContributorLeaderboardRowResponse>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
}

/// Authenticated per-user performance card response.
///
/// Carries the caller's own vault balances, performance, latest deposit time,
/// and pending withdrawal state. Public vault overview endpoints expose only
/// aggregate vault totals.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct VaultUserPerformanceResponse {
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub current_balance_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub unallocated_micros: u64,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub allocated_micros: u64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub lifetime_deposits_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub all_time_earned_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub all_time_pnl_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub unrealized_pnl_micros: i64,
    /// Millisecond timestamp of the caller's most recent deposit, or `None` if
    /// they have never deposited.
    pub latest_deposit_time_ms: Option<i64>,
    /// The caller's own pending withdrawal request, or `None` if no withdrawal
    /// is currently queued.
    pub pending_withdrawal: Option<PendingVaultWithdrawalResponse>,
}

/// Response containing the user's immediately available balance.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "available_micros": "1000000"
})))]
pub struct AvailableBalanceResponse {
    /// Immediately available user balance in USDC micros.
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "1000000"))]
    pub available_micros: u64,
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
    pub id: String,
    pub category: UserTransactionCategory,
    pub title: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
    pub status: UserTransactionStatus,
    pub occurred_at_ms: i64,
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

/// User response after placing a contest bet.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PlaceContestBetResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub contest_id: String,
    pub entry_index: u32,
    #[serde(with = "crate::api::wire_int::u64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub reserved_micros: u64,
}

/// Category served by contest read endpoints.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ContestCategoryResponse {
    Mentions,
    Sports,
    Culture,
}

/// Contest lifecycle status exposed to clients.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ContestStatusResponse {
    Open,
    Resolved,
    Voided,
}

/// Contest bet-type payload echoed back on detail reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "type", content = "value", rename_all = "snake_case")]
pub enum ContestBetTypeResponse {
    NumBets(usize),
    BetsPerCategory(usize),
}

/// Contest game-type payload echoed back on detail reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ContestGameTypeResponse {
    Lineups,
    Survivor,
    Streak,
    Outcast,
    Roster,
}

/// Direction payload echoed back on user-entry reads.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ContestDirectionResponse {
    Up,
    Down,
}

/// Leg-outcome payload echoed back on user-entry reads.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum ContestLegOutcome {
    Pending,
    Won,
    Lost,
    Voided,
}

/// Server-authoritative Survivor surface lifecycle.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SurvivorPhaseResponse {
    /// The current round exists, but its pick window has not opened yet.
    Scheduled,
    PickOpen,
    PickLocked,
    Live,
    RoundSettled,
    /// Transitional gap before an ordinary successor or a same-index
    /// replacement for a voided round is persisted.
    AwaitingNextRound,
    ContestSettled,
    Voided,
}

/// Persisted round lifecycle used by the exact pick, live, and settled views.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SurvivorRoundStatusResponse {
    Scheduled,
    PickOpen,
    PickLocked,
    Live,
    Settled,
    Voided,
}

/// Result of one entry in one Survivor round.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SurvivorEntryRoundResultResponse {
    Pending,
    Won,
    Lost,
    Missed,
    Voided,
}

/// Why an entry became terminal before contest settlement.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "snake_case")]
pub enum SurvivorEliminationReasonResponse {
    IncorrectPick,
    MissedDeadline,
}

/// Public Perfect Slate configuration and settled winner summary.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestPerfectSlateResponse {
    /// Total cash pool split evenly among entries that win every selection and,
    /// when configured, guess the tie-breaker result exactly.
    pub payout_micros: u64,
    /// Number of qualifying entries after contest settlement.
    pub winner_count: u32,
}

/// Public contest summary fields visible without a session.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicContestSummaryResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub contest_id: String,
    pub title: String,
    pub category: ContestCategoryResponse,
    pub status: ContestStatusResponse,
    /// Game type is present on newly served lobby and detail responses. It is
    /// optional so clients can read responses from an older API during an
    /// additive rollout.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub game_type: Option<ContestGameTypeResponse>,
    /// `true` only while an open Survivor contest has no persisted current
    /// round because a voided round is awaiting same-index replacement.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor_awaiting_replacement: Option<bool>,
    /// Zero-based round cursor of a Survivor contest, and `None` for
    /// every other game type. Survivor accepts new entrants only during round
    /// zero, so a value above zero means entries are closed even while a later
    /// round's pick window is open and `betting_closes_ms` is still ahead.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor_current_game_index: Option<u32>,
    pub bet_amount_micros: u64,
    pub protocol_prize_pool_micros: u64,
    pub total_pot_micros: u64,
    /// Number of paid entries after which the next entry begins increasing the
    /// displayed prize pool. Zero means the first paid entry increases it;
    /// `None` means entries cannot grow this contest's prize pool.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub prize_pool_growth_starts_after_entries: Option<u32>,
    /// Present when this Lineups contest offers a Perfect Slate bonus.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub perfect_slate: Option<ContestPerfectSlateResponse>,
    /// Explicit contest-lobby placement while entries are open: 1 is the
    /// left card and 2 is the right card.
    #[cfg_attr(feature = "openapi", schema(required, minimum = 1, maximum = 2))]
    pub featured_slot: Option<u8>,
    pub entries_filled: u32,
    pub entry_cap: u32,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub entry_opens_at_ms: Option<u64>,
    pub betting_closes_ms: u64,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub live_ends_at_ms: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolved_at_ms: Option<u64>,
    pub created_at_ms: u64,
    /// Resolved contest image URL, if any.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
}

/// Caller-scoped contest summary fields for optional-session reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestCallerSummaryResponse {
    /// True when the authenticated caller has entered this contest.
    pub joined: bool,
    /// Number of entries owned by the authenticated caller.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required))]
    pub entry_count: u32,
}

/// Single row in the session-aware contest lobby list.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CallerContestSummaryResponse {
    #[serde(flatten)]
    pub contest: PublicContestSummaryResponse,
    /// Present only when the request includes a valid caller session.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub caller: Option<ContestCallerSummaryResponse>,
}

/// Contest-lobby row with list-only presentation and entry metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestLobbySummaryResponse {
    #[serde(flatten)]
    #[cfg_attr(feature = "openapi", schema(inline))]
    pub summary: CallerContestSummaryResponse,
    /// Marker-free public display copy for lobby cards, capped at 160 characters.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub description: Option<String>,
    /// Maximum entries one caller can submit to this contest.
    #[serde(default = "default_contest_entry_count")]
    #[cfg_attr(feature = "openapi", schema(required, minimum = 1, maximum = 5))]
    pub max_entries_per_player: u32,
    pub protocol_prize_pool_pays_app_tokens: bool,
}

/// Response for session-aware GET /v1/contests.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CallerContestsListResponse {
    pub contests: Vec<ContestLobbySummaryResponse>,
    /// Opaque cursor to pass to the next request, if more rows remain.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub next_cursor: Option<String>,
}

/// Single market entry on a contest detail.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestMarketResponse {
    pub market_id: u64,
    /// Per-contest pick grouping. This never selects market behavior.
    pub selection_group: String,
    /// Open user-facing category slug.
    pub market_type: MarketType,
    /// Trading surfaces enabled on the canonical market.
    pub trading_channels: Vec<TradingChannel>,
    pub name: String,
    /// Resolved event image for this market, when assigned.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub image_url: Option<String>,
    /// Public rules text for this tournament child market. This is sourced
    /// from the underlying market's Polymarket description so fantasy rule
    /// panels do not need the public price-market detail endpoint.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub description: Option<String>,
    /// Canonical event-market resolution rules. `None` for price markets.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolution_rules: Option<String>,
    pub status: MarketStatus,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub outcome: Option<Outcome>,
    /// Canonical source identity for source-backed event contracts.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub source: Option<EventMarketSource>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub betting_closes_at_ms: Option<u64>,
    /// Scheduled event start. For Survivor this separates the immutable
    /// pick-locked interval from the live interval.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub opens_at_ms: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub live_ends_at_ms: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub resolution_time_ms: Option<u64>,
    /// Admin-provided live yes probability for manual fantasy markets.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub manual_probability_bps: Option<i32>,
    /// Admin-provided live-state payload for manual fantasy markets.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub manual_live_state: Option<Value>,
}

/// Per-market pick on a user's contest entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestUserPickResponse {
    pub market_id: u64,
    pub direction: ContestDirectionResponse,
    pub outcome: ContestLegOutcome,
}

/// A selection offered inside a roster contest tier.
///
/// Points are milli-points (17.34 points -> 17340) and can be negative.
/// `live_state` and `metadata` are opaque engine-defined payloads (game
/// schedule, quarter/clock, post counts, ...) rendered by the frontend.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestRosterSelectionResponse {
    pub selection_index: u16,
    pub name: String,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub image_url: Option<String>,
    /// Average/projected points litmus shown in the UI.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub avg_points_milli: Option<i64>,
    /// Current live points.
    pub points_milli: i64,
    /// Final points, set once the contest is finalized.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub final_points_milli: Option<i64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub live_state: Option<Value>,
    /// Static engine-defined metadata set at creation (team, position, ...),
    /// rendered by the frontend alongside `live_state`.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub metadata: Option<Value>,
    pub updated_at_ms: u64,
}

/// A named roster tier; entrants pick exactly one of its selections.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestRosterTierResponse {
    pub tier_index: u16,
    pub name: String,
    pub selections: Vec<ContestRosterSelectionResponse>,
}

/// Roster contest structure attached to detail reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestRosterResponse {
    pub tiers: Vec<ContestRosterTierResponse>,
}

/// A single roster pick on a user's entry or a leaderboard row.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestRosterPickResponse {
    pub tier_index: u16,
    pub selection_index: u16,
}

/// Reveal-safe picks for an entrant round. A hidden round structurally carries
/// JSON `null`, so an API response cannot accidentally include rival picks.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "visibility", rename_all = "snake_case")]
pub enum SurvivorRoundPicksResponse {
    Hidden { picks: () },
    Revealed { picks: Vec<ContestUserPickResponse> },
}

/// Reveal-safe direction counts for one market in a Survivor round.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorMarketPickCountsResponse {
    pub market_id: u64,
    pub up_count: u32,
    pub down_count: u32,
}

/// Aggregate Survivor participation for a locked round. The eligible count is
/// fixed when the round opens. Submitted entries have an accepted submission
/// by lock; all other eligible entries are explicitly missed, so submitted plus
/// missed equals eligible. `markets` is bounded to the persisted round slate.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorRoundBreakdownResponse {
    pub eligible_entry_count: u32,
    pub submitted_entry_count: u32,
    pub missed_entry_count: u32,
    pub markets: Vec<SurvivorMarketPickCountsResponse>,
}

/// One persisted round and its exact market slate.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorRoundResponse {
    pub game_index: u32,
    pub status: SurvivorRoundStatusResponse,
    pub required_pick_count: u32,
    pub betting_opens_at_ms: u64,
    pub betting_closes_at_ms: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_at_ms: Option<u64>,
    pub markets: Vec<ContestMarketResponse>,
    /// Reveal-safe aggregate counts. Absent until the round's picks lock.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub breakdown: Option<SurvivorRoundBreakdownResponse>,
}

/// One entry's result and reveal-safe picks for a persisted round.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorEntryRoundResponse {
    pub game_index: u32,
    pub result: SurvivorEntryRoundResultResponse,
    pub picks: SurvivorRoundPicksResponse,
}

/// Survivor-specific state attached only to a caller-owned entry or a
/// leaderboard row. Identity, payout, and refund fields remain on the parent.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum SurvivorEntryStateResponse {
    Alive {
        eligible_for_current_game: bool,
        /// Route-scoped cursor for the next older round page.
        rounds_next_cursor: Option<u32>,
        rounds: Vec<SurvivorEntryRoundResponse>,
    },
    Eliminated {
        eliminated_game_index: u32,
        elimination_reason: SurvivorEliminationReasonResponse,
        /// Route-scoped cursor for the next older round page.
        rounds_next_cursor: Option<u32>,
        rounds: Vec<SurvivorEntryRoundResponse>,
    },
    Winner {
        /// Route-scoped cursor for the next older round page.
        rounds_next_cursor: Option<u32>,
        rounds: Vec<SurvivorEntryRoundResponse>,
    },
    Voided {
        /// Route-scoped cursor for the next older round page.
        rounds_next_cursor: Option<u32>,
        rounds: Vec<SurvivorEntryRoundResponse>,
    },
}

/// Additive public Survivor state on a contest detail response.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorContestResponse {
    pub version: u32,
    /// Immutable number of rounds in this contest's Survivor schedule.
    #[cfg_attr(feature = "openapi", schema(minimum = 1, maximum = 32767))]
    pub round_count: u32,
    pub phase: SurvivorPhaseResponse,
    pub current_game_index: u32,
    /// Present only during `awaiting_next_round`. This is
    /// `current_game_index + 1` for an ordinary successor, or equals
    /// `current_game_index` while a voided round awaits its replacement.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub next_game_index: Option<u32>,
    /// Persisted rounds are sorted by their unique game indexes and ordinarily
    /// form a contiguous prefix. During a same-index replacement, the current
    /// index is the sole permitted hole; a pre-scheduled successor may remain.
    /// A replacement gap at index zero may therefore have no persisted rounds.
    pub rounds: Vec<SurvivorRoundResponse>,
    /// Exclusive cursor for the next older contest-round page.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub rounds_next_cursor: Option<u32>,
    /// Game indexes whose entrant picks the server has made public.
    pub revealed_game_indexes: Vec<u32>,
    pub remaining_survivor_count: u32,
}

/// One team already used by a caller-owned Survivor entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct SurvivorTeamUsageResponse {
    pub source_team_id: String,
    pub used_game_index: u32,
}

/// A user's entry on a contest detail response.
///
/// This appears under a scoped parent such as `caller` or `profile_owner`.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestUserEntryResponse {
    pub entry_index: u32,
    pub created_at_ms: u64,
    pub picks: Vec<ContestUserPickResponse>,
    pub open_leg_count: u32,
    pub resolved_win_count: u32,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub payout_micros: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub net_payout_micros: Option<u64>,
    /// Whether settlement returned this entry's stake without a win or loss.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required, default = false))]
    pub refunded: bool,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub rank: Option<u32>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub tiebreaker_guess: Option<i64>,
    /// True after settlement when this entry earned the Perfect Slate bonus.
    #[serde(default)]
    pub perfect_slate_won: bool,
    /// Perfect Slate portion of this entry's gross payout.
    #[serde(default)]
    pub perfect_slate_payout_micros: u64,
    /// Roster contests only: this entry's picks, one per tier.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub roster_picks: Option<Vec<ContestRosterPickResponse>>,
    /// Roster contests only: the entry's current (or final) points score.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub roster_points_milli: Option<i64>,
    /// Present for Survivor entries on APIs that support round history.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor: Option<SurvivorEntryStateResponse>,
    /// Survivor only: teams already consumed by this entry.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor_team_usage: Option<Vec<SurvivorTeamUsageResponse>>,
}

/// Public tie-breaker metadata for Lineups, Survivor, and Outcast contests.
///
/// For Lineups, closer guesses rank ahead among entries tied on score. For
/// Survivor, a final-round guess is display-only and must not change the equal
/// split among every entry still alive after the final round. For Outcast,
/// among the lowest-scoring entries, the guess furthest from the result is the
/// Outcast.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestTiebreakerResponse {
    /// Whether the contest uses a tie-breaker.
    pub enabled: bool,
    /// Contest-specific tie-breaker prompt shown to entrants.
    pub hint: String,
    /// Actual value used to calculate absolute distance from each entrant's
    /// guess. Exposed once entries lock or the contest resolves, if set.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub result: Option<i64>,
}

/// Public contest detail fields visible without a session.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicContestDetailResponse {
    #[serde(flatten)]
    pub summary: PublicContestSummaryResponse,
    #[serde(default = "default_contest_entry_count")]
    #[cfg_attr(feature = "openapi", schema(required, default = 1, minimum = 1))]
    pub max_entries_per_player: u32,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub description: Option<String>,
    pub bet_type: ContestBetTypeResponse,
    pub winning_split_bps: Vec<u64>,
    pub protocol_winning_split_bps: Vec<u64>,
    pub protocol_prize_pool_pays_app_tokens: bool,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub tiebreaker: Option<ContestTiebreakerResponse>,
    pub markets: Vec<ContestMarketResponse>,
    /// Tier/selection structure for roster contests; absent for every other
    /// game type (roster contests carry no markets).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub roster: Option<ContestRosterResponse>,
    /// Present only for Survivor contests on APIs that support the product.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor: Option<SurvivorContestResponse>,
}

/// Caller-scoped contest detail fields for optional-session reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestCallerDetailResponse {
    /// True when the authenticated caller has entered this contest.
    pub joined: bool,
    /// Entries for the authenticated caller.
    pub entries: Vec<ContestUserEntryResponse>,
}

/// Response for session-aware GET /v1/contests/:id.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CallerContestDetailResponse {
    #[serde(flatten)]
    pub contest: PublicContestDetailResponse,
    /// Present only when the request includes a valid caller session.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub caller: Option<ContestCallerDetailResponse>,
}

fn default_contest_entry_count() -> u32 {
    1
}

/// Single row in the contest leaderboard.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestLeaderboardRowResponse {
    pub rank: u32,
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    pub entry_index: u32,
    #[serde(default = "default_contest_entry_count")]
    #[cfg_attr(feature = "openapi", schema(required, default = 1, minimum = 1))]
    pub user_entry_count: u32,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub handle: Option<String>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub x_handle: Option<String>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub x_avatar_url: Option<String>,
    // i32 (not u32): avatar_seed is a signed hash that is often negative.
    pub avatar_seed: i32,
    pub resolved_win_count: u32,
    pub open_leg_count: u32,
    /// Entrant picks, populated only after entries lock. Always `None` for a
    /// Survivor row; its per-round reveal-safe picks live under `survivor`.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub picks: Option<Vec<ContestUserPickResponse>>,
    /// Entrant's tiebreaker guess. Populated once entries lock (guesses are
    /// immutable from then on), enabling live closest-guess leaderboards.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub tiebreaker_guess: Option<i64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub payout_micros: Option<u64>,
    #[cfg_attr(feature = "openapi", schema(required))]
    pub net_payout_micros: Option<u64>,
    /// True after settlement when this entry earned the Perfect Slate bonus.
    #[serde(default)]
    pub perfect_slate_won: bool,
    /// Perfect Slate portion of this entry's gross payout.
    #[serde(default)]
    pub perfect_slate_payout_micros: u64,
    /// Whether settlement returned this entry's stake without a win or loss.
    #[serde(default)]
    #[cfg_attr(feature = "openapi", schema(required, default = false))]
    pub refunded: bool,
    /// Roster contests only: the row's picks, exposed once entries lock.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub roster_picks: Option<Vec<ContestRosterPickResponse>>,
    /// Roster contests only: the row's points score (live while open, final
    /// after settlement).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub roster_points_milli: Option<i64>,
    /// Present for Survivor rows on APIs that support round history.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub survivor: Option<SurvivorEntryStateResponse>,
}

/// Public contest leaderboard fields visible without a session.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicContestLeaderboardResponse {
    pub total_entries: u32,
    pub entries: Vec<ContestLeaderboardRowResponse>,
    /// Opaque cursor for the next page; null when the listing is exhausted.
    pub next_cursor: Option<String>,
}

/// Caller-scoped contest leaderboard fields for optional-session reads.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestCallerLeaderboardResponse {
    /// Rows for the authenticated caller, present when they entered and fell
    /// outside the top-N slice returned in `entries`.
    pub rows: Vec<ContestLeaderboardRowResponse>,
}

/// Response for session-aware GET /v1/contests/:id/leaderboard.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct CallerContestLeaderboardResponse {
    #[serde(flatten)]
    pub leaderboard: PublicContestLeaderboardResponse,
    /// Present only when the request includes a valid caller session.
    #[cfg_attr(feature = "openapi", schema(required))]
    pub caller: Option<ContestCallerLeaderboardResponse>,
}

/// Single "Top Participant" row: an entrant of this contest ranked by
/// their payout history across all contests over the specified window.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestTopParticipantRowResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: String,
    pub handle: Option<String>,
    pub x_handle: Option<String>,
    pub x_avatar_url: Option<String>,
    // i32 (not u32): avatar_seed is a signed hash that is often negative.
    pub avatar_seed: i32,
    pub won_count: u32,
    pub total_winnings_micros: u64,
}

/// Response for GET /v1/contests/:id/top-participants.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestTopParticipantsResponse {
    pub window_ms: u64,
    pub participants: Vec<ContestTopParticipantRowResponse>,
}

/// Per-market pick distribution for the "Most Popular Entry" card.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestPopularEntryMarketResponse {
    pub market_id: u64,
    pub yes_count: u32,
    pub no_count: u32,
}

/// Response for GET /v1/contests/:id/popular-entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ContestPopularEntryResponse {
    pub total_entries: u32,
    pub markets: Vec<ContestPopularEntryMarketResponse>,
}

/// Response containing the authenticated user's referral code.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserReferralCodeResponse {
    pub referral_code: String,
    pub max_referrals: Option<u32>,
    pub referrals_used: u32,
    pub referrals_remaining: Option<u32>,
    pub ever_had_referral_capacity: bool,
    pub can_edit: bool,
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

/// Deposit-match offer attached to a valid referral link.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct PublicReferralDepositMatchOffer {
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = String, format = "int64", example = "10000000")
    )]
    pub match_limit_micros: i64,
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

/// Result of leasing a referral prompt for presentation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ClaimReferralPromptResponse {
    pub show: bool,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        with = "crate::api::wire_int::option_i64_string"
    )]
    #[cfg_attr(
        feature = "openapi",
        schema(value_type = Option<String>, format = "int64")
    )]
    pub amount_micros: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub claim_token: Option<Uuid>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub retry_after_ms: Option<u32>,
}

/// Response after successfully setting the authenticated user's referrer.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserSetReferrerResponse {}

/// Effective referral kickback rates for the authenticated user.
/// Super-referrer status is hidden — users see whichever rates actually
/// apply to them.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "primary_kickback_bps": 1500,
    "secondary_kickback_bps": 250,
})))]
pub struct UserReferralRatesResponse {
    /// Primary kickback rate (direct referrals) in basis points.
    pub primary_kickback_bps: u32,
    /// Secondary kickback rate (referrals of referrals) in basis points.
    pub secondary_kickback_bps: u32,
}

/// Aggregated referral stats for the authenticated user.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[cfg_attr(feature = "openapi", schema(example = json!({
    "total_referred": 22,
    "total_rewards_micros": "352220000",
})))]
pub struct UserReferralStatsResponse {
    /// Number of users directly referred by this user.
    pub total_referred: u32,
    /// Total rewards earned from direct + indirect referrals on resolved
    /// positions, in USDC micros.
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64", example = "352220000"))]
    pub total_rewards_micros: i64,
    pub has_settled_referral_trade: bool,
}

/// Referral chain level label used in the "my referrals" list.
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
#[serde(rename_all = "lowercase")]
pub enum ReferralLevelLabel {
    /// User referred this person directly.
    First,
    /// Referred by one of the user's direct referrals.
    Second,
}

/// Single entry in the "my referrals" list.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserReferralEntryResponse {
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "uuid"))]
    pub user_id: Uuid,
    pub handle: String,
    pub display_name: String,
    pub avatar_seed: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_handle: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub x_avatar_url: Option<String>,
    pub referred_at_ms: i64,
    pub level: ReferralLevelLabel,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub total_volume_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub total_fees_paid_micros: i64,
    #[serde(with = "crate::api::wire_int::i64_string")]
    #[cfg_attr(feature = "openapi", schema(value_type = String, format = "int64"))]
    pub my_kickback_micros: i64,
}

/// Paginated list response for GET /v1/user/referrals.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserReferralsListResponse {
    pub entries: Vec<UserReferralEntryResponse>,
    pub total_count: i64,
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

/// Public logged-out observer-access policy.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct ObserverAccessResponse {
    pub enabled: bool,
}

/// Public global visibility for fixed market-navigation categories.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct MarketCategoryVisibilityResponse {
    pub crypto: bool,
    pub mentions: bool,
    pub nfl: bool,
    pub culture: bool,
}

/// Legacy feature-access response retained for older clients.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "openapi", derive(utoipa::ToSchema))]
pub struct UserFeaturesResponse {
    pub markets_access: bool,
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::{
        AccessResponse, ContestGameTypeResponse, ContestLeaderboardRowResponse,
        ContestUserEntryResponse, PublicContestDetailResponse, SessionResponse,
        SurvivorContestResponse, SurvivorMarketPickCountsResponse, SurvivorPhaseResponse,
        SurvivorRoundBreakdownResponse, SurvivorRoundPicksResponse, SurvivorRoundResponse,
        SurvivorRoundStatusResponse,
    };

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
        assert!(!compatible.onboarding_completed);

        let debug = format!("{compatible:?}");
        assert!(!debug.contains("compatible-token"));
        assert!(debug.contains("<redacted>"));
    }

    #[test]
    fn contest_leaderboard_row_defaults_legacy_user_entry_count() {
        let json = r#"{"rank":0,"user_id":"","entry_index":0,"avatar_seed":0,"resolved_win_count":0,"open_leg_count":0}"#;
        let row: ContestLeaderboardRowResponse =
            serde_json::from_str(json).expect("deserialize legacy leaderboard row");
        assert_eq!(row.user_entry_count, 1);
    }

    #[test]
    fn contest_detail_defaults_legacy_max_entries_per_player() {
        let json = r#"{
            "contest_id":"","title":"","category":"sports","status":"open",
            "bet_amount_micros":0,"protocol_prize_pool_micros":0,"total_pot_micros":0,
            "entries_filled":0,"entry_cap":0,"entry_opens_at_ms":null,
            "betting_closes_ms":0,"live_ends_at_ms":null,"resolved_at_ms":null,
            "created_at_ms":0,"description":null,"bet_type":{"type":"num_bets","value":1},
            "game_type":"lineups","winning_split_bps":[],"protocol_winning_split_bps":[],
            "protocol_prize_pool_pays_app_tokens":false,"tiebreaker":null,"markets":[]
        }"#;
        let detail: PublicContestDetailResponse =
            serde_json::from_str(json).expect("deserialize legacy contest detail");
        assert_eq!(detail.max_entries_per_player, 1);
        assert_eq!(detail.summary.prize_pool_growth_starts_after_entries, None);
        assert!(matches!(
            detail.summary.game_type,
            Some(ContestGameTypeResponse::Lineups)
        ));
    }

    #[test]
    fn contest_lobby_defaults_legacy_entry_progress() {
        let json = r#"{
            "contest_id":"","title":"","category":"sports","status":"open",
            "bet_amount_micros":0,"protocol_prize_pool_micros":0,"total_pot_micros":0,
            "entries_filled":1,"entry_cap":5,"entry_opens_at_ms":null,
            "betting_closes_ms":0,"live_ends_at_ms":null,"resolved_at_ms":null,
            "created_at_ms":0,"caller":{"joined":true},
            "protocol_prize_pool_pays_app_tokens":false
        }"#;
        let summary: super::ContestLobbySummaryResponse =
            serde_json::from_str(json).expect("deserialize legacy contest lobby summary");

        assert_eq!(summary.max_entries_per_player, 1);
        assert_eq!(summary.summary.caller.expect("caller").entry_count, 0);
    }

    #[test]
    fn survivor_hidden_picks_serialize_as_explicit_null() {
        let value = serde_json::to_value(SurvivorRoundPicksResponse::Hidden { picks: () })
            .expect("serialize hidden picks");

        assert_eq!(
            value,
            serde_json::json!({ "visibility": "hidden", "picks": null })
        );
    }

    #[test]
    fn contest_detail_round_trips_top_level_game_type() {
        // `game_type` moved from the detail struct into the flattened summary;
        // the detail wire JSON must stay byte-compatible: `game_type` remains a
        // top-level key on both serialize and deserialize.
        let json = r#"{
            "contest_id":"c","title":"t","category":"sports","status":"open",
            "game_type":"roster",
            "bet_amount_micros":0,"protocol_prize_pool_micros":0,"total_pot_micros":0,
            "perfect_slate":null,"featured_slot":null,
            "entries_filled":0,"entry_cap":0,"entry_opens_at_ms":null,
            "betting_closes_ms":0,"live_ends_at_ms":null,"resolved_at_ms":null,
            "created_at_ms":0,"max_entries_per_player":1,"description":null,
            "bet_type":{"type":"num_bets","value":1},
            "winning_split_bps":[],"protocol_winning_split_bps":[],
            "protocol_prize_pool_pays_app_tokens":false,"tiebreaker":null,"markets":[]
        }"#;
        let detail: PublicContestDetailResponse =
            serde_json::from_str(json).expect("deserialize contest detail");
        assert!(matches!(
            detail.summary.game_type,
            Some(super::ContestGameTypeResponse::Roster)
        ));

        let value = serde_json::to_value(&detail).expect("serialize contest detail");
        assert_eq!(value["game_type"], "roster");
        let round_tripped: PublicContestDetailResponse =
            serde_json::from_value(value).expect("round-trip contest detail");
        assert!(matches!(
            round_tripped.summary.game_type,
            Some(super::ContestGameTypeResponse::Roster)
        ));
    }

    #[test]
    fn contest_user_entry_refunded_defaults_false_and_preserves_true() {
        let entry = json!({
            "entry_index": 0,
            "created_at_ms": 1,
            "picks": [],
            "open_leg_count": 0,
            "resolved_win_count": 0
        });

        let defaulted: ContestUserEntryResponse = serde_json::from_value(entry.clone()).unwrap();
        assert!(!defaulted.refunded);
        assert_eq!(serde_json::to_value(defaulted).unwrap()["refunded"], false);

        let mut refunded = entry;
        refunded["refunded"] = json!(true);
        let refunded: ContestUserEntryResponse = serde_json::from_value(refunded).unwrap();
        assert!(refunded.refunded);
    }

    #[test]
    fn survivor_round_breakdown_serializes_explicit_missed_entries() {
        let value = serde_json::to_value(SurvivorRoundBreakdownResponse {
            eligible_entry_count: 10,
            submitted_entry_count: 8,
            missed_entry_count: 2,
            markets: vec![SurvivorMarketPickCountsResponse {
                market_id: 42,
                up_count: 5,
                down_count: 3,
            }],
        })
        .expect("serialize Survivor round breakdown");

        assert_eq!(
            value,
            serde_json::json!({
                "eligible_entry_count": 10,
                "submitted_entry_count": 8,
                "missed_entry_count": 2,
                "markets": [{ "market_id": 42, "up_count": 5, "down_count": 3 }]
            })
        );
    }

    #[test]
    fn survivor_round_omits_breakdown_before_lock() {
        let value = serde_json::to_value(SurvivorRoundResponse {
            game_index: 0,
            status: SurvivorRoundStatusResponse::PickOpen,
            required_pick_count: 1,
            betting_opens_at_ms: 1,
            betting_closes_at_ms: 2,
            resolved_at_ms: None,
            markets: vec![],
            breakdown: None,
        })
        .expect("serialize open Survivor round");

        assert!(value.get("breakdown").is_none());
    }

    #[test]
    fn survivor_awaiting_next_round_accepts_successor_and_replacement_gaps() {
        let round = |game_index, status| {
            serde_json::json!({
                "game_index": game_index,
                "status": status,
                "required_pick_count": 1,
                "betting_opens_at_ms": 1,
                "betting_closes_at_ms": 2,
                "markets": []
            })
        };
        let cases = [
            (
                "ordinary successor",
                1,
                serde_json::json!([round(0, "settled")]),
                vec![0],
            ),
            (
                "empty round-zero replacement",
                0,
                serde_json::json!([]),
                vec![],
            ),
            (
                "replacement with scheduled successor",
                0,
                serde_json::json!([round(1, "scheduled")]),
                vec![1],
            ),
        ];

        for (case, next_game_index, rounds, expected_game_indexes) in cases {
            let response: SurvivorContestResponse = serde_json::from_value(serde_json::json!({
                "version": 1,
                "round_count": 7,
                "phase": "awaiting_next_round",
                "current_game_index": 0,
                "next_game_index": next_game_index,
                "rounds": rounds,
                "revealed_game_indexes": [],
                "remaining_survivor_count": 10
            }))
            .unwrap_or_else(|error| panic!("deserialize {case}: {error}"));

            assert!(matches!(
                response.phase,
                SurvivorPhaseResponse::AwaitingNextRound
            ));
            assert_eq!(response.next_game_index, Some(next_game_index));
            assert_eq!(
                response
                    .rounds
                    .iter()
                    .map(|round| round.game_index)
                    .collect::<Vec<_>>(),
                expected_game_indexes
            );
        }
    }
}
