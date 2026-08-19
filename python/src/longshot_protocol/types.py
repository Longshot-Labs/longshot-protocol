"""Primitive protocol types shared with the Rust crate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, EnumMeta, IntEnum
from time import time
from typing import ClassVar, List, Optional, Tuple, Type, TypeVar, Union
from uuid import UUID, uuid4

from eth_utils import to_canonical_address, to_checksum_address

MIN_BET_MICROS = 500_000
U64_MAX = (1 << 64) - 1

_UuidIdT = TypeVar("_UuidIdT", bound="UuidId")


def _check_u8(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must fit in u8")
    return value


def _check_u32(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"{name} must fit in u32")
    return value


def _check_u64(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= U64_MAX:
        raise ValueError(f"{name} must fit in u64")
    return value


@dataclass(frozen=True)
class Address:
    """EVM address stored as exactly 20 bytes."""

    ZERO: ClassVar[Address]

    bytes: bytes

    def __post_init__(self) -> None:
        try:
            canonical = bytes(to_canonical_address(self.bytes))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid EVM address") from exc
        object.__setattr__(self, "bytes", canonical)

    @classmethod
    def zero(cls) -> Address:
        return cls(bytes(20))

    @classmethod
    def from_evm(cls, value: Union[str, bytes, Address]) -> Address:
        if isinstance(value, Address):
            return value
        try:
            return cls(bytes(to_canonical_address(value)))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid EVM address") from exc

    @classmethod
    def from_hex(cls, value: str) -> Address:
        return cls.from_evm(value)

    def hex(self, prefixed: bool = True) -> str:
        value = self.bytes.hex()
        return f"0x{value}" if prefixed else value

    def serde_value(self) -> str:
        return self.hex()

    def to_checksum(self) -> str:
        return to_checksum_address(self.bytes)

    def __str__(self) -> str:
        return self.to_checksum()


Address.ZERO = Address.zero()


@dataclass(frozen=True)
class MarketId:
    value: int

    def __post_init__(self) -> None:
        _check_u64(self.value, "market_id")

    @classmethod
    def new(cls, value: int) -> MarketId:
        return cls(value)

    def as_u64(self) -> int:
        return self.value

    def serde_value(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class UuidId:
    value: UUID

    @classmethod
    def new(cls: Type[_UuidIdT]) -> _UuidIdT:
        return cls(uuid4())

    @classmethod
    def from_uuid(cls: Type[_UuidIdT], value: UUID) -> _UuidIdT:
        return cls(value)

    @classmethod
    def nil(cls: Type[_UuidIdT]) -> _UuidIdT:
        return cls(UUID(int=0))

    @classmethod
    def from_bytes(cls: Type[_UuidIdT], value: bytes) -> _UuidIdT:
        if len(value) != 16:
            raise ValueError("uuid id must be 16 bytes")
        return cls(UUID(bytes=value))

    @classmethod
    def from_string(cls: Type[_UuidIdT], value: str) -> _UuidIdT:
        return cls(UUID(value))

    @property
    def bytes(self) -> bytes:
        return self.value.bytes

    def as_uuid(self) -> UUID:
        return self.value

    def as_bytes(self) -> bytes:
        return self.value.bytes

    def serde_value(self) -> str:
        return str(self.value)

    def is_nil(self) -> bool:
        return self.value.int == 0

    def __str__(self) -> str:
        return str(self.value)

    def __call__(self) -> UuidId:
        return self


class RequestId(UuidId):
    pass


class UserId(UuidId):
    pass


class QuoteId(UuidId):
    pass


class ClientQuoteId(UuidId):
    pass


class PositionId(UuidId):
    pass


class ContestId(UuidId):
    pass


class ChatId(UuidId):
    pass


class MessageId(UuidId):
    pass


class MathError(str, Enum):
    Overflow = "Overflow"
    Underflow = "Underflow"
    DivisionByZero = "DivisionByZero"


class MarketType(str):
    """Open user-facing market category slug.

    The constants are conveniences only; constructing an unknown slug preserves
    it so reads remain forward-compatible with categories added by the server.
    """

    Sports: MarketType
    Culture: MarketType
    Crypto: MarketType
    Politics: MarketType
    Earnings: MarketType
    Entertainment: MarketType
    Esports: MarketType
    Weather: MarketType
    Mentions: MarketType
    Extra: MarketType
    Other: MarketType


MarketType.Sports = MarketType("sports")
MarketType.Culture = MarketType("culture")
MarketType.Crypto = MarketType("crypto")
MarketType.Politics = MarketType("politics")
MarketType.Earnings = MarketType("earnings")
MarketType.Entertainment = MarketType("entertainment")
MarketType.Esports = MarketType("esports")
MarketType.Weather = MarketType("weather")
MarketType.Mentions = MarketType("mentions")
MarketType.Extra = MarketType("extra")
MarketType.Other = MarketType("other")


class TradingChannel(str, Enum):
    Rfq = "rfq"
    Contest = "contest"


class MarketStatus(str, Enum):
    Pending = "PENDING"
    Open = "OPEN"
    Frozen = "FROZEN"
    Disputed = "DISPUTED"
    PendingResolution = "PENDING_RESOLUTION"
    Resolved = "RESOLVED"
    Voided = "VOIDED"

    def is_tradeable(self) -> bool:
        return self is MarketStatus.Open

    def is_terminal(self) -> bool:
        return self in {MarketStatus.Resolved, MarketStatus.Voided}

    def is_visible(self) -> bool:
        return self is not MarketStatus.Pending

    def can_transition_to(self, target: MarketStatus) -> bool:
        if target is MarketStatus.Voided and not self.is_terminal():
            return True
        transitions = {
            MarketStatus.Pending: {MarketStatus.Open},
            MarketStatus.Open: {MarketStatus.Frozen},
            MarketStatus.Frozen: {
                MarketStatus.PendingResolution,
                MarketStatus.Resolved,
                MarketStatus.Voided,
                MarketStatus.Disputed,
            },
            MarketStatus.Disputed: {
                MarketStatus.PendingResolution,
                MarketStatus.Resolved,
                MarketStatus.Voided,
            },
            MarketStatus.PendingResolution: {MarketStatus.Resolved, MarketStatus.Voided},
            MarketStatus.Resolved: set(),
            MarketStatus.Voided: set(),
        }
        return target in transitions[self]

    def can_transition_to_worker_owned(self, target: MarketStatus) -> bool:
        return self.can_transition_to(target) or (
            (self is MarketStatus.Pending and target in {MarketStatus.Frozen, MarketStatus.Resolved})
            or (self is MarketStatus.Open and target is MarketStatus.Resolved)
        )


class Outcome(str, Enum):
    Yes = "YES"
    No = "NO"

    def opposite(self) -> Outcome:
        return Outcome.No if self is Outcome.Yes else Outcome.Yes


class _AssetMeta(EnumMeta):
    COUNT: ClassVar[int]
    ALL: ClassVar[List[Asset]]


class Asset(IntEnum, metaclass=_AssetMeta):
    BTC = 0
    ETH = 1
    SOL = 2
    XRP = 3
    HYPE = 4

    @classmethod
    def from_u8(cls, value: int) -> Optional[Asset]:
        try:
            return cls(_check_u8(value, "asset"))
        except ValueError:
            return None

    @classmethod
    def parse_symbol(cls, raw: str) -> Optional[Asset]:
        symbol = raw.strip().upper()
        return cls.__members__.get(symbol)

    def ticker(self) -> str:
        return self.name

    def serde_value(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.ticker()


_AssetMeta.COUNT = 5
_AssetMeta.ALL = [Asset.BTC, Asset.ETH, Asset.SOL, Asset.XRP, Asset.HYPE]


class Direction(IntEnum):
    Up = 0
    Down = 1

    @classmethod
    def from_u8(cls, value: int) -> Optional[Direction]:
        try:
            return cls(_check_u8(value, "direction"))
        except ValueError:
            return None

    @classmethod
    def from_predicts_higher(cls, prediction: bool) -> Direction:
        return cls.Up if prediction else cls.Down

    def predicts_higher(self) -> bool:
        return self is Direction.Up

    def opposite(self) -> Direction:
        return Direction.Down if self is Direction.Up else Direction.Up

    def serde_value(self) -> str:
        return self.name

    def __str__(self) -> str:
        return "UP" if self is Direction.Up else "DOWN"


@dataclass(frozen=True)
class Duration:
    ONE_MINUTE: ClassVar[Duration]
    FIVE_MINUTES: ClassVar[Duration]
    FIFTEEN_MINUTES: ClassVar[Duration]
    ONE_HOUR: ClassVar[Duration]
    FOUR_HOURS: ClassVar[Duration]
    ONE_DAY: ClassVar[Duration]

    seconds: int

    ONE_MINUTE_SECS = 60
    FIVE_MINUTES_SECS = 5 * 60
    FIFTEEN_MINUTES_SECS = 15 * 60
    ONE_HOUR_SECS = 60 * 60
    FOUR_HOURS_SECS = 4 * 60 * 60
    ONE_DAY_SECS = 24 * 60 * 60
    VALID_SECONDS = {
        ONE_MINUTE_SECS,
        FIVE_MINUTES_SECS,
        FIFTEEN_MINUTES_SECS,
        ONE_HOUR_SECS,
        FOUR_HOURS_SECS,
        ONE_DAY_SECS,
    }

    def __post_init__(self) -> None:
        _check_u32(self.seconds, "duration seconds")

    @classmethod
    def from_secs(cls, seconds: int) -> Optional[Duration]:
        return cls(seconds) if seconds in cls.VALID_SECONDS else None

    def is_valid(self) -> bool:
        return self.seconds in self.VALID_SECONDS

    def as_secs(self) -> int:
        return self.seconds

    def as_mins(self) -> int:
        return self.seconds // 60

    def expiry_from_now(self) -> int:
        return Timestamp.now().as_millis() + (self.seconds * 1000)

    def serde_value(self) -> int:
        return self.seconds

    def __str__(self) -> str:
        if self.seconds == self.ONE_MINUTE_SECS:
            return "1m"
        if self.seconds == self.FIVE_MINUTES_SECS:
            return "5m"
        if self.seconds == self.FIFTEEN_MINUTES_SECS:
            return "15m"
        if self.seconds == self.ONE_HOUR_SECS:
            return "1h"
        if self.seconds == self.FOUR_HOURS_SECS:
            return "4h"
        if self.seconds == self.ONE_DAY_SECS:
            return "1d"
        return f"{self.seconds}s"


Duration.ONE_MINUTE = Duration(Duration.ONE_MINUTE_SECS)
Duration.FIVE_MINUTES = Duration(Duration.FIVE_MINUTES_SECS)
Duration.FIFTEEN_MINUTES = Duration(Duration.FIFTEEN_MINUTES_SECS)
Duration.ONE_HOUR = Duration(Duration.ONE_HOUR_SECS)
Duration.FOUR_HOURS = Duration(Duration.FOUR_HOURS_SECS)
Duration.ONE_DAY = Duration(Duration.ONE_DAY_SECS)


@dataclass(frozen=True)
class Odds:
    EVEN: ClassVar[Odds]
    MIN: ClassVar[Odds]
    MAX: ClassVar[Odds]

    value: int

    BASIS_POINTS = 10_000
    EVEN_VALUE = 10_000
    MIN_VALUE = 10_001
    MAX_VALUE = 10_000_000

    def __post_init__(self) -> None:
        _check_u32(self.value, "odds")

    @classmethod
    def from_decimal(cls, whole: int, fractional_bps: int) -> Odds:
        return cls((whole * cls.BASIS_POINTS) + fractional_bps)

    def to_decimal(self) -> Tuple[int, int]:
        return self.value // self.BASIS_POINTS, self.value % self.BASIS_POINTS

    def to_float(self) -> float:
        return self.value / self.BASIS_POINTS

    def to_f64(self) -> float:
        return self.to_float()

    def is_valid(self) -> bool:
        return self.EVEN_VALUE < self.value <= self.MAX_VALUE

    def _payout_micros(self, wager_micros: int) -> int:
        _check_u64(wager_micros, "wager_micros")
        return (wager_micros * self.value) // self.BASIS_POINTS

    def checked_calculate_payout(self, wager_micros: int) -> Optional[int]:
        payout = self._payout_micros(wager_micros)
        return payout if payout <= U64_MAX else None

    def calculate_payout(self, wager_micros: int) -> int:
        payout = self.checked_calculate_payout(wager_micros)
        return U64_MAX if payout is None else payout

    def checked_calculate_profit(self, wager_micros: int) -> Optional[int]:
        profit = self._payout_micros(wager_micros) - wager_micros
        return profit if 0 <= profit <= U64_MAX else None

    def calculate_profit(self, wager_micros: int) -> int:
        profit = self.checked_calculate_profit(wager_micros)
        if profit is not None:
            return profit
        return 0 if self.value <= self.BASIS_POINTS else U64_MAX

    def checked_calculate_mm_liability(self, fill_micros: int) -> Optional[int]:
        return self.checked_calculate_profit(fill_micros)

    def serde_value(self) -> int:
        return self.value

    def __str__(self) -> str:
        whole, fractional_bps = self.to_decimal()
        return f"{whole}.{fractional_bps:04}x"


Odds.EVEN = Odds(Odds.EVEN_VALUE)
Odds.MIN = Odds(Odds.MIN_VALUE)
Odds.MAX = Odds(Odds.MAX_VALUE)


@dataclass(frozen=True)
class Amount:
    ZERO: ClassVar[Amount]

    micros: int

    MICROS_PER_DOLLAR = 1_000_000

    def __post_init__(self) -> None:
        _check_u64(self.micros, "amount micros")

    @classmethod
    def zero(cls) -> Amount:
        return cls(0)

    @classmethod
    def from_dollars(cls, dollars: int) -> Amount:
        _check_u64(dollars, "dollars")
        return cls(min(U64_MAX, dollars * cls.MICROS_PER_DOLLAR))

    @classmethod
    def from_micro(cls, micros: int) -> Amount:
        return cls(micros)

    def fixed_mul(self, other: Amount) -> Amount:
        scaled = (self.micros * other.micros) // self.MICROS_PER_DOLLAR
        if scaled > U64_MAX:
            raise ArithmeticError(MathError.Overflow)
        return Amount(scaled)

    def fixed_div(self, other: Amount) -> Amount:
        if other.micros == 0:
            raise ArithmeticError(MathError.DivisionByZero)
        scaled = (self.micros * self.MICROS_PER_DOLLAR) // other.micros
        if scaled > U64_MAX:
            raise ArithmeticError(MathError.Overflow)
        return Amount(scaled)

    def fixed_mul_div(self, mul: Amount, div: Amount) -> Amount:
        if div.micros == 0:
            raise ArithmeticError(MathError.DivisionByZero)
        scaled = (self.micros * mul.micros) // div.micros
        if scaled > U64_MAX:
            raise ArithmeticError(MathError.Overflow)
        return Amount(scaled)

    def as_micros(self) -> int:
        return self.micros

    def to_float(self) -> float:
        return self.micros / self.MICROS_PER_DOLLAR

    def to_f64(self) -> float:
        return self.to_float()

    def serde_value(self) -> int:
        return self.micros

    def is_valid_bet(self) -> bool:
        return self.micros >= MIN_BET_MICROS

    def saturating_sub(self, other: Amount) -> Amount:
        return Amount(max(0, self.micros - other.micros))

    def saturating_add(self, other: Amount) -> Amount:
        return Amount(min(U64_MAX, self.micros + other.micros))

    def __add__(self, other: Amount) -> Amount:
        return self.saturating_add(other)

    def __sub__(self, other: Amount) -> Amount:
        return self.saturating_sub(other)

    def __str__(self) -> str:
        return f"${self.to_float():.2f}"


Amount.ZERO = Amount.zero()


@dataclass(frozen=True)
class Timestamp:
    ZERO: ClassVar[Timestamp]

    millis: int

    def __post_init__(self) -> None:
        _check_u64(self.millis, "timestamp millis")

    @classmethod
    def now(cls) -> Timestamp:
        return cls(int(time() * 1000))

    @classmethod
    def from_secs(cls, seconds: int) -> Optional[Timestamp]:
        seconds = _check_u64(seconds, "timestamp seconds")
        # Python integers do not overflow, so enforce Rust's checked_mul contract
        # explicitly instead of letting Timestamp construction raise afterward.
        if seconds > U64_MAX // 1000:
            return None
        return cls(seconds * 1000)

    @classmethod
    def from_millis(cls, millis: int) -> Timestamp:
        return cls(millis)

    def as_secs(self) -> int:
        return self.millis // 1000

    def as_millis(self) -> int:
        return self.millis

    def is_expired(self, current: Timestamp) -> bool:
        return self.millis < current.millis

    def add_millis(self, millis: int) -> Optional[Timestamp]:
        millis = _check_u64(millis, "millis")
        if self.millis > U64_MAX - millis:
            return None
        return Timestamp(self.millis + millis)

    def millis_until(self, current: Timestamp) -> int:
        return max(0, self.millis - current.millis)

    def serde_value(self) -> int:
        return self.millis

    def __str__(self) -> str:
        return f"{self.millis}ms"


Timestamp.ZERO = Timestamp(0)


class OrderType(IntEnum):
    IOC = 1
    FOK = 2

    @classmethod
    def from_u8(cls, value: int) -> Optional[OrderType]:
        try:
            return cls(_check_u8(value, "order_type"))
        except ValueError:
            return None

    def requires_full_fill(self) -> bool:
        return self is OrderType.FOK

    def allows_partial_fill(self) -> bool:
        return self is OrderType.IOC

    def __call__(self) -> OrderType:
        return self

    def serde_value(self) -> str:
        return self.name


class UserTier(IntEnum):
    Standard = 0
    Silver = 1
    Gold = 2
    Platinum = 3
    VIP = 4

    @classmethod
    def from_u8(cls, value: int) -> Optional[UserTier]:
        try:
            return cls(_check_u8(value, "user_tier"))
        except ValueError:
            return None

    def serde_value(self) -> str:
        return self.name
