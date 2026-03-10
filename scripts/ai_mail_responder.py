#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Mail Responder (Python 3.11+)

Monitors an IMAP mailbox and sends controlled auto-replies to a whitelist of senders.

Rules (per sender):
- First email ever: AI reply + universal license key (key is appended by code; AI never sees it).
- Second email within 24h of first: fixed template reply.
- Third email OR any email after 24h of first: no reply (permanently closed).

Only responds to senders in ALLOWED_SENDERS (see ai_responder_config.py or env AI_RESPONDER_ALLOWED_SENDERS).

Usage:
    python ai_mail_responder.py

Or run as a service: python run_ai_responder_service.py
"""

from __future__ import annotations

import logging
import signal
import smtplib
import sqlite3
import ssl
import sys
import time
import traceback
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path
from typing import Optional, Tuple, List

# Add parent so we can import from scripts
sys.path.insert(0, str(Path(__file__).parent))

import ai_responder_config as config
from ai_responder_utils import (
    build_summary_for_ai,
    extract_text_body,
    get_email_sender,
    get_email_subject,
    get_message_id,
    has_auto_reply_headers,
    imap_connect,
    imap_fetch_rfc822,
    imap_mark_seen,
    imap_search_unseen,
    imap_select_box,
    parse_message,
)

# ---------------------------------------------------------------------------
# Logging (configured after config is loaded)
# ---------------------------------------------------------------------------
def _setup_logging() -> logging.Logger:
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    log_file = config.LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handlers: List[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]
    try:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    except Exception:
        pass

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
    return logging.getLogger(__name__)


logger = _setup_logging()

# ---------------------------------------------------------------------------
# Shutdown flag for graceful exit
# ---------------------------------------------------------------------------
_shutdown_requested = False


def _signal_handler(sig, frame):
    global _shutdown_requested
    logger.info("Shutdown requested (signal %s), finishing current cycle...", sig)
    _shutdown_requested = True


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class SenderState:
    sender: str
    first_seen_ts: int
    reply_count: int
    closed: int  # 0 or 1


# ---------------------------------------------------------------------------
# SQLite state
# ---------------------------------------------------------------------------
def db_init(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sender_state (
            sender TEXT PRIMARY KEY,
            first_seen_ts INTEGER NOT NULL,
            reply_count INTEGER NOT NULL,
            closed INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS processed_messages (
            message_id TEXT PRIMARY KEY,
            processed_ts INTEGER NOT NULL
        )
    """)
    conn.commit()


