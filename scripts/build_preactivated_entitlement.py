#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a preactivated entitlement artifact from an existing signed license key.

Usage:
  python scripts/build_preactivated_entitlement.py --license-file license.key --output preactivated/entitlement.json

Optional metadata:
  --issued-for hfmdd.de
  --bundle-id HFMDD-2026-04
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utilities.entitlement import build_preactivated_entitlement
from utilities.license import validate_license_key


def main() -> int:
    ap = argparse.ArgumentParser(description="Create preactivated entitlement artifact")
    ap.add_argument("--license-file", required=True, help="Path to signed license.key file")
    ap.add_argument(
        "--output",
        default="preactivated/entitlement.json",
        help="Output entitlement artifact path",
    )
    ap.add_argument("--issued-for", default="hfmdd.de", help="Metadata field: issued_for")
    ap.add_argument("--bundle-id", default="", help="Metadata field: bundle_id")
    args = ap.parse_args()

    lic_path = Path(args.license_file).resolve()
    out_path = Path(args.output).resolve()

    if not lic_path.exists():
        print(f"[ERROR] License file not found: {lic_path}")
        return 2

    license_key = lic_path.read_text(encoding="utf-8").strip()
    ok, _, err = validate_license_key(license_key)
    if not ok:
        print(f"[ERROR] Invalid license key: {err}")
        return 3

    payload = build_preactivated_entitlement(
        license_key=license_key,
        issued_for=args.issued_for,
        bundle_id=args.bundle_id or None,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"[OK] Wrote preactivated entitlement: {out_path}")
    print(f"[INFO] format={payload['format']} source={payload['source']} issued_for={payload['issued_for']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
