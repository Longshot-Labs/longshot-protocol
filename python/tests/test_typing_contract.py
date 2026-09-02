from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


VALID_PROGRAM = """
from longshot_protocol import (
    ConfirmPositionQuery,
    CreateRfqRequest,
    MarketLookupQuery,
    MarketType,
    ProfitCapConfigResponse,
    ProfitCapOverrideResponse,
    SignedOrderJson,
)

order = SignedOrderJson(
    user="0x0000000000000000000000000000000000000000",
    wager_micros=1,
    min_odds=2.0,
    legs=[],
    nonce=1,
    expires_at_ms=1,
    shield_on=False,
    signature="signature",
)
request = CreateRfqRequest(order=order, use_app_tokens=False)
typed_order: SignedOrderJson = request.order
typed_flag: bool = request.use_app_tokens
MarketLookupQuery(asset="BTC", duration_secs=300, window_start_ms=1)
ConfirmPositionQuery(position_id="position", accept=True)
ProfitCapConfigResponse(
    default_max_profit_micros=75_000_000,
    overrides=[
        ProfitCapOverrideResponse(
            market_type=MarketType.Sports,
            max_profit_micros=500_000_000,
        )
    ],
)
"""

INVALID_PROGRAM = """
from longshot_protocol import (
    ConfirmPositionQuery,
    CreateRfqRequest,
    MarketLookupQuery,
    ProfitCapConfigResponse,
    SignedOrderJson,
)

order = SignedOrderJson(
    user="0x0000000000000000000000000000000000000000",
    wager_micros=1,
    min_odds=2.0,
    legs=[],
    nonce=1,
    expires_at_ms=1,
    shield_on=False,
    signature="signature",
)
CreateRfqRequest()
CreateRfqRequest(order=order)
CreateRfqRequest(use_app_tokens=False)
CreateRfqRequest(order=None, use_app_tokens=False)
MarketLookupQuery()
MarketLookupQuery(asset="BTC", duration_secs="300", window_start_ms=1)
ConfirmPositionQuery(position_id="position", accept="true")
ProfitCapConfigResponse()
"""

UUID_ID_FACTORY_PROGRAM = """
from uuid import UUID

from longshot_protocol import RequestId

new_id: RequestId = RequestId.new()
uuid_id: RequestId = RequestId.from_uuid(UUID(int=0))
nil_id: RequestId = RequestId.nil()
bytes_id: RequestId = RequestId.from_bytes(bytes(16))
string_id: RequestId = RequestId.from_string("00000000-0000-0000-0000-000000000000")
"""

SUBCLASS_DECODER_PROGRAM = """
from longshot_protocol import QuoteResultStatus, ServerMessage

message: ServerMessage = ServerMessage.from_dict(
    {"type": "ping", "timestamp": 1}
)
status: QuoteResultStatus = QuoteResultStatus.from_json("filled")
"""


class TypingContractTests(unittest.TestCase):
    def _mypy(self, source: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.py"
            path.write_text(textwrap.dedent(source))
            return subprocess.run(
                [sys.executable, "-m", "mypy", "--strict", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_rust_required_fields_are_required_by_static_typing(self) -> None:
        valid = self._mypy(VALID_PROGRAM)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

        invalid = self._mypy(INVALID_PROGRAM)
        output = invalid.stdout + invalid.stderr
        self.assertNotEqual(invalid.returncode, 0, output)
        self.assertIn('Missing named argument "order" for "CreateRfqRequest"', output)
        self.assertIn(
            'Missing named argument "use_app_tokens" for "CreateRfqRequest"', output
        )
        self.assertIn(
            'Argument "order" to "CreateRfqRequest" has incompatible type "None"',
            output,
        )
        self.assertIn(
            'Missing named argument "asset" for "MarketLookupQuery"', output
        )
        self.assertIn(
            'Argument "duration_secs" to "MarketLookupQuery" has incompatible type "str"',
            output,
        )
        self.assertIn(
            'Argument "accept" to "ConfirmPositionQuery" has incompatible type "str"',
            output,
        )
        self.assertIn(
            'Missing named argument "default_max_profit_micros" for "ProfitCapConfigResponse"',
            output,
        )

    def test_uuid_id_factories_preserve_subclass_typing(self) -> None:
        result = self._mypy(UUID_ID_FACTORY_PROGRAM)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_decoders_preserve_subclass_typing(self) -> None:
        result = self._mypy(SUBCLASS_DECODER_PROGRAM)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
