"""RFQ and quote fixed-size binary protocol layouts."""

from __future__ import annotations

from dataclasses import dataclass, field
from struct import calcsize, pack, unpack_from
from typing import Iterator, List, Optional, Union

from eth_account import Account
from eth_account.messages import encode_defunct

from .types import (
    Address,
    Amount,
    Asset,
    ClientQuoteId,
    Direction,
    Duration,
    Odds,
    OrderType,
    RequestId,
    Timestamp,
    UserTier,
    _check_u8,
    _check_u32,
    _check_u64,
)

MAX_RFQ_LEGS = 9
RFQ_PROTOCOL_VERSION = 2
RFQ_LEG_TYPE_PRICE_STRIKE_TAG = 0
# Tag 1 is retired so a v1 client cannot silently decode a binary event as Politics.
RFQ_LEG_TYPE_BINARY_EVENT_TAG = 2

RFQ_LEG_WIRE_FORMAT = "<QQBBBBI"
RFQ_LEG_WIRE_SIZE = calcsize(RFQ_LEG_WIRE_FORMAT)
TAKER_METADATA_WIRE_SIZE = 24
BROADCAST_RFQ_REQUEST_SIZE = 280
QUOTE_RESPONSE_SIZE = 113
QUOTE_RESPONSE_SIGNED_DATA_SIZE = 48


class _CallableOdds(int):
    def __new__(cls, value: int) -> _CallableOdds:
        return int.__new__(cls, value)

    def __call__(self) -> Odds:
        return Odds(int(self))


class _CallableOrderType(int):
    def __new__(cls, value: int) -> _CallableOrderType:
        return int.__new__(cls, value)

    def __call__(self) -> Optional[OrderType]:
        return OrderType.from_u8(int(self))


class _CallablePriceWindowSecs(int):
    def __new__(cls, value: int, type_tag: int) -> _CallablePriceWindowSecs:
        instance = int.__new__(cls, value)
        instance._type_tag = type_tag
        return instance

    def __call__(self) -> Optional[int]:
        return int(self) if self._type_tag == RFQ_LEG_TYPE_PRICE_STRIKE_TAG else None


class RfqLegWireDecodeError(ValueError):
    pass


@dataclass(frozen=True)
class RfqLegType:
    kind: str
    asset: Optional[Asset] = None
    window: Optional[Duration] = None

    @classmethod
    def price_strike(cls, asset: Union[Asset, int], window: Duration) -> RfqLegType:
        return cls(kind="price_strike", asset=Asset(asset), window=window)

    @classmethod
    def binary_event(cls) -> RfqLegType:
        return cls(kind="binary_event")

    def type_tag(self) -> int:
        return (
            RFQ_LEG_TYPE_PRICE_STRIKE_TAG
            if self.kind == "price_strike"
            else RFQ_LEG_TYPE_BINARY_EVENT_TAG
        )

    def is_price_strike(self) -> bool:
        return self.kind == "price_strike"

    def is_binary_event(self) -> bool:
        return self.kind == "binary_event"


