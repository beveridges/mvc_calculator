"""Tests for utilities.entitlement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from utilities import entitlement as ent
from utilities import license as lic


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _valid_key(email="user@example.com", country="US", hwid="HWID"):
    return lic.generate_license_key(email, country, hwid, 0)


# ---------------------------------------------------------------------------
# is_preactivated_bundle_entitlement
# ---------------------------------------------------------------------------
class TestIsPreactivatedBundle:
    def test_true_for_exact_match(self):
        assert ent.is_preactivated_bundle_entitlement({"source": "preactivated_bundle"}) is True

    def test_case_insensitive(self):
        assert ent.is_preactivated_bundle_entitlement({"source": " Preactivated_Bundle "}) is True

    def test_false_for_other_sources(self):
        assert ent.is_preactivated_bundle_entitlement({"source": "migrated_license_key"}) is False

    def test_false_for_non_dict(self):
        assert ent.is_preactivated_bundle_entitlement(None) is False
        assert ent.is_preactivated_bundle_entitlement("string") is False


# ---------------------------------------------------------------------------
# build_preactivated_entitlement
# ---------------------------------------------------------------------------
class TestBuildPreactivatedEntitlement:
    def test_core_fields(self):
        payload = ent.build_preactivated_entitlement("   some-key   ")
        assert payload["license_key"] == "some-key"
        assert payload["format"] == "license_key_v1"
        assert payload["source"] == "preactivated_bundle"
        assert payload["issued_for"] == "hfmdd.de"
        assert "issued_at_utc" in payload
        assert "bundle_id" not in payload

    def test_custom_fields(self):
        payload = ent.build_preactivated_entitlement(
            "k", issued_for="custom.org", bundle_id="BUNDLE-1"
        )
        assert payload["issued_for"] == "custom.org"
        assert payload["bundle_id"] == "BUNDLE-1"


# ---------------------------------------------------------------------------
# save_entitlement / load_entitlement
# ---------------------------------------------------------------------------
class TestSaveLoadEntitlement:
    def test_save_then_load(self, isolated_user_data):
        ok, err = ent.save_entitlement({"license_key": "abc", "source": "preactivated_bundle"})
        assert ok is True
        assert err is None

        loaded = ent.load_entitlement()
        assert loaded is not None
        assert loaded["license_key"] == "abc"
        assert "stored_at_utc" in loaded

    def test_load_returns_none_when_missing(self, isolated_user_data):
        assert ent.load_entitlement() is None

    def test_load_returns_none_when_malformed(self, isolated_user_data):
        path = ent.get_entitlement_file_path()
        path.write_text("{not json", encoding="utf-8")
        assert ent.load_entitlement() is None

    def test_load_returns_none_when_not_object(self, isolated_user_data):
        path = ent.get_entitlement_file_path()
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        assert ent.load_entitlement() is None

    def test_save_reports_error_when_write_fails(self, isolated_user_data, monkeypatch):
        def _boom(self, *a, **kw):  # pragma: no cover - exercised via monkeypatch
            raise OSError("disk full")
        monkeypatch.setattr(Path, "write_text", _boom)
        ok, err = ent.save_entitlement({"license_key": "abc"})
        assert ok is False
        assert "disk full" in err


# ---------------------------------------------------------------------------
# migrate_license_key_to_entitlement
# ---------------------------------------------------------------------------
class TestMigrateLicenseKey:
    def test_skips_when_entitlement_already_exists(self, isolated_user_data):
        ent.save_entitlement({"license_key": "x"})
        ok, err = ent.migrate_license_key_to_entitlement()
        assert ok is True
        assert err is None

    def test_returns_error_when_no_license_found(self, isolated_user_data, monkeypatch):
        monkeypatch.setattr(ent, "find_license_file", lambda: None)
        ok, err = ent.migrate_license_key_to_entitlement()
        assert ok is False
        assert "No license.key" in err

    def test_error_when_license_invalid(self, isolated_user_data, tmp_path, monkeypatch):
        bogus = tmp_path / "license.key"
        bogus.write_text("not-a-valid-key", encoding="utf-8")
        monkeypatch.setattr(ent, "find_license_file", lambda: bogus)
        ok, err = ent.migrate_license_key_to_entitlement()
        assert ok is False
        assert err

    def test_migrates_valid_license(self, isolated_user_data, tmp_path, monkeypatch):
        key = _valid_key()
        lic_path = tmp_path / "license.key"
        lic_path.write_text(key, encoding="utf-8")
        monkeypatch.setattr(ent, "find_license_file", lambda: lic_path)
        ok, err = ent.migrate_license_key_to_entitlement()
        assert ok is True
        data = ent.load_entitlement()
        assert data["license_key"] == key
        assert data["source"] == "migrated_license_key"
        assert data["source_path"] == str(lic_path)


# ---------------------------------------------------------------------------
# install_bundled_entitlement_if_available
# ---------------------------------------------------------------------------
class TestInstallBundled:
    def test_returns_ok_when_target_exists(self, isolated_user_data):
        ent.save_entitlement({"license_key": "x"})
        ok, err = ent.install_bundled_entitlement_if_available()
        assert ok is True
        assert err is None

    def test_reports_when_none_found(self, isolated_user_data, tmp_path, monkeypatch):
        # Remove any bundled project preactivated folder by pointing project root at tmp.
        import utilities.entitlement as _em
        monkeypatch.setattr(_em, "__file__", str(tmp_path / "utilities" / "entitlement.py"))
        ok, err = ent.install_bundled_entitlement_if_available()
        assert ok is False
        assert "No bundled entitlement" in err


# ---------------------------------------------------------------------------
# validate_entitlement
# ---------------------------------------------------------------------------
class TestValidateEntitlement:
    def test_reports_missing_when_nothing_on_disk(self, isolated_user_data, monkeypatch):
        monkeypatch.setattr(ent, "find_license_file", lambda: None)
        monkeypatch.setattr(ent, "install_bundled_entitlement_if_available", lambda: (False, "x"))
        ok, err = ent.validate_entitlement()
        assert ok is False
        assert "Entitlement file not found" in err

    def test_reports_missing_license_key(self, isolated_user_data):
        ent.save_entitlement({"source": "preactivated_bundle"})
        ok, err = ent.validate_entitlement()
        assert ok is False
        assert "missing license_key" in err

    def test_rejects_invalid_license_key(self, isolated_user_data):
        ent.save_entitlement({"license_key": "not-valid"})
        ok, err = ent.validate_entitlement()
        assert ok is False
        assert err

    def test_accepts_valid_entitlement(self, isolated_user_data, monkeypatch):
        key = _valid_key(hwid="HWID", country="US")
        ent.save_entitlement({"license_key": key})
        monkeypatch.setattr(ent, "get_machine_id", lambda: "HWID")
        monkeypatch.setattr(ent, "get_country", lambda: "US")
        ok, err = ent.validate_entitlement()
        assert ok is True
        assert err is None

    def test_preactivated_bundle_skips_country_check(self, isolated_user_data, monkeypatch):
        key = lic.generate_license_key(
            "prof@hfmdd.de", "DE", "ignored", 0, use_wildcard_hwid=True
        )
        ent.save_entitlement(
            ent.build_preactivated_entitlement(key, issued_for="hfmdd.de")
        )
        monkeypatch.setattr(ent, "get_machine_id", lambda: "ANY")
        monkeypatch.setattr(ent, "get_country", lambda: "FR")  # different country
        ok, err = ent.validate_entitlement()
        assert ok is True
        assert err is None

    def test_wildcard_rejected_for_non_hfmdd_email(self, isolated_user_data, monkeypatch):
        key = lic.generate_license_key(
            "person@other.com", "DE", "ignored", 0, use_wildcard_hwid=True
        )
        ent.save_entitlement(
            ent.build_preactivated_entitlement(key, issued_for="hfmdd.de")
        )
        monkeypatch.setattr(ent, "get_machine_id", lambda: "ANY")
        monkeypatch.setattr(ent, "get_country", lambda: "DE")
        ok, err = ent.validate_entitlement()
        assert ok is False
        assert "hfmdd.de" in err
