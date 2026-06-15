from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "space" / "app.py"
CASES_PATH = ROOT / "eval" / "cases" / "tiny_aya_seed_cases.jsonl"


def load_app_module():
    spec = importlib.util.spec_from_file_location("vcw_v1_space_app", APP_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_cases() -> list[dict]:
    return [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_seed_cases_are_loadable() -> None:
    cases = read_cases()
    assert {case["case_id"] for case in cases} == {
        "unrelated_antique_transcript",
        "hinglish_pricing_callback",
        "actual_order_status_allowed",
    }


def test_prompt_contract_removes_support_metadata_slots() -> None:
    app = load_app_module()
    packet = {"site_id": "metime-to", "brand_name": "metime.to"}
    messages = app.tiny_aya_messages(packet, "Namaste, pricing details chahiye.", "hinglish", "hi-IN")
    joined = "\n".join(message["content"] for message in messages)

    assert "Do not act as customer support" in joined
    assert "intent" not in joined
    assert "missing_fields" not in joined
    assert "message_en" in joined
    assert "needs_edit" in joined


def test_guardrail_catches_hallucinated_support_fields_from_bad_trace() -> None:
    app = load_app_module()
    transcript = (
        "\u0910\u0938\u0940 \u0915\u094b\u0908 \u0935\u0948\u0936\u094d\u0935\u093f\u0915 "
        "\u092a\u0930\u093f\u092d\u093e\u0937\u093e \u0928\u0939\u0940\u0902 \u0939\u0948 "
        "\u091c\u093f\u0938\u0915\u0947 \u0932\u093f\u090f \u0928\u093f\u0930\u094d\u092e\u093f\u0924 "
        "\u0938\u092e\u093e\u0928 \u090f\u0902\u091f\u0940\u0915 \u0939\u094b\u0924\u0947 \u0939\u0948\u0902"
    )
    raw = json.dumps(
        {
            "message_en": "Could you please provide your order ID and delivery address so we can assist you better?",
            "confidence": 0.82,
            "needs_edit": False,
            "notes": [],
        }
    )

    parsed = app.parse_model_json(raw, transcript)

    assert parsed["needs_edit"] is True
    assert "draft_mentions_support_fields_not_present_in_transcript" in parsed["notes"]
    assert any(flag.startswith("unsupported_support_fields:") for flag in parsed["guardrail_flags"])
    flagged = ",".join(parsed["guardrail_flags"])
    assert "order" in flagged
    assert "delivery" in flagged
    assert "address" in flagged


def test_parser_recovers_nested_output_schema_and_flags_new_hosted_failure() -> None:
    app = load_app_module()
    transcript = (
        "\u0910\u0938\u0940 \u0915\u094b\u0908 \u0935\u0948\u0936\u094d\u0935\u093f\u0915 "
        "\u092a\u0930\u093f\u092d\u093e\u0937\u093e \u0928\u0939\u0940\u0902 \u0939\u0948 "
        "\u091c\u093f\u0938\u0915\u0947 \u0932\u093f\u090f \u0928\u093f\u0930\u094d\u092e\u093f\u0924 "
        "\u0938\u092e\u093e\u0928 \u090f\u0902\u091f\u0940\u0915 \u0939\u094b\u0924\u0947 \u0939\u0948\u0902"
    )
    raw = json.dumps(
        {
            "asr_transcript": "Hello, I need to book a Metime appointment. Please call me at 9876543210.",
            "output_schema": {
                "message_en": "Hello, I need to book a Metime appointment. Please call me at 9876543210.",
                "confidence": 0.95,
                "needs_edit": False,
                "notes": [],
            },
        }
    )

    parsed = app.parse_model_json(raw, transcript)

    assert parsed["needs_edit"] is True
    flagged = ",".join(parsed["guardrail_flags"])
    assert "booking" in flagged
    assert "phone" in flagged
    assert "missing_preservation_cues:antique" in flagged


def test_guardrail_allows_support_terms_when_source_contains_them() -> None:
    app = load_app_module()
    transcript = "Mera order aaj delivery hona tha, please delivery status bata dijiye."
    raw = json.dumps(
        {
            "message_en": "My order was supposed to be delivered today. Please share the delivery status.",
            "confidence": 0.79,
            "needs_edit": False,
            "notes": [],
        }
    )

    parsed = app.parse_model_json(raw, transcript)

    assert parsed["needs_edit"] is False
    assert parsed["guardrail_flags"] == []


def test_runtime_controls_gate_test_only_options(monkeypatch) -> None:
    app = load_app_module()
    monkeypatch.setenv("VCW_MODEL_MODE", "real")
    monkeypatch.setenv("VCW_MODEL_RUNTIME", "hf_space")
    monkeypatch.delenv("VCW_ALLOW_RUNTIME_SWITCH", raising=False)

    controls = app.runtime_controls(app.selected_model_runtime())

    assert controls["selected"] == "hf_space"
    assert controls["allow_switch"] is False
    enabled = {option["value"]: option["enabled"] for option in controls["options"]}
    assert enabled == {"hf_space": True, "hf_personal_space": False, "modal": False}


def test_runtime_override_requires_switch(monkeypatch) -> None:
    app = load_app_module()
    monkeypatch.setenv("VCW_MODEL_MODE", "real")
    monkeypatch.setenv("VCW_MODEL_RUNTIME", "hf_space")
    monkeypatch.delenv("VCW_ALLOW_RUNTIME_SWITCH", raising=False)

    try:
        app.selected_model_runtime("modal")
    except app.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("modal override should be rejected when switch is disabled")

    monkeypatch.setenv("VCW_ALLOW_RUNTIME_SWITCH", "1")
    assert app.selected_model_runtime("modal") == "modal"
    assert app.selected_model_runtime("hf_personal_space") == "hf_personal_space"


def test_local_deterministic_selected_hf_space_is_unavailable(monkeypatch) -> None:
    app = load_app_module()
    monkeypatch.setenv("VCW_MODEL_MODE", "deterministic")
    monkeypatch.setenv("VCW_MODEL_RUNTIME", "hf_space")
    monkeypatch.setenv("VCW_ALLOW_RUNTIME_SWITCH", "1")

    assert app.selected_model_runtime() == "hf_space"
    assert app.selected_model_runtime("hf_space") == "hf_space"
    assert app.runtime_availability("hf_space")["available"] is False
    controls = app.runtime_controls(app.selected_model_runtime())
    hf_space = next(option for option in controls["options"] if option["value"] == "hf_space")
    assert hf_space["enabled"] is True
    assert hf_space["available"] is False
    assert "local deterministic mode" in hf_space["disabled_reason"]
    assert app.selected_model_runtime("modal") == "modal"


def test_runtime_unavailable_response_does_not_mark_fallback(monkeypatch) -> None:
    app = load_app_module()
    monkeypatch.setenv("VCW_MODEL_MODE", "deterministic")
    packet = app.load_packet()
    payload = {"speech_mode": "hinglish", "model_runtime": "hf_space"}

    response = app.runtime_unavailable_response(packet, payload, "hf_space", text_only=False)
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 424
    assert "deterministic output was not substituted" in body["error"]
    assert body["trace"]["model_runtime"] == "hf_space"
    assert body["trace"]["fallback_used"] is False
    assert body["trace"]["fallback_reason"] is None


def test_local_env_loader_fills_missing_modal_keys_without_overriding(monkeypatch, tmp_path) -> None:
    app = load_app_module()
    env_path = tmp_path / ".env.modal.local"
    env_path.write_text(
        "\n".join(
            [
                "APP_MODAL_BASE_URL=https://example-modal.invalid/process",
                "APP_MODAL_AUTH_TOKEN=local-secret",
                "APP_MODAL_TIMEOUT_SECONDS=42",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("APP_MODAL_BASE_URL", "https://already-set.invalid/process")
    monkeypatch.delenv("APP_MODAL_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("APP_MODAL_TIMEOUT_SECONDS", raising=False)

    loaded = app.load_local_env_files((env_path,))

    assert loaded == [str(env_path)]
    assert app.modal_base_url() == "https://already-set.invalid/process"
    assert app.modal_auth_token() == "local-secret"
    assert app.modal_timeout_seconds() == 42