@dataclass(frozen=True)
class RfqLeg:
    market_id: int
    start_at_ms: int
    type_tag: int
    direction: Union[Direction, int]
    leg_index: int
    type_value: int
    price_window_secs: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", _check_u8(self.direction, "direction"))
        object.__setattr__(
            self,
            "price_window_secs",
            _CallablePriceWindowSecs(self.price_window_secs, self.type_tag),
        )

    @classmethod
    def new_price_strike(
        cls,
        market_id: int,
        start_at_ms: int,
        asset: Union[Asset, int],
        direction: Union[Direction, int],
        window: Duration,
        leg_index: int,
    ) -> RfqLeg:
        return cls.price_strike(market_id, start_at_ms, asset, direction, window, leg_index)

    @classmethod
    def price_strike(
        cls,
        market_id: int,
        start_at_ms: int,
        asset: Union[Asset, int],
        direction: Union[Direction, int],
        window: Duration,
        leg_index: int,
    ) -> RfqLeg:
        asset_value = int(_check_u8(asset, "asset"))
        return cls(
            market_id=market_id,
            start_at_ms=start_at_ms,
            type_tag=RFQ_LEG_TYPE_PRICE_STRIKE_TAG,
            direction=direction,
            leg_index=leg_index,
            type_value=asset_value,
            price_window_secs=window.as_secs(),
        )

    @classmethod
    def new_binary_event(
        cls,
        market_id: int,
        start_at_ms: int,
        direction: Union[Direction, int],
        leg_index: int,
    ) -> RfqLeg:
        return cls.binary_event(market_id, start_at_ms, direction, leg_index)

    @classmethod
    def binary_event(
        cls,
        market_id: int,
        start_at_ms: int,
        direction: Union[Direction, int],
        leg_index: int,
    ) -> RfqLeg:
        return cls(
            market_id=market_id,
            start_at_ms=start_at_ms,
            type_tag=RFQ_LEG_TYPE_BINARY_EVENT_TAG,
            direction=direction,
            leg_index=leg_index,
            type_value=0,
            price_window_secs=0,
        )

    @classmethod
    def from_wire_bytes(cls, data: bytes) -> RfqLeg:
        if len(data) != RFQ_LEG_WIRE_SIZE:
            raise RfqLegWireDecodeError("RFQ leg wire payload must be 24 bytes")
        values = unpack_from(RFQ_LEG_WIRE_FORMAT, data)
        leg = cls(
            market_id=values[0],
            start_at_ms=values[1],
            type_tag=values[2],
            direction=values[3],
            leg_index=values[4],
            type_value=values[5],
            price_window_secs=values[6],
        )
        leg.validate()
        return leg

    def validate(self) -> None:
        _check_u64(self.market_id, "market_id")
        _check_u64(self.start_at_ms, "start_at_ms")
        _check_u8(self.type_tag, "type_tag")
        direction = _check_u8(self.direction, "direction")
        _check_u8(self.leg_index, "leg_index")
        _check_u8(self.type_value, "type_value")
        _check_u32(self.price_window_secs, "price_window_secs")

        if Direction.from_u8(direction) is None:
            raise RfqLegWireDecodeError(f"invalid RFQ direction: {direction}")
        if self.type_tag == RFQ_LEG_TYPE_PRICE_STRIKE_TAG:
            if Asset.from_u8(self.type_value) is None:
                raise RfqLegWireDecodeError(f"invalid RFQ asset: {self.type_value}")
            if Duration.from_secs(self.price_window_secs) is None:
                raise RfqLegWireDecodeError(
                    f"invalid RFQ price_window_secs: {self.price_window_secs}"
                )
        elif self.type_tag == RFQ_LEG_TYPE_BINARY_EVENT_TAG:
            if self.price_window_secs != 0:
                raise RfqLegWireDecodeError(
                    f"invalid RFQ binary-event price_window_secs: {self.price_window_secs}"
                )
            if self.type_value != 0:
                raise RfqLegWireDecodeError(
                    f"invalid RFQ binary-event type value: {self.type_value}"
                )
        else:
            raise RfqLegWireDecodeError(f"invalid RFQ leg type tag: {self.type_tag}")

    def leg_type(self) -> RfqLegType:
        self.validate()
        if self.type_tag == RFQ_LEG_TYPE_PRICE_STRIKE_TAG:
            window = Duration.from_secs(self.price_window_secs)
            if window is None:
                raise RfqLegWireDecodeError(
                    f"invalid RFQ price_window_secs: {self.price_window_secs}"
                )
            return RfqLegType.price_strike(Asset(self.type_value), window)
        return RfqLegType.binary_event()

    def price_asset(self) -> Optional[Asset]:
        return (
            Asset(self.type_value)
            if self.type_tag == RFQ_LEG_TYPE_PRICE_STRIKE_TAG
            else None
        )

    def price_window(self) -> Optional[Duration]:
        return (
            Duration.from_secs(self.price_window_secs)
            if self.type_tag == RFQ_LEG_TYPE_PRICE_STRIKE_TAG
            else None
        )

    def price_window_seconds(self) -> Optional[int]:
        return (
            self.price_window_secs
            if self.type_tag == RFQ_LEG_TYPE_PRICE_STRIKE_TAG
            else None
        )

    def to_wire_bytes(self) -> bytes:
        self.validate()
        return pack(
            RFQ_LEG_WIRE_FORMAT,
            self.market_id,
            self.start_at_ms,
            self.type_tag,
            int(self.direction),
            self.leg_index,
            self.type_value,
            self.price_window_secs,
        )