def db_get_sender_state(conn: sqlite3.Connection, sender: str) -> Optional[SenderState]:
    cur = conn.cursor()
    cur.execute(
        "SELECT sender, first_seen_ts, reply_count, closed FROM sender_state WHERE sender = ?",
        (sender,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return SenderState(sender=row[0], first_seen_ts=row[1], reply_count=row[2], closed=row[3])


def db_upsert_sender_state(conn: sqlite3.Connection, state: SenderState) -> None:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sender_state (sender, first_seen_ts, reply_count, closed)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sender) DO UPDATE SET
            first_seen_ts=excluded.first_seen_ts,
            reply_count=excluded.reply_count,
            closed=excluded.closed
    """, (state.sender, state.first_seen_ts, state.reply_count, state.closed))
    conn.commit()


def db_is_message_processed(conn: sqlite3.Connection, message_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM processed_messages WHERE message_id = ?", (message_id,))
    return cur.fetchone() is not None


def db_mark_message_processed(conn: sqlite3.Connection, message_id: str, ts: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO processed_messages (message_id, processed_ts) VALUES (?, ?)",
        (message_id, ts),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------
def generate_ai_reply(api_key: str, model: str, summary: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": summary},
        ],
        temperature=0.2,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text


# ---------------------------------------------------------------------------
# SMTP send
# ---------------------------------------------------------------------------
def send_reply_smtp(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    to_addr: str,
    from_addr: str,
    from_name: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str],
    references: Optional[str],
) -> None:
    msg = EmailMessage()
    msg["To"] = to_addr
    msg["From"] = formataddr((from_name, from_addr))
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=ctx)
        server.ehlo()
        server.login(username, password)
        server.send_message(msg)


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------
def should_respond_to_sender(sender: str) -> bool:
    return sender in config.ALLOWED_SENDERS


def compute_action_for_sender(
    state: Optional[SenderState], now_ts: int
) -> Tuple[str, Optional[SenderState]]:
    """
    Returns (action, possibly_updated_state).
    action is one of: "FIRST", "SECOND", "NONE".
    """
    if state is None:
        return "FIRST", None

    if state.closed == 1:
        return "NONE", state

    age = now_ts - state.first_seen_ts
    if age > config.SECOND_REPLY_WINDOW_SECONDS:
        state.closed = 1
        return "NONE", state

    if state.reply_count == 1:
        return "SECOND", state

    return "NONE", state


# ---------------------------------------------------------------------------
# Process one email
# ---------------------------------------------------------------------------
def process_one_email(conn: sqlite3.Connection, raw_bytes: bytes) -> None:
    msg = parse_message(raw_bytes)

    sender = get_email_sender(msg)
    subject = get_email_subject(msg)
    body = extract_text_body(msg)
    message_id = get_message_id(msg)
    in_reply_to = message_id or None
    references = (msg.get("References") or "").strip() or None

    now_ts = int(time.time())

    if not sender:
        return
    if sender == config.MAILBOX_USER.lower():
        return
    if has_auto_reply_headers(msg):
        return

    if not should_respond_to_sender(sender):
        return

    if message_id and db_is_message_processed(conn, message_id):
        return

    state = db_get_sender_state(conn, sender)
    action, state_after = compute_action_for_sender(state, now_ts)

    # Persist closed flag if we just set it (e.g. window expired)
    if state_after is not None and state_after.closed == 1:
        db_upsert_sender_state(conn, state_after)

    if action == "NONE":
        if message_id:
            db_mark_message_processed(conn, message_id, now_ts)
        return

    reply_subject = subject
    if reply_subject and not reply_subject.lower().startswith("re:"):
        reply_subject = "Re: " + reply_subject
    if not reply_subject:
        reply_subject = "Re: Your email"

    from_name = "MovioLabs Support"
    license_key = config.get_universal_license_key()

    if action == "FIRST":
        summary = build_summary_for_ai(subject, body)
        try:
            ai_text = generate_ai_reply(config.OPENAI_API_KEY, config.OPENAI_MODEL, summary)
        except Exception as e:
            logger.warning("OpenAI call failed, using fallback reply: %s", e)
            ai_text = (
                "Thanks for your message.\n\n"
                "I understand you're having trouble with the license key. "
                "Please try the universal license key below."
            )

        full_body = ai_text.strip() + config.first_reply_footer(license_key)

        send_reply_smtp(
            smtp_host=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT,
            username=config.MAILBOX_USER,
            password=config.MAILBOX_PASS,
            to_addr=sender,
            from_addr=config.MAILBOX_USER,
            from_name=from_name,
            subject=reply_subject,
            body=full_body,
            in_reply_to=in_reply_to,
            references=references,
        )
        logger.info("Sent FIRST reply to %s", sender)

        new_state = SenderState(sender=sender, first_seen_ts=now_ts, reply_count=1, closed=0)
        db_upsert_sender_state(conn, new_state)

    elif action == "SECOND":
        send_reply_smtp(
            smtp_host=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT,
            username=config.MAILBOX_USER,
            password=config.MAILBOX_PASS,
            to_addr=sender,
            from_addr=config.MAILBOX_USER,
            from_name=from_name,
            subject=reply_subject,
            body=config.SECOND_REPLY_TEMPLATE,
            in_reply_to=in_reply_to,
            references=references,
        )
        logger.info("Sent SECOND reply to %s", sender)
        assert state is not None
        state.reply_count = 2
        db_upsert_sender_state(conn, state)

    if message_id:
        db_mark_message_processed(conn, message_id, now_ts)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run_loop() -> None:
    global _shutdown_requested
    conn = sqlite3.connect(config.DB_PATH)
    db_init(conn)

    logger.info(
        "AI Mail Responder started. Mailbox=%s IMAP=%s:%s SMTP=%s:%s Allowed=%s",
        config.MAILBOX_USER,
        config.IMAP_HOST,
        config.IMAP_PORT,
        config.SMTP_HOST,
        config.SMTP_PORT,
        sorted(config.ALLOWED_SENDERS),
    )

    while not _shutdown_requested:
        imap = None
        try:
            imap = imap_connect(config.IMAP_HOST, config.IMAP_PORT, config.IMAP_USE_SSL)
            imap.login(config.MAILBOX_USER, config.MAILBOX_PASS)
            imap_select_box(imap, config.IMAP_FOLDER)

            uids = imap_search_unseen(imap)
            if uids:
                logger.debug("Found %d unseen message(s)", len(uids))

            for uid in uids:
                if _shutdown_requested:
                    break
                try:
                    raw = imap_fetch_rfc822(imap, uid)
                    process_one_email(conn, raw)
                except Exception:
                    logger.exception("Error processing one email")
                finally:
                    try:
                        imap_mark_seen(imap, uid)
                    except Exception:
                        pass

            try:
                imap.logout()
            except Exception:
                pass

        except Exception:
            logger.exception("Error in poll cycle")
            try:
                if imap is not None:
                    imap.logout()
            except Exception:
                pass

        for _ in range(config.POLL_SECONDS):
            if _shutdown_requested:
                break
            time.sleep(1)

    conn.close()
    logger.info("AI Mail Responder stopped.")


def main() -> None:
    # Config sanity
    if not config.MAILBOX_PASS or not config.OPENAI_API_KEY:
        logger.error(
            "Set AI_RESPONDER_MAILBOX_PASS and AI_RESPONDER_OPENAI_API_KEY (and optionally "
            "AI_RESPONDER_UNIVERSAL_LICENSE_KEY or AI_RESPONDER_UNIVERSAL_LICENSE_KEY_FILE)."
        )
        sys.exit(1)

    license_key = config.get_universal_license_key()
    if not license_key:
        logger.warning("No universal license key set; first-reply footer will be empty.")

    # Graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, _signal_handler)
        except AttributeError:
            pass

    run_loop()


if __name__ == "__main__":
    main()
