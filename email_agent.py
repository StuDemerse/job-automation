"""
email_agent.py — Connects to Yahoo & Gmail, sorts emails into folders,
and returns a list of important emails for the daily digest.

How it works:
  1. Connects via IMAP (secure, read/move only — never deletes anything)
  2. Scans inbox for emails from the last N days
  3. Matches subject/sender against SORTING_RULES in config.py
  4. Moves matched emails into the appropriate folder
  5. Returns high-priority emails for the digest report
"""

import imaplib
import email
import email.policy
from email.header import decode_header
import datetime
import re
from typing import Optional
from config import (
    YAHOO_EMAIL, YAHOO_APP_PASSWORD,
    GMAIL_EMAIL, GMAIL_APP_PASSWORD,
    EMAIL_LOOKBACK_DAYS, SORTING_RULES, DIGEST_PRIORITY_THRESHOLD
)


# ── IMAP server settings for each provider ────────────────────────────────────

IMAP_SERVERS = {
    "yahoo": {"host": "imap.mail.yahoo.com", "port": 993},
    "gmail": {"host": "imap.gmail.com",      "port": 993},
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def decode_str(value: str) -> str:
    """Decode encoded email header strings to plain text."""
    if value is None:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            # Handle unknown or invalid charsets gracefully
            safe_charset = charset or "utf-8"
            if safe_charset.lower() in ("unknown-8bit", "unknown", "x-unknown"):
                safe_charset = "latin-1"
            try:
                decoded.append(part.decode(safe_charset, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                decoded.append(part.decode("latin-1", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def match_rule(subject: str, sender: str) -> Optional[dict]:
    """
    Check if an email matches any sorting rule.
    Returns the highest-priority (lowest number) matching rule, or None.
    """
    text = (subject + " " + sender).lower()
    matches = []
    for rule in SORTING_RULES:
        if any(kw.lower() in text for kw in rule["keywords"]):
            matches.append(rule)
    if not matches:
        return None
    return min(matches, key=lambda r: r["priority"])


def ensure_folder(imap: imaplib.IMAP4_SSL, provider: str, folder_name: str):
    """Create a folder/label if it doesn't already exist."""
    # Gmail uses labels differently — prefix with parent if needed
    if provider == "gmail":
        folder_name = folder_name  # Gmail creates under root fine via IMAP
    status, _ = imap.create(folder_name)
    # Ignore "already exists" errors
    return


def move_email(imap: imaplib.IMAP4_SSL, uid: bytes, folder: str, provider: str):
    """Copy email to target folder then mark original as deleted."""
    try:
        ensure_folder(imap, provider, folder)
        # COPY to destination
        imap.uid("COPY", uid, folder)
        # Mark original for deletion
        imap.uid("STORE", uid, "+FLAGS", "\\Deleted")
    except Exception as e:
        print(f"    ⚠️  Could not move email to '{folder}': {e}")


# ── Core agent function ───────────────────────────────────────────────────────

def run_email_agent(provider: str) -> list[dict]:
    """
    Run the email agent for one provider ('yahoo' or 'gmail').
    Returns a list of high-priority email dicts for the digest.
    """
    if provider == "yahoo":
        address  = YAHOO_EMAIL
        password = YAHOO_APP_PASSWORD
    else:
        address  = GMAIL_EMAIL
        password = GMAIL_APP_PASSWORD

    server_cfg = IMAP_SERVERS[provider]
    digest_items = []

    print(f"\n📬 Connecting to {provider.title()} ({address})...")

    try:
        imap = imaplib.IMAP4_SSL(server_cfg["host"], server_cfg["port"])
        imap.login(address, password)
    except imaplib.IMAP4.error as e:
        print(f"  ❌ Login failed for {provider}: {e}")
        print("  → Make sure you're using an App Password, not your regular password.")
        return []

    imap.select("INBOX")

    # Build date filter (IMAP uses DD-Mon-YYYY format)
    since_date = (datetime.date.today() - datetime.timedelta(days=EMAIL_LOOKBACK_DAYS))
    since_str  = since_date.strftime("%d-%b-%Y")

    _, data = imap.uid("SEARCH", None, f'SINCE "{since_str}"')
    uids = data[0].split() if data[0] else []

    print(f"  Found {len(uids)} email(s) since {since_str}")

    moved_count = 0
    for uid in uids:
        _, msg_data = imap.uid("FETCH", uid, "(RFC822)")
        if not msg_data or not msg_data[0]:
            continue

        raw = msg_data[0][1]
        try:
            msg = email.message_from_bytes(raw, policy=email.policy.compat32)
        except Exception:
            try:
                raw = raw.replace(b'unknown-8bit', b'utf-8')
                msg = email.message_from_bytes(raw)
            except Exception:
                continue

        subject = decode_str(msg.get("Subject", "(no subject)"))
        sender  = decode_str(msg.get("From", ""))
        date    = msg.get("Date", "")

        rule = match_rule(subject, sender)

        if rule:
            print(f"  → [{rule['folder']}] {subject[:60]}")
            move_email(imap, uid, rule["folder"], provider)
            moved_count += 1

            if rule["priority"] <= DIGEST_PRIORITY_THRESHOLD:
                digest_items.append({
                    "provider": provider,
                    "subject":  subject,
                    "sender":   sender,
                    "date":     date,
                    "folder":   rule["folder"],
                    "priority": rule["priority"],
                })
        # Emails with no matching rule stay in Inbox untouched

    # Commit deletions (moves)
    imap.expunge()
    imap.logout()

    print(f"  ✅ Sorted {moved_count} email(s). {len(digest_items)} flagged for digest.")
    return digest_items


def run_all_email_agents() -> list[dict]:
    """Run the agent for both Yahoo and Gmail, combine results."""
    all_digest = []
    all_digest.extend(run_email_agent("yahoo"))
    all_digest.extend(run_email_agent("gmail"))
    # Sort digest by priority
    all_digest.sort(key=lambda x: x["priority"])
    return all_digest


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    results = run_all_email_agents()
    print(f"\n📋 Digest preview ({len(results)} items):")
    for item in results:
        print(f"  [{item['priority']}] {item['folder']} | {item['subject'][:50]} | {item['sender'][:30]}")