@dataclass(frozen=True)
class RfqLegWire:
    market_id: int
    start_at_ms: int
    type_tag: int
    direction: int
    leg_index: int
    type_value: int
    price_window_secs: int

    SIZE = RFQ_LEG_WIRE_SIZE

    @classmethod
    def default(cls) -> RfqLegWire:
        return cls(
            market_id=0,
            start_at_ms=0,
            type_tag=0,
            direction=0,
            leg_index=0,
            type_value=0,
            price_window_secs=0,
        )

    @classmethod
    def from_leg(cls, leg: RfqLeg) -> RfqLegWire:
        leg.validate()
        return cls(
            market_id=leg.market_id,
            start_at_ms=leg.start_at_ms,
            type_tag=leg.type_tag,
            direction=int(leg.direction),
            leg_index=leg.leg_index,
            type_value=leg.type_value,
            price_window_secs=leg.price_window_secs,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> RfqLegWire:
        # Wire decoding preserves inactive padding and future tag values; callers
        # that need a validated active leg must convert through RfqLeg instead.
        return cls.from_raw_bytes(data)

    @classmethod
    def from_raw_bytes(cls, data: bytes) -> RfqLegWire:
        if len(data) != RFQ_LEG_WIRE_SIZE:
            raise ValueError("RFQ leg wire payload must be 24 bytes")
        values = unpack_from(RFQ_LEG_WIRE_FORMAT, data)
        return cls(
            market_id=values[0],
            start_at_ms=values[1],
            type_tag=values[2],
            direction=values[3],
            leg_index=values[4],
            type_value=values[5],
            price_window_secs=values[6],
        )

    def to_leg(self) -> RfqLeg:
        return RfqLeg(
            market_id=self.market_id,
            start_at_ms=self.start_at_ms,
            type_tag=self.type_tag,
            direction=self.direction,
            leg_index=self.leg_index,
            type_value=self.type_value,
            price_window_secs=self.price_window_secs,
        )

    def to_bytes(self) -> bytes:
        _check_u64(self.market_id, "market_id")
        _check_u64(self.start_at_ms, "start_at_ms")
        _check_u8(self.type_tag, "type_tag")
        _check_u8(self.direction, "direction")
        _check_u8(self.leg_index, "leg_index")
        _check_u8(self.type_value, "type_value")
        _check_u32(self.price_window_secs, "price_window_secs")
        return pack(
            RFQ_LEG_WIRE_FORMAT,
            self.market_id,
            self.start_at_ms,
            self.type_tag,
            self.direction,
            self.leg_index,
            self.type_value,
            self.price_window_secs,
        )


def _leg_to_wire(leg: Union[RfqLeg, RfqLegWire]) -> RfqLegWire:
    return leg if isinstance(leg, RfqLegWire) else RfqLegWire.from_leg(leg)


def _leg_to_typed(leg: Union[RfqLeg, RfqLegWire]) -> RfqLeg:
    typed = leg.to_leg() if isinstance(leg, RfqLegWire) else leg
    typed.validate()
    return typed


@dataclass(frozen=True)
class TakerMetadata:
    tier: Union[UserTier, int]
    address: Union[Address, bytes]

    @classmethod
    def new(cls, tier: Union[UserTier, int], address: Address) -> TakerMetadata:
        return cls(tier=tier, address=address)

    def to_wire_bytes(self) -> bytes:
        address = self.address.bytes if isinstance(self.address, Address) else self.address
        if len(address) != 20:
            raise ValueError("taker metadata address must be 20 bytes")
        return pack("<BB2s20s", 1, int(self.tier), b"\x00\x00", address)

    @classmethod
    def from_wire_bytes(cls, data: bytes) -> Optional[TakerMetadata]:
        if len(data) != TAKER_METADATA_WIRE_SIZE:
            raise ValueError("taker metadata wire payload must be 24 bytes")
        option, tier, _reserved, address = unpack_from("<BB2s20s", data)
        if option == 0:
            return None
        return cls(tier=tier, address=Address(address))


@dataclass(frozen=True)
class BroadcastRfqRequest:
    request_id: RequestId
    wager_micros: int
    expires_at_ms: int
    taker_metadata: Optional[TakerMetadata]
    order_type: Union[OrderType, int]
    leg_count: int
    protocol_version: int
    legs: List[Union[RfqLeg, RfqLegWire]]
    reserved: bytes = field(default_factory=lambda: bytes(5))
    inactive_leg_bytes: bytes = b""
    taker_metadata_wire_bytes: bytes = b""

    SIZE = BROADCAST_RFQ_REQUEST_SIZE

    def __post_init__(self) -> None:
        object.__setattr__(self, "order_type", _CallableOrderType(int(self.order_type)))
        if self.taker_metadata_wire_bytes:
            if len(self.taker_metadata_wire_bytes) != TAKER_METADATA_WIRE_SIZE:
                raise ValueError("taker metadata wire payload must be 24 bytes")
            wire_bytes = bytes(self.taker_metadata_wire_bytes)
            object.__setattr__(
                self, "taker_metadata", TakerMetadata.from_wire_bytes(wire_bytes)
            )
        elif self.taker_metadata is None:
            wire_bytes = bytes(TAKER_METADATA_WIRE_SIZE)
        else:
            wire_bytes = self.taker_metadata.to_wire_bytes()
        object.__setattr__(self, "taker_metadata_wire_bytes", wire_bytes)

    @classmethod
    def from_bytes(cls, data: bytes) -> BroadcastRfqRequest:
        if len(data) != BROADCAST_RFQ_REQUEST_SIZE:
            raise ValueError("broadcast RFQ payload must be 280 bytes")

        request_id = RequestId.from_bytes(data[0:16])
        wager_micros = unpack_from("<Q", data, 16)[0]
        expires_at_ms = unpack_from("<Q", data, 24)[0]
        taker_metadata_wire_bytes = data[32:56]
        order_type = data[56]
        leg_count = data[57]
        protocol_version = data[58]
        reserved = data[59:64]

        legs = []
        offset = 64
        active_leg_count = min(leg_count, MAX_RFQ_LEGS)
        for index in range(active_leg_count):
            start = offset + (index * RFQ_LEG_WIRE_SIZE)
            legs.append(RfqLegWire.from_raw_bytes(data[start : start + RFQ_LEG_WIRE_SIZE]))

        return cls(
            request_id=request_id,
            wager_micros=wager_micros,
            expires_at_ms=expires_at_ms,
            taker_metadata=None,
            order_type=order_type,
            leg_count=leg_count,
            protocol_version=protocol_version,
            legs=legs,
            reserved=reserved,
            inactive_leg_bytes=data[offset + (active_leg_count * RFQ_LEG_WIRE_SIZE) :],
            taker_metadata_wire_bytes=taker_metadata_wire_bytes,
        )

    def to_bytes(self) -> bytes:
        if len(self.reserved) != 5:
            raise ValueError("broadcast RFQ reserved field must be 5 bytes")
        active_leg_count = min(self.leg_count, MAX_RFQ_LEGS)
        active_legs = self.legs[:active_leg_count]
        if len(active_legs) != active_leg_count:
            raise ValueError("broadcast RFQ active legs shorter than leg_count")

        result = bytearray()
        result.extend(self.request_id.bytes)
        result.extend(pack("<Q", self.wager_micros))
        result.extend(pack("<Q", self.expires_at_ms))
        result.extend(self.taker_metadata_wire_bytes)
        result.append(int(self.order_type))
        result.append(self.leg_count)
        result.append(_check_u8(self.protocol_version, "protocol_version"))
        result.extend(self.reserved)
        for leg in active_legs:
            result.extend(_leg_to_wire(leg).to_bytes())

        expected_inactive_len = RFQ_LEG_WIRE_SIZE * (MAX_RFQ_LEGS - active_leg_count)
        if self.inactive_leg_bytes:
            if len(self.inactive_leg_bytes) != expected_inactive_len:
                raise ValueError("broadcast RFQ inactive leg bytes have wrong length")
            result.extend(self.inactive_leg_bytes)
        else:
            result.extend(bytes(expected_inactive_len))

        if len(result) != BROADCAST_RFQ_REQUEST_SIZE:
            raise AssertionError("encoded broadcast RFQ size mismatch")
        return bytes(result)

    def wager(self) -> Amount:
        return Amount.from_micro(self.wager_micros)

    def expires_at(self) -> Timestamp:
        return Timestamp.from_millis(self.expires_at_ms)

    def order_type_value(self) -> Optional[OrderType]:
        return OrderType.from_u8(int(self.order_type))

    def is_expired(self) -> bool:
        return Timestamp.now().as_millis() > self.expires_at_ms

    def active_leg_wires(self) -> List[RfqLegWire]:
        active_leg_count = min(self.leg_count, MAX_RFQ_LEGS)
        return [_leg_to_wire(leg) for leg in self.legs[:active_leg_count]]

    def leg_wire(self, index: int) -> Optional[RfqLegWire]:
        wires = [_leg_to_wire(leg) for leg in self.legs[: self.leg_count]]
        return wires[index] if 0 <= index < len(wires) else None

    def iter_leg_wires(self) -> Iterator[RfqLegWire]:
        return iter(_leg_to_wire(leg) for leg in self.legs[: self.leg_count])

    def leg(self, index: int) -> Optional[RfqLeg]:
        return (
            _leg_to_typed(self.legs[index])
            if 0 <= index < min(self.leg_count, len(self.legs))
            else None
        )

    def iter_legs(self) -> Iterator[RfqLeg]:
        return (_leg_to_typed(leg) for leg in self.legs[: self.leg_count])

    def remaining_ms(self) -> int:
        return max(0, self.expires_at_ms - Timestamp.now().as_millis())

    def get_taker_metadata(self) -> Optional[TakerMetadata]:
        return self.taker_metadata

    def taker_tier(self) -> Optional[UserTier]:
        if self.taker_metadata is None:
            return None
        return UserTier.from_u8(int(self.taker_metadata.tier))

    def taker_address(self) -> Optional[Address]:
        if self.taker_metadata is None:
            return None
        address = self.taker_metadata.address
        return address if isinstance(address, Address) else Address(address)


@dataclass(frozen=True)
class QuoteResponse:
    request_id: RequestId
    odds: int
    max_fill_micros: int
    client_quote_id: ClientQuoteId = field(default_factory=ClientQuoteId.nil)
    signature: bytes = field(default_factory=lambda: bytes(65))
    reserved: bytes = field(default_factory=lambda: bytes(4))

    SIZE = QUOTE_RESPONSE_SIZE
    SIGNED_DATA_SIZE = QUOTE_RESPONSE_SIGNED_DATA_SIZE

    def __post_init__(self) -> None:
        _check_u32(self.odds, "odds")
        _check_u64(self.max_fill_micros, "max_fill_micros")
        if len(self.reserved) != 4:
            raise ValueError("reserved field must be 4 bytes")
        if len(self.signature) != 65:
            raise ValueError("signature must be 65 bytes")
        object.__setattr__(self, "odds", _CallableOdds(self.odds))

    @classmethod
    def new(
        cls,
        request_id: RequestId,
        odds: Odds,
        max_fill: Amount,
        client_quote_id: Optional[ClientQuoteId] = None,
    ) -> QuoteResponse:
        return cls(
            request_id=request_id,
            odds=odds.value,
            max_fill_micros=max_fill.as_micros(),
            client_quote_id=client_quote_id or ClientQuoteId.nil(),
            signature=bytes(65),
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> QuoteResponse:
        if len(data) != QUOTE_RESPONSE_SIZE:
            raise ValueError(f"quote response payload must be {QUOTE_RESPONSE_SIZE} bytes")
        request_id = RequestId.from_bytes(data[0:16])
        odds = unpack_from("<I", data, 16)[0]
        max_fill_micros = unpack_from("<Q", data, 20)[0]
        client_quote_id = ClientQuoteId.from_bytes(data[28:44])
        reserved = data[44:48]
        signature = data[48:113]
        return cls(
            request_id=request_id,
            odds=odds,
            max_fill_micros=max_fill_micros,
            client_quote_id=client_quote_id,
            signature=signature,
            reserved=reserved,
        )

    @classmethod
    def from_slice(cls, data: bytes) -> Optional[QuoteResponse]:
        return cls.from_bytes(data) if len(data) == QUOTE_RESPONSE_SIZE else None

    def signed_data_bytes(self) -> bytes:
        return self.to_bytes()[:QUOTE_RESPONSE_SIGNED_DATA_SIZE]

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(self.request_id.bytes)
        result.extend(pack("<I", self.odds))
        result.extend(pack("<Q", self.max_fill_micros))
        result.extend(self.client_quote_id.bytes)
        result.extend(self.reserved)
        result.extend(self.signature)
        if len(result) != QUOTE_RESPONSE_SIZE:
            raise AssertionError("encoded quote response size mismatch")
        return bytes(result)

    def meets_min_odds(self, min_odds: Odds) -> bool:
        return self.odds >= min_odds.value

    def max_fill(self) -> Amount:
        return Amount.from_micro(self.max_fill_micros)

    def client_quote_id_option(self) -> Optional[ClientQuoteId]:
        return None if self.client_quote_id.is_nil() else self.client_quote_id

    def verify_signature(self, wallet_address: Address) -> bool:
        try:
            recovered = Account.recover_message(
                encode_defunct(primitive=self.signed_data_bytes()),
                signature=self.signature,
            )
        except Exception:
            return False
        return Address.from_evm(recovered) == wallet_address
