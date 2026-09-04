from __future__ import annotations

import json
import unittest
from base64 import b64decode, b64encode
from dataclasses import fields, replace
from pathlib import Path

from eth_account import Account
from eth_account.messages import encode_defunct

from longshot_protocol import (
    Address,
    Amount,
    Asset,
    BroadcastRfqRequest,
    Direction,
    Duration,
    MarketId,
    MmDecodeError,
    MathError,
    MAX_RFQ_LEGS,
    Odds,
    OrderLeg,
    OrderType,
    QuoteResponse,
    RequestId,
    RfqLeg,
    RfqLegType,
    RfqLegWire,
    RfqLegWireDecodeError,
    RFQ_PROTOCOL_VERSION,
    SignedOrder,
    SignedOrderError,
    SignedOrderJson,
    TakerSignError,
    Timestamp,
    auth_response_message,
    build_auth_message,
    decode_broadcast_rfq,
    decode_quote_response,
    encode_quote_response,
    parse_auth_challenge_id,
    sign_auth_response,
    sign_order,
    sign_quote_response,
    signed_order,
    signed_quote_response,
)
from longshot_protocol.types import U64_MAX

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "protocol" / "parity.json"


def _rfq_leg(row: dict[str, int]) -> RfqLeg:
    if row["type_tag"] == 0:
        return RfqLeg.price_strike(
            market_id=row["market_id"],
            start_at_ms=row["start_at_ms"],
            asset=Asset(row["asset"]),
            direction=Direction(row["direction"]),
            window=Duration.from_secs(row["price_window_secs"]),
            leg_index=row["leg_index"],
        )
    if row["type_tag"] == 2:
        return RfqLeg.binary_event(
            market_id=row["market_id"],
            start_at_ms=row["start_at_ms"],
            direction=Direction(row["direction"]),
            leg_index=row["leg_index"],
        )
    raise AssertionError(f"unsupported RFQ leg type tag {row['type_tag']}")


class ProtocolFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text())

    def test_auth_message_matches_rust_fixture(self) -> None:
        case = self.fixture["auth_message"]
        message = build_auth_message(
            self.fixture["mm_signing"]["wallet_address"],
            case["challenge_id"],
            case["timestamp_ms"],
        )
        self.assertEqual(message, case["message"])
        self.assertEqual(message.encode().hex(), case["message_hex"])

    def test_auth_challenge_id_requires_canonical_rfc4122_uuid_v4(self) -> None:
        canonical = "550e8400-e29b-41d4-a716-446655440000"
        self.assertEqual(str(parse_auth_challenge_id(canonical)), canonical)
        for invalid in (
            canonical.upper(),
            canonical.replace("-", ""),
            "550e8400-e29b-11d4-a716-446655440000",
            "550e8400-e29b-41d4-0716-446655440000",
            "not-a-uuid",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                parse_auth_challenge_id(invalid)

    def test_address_helpers_use_evm_normalization(self) -> None:
        case = self.fixture["mm_signing"]
        address = Address.from_hex(case["wallet_address"].lower())

        self.assertEqual(address.to_checksum(), case["wallet_address"])
        self.assertEqual(Address.ZERO, Address.zero())
        self.assertEqual(str(address), case["wallet_address"])
        self.assertEqual(address.hex(), case["wallet_address"].lower())

        with self.assertRaises(ValueError):
            Address.from_hex("not-an-address")

    def test_taker_signing_bytes_match_rust_fixture(self) -> None:
        case = self.fixture["taker_signed_order"]
        signed_order_fields = {field.name for field in fields(SignedOrder)}
        self.assertIn("min_odds_bps", signed_order_fields)
        self.assertNotIn("min_odds", signed_order_fields)
        order = SignedOrder(
            user=Address.from_hex(case["user"]),
            wager_micros=case["wager_micros"],
            min_odds_bps=case["min_odds_bps"],
            nonce=case["nonce"],
            expires_at_ms=case["expires_at_ms"],
            order_type=OrderType(case["order_type"]),
            shield_on=case["shield_on"],
            legs=[
                OrderLeg(market_id=leg["market_id"], direction=leg["direction"])
                for leg in case["legs"]
            ],
        )
        self.assertEqual(
            order.signing_bytes(case["use_app_tokens"]).hex(),
            case["signing_bytes_hex"],
        )
        invalid_orders = (
            replace(order, legs=[]),
            replace(order, legs=[OrderLeg(market_id=42, direction=2)]),
            replace(order, legs=[OrderLeg(market_id=42, direction=True)]),
            replace(order, legs=[OrderLeg(market_id=42, direction=1.0)]),
            replace(order, legs=[OrderLeg(market_id=42.9, direction=0)]),
            replace(order, legs=[OrderLeg(market_id=True, direction=0)]),
            replace(order, legs=[OrderLeg(market_id="42", direction=0)]),
            replace(order, legs=[OrderLeg(market_id=-1, direction=0)]),
            replace(order, legs=[OrderLeg(market_id=U64_MAX + 1, direction=0)]),
            replace(order, legs=order.legs * (SignedOrder.MAX_LEGS + 1)),
            replace(order, order_type=3),
            replace(order, order_type=1.5),
            replace(order, order_type=True),
            replace(order, shield_on=1),
            replace(order, shield_on="false"),
            replace(order, wager_micros=U64_MAX + 1),
        )
        for invalid in invalid_orders:
            for serialize in (
                lambda: invalid.signing_bytes(case["use_app_tokens"]),
                lambda: SignedOrderJson.from_signed_order(invalid),
            ):
                with self.assertRaises(ValueError):
                    serialize()

        for invalid_use_app_tokens in (1, "false"):
            with self.subTest(use_app_tokens=invalid_use_app_tokens):
                with self.assertRaisesRegex(ValueError, "use_app_tokens must be bool"):
                    order.signing_bytes(invalid_use_app_tokens)

        with self.assertRaisesRegex(ValueError, "direction must fit in u8"):
            OrderLeg(market_id=42, direction=True).to_bytes()

    def test_taker_signing_helper_signs_eip191_preimage(self) -> None:
        case = self.fixture["taker_signed_order"]
        signing = self.fixture["mm_signing"]
        account = Account.from_key(signing["private_key"])
        order = SignedOrder(
            user=Address.from_hex(account.address),
            wager_micros=case["wager_micros"],
            min_odds_bps=case["min_odds_bps"],
            nonce=case["nonce"],
            expires_at_ms=case["expires_at_ms"],
            order_type=OrderType(case["order_type"]),
            shield_on=case["shield_on"],
            legs=[OrderLeg(market_id=42, direction=Direction.Down)],
        )

        use_app_tokens = case["use_app_tokens"]
        signed = sign_order(order, use_app_tokens, signing["private_key"])
        built = signed_order(order, use_app_tokens, signing["private_key"])

        self.assertEqual(signed, built)
        self.assertNotEqual(signed.signature, bytes(65))
        self.assertTrue(signed.verify_signature(use_app_tokens))
        self.assertFalse(signed.verify_signature(not use_app_tokens))
        recovered = Account.recover_message(
            encode_defunct(primitive=order.signing_bytes(use_app_tokens)),
            signature=signed.signature,
        )
        self.assertEqual(recovered, account.address)
        tampered_signature = bytes([signed.signature[0] ^ 1]) + signed.signature[1:]
        self.assertFalse(
            replace(signed, signature=tampered_signature).verify_signature(use_app_tokens)
        )
        self.assertFalse(
            replace(signed, wager_micros=signed.wager_micros + 1).verify_signature(
                use_app_tokens
            )
        )
        self.assertFalse(replace(signed, legs=[]).verify_signature(use_app_tokens))

    def test_taker_signing_uses_advertised_error_boundary(self) -> None:
        case = self.fixture["taker_signed_order"]
        signing_key = self.fixture["mm_signing"]["private_key"]
        order = SignedOrder(
            user=Address.from_hex(case["user"]),
            wager_micros=case["wager_micros"],
            min_odds_bps=case["min_odds_bps"],
            nonce=case["nonce"],
            expires_at_ms=case["expires_at_ms"],
            order_type=OrderType(case["order_type"]),
            shield_on=case["shield_on"],
            legs=[OrderLeg(market_id=42, direction=Direction.Down)],
        )

        with self.assertRaisesRegex(
            TakerSignError, "failed to sign taker order"
        ) as invalid_order:
            sign_order(replace(order, legs=[]), case["use_app_tokens"], signing_key)
        self.assertIsInstance(invalid_order.exception.__cause__, SignedOrderError)
        self.assertEqual(
            str(invalid_order.exception.__cause__),
            "order must include at least one leg",
        )

        with self.assertRaisesRegex(
            TakerSignError, "failed to sign taker order"
        ) as invalid_key:
            signed_order(order, case["use_app_tokens"], b"bad")
        self.assertIsInstance(invalid_key.exception.__cause__, ValueError)
        self.assertIn("exactly 32 bytes", str(invalid_key.exception.__cause__))

    def test_taker_signing_rejects_more_than_max_legs(self) -> None:
        case = self.fixture["taker_signed_order"]
        order = SignedOrder(
            user=Address.from_hex(case["user"]),
            wager_micros=case["wager_micros"],
            min_odds_bps=case["min_odds_bps"],
            nonce=case["nonce"],
            expires_at_ms=case["expires_at_ms"],
            order_type=OrderType(case["order_type"]),
            shield_on=case["shield_on"],
            legs=[OrderLeg(market_id=42, direction=Direction.Down)] * SignedOrder.MAX_LEGS,
        )
        self.assertEqual(SignedOrder.MAX_LEGS, 9)
        order.signing_bytes(case["use_app_tokens"])
        order.legs.append(OrderLeg(market_id=99, direction=Direction.Up))

        with self.assertRaisesRegex(ValueError, "order legs exceed MAX_LEGS"):
            order.signing_bytes(case["use_app_tokens"])

    def test_quote_response_matches_rust_fixture(self) -> None:
        case = self.fixture["quote_response"]
        quote = QuoteResponse.new(
            request_id=RequestId.from_string(case["request_id"]),
            odds=Odds(case["odds"]),
            max_fill=Amount.from_micro(case["max_fill_micros"]),
        )
        self.assertEqual(quote.to_bytes().hex(), case["bytes_hex"])
        self.assertEqual(quote.signed_data_bytes().hex(), case["signed_data_hex"])
        self.assertEqual(encode_quote_response(quote), case["base64"])
        self.assertEqual(decode_quote_response(case["base64"]).to_bytes(), quote.to_bytes())
        self.assertEqual(quote.request_id(), RequestId.from_string(case["request_id"]))
        self.assertEqual(quote.odds(), Odds(case["odds"]))
        self.assertEqual(quote.max_fill(), Amount.from_micro(case["max_fill_micros"]))
        self.assertEqual(QuoteResponse.from_slice(quote.to_bytes()), quote)
        self.assertIsNone(QuoteResponse.from_slice(quote.to_bytes()[:-1]))

    def test_mm_signing_matches_rust_fixture(self) -> None:
        auth = self.fixture["auth_message"]
        quote_case = self.fixture["quote_response"]
        case = self.fixture["mm_signing"]

        auth_signature = sign_auth_response(
            auth["challenge_id"],
            auth["timestamp_ms"],
            case["private_key"],
        )

        self.assertEqual(auth_signature.hex(), case["auth_signature_hex"])
        self.assertEqual(
            auth_response_message(
                auth["challenge_id"],
                auth["timestamp_ms"],
                case["private_key"],
            ).to_dict(),
            {
                "type": "auth_response",
                "wallet_address": case["wallet_address"],
                "signature": case["auth_signature_hex"],
            },
        )

        unsigned_quote = QuoteResponse.new(
            request_id=RequestId.from_string(quote_case["request_id"]),
            odds=Odds(quote_case["odds"]),
            max_fill=Amount.from_micro(quote_case["max_fill_micros"]),
        )
        signed_quote = sign_quote_response(unsigned_quote, case["private_key"])

        self.assertEqual(signed_quote.signature.hex(), case["quote_signature_hex"])
        self.assertEqual(signed_quote.to_bytes().hex(), case["signed_quote_bytes_hex"])
        self.assertEqual(encode_quote_response(signed_quote), case["signed_quote_base64"])
        self.assertTrue(signed_quote.verify_signature(Address.from_hex(case["wallet_address"])))

        built_quote = signed_quote_response(
            RequestId.from_string(quote_case["request_id"]),
            Odds(quote_case["odds"]),
            Amount.from_micro(quote_case["max_fill_micros"]),
            case["private_key"],
        )
        self.assertEqual(built_quote, signed_quote)

        tampered_quote = QuoteResponse(
            request_id=signed_quote.request_id,
            odds=30_000,
            max_fill_micros=signed_quote.max_fill_micros,
            client_quote_id=signed_quote.client_quote_id,
            signature=signed_quote.signature,
            reserved=signed_quote.reserved,
        )
        self.assertFalse(tampered_quote.verify_signature(Address.from_hex(case["wallet_address"])))

    def test_mm_decode_errors_match_rust_error_shape(self) -> None:
        case = self.fixture["quote_response"]
        wrong_size = b64encode(bytes(QuoteResponse.SIZE - 1)).decode("ascii").rstrip("=")

        with self.assertRaises(MmDecodeError) as wrong_size_error:
            decode_quote_response(wrong_size)
        self.assertEqual(wrong_size_error.exception.kind, "quote response")
        self.assertEqual(wrong_size_error.exception.expected, QuoteResponse.SIZE)
        self.assertEqual(wrong_size_error.exception.actual, QuoteResponse.SIZE - 1)

        with self.assertRaises(MmDecodeError):
            decode_quote_response(case["base64"] + "!")
        with self.assertRaises(MmDecodeError):
            decode_quote_response(case["base64"][:-1] + "B")

        wrong_rfq_size = b64encode(bytes(BroadcastRfqRequest.SIZE - 1)).decode(
            "ascii"
        ).rstrip("=")
        with self.assertRaises(MmDecodeError) as wrong_rfq_size_error:
            decode_broadcast_rfq(wrong_rfq_size)
        self.assertEqual(wrong_rfq_size_error.exception.kind, "broadcast RFQ")
        self.assertEqual(
            wrong_rfq_size_error.exception.expected, BroadcastRfqRequest.SIZE
        )
        self.assertEqual(
            wrong_rfq_size_error.exception.actual, BroadcastRfqRequest.SIZE - 1
        )

    def test_mm_decoders_reject_padded_base64(self) -> None:
        quote_case = self.fixture["quote_response"]
        rfq_case = self.fixture["broadcast_rfq"]

        with self.assertRaises(MmDecodeError):
            decode_quote_response(quote_case["base64"] + "==")
        with self.assertRaises(MmDecodeError):
            decode_broadcast_rfq(rfq_case["base64"] + "==")

    def test_mm_decoders_normalize_non_ascii_base64_errors(self) -> None:
        for decoder in (decode_quote_response, decode_broadcast_rfq):
            for payload in ("é", "💥"):
                with self.subTest(decoder=decoder.__name__, payload=payload):
                    with self.assertRaises(MmDecodeError):
                        decoder(payload)

    def test_broadcast_rfq_matches_rust_fixture(self) -> None:
        case = self.fixture["broadcast_rfq"]
        legs = [_rfq_leg(row) for row in case["legs"]]
        padding = "=" * ((4 - len(case["base64"]) % 4) % 4)
        encoded = b64decode(case["base64"] + padding, validate=True)
        decoded = decode_broadcast_rfq(case["base64"])

        self.assertEqual(encoded.hex(), case["bytes_hex"])
        self.assertEqual(
            b64encode(decoded.to_bytes()).decode("ascii").rstrip("="),
            case["base64"],
        )
        self.assertEqual(decoded.protocol_version, RFQ_PROTOCOL_VERSION)
        self.assertEqual(decoded.to_bytes(), encoded)
        self.assertEqual(decoded.wager(), Amount.from_micro(case["wager_micros"]))
        self.assertEqual(decoded.request_id(), RequestId.from_string(case["request_id"]))
        self.assertEqual(decoded.expires_at(), Timestamp.from_millis(case["expires_at_ms"]))
        self.assertEqual(decoded.order_type(), OrderType(case["order_type"]))
        self.assertEqual(decoded.order_type_value(), OrderType(case["order_type"]))
        self.assertEqual(decoded.leg_count, MAX_RFQ_LEGS)
        self.assertEqual(len(decoded.active_leg_wires()), MAX_RFQ_LEGS)
        self.assertEqual(len(list(decoded.iter_leg_wires())), MAX_RFQ_LEGS)
        self.assertEqual(list(decoded.iter_legs()), legs)
        self.assertEqual(decoded.leg_wire(0).to_leg(), legs[0])
        self.assertEqual(decoded.leg(MAX_RFQ_LEGS - 1), legs[-1])
        self.assertIsNone(decoded.leg(MAX_RFQ_LEGS))
        self.assertEqual(decoded.taker_metadata.tier, case["taker_metadata"]["tier"])
        self.assertEqual(
            decoded.taker_address(),
            Address.from_hex(case["taker_metadata"]["address"]),
        )

    def test_broadcast_rfq_preserves_taker_metadata_wire_bytes(self) -> None:
        case = self.fixture["broadcast_rfq"]
        padding = "=" * ((4 - len(case["base64"]) % 4) % 4)
        raw = bytearray(b64decode(case["base64"] + padding, validate=True))
        raw[32] = 2
        raw[34:36] = b"\xaa\xbb"

        decoded = decode_broadcast_rfq(
            b64encode(raw).decode("ascii").rstrip("=")
        )

        self.assertEqual(decoded.to_bytes(), bytes(raw))

    def test_rfq_leg_builder_rejects_boolean_enum_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "asset must fit in u8"):
            RfqLeg.price_strike(
                1,
                0,
                True,
                Direction.Up,
                Duration.ONE_MINUTE,
                0,
            )
        with self.assertRaisesRegex(ValueError, "direction must fit in u8"):
            RfqLeg.price_strike(
                1,
                0,
                Asset.BTC,
                True,
                Duration.ONE_MINUTE,
                0,
            )

    def test_decode_broadcast_rfq_preserves_invalid_active_leg_wire(self) -> None:
        case = self.fixture["broadcast_rfq"]
        padding = "=" * ((4 - len(case["base64"]) % 4) % 4)
        raw = bytearray(b64decode(case["base64"] + padding, validate=True))
        raw[64 + 17] = 255
        encoded = b64encode(raw).decode("ascii").rstrip("=")

        decoded = decode_broadcast_rfq(encoded)

        self.assertEqual(decoded.to_bytes(), bytes(raw))
        self.assertEqual(decoded.leg_wire(0).direction, 255)
        with self.assertRaises(RfqLegWireDecodeError):
            decoded.leg(0)
        with self.assertRaises(RfqLegWireDecodeError):
            list(decoded.iter_legs())

    def test_rfq_leg_wire_decoder_round_trips_inactive_padding(self) -> None:
        wire = RfqLegWire.default()
        raw = wire.to_bytes()

        self.assertEqual(RfqLegWire.from_bytes(raw), wire)
        with self.assertRaises(RfqLegWireDecodeError):
            RfqLeg.from_wire_bytes(raw)

    def test_raw_rfq_parser_preserves_invalid_counts_but_public_decoder_rejects_them(
        self,
    ) -> None:
        case = self.fixture["broadcast_rfq"]
        padding = "=" * ((4 - len(case["base64"]) % 4) % 4)
        for leg_count in (0, MAX_RFQ_LEGS + 1):
            raw = bytearray(b64decode(case["base64"] + padding, validate=True))
            raw[57] = leg_count

            parsed = BroadcastRfqRequest.from_bytes(bytes(raw))
            self.assertEqual(parsed.leg_count, leg_count)
            self.assertEqual(parsed.to_bytes(), bytes(raw))

            encoded = b64encode(raw).decode("ascii").rstrip("=")
            with self.assertRaisesRegex(MmDecodeError, "expected 1..=9"):
                decode_broadcast_rfq(encoded)

    def test_primitive_helpers_match_rust_semantics(self) -> None:
        before = Timestamp.now().as_millis()
        expiry = Duration.FIFTEEN_MINUTES.expiry_from_now()
        after = Timestamp.now().as_millis()
        self.assertGreaterEqual(expiry, before + Duration.FIFTEEN_MINUTES.as_secs() * 1000)
        self.assertLessEqual(expiry, after + Duration.FIFTEEN_MINUTES.as_secs() * 1000)

        max_seconds = U64_MAX // 1000
        self.assertEqual(
            Timestamp.from_secs(max_seconds),
            Timestamp.from_millis(max_seconds * 1000),
        )
        self.assertIsNone(Timestamp.from_secs(U64_MAX))
        self.assertEqual(
            Timestamp.from_millis(U64_MAX).add_millis(0),
            Timestamp.from_millis(U64_MAX),
        )
        self.assertIsNone(Timestamp.from_millis(U64_MAX).add_millis(1))

        odds = Odds.from_decimal(2, 0)
        self.assertEqual(odds.to_f64(), odds.to_float())
        self.assertEqual(odds.checked_calculate_mm_liability(1_000_000), 1_000_000)
        self.assertIsNone(Odds(5_000).checked_calculate_mm_liability(1_000_000))
        wager = U64_MAX // 2 + 1
        self.assertIsNone(odds.checked_calculate_payout(wager))
        self.assertEqual(odds.calculate_payout(wager), U64_MAX)
        self.assertEqual(odds.checked_calculate_profit(wager), wager)
        self.assertEqual(Odds.from_decimal(3, 0).calculate_profit(wager), U64_MAX)

        lhs = Amount.from_micro(1_500_000)
        rhs = Amount.from_micro(2_000_000)
        self.assertEqual(lhs.fixed_mul(rhs), Amount.from_micro(3_000_000))
        self.assertEqual(Amount.from_micro(3_000_000).fixed_div(rhs), lhs)
        self.assertEqual(
            lhs.fixed_mul_div(rhs, Amount.from_micro(500_000)),
            Amount.from_micro(6_000_000),
        )
        self.assertEqual(lhs.to_f64(), lhs.to_float())
        self.assertEqual(
            Amount.from_micro(U64_MAX).saturating_add(Amount.from_micro(1)).as_micros(),
            U64_MAX,
        )
        self.assertEqual(
            Amount.from_micro(10).saturating_sub(Amount.from_micro(100)),
            Amount.ZERO,
        )

        with self.assertRaises(ArithmeticError) as division_error:
            Amount.from_micro(1_000_000).fixed_div(Amount.ZERO)
        self.assertIs(division_error.exception.args[0], MathError.DivisionByZero)

        with self.assertRaises(ArithmeticError) as overflow_error:
            Amount.from_micro(U64_MAX).fixed_mul(Amount.from_micro(U64_MAX))
        self.assertIs(overflow_error.exception.args[0], MathError.Overflow)

        self.assertEqual(Asset.COUNT, 3)
        self.assertEqual(Asset.ALL, [Asset.BTC, Asset.ETH, Asset.SOL])
        self.assertEqual(MarketId.new(42), MarketId(42))
        self.assertEqual(str(MarketId(42)), "42")
        self.assertEqual(RequestId.from_uuid(RequestId.nil().as_uuid()), RequestId.nil())
        self.assertEqual(RequestId.nil().as_bytes(), RequestId.nil().bytes)
        self.assertTrue(RfqLegType.binary_event().is_binary_event())
        self.assertEqual(str(Asset.BTC), "BTC")
        self.assertEqual(str(Direction.Up), "UP")
        self.assertEqual(str(Duration.FIFTEEN_MINUTES), "15m")
        self.assertEqual(str(Duration.FOUR_HOURS), "4h")
        self.assertEqual(str(Duration.ONE_DAY), "1d")
        self.assertEqual(str(Odds.from_decimal(2, 5000)), "2.5000x")
        self.assertEqual(str(Amount.from_dollars(50)), "$50.00")
        self.assertEqual(str(Timestamp.from_millis(123)), "123ms")
        self.assertEqual(Amount.from_micro(U64_MAX) + Amount.from_micro(1), Amount.from_micro(U64_MAX))
        self.assertEqual(Amount.from_micro(10) - Amount.from_micro(100), Amount.ZERO)

if __name__ == "__main__":
    unittest.main()
