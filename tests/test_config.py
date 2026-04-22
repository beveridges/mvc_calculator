"""Tests for config.defaults and config.code_signing_config."""

from __future__ import annotations


class TestDefaults:
    def test_default_semg_frequency_is_positive_int(self):
        from config.defaults import DEFAULT_SEMG_FREQUENCY
        assert isinstance(DEFAULT_SEMG_FREQUENCY, int)
        assert DEFAULT_SEMG_FREQUENCY > 0

    def test_best_of_is_three(self):
        from config.defaults import BEST_OF
        assert BEST_OF == 3


class TestCodeSigningConfig:
    def test_exposes_expected_constants(self):
        from config import code_signing_config as cfg
        assert hasattr(cfg, "ENABLE_CODE_SIGNING")
        assert isinstance(cfg.ENABLE_CODE_SIGNING, bool)
        assert hasattr(cfg, "CERT_PATH")
        assert hasattr(cfg, "CERT_PASSWORD")
        assert hasattr(cfg, "CERT_THUMBPRINT")
        assert hasattr(cfg, "TIMESTAMP_URL")
        assert hasattr(cfg, "FILE_DESCRIPTION")
        assert hasattr(cfg, "FILE_DESCRIPTION_URL")

    def test_timestamp_url_is_http(self):
        from config import code_signing_config as cfg
        assert cfg.TIMESTAMP_URL.startswith(("http://", "https://"))
