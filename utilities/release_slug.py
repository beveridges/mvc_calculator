# -*- coding: utf-8 -*-
"""
Short public release names (directories + installer filenames).

Internal BUILDNUMBER in version_info.py stays e.g. 26.04-alpha.01.16.
Public slug uses -al.- instead of -alpha.- and mvcalc / mvcalc-oa prefixes.
"""

from __future__ import annotations

from pathlib import Path


def public_version_tail(buildnumber: str) -> str:
    """Map internal BUILDNUMBER to public tail (26.04-alpha.01.16 -> 26.04-al.01.16)."""
    if "-alpha." in buildnumber:
        return buildnumber.replace("-alpha.", "-al.", 1)
    return buildnumber


def to_internal_version_tail(tail_or_segment: str) -> str:
    """Map public -al.- segment back to -alpha.- for internal keys and RELEASE_NOTES names."""
    if "-al." in tail_or_segment:
        return tail_or_segment.replace("-al.", "-alpha.", 1)
    return tail_or_segment


def release_dir_name(internal_buildnumber: str, oa: bool) -> str:
    """Versioned directory / MSI basename prefix, e.g. mvcalc-oa-26.04-al.01.16."""
    tail = public_version_tail(internal_buildnumber)
    if oa:
        return f"mvcalc-oa-{tail}"
    return f"mvcalc-{tail}"


def legacy_release_dir_name(internal_buildnumber: str, oa: bool) -> str:
    """Previous long directory names (still recognized by deploy / cleanup)."""
    if oa:
        return f"MVC_Calculator-oa-{internal_buildnumber}"
    return f"MVC_Calculator-{internal_buildnumber}"


def resolve_licensed_version_dir(build_base: Path, internal_version: str) -> Path:
    """Prefer legacy dir if it exists, else new slug path (for mkdir / notes / MaxMSP)."""
    legacy = build_base / legacy_release_dir_name(internal_version, False)
    modern = build_base / release_dir_name(internal_version, False)
    if legacy.exists():
        return legacy
    return modern


def resolve_oa_version_dir(build_base: Path, internal_version: str) -> Path:
    legacy = build_base / legacy_release_dir_name(internal_version, True)
    modern = build_base / release_dir_name(internal_version, True)
    if legacy.exists():
        return legacy
    return modern


def licensed_version_dir_is_candidate(dir_name: str) -> bool:
    if dir_name in ("pyinstaller", "temp_logs", "msi"):
        return False
    if dir_name.startswith("MVC_Calculator-oa-") or dir_name.startswith("mvcalc-oa-"):
        return False
    if dir_name.startswith("MVC_Calculator-"):
        return True
    if dir_name.startswith("mvcalc-"):
        return True
    return False


def oa_version_dir_is_candidate(dir_name: str) -> bool:
    return dir_name.startswith("MVC_Calculator-oa-") or dir_name.startswith("mvcalc-oa-")


def internal_version_from_licensed_dir(dir_name: str) -> str | None:
    if not licensed_version_dir_is_candidate(dir_name):
        return None
    if dir_name.startswith("MVC_Calculator-"):
        return dir_name[len("MVC_Calculator-") :]
    rest = dir_name[len("mvcalc-") :]
    return to_internal_version_tail(rest)


def internal_version_from_oa_dir(dir_name: str) -> str | None:
    if not oa_version_dir_is_candidate(dir_name):
        return None
    if dir_name.startswith("MVC_Calculator-oa-"):
        return dir_name[len("MVC_Calculator-oa-") :]
    rest = dir_name[len("mvcalc-oa-") :]
    return to_internal_version_tail(rest)


def is_versioned_release_directory(dir_name: str) -> bool:
    """Under BUILD_BASE: licensed or OA release folder (new slug or legacy)."""
    return licensed_version_dir_is_candidate(dir_name) or oa_version_dir_is_candidate(dir_name)
