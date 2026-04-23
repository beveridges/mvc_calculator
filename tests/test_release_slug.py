"""Release directory / artifact slug helpers."""

from pathlib import Path

from utilities.release_slug import (
    internal_version_from_licensed_dir,
    internal_version_from_oa_dir,
    legacy_release_dir_name,
    licensed_version_dir_is_candidate,
    public_version_tail,
    release_dir_name,
    resolve_licensed_version_dir,
    to_internal_version_tail,
)


def test_public_tail_maps_alpha_to_al():
    assert public_version_tail("26.04-alpha.01.16") == "26.04-al.01.16"


def test_roundtrip_internal_tail():
    assert to_internal_version_tail("26.04-al.01.16") == "26.04-alpha.01.16"


def test_release_dir_names():
    b = "26.04-alpha.01.16"
    assert release_dir_name(b, False) == "mvcalc-26.04-al.01.16"
    assert release_dir_name(b, True) == "mvcalc-oa-26.04-al.01.16"
    assert legacy_release_dir_name(b, False) == "MVC_Calculator-26.04-alpha.01.16"


def test_internal_version_from_dir_names():
    assert internal_version_from_licensed_dir("mvcalc-26.04-al.01.16") == "26.04-alpha.01.16"
    assert internal_version_from_licensed_dir("MVC_Calculator-26.04-alpha.01.16") == "26.04-alpha.01.16"
    assert internal_version_from_oa_dir("mvcalc-oa-26.04-al.01.16") == "26.04-alpha.01.16"
    assert internal_version_from_oa_dir("MVC_Calculator-oa-26.04-alpha.01.16") == "26.04-alpha.01.16"
    assert internal_version_from_licensed_dir("mvcalc-oa-26.04-al.01.16") is None


def test_licensed_candidate_skips_oa():
    assert licensed_version_dir_is_candidate("mvcalc-26.04-al.01.16")
    assert not licensed_version_dir_is_candidate("mvcalc-oa-26.04-al.01.16")


def test_resolve_licensed_prefers_legacy(tmp_path: Path):
    internal = "26.04-alpha.01.01"
    legacy = tmp_path / legacy_release_dir_name(internal, False)
    legacy.mkdir()
    modern = tmp_path / release_dir_name(internal, False)
    assert resolve_licensed_version_dir(tmp_path, internal) == legacy
    modern.mkdir()
    assert resolve_licensed_version_dir(tmp_path, internal) == legacy


def test_resolve_licensed_uses_modern_when_no_legacy(tmp_path: Path):
    internal = "26.04-alpha.01.02"
    modern = tmp_path / release_dir_name(internal, False)
    assert resolve_licensed_version_dir(tmp_path, internal) == modern
