"""Standalone script to fetch recent Gmail emails via IMAP and save as JSON files."""

import argparse
import base64
import email
from email.header import decode_header
import email.message
import imaplib
import json
import os
from pathlib import Path
import re

from dotenv import load_dotenv


def decode_header_value(value: str | None) -> str:
    """Decode an email header value that may contain encoded words."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def sanitize_filename(name: str) -> str:
    """Remove or replace characters that are unsafe for filenames."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(". ")
    return name[:100] if name else "no_subject"


def extract_all_headers(msg: email.message.Message) -> dict[str, list[str]]:
    """Extract all headers from the message, decoded.

    Returns a dict of header name -> list of values.
    """
    headers: dict[str, list[str]] = {}
    for key, value in msg.items():
        decoded = decode_header_value(value)
        headers.setdefault(key, []).append(decoded)
    return headers


def extract_mime_parts(msg: email.message.Message) -> list[dict]:
    """Recursively extract all MIME parts from the message."""
    parts = []

    if msg.is_multipart():
        for part in msg.walk():
            if part.is_multipart():
                continue
            parts.append(_extract_single_part(part))
    else:
        parts.append(_extract_single_part(msg))

    return parts


def _extract_single_part(part: email.message.Message) -> dict:
    """Extract data from a single MIME part."""
    content_type = part.get_content_type()
    content_disposition = str(part.get("Content-Disposition", ""))
    charset = part.get_content_charset() or "utf-8"
    filename = part.get_filename()
    if filename:
        filename = decode_header_value(filename)

    part_data: dict = {
        "content_type": content_type,
        "content_disposition": content_disposition,
        "charset": charset,
        "filename": filename,
        "content_id": part.get("Content-ID"),
        "content_transfer_encoding": part.get("Content-Transfer-Encoding"),
    }

    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            part_data["body"] = None
        elif content_type.startswith("text/"):
            part_data["body"] = payload.decode(charset, errors="replace")
        else:
            part_data["body_base64"] = base64.b64encode(payload).decode("ascii")
            part_data["size_bytes"] = len(payload)
    except Exception as e:
        part_data["decode_error"] = str(e)

    return part_data


def extract_body_text_and_html(parts: list[dict]) -> tuple[str, str]:
    """Pull out the first plain text and HTML body from extracted MIME parts."""
    body_text = ""
    body_html = ""
    for part in parts:
        is_attachment = "attachment" in part.get("content_disposition", "")
        body = part.get("body")
        if not body or is_attachment:
            continue
        if part["content_type"] == "text/plain" and not body_text:
            body_text = body
        elif part["content_type"] == "text/html" and not body_html:
            body_html = body
    return body_text, body_html


def fetch_emails(count: int) -> None:
    load_dotenv(override=True)

    gmail_email = os.getenv("GMAIL_EMAIL")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_email or not gmail_password:
        print("Error: GMAIL_EMAIL and GMAIL_APP_PASSWORD must be set in .env")
        return

    output_dir = Path("email_logs")
    output_dir.mkdir(exist_ok=True)

    print(f"Connecting to Gmail IMAP as {gmail_email}...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(gmail_email, gmail_password)
    _status, mailbox_data = mail.select("INBOX")
    total_messages = int(mailbox_data[0])

    if total_messages == 0:
        print("Inbox is empty.")
        mail.logout()
        return

    # Fetch the last N messages by sequence number (newest = highest)
    start = max(1, total_messages - count + 1)
    fetch_range = f"{start}:{total_messages}"

    print(
        f"Found {total_messages} emails total, "
        f"fetching {min(count, total_messages)} most recent..."
    )

    # Fetch UIDs and full messages in the range
    _status, uid_response = mail.fetch(fetch_range, "(UID)")
    uids = []
    for item in uid_response:
        if isinstance(item, bytes):
            match = re.search(rb"UID (\d+)", item)
            if match:
                uids.append((item.split()[0], match.group(1).decode()))

    # Process newest first
    uids.reverse()

    for i, (seq_num, uid) in enumerate(uids, 1):
        # Fetch IMAP metadata separately (flags, labels, dates, Gmail IDs)
        _, meta_response = mail.fetch(
            seq_num, "(FLAGS INTERNALDATE X-GM-LABELS X-GM-MSGID X-GM-THRID)"
        )
        meta_line = b""
        for part in meta_response:
            if isinstance(part, bytes):
                meta_line = part
                break

        # Fetch full RFC822 message
        _, msg_data = mail.fetch(seq_num, "(RFC822)")
        raw_email = None
        for part in msg_data:
            if isinstance(part, tuple):
                raw_email = part[1]

        if raw_email is None:
            print(f"  [{i}/{len(uids)}] Skipped: could not parse message {uid}")
            continue

        msg = email.message_from_bytes(raw_email)

        # Extract IMAP-level metadata
        flags_match = re.search(rb"FLAGS \(([^)]*)\)", meta_line)
        imap_flags = (
            flags_match.group(1).decode(errors="replace").split() if flags_match else []
        )

        internal_date_match = re.search(rb'INTERNALDATE "([^"]*)"', meta_line)
        internal_date = (
            internal_date_match.group(1).decode(errors="replace")
            if internal_date_match
            else ""
        )

        gm_labels_match = re.search(rb"X-GM-LABELS \(([^)]*)\)", meta_line)
        gmail_labels = (
            gm_labels_match.group(1).decode(errors="replace").split()
            if gm_labels_match
            else []
        )

        gm_msgid_match = re.search(rb"X-GM-MSGID (\d+)", meta_line)
        gmail_message_id = gm_msgid_match.group(1).decode() if gm_msgid_match else None

        gm_thrid_match = re.search(rb"X-GM-THRID (\d+)", meta_line)
        gmail_thread_id = gm_thrid_match.group(1).decode() if gm_thrid_match else None

        # Extract all headers and MIME parts
        all_headers = extract_all_headers(msg)
        mime_parts = extract_mime_parts(msg)
        body_text, body_html = extract_body_text_and_html(mime_parts)

        subject = decode_header_value(msg.get("Subject"))

        email_data = {
            # IMAP metadata
            "uid": uid,
            "imap_flags": imap_flags,
            "imap_internal_date": internal_date,
            "gmail_message_id": gmail_message_id,
            "gmail_thread_id": gmail_thread_id,
            "gmail_labels": gmail_labels,
            # All headers (decoded)
            "headers": all_headers,
            # Convenience top-level fields
            "subject": subject,
            "from": decode_header_value(msg.get("From")),
            "to": decode_header_value(msg.get("To")),
            "cc": decode_header_value(msg.get("Cc")),
            "bcc": decode_header_value(msg.get("Bcc")),
            "reply_to": decode_header_value(msg.get("Reply-To")),
            "date": msg.get("Date", ""),
            "message_id": msg.get("Message-ID", ""),
            "in_reply_to": msg.get("In-Reply-To", ""),
            "references": msg.get("References", ""),
            "content_type": msg.get_content_type(),
            # Body (convenience)
            "body_text": body_text,
            "body_html": body_html,
            # All MIME parts (includes attachments as base64)
            "mime_parts": mime_parts,
        }

        safe_subject = sanitize_filename(subject)
        filename = f"{uid}_{safe_subject}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(email_data, f, indent=2, ensure_ascii=False)

        print(f"  [{i}/{len(uids)}] Saved: {filename}")

    mail.logout()
    print(f"Done. {len(uids)} emails saved to {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch recent Gmail emails via IMAP")
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of recent emails to fetch (default: 50)",
    )
    args = parser.parse_args()
    fetch_emails(args.count)
