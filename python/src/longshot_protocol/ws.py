"""Market-maker WebSocket protocol message shapes."""

from __future__ import annotations

from typing import List, Optional, Union

from ._serde_metadata import (
    DENY_UNKNOWN_TAGGED_UNIONS,
    STRUCT_INTEGER_FIELDS,
    STRUCT_REQUIRED_FIELDS,
    TAGGED_UNION_FIELDS,
)
from .model import RustStringEnum, RustTaggedUnion, _install_serde_metadata
from .types import Asset


class QuoteResultStatus(RustStringEnum):
    Filled = "filled"
    NotFilled = "not_filled"
    Rejected = "rejected"
    SelectedFailed = "selected_failed"


class RfqSubscription(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_content__ = "asset"
    __serde_variants__ = {
        "All": "all",
        "BinaryEvent": "binary_event",
        "PriceStrike": "price_strike",
    }

    @classmethod
    def all(cls) -> RfqSubscription:
        return cls("All")

    @classmethod
    def binary_event(cls) -> RfqSubscription:
        return cls("BinaryEvent")

    @classmethod
    def price_strike(cls, asset: Union[Asset, str]) -> RfqSubscription:
        return cls("PriceStrike", asset)


class ClientMessage(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
        "Auth": "auth",
        "AuthResponse": "auth_response",
        "Quote": "quote",
        "Pong": "pong",
        "Subscribe": "subscribe",
    }
    __repr_redacted_fields__ = {"signature"}

    @classmethod
    def auth(cls) -> ClientMessage:
        return cls("Auth")

    @classmethod
    def auth_response(cls, wallet_address: str, signature: str) -> ClientMessage:
        return cls("AuthResponse", wallet_address=wallet_address, signature=signature)

    @classmethod
    def quote(cls, data: str) -> ClientMessage:
        return cls("Quote", data=data)

    @classmethod
    def pong(cls) -> ClientMessage:
        return cls("Pong")

    @classmethod
    def subscribe(
        cls, protocol_version: int, subscriptions: List[RfqSubscription]
    ) -> ClientMessage:
        return cls(
            "Subscribe",
            protocol_version=protocol_version,
            subscriptions=subscriptions,
        )


class ServerMessage(RustTaggedUnion):
    __serde_tag__ = "type"
    __serde_variants__ = {
        "AuthChallenge": "auth_challenge",
        "AuthResult": "auth_result",
        "Rfq": "rfq",
        "Subscribed": "subscribed",
        "QuoteAck": "quote_ack",
        "QuoteResult": "quote_result",
        "Ping": "ping",
        "Error": "error",
        "RateLimit": "rate_limit",
    }
    __repr_redacted_fields__ = {"session_token"}

    @classmethod
    def auth_challenge(cls, challenge_id: str, timestamp_ms: int) -> ServerMessage:
        return cls(
            "AuthChallenge",
            challenge_id=challenge_id,
            timestamp_ms=timestamp_ms,
        )

    @classmethod
    def auth_result(
        cls, success: bool, error: Optional[str] = None, session_token: Optional[str] = None
    ) -> ServerMessage:
        return cls("AuthResult", success=success, error=error, session_token=session_token)

    @classmethod
    def rfq(cls, data: str) -> ServerMessage:
        return cls("Rfq", data=data)

    @classmethod
    def subscribed(cls, protocol_version: int) -> ServerMessage:
        return cls("Subscribed", protocol_version=protocol_version)

    @classmethod
    def quote_ack(
        cls,
        request_id: str,
        quote_id: str,
        client_quote_id: Optional[str],
        accepted: bool,
        error: Optional[str] = None,
    ) -> ServerMessage:
        return cls(
            "QuoteAck",
            request_id=request_id,
            quote_id=quote_id,
            client_quote_id=client_quote_id,
            accepted=accepted,
            error=error,
        )

    @classmethod
    def quote_result(
        cls,
        request_id: str,
        quote_id: str,
        client_quote_id: Optional[str],
        status: Union[QuoteResultStatus, str],
        position_id: Optional[str] = None,
        fill_amount: Optional[str] = None,
        fill_odds: Optional[int] = None,
        filled_at_ms: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> ServerMessage:
        return cls(
            "QuoteResult",
            request_id=request_id,
            quote_id=quote_id,
            client_quote_id=client_quote_id,
            status=status,
            position_id=position_id,
            fill_amount=fill_amount,
            fill_odds=fill_odds,
            filled_at_ms=filled_at_ms,
            reason=reason,
        )

    @classmethod
    def ping(cls, timestamp: int) -> ServerMessage:
        return cls("Ping", timestamp=timestamp)

    @classmethod
    def error(cls, code: str, message: str) -> ServerMessage:
        return cls("Error", code=code, message=message)

    @classmethod
    def rate_limit(cls, retry_after_ms: int) -> ServerMessage:
        return cls("RateLimit", retry_after_ms=retry_after_ms)


_install_serde_metadata(
    globals(),
    STRUCT_INTEGER_FIELDS,
    STRUCT_REQUIRED_FIELDS,
    TAGGED_UNION_FIELDS,
    DENY_UNKNOWN_TAGGED_UNIONS,
)
