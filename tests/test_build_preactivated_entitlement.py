"""Tests for scripts.build_preactivated_entitlement CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from utilities import license as lic


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_preactivated_entitlement.py"


class TestBuildPreactivatedEntitlementCLI:
    def test_license_missing_reports_error(self, tmp_path):
        out = tmp_path / "entitlement.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--license-file",
                str(tmp_path / "nope.key"),
                "--output",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "License file not found" in result.stdout + result.stderr

    def test_invalid_license_reports_error(self, tmp_path):
        bad = tmp_path / "license.key"
        bad.write_text("not-a-license", encoding="utf-8")
        out = tmp_path / "entitlement.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--license-file",
                str(bad),
                "--output",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Invalid license" in result.stdout + result.stderr

    def test_valid_license_writes_entitlement(self, tmp_path):
        key = lic.generate_license_key(
            "inst@hfmdd.de", "DE", "ignored", 0, use_wildcard_hwid=True
        )
        lic_path = tmp_path / "license.key"
        lic_path.write_text(key, encoding="utf-8")

        out = tmp_path / "sub" / "entitlement.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--license-file",
                str(lic_path),
                "--output",
                str(out),
                "--issued-for",
                "hfmdd.de",
                "--bundle-id",
                "BUNDLE-TEST",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert out.exists()
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["license_key"] == key
        assert payload["format"] == "license_key_v1"
        assert payload["source"] == "preactivated_bundle"
        assert payload["issued_for"] == "hfmdd.de"
        assert payload["bundle_id"] == "BUNDLE-TEST"
