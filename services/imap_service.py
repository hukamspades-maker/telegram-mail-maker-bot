import imaplib
import asyncio
import logging
from typing import Optional
from telegram.ext import Application

from config import IMAP_ENABLED, IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD, IMAP_POLL_INTERVAL
from database.db_manager import DatabaseManager
from services.email_parser import parse_raw_email, format_telegram_email_message

logger = logging.getLogger(__name__)

class IMAPService:
    def __init__(self, db: DatabaseManager, bot_app: Application):
        self.db = db
        self.bot_app = bot_app
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    def fetch_unseen_emails_sync(self):
        """Synchronous IMAP query to run inside asyncio.to_thread."""
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.login(IMAP_USER, IMAP_PASSWORD)
            mail.select("INBOX")

            status, response = mail.search(None, "UNSEEN")
            if status != "OK":
                mail.logout()
                return []

            email_ids = response[0].split()
            messages = []

            for e_id in email_ids:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                if res == "OK":
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            raw_bytes = response_part[1]
                            messages.append(raw_bytes)
                    # Mark as deleted or read
                    mail.store(e_id, "+FLAGS", "\\Seen")

            mail.logout()
            return messages
        except Exception as e:
            logger.error(f"IMAP fetch error: {e}")
            return []

    async def poll_loop(self):
        logger.info(f"📧 IMAP Catch-All Poller started for {IMAP_USER}@{IMAP_HOST}")
        while self.is_running:
            try:
                raw_messages = await asyncio.to_thread(self.fetch_unseen_emails_sync)
                for raw_bytes in raw_messages:
                    await self.process_raw_email(raw_bytes)
            except Exception as e:
                logger.error(f"IMAP Poller loop error: {e}")

            await asyncio.sleep(IMAP_POLL_INTERVAL)

    async def process_raw_email(self, raw_bytes: bytes):
        parsed = parse_raw_email(raw_bytes)
        to_address = parsed.get("recipient", "").lower().strip()
        
        # Check if recipient matches an alias
        if not to_address:
            return

        alias = await self.db.get_alias(to_address)
        if not alias:
            logger.debug(f"IMAP: Ignored email for {to_address} (alias not found or expired)")
            return

        user_id = alias["user_id"]

        # Log to DB
        email_id = await self.db.log_received_email(
            alias_address=to_address,
            user_id=user_id,
            sender=parsed["sender"],
            subject=parsed["subject"],
            body_text=parsed["body_text"],
            body_html=parsed["body_html"],
            has_attachments=parsed["has_attachments"]
        )

        tg_message = format_telegram_email_message(parsed, to_address)
        try:
            await self.bot_app.bot.send_message(
                chat_id=user_id,
                text=tg_message,
                parse_mode="HTML"
            )
            logger.info(f"IMAP: Delivered email #{email_id} to user {user_id}")
        except Exception as e:
            logger.error(f"IMAP: Failed to notify Telegram user {user_id}: {e}")

    def start(self):
        if not IMAP_ENABLED:
            logger.info("IMAP Poller is disabled in config.")
            return
        self.is_running = True
        self.task = asyncio.create_task(self.poll_loop())

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
