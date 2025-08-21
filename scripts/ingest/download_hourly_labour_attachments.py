#!/usr/bin/env python3
"""
Download all 'Hourly Sales & Labour Prompted' Excel attachments since 28-Jul-2025.

- Requires ONLY IMAP_USER and IMAP_PASS in .env at project root (par-delta-dashboard/.env)
- Defaults:
    IMAP_HOST=imap.gmail.com
    IMAP_SENDER=biziq@crunchtime.it
    IMAP_SUBJECT_KEY=Hourly Sales & Labour Prompted
    IMAP_SINCE=28-Jul-2025
- Saves to: <project_root>/data/raw/labour/actual_labor
- File naming: YYYY-MM-DD__<original_name>.xlsx (email's Date header)
- Idempotent: de-dupes by content; appends short hash if same name but different bytes
"""

import email
import imaplib
import os
import sys
import hashlib
from email.header import decode_header, make_header
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# ----------------------------
# Load secrets & config from .env
# ----------------------------
# .env must live in the repo root (par-delta-dashboard/.env)
# Example:
#   IMAP_USER=your_email@example.com
#   IMAP_PASS=your_app_password
load_dotenv()

IMAP_HOST     = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER     = os.getenv("IMAP_USER", "")
IMAP_PASS     = os.getenv("IMAP_PASS", "")

SENDER        = os.getenv("IMAP_SENDER", "biziq@crunchtime.it")
SUBJECT_KEY   = os.getenv("IMAP_SUBJECT_KEY", "Hourly Sales & Labour Prompted")
SINCE_DATE    = os.getenv("IMAP_SINCE", "28-Jul-2025")  # IMAP format: DD-MMM-YYYY

# Only these attachment types will be saved
ALLOWED_EXT = {".xlsx", ".xls"}

# ----------------------------
# Dynamic, portable save path
# ----------------------------
# This file is at: <root>/scripts/ingest/download_hourly_labour_attachments.py
SCRIPT_PATH  = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]  # go up two levels to <root>
SAVE_DIR     = PROJECT_ROOT / "data" / "raw" / "labour" / "actual_labor"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Helpers
# ----------------------------
def _decode(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s

def _safe_filename(name: str) -> str:
    # Remove filesystem-unfriendly chars
    return "".join(ch if ch.isalnum() or ch in (" ", ".", "_", "-", "(", ")") else "_" for ch in name).strip()

def _content_hash(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()[:8]

def _prefix_from_date(date_hdr: str) -> str:
    """Parse email 'Date' header into YYYY-MM-DD, fallback to today."""
    try:
        dt = email.utils.parsedate_to_datetime(date_hdr)
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return datetime.today().strftime("%Y-%m-%d")

def _save_unique(base_dir: Path, suggested_name: str, payload: bytes) -> Path:
    """
    Save bytes; avoid overwriting different content with same name by appending short hash.
    If identical content already exists, skip writing.
    """
    out_path = base_dir / suggested_name
    if out_path.exists():
        existing = out_path.read_bytes()
        if existing == payload:
            return out_path  # identical, nothing to do
        stem, ext = out_path.stem, out_path.suffix
        out_path = base_dir / f"{stem}__{_content_hash(payload)}{ext}"
    out_path.write_bytes(payload)
    return out_path

# ----------------------------
# Main
# ----------------------------
def download():
    # Basic sanity check for required secrets
    if not IMAP_USER or not IMAP_PASS:
        print("[ERROR] IMAP_USER and IMAP_PASS must be set in your .env at the project root.")
        print("Example .env:\n  IMAP_USER=your_email@example.com\n  IMAP_PASS=your_app_password")
        sys.exit(1)

    print(f"[INFO] Saving to: {SAVE_DIR}")
    print(f"[INFO] Connecting to IMAP: {IMAP_HOST} as {IMAP_USER}")

    M = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        M.login(IMAP_USER, IMAP_PASS)
    except imaplib.IMAP4.error as e:
        print(f"[ERROR] Login failed: {e}")
        sys.exit(2)

    M.select("INBOX")

    # Build IMAP search query (args passed separately to imaplib.search)
    criteria = ["SINCE", SINCE_DATE]
    if SENDER:
        criteria += ["FROM", f'"{SENDER}"']
    if SUBJECT_KEY:
        criteria += ["SUBJECT", f'"{SUBJECT_KEY}"']

    typ, data = M.search(None, *criteria)
    if typ != "OK":
        print("[ERROR] IMAP search failed:", data)
        M.close()
        M.logout()
        sys.exit(3)

    msg_ids = data[0].split()
    print(f"[INFO] Found {len(msg_ids)} matching message(s) since {SINCE_DATE}")

    saved = 0
    for msg_id in msg_ids:
        typ, msg_data = M.fetch(msg_id, "(RFC822)")
        if typ != "OK":
            print(f"[WARN] Skipping message id {msg_id.decode()}: fetch failed")
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        subj = _decode(msg.get("Subject"))
        frm  = _decode(msg.get("From"))
        date_hdr = _decode(msg.get("Date"))
        date_prefix = _prefix_from_date(date_hdr)

        for part in msg.walk():
            if part.get_content_disposition() != "attachment":
                continue

            fname = _decode(part.get_filename() or "")
            if not fname:
                continue

            ext = Path(fname).suffix.lower()
            if ext not in ALLOWED_EXT:
                continue

            payload = part.get_payload(decode=True) or b""
            safe_name = _safe_filename(fname)
            suggested = f"{date_prefix}__{safe_name}"
            out_path = _save_unique(SAVE_DIR, suggested, payload)

            print(f"[SAVE] {out_path.name}  (From: {frm}; Subject: {subj})")
            saved += 1

    M.close()
    M.logout()
    print(f"[DONE] Saved {saved} attachment(s) to {SAVE_DIR}")

if __name__ == "__main__":
    download()
