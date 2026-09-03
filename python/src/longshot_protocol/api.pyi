"""Generated public API typing contracts. Do not edit by hand."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from .model import LongshotModel, RustStringEnum, RustTaggedUnion
from .taker import OrderLeg, SignedOrder
from .types import (
    Address,
    Direction,
    MarketId,
    MarketStatus,
    MarketType,
    Odds,
    OrderType,
    Outcome,
    PositionId,
    TradingChannel,
)

# Runtime dataclasses remain permissive for decoding, but Rust-required fields
# must be supplied by typed callers; nullable fields retain Optional annotations.

class PublicMarketsRawQuery(LongshotModel):
    market_type: Optional[MarketType]
    trading_channel: Optional[TradingChannel]
    limit: Optional[int]
    cursor: Optional[str]
    statuses: Optional[List[MarketStatus]]
    def __init__(self, *, market_type: Optional[MarketType] = ..., trading_channel: Optional[TradingChannel] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ..., statuses: Optional[List[MarketStatus]] = ...) -> None: ...

class PriceStrikeMarket(LongshotModel):
    id: MarketId
    market_type: MarketType
    trading_channels: List[TradingChannel]
    name: str
    description: Optional[str]
    status: MarketStatus
    tradeable: bool
    category_tags: List[str]
    betting_closes_at_ms: int
    resolution_time_ms: int
    open_strike_micros: Optional[int]
    resolved_outcome: Optional[Outcome]
    created_at_ms: int
    opened_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    image_url: Optional[str]
    def __init__(self, *, id: MarketId, market_type: MarketType, trading_channels: List[TradingChannel], name: str, description: Optional[str] = ..., status: MarketStatus, tradeable: bool, category_tags: List[str], betting_closes_at_ms: int, resolution_time_ms: int, open_strike_micros: Optional[int] = ..., resolved_outcome: Optional[Outcome] = ..., created_at_ms: int, opened_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., image_url: Optional[str] = ...) -> None: ...

class EventMarket(LongshotModel):
    id: MarketId
    market_type: MarketType
    trading_channels: List[TradingChannel]
    name: str
    description: Optional[str]
    resolution_rules: Optional[str]
    status: MarketStatus
    tradeable: bool
    category_tags: List[str]
    opens_at_ms: Optional[int]
    source_starts_at_ms: Optional[int]
    betting_closes_at_ms: int
    live_ends_at_ms: Optional[int]
    resolution_time_ms: int
    resolved_outcome: Optional[Outcome]
    created_at_ms: int
    opened_at_ms: Optional[int]
    resolved_at_ms: Optional[int]
    display_probability_bps: Optional[int]
    image_url: Optional[str]
    def __init__(self, *, id: MarketId, market_type: MarketType, trading_channels: List[TradingChannel], name: str, description: Optional[str] = ..., resolution_rules: Optional[str] = ..., status: MarketStatus, tradeable: bool, category_tags: List[str], opens_at_ms: Optional[int], source_starts_at_ms: Optional[int] = ..., betting_closes_at_ms: int, live_ends_at_ms: Optional[int] = ..., resolution_time_ms: int, resolved_outcome: Optional[Outcome] = ..., created_at_ms: int, opened_at_ms: Optional[int] = ..., resolved_at_ms: Optional[int] = ..., display_probability_bps: Optional[int] = ..., image_url: Optional[str] = ...) -> None: ...

class PublicMarket(RustTaggedUnion):
    @classmethod
    def event(cls, payload: Any=None, **fields: Any) -> PublicMarket:
        ...
    @classmethod
    def price_strike(cls, payload: Any=None, **fields: Any) -> PublicMarket:
        ...

class PublicMarketResponse(LongshotModel):
    market: PublicMarket
    def __init__(self, *, market: PublicMarket) -> None: ...

class PublicMarketsResponse(LongshotModel):
    markets: List[PublicMarket]
    next_cursor: Optional[str]
    def __init__(self, *, markets: List[PublicMarket], next_cursor: Optional[str] = ...) -> None: ...

class MarketMetadataEntry(LongshotModel):
    market_id: int
    asset: str
    duration_secs: int
    start_at_ms: int
    betting_closes_at_ms: int
    def __init__(self, *, market_id: int, asset: str, duration_secs: int, start_at_ms: int, betting_closes_at_ms: int) -> None: ...

class MarketLookupResponse(LongshotModel):
    market: MarketMetadataEntry
    def __init__(self, *, market: MarketMetadataEntry) -> None: ...

class MarketLookupQuery(LongshotModel):
    asset: str
    duration_secs: int
    window_start_ms: int
    def __init__(self, *, asset: str, duration_secs: int, window_start_ms: int) -> None: ...

class MarketCurrentQuery(LongshotModel):
    asset: str
    duration_secs: int
    def __init__(self, *, asset: str, duration_secs: int) -> None: ...

class RecentResolutionsQuery(LongshotModel):
    asset: str
    duration_secs: int
    limit: Optional[int]
    def __init__(self, *, asset: str, duration_secs: int, limit: Optional[int] = ...) -> None: ...

class RecentResolutionEntry(LongshotModel):
    market_id: int
    outcome: str
    window_start_ms: int
    resolved_at_ms: int
    def __init__(self, *, market_id: int, outcome: str, window_start_ms: int, resolved_at_ms: int) -> None: ...

class RecentResolutionsResponse(LongshotModel):
    asset: str
    duration_secs: int
    resolutions: List[RecentResolutionEntry]
    def __init__(self, *, asset: str, duration_secs: int, resolutions: List[RecentResolutionEntry]) -> None: ...

class ProfitCapOverrideResponse(LongshotModel):
    market_type: MarketType
    max_profit_micros: int
    def __init__(self, *, market_type: MarketType, max_profit_micros: int) -> None: ...

class ProfitCapConfigResponse(LongshotModel):
    default_max_profit_micros: int
    overrides: List[ProfitCapOverrideResponse]
    def __init__(self, *, default_max_profit_micros: int, overrides: List[ProfitCapOverrideResponse]) -> None: ...

class PortfolioStatsResponse(LongshotModel):
    total_positions: int
    open_positions: int
    wins: int
    losses: int
    win_rate_pct: float
    total_pnl_micros: int
    def __init__(self, *, total_positions: int, open_positions: int, wins: int, losses: int, win_rate_pct: float, total_pnl_micros: int) -> None: ...

class PnlHistoryQuery(LongshotModel):
    from_: Optional[int]
    to: Optional[int]
    def __init__(self, *, from_: Optional[int] = ..., to: Optional[int] = ...) -> None: ...

class PnlEventResponse(LongshotModel):
    source: str
    resolved_at_ms: int
    position_id: Optional[str]
    contest_id: Optional[str]
    pnl_micros: int
    cumulative_micros: int
    def __init__(self, *, source: str, resolved_at_ms: int, position_id: Optional[str] = ..., contest_id: Optional[str] = ..., pnl_micros: int, cumulative_micros: int) -> None: ...

class PnlHistoryResponse(LongshotModel):
    events: List[PnlEventResponse]
    def __init__(self, *, events: List[PnlEventResponse]) -> None: ...

class PositionsQuery(LongshotModel):
    status: Optional[str]
    sort: Optional[str]
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, status: Optional[str] = ..., sort: Optional[str] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class PositionStatusQueryParam(RustStringEnum):
    Open = 'open'
    Won = 'won'
    Lost = 'lost'
    Voided = 'voided'

class PositionSortQueryParam(RustStringEnum):
    DateDesc = 'date_desc'
    DateAsc = 'date_asc'
    PnlDesc = 'pnl_desc'
    PnlAsc = 'pnl_asc'

class PositionSummary(LongshotModel):
    id: str
    wager_micros: int
    app_token_wager_micros: Optional[int]
    refunded_app_token_micros: Optional[int]
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    has_binary_event_leg: bool
    market_types: List[MarketType]
    def __init__(self, *, id: str, wager_micros: int, app_token_wager_micros: Optional[int] = ..., refunded_app_token_micros: Optional[int], payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., has_binary_event_leg: bool, market_types: List[MarketType]) -> None: ...

class PositionsListResponse(LongshotModel):
    positions: List[PositionSummary]
    next_cursor: Optional[str]
    partial: bool
    def __init__(self, *, positions: List[PositionSummary], next_cursor: Optional[str] = ..., partial: bool) -> None: ...

class ActivePositionStatus(RustStringEnum):
    Pending = 'pending'
    Open = 'open'

class PositionRole(RustStringEnum):
    Taker = 'taker'
    Maker = 'maker'

class ActivePosition(LongshotModel):
    position_id: PositionId
    status: ActivePositionStatus
    role: PositionRole
    taker_address: Optional[Address]
    wager_micros: int
    app_token_wager_micros: Optional[int]
    payout_micros: int
    legs: List[LegDetail]
    def __init__(self, *, position_id: PositionId, status: ActivePositionStatus, role: PositionRole, taker_address: Optional[Address] = ..., wager_micros: int, app_token_wager_micros: Optional[int] = ..., payout_micros: int, legs: List[LegDetail]) -> None: ...

class ActivePositionsResponse(LongshotModel):
    positions: List[ActivePosition]
    def __init__(self, *, positions: List[ActivePosition]) -> None: ...

class LegDetail(LongshotModel):
    leg_index: int
    market_id: int
    market_type: Optional[MarketType]
    label: Optional[str]
    asset: Optional[str]
    direction: str
    duration_secs: Optional[int]
    outcome: str
    window_start_ms: Optional[int]
    resolution_time_ms: int
    def __init__(self, *, leg_index: int, market_id: int, market_type: Optional[MarketType] = ..., label: Optional[str] = ..., asset: Optional[str] = ..., direction: str, duration_secs: Optional[int] = ..., outcome: str, window_start_ms: Optional[int] = ..., resolution_time_ms: int) -> None: ...

class PositionDetailResponse(LongshotModel):
    id: str
    wager_micros: int
    app_token_wager_micros: Optional[int]
    refunded_app_token_micros: Optional[int]
    payout_micros: int
    net_payout_micros: Optional[int]
    legs_count: int
    legs_summary: str
    status: str
    pnl_micros: Optional[int]
    created_at_ms: int
    resolved_at_ms: Optional[int]
    legs: List[LegDetail]
    def __init__(self, *, id: str, wager_micros: int, app_token_wager_micros: Optional[int] = ..., refunded_app_token_micros: Optional[int], payout_micros: int, net_payout_micros: Optional[int], legs_count: int, legs_summary: str, status: str, pnl_micros: Optional[int], created_at_ms: int, resolved_at_ms: Optional[int] = ..., legs: List[LegDetail]) -> None: ...

class PreferencesResponse(LongshotModel):
    notifications_enabled: bool
    quote_tolerance: QuoteTolerancePreference
    anonymous_mode_enabled: bool
    def __init__(self, *, notifications_enabled: bool, quote_tolerance: QuoteTolerancePreference, anonymous_mode_enabled: bool) -> None: ...

class QuoteTolerancePreference(RustStringEnum):
    Strict = 'strict'
    Normal = 'normal'
    Lenient = 'lenient'

class UpdatePreferencesRequest(LongshotModel):
    notifications_enabled: Optional[bool]
    quote_tolerance: Optional[QuoteTolerancePreference]
    anonymous_mode_enabled: Optional[bool]
    def __init__(self, *, notifications_enabled: Optional[bool] = ..., quote_tolerance: Optional[QuoteTolerancePreference] = ..., anonymous_mode_enabled: Optional[bool] = ...) -> None: ...

class CheckHandleQuery(LongshotModel):
    handle: str
    def __init__(self, *, handle: str) -> None: ...

class ProfileResponse(LongshotModel):
    handle: str
    display_name: str
    avatar_seed: int
    email: Optional[str]
    x_handle: Optional[str]
    x_avatar_url: Optional[str]
    created_at_ms: int
    updated_at_ms: int
    referral_code: Optional[str]
    def __init__(self, *, handle: str, display_name: str, avatar_seed: int, email: Optional[str] = ..., x_handle: Optional[str] = ..., x_avatar_url: Optional[str] = ..., created_at_ms: int, updated_at_ms: int, referral_code: Optional[str] = ...) -> None: ...

class UpdateProfileRequest(LongshotModel):
    handle: Optional[str]
    display_name: Optional[str]
    def __init__(self, *, handle: Optional[str] = ..., display_name: Optional[str] = ...) -> None: ...

class CheckHandleResponse(LongshotModel):
    available: bool
    reason: Optional[str]
    def __init__(self, *, available: bool, reason: Optional[str] = ...) -> None: ...

class WalletAuthRequest(LongshotModel):
    address: str
    signature: str
    signed_at_ms: int
    referral_code: Optional[str]
    def __init__(self, *, address: str, signature: str, signed_at_ms: int, referral_code: Optional[str] = ...) -> None: ...

class UserDepositRequest(LongshotModel):
    amount_micros: int
    idempotency_key: str
    def __init__(self, *, amount_micros: int, idempotency_key: str) -> None: ...

class UserWithdrawParams(LongshotModel):
    amount_micros: int
    destination_address: Optional[str]
    idempotency_key: str
    def __init__(self, *, amount_micros: int, destination_address: Optional[str] = ..., idempotency_key: str) -> None: ...

class WithdrawalAuthorization(RustTaggedUnion):
    @classmethod
    def wallet_signature(cls, payload: Any=None, **fields: Any) -> WithdrawalAuthorization:
        ...

class UserWithdrawRequest(LongshotModel):
    withdraw_params: UserWithdrawParams
    authorization: WithdrawalAuthorization
    def __init__(self, *, withdraw_params: UserWithdrawParams, authorization: WithdrawalAuthorization) -> None: ...

def build_wallet_authentication_message(domain: str, auth_address: Address | str, signed_at_ms: int) -> str:
    ...

def build_wallet_withdrawal_authorization_message(domain: str, chain_id: int, auth_address: Address | str, destination_address: Address | str, amount_micros: int, idempotency_key: UUID | str, signed_at_ms: int) -> str:
    ...

def encode_wallet_signature(signature: bytes) -> str:
    ...

class OrderLegJson(LongshotModel):
    market_id: int
    direction: str
    def __init__(self, *, market_id: int, direction: str) -> None: ...
    def parse(self: OrderLegJson) -> ParsedOrderLeg:
        ...
    @classmethod
    def from_order_leg(cls, leg: OrderLeg) -> OrderLegJson:
        ...

class SignedOrderJson(LongshotModel):
    user: str
    wager_micros: int
    min_odds: float
    legs: List[OrderLegJson]
    nonce: int
    expires_at_ms: int
    order_type: Optional[int]
    shield_on: bool
    signature: str
    def __init__(self, *, user: str, wager_micros: int, min_odds: float, legs: List[OrderLegJson], nonce: int, expires_at_ms: int, order_type: Optional[int] = ..., shield_on: bool, signature: str) -> None: ...
    @classmethod
    def from_signed_order(cls, order: SignedOrder) -> SignedOrderJson:
        ...
    def to_signed_order(self: SignedOrderJson) -> SignedOrder:
        ...

class CreateRfqRequest(LongshotModel):
    order: SignedOrderJson
    use_app_tokens: bool
    def __init__(self, *, order: SignedOrderJson, use_app_tokens: bool) -> None: ...
    @classmethod
    def from_signed_order(cls, order: SignedOrder, use_app_tokens: bool) -> CreateRfqRequest:
        ...

class ParsedOrderLeg(LongshotModel):
    market_id: Optional[MarketId]
    direction: Optional[Direction]
    def __init__(self, *, market_id: Optional[MarketId] = ..., direction: Optional[Direction] = ...) -> None: ...

class OrderLegParseError(RustTaggedUnion):
    @classmethod
    def invalid_market_id(cls, payload: Any=None, **fields: Any) -> OrderLegParseError:
        ...
    @classmethod
    def invalid_direction(cls, payload: Any=None, **fields: Any) -> OrderLegParseError:
        ...

class RfqOrderJsonError(RustTaggedUnion):
    @classmethod
    def invalid_address(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_min_odds(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def missing_legs(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def too_many_legs(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_order_type(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_signature_format(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_idempotency_key(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_leg_market_id(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...
    @classmethod
    def invalid_leg_direction(cls, payload: Any=None, **fields: Any) -> RfqOrderJsonError:
        ...

class AccessResponse(LongshotModel):
    position_opening_allowed: bool
    reason_code: Optional[str]
    def __init__(self, *, position_opening_allowed: bool, reason_code: Optional[str] = ...) -> None: ...

class SessionResponse(LongshotModel):
    session_token: str
    address: str
    auth_wallet_address: str
    deposit_address: Optional[str]
    deposit_chain_id: Optional[int]
    user_id: str
    expires_at: int
    account_created: Optional[bool]
    def __init__(self, *, session_token: str, address: str, auth_wallet_address: str, deposit_address: Optional[str] = ..., deposit_chain_id: Optional[int] = ..., user_id: str, expires_at: int, account_created: Optional[bool] = ...) -> None: ...
    def __repr__(self) -> str:
        ...

class RfqStatus(RustStringEnum):
    Pending = 'pending'
    Finalizing = 'finalizing'
    Completed = 'completed'
    Failed = 'failed'
    Cancelled = 'cancelled'
    Timeout = 'timeout'

class RfqResponse(LongshotModel):
    request_id: UUID
    status: RfqStatus
    odds: Optional[float]
    payout_micros: Optional[int]
    error: Optional[str]
    quotes_received: int
    def __init__(self, *, request_id: UUID, status: RfqStatus, odds: Optional[float] = ..., payout_micros: Optional[int] = ..., error: Optional[str] = ..., quotes_received: int) -> None: ...

class CancelResponse(LongshotModel):
    request_id: str
    cancelled: bool
    message: str
    def __init__(self, *, request_id: str, cancelled: bool, message: str) -> None: ...

class UserDepositResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    tx_hash: str
    def __init__(self, *, amount_micros: int, operation_id: UUID, tx_hash: str) -> None: ...

class UserDepositWalletResponse(LongshotModel):
    address: str
    chain_id: int
    token_symbol: str
    token_decimals: int
    def __init__(self, *, address: str, chain_id: int, token_symbol: str, token_decimals: int) -> None: ...

class WithdrawalStage(RustStringEnum):
    Processing = 'processing'
    Held = 'held'
    OnchainQueued = 'onchain_queued'
    Completed = 'completed'
    Failed = 'failed'

class UserWithdrawResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    destination_address: Optional[str]
    tx_hash: str
    withdrawal_stage: Optional[WithdrawalStage]
    available_at_ms: Optional[int]
    submission_tx_hash: Optional[str]
    def __init__(self, *, amount_micros: int, operation_id: UUID, destination_address: Optional[str] = ..., tx_hash: str, withdrawal_stage: Optional[WithdrawalStage] = ..., available_at_ms: Optional[int] = ..., submission_tx_hash: Optional[str] = ...) -> None: ...

class BalanceOperationStatus(RustStringEnum):
    Pending = 'pending'
    Failed = 'failed'
    Success = 'success'
    Recovering = 'recovering'

class BalanceOperationStatusResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    status: BalanceOperationStatus
    wallet_address: Optional[str]
    withdrawal_stage: Optional[WithdrawalStage]
    available_at_ms: Optional[int]
    submission_tx_hash: Optional[str]
    tx_hash: Optional[str]
    def __init__(self, *, amount_micros: int, operation_id: UUID, status: BalanceOperationStatus, wallet_address: Optional[str] = ..., withdrawal_stage: Optional[WithdrawalStage] = ..., available_at_ms: Optional[int] = ..., submission_tx_hash: Optional[str] = ..., tx_hash: Optional[str] = ...) -> None: ...

class DepositOperationResponse(RustTaggedUnion):
    @classmethod
    def completed(cls, payload: Any=None, **fields: Any) -> DepositOperationResponse:
        ...
    @classmethod
    def operation_status(cls, payload: Any=None, **fields: Any) -> DepositOperationResponse:
        ...

class WithdrawOperationResponse(RustTaggedUnion):
    @classmethod
    def completed(cls, payload: Any=None, **fields: Any) -> WithdrawOperationResponse:
        ...
    @classmethod
    def operation_status(cls, payload: Any=None, **fields: Any) -> WithdrawOperationResponse:
        ...

class ReservedBalanceResponse(LongshotModel):
    reserved_micros: int
    def __init__(self, *, reserved_micros: int) -> None: ...

class UserTransactionCategory(RustStringEnum):
    Deposit = 'deposit'
    Withdrawal = 'withdrawal'
    Credits = 'credits'
    Market = 'market'
    Contest = 'contest'

class UserTransactionStatus(RustStringEnum):
    Completed = 'completed'
    Pending = 'pending'
    Failed = 'failed'
    Expired = 'expired'
    Entered = 'entered'
    Won = 'won'

class UserTransactionUnit(RustStringEnum):
    Usdc = 'usdc'
    Credits = 'credits'

class UserTransactionFunding(RustStringEnum):
    Cash = 'cash'
    Credits = 'credits'
    CashAndCredits = 'cash_and_credits'

class UserTransactionResponse(LongshotModel):
    id: str
    category: UserTransactionCategory
    title: str
    detail: Optional[str]
    status: UserTransactionStatus
    occurred_at_ms: int
    amount_micros: int
    unit: UserTransactionUnit
    funding: Optional[UserTransactionFunding]
    network: Optional[str]
    wallet_address: Optional[str]
    tx_hash: Optional[str]
    source: Optional[str]
    expires_at_ms: Optional[int]
    reason: Optional[str]
    reference: Optional[str]
    withdrawal_stage: Optional[WithdrawalStage]
    available_at_ms: Optional[int]
    submission_tx_hash: Optional[str]
    def __init__(self, *, id: str, category: UserTransactionCategory, title: str, detail: Optional[str] = ..., status: UserTransactionStatus, occurred_at_ms: int, amount_micros: int, unit: UserTransactionUnit, funding: Optional[UserTransactionFunding] = ..., network: Optional[str] = ..., wallet_address: Optional[str] = ..., tx_hash: Optional[str] = ..., source: Optional[str] = ..., expires_at_ms: Optional[int] = ..., reason: Optional[str] = ..., reference: Optional[str] = ..., withdrawal_stage: Optional[WithdrawalStage] = ..., available_at_ms: Optional[int] = ..., submission_tx_hash: Optional[str] = ...) -> None: ...

class UserTransactionsResponse(LongshotModel):
    items: List[UserTransactionResponse]
    next_cursor: Optional[str]
    def __init__(self, *, items: List[UserTransactionResponse], next_cursor: Optional[str] = ...) -> None: ...

class FeeScheduleTier(RustStringEnum):
    Standard = 'standard'
    Silver = 'silver'
    Gold = 'gold'
    Platinum = 'platinum'
    Vip = 'vip'

class TierFeeRate(LongshotModel):
    tier: FeeScheduleTier
    parlay_fee_bps: int
    def __init__(self, *, tier: FeeScheduleTier, parlay_fee_bps: int) -> None: ...

class FeeScheduleResponse(LongshotModel):
    user_tier: FeeScheduleTier
    parlay_fee_bps: int
    spot_fee_bps: int
    bonding_spot_fee_bps: int
    shield_fee_multiplier: int
    tiers: List[TierFeeRate]
    def __init__(self, *, user_tier: FeeScheduleTier, parlay_fee_bps: int, spot_fee_bps: int, bonding_spot_fee_bps: int, shield_fee_multiplier: int, tiers: List[TierFeeRate]) -> None: ...

class ErrorResponse(LongshotModel):
    error: str
    code: str
    details: Optional[str]
    def __init__(self, *, error: str, code: str, details: Optional[str] = ...) -> None: ...
    @classmethod
    def new(cls, error: Any, code: Any) -> ErrorResponse:
        ...
    def with_details(self: ErrorResponse, details: Any) -> ErrorResponse:
        ...

class UserTransactionsRawQuery(LongshotModel):
    category: Optional[str]
    from_ms: Optional[str]
    to_ms: Optional[str]
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, category: Optional[str] = ..., from_ms: Optional[str] = ..., to_ms: Optional[str] = ..., limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class ConfirmPositionQuery(LongshotModel):
    position_id: str
    accept: bool
    def __init__(self, *, position_id: str, accept: bool) -> None: ...

class RfqEstimateRequest(LongshotModel):
    wager_micros: int
    legs: List[OrderLegJson]
    shield_on: Optional[bool]
    def __init__(self, *, wager_micros: int, legs: List[OrderLegJson], shield_on: Optional[bool] = ...) -> None: ...

class RfqEstimateResponse(LongshotModel):
    request_id: UUID
    quotable: bool
    odds: Optional[float]
    fillable_micros: Optional[int]
    quotes_received: int
    quoted_at_ms: int
    reason: Optional[str]
    def __init__(self, *, request_id: UUID, quotable: bool, odds: Optional[float] = ..., fillable_micros: Optional[int] = ..., quotes_received: int, quoted_at_ms: int, reason: Optional[str] = ...) -> None: ...

class MmRfqStatusResponse(LongshotModel):
    request_id: str
    status: RfqStatus
    def __init__(self, *, request_id: str, status: RfqStatus) -> None: ...

class UserAvailableBalanceResponse(LongshotModel):
    available_micros: int
    pending_custodial_deposit_micros: int
    credited_custodial_deposit_micros: int
    deposit_withdrawal_min_micros: int
    withdrawal_max_micros: int
    def __init__(self, *, available_micros: int, pending_custodial_deposit_micros: int, credited_custodial_deposit_micros: int, deposit_withdrawal_min_micros: int, withdrawal_max_micros: int) -> None: ...

class WithdrawalDeliveryStatus(RustStringEnum):
    Queued = 'queued'

class QueuedWithdrawalResponse(LongshotModel):
    amount_micros: int
    operation_id: UUID
    destination_address: Optional[str]
    delivery_status: WithdrawalDeliveryStatus
    withdrawal_stage: WithdrawalStage
    available_at_ms: int
    submission_tx_hash: str
    def __init__(self, *, amount_micros: int, operation_id: UUID, destination_address: Optional[str] = ..., delivery_status: WithdrawalDeliveryStatus, withdrawal_stage: WithdrawalStage, available_at_ms: int, submission_tx_hash: str) -> None: ...

class ActiveWithdrawalResponse(LongshotModel):
    operation_id: UUID
    amount_micros: int
    destination_address: Optional[str]
    withdrawal_stage: WithdrawalStage
    created_at_ms: int
    available_at_ms: Optional[int]
    submission_tx_hash: Optional[str]
    def __init__(self, *, operation_id: UUID, amount_micros: int, destination_address: Optional[str] = ..., withdrawal_stage: WithdrawalStage, created_at_ms: int, available_at_ms: Optional[int] = ..., submission_tx_hash: Optional[str] = ...) -> None: ...

class UserWithdrawalStateResponse(LongshotModel):
    withdrawals_available: bool
    hold_trigger_amount_micros: int
    hold_threshold_micros: int
    hold_window_ms: int
    hold_duration_ms: int
    active_withdrawals: List[ActiveWithdrawalResponse]
    def __init__(self, *, withdrawals_available: bool, hold_trigger_amount_micros: int, hold_threshold_micros: int, hold_window_ms: int, hold_duration_ms: int, active_withdrawals: List[ActiveWithdrawalResponse]) -> None: ...

class AcceptedWithdrawOperationResponse(RustTaggedUnion):
    @classmethod
    def queued(cls, payload: Any=None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        ...
    @classmethod
    def recovery(cls, payload: Any=None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        ...

class PublicReferralStatusResponse(RustStringEnum):
    Valid = 'valid'
    Redeemed = 'redeemed'
    Expired = 'expired'

class PublicReferralInviterResponse(LongshotModel):
    display_name: str
    avatar_seed: int
    avatar_url: Optional[str]
    def __init__(self, *, display_name: str, avatar_seed: int, avatar_url: Optional[str] = ...) -> None: ...

class PublicReferralDepositMatchOffer(LongshotModel):
    match_limit_micros: int
    duration_ms: int
    def __init__(self, *, match_limit_micros: int, duration_ms: int) -> None: ...

class PublicReferralCodeResponse(LongshotModel):
    status: PublicReferralStatusResponse
    inviter: Optional[PublicReferralInviterResponse]
    deposit_match: Optional[PublicReferralDepositMatchOffer]
    def __init__(self, *, status: PublicReferralStatusResponse, inviter: Optional[PublicReferralInviterResponse] = ..., deposit_match: Optional[PublicReferralDepositMatchOffer] = ...) -> None: ...

class PnlHistoryScopedQuery(LongshotModel):
    from_: Optional[int]
    to: Optional[int]
    scope: Optional[str]
    def __init__(self, *, from_: Optional[int] = ..., to: Optional[int] = ..., scope: Optional[str] = ...) -> None: ...

class PositionsByMarketsQuery(LongshotModel):
    market_ids: str
    limit: Optional[int]
    cursor: Optional[str]
    def __init__(self, *, market_ids: str, limit: Optional[int] = ..., cursor: Optional[str] = ...) -> None: ...

class PositionsByMarketsResponse(LongshotModel):
    positions: List[PositionDetailResponse]
    next_cursor: Optional[str]
    def __init__(self, *, positions: List[PositionDetailResponse], next_cursor: Optional[str] = ...) -> None: ...

class HandleAvailabilityQuery(LongshotModel):
    handle: str
    def __init__(self, *, handle: str) -> None: ...

__all__ = [
    "PublicMarketsRawQuery",
    "PriceStrikeMarket",
    "EventMarket",
    "PublicMarket",
    "PublicMarketResponse",
    "PublicMarketsResponse",
    "MarketMetadataEntry",
    "MarketLookupResponse",
    "MarketLookupQuery",
    "MarketCurrentQuery",
    "RecentResolutionsQuery",
    "RecentResolutionEntry",
    "RecentResolutionsResponse",
    "ProfitCapOverrideResponse",
    "ProfitCapConfigResponse",
    "PortfolioStatsResponse",
    "PnlHistoryQuery",
    "PnlEventResponse",
    "PnlHistoryResponse",
    "PositionsQuery",
    "PositionStatusQueryParam",
    "PositionSortQueryParam",
    "PositionSummary",
    "PositionsListResponse",
    "ActivePositionStatus",
    "PositionRole",
    "ActivePosition",
    "ActivePositionsResponse",
    "LegDetail",
    "PositionDetailResponse",
    "PreferencesResponse",
    "QuoteTolerancePreference",
    "UpdatePreferencesRequest",
    "CheckHandleQuery",
    "ProfileResponse",
    "UpdateProfileRequest",
    "CheckHandleResponse",
    "WalletAuthRequest",
    "UserDepositRequest",
    "UserWithdrawParams",
    "WithdrawalAuthorization",
    "UserWithdrawRequest",
    "build_wallet_authentication_message",
    "build_wallet_withdrawal_authorization_message",
    "encode_wallet_signature",
    "OrderLegJson",
    "SignedOrderJson",
    "CreateRfqRequest",
    "ParsedOrderLeg",
    "OrderLegParseError",
    "RfqOrderJsonError",
    "AccessResponse",
    "SessionResponse",
    "RfqStatus",
    "RfqResponse",
    "CancelResponse",
    "UserDepositResponse",
    "UserDepositWalletResponse",
    "WithdrawalStage",
    "UserWithdrawResponse",
    "BalanceOperationStatus",
    "BalanceOperationStatusResponse",
    "DepositOperationResponse",
    "WithdrawOperationResponse",
    "ReservedBalanceResponse",
    "UserTransactionCategory",
    "UserTransactionStatus",
    "UserTransactionUnit",
    "UserTransactionFunding",
    "UserTransactionResponse",
    "UserTransactionsResponse",
    "FeeScheduleTier",
    "TierFeeRate",
    "FeeScheduleResponse",
    "ErrorResponse",
    "UserTransactionsRawQuery",
    "ConfirmPositionQuery",
    "RfqEstimateRequest",
    "RfqEstimateResponse",
    "MmRfqStatusResponse",
    "UserAvailableBalanceResponse",
    "WithdrawalDeliveryStatus",
    "QueuedWithdrawalResponse",
    "ActiveWithdrawalResponse",
    "UserWithdrawalStateResponse",
    "AcceptedWithdrawOperationResponse",
    "PublicReferralStatusResponse",
    "PublicReferralInviterResponse",
    "PublicReferralDepositMatchOffer",
    "PublicReferralCodeResponse",
    "PnlHistoryScopedQuery",
    "PositionsByMarketsQuery",
    "PositionsByMarketsResponse",
    "HandleAvailabilityQuery",
]
