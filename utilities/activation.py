"""
Activation API integration for redemption-based licensing.

Public API expected by main.py:
- activation_api_configured() -> bool
- redeem_activation_code(code: str) -> tuple[bool, dict|None, str]
"""

from __future__ import annotations

import json
import logging
import os
import platform
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib import error as urlerror
from urllib import request as urlrequest

from utilities.license import get_country, get_machine_id
from utilities.version_info import BUILDNUMBER, VERSIONNUMBER

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 8
DEFAULT_RETRIES = 2


def _get_activation_api_url() -> str:
    return str(os.environ.get("ACTIVATION_API_URL", "")).strip()


def _get_int_env(name: str, default: int, minimum: int = 0) -> int:
    raw = str(os.environ.get(name, "")).strip()
    if not raw:
        return default
    try:
        value = int(raw)
        return value if value >= minimum else default
    except ValueError:
        return default


def activation_api_configured() -> bool:
    """Return True when ACTIVATION_API_URL is present and non-empty."""
    return bool(_get_activation_api_url())


def _build_payload(activation_code: str) -> Dict[str, Any]:
    return {
        "activation_code": activation_code,
        "hwid": get_machine_id(),
        "country": get_country(),
        "app_version": str(VERSIONNUMBER),
        "build_number": str(BUILDNUMBER),
        "platform": platform.platform(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def _post_json(url: str, payload: Dict[str, Any], timeout_seconds: int) -> Dict[str, Any]:
    request_data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    req = urlrequest.Request(
        url=url,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=timeout_seconds) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        if not body.strip():
            return {}
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("Activation API returned non-object JSON.")
        return parsed


def redeem_activation_code(code: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Redeem activation code against configured API.

    Returns:
    - (True, response_json, success_message) on success (requires license_key in response)
    - (False, None, error_message) on failure
    """
    activation_code = str(code or "").strip()
    if not activation_code:
        return False, None, "Activation code cannot be empty."

    api_url = _get_activation_api_url()
    if not api_url:
        return False, None, "Activation API URL is not configured."

    timeout_seconds = _get_int_env(
        "ACTIVATION_HTTP_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS, minimum=1
    )
    retries = _get_int_env("ACTIVATION_HTTP_RETRIES", DEFAULT_RETRIES, minimum=0)
    payload = _build_payload(activation_code)

    last_error = "Activation request failed."
    total_attempts = retries + 1

    for attempt in range(1, total_attempts + 1):
        try:
            response_data = _post_json(api_url, payload, timeout_seconds)
            license_key = str(response_data.get("license_key", "")).strip()
            if not license_key:
                message = str(response_data.get("message", "")).strip()
                return (
                    False,
                    None,
                    message or "Activation API response is missing license_key.",
                )

            message = str(response_data.get("message", "")).strip() or "Activation successful."
            return True, response_data, message

        except urlerror.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace").strip()
            except Exception:
                body = ""
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}

            api_message = ""
            if isinstance(data, dict):
                api_message = str(data.get("message", "")).strip()

            last_error = api_message or f"Activation request failed (HTTP {e.code})."
            logger.warning("Activation HTTPError on attempt %s/%s: %s", attempt, total_attempts, last_error)

        except urlerror.URLError:
            last_error = "Could not reach activation server. Check internet connection and API URL."
            logger.warning(
                "Activation URLError on attempt %s/%s", attempt, total_attempts, exc_info=True
            )

        except TimeoutError:
            last_error = f"Activation request timed out after {timeout_seconds} seconds."
            logger.warning(
                "Activation timeout on attempt %s/%s", attempt, total_attempts, exc_info=True
            )

        except json.JSONDecodeError:
            last_error = "Activation server returned invalid JSON."
            logger.warning(
                "Activation JSON decode error on attempt %s/%s", attempt, total_attempts, exc_info=True
            )

        except Exception:
            last_error = "Unexpected activation error."
            logger.exception("Unexpected activation error on attempt %s/%s", attempt, total_attempts)

        if attempt < total_attempts:
            # Tiny linear backoff to avoid instant tight retry loops.
            time.sleep(0.4 * attempt)

    return False, None, last_error
