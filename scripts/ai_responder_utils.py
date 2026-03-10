#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared email parsing and IMAP helpers for the AI Mail Responder.
"""

import imaplib
import re
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import List

# ---------------------------------------------------------------------------
# Header and sender
# ---------------------------------------------------------------------------


def decode_mime_header(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def get_email_sender(msg) -> str:
    from_header = msg.get("From", "")
    _, addr = parseaddr(from_header)
    return (addr or "").strip().lower()


def get_email_subject(msg) -> str:
    return decode_mime_header(msg.get("Subject", ""))


def get_message_id(msg) -> str:
    return (msg.get("Message-ID") or "").strip()


def has_auto_reply_headers(msg) -> bool:
    """Return True if message looks like auto/bulk so we should not reply."""
    auto_submitted = (msg.get("Auto-Submitted") or "").lower().strip()
    precedence = (msg.get("Precedence") or "").lower().strip()
    if auto_submitted and auto_submitted != "no":
        return True
    if precedence in {"bulk", "list", "junk"}:
        return True
    return False


# ---------------------------------------------------------------------------
# Body extraction
# ---------------------------------------------------------------------------


def crude_strip_html(html: str) -> str:
    """Minimal HTML strip for support email bodies."""
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p\s*>", "\n", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n\s+\n", "\n\n", html)
    return html


def extract_text_body(msg, max_chars: int = 50000) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    charset = part.get_content_charset() or "utf-8"
                    parts.append(
                        part.get_payload(decode=True).decode(charset, errors="replace")
                    )
                except Exception:
                    continue
        if parts:
            text = "\n\n".join(parts).strip()
            return text[:max_chars] if len(text) > max_chars else text
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if ctype == "text/html" and "attachment" not in disp:
                try:
                    charset = part.get_content_charset() or "utf-8"
                    html = part.get_payload(decode=True).decode(charset, errors="replace")
                    return crude_strip_html(html).strip()[:max_chars]
                except Exception:
                    continue
        return ""
    ctype = msg.get_content_type()
    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    text = payload.decode(charset, errors="replace")
    if ctype == "text/html":
        text = crude_strip_html(text).strip()
    return (text.strip())[:max_chars]


def build_summary_for_ai(subject: str, body: str, max_chars: int = 2500) -> str:
    """Build a summary string for the OpenAI prompt."""
    body = body.strip()
    if len(body) > max_chars:
        body = body[:max_chars] + "\n\n[truncated]"
    return f"Subject: {subject}\n\nCustomer message:\n{body}"


# ---------------------------------------------------------------------------
# IMAP helpers
# ---------------------------------------------------------------------------


def imap_connect(host: str, port: int, use_ssl: bool) -> imaplib.IMAP4:
    if use_ssl:
        return imaplib.IMAP4_SSL(host, port)
    return imaplib.IMAP4(host, port)


def imap_select_box(imap: imaplib.IMAP4, folder: str) -> None:
    typ, data = imap.select(folder)
    if typ != "OK":
        raise RuntimeError(f"IMAP select failed for {folder}: {typ} {data}")


def imap_search_unseen(imap: imaplib.IMAP4) -> List[bytes]:
    typ, data = imap.search(None, "UNSEEN")
    if typ != "OK":
        return []
    if not data or not data[0]:
        return []
    return data[0].split()


def imap_fetch_rfc822(imap: imaplib.IMAP4, uid: bytes) -> bytes:
    typ, data = imap.fetch(uid, "(RFC822)")
    if typ != "OK" or not data or not data[0]:
        raise RuntimeError(f"IMAP fetch failed for {uid!r}: {typ} {data}")
    return data[0][1]


def imap_mark_seen(imap: imaplib.IMAP4, uid: bytes) -> None:
    imap.store(uid, "+FLAGS", "\\Seen")


def parse_message(raw_bytes: bytes):
    """Parse raw RFC822 bytes into an email message."""
    return message_from_bytes(raw_bytes)
