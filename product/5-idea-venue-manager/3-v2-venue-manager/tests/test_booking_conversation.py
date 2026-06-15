from __future__ import annotations

import sys
import unittest
import os
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any


SPACE_ROOT = Path(__file__).resolve().parents[1] / "space"
sys.path.insert(0, str(SPACE_ROOT))

from fastapi.testclient import TestClient

import app as app_module
from floodlight_space.booking_flow import approve_booking_flow
from floodlight_space.conversation_service import process_simulated_message
from floodlight_space.conversation_store import InMemoryConversationStore
from floodlight_space.fixtures import build_bootstrap
from floodlight_space.owner_review import apply_owner_review


def venue_context(scenario: str = "normal") -> dict[str, Any]:
    data = build_bootstrap(scenario)
    return {
        "slots": data["slots"],
        "venues": data["venues"],
        "bookings": data.get("bookings", []),
        "registered_teams": data.get("registered_teams", []),
        "players": data.get("players", []),
        "decision": data["decision"],
    }


def booking(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "intent": "book_slot",
        "customer": {"name": "Aman Sharma", "phone": "+91 98765 43210"},
        "sport": "cricket",
        "date_text": "tomorrow",
        "time_window": "8 AM - 12 PM",
        "venue_preference": "North Field",
        "surface_preference": "Natural grass",
        "players": 12,
        "budget": {"amount": 6000, "currency": "Rs"},
        "missing_fields": [],
        "confidence": 0.95,
    }
    return merge(base, overrides)


def payload(session_id: str, candidate: dict[str, Any] | None, text: str = "Need a ground") -> dict[str, Any]:
    data: dict[str, Any] = {
        "session_id": session_id,
        "message_id": f"{session_id}-msg",
        "sender_phone": "+91 98765 43210",
        "text": text,
        "trace_id": f"{session_id}-trace",
    }
    if candidate is not None:
        data["extraction"] = {"ok": True, "booking": candidate, "fallback_used": False}
    return data


def merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


class BookingConversationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryConversationStore()
        self.context = venue_context()

    def process(self, session_id: str, candidate: dict[str, Any] | None, text: str = "Need a ground") -> dict[str, Any]:
        return process_simulated_message(
            payload=payload(session_id, candidate, text),
            venue_context=self.context,
            store=self.store,
        )

    def review(self, session_id: str, **body: Any) -> dict[str, Any]:
        session = self.store.get_mutable(session_id)
        assert session is not None
        return apply_owner_review(session=session, payload=body, venue_context=self.context)

    def test_complete_request_reaches_owner_review_then_confirmed_simulated(self) -> None:
        session = self.process("complete", booking())

        self.assertEqual(session["status"], "ready_for_owner_review")
        self.assertTrue(session["owner_review_required"])
        self.assertEqual(session["truth_check_initial"]["status"], "available")

        reviewed = self.review("complete", action="approve")

        self.assertEqual(reviewed["terminal_state"], "confirmed_simulated")
        self.assertEqual(reviewed["status"], "confirmed_simulated")
        self.assertEqual(reviewed["send_adapter"]["delivery_state"], "simulated_sent")

    def test_missing_phone_and_time_requests_clarification_without_confirmation_send(self) -> None:
        candidate = booking(customer={"name": "Aman Sharma", "phone": ""}, time_window="", missing_fields=["customer.phone", "time_window"])
        session = self.process("missing", candidate)

        self.assertEqual(session["status"], "needs_player_info")
        self.assertIn("customer.phone", session["truth_check_initial"]["missing_fields"])
        self.assertIn("time_window", session["truth_check_initial"]["missing_fields"])
        self.assertEqual(session["outbound_message"]["kind"], "clarification")
        self.assertEqual(session["outbound_message"]["delivery_state"], "drafted_for_owner")
        self.assertNotEqual(session["send_adapter"]["delivery_state"], "simulated_sent")
        self.assertNotIn("is available", session["outbound_message"]["text"])

    def test_follow_up_supplies_missing_fields_then_confirms(self) -> None:
        first = booking(customer={"name": "Aman Sharma", "phone": ""}, time_window="", missing_fields=["customer.phone", "time_window"])
        self.process("followup", first)

        second = {"customer": {"phone": "+91 98765 43210"}, "time_window": "8 AM - 12 PM", "missing_fields": []}
        session = self.process("followup", second, text="Phone is +91 98765 43210, morning works")
        reviewed = self.review("followup", action="approve")

        self.assertEqual(session["status"], "ready_for_owner_review")
        self.assertEqual(reviewed["terminal_state"], "confirmed_simulated")

    def test_requested_booked_slot_uses_conflict_action_over_model_wording(self) -> None:
        candidate = booking(
            customer={"name": "Rohit Verma", "phone": "+91 90123 45678"},
            venue_preference="North Field",
            time_window="2 PM - 6 PM",
            players=10,
            reply_draft="Confirmed, see you in the afternoon.",
        )
        session = self.process("conflict", candidate)

        self.assertEqual(session["status"], "conflict_possible")
        self.assertEqual(session["outbound_message"]["kind"], "alternative")
        self.assertNotIn("Confirmed", session["outbound_message"]["text"])
        self.assertTrue(session["truth_check_initial"]["conflicts"])

    def test_owner_edits_wrong_slot_and_second_truth_check_is_recomputed(self) -> None:
        candidate = booking(time_window="2 PM - 6 PM")
        self.process("edit-slot", candidate)
        reviewed = self.review("edit-slot", action="edit_extraction", edits={"time_window": "8 AM - 12 PM"}, reason="model chose the wrong slot")

        self.assertEqual(reviewed["truth_check_final"]["flow_state"], "ready_for_owner_review")
        self.assertEqual(reviewed["status"], "ready_for_owner_review")
        diff_fields = [item["field"] for item in reviewed["owner_correction_diff"][0]["diff"]]
        self.assertIn("time_window", diff_fields)

    def test_owner_edits_to_unavailable_slot_blocks_confirmation_send(self) -> None:
        self.process("edit-unavailable", booking())
        reviewed = self.review("edit-unavailable", action="approve", edits={"time_window": "2 PM - 6 PM"})

        self.assertEqual(reviewed["truth_check_final"]["flow_state"], "conflict_possible")
        self.assertIsNone(reviewed["terminal_state"])
        self.assertEqual(reviewed["send_adapter"]["delivery_state"], "not_sent")

    def test_unknown_player_remains_bookable_when_required_fields_exist(self) -> None:
        candidate = booking(customer={"name": "Meera Rao", "phone": "+91 77777 88888"})
        session = self.process("unknown-player", candidate)

        self.assertEqual(session["status"], "ready_for_owner_review")
        self.assertIsNone(session["truth_check_initial"]["matched_player_id"])
        self.assertIsNone(session["truth_check_initial"]["matched_team_id"])

    def test_registered_phone_resolves_team(self) -> None:
        session = self.process("registered", booking())

        self.assertEqual(session["truth_check_initial"]["matched_player_id"], "aman-sharma")
        self.assertEqual(session["truth_check_initial"]["matched_team_id"], "corporate-aman")
        self.assertEqual(session["booking_record"]["registered_team_name"], "Aman Corporate XI")

    def test_model_runtime_blocked_fails_without_send_or_fallback(self) -> None:
        session = self.process("blocked", None)

        self.assertEqual(session["status"], "failed_model")
        self.assertEqual(session["terminal_state"], "failed_model")
        self.assertFalse(session["model_extraction"]["fallback_used"])
        self.assertEqual(session["send_adapter"]["delivery_state"], "not_sent")

    def test_eval_auto_approval_records_owner_review_and_source(self) -> None:
        session = self.process("eval-auto", booking())
        reviewed = self.review("eval-auto", action="approve", approval_source="eval_harness")

        self.assertTrue(session["owner_review_required"])
        self.assertTrue(reviewed["owner_review_required"])
        self.assertEqual(reviewed["approval_source"], "eval_harness")
        self.assertEqual(reviewed["terminal_state"], "confirmed_simulated")

    def test_owner_can_edit_reply_draft_before_approval_send(self) -> None:
        self.process("reply-edit", booking())
        reviewed = self.review("reply-edit", action="approve", reply_draft="Hi Aman, custom owner-approved reply.")

        self.assertEqual(reviewed["terminal_state"], "confirmed_simulated")
        self.assertEqual(reviewed["outbound_message"]["text"], "Hi Aman, custom owner-approved reply.")
        self.assertTrue(reviewed["outbound_message"]["edited_by_owner"])
        self.assertEqual(reviewed["send_adapter"]["message_text"], "Hi Aman, custom owner-approved reply.")

    def test_conflict_then_alternative_followup_can_complete(self) -> None:
        first = booking(time_window="2 PM - 6 PM")
        session = self.process("alternative", first)
        self.assertEqual(session["status"], "conflict_possible")

        followup = {"venue_preference": "South Field", "time_window": "8 AM - 12 PM", "missing_fields": []}
        session = self.process("alternative", followup, text="South Field morning works")
        reviewed = self.review("alternative", action="approve")

        self.assertEqual(session["status"], "ready_for_owner_review")
        self.assertEqual(reviewed["terminal_state"], "confirmed_simulated")


class BookingConversationRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved_env = {
            key: os.environ.get(key)
            for key in [
                "FLOODLIGHT_ADAPTER_TOKEN",
                "FLOODLIGHT_ALLOWED_PHONES",
                "FLOODLIGHT_LIVE_ADAPTER_MODE",
            ]
        }
        app_module.CONVERSATION_STORE.reset()
        self.client = TestClient(app_module.app)

    def tearDown(self) -> None:
        for key, value in self.saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def baileys_payload(self, **overrides: Any) -> dict[str, Any]:
        data: dict[str, Any] = {
            "adapter": "baileys",
            "message_id": "baileys-msg-001",
            "chat_jid": "919876543210@s.whatsapp.net",
            "sender_jid": "919876543210@s.whatsapp.net",
            "sender_phone": "+91 98765 43210",
            "received_at": "2026-06-14T00:00:00Z",
            "text": "Need North Field tomorrow morning for 12 players",
            "trace_id": "baileys-route-test",
            "scenario": "normal",
            "provider_metadata": {"message_type": "conversation", "source": "baileys"},
            "extraction": {"ok": True, "booking": booking(), "fallback_used": False},
        }
        return merge(data, overrides)

    def configure_baileys_route(self, *, mode: str = "fixture_dry_run", allowed: str = "+91 98765 43210") -> dict[str, str]:
        os.environ["FLOODLIGHT_ADAPTER_TOKEN"] = "test-adapter-token"
        os.environ["FLOODLIGHT_ALLOWED_PHONES"] = allowed
        os.environ["FLOODLIGHT_LIVE_ADAPTER_MODE"] = mode
        return {"X-Floodlight-Adapter-Token": "test-adapter-token"}

    def test_player_message_endpoint_is_retired_without_calling_model(self) -> None:
        response = self.client.post("/api/player-message", json={"trace_id": "retired-route"})

        self.assertEqual(response.status_code, 410)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"], "endpoint_retired")
        self.assertEqual(body["replacement"], "/api/whatsapp/simulated-message")

    def test_legacy_booking_decision_refuses_nonconfirmable_states(self) -> None:
        for state in ["model_blocked", "needs_player_info", "slot_clarification", "conflict_possible"]:
            with self.subTest(state=state):
                flow = {
                    "trace_id": f"{state}-trace",
                    "flow_state": state,
                    "booking_record": {"status": state},
                    "player_message": {"delivery_state": "drafted_for_owner", "text": "draft"},
                    "agent_trace": [],
                }
                result = approve_booking_flow(flow, decision="approve")

                self.assertNotEqual(result["booking_record"]["status"], "confirmed_simulated")
                self.assertEqual(result["player_message"]["delivery_state"], "not_sent")
                self.assertEqual(result["player_message"]["reason"], f"cannot_confirm_{state}")

    def test_trace_endpoint_includes_raw_message_runtime_axes_and_failure_reason(self) -> None:
        response = self.client.post(
            "/api/whatsapp/simulated-message",
            json={
                "session_id": "trace-route",
                "message_id": "trace-route-1",
                "sender_phone": "+91 98765 43210",
                "text": "Need North Field tomorrow morning",
                "extraction": {"ok": True, "booking": booking(), "fallback_used": False},
            },
        )
        self.assertEqual(response.status_code, 200)

        trace_response = self.client.get("/api/conversations/trace-route/trace")
        self.assertEqual(trace_response.status_code, 200)
        trace = trace_response.json()["trace"]

        self.assertEqual(trace["raw_message"], "Need North Field tomorrow morning")
        self.assertIn("runtime_axes", trace)
        self.assertEqual(trace["runtime_axes"]["model_runtime"], "fixture_model_shaped_input")
        self.assertIn("failure_reason", trace)
        self.assertIsNone(trace["failure_reason"])

    def test_extract_booking_rejects_malformed_ok_true_modal_shape_without_network(self) -> None:
        original_urlopen = urllib.request.urlopen
        original_base = os.environ.get("APP_MODAL_BASE_URL")
        original_token = os.environ.get("APP_MODAL_AUTH_TOKEN")
        os.environ["APP_MODAL_BASE_URL"] = "https://modal.invalid/extract"
        os.environ["APP_MODAL_AUTH_TOKEN"] = "test-token"

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
                return None

            def read(self) -> bytes:
                return (
                    b'{"ok": true, "trace_id": "bad-schema", "booking": {"customer": "bad"}, '
                    b'"latency_ms": 1234, "timing_ms": {"load_llm_end": 1000}, "raw_text": "{\\"customer\\": \\"bad\\"}"}'
                )

        def fake_urlopen(request: object, timeout: float) -> FakeResponse:
            return FakeResponse()

        urllib.request.urlopen = fake_urlopen
        try:
            response = self.client.post("/api/extract-booking", json={"trace_id": "bad-schema", "message": "bad"})
        finally:
            urllib.request.urlopen = original_urlopen
            if original_base is None:
                os.environ.pop("APP_MODAL_BASE_URL", None)
            else:
                os.environ["APP_MODAL_BASE_URL"] = original_base
            if original_token is None:
                os.environ.pop("APP_MODAL_AUTH_TOKEN", None)
            else:
                os.environ["APP_MODAL_AUTH_TOKEN"] = original_token

        self.assertEqual(response.status_code, 502)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertEqual(body["blocker"], "Modal returned ok=true but booking schema was invalid.")
        self.assertIn("customer_not_object", body["validation"]["errors"])
        self.assertEqual(body["latency_ms"], 1234)
        self.assertEqual(body["timing_ms"]["load_llm_end"], 1000)
        self.assertEqual(body["raw_text"], '{"customer": "bad"}')

    def test_bootstrap_loads_state_snapshot_world(self) -> None:
        response = self.client.get("/api/bootstrap")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["state_snapshot"]["schema_version"], "state_snapshot.v1")
        self.assertEqual(body["state_snapshot"]["snapshot_id"], "floodlight-demo-world-2026-06-15")
        self.assertGreaterEqual(len(body["state_snapshot"]["conversation_threads"]), 10)
        self.assertEqual(len(body["requests"]), 10)
        self.assertEqual(body["runtime"]["pending_count"], 9)

    def test_reload_demo_clears_temporary_conversations_and_returns_snapshot(self) -> None:
        created = self.client.post(
            "/api/whatsapp/simulated-message",
            json=payload("reset-route", booking(), "Need North Field tomorrow morning"),
        )
        self.assertEqual(created.status_code, 200)
        self.assertIsNotNone(app_module.CONVERSATION_STORE.get("reset-route"))

        response = self.client.post("/api/reload-demo", json={})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["demo_reset"]["state"], "reloaded")
        self.assertTrue(body["demo_reset"]["temporary_sessions_cleared"])
        self.assertEqual(body["state_snapshot"]["snapshot_id"], "floodlight-demo-world-2026-06-15")
        self.assertIsNone(app_module.CONVERSATION_STORE.get("reset-route"))

    def test_simulated_model_message_uses_server_extractor_without_baileys(self) -> None:
        original = app_module.call_booking_extractor
        calls: list[dict[str, Any]] = []

        def fake_extractor(**kwargs: Any) -> dict[str, Any]:
            calls.append(kwargs)
            return {
                "ok": True,
                "trace_id": kwargs["trace_id"],
                "model_id": "nvidia/Nemotron-Cascade-2-30B-A3B",
                "backend": "modal_http",
                "fallback_used": False,
                "booking": booking(customer={"name": "Snapshot Sim", "phone": "+91 98765 43210"}),
                "validation": {"valid": True, "errors": []},
            }

        app_module.call_booking_extractor = fake_extractor
        try:
            response = self.client.post(
                "/api/whatsapp/simulated-model-message",
                json={
                    "session_id": "sim-model-route",
                    "message_id": "sim-model-route-1",
                    "sender_phone": "+91 98765 43210",
                    "text": "Need North Field tomorrow morning for 12 players",
                    "extraction": {"ok": True, "booking": booking(customer={"name": "Client Spoof", "phone": "+91 98765 43210"})},
                },
            )
        finally:
            app_module.call_booking_extractor = original

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["message"], "Need North Field tomorrow morning for 12 players")
        body = response.json()
        self.assertEqual(body["proof_boundary"]["adapter"], "simulator")
        self.assertFalse(body["proof_boundary"]["live_whatsapp_inbound_proven"])
        conversation = body["conversation"]
        self.assertEqual(conversation["candidate_extraction"]["customer"]["name"], "Snapshot Sim")
        self.assertNotEqual(conversation["candidate_extraction"]["customer"]["name"], "Client Spoof")
        self.assertEqual(conversation["model_extraction"]["backend"], "modal_http")

    def test_baileys_message_rejects_missing_or_wrong_adapter_token(self) -> None:
        os.environ["FLOODLIGHT_ADAPTER_TOKEN"] = "test-adapter-token"

        missing = self.client.post("/api/whatsapp/baileys-message", json=self.baileys_payload())
        wrong = self.client.post(
            "/api/whatsapp/baileys-message",
            json=self.baileys_payload(),
            headers={"X-Floodlight-Adapter-Token": "wrong-token"},
        )

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(missing.json()["error"], "adapter_token_missing_or_invalid")

    def test_baileys_message_rejects_disallowed_sender_before_extraction(self) -> None:
        headers = self.configure_baileys_route(allowed="+91 11111 11111")

        response = self.client.post("/api/whatsapp/baileys-message", json=self.baileys_payload(), headers=headers)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "sender_not_allowed")
        self.assertIsNone(app_module.CONVERSATION_STORE.get("wa-919876543210"))

    def test_baileys_message_rejects_invalid_payload(self) -> None:
        headers = self.configure_baileys_route()

        unsupported = self.client.post(
            "/api/whatsapp/baileys-message",
            json=self.baileys_payload(adapter="simulator"),
            headers=headers,
        )
        empty_text = self.client.post(
            "/api/whatsapp/baileys-message",
            json=self.baileys_payload(text="   "),
            headers=headers,
        )

        self.assertEqual(unsupported.status_code, 400)
        self.assertEqual(unsupported.json()["error"], "unsupported_adapter")
        self.assertEqual(empty_text.status_code, 400)
        self.assertEqual(empty_text.json()["error"], "empty_text")

    def test_baileys_fixture_dry_run_reaches_owner_review_without_live_send(self) -> None:
        headers = self.configure_baileys_route()

        response = self.client.post("/api/whatsapp/baileys-message", json=self.baileys_payload(), headers=headers)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["proof_boundary"]["live_whatsapp_inbound_proven"])
        self.assertFalse(body["proof_boundary"]["live_outbound_proven"])
        conversation = body["conversation"]
        self.assertEqual(conversation["session_id"], "wa-919876543210")
        self.assertEqual(conversation["status"], "ready_for_owner_review")
        self.assertTrue(conversation["owner_review_required"])
        self.assertEqual(conversation["outbound_message"]["delivery_state"], "drafted_for_owner")
        self.assertEqual(conversation["send_adapter"]["adapter"], "simulator")
        self.assertEqual(conversation["send_adapter"]["delivery_state"], "not_sent")

    def test_baileys_allowlist_can_match_phone_derived_from_jid(self) -> None:
        headers = self.configure_baileys_route(allowed="919876543210")

        response = self.client.post(
            "/api/whatsapp/baileys-message",
            json=self.baileys_payload(sender_phone=""),
            headers=headers,
        )

        self.assertEqual(response.status_code, 200)
        conversation = response.json()["conversation"]
        self.assertEqual(conversation["player_phone"], "+919876543210")
        self.assertEqual(conversation["session_id"], "wa-919876543210")

    def test_baileys_modal_mode_uses_server_extractor_and_ignores_client_extraction(self) -> None:
        headers = self.configure_baileys_route(mode="modal")
        original = app_module.call_booking_extractor
        calls: list[dict[str, Any]] = []

        def fake_extractor(**kwargs: Any) -> dict[str, Any]:
            calls.append(kwargs)
            return {
                "ok": True,
                "trace_id": kwargs["trace_id"],
                "model_id": "nvidia/Nemotron-Cascade-2-30B-A3B",
                "backend": "modal_http",
                "fallback_used": False,
                "booking": booking(customer={"name": "Server Extracted", "phone": "+91 98765 43210"}),
                "validation": {"valid": True, "errors": []},
            }

        app_module.call_booking_extractor = fake_extractor
        try:
            response = self.client.post(
                "/api/whatsapp/baileys-message",
                json=self.baileys_payload(extraction={"ok": True, "booking": booking(customer={"name": "Client Spoof", "phone": "+91 98765 43210"})}),
                headers=headers,
            )
        finally:
            app_module.call_booking_extractor = original

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["message"], "Need North Field tomorrow morning for 12 players")
        conversation = response.json()["conversation"]
        self.assertEqual(conversation["candidate_extraction"]["customer"]["name"], "Server Extracted")
        self.assertNotEqual(conversation["candidate_extraction"]["customer"]["name"], "Client Spoof")
        self.assertEqual(conversation["model_extraction"]["backend"], "modal_http")
        self.assertFalse(conversation["model_extraction"]["fallback_used"])

    def test_baileys_modal_mode_blocker_returns_502_without_fallback_or_send(self) -> None:
        headers = self.configure_baileys_route(mode="modal")
        original = app_module.call_booking_extractor

        def fake_blocked(**kwargs: Any) -> dict[str, Any]:
            return {
                "ok": False,
                "trace_id": kwargs["trace_id"],
                "model_id": "nvidia/Nemotron-Cascade-2-30B-A3B",
                "backend": "modal_http",
                "fallback_used": False,
                "booking": None,
                "blocker": "stubbed_modal_blocker",
                "validation": {"valid": False, "errors": ["stubbed_modal_blocker"]},
            }

        app_module.call_booking_extractor = fake_blocked
        try:
            response = self.client.post("/api/whatsapp/baileys-message", json=self.baileys_payload(), headers=headers)
        finally:
            app_module.call_booking_extractor = original

        self.assertEqual(response.status_code, 502)
        body = response.json()
        self.assertFalse(body["ok"])
        conversation = body["conversation"]
        self.assertEqual(conversation["status"], "failed_model")
        self.assertFalse(conversation["model_extraction"]["fallback_used"])
        self.assertEqual(conversation["send_adapter"]["delivery_state"], "not_sent")

    def test_simulator_route_still_processes_fixture_booking_with_adapter_env_configured(self) -> None:
        self.configure_baileys_route()

        response = self.client.post(
            "/api/whatsapp/simulated-message",
            json=payload("sim-regression", booking(), "Need North Field tomorrow morning"),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["conversation"]["status"], "ready_for_owner_review")
        self.assertEqual(body["conversation"]["session_id"], "sim-regression")


if __name__ == "__main__":
    unittest.main()
