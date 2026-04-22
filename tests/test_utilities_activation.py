"""Tests for utilities.activation."""

from __future__ import annotations

import io
import json
from unittest.mock import patch, MagicMock
from urllib import error as urlerror

import pytest

from utilities import activation


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in [
        "ACTIVATION_API_URL",
        "ACTIVATION_HTTP_TIMEOUT_SECONDS",
        "ACTIVATION_HTTP_RETRIES",
    ]:
        monkeypatch.delenv(var, raising=False)


class TestApiConfigured:
    def test_not_configured_by_default(self):
        assert activation.activation_api_configured() is False

    def test_configured_when_env_set(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://example.com/api")
        assert activation.activation_api_configured() is True

    def test_whitespace_url_is_not_configured(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "   ")
        assert activation.activation_api_configured() is False


class TestIntEnv:
    def test_default_when_missing(self):
        assert activation._get_int_env("NOPE", 42) == 42

    def test_parses_int(self, monkeypatch):
        monkeypatch.setenv("FOO", "7")
        assert activation._get_int_env("FOO", 1) == 7

    def test_invalid_returns_default(self, monkeypatch):
        monkeypatch.setenv("FOO", "banana")
        assert activation._get_int_env("FOO", 3) == 3

    def test_below_minimum_returns_default(self, monkeypatch):
        monkeypatch.setenv("FOO", "-5")
        assert activation._get_int_env("FOO", 10, minimum=0) == 10


class TestBuildPayload:
    def test_contains_required_fields(self, monkeypatch):
        monkeypatch.setattr(activation, "get_machine_id", lambda: "HWID123")
        monkeypatch.setattr(activation, "get_country", lambda: "US")
        payload = activation._build_payload("MYCODE")
        assert payload["activation_code"] == "MYCODE"
        assert payload["hwid"] == "HWID123"
        assert payload["country"] == "US"
        assert "app_version" in payload
        assert "build_number" in payload
        assert "platform" in payload
        assert "timestamp_utc" in payload


class TestRedeemActivationCode:
    def test_empty_code_rejected(self):
        ok, data, msg = activation.redeem_activation_code("")
        assert ok is False
        assert data is None
        assert "empty" in msg.lower()

    def test_no_api_url_configured(self):
        ok, data, msg = activation.redeem_activation_code("CODE")
        assert ok is False
        assert "not configured" in msg.lower()

    def test_success_returns_license_key(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")
        monkeypatch.setattr(activation, "get_machine_id", lambda: "HWID")
        monkeypatch.setattr(activation, "get_country", lambda: "US")

        response_body = json.dumps(
            {"license_key": "my-license", "message": "All good"}
        ).encode("utf-8")

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return response_body

        with patch.object(activation.urlrequest, "urlopen", return_value=_FakeResponse()):
            ok, data, msg = activation.redeem_activation_code("CODE")

        assert ok is True
        assert data == {"license_key": "my-license", "message": "All good"}
        assert msg == "All good"

    def test_missing_license_key_in_response_is_failure(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")

        response_body = json.dumps({"message": "Bad request"}).encode("utf-8")

        class _FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return response_body

        with patch.object(activation.urlrequest, "urlopen", return_value=_FakeResponse()):
            ok, data, msg = activation.redeem_activation_code("CODE")

        assert ok is False
        assert data is None
        assert msg == "Bad request"

    def test_http_error_propagates_api_message(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")

        err = urlerror.HTTPError(
            url="https://x.invalid/api",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=io.BytesIO(json.dumps({"message": "Nope"}).encode()),
        )

        with patch.object(activation.urlrequest, "urlopen", side_effect=err):
            ok, _data, msg = activation.redeem_activation_code("CODE")

        assert ok is False
        assert msg == "Nope"

    def test_http_error_falls_back_to_status_code(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")

        err = urlerror.HTTPError(
            url="https://x.invalid/api",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=io.BytesIO(b""),
        )
        with patch.object(activation.urlrequest, "urlopen", side_effect=err):
            ok, _data, msg = activation.redeem_activation_code("CODE")
        assert ok is False
        assert "HTTP 500" in msg

    def test_url_error_reports_network_issue(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")

        with patch.object(
            activation.urlrequest,
            "urlopen",
            side_effect=urlerror.URLError("no route"),
        ):
            ok, _data, msg = activation.redeem_activation_code("CODE")
        assert ok is False
        assert "Could not reach" in msg

    def test_retries_before_giving_up(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "2")
        monkeypatch.setattr(activation.time, "sleep", lambda *_a, **_k: None)

        mock_open = MagicMock(side_effect=urlerror.URLError("down"))
        with patch.object(activation.urlrequest, "urlopen", mock_open):
            ok, _data, _msg = activation.redeem_activation_code("CODE")

        assert ok is False
        # retries=2 → 3 attempts total
        assert mock_open.call_count == 3

    def test_invalid_json_response(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")

        class _FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b"<<not json>>"

        with patch.object(activation.urlrequest, "urlopen", return_value=_FakeResponse()):
            ok, _data, msg = activation.redeem_activation_code("CODE")
        assert ok is False
        assert "invalid JSON" in msg

    def test_empty_response_body_treated_as_missing_license_key(self, monkeypatch):
        monkeypatch.setenv("ACTIVATION_API_URL", "https://x.invalid/api")
        monkeypatch.setenv("ACTIVATION_HTTP_RETRIES", "0")

        class _FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b"   "

        with patch.object(activation.urlrequest, "urlopen", return_value=_FakeResponse()):
            ok, _data, msg = activation.redeem_activation_code("CODE")
        assert ok is False
        assert "license_key" in msg
