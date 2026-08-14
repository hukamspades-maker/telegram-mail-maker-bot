import email
from email.header import decode_header
from bs4 import BeautifulSoup
import re
import html
from typing import Dict, Any, List

def parse_header_str(header_val: str) -> str:
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for content, encoding in decoded_parts:
        if isinstance(content, bytes):
            enc = encoding or 'utf-8'
            try:
                result.append(content.decode(enc, errors='replace'))
            except Exception:
                result.append(content.decode('latin-1', errors='replace'))
        else:
            result.append(str(content))
    return "".join(result)

def extract_otp_code(text: str) -> str:
    """Finds 4-8 digit OTP verification codes in email text."""
    if not text:
        return ""
    matches = re.findall(r'\b\d{4,8}\b', text)
    if matches:
        return matches[0]
    return ""

def parse_raw_email(raw_bytes: bytes) -> Dict[str, Any]:
    msg = email.message_from_bytes(raw_bytes)

    sender = parse_header_str(msg.get("From", "Unknown Sender"))
    recipient = parse_header_str(msg.get("To", ""))
    subject = parse_header_str(msg.get("Subject", "(No Subject)"))

    body_text = ""
    body_html = ""
    has_attachments = False
    attachments_info: List[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition:
                has_attachments = True
                filename = parse_header_str(part.get_filename() or "attachment")
                attachments_info.append(filename)
                continue

            if content_type == "text/plain" and not body_text:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    body_text = payload.decode(charset, errors='replace')

            elif content_type == "text/html" and not body_html:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    body_html = payload.decode(charset, errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            decoded = payload.decode(charset, errors='replace')
            if msg.get_content_type() == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    if not body_text and body_html:
        soup = BeautifulSoup(body_html, 'html.parser')
        body_text = soup.get_text()

    otp_code = extract_otp_code(f"{subject} {body_text}")

    return {
        "sender": sender,
        "recipient": recipient,
        "subject": subject,
        "body_text": body_text or "(Empty message body)",
        "body_html": body_html,
        "has_attachments": has_attachments,
        "attachments_info": attachments_info,
        "otp_code": otp_code
    }

def format_telegram_email_message(parsed_email: Dict[str, Any], recipient_address: str) -> str:
    """Formats parsed email with OTP code highlighted."""
    sender_esc = html.escape(parsed_email.get("sender", "Unknown"))
    subject_esc = html.escape(parsed_email.get("subject", "(No Subject)"))
    body_esc = html.escape(parsed_email.get("body_text", "")[:2500])
    otp = parsed_email.get("otp_code")

    otp_banner = f"\n🔑 <b>OTP CODE:</b> <code>{otp}</code>\n" if otp else ""

    msg = (
        f"📩 <b>New Email / OTP Received!</b>\n{otp_banner}\n"
        f"<b>📬 To:</b> <code>{html.escape(recipient_address)}</code>\n"
        f"<b>👤 From:</b> {sender_esc}\n"
        f"<b>📌 Subject:</b> <b>{subject_esc}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{body_esc}"
    )

    if parsed_email.get("has_attachments"):
        files = ", ".join([html.escape(f) for f in parsed_email.get("attachments_info", [])])
        msg += f"\n\n📎 <b>Attachments:</b> <i>{files}</i>"

    return msg
