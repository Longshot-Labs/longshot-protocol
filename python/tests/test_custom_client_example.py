from __future__ import annotations

import importlib.util
import io
import json
import unittest
from base64 import b64decode
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

from eth_account import Account
from eth_account.messages import encode_defunct
from longshot_protocol import Address, SignedOrderJson, decode_quote_response


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "custom_client.py"
)


def _load_example() -> ModuleType:
    spec = importlib.util.spec_from_file_location("custom_client", EXAMPLE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load example at {EXAMPLE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CustomClientExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example = _load_example()

    def test_example_builds_verifiable_wire_payloads(self) -> None:
        payloads = self.example.build_example_payloads()
        expected_address = Account.from_key(self.example.EXAMPLE_SIGNING_KEY).address

        wallet_authentication = payloads["wallet_authentication"]
        auth_request = wallet_authentication["request_body"]
        recovered_auth_address = Account.recover_message(
            encode_defunct(text=wallet_authentication["message"]),
            signature=b64decode(auth_request["signature"], validate=True),
        )
        self.assertEqual(recovered_auth_address, expected_address)
        self.assertEqual(auth_request["address"], expected_address)

        signed_rfq = payloads["signed_rfq"]["request_body"]
        self.assertFalse(signed_rfq["use_app_tokens"])
        self.assertEqual(signed_rfq["order"]["min_odds"], 2.5)
        self.assertEqual(len(signed_rfq["order"]["signature"]), 88)
        signed_order = SignedOrderJson.from_dict(signed_rfq["order"]).to_signed_order()
        self.assertTrue(signed_order.verify_signature(signed_rfq["use_app_tokens"]))
        self.assertEqual(
            signed_order.signing_bytes(signed_rfq["use_app_tokens"]).hex(),
            payloads["signed_rfq"]["signing_bytes_hex"],
        )

        wallet_withdrawal = payloads["wallet_withdrawal"]
        withdrawal_authorization = wallet_withdrawal["request_body"]["authorization"]
        recovered_withdrawal_address = Account.recover_message(
            encode_defunct(text=wallet_withdrawal["message"]),
            signature=b64decode(
                withdrawal_authorization["signature"], validate=True
            ),
        )
        self.assertEqual(recovered_withdrawal_address, expected_address)
        self.assertEqual(withdrawal_authorization["type"], "wallet_signature")

        market_maker = payloads["market_maker"]
        auth_response = market_maker["auth_response"]
        self.assertEqual(auth_response["type"], "auth_response")
        self.assertRegex(auth_response["signature"], r"^[0-9a-f]{130}$")

        quote_response = market_maker["quote_response"]
        self.assertEqual(quote_response["type"], "quote")
        quote_data = quote_response["data"]
        self.assertNotIn("=", quote_data)
        self.assertRegex(quote_data, r"^[A-Za-z0-9+/]+$")
        decoded_quote = decode_quote_response(quote_data)
        self.assertTrue(
            decoded_quote.verify_signature(Address.from_evm(expected_address))
        )

    def test_example_entrypoint_prints_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.example.main()

        self.assertEqual(
            json.loads(stdout.getvalue()),
            self.example.build_example_payloads(),
        )


if __name__ == "__main__":
    unittest.main()
