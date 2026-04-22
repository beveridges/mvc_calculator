"""Tests for the top-level generate_license.py CLI script."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from utilities import license as lic


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "generate_license.py"


def _load_generate_license():
    spec = importlib.util.spec_from_file_location("generate_license_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBuildOutputFilename:
    def test_filename_has_expected_prefix_and_suffix(self):
        mod = _load_generate_license()
        path = mod._build_output_filename()
        assert path.name.startswith("license-")
        assert path.name.endswith(f"-{mod.CLIENT_CODE}.key")
        # Match pattern license-YYYYMMDDTHHMMSSZ-<client>.key
        parsed = lic._parse_timestamped_license_filename(path.name)
        assert parsed is not None


def _run_cli(args, cwd):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


class TestGenerateLicenseCLI:
    def test_missing_args_shows_usage(self, tmp_path):
        result = _run_cli([], tmp_path)
        assert result.returncode != 0
        assert "Usage" in (result.stdout + result.stderr)

    def test_wildcard_generates_valid_hfmdd_license(self, tmp_path):
        result = _run_cli(
            ["inst@hfmdd.de", "DE", "0", "--wildcard-hfmdd"],
            tmp_path,
        )
        assert result.returncode == 0
        licenses = list(tmp_path.glob("license-*-CLT0002.key"))
        assert licenses, f"No license file generated. stdout={result.stdout}"
        key = licenses[0].read_text(encoding="utf-8").strip()
        ok, data, _err = lic.validate_license_key(key)
        assert ok is True
        assert data["hwid"] == lic.WILDCARD_HWID_HFMDD
        assert data["email"] == "inst@hfmdd.de"
        assert data["country"] == "DE"

    def test_provided_hwid_is_respected(self, tmp_path):
        result = _run_cli(
            ["user@example.com", "us", "30", "CUSTOM-HWID"],
            tmp_path,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        licenses = list(tmp_path.glob("license-*-CLT0002.key"))
        key = licenses[0].read_text(encoding="utf-8").strip()
        ok, data, _ = lic.validate_license_key(key)
        assert ok is True
        assert data["country"] == "US"  # uppercased
        assert data["hwid"] == "CUSTOM-HWID"
        assert data["expiration"] == "30"

    def test_invalid_expiration_rejected(self, tmp_path):
        result = _run_cli(
            ["user@example.com", "US", "not-a-number"],
            tmp_path,
        )
        assert result.returncode != 0
        assert "Invalid expiration" in (result.stdout + result.stderr)
