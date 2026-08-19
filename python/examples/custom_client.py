"""Executable, transport-free examples for constructing Longshot wire payloads."""

from __future__ import annotations

import json
from typing import Any, Dict, Union
from uuid import UUID

from eth_account import Account
from eth_account.messages import encode_defunct

from longshot_protocol import (
    Address,
    Amount,
    CreateRfqRequest,
    Direction,
    Odds,
    OrderLeg,
    OrderType,
    RequestId,
    SignedOrder,
    UserWithdrawParams,
    UserWithdrawRequest,
    WalletAuthRequest,
    WithdrawalAuthorization,
    auth_response_message,
    build_wallet_authentication_message,
    build_wallet_withdrawal_authorization_message,
    encode_wallet_signature,
    quote_response_message,
    sign_order,
    signed_quote_response,
)

# This deterministic key is public test data. Never fund or reuse it outside examples.
EXAMPLE_SIGNING_KEY = "0x" + "01" * 32
# These fixed values make the example reproducible. A real client injects the
# target deployment's domain and chain ID plus current timestamps and expiry.
EXAMPLE_DOMAIN = "longshot.xyz"
EXAMPLE_CHAIN_ID = 8453
EXAMPLE_SIGNED_AT_MS = 1_785_529_737_000
EXAMPLE_ORDER_EXPIRES_AT_MS = EXAMPLE_SIGNED_AT_MS + 15 * 60 * 1_000
EXAMPLE_IDEMPOTENCY_KEY = UUID("550e8400-e29b-41d4-a716-446655440000")
EXAMPLE_DESTINATION_ADDRESS = "0xde709f2102306220921060314715629080e2fb77"
EXAMPLE_MM_CHALLENGE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
EXAMPLE_MM_REQUEST_ID = "00112233-4455-6677-8899-aabbccddeeff"


def _sign_text(message: str, signing_key: Union[str, bytes]) -> bytes:
    return bytes(
        Account.sign_message(
            encode_defunct(text=message),
            private_key=signing_key,
        ).signature
    )


def build_example_payloads(
    *,
    signing_key: Union[str, bytes] = EXAMPLE_SIGNING_KEY,
    domain: str = EXAMPLE_DOMAIN,
    chain_id: int = EXAMPLE_CHAIN_ID,
    signed_at_ms: int = EXAMPLE_SIGNED_AT_MS,
    order_expires_at_ms: int = EXAMPLE_ORDER_EXPIRES_AT_MS,
) -> Dict[str, Any]:
    """Build deterministic request bodies without performing network I/O."""

    account = Account.from_key(signing_key)
    auth_address = Address.from_evm(account.address)

    authentication_message = build_wallet_authentication_message(
        domain,
        auth_address,
        signed_at_ms,
    )
    authentication_signature = _sign_text(authentication_message, signing_key)
    authentication_request = WalletAuthRequest(
        address=auth_address.to_checksum(),
        signature=encode_wallet_signature(authentication_signature),
        signed_at_ms=signed_at_ms,
    )

    unsigned_order = SignedOrder(
        user=auth_address,
        wager_micros=1_000_000,
        # SignedOrder uses basis points internally; the HTTP DTO converts this to 2.5.
        min_odds_bps=25_000,
        legs=[OrderLeg(market_id=42, direction=Direction.Up)],
        nonce=7,
        expires_at_ms=order_expires_at_ms,
        order_type=OrderType.FOK,
        shield_on=False,
    )
    use_app_tokens = False
    # The funding choice is part of the signature and must match the request field.
    signed = sign_order(unsigned_order, use_app_tokens, signing_key)
    rfq_request = CreateRfqRequest.from_signed_order(signed, use_app_tokens)

    withdrawal_message = build_wallet_withdrawal_authorization_message(
        domain,
        chain_id,
        auth_address,
        EXAMPLE_DESTINATION_ADDRESS,
        1_000_000,
        EXAMPLE_IDEMPOTENCY_KEY,
        signed_at_ms,
    )
    withdrawal_signature = _sign_text(withdrawal_message, signing_key)
    withdrawal_request = UserWithdrawRequest(
        withdraw_params=UserWithdrawParams(
            amount_micros=1_000_000,
            destination_address=EXAMPLE_DESTINATION_ADDRESS,
            idempotency_key=str(EXAMPLE_IDEMPOTENCY_KEY),
        ),
        authorization=WithdrawalAuthorization.wallet_signature(
            signature=encode_wallet_signature(withdrawal_signature),
            signed_at_ms=signed_at_ms,
        ),
    )

    mm_auth_response = auth_response_message(
        EXAMPLE_MM_CHALLENGE_ID,
        signed_at_ms,
        signing_key,
    )
    signed_quote = signed_quote_response(
        RequestId.from_string(EXAMPLE_MM_REQUEST_ID),
        Odds(25_000),
        Amount.from_micro(5_000_000),
        signing_key,
    )
    # MM auth uses lowercase hex while binary quote frames use unpadded Base64.
    mm_quote_response = quote_response_message(signed_quote)

    return {
        "wallet_authentication": {
            "message": authentication_message,
            "request_body": authentication_request.to_dict(),
        },
        "signed_rfq": {
            "signing_bytes_hex": signed.signing_bytes(use_app_tokens).hex(),
            "request_body": rfq_request.to_dict(),
        },
        "wallet_withdrawal": {
            "message": withdrawal_message,
            "request_body": withdrawal_request.to_dict(),
        },
        "market_maker": {
            "auth_response": mm_auth_response.to_dict(),
            "quote_response": mm_quote_response.to_dict(),
        },
    }


def main() -> None:
    print(json.dumps(build_example_payloads(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
