"""Market-maker protocol helpers."""

from __future__ import annotations

from base64 import b64decode, b64encode
from binascii import Error as BinasciiError
from typing import Optional, Union
from uuid import RFC_4122, UUID

from eth_account import Account
from eth_account.messages import encode_defunct

from .rfq import BroadcastRfqRequest, MAX_RFQ_LEGS, QuoteResponse, RFQ_PROTOCOL_VERSION
from .types import Address, Amount, ClientQuoteId, Odds, RequestId
from .ws import ClientMessage

AUTH_DOMAIN = "longshot.xyz"


class AuthChallengeIdError(ValueError):
    """Raised when an MM WebSocket challenge ID is not canonical UUIDv4 text."""


class MmDecodeError(ValueError):
    """Market-maker fixed-size payload decode error."""

    def __init__(
        self,
        message: str,
        *,
        kind: Optional[str] = None,
        expected: Optional[int] = None,
        actual: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.expected = expected
        self.actual = actual


def parse_auth_challenge_id(challenge_id: str) -> UUID:
    try:
        parsed = UUID(challenge_id)
    except (AttributeError, TypeError, ValueError) as exc:
        raise AuthChallengeIdError("challenge ID must be a UUID") from exc
    if str(parsed) != challenge_id:
        raise AuthChallengeIdError(
            "challenge ID must be lowercase canonical hyphenated UUID text"
        )
    if parsed.variant != RFC_4122:
        raise AuthChallengeIdError("challenge ID must use the RFC 4122 variant")
    if parsed.version != 4:
        raise AuthChallengeIdError("challenge ID must be a UUIDv4")
    return parsed


def build_auth_message(
    auth_address: Union[str, Address],
    challenge_id: Union[str, UUID],
    timestamp_ms: int,
) -> str:
    address = Address.from_evm(auth_address).to_checksum()
    parsed_challenge_id = (
        parse_auth_challenge_id(challenge_id)
        if isinstance(challenge_id, str)
        else parse_auth_challenge_id(str(challenge_id))
    )
    if (
        not isinstance(timestamp_ms, int)
        or isinstance(timestamp_ms, bool)
        or not 0 <= timestamp_ms <= (1 << 64) - 1
    ):
        raise ValueError("timestamp_ms must fit in u64")
    return (
        "Longshot Market Maker WebSocket Authentication\n\n"
        f"Version: 1\nDomain: {AUTH_DOMAIN}\nAuth Address: {address}\n"
        f"Challenge ID: {parsed_challenge_id}\nTimestamp: {timestamp_ms}"
    )


def _decode_unpadded_base64(data: str) -> bytes:
    if "=" in data:
        raise MmDecodeError("invalid base64 payload: padding is not allowed")
    padding = "=" * ((4 - len(data) % 4) % 4)
    try:
        decoded = b64decode(data + padding, validate=True)
    except (BinasciiError, ValueError) as exc:
        # b64decode uses ValueError for non-ASCII strings and BinasciiError for
        # ASCII-invalid input; callers should receive one MM decode error contract.
        raise MmDecodeError(f"invalid base64 payload: {exc}") from exc
    if b64encode(decoded).decode("ascii").rstrip("=") != data:
        raise MmDecodeError("invalid base64 payload: non-canonical encoding")
    return decoded


def sign_auth_response(
    challenge_id: Union[str, UUID],
    timestamp_ms: int,
    signing_key: Union[str, bytes],
) -> bytes:
    account = Account.from_key(signing_key)
    return bytes(
        Account.sign_message(
            encode_defunct(
                text=build_auth_message(account.address, challenge_id, timestamp_ms)
            ),
            signing_key,
        ).signature
    )


def auth_response_message(
    challenge_id: Union[str, UUID],
    timestamp_ms: int,
    signing_key: Union[str, bytes],
) -> ClientMessage:
    address = Account.from_key(signing_key).address
    return ClientMessage.auth_response(
        address,
        sign_auth_response(challenge_id, timestamp_ms, signing_key).hex(),
    )


def sign_quote_response(quote: QuoteResponse, signing_key: Union[str, bytes]) -> QuoteResponse:
    signature = bytes(
        Account.sign_message(
            encode_defunct(primitive=quote.signed_data_bytes()),
            signing_key,
        ).signature
    )
    return QuoteResponse(
        request_id=quote.request_id,
        odds=quote.odds,
        max_fill_micros=quote.max_fill_micros,
        client_quote_id=quote.client_quote_id,
        signature=signature,
        reserved=quote.reserved,
    )


def signed_quote_response(
    request_id: RequestId,
    odds: Odds,
    max_fill: Amount,
    signing_key: Union[str, bytes],
    client_quote_id: Optional[ClientQuoteId] = None,
) -> QuoteResponse:
    return sign_quote_response(
        QuoteResponse.new(request_id, odds, max_fill, client_quote_id),
        signing_key,
    )


def signed_quote_response_with_client_quote_id(
    request_id: RequestId,
    odds: Odds,
    max_fill: Amount,
    client_quote_id: ClientQuoteId,
    signing_key: Union[str, bytes],
) -> QuoteResponse:
    return signed_quote_response(
        request_id,
        odds,
        max_fill,
        signing_key,
        client_quote_id,
    )


def encode_quote_response(quote: QuoteResponse) -> str:
    return b64encode(quote.to_bytes()).decode("ascii").rstrip("=")


def decode_quote_response(data: str) -> QuoteResponse:
    decoded = _decode_unpadded_base64(data)
    if len(decoded) != QuoteResponse.SIZE:
        raise MmDecodeError(
            "invalid quote response payload size: "
            f"expected {QuoteResponse.SIZE} bytes, got {len(decoded)}",
            kind="quote response",
            expected=QuoteResponse.SIZE,
            actual=len(decoded),
        )
    return QuoteResponse.from_bytes(decoded)


def quote_response_message(quote: QuoteResponse) -> ClientMessage:
    return ClientMessage.quote(encode_quote_response(quote))


def decode_broadcast_rfq(data: str) -> BroadcastRfqRequest:
    decoded = _decode_unpadded_base64(data)
    if len(decoded) != BroadcastRfqRequest.SIZE:
        raise MmDecodeError(
            "invalid broadcast RFQ payload size: "
            f"expected {BroadcastRfqRequest.SIZE} bytes, got {len(decoded)}",
            kind="broadcast RFQ",
            expected=BroadcastRfqRequest.SIZE,
            actual=len(decoded),
        )
    request = BroadcastRfqRequest.from_bytes(decoded)
    if request.protocol_version != RFQ_PROTOCOL_VERSION:
        raise MmDecodeError(
            "unsupported RFQ protocol version: "
            f"expected {RFQ_PROTOCOL_VERSION}, got {request.protocol_version}",
            expected=RFQ_PROTOCOL_VERSION,
            actual=request.protocol_version,
        )
    if not 1 <= request.leg_count <= MAX_RFQ_LEGS:
        raise MmDecodeError(
            "invalid broadcast RFQ leg count: "
            f"expected 1..={MAX_RFQ_LEGS}, got {request.leg_count}"
        )
    return request
