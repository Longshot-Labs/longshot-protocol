"""Taker order signing byte layout."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from struct import pack
from typing import List, Union

from eth_account import Account
from eth_account.messages import encode_defunct

from .rfq import MAX_RFQ_LEGS
from .types import Address, MarketId, OrderType, _check_u8, _check_u32, _check_u64


class SignedOrderError(ValueError):
    """Invalid signed-order data."""


class TakerSignError(ValueError):
    """Taker order signing failed."""


@dataclass(frozen=True)
class OrderLeg:
    market_id: Union[MarketId, int]
    direction: int

    def to_bytes(self) -> bytes:
        market_id = self.market_id.as_u64() if isinstance(self.market_id, MarketId) else self.market_id
        _check_u64(market_id, "market_id")
        _check_u8(self.direction, "direction")
        return pack("<QB", market_id, self.direction)


@dataclass(frozen=True)
class SignedOrder:
    user: Union[Address, bytes]
    wager_micros: int
    # This value is signed as basis points; HTTP SignedOrderJson.min_odds is decimal odds.
    min_odds_bps: int
    legs: List[OrderLeg]
    nonce: int
    expires_at_ms: int
    order_type: Union[OrderType, int]
    shield_on: bool
    signature: bytes = field(default_factory=lambda: bytes(65))

    MAX_LEGS = MAX_RFQ_LEGS

    def __post_init__(self) -> None:
        if len(self.signature) != 65:
            raise ValueError("signature must be 65 bytes")

    def validate(self) -> None:
        if not self.legs:
            raise SignedOrderError("order must include at least one leg")
        if len(self.legs) > self.MAX_LEGS:
            raise SignedOrderError("order legs exceed MAX_LEGS")
        for index, leg in enumerate(self.legs):
            # Python bools compare equal to 0/1, but signed wire values must retain
            # the exact Rust integer and boolean types rather than Python truthiness.
            if (
                not isinstance(leg.direction, int)
                or isinstance(leg.direction, bool)
                or leg.direction not in (0, 1)
            ):
                raise SignedOrderError(f"invalid direction {leg.direction} at legs[{index}]")
        if isinstance(self.order_type, bool) or OrderType.from_u8(self.order_type) is None:
            raise SignedOrderError(f"invalid order type: {self.order_type}")
        if type(self.shield_on) is not bool:
            raise SignedOrderError("shield_on must be bool")
        user = self.user.bytes if isinstance(self.user, Address) else self.user
        if len(user) != 20:
            raise SignedOrderError("user address must be 20 bytes")
        _check_u64(self.wager_micros, "wager_micros")
        _check_u32(self.min_odds_bps, "min_odds_bps")
        _check_u64(self.nonce, "nonce")
        _check_u64(self.expires_at_ms, "expires_at_ms")

    def signing_bytes(self, use_app_tokens: bool) -> bytes:
        self.validate()
        if type(use_app_tokens) is not bool:
            raise SignedOrderError("use_app_tokens must be bool")
        user = self.user.bytes if isinstance(self.user, Address) else self.user
        order_type = int(self.order_type)

        result = bytearray()
        result.extend(user)
        result.extend(pack("<Q", self.wager_micros))
        result.extend(pack("<I", self.min_odds_bps))
        result.extend(pack("<Q", self.nonce))
        result.extend(pack("<Q", self.expires_at_ms))
        result.append(order_type)
        result.append(1 if self.shield_on else 0)
        result.append(1 if use_app_tokens else 0)
        result.append(len(self.legs))
        for leg in self.legs:
            result.extend(leg.to_bytes())
        return bytes(result)

    def verify_signature(self, use_app_tokens: bool) -> bool:
        """Verify this order's signature and funding choice against ``self.user``."""

        try:
            recovered = Account.recover_message(
                encode_defunct(primitive=self.signing_bytes(use_app_tokens)),
                signature=self.signature,
            )
            return Address.from_evm(recovered) == Address.from_evm(self.user)
        except Exception:
            return False


def sign_order(
    order: SignedOrder,
    use_app_tokens: bool,
    signing_key: Union[str, bytes],
) -> SignedOrder:
    """Sign a taker order and funding choice with EIP-191."""

    try:
        signature = bytes(
            Account.sign_message(
                encode_defunct(primitive=order.signing_bytes(use_app_tokens)),
                signing_key,
            ).signature
        )
        return replace(order, signature=signature)
    except Exception as error:
        # Signing exposes one stable failure boundary while exception chaining keeps
        # validation and signer details available to callers for diagnostics.
        raise TakerSignError("failed to sign taker order") from error


def signed_order(
    order: SignedOrder,
    use_app_tokens: bool,
    signing_key: Union[str, bytes],
) -> SignedOrder:
    """Return a signed taker order, preserving all fields except ``signature``."""

    return sign_order(order, use_app_tokens, signing_key)
