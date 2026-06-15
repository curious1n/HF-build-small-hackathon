from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODAL_ROOT = ROOT / "modal"
sys.path.insert(0, str(MODAL_ROOT))

import modal_venue_manager_cascade as extractor  # noqa: E402


SAVED_FAILURE_RAW_EXCERPT = """
We need to extract details.

players: 12

budget: {amount: 6000, currency: "Rs"} (they said around Rs 6000). Use amount 6000, currency "Rs".

Now produce JSON.

{
  "intent": "book_slot",
  "customer": {
    "name": "Aman Sharma",
    "phone": "+91 98765 43210"
  },
  "sport": "cricket",
  "date_text": "tomorrow",
  "time_window": "8 AM - 12 PM",
  "venue_preference": "North Field",
  "surface_preference": "Natural grass",
  "players": 12,
  "budget": {
    "amount": 6000,
    "currency": "Rs"
  },
  "booking_status": "ready_for_owner_review",
  "missing_fields": [],
  "confidence": 0.98,
  "owner_next_action": "Review the booking request for North Field morning slot, confirm availability and rate, then approve
"""


def valid_booking() -> dict[str, object]:
    return {
        "intent": "book_slot",
        "customer": {"name": "Aman Sharma", "phone": "+91 98765 43210"},
        "sport": "cricket",
        "date_text": "tomorrow",
        "time_window": "8 AM - 12 PM",
        "venue_preference": "North Field",
        "surface_preference": "Natural grass",
        "players": 12,
        "budget": {"amount": 6000, "currency": "Rs"},
        "booking_status": "ready_for_owner_review",
        "missing_fields": [],
        "confidence": 0.98,
        "owner_next_action": "Review the request.",
        "reply_draft": "Hi Aman, North Field is available tomorrow morning.",
    }


class ModalExtractorContractTests(unittest.TestCase):
    def test_saved_failure_raw_text_rejects_inline_pseudo_object(self) -> None:
        raw_text = SAVED_FAILURE_RAW_EXCERPT

        self.assertIn('{amount: 6000, currency: "Rs"}', raw_text)
        with self.assertRaisesRegex(ValueError, "valid_booking_json_object"):
            extractor._extract_json_object(raw_text)

    def test_extract_json_skips_prose_pseudo_object_for_later_booking_object(self) -> None:
        booking = valid_booking()
        raw_text = (
            'Reasoning: budget looked like {amount: 6000, currency: "Rs"}.\n'
            "Final answer:\n"
            f"{json.dumps(booking)}"
        )

        extracted = extractor._extract_json_object(raw_text)

        self.assertEqual(json.loads(extracted), booking)

    def test_extract_json_accepts_fenced_booking_object(self) -> None:
        booking = valid_booking()
        raw_text = f"```json\n{json.dumps(booking)}\n```"

        extracted = extractor._extract_json_object(raw_text)

        self.assertEqual(json.loads(extracted), booking)


if __name__ == "__main__":
    unittest.main()
