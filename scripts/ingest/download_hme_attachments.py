#!/usr/bin/env python3
"""
Download HME (Hourly Metrics & Efficiency) reports from Gmail attachments.
This script searches for emails with HME reports and downloads the Excel attachments.
"""
import email
import imaplib
import os
import sys
import hashlib
from email.header import decode_header, make_header
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

# Fix: Define SCRIPT_PATH properly
SCRIPT_PATH = Path(__file__).resolve()

IMAP_HOST   = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER   = os.getenv("IMAP_USER", "")
IMAP_PASS   = os.getenv("IMAP_PASS", "")
MAILBOX     = "INBOX"

# HME-specific settings
SENDER      = os.getenv("HME_IMAP_SENDER", "")  # Set in .env if different from default
SUBJECT_KEY = os.getenv("HME_IMAP_SUBJECT_KEY", "HME")  # Subject keyword to search for
# Default to 30 days ago to catch recent emails (fixes Dec 31 issue)
days_back = int(os.getenv("HME_IMAP_DAYS_BACK", "30"))
default_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
SINCE_DATE  = os.getenv("HME_IMAP_SINCE", default_since)  # DD-MMM-YYYY format
DEBUG_LIST  = int(os.getenv("HME_IMAP_DEBUG_LIST", "1"))

ALLOWED_EXT = {".xlsx", ".xls"}

PROJECT_ROOT = SCRIPT_PATH.parents[2]
SAVE_DIR     = PROJECT_ROOT / "data" / "raw" / "hme"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def _decode(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s

def _norm_subject(s: str) -> str:
    s = s.replace("&amp;", "&")
    # collapse whitespace
    s = " ".join(s.split())
    return s.casefold()

def _safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in (" ", ".", "_", "-", "(", ")") else "_" for ch in name).strip()

def _content_hash(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()[:8]

def _prefix_from_date(date_hdr: str) -> str:
    try:
        dt = email.utils.parsedate_to_datetime(date_hdr)
        if dt.tzinfo:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return datetime.today().strftime("%Y-%m-%d")

def _save_unique(base_dir: Path, suggested_name: str, payload: bytes) -> Path:
    out_path = base_dir / suggested_name
    if out_path.exists():
        existing = out_path.read_bytes()
        if existing == payload:
            return out_path
        stem, ext = out_path.stem, out_path.suffix
        out_path = base_dir / f"{stem}__{_content_hash(payload)}{ext}"
    out_path.write_bytes(payload)
    return out_path

def _debug_list_recent_inbox(M: imaplib.IMAP4_SSL, limit=20):
    print("\n[DEBUG] Last messages in INBOX (up to 20):")
    criteria = ["FROM", f'"{SENDER}"'] if SENDER else ["ALL"]
    typ, data = M.search(None, *criteria)
    if typ != "OK" or not data or not data[0]:
        print("[DEBUG] Could not list INBOX messages for diagnostics.")
        return
    all_ids = data[0].split()
    for msg_id in reversed(all_ids[-limit:]):
        typ, msg_data = M.fetch(msg_id, "(RFC822.HEADER)")
        if typ != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        subj = _decode(msg.get("Subject"))
        frm  = _decode(msg.get("From"))
        date_hdr = _decode(msg.get("Date"))
        print(f"  - {msg_id.decode():>6} | {date_hdr} | {frm} | Subject: {subj}")

def download():
    if not IMAP_USER or not IMAP_PASS:
        print("[ERROR] IMAP_USER and IMAP_PASS must be set in your .env at the repo root.")
        sys.exit(1)

    print(f"[INFO] HME Download Script")
    print(f"[INFO] Saving to: {SAVE_DIR}")
    print(f"[INFO] Connecting: {IMAP_HOST} as {IMAP_USER}")
    print(f"[INFO] Searching since: {SINCE_DATE}")
    print(f"[INFO] Subject keyword: {SUBJECT_KEY}")
    if SENDER:
        print(f"[INFO] Sender filter: {SENDER}")

    M = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        M.login(IMAP_USER, IMAP_PASS)
    except imaplib.IMAP4.error as e:
        print(f"[ERROR] Login failed: {e}")
        sys.exit(2)

    typ, _ = M.select(MAILBOX)
    if typ != "OK":
        print(f"[ERROR] Could not select mailbox {MAILBOX}.")
        M.logout()
        sys.exit(3)
    print(f"[INFO] Selected mailbox: {MAILBOX}")

    # Standard IMAP search in INBOX
    criteria = ["SINCE", SINCE_DATE]
    if SENDER:
        criteria += ["FROM", f'"{SENDER}"']
    typ, data = M.search(None, *criteria)
    if typ != "OK":
        print("[ERROR] IMAP search failed:", data)
        M.close(); M.logout(); sys.exit(4)

    ids = data[0].split() if data and data[0] else []
    print(f"[INFO] Candidate messages since {SINCE_DATE}: {len(ids)}")

    if not ids and DEBUG_LIST:
        _debug_list_recent_inbox(M, limit=20)
        M.close(); M.logout()
        print(f"[DONE] Saved 0 attachment(s) to {SAVE_DIR}")
        return

    TARGET_SUBJ = _norm_subject(SUBJECT_KEY)
    seen_days = set()
    saved = 0

    for msg_id in ids:
        typ, msg_data = M.fetch(msg_id, "(RFC822)")
        if typ != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        subj = _decode(msg.get("Subject"))
        
        # Check if subject contains HME keyword (case-insensitive)
        if TARGET_SUBJ not in _norm_subject(subj):
            continue

        date_hdr = _decode(msg.get("Date"))
        day_key = _prefix_from_date(date_hdr)  # YYYY-MM-DD (email day)
        if day_key in seen_days:
            continue  # keep at most one file per day
        seen_days.add(day_key)

        frm  = _decode(msg.get("From"))
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
            suggested = f"{day_key}__{safe_name}"
            out_path = _save_unique(SAVE_DIR, suggested, payload)
            print(f"[SAVE] {out_path.name}  (From: {frm}; Subject: {subj})")
            saved += 1

    M.close(); M.logout()
    print(f"[DONE] Saved {saved} attachment(s) to {SAVE_DIR}")

if __name__ == "__main__":
    download()

