"""
Unit tests for utilities.license.

Covers:
- License key generation and validation (signature, payload, wildcard, expiration).
- Filename parsing and directory scanning.
- Machine ID and country detection fallbacks.
- File location / migration helpers.
- load_and_validate_license() and check_license() end-to-end flows.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime
from pathlib import Path

import pytest

from utilities import license as lic


# ---------------------------------------------------------------------------
# generate_license_key / validate_license_key
# ---------------------------------------------------------------------------
class TestGenerateValidateLicenseKey:
    def test_roundtrip_basic(self):
        key = lic.generate_license_key("alice@example.com", "US", "HWID-ABC", 0)
        ok, data, err = lic.validate_license_key(key)
        assert ok is True
        assert err is None
        assert data == {
            "email": "alice@example.com",
            "country": "US",
            "hwid": "HWID-ABC",
            "expiration": "0",
        }

    def test_wildcard_hwid_flag_overrides_hwid(self):
        key = lic.generate_license_key(
            "bob@hfmdd.de", "DE", "ignored-hwid", 0, use_wildcard_hwid=True
        )
        ok, data, err = lic.validate_license_key(key)
        assert ok is True
        assert data["hwid"] == lic.WILDCARD_HWID_HFMDD

    def test_invalid_base64(self):
        ok, data, err = lic.validate_license_key("not base64 #$@!")
        assert ok is False
        assert data is None
        assert err and "License validation failed" in err

    def test_malformed_payload_wrong_part_count(self):
        payload = base64.b64encode(b"only|three|parts").decode()
        ok, data, err = lic.validate_license_key(payload)
        assert ok is False
        assert err == "Invalid license key format"

    def test_tampered_signature_rejected(self):
        key = lic.generate_license_key("alice@example.com", "US", "HWID", 0)
        decoded = base64.b64decode(key).decode()
        parts = decoded.split("|")
        parts[-1] = "deadbeef" * 8
        tampered = base64.b64encode("|".join(parts).encode()).decode()
        ok, data, err = lic.validate_license_key(tampered)
        assert ok is False
        assert err == "Invalid license key signature"

    def test_signature_is_hmac_sha256_of_payload(self):
        """Lock down the exact signing scheme so a silent change would fail."""
        key = lic.generate_license_key("x@y.z", "GB", "HWID", 7)
        decoded = base64.b64decode(key).decode()
        email, country, hwid, exp, sig = decoded.split("|")
        expected_sig = hmac.new(
            lic.LICENSE_SECRET,
            f"{email}|{country}|{hwid}|{exp}".encode(),
            hashlib.sha256,
        ).hexdigest()
        assert sig == expected_sig


# ---------------------------------------------------------------------------
# Timestamped filename helpers
# ---------------------------------------------------------------------------
class TestTimestampedFilenames:
    def test_parse_valid_filename(self):
        parsed = lic._parse_timestamped_license_filename(
            "license-20260101T120000Z-CLT0001.key"
        )
        assert parsed == datetime(2026, 1, 1, 12, 0, 0)

    def test_parse_invalid_filenames(self):
        for name in [
            "license.key",
            "license-xxxx-CLT.key",
            "license-20260101T120000Z.key",
            "license-20260101T999999Z-CLT.key",
            "",
        ]:
            assert lic._parse_timestamped_license_filename(name) is None

    def test_find_latest_timestamped_prefers_newest(self, tmp_path):
        older = tmp_path / "license-20250101T000000Z-CLT.key"
        newer = tmp_path / "license-20260101T000000Z-CLT.key"
        older.write_text("old")
        newer.write_text("new")
        latest = lic._find_latest_timestamped_license_file(tmp_path)
        assert latest == newer

    def test_find_latest_returns_none_when_no_candidates(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hi")
        assert lic._find_latest_timestamped_license_file(tmp_path) is None

    def test_find_license_file_in_directory_prefers_exact_license_key(self, tmp_path):
        exact = tmp_path / "license.key"
        stamped = tmp_path / "license-20260101T000000Z-CLT.key"
        exact.write_text("exact")
        stamped.write_text("stamped")
        result = lic._find_license_file_in_directory(tmp_path)
        assert result == exact

    def test_find_license_file_in_directory_falls_back_to_timestamped(self, tmp_path):
        stamped = tmp_path / "license-20260101T000000Z-CLT.key"
        stamped.write_text("stamped")
        result = lic._find_license_file_in_directory(tmp_path)
        assert result == stamped


# ---------------------------------------------------------------------------
# Machine ID & country
# ---------------------------------------------------------------------------
class TestMachineIDAndCountry:
    def test_get_machine_id_returns_hex_sha256(self, monkeypatch):
        monkeypatch.setattr(lic.platform, "system", lambda: "Linux")
        mid = lic.get_machine_id()
        assert isinstance(mid, str)
        assert len(mid) == 64
        assert all(c in "0123456789abcdef" for c in mid)

    def test_get_machine_id_is_stable(self, monkeypatch):
        monkeypatch.setattr(lic.platform, "system", lambda: "Linux")
        assert lic.get_machine_id() == lic.get_machine_id()

    def test_get_country_prefers_online(self, monkeypatch):
        monkeypatch.setattr(lic, "get_country_online", lambda: "CO")
        monkeypatch.setattr(lic, "get_country_offline", lambda: "GB")
        assert lic.get_country() == "CO"

    def test_get_country_falls_back_to_offline(self, monkeypatch):
        monkeypatch.setattr(lic, "get_country_online", lambda: None)
        monkeypatch.setattr(lic, "get_country_offline", lambda: "DE")
        assert lic.get_country() == "DE"

    def test_get_country_online_handles_errors(self, monkeypatch):
        class _Boom:
            @staticmethod
            def get(*a, **kw):
                raise RuntimeError("offline")

        import sys as _sys
        monkeypatch.setitem(_sys.modules, "requests", _Boom)
        assert lic.get_country_online() is None


# ---------------------------------------------------------------------------
# User data dir / license discovery
# ---------------------------------------------------------------------------
class TestUserDataAndDiscovery:
    def test_get_user_data_dir_in_dev_mode(self, monkeypatch):
        monkeypatch.setattr(lic.sys, "frozen", False, raising=False)
        path = lic.get_user_data_dir()
        assert isinstance(path, Path)
        assert path.name == "MVC_Calculator"
        assert path.exists()

    def test_get_license_file_path_returns_licence_key_in_data_dir(self, isolated_user_data):
        target = lic.get_license_file_path()
        assert target == isolated_user_data / lic.LICENSE_FILENAME

    def test_find_license_file_uses_persistent_directory(self, isolated_user_data, monkeypatch):
        key = lic.generate_license_key("a@b.c", "US", "HWID", 0)
        (isolated_user_data / lic.LICENSE_FILENAME).write_text(key)
        monkeypatch.setattr(lic.sys, "frozen", False, raising=False)
        monkeypatch.setattr(lic, "migrate_license_from_old_locations", lambda: None)
        found = lic.find_license_file()
        assert found == isolated_user_data / lic.LICENSE_FILENAME

    def test_migrate_license_when_already_in_persistent(self, isolated_user_data):
        (isolated_user_data / lic.LICENSE_FILENAME).write_text("key")
        migrated = lic.migrate_license_from_old_locations()
        assert migrated == isolated_user_data / lic.LICENSE_FILENAME


# ---------------------------------------------------------------------------
# load_and_validate_license / check_license
# ---------------------------------------------------------------------------
class TestLoadAndValidateLicense:
    def _write_valid_license(self, dest: Path, *, hwid="HWID", country="US", email="a@b.c"):
        key = lic.generate_license_key(email, country, hwid, 0)
        dest.write_text(key, encoding="utf-8")
        return key

    def test_missing_license_returns_error(self, isolated_user_data, monkeypatch):
        monkeypatch.setattr(lic, "find_license_file", lambda: None)
        ok, err = lic.load_and_validate_license()
        assert ok is False
        assert err and "License file not found" in err

    def test_valid_license_with_matching_hwid_and_country(self, isolated_user_data, monkeypatch):
        path = isolated_user_data / lic.LICENSE_FILENAME
        self._write_valid_license(path, hwid="HWID", country="US")
        monkeypatch.setattr(lic, "find_license_file", lambda: path)
        monkeypatch.setattr(lic, "get_machine_id", lambda: "HWID")
        monkeypatch.setattr(lic, "get_country", lambda: "US")
        # Silence telemetry
        monkeypatch.setattr(lic, "_report_license_success", lambda *_a, **_k: None)
        ok, err = lic.load_and_validate_license()
        assert ok is True
        assert err is None

    def test_hwid_mismatch_rejected(self, isolated_user_data, monkeypatch):
        path = isolated_user_data / lic.LICENSE_FILENAME
        self._write_valid_license(path, hwid="GOOD", country="US")
        monkeypatch.setattr(lic, "find_license_file", lambda: path)
        monkeypatch.setattr(lic, "get_machine_id", lambda: "BAD")
        monkeypatch.setattr(lic, "get_country", lambda: "US")
        monkeypatch.setattr(lic, "_report_license_failure", lambda *_a, **_k: None)
        ok, err = lic.load_and_validate_license()
        assert ok is False
        assert "Hardware ID mismatch" in err

    def test_country_mismatch_rejected(self, isolated_user_data, monkeypatch):
        path = isolated_user_data / lic.LICENSE_FILENAME
        self._write_valid_license(path, hwid="HWID", country="US")
        monkeypatch.setattr(lic, "find_license_file", lambda: path)
        monkeypatch.setattr(lic, "get_machine_id", lambda: "HWID")
        monkeypatch.setattr(lic, "get_country", lambda: "DE")
        monkeypatch.setattr(lic, "_report_license_failure", lambda *_a, **_k: None)
        ok, err = lic.load_and_validate_license()
        assert ok is False
        assert "not valid for this country" in err

    def test_wildcard_hfmdd_accepted_for_hfmdd_email(self, isolated_user_data, monkeypatch):
        path = isolated_user_data / lic.LICENSE_FILENAME
        key = lic.generate_license_key(
            "professor@hfmdd.de", "DE", "ignored", 0, use_wildcard_hwid=True
        )
        path.write_text(key, encoding="utf-8")
        monkeypatch.setattr(lic, "find_license_file", lambda: path)
        monkeypatch.setattr(lic, "get_machine_id", lambda: "ANY-MACHINE")
        monkeypatch.setattr(lic, "get_country", lambda: "DE")
        monkeypatch.setattr(lic, "_report_license_success", lambda *_a, **_k: None)
        ok, err = lic.load_and_validate_license()
        assert ok is True
        assert err is None

    def test_wildcard_hfmdd_rejected_for_non_hfmdd_email(self, isolated_user_data, monkeypatch):
        path = isolated_user_data / lic.LICENSE_FILENAME
        key = lic.generate_license_key(
            "someone@gmail.com", "DE", "ignored", 0, use_wildcard_hwid=True
        )
        path.write_text(key, encoding="utf-8")
        monkeypatch.setattr(lic, "find_license_file", lambda: path)
        monkeypatch.setattr(lic, "get_machine_id", lambda: "ANY")
        monkeypatch.setattr(lic, "get_country", lambda: "DE")
        monkeypatch.setattr(lic, "_report_license_failure", lambda *_a, **_k: None)
        ok, err = lic.load_and_validate_license()
        assert ok is False
        assert "hfmdd.de" in err

    def test_check_license_is_noop_when_not_enforced(self, monkeypatch):
        monkeypatch.setattr(lic, "ENFORCE_LICENSE", False)
        assert lic.check_license() is True

    def test_check_license_calls_loader_when_enforced(self, monkeypatch):
        monkeypatch.setattr(lic, "ENFORCE_LICENSE", True)
        called = {}

        def fake_loader():
            called["ok"] = True
            return True, None

        monkeypatch.setattr(lic, "load_and_validate_license", fake_loader)
        assert lic.check_license() is True
        assert called["ok"] is True

    def test_check_license_returns_false_when_loader_fails(self, monkeypatch):
        monkeypatch.setattr(lic, "ENFORCE_LICENSE", True)
        monkeypatch.setattr(lic, "load_and_validate_license", lambda: (False, "bad"))
        assert lic.check_license() is False


# ---------------------------------------------------------------------------
# Telemetry reporter suppression
# ---------------------------------------------------------------------------
class TestReportOncePerSession:
    def test_failure_reporter_does_nothing_when_not_enforced(self, monkeypatch):
        monkeypatch.setattr(lic, "ENFORCE_LICENSE", False)
        # Should not raise, and should not try to import telemetry.
        lic._report_license_failure("some error")

    def test_success_reporter_does_nothing_when_not_enforced(self, monkeypatch):
        monkeypatch.setattr(lic, "ENFORCE_LICENSE", False)
        lic._report_license_success("user@example.com")
