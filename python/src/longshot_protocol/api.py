# Hand-maintained Python mirror of rust/src/api/*.rs; parity is enforced by tests.
# Keep shared behavior in longshot_protocol.model and helper functions below.

from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from math import ceil, floor, isfinite
from typing import Any, Dict, List, Optional
from uuid import UUID

from ._serde_metadata import (
    DENY_UNKNOWN_TAGGED_UNIONS,
    STRUCT_INTEGER_FIELDS,
    STRUCT_REQUIRED_FIELDS,
    STRUCT_REQUIRED_NULLABLE_FIELDS,
    TAGGED_UNION_FIELDS,
)
from .model import LongshotModel, RustStringEnum, RustTaggedUnion, _install_serde_metadata
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


@dataclass
class PublicMarketsRawQuery(LongshotModel):
    __serde_skip_none__ = set(["statuses"])
    __serde_query_csv__ = set(["statuses"])
    market_type: Optional[MarketType] = None
    trading_channel: Optional[TradingChannel] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None
    # Statuses use one CSV query value to match the Rust form adapter.
    statuses: Optional[List[MarketStatus]] = None

@dataclass
class PriceStrikeMarket(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    id: Optional[MarketId] = None
    market_type: Optional[MarketType] = None
    trading_channels: Optional[List[TradingChannel]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MarketStatus] = None
    tradeable: Optional[bool] = None
    category_tags: Optional[List[str]] = None
    betting_closes_at_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None
    open_strike_micros: Optional[int] = None
    resolved_outcome: Optional[Outcome] = None
    created_at_ms: Optional[int] = None
    opened_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    image_url: Optional[str] = None

@dataclass
class EventMarket(LongshotModel):
    __serde_skip_none__ = set(["image_url"])
    id: Optional[MarketId] = None
    market_type: Optional[MarketType] = None
    trading_channels: Optional[List[TradingChannel]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    resolution_rules: Optional[str] = None
    status: Optional[MarketStatus] = None
    tradeable: Optional[bool] = None
    category_tags: Optional[List[str]] = None
    opens_at_ms: Optional[int] = None
    # Original event start, distinct from Longshot's lifecycle opens_at_ms.
    source_starts_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None
    live_ends_at_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None
    resolved_outcome: Optional[Outcome] = None
    created_at_ms: Optional[int] = None
    opened_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    display_probability_bps: Optional[int] = None
    image_url: Optional[str] = None

class PublicMarket(RustTaggedUnion):
    __serde_tag__ = None
    __serde_untagged__ = True
    __serde_variants__ = {
            "Event": "Event",
            "PriceStrike": "PriceStrike"
    }

    @classmethod
    def event(cls, payload: Any = None, **fields: Any) -> PublicMarket:
        return cls("Event", payload, **fields)

    @classmethod
    def price_strike(cls, payload: Any = None, **fields: Any) -> PublicMarket:
        return cls("PriceStrike", payload, **fields)

@dataclass
class PublicMarketResponse(LongshotModel):
    market: Optional[PublicMarket] = None

@dataclass
class PublicMarketsResponse(LongshotModel):
    markets: Optional[List[PublicMarket]] = None
    next_cursor: Optional[str] = None

@dataclass
class MarketMetadataEntry(LongshotModel):
    market_id: Optional[int] = None
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    start_at_ms: Optional[int] = None
    betting_closes_at_ms: Optional[int] = None

@dataclass
class MarketLookupResponse(LongshotModel):
    market: Optional[MarketMetadataEntry] = None

@dataclass
class MarketLookupQuery(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    window_start_ms: Optional[int] = None

@dataclass
class MarketCurrentQuery(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None

@dataclass
class RecentResolutionsQuery(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    limit: Optional[int] = None

@dataclass
class RecentResolutionEntry(LongshotModel):
    market_id: Optional[int] = None
    outcome: Optional[str] = None
    window_start_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None

@dataclass
class RecentResolutionsResponse(LongshotModel):
    asset: Optional[str] = None
    duration_secs: Optional[int] = None
    resolutions: Optional[List[RecentResolutionEntry]] = None

@dataclass
class ProfitCapOverrideResponse(LongshotModel):
    market_type: Optional[MarketType] = None
    max_profit_micros: Optional[int] = None

@dataclass
class ProfitCapConfigResponse(LongshotModel):
    default_max_profit_micros: Optional[int] = None
    overrides: Optional[List[ProfitCapOverrideResponse]] = None


@dataclass
class PortfolioStatsResponse(LongshotModel):
    total_positions: Optional[int] = None
    open_positions: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    win_rate_pct: Optional[float] = None
    total_pnl_micros: Optional[int] = None


@dataclass
class PnlHistoryQuery(LongshotModel):
    __serde_renames__ = {"from_":"from"}
    from_: Optional[int] = None
    to: Optional[int] = None

@dataclass
class PnlEventResponse(LongshotModel):
    source: Optional[str] = None
    resolved_at_ms: Optional[int] = None
    position_id: Optional[str] = None
    contest_id: Optional[str] = None
    pnl_micros: Optional[int] = None
    cumulative_micros: Optional[int] = None

@dataclass
class PnlHistoryResponse(LongshotModel):
    events: Optional[List[PnlEventResponse]] = None


@dataclass
class PositionsQuery(LongshotModel):
    status: Optional[str] = None
    sort: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

class PositionStatusQueryParam(RustStringEnum):
    Open = "open"
    Won = "won"
    Lost = "lost"
    Voided = "voided"

class PositionSortQueryParam(RustStringEnum):
    DateDesc = "date_desc"
    DateAsc = "date_asc"
    PnlDesc = "pnl_desc"
    PnlAsc = "pnl_asc"


@dataclass
class PositionSummary(LongshotModel):
    id: Optional[str] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    refunded_app_token_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    legs_count: Optional[int] = None
    legs_summary: Optional[str] = None
    status: Optional[str] = None
    pnl_micros: Optional[int] = None
    created_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    has_binary_event_leg: Optional[bool] = None
    market_types: Optional[List[MarketType]] = None

@dataclass
class PositionsListResponse(LongshotModel):
    positions: Optional[List[PositionSummary]] = None
    next_cursor: Optional[str] = None
    partial: Optional[bool] = None

class ActivePositionStatus(RustStringEnum):
    Pending = "pending"
    Open = "open"

class PositionRole(RustStringEnum):
    Taker = "taker"
    Maker = "maker"

@dataclass
class ActivePosition(LongshotModel):
    """Active taker or maker position in a complete portfolio snapshot."""

    position_id: Optional[PositionId] = None
    status: Optional[ActivePositionStatus] = None
    role: Optional[PositionRole] = None
    taker_address: Optional[Address] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    legs: Optional[List[LegDetail]] = None

@dataclass
class ActivePositionsResponse(LongshotModel):
    positions: Optional[List[ActivePosition]] = None

@dataclass
class LegDetail(LongshotModel):
    __serde_skip_none__ = set(["market_type","label","asset","duration_secs","window_start_ms"])
    leg_index: Optional[int] = None
    market_id: Optional[int] = None
    market_type: Optional[MarketType] = None
    label: Optional[str] = None
    asset: Optional[str] = None
    direction: Optional[str] = None
    duration_secs: Optional[int] = None
    outcome: Optional[str] = None
    window_start_ms: Optional[int] = None
    resolution_time_ms: Optional[int] = None

@dataclass
class PositionDetailResponse(LongshotModel):
    id: Optional[str] = None
    wager_micros: Optional[int] = None
    app_token_wager_micros: Optional[int] = None
    refunded_app_token_micros: Optional[int] = None
    payout_micros: Optional[int] = None
    net_payout_micros: Optional[int] = None
    legs_count: Optional[int] = None
    legs_summary: Optional[str] = None
    status: Optional[str] = None
    pnl_micros: Optional[int] = None
    created_at_ms: Optional[int] = None
    resolved_at_ms: Optional[int] = None
    legs: Optional[List[LegDetail]] = None

@dataclass
class PreferencesResponse(LongshotModel):
    notifications_enabled: Optional[bool] = None
    quote_tolerance: Optional[QuoteTolerancePreference] = None
    anonymous_mode_enabled: Optional[bool] = None

class QuoteTolerancePreference(RustStringEnum):
    Strict = "strict"
    Normal = "normal"
    Lenient = "lenient"

@dataclass
class UpdatePreferencesRequest(LongshotModel):
    notifications_enabled: Optional[bool] = None
    quote_tolerance: Optional[QuoteTolerancePreference] = None
    anonymous_mode_enabled: Optional[bool] = None


@dataclass
class CheckHandleQuery(LongshotModel):
    handle: Optional[str] = None

@dataclass
class ProfileResponse(LongshotModel):
    __serde_skip_none__ = set(["email","x_handle","x_avatar_url"])
    handle: Optional[str] = None
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    email: Optional[str] = None
    x_handle: Optional[str] = None
    x_avatar_url: Optional[str] = None
    created_at_ms: Optional[int] = None
    updated_at_ms: Optional[int] = None
    referral_code: Optional[str] = None


@dataclass
class UpdateProfileRequest(LongshotModel):
    handle: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class CheckHandleResponse(LongshotModel):
    __serde_skip_none__ = set(["reason"])
    available: Optional[bool] = None
    reason: Optional[str] = None


@dataclass(repr=False)
class WalletAuthRequest(LongshotModel):
    __serde_skip_none__ = set(["referral_code"])
    __repr_redacted_fields__ = {"signature"}
    address: Optional[str] = None
    signature: Optional[str] = None
    signed_at_ms: Optional[int] = None
    referral_code: Optional[str] = None


@dataclass
class UserDepositRequest(LongshotModel):
    amount_micros: Optional[int] = None
    idempotency_key: Optional[str] = None

@dataclass
class UserWithdrawParams(LongshotModel):
    amount_micros: Optional[int] = None
    destination_address: Optional[str] = None
    idempotency_key: Optional[str] = None

class WithdrawalAuthorization(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "WalletSignature": "wallet_signature"
    }
    __repr_redacted_fields__ = {"token", "signature"}

    @classmethod
    def wallet_signature(cls, payload: Any = None, **fields: Any) -> WithdrawalAuthorization:
        return cls("WalletSignature", payload, **fields)

@dataclass
class UserWithdrawRequest(LongshotModel):
    withdraw_params: Optional[UserWithdrawParams] = None
    authorization: Optional[WithdrawalAuthorization] = None

@dataclass
class OrderLegJson(LongshotModel):
    market_id: Optional[int] = None
    direction: Optional[str] = None

@dataclass
class SignedOrderJson(LongshotModel):
    user: Optional[str] = None
    wager_micros: Optional[int] = None
    min_odds: Optional[float] = None
    legs: Optional[List[OrderLegJson]] = None
    nonce: Optional[int] = None
    expires_at_ms: Optional[int] = None
    order_type: Optional[int] = None
    shield_on: Optional[bool] = None
    signature: Optional[str] = None

@dataclass
class CreateRfqRequest(LongshotModel):
    order: Optional[SignedOrderJson] = None
    use_app_tokens: Optional[bool] = None

@dataclass
class ParsedOrderLeg(LongshotModel):
    market_id: Optional[MarketId] = None
    direction: Optional[Direction] = None

class OrderLegParseError(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "InvalidMarketId": "InvalidMarketId",
            "InvalidDirection": "InvalidDirection"
    }

    @classmethod
    def invalid_market_id(cls, payload: Any = None, **fields: Any) -> OrderLegParseError:
        return cls("InvalidMarketId", payload, **fields)

    @classmethod
    def invalid_direction(cls, payload: Any = None, **fields: Any) -> OrderLegParseError:
        return cls("InvalidDirection", payload, **fields)

class RfqOrderJsonError(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
            "InvalidAddress": "InvalidAddress",
            "InvalidMinOdds": "InvalidMinOdds",
            "MissingLegs": "MissingLegs",
            "TooManyLegs": "TooManyLegs",
            "InvalidOrderType": "InvalidOrderType",
            "InvalidSignatureFormat": "InvalidSignatureFormat",
            "InvalidIdempotencyKey": "InvalidIdempotencyKey",
            "InvalidLegMarketId": "InvalidLegMarketId",
            "InvalidLegDirection": "InvalidLegDirection"
    }

    @classmethod
    def invalid_address(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidAddress", payload, **fields)

    @classmethod
    def invalid_min_odds(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidMinOdds", payload, **fields)

    @classmethod
    def missing_legs(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("MissingLegs", payload, **fields)

    @classmethod
    def too_many_legs(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("TooManyLegs", payload, **fields)

    @classmethod
    def invalid_order_type(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidOrderType", payload, **fields)

    @classmethod
    def invalid_signature_format(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidSignatureFormat", payload, **fields)

    @classmethod
    def invalid_idempotency_key(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidIdempotencyKey", payload, **fields)

    @classmethod
    def invalid_leg_market_id(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidLegMarketId", payload, **fields)

    @classmethod
    def invalid_leg_direction(cls, payload: Any = None, **fields: Any) -> RfqOrderJsonError:
        return cls("InvalidLegDirection", payload, **fields)

@dataclass
class AccessResponse(LongshotModel):
    __serde_skip_none__ = set(["reason_code"])
    position_opening_allowed: Optional[bool] = None
    reason_code: Optional[str] = None

@dataclass
class SessionResponse(LongshotModel):
    __serde_skip_none__ = set(["deposit_address","deposit_chain_id"])
    session_token: Optional[str] = None
    address: Optional[str] = None
    auth_wallet_address: Optional[str] = None
    deposit_address: Optional[str] = None
    deposit_chain_id: Optional[int] = None
    user_id: Optional[str] = None
    expires_at: Optional[int] = None
    account_created: Optional[bool] = False

    def __repr__(self) -> str:
        session_token = "'<redacted>'" if self.session_token else "None"
        return (
            "SessionResponse("
            f"session_token={session_token}"
            f", address={self.address!r}"
            f", auth_wallet_address={self.auth_wallet_address!r}"
            f", deposit_address={self.deposit_address!r}"
            f", deposit_chain_id={self.deposit_chain_id!r}"
            f", user_id={self.user_id!r}"
            f", expires_at={self.expires_at!r}"
            f", account_created={self.account_created!r})"
        )

class RfqStatus(RustStringEnum):
    Pending = "pending"
    Finalizing = "finalizing"
    Completed = "completed"
    Failed = "failed"
    Cancelled = "cancelled"
    Timeout = "timeout"

@dataclass
class RfqResponse(LongshotModel):
    __serde_skip_none__ = set(["payout_micros","error"])
    __serde_skip_non_finite__ = set(["odds"])
    request_id: Optional[UUID] = None
    status: Optional[RfqStatus] = None
    odds: Optional[float] = None
    payout_micros: Optional[int] = None
    error: Optional[str] = None
    quotes_received: Optional[int] = None

@dataclass
class CancelResponse(LongshotModel):
    request_id: Optional[str] = None
    cancelled: Optional[bool] = None
    message: Optional[str] = None

@dataclass
class UserDepositResponse(LongshotModel):
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    tx_hash: Optional[str] = None

@dataclass
class UserDepositWalletResponse(LongshotModel):
    address: Optional[str] = None
    chain_id: Optional[int] = None
    token_symbol: Optional[str] = None
    token_decimals: Optional[int] = None

class WithdrawalStage(RustStringEnum):
    Processing = "processing"
    Held = "held"
    OnchainQueued = "onchain_queued"
    Completed = "completed"
    Failed = "failed"

@dataclass
class UserWithdrawResponse(LongshotModel):
    __serde_skip_none__ = set(["available_at_ms","destination_address","submission_tx_hash","withdrawal_stage"])
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    destination_address: Optional[str] = None
    tx_hash: Optional[str] = None
    withdrawal_stage: Optional[WithdrawalStage] = None
    available_at_ms: Optional[int] = None
    submission_tx_hash: Optional[str] = None

class BalanceOperationStatus(RustStringEnum):
    Pending = "pending"
    Failed = "failed"
    Success = "success"
    Recovering = "recovering"

@dataclass
class BalanceOperationStatusResponse(LongshotModel):
    __serde_skip_none__ = set(["available_at_ms","submission_tx_hash","tx_hash","wallet_address","withdrawal_stage"])
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    status: Optional[BalanceOperationStatus] = None
    wallet_address: Optional[str] = None
    withdrawal_stage: Optional[WithdrawalStage] = None
    available_at_ms: Optional[int] = None
    submission_tx_hash: Optional[str] = None
    tx_hash: Optional[str] = None

class DepositOperationResponse(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {
            "Completed": "Completed",
            "OperationStatus": "OperationStatus"
    }

    @classmethod
    def completed(cls, payload: Any = None, **fields: Any) -> DepositOperationResponse:
        return cls("Completed", payload, **fields)

    @classmethod
    def operation_status(cls, payload: Any = None, **fields: Any) -> DepositOperationResponse:
        return cls("OperationStatus", payload, **fields)

class WithdrawOperationResponse(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {
            "Completed": "Completed",
            "OperationStatus": "OperationStatus"
    }

    @classmethod
    def completed(cls, payload: Any = None, **fields: Any) -> WithdrawOperationResponse:
        return cls("Completed", payload, **fields)

    @classmethod
    def operation_status(cls, payload: Any = None, **fields: Any) -> WithdrawOperationResponse:
        return cls("OperationStatus", payload, **fields)

@dataclass
class ReservedBalanceResponse(LongshotModel):
    reserved_micros: Optional[int] = None

class UserTransactionCategory(RustStringEnum):
    Deposit = "deposit"
    Withdrawal = "withdrawal"
    Credits = "credits"
    Market = "market"
    Contest = "contest"

class UserTransactionStatus(RustStringEnum):
    Completed = "completed"
    Pending = "pending"
    Failed = "failed"
    Expired = "expired"
    Entered = "entered"
    Won = "won"

class UserTransactionUnit(RustStringEnum):
    Usdc = "usdc"
    Credits = "credits"

class UserTransactionFunding(RustStringEnum):
    Cash = "cash"
    Credits = "credits"
    CashAndCredits = "cash_and_credits"

@dataclass
class UserTransactionResponse(LongshotModel):
    __serde_skip_none__ = set(["available_at_ms","detail","expires_at_ms","funding","network","reason","reference","source","submission_tx_hash","tx_hash","wallet_address","withdrawal_stage"])
    id: Optional[str] = None
    category: Optional[UserTransactionCategory] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    status: Optional[UserTransactionStatus] = None
    occurred_at_ms: Optional[int] = None
    amount_micros: Optional[int] = None
    unit: Optional[UserTransactionUnit] = None
    funding: Optional[UserTransactionFunding] = None
    network: Optional[str] = None
    wallet_address: Optional[str] = None
    tx_hash: Optional[str] = None
    source: Optional[str] = None
    expires_at_ms: Optional[int] = None
    reason: Optional[str] = None
    reference: Optional[str] = None
    withdrawal_stage: Optional[WithdrawalStage] = None
    available_at_ms: Optional[int] = None
    submission_tx_hash: Optional[str] = None

@dataclass
class UserTransactionsResponse(LongshotModel):
    items: Optional[List[UserTransactionResponse]] = None
    next_cursor: Optional[str] = None

class FeeScheduleTier(RustStringEnum):
    Standard = "standard"
    Silver = "silver"
    Gold = "gold"
    Platinum = "platinum"
    Vip = "vip"

@dataclass
class TierFeeRate(LongshotModel):
    tier: Optional[FeeScheduleTier] = None
    parlay_fee_bps: Optional[int] = None

@dataclass
class FeeScheduleResponse(LongshotModel):
    user_tier: Optional[FeeScheduleTier] = None
    parlay_fee_bps: Optional[int] = None
    spot_fee_bps: Optional[int] = None
    bonding_spot_fee_bps: Optional[int] = None
    shield_fee_multiplier: Optional[int] = None
    tiers: Optional[List[TierFeeRate]] = None


@dataclass
class ErrorResponse(LongshotModel):
    __serde_skip_none__ = set(["details"])
    error: Optional[str] = None
    code: Optional[str] = None
    details: Optional[str] = None


@dataclass
class UserTransactionsRawQuery(LongshotModel):
    category: Optional[str] = None
    from_ms: Optional[str] = None
    to_ms: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class ConfirmPositionQuery(LongshotModel):
    position_id: Optional[str] = None
    accept: Optional[bool] = None


def _direction_to_wire(direction: Direction) -> int:
    return 0 if direction is Direction.Up else 1

def _round_half_away_from_zero(value: float) -> int:
    return floor(value + 0.5) if value >= 0 else ceil(value - 0.5)

def _parse_min_odds_bps(min_odds_decimal: float) -> int:
    if not isfinite(min_odds_decimal):
        raise ValueError("invalid min odds")
    min_odds_bps = _round_half_away_from_zero(min_odds_decimal * 10_000)
    if min_odds_bps <= Odds.EVEN.value or min_odds_bps > Odds.MAX.value:
        raise ValueError("invalid min odds")
    return int(min_odds_bps)

def _order_leg_json_parse(self: OrderLegJson) -> ParsedOrderLeg:
    market_id = _canonical_u64(self.market_id, "market_id")
    if market_id == 0:
        raise ValueError("invalid market id")
    raw_direction = str(self.direction)
    if raw_direction.lower() == "up":
        direction = Direction.Up
    elif raw_direction.lower() == "down":
        direction = Direction.Down
    else:
        raise ValueError("invalid direction")
    return ParsedOrderLeg(market_id=MarketId(market_id), direction=direction)

def _order_leg_json_from_order_leg(cls, leg: OrderLeg) -> OrderLegJson:
    direction = Direction.from_u8(leg.direction)
    if direction is None:
        raise ValueError(f"invalid direction: {leg.direction}")
    raw_market_id = (
        leg.market_id.as_u64() if isinstance(leg.market_id, MarketId) else leg.market_id
    )
    market_id = _canonical_u64(raw_market_id, "market_id")
    return cls(market_id=market_id, direction=direction.name.lower())

def _signed_order_json_from_signed_order(cls, order: SignedOrder) -> SignedOrderJson:
    order.validate()
    user = order.user if isinstance(order.user, Address) else Address(order.user)
    return cls(
        user=user.to_checksum(),
        wager_micros=order.wager_micros,
        min_odds=order.min_odds_bps / 10_000,
        legs=[OrderLegJson.from_order_leg(leg) for leg in order.legs],
        nonce=order.nonce,
        expires_at_ms=order.expires_at_ms,
        order_type=int(order.order_type),
        shield_on=order.shield_on,
        signature=b64encode(order.signature).decode("ascii"),
    )

def _parse_order_legs(raw_legs: List[OrderLegJson]) -> List[OrderLeg]:
    legs = [leg.parse() if hasattr(leg, "parse") else OrderLegJson.from_dict(leg).parse() for leg in raw_legs]
    if not legs:
        raise ValueError("order must include at least one leg")
    if len(legs) > SignedOrder.MAX_LEGS:
        raise ValueError("too many legs")
    return [OrderLeg(market_id=leg.market_id, direction=_direction_to_wire(leg.direction)) for leg in legs]

def _parse_required_bool(value: object, field: str) -> bool:
    # Identity checks preserve Rust's exact bool contract; Python truthiness would turn "false" into true.
    if value is True:
        return True
    if value is False:
        return False
    raise ValueError(f"{field} must be bool")

def _signed_order_json_to_signed_order(self: SignedOrderJson) -> SignedOrder:
    signature = b64decode(self.signature, validate=True)
    if (
        len(signature) != 65
        or b64encode(signature).decode("ascii") != self.signature
    ):
        raise ValueError("invalid signature format")
    return SignedOrder(
        user=Address.from_hex(self.user),
        wager_micros=_canonical_u64(self.wager_micros, "wager_micros"),
        min_odds_bps=_parse_min_odds_bps(float(self.min_odds)),
        legs=_parse_order_legs(self.legs),
        nonce=_canonical_u64(self.nonce, "nonce"),
        expires_at_ms=_canonical_u64(self.expires_at_ms, "expires_at_ms"),
        order_type=_parse_order_type(self.order_type),
        shield_on=_parse_required_bool(self.shield_on, "shield_on"),
        signature=signature,
    )

def _create_rfq_request_from_signed_order(
    cls, order: SignedOrder, use_app_tokens: bool
) -> CreateRfqRequest:
    return cls(
        order=SignedOrderJson.from_signed_order(order),
        use_app_tokens=use_app_tokens,
    )

def _canonical_u64(value: object, field: str) -> int:
    # Signed payloads must preserve exact integer inputs; int(value) would silently
    # turn booleans, floats, and numeric strings into a different order.
    if type(value) is not int or not 0 <= value <= (1 << 64) - 1:
        raise ValueError(f"{field} must fit in u64")
    return value

def _parse_order_type(value: object) -> OrderType:
    if value is None:
        return OrderType.FOK
    if type(value) is not int:
        raise ValueError("order_type must be int")
    return OrderType(value)

def build_wallet_authentication_message(
    domain: str,
    auth_address: Address | str,
    signed_at_ms: int,
) -> str:
    auth = Address.from_evm(auth_address)
    return "\n".join(
        [
            "Longshot Wallet Authentication",
            "",
            "Version: 1",
            f"Domain: {domain}",
            f"Auth Address: {auth.to_checksum()}",
            f"Timestamp: {_canonical_u64(signed_at_ms, 'signed_at_ms')}",
        ]
    )

def build_wallet_withdrawal_authorization_message(
    domain: str,
    chain_id: int,
    auth_address: Address | str,
    destination_address: Address | str,
    amount_micros: int,
    idempotency_key: UUID | str,
    signed_at_ms: int,
) -> str:
    auth = Address.from_evm(auth_address)
    destination = Address.from_evm(destination_address)
    canonical_idempotency_key = UUID(str(idempotency_key).strip())
    return "\n".join(
        [
            "Longshot Withdrawal Authorization",
            "",
            "Version: 1",
            f"Domain: {domain}",
            f"Chain ID: {_canonical_u64(chain_id, 'chain_id')}",
            f"Auth Address: {auth.to_checksum()}",
            f"Destination Address: {destination.to_checksum()}",
            f"Amount Micros: {_canonical_u64(amount_micros, 'amount_micros')}",
            f"Idempotency Key: {canonical_idempotency_key}",
            f"Timestamp: {_canonical_u64(signed_at_ms, 'signed_at_ms')}",
        ]
    )

def encode_wallet_signature(signature: bytes) -> str:
    if len(signature) != 65:
        raise ValueError("wallet signature must be 65 bytes")
    return b64encode(signature).decode("ascii")

def _error_response_new(cls, error: Any, code: Any) -> ErrorResponse:
    return cls(error=str(error), code=str(code), details=None)

def _error_response_with_details(self: ErrorResponse, details: Any) -> ErrorResponse:
    return type(self)(error=self.error, code=self.code, details=str(details))


@dataclass
class RfqEstimateRequest(LongshotModel):
    wager_micros: Optional[int] = None
    legs: Optional[List[OrderLegJson]] = None
    shield_on: Optional[bool] = False


@dataclass
class RfqEstimateResponse(LongshotModel):
    __serde_skip_none__ = set(["odds", "fillable_micros", "reason"])
    request_id: Optional[UUID] = None
    quotable: Optional[bool] = None
    odds: Optional[float] = None
    fillable_micros: Optional[int] = None
    quotes_received: Optional[int] = None
    quoted_at_ms: Optional[int] = None
    reason: Optional[str] = None


@dataclass
class MmRfqStatusResponse(LongshotModel):
    request_id: Optional[str] = None
    status: Optional[RfqStatus] = None

@dataclass
class UserAvailableBalanceResponse(LongshotModel):
    available_micros: Optional[int] = None
    pending_custodial_deposit_micros: Optional[int] = None
    credited_custodial_deposit_micros: Optional[int] = None
    deposit_withdrawal_min_micros: Optional[int] = None
    withdrawal_max_micros: Optional[int] = None

class WithdrawalDeliveryStatus(RustStringEnum):
    Queued = "queued"

@dataclass
class QueuedWithdrawalResponse(LongshotModel):
    __serde_skip_none__ = set(["destination_address"])
    amount_micros: Optional[int] = None
    operation_id: Optional[UUID] = None
    destination_address: Optional[str] = None
    delivery_status: Optional[WithdrawalDeliveryStatus] = None
    withdrawal_stage: Optional[WithdrawalStage] = None
    available_at_ms: Optional[int] = None
    submission_tx_hash: Optional[str] = None

@dataclass
class ActiveWithdrawalResponse(LongshotModel):
    __serde_skip_none__ = set(["available_at_ms","destination_address","submission_tx_hash"])
    operation_id: Optional[UUID] = None
    amount_micros: Optional[int] = None
    destination_address: Optional[str] = None
    withdrawal_stage: Optional[WithdrawalStage] = None
    created_at_ms: Optional[int] = None
    available_at_ms: Optional[int] = None
    submission_tx_hash: Optional[str] = None

@dataclass
class UserWithdrawalStateResponse(LongshotModel):
    withdrawals_available: Optional[bool] = None
    hold_trigger_amount_micros: Optional[int] = None
    hold_threshold_micros: Optional[int] = None
    hold_window_ms: Optional[int] = None
    hold_duration_ms: Optional[int] = None
    active_withdrawals: Optional[List[ActiveWithdrawalResponse]] = None

class AcceptedWithdrawOperationResponse(RustTaggedUnion):
    __serde_untagged__ = True
    __serde_variants__ = {
        "Queued": "Queued",
        "Recovery": "Recovery",
    }

    @classmethod
    def queued(cls, payload: Any = None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        return cls("Queued", payload, **fields)

    @classmethod
    def recovery(cls, payload: Any = None, **fields: Any) -> AcceptedWithdrawOperationResponse:
        return cls("Recovery", payload, **fields)

class PublicReferralStatusResponse(RustStringEnum):
    Valid = "valid"
    Redeemed = "redeemed"
    Expired = "expired"

@dataclass
class PublicReferralInviterResponse(LongshotModel):
    display_name: Optional[str] = None
    avatar_seed: Optional[int] = None
    avatar_url: Optional[str] = None

@dataclass
class PublicReferralDepositMatchOffer(LongshotModel):
    match_limit_micros: Optional[int] = None
    duration_ms: Optional[int] = None

@dataclass
class PublicReferralCodeResponse(LongshotModel):
    __serde_skip_none__ = set(["inviter", "deposit_match"])
    status: Optional[PublicReferralStatusResponse] = None
    inviter: Optional[PublicReferralInviterResponse] = None
    deposit_match: Optional[PublicReferralDepositMatchOffer] = None


@dataclass
class PnlHistoryScopedQuery(LongshotModel):
    __serde_renames__ = {"from_": "from"}
    from_: Optional[int] = None
    to: Optional[int] = None
    scope: Optional[str] = None


@dataclass
class PositionsByMarketsQuery(LongshotModel):
    market_ids: Optional[str] = None
    limit: Optional[int] = None
    cursor: Optional[str] = None

@dataclass
class PositionsByMarketsResponse(LongshotModel):
    positions: Optional[List[PositionDetailResponse]] = None
    next_cursor: Optional[str] = None

@dataclass
class HandleAvailabilityQuery(LongshotModel):
    handle: Optional[str] = None


OrderLegJson.parse = _order_leg_json_parse
OrderLegJson.from_order_leg = classmethod(_order_leg_json_from_order_leg)
SignedOrderJson.from_signed_order = classmethod(_signed_order_json_from_signed_order)
SignedOrderJson.to_signed_order = _signed_order_json_to_signed_order
CreateRfqRequest.from_signed_order = classmethod(_create_rfq_request_from_signed_order)
ErrorResponse.new = classmethod(_error_response_new)
ErrorResponse.with_details = _error_response_with_details

_install_serde_metadata(
    globals(),
    STRUCT_INTEGER_FIELDS,
    STRUCT_REQUIRED_FIELDS,
    TAGGED_UNION_FIELDS,
    DENY_UNKNOWN_TAGGED_UNIONS,
    required_nullable_fields=STRUCT_REQUIRED_NULLABLE_FIELDS,
)

_DEFAULT_FIELDS = {
    "EventMarket": {"resolution_rules": ""},
    "SessionResponse": {"account_created": False},
    "ActivePosition": {"app_token_wager_micros": 0},
    "PositionDetailResponse": {"app_token_wager_micros": 0},
    "PositionSummary": {"app_token_wager_micros": 0},
    "RfqEstimateRequest": {"shield_on": False},
    "SignedOrderJson": {"order_type": 2},
}

for _class_name, _field_defaults in _DEFAULT_FIELDS.items():
    globals()[_class_name].__serde_defaults__ = _field_defaults

DepositOperationResponse.__serde_untagged_payloads__ = {
    "Completed": UserDepositResponse,
    "OperationStatus": BalanceOperationStatusResponse,
}
DepositOperationResponse.__serde_untagged_required_fields__ = {
    "Completed": {"amount_micros", "operation_id", "tx_hash"},
    "OperationStatus": {"amount_micros", "operation_id", "status"},
}

WithdrawOperationResponse.__serde_untagged_payloads__ = {
    "Completed": UserWithdrawResponse,
    "OperationStatus": BalanceOperationStatusResponse,
}
WithdrawOperationResponse.__serde_untagged_required_fields__ = {
    "Completed": {"amount_micros", "operation_id", "tx_hash"},
    "OperationStatus": {"amount_micros", "operation_id", "status"},
}

AcceptedWithdrawOperationResponse.__serde_untagged_payloads__ = {
    "Queued": QueuedWithdrawalResponse,
    "Recovery": BalanceOperationStatusResponse,
}
AcceptedWithdrawOperationResponse.__serde_untagged_required_fields__ = {
    "Queued": {"amount_micros", "operation_id", "delivery_status"},
    "Recovery": {"amount_micros", "operation_id", "status"},
}

PublicMarket.__serde_untagged_payloads__ = {
    "Event": EventMarket,
    "PriceStrike": PriceStrikeMarket,
}
# Event must stay first: `opens_at_ms` is its unique structural selector,
# while the price variant is the strict fallback for otherwise valid objects.
PublicMarket.__serde_untagged_required_fields__ = {
    "Event": {"opens_at_ms"},
    "PriceStrike": set(),
}

_DENY_UNKNOWN_FIELDS = {
    "RfqEstimateRequest",
    "PublicMarketsRawQuery",
    "PriceStrikeMarket",
    "PublicMarketResponse",
    "PublicMarketsResponse",
    "MarketLookupQuery",
    "MarketCurrentQuery",
    "RecentResolutionsQuery",
    "PnlHistoryQuery",
    "PnlHistoryScopedQuery",
    "PositionsQuery",
    "PositionsByMarketsQuery",
    "UpdatePreferencesRequest",
    "UpdateProfileRequest",
    "WalletAuthRequest",
    "UserDepositRequest",
    "UserWithdrawParams",
    "UserWithdrawRequest",
    "CreateRfqRequest",
    "UserTransactionsRawQuery",
    "ConfirmPositionQuery",
}

for _class_name in _DENY_UNKNOWN_FIELDS:
    globals()[_class_name].__serde_deny_unknown__ = True

for _class_name in {
    "AcceptedWithdrawOperationResponse",
    "DepositOperationResponse",
    "WithdrawOperationResponse",
}:
    globals()[_class_name].__serde_tag__ = None


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
