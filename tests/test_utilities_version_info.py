"""Tests for utilities.version_info auto-generated build metadata."""

from __future__ import annotations

import re

from utilities import version_info as v


EXPECTED_STRING_ATTRS = [
    "GITREVHEAD",
    "BUILDNUMBER",
    "VERSIONNUMBER",
    "FRIENDLYVERSIONNAME",
    "VERSIONNAME",
    "GITTAG",
    "CONDAENVIRONMENTNAME",
    "PYTHONVERSION",
    "CONDAENVIRONMENTFILENAME",
    "RELEASENAME",
]


def test_all_string_attributes_are_strings():
    for name in EXPECTED_STRING_ATTRS:
        value = getattr(v, name)
        assert isinstance(value, str), f"{name} should be a string, got {type(value)}"


def test_dev_build_is_bool():
    assert isinstance(v.DEV_BUILD, bool)


def test_build_number_starts_with_version_number():
    # Example: VERSIONNUMBER = "26.04-alpha.01", BUILDNUMBER = "26.04-alpha.01.02"
    assert v.BUILDNUMBER.startswith(v.VERSIONNUMBER)


def test_python_version_format():
    assert re.match(r"^\d+\.\d+\.\d+", v.PYTHONVERSION)


def test_version_name_is_lowercase_slug():
    assert v.VERSIONNAME == v.VERSIONNAME.lower()
    assert " " not in v.VERSIONNAME
