import base64
import logging
from aiohttp import web
from telegram.ext import Application

from config import WEBHOOK_HOST, WEBHOOK_PORT, WEBHOOK_SECRET
from database.db_manager import DatabaseManager
from services.email_parser import parse_raw_email, format_telegram_email_message

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self, db: DatabaseManager, bot_app: Application):
        self.db = db
        self.bot_app = bot_app
        self.app = web.Application()
        self.runner = None

        self.app.router.add_post('/webhook/email', self.handle_inbound_email)
        self.app.router.add_get('/health', self.handle_health)

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "healthy", "service": "Telegram Mail Maker Webhook"})

    async def handle_inbound_email(self, request: web.Request) -> web.Response:
        # Validate secret header if set
        auth_header = request.headers.get("X-Webhook-Secret", "")
        if WEBHOOK_SECRET and auth_header != WEBHOOK_SECRET:
            logger.warning("Unauthorized webhook request attempt.")
            return web.json_response({"error": "Unauthorized"}, status=401)

        try:
            payload = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        raw_email_b64 = payload.get("raw_email")
        to_address = payload.get("to", "").lower().strip()
        
        parsed_email = {}

        if raw_email_b64:
            try:
                raw_bytes = base64.b64decode(raw_email_b64)
                parsed_email = parse_raw_email(raw_bytes)
                if not to_address:
                    to_address = parsed_email.get("recipient", "").lower().strip()
            except Exception as e:
                logger.error(f"Error parsing raw email: {e}")
        
        if not parsed_email:
            # Fallback to direct JSON keys
            parsed_email = {
                "sender": payload.get("from", "Unknown Sender"),
                "recipient": to_address,
                "subject": payload.get("subject", "(No Subject)"),
                "body_text": payload.get("text", payload.get("body", "")),
                "body_html": payload.get("html", ""),
                "has_attachments": bool(payload.get("attachments")),
                "attachments_info": payload.get("attachments", [])
            }

        if not to_address:
            return web.json_response({"error": "Missing recipient address ('to')"}, status=400)

        # Lookup recipient alias in DB
        alias = await self.db.get_alias(to_address)
        if not alias:
            logger.info(f"Received email for unknown/expired address: {to_address}")
            return web.json_response({"status": "ignored", "reason": "Alias not found or expired"}, status=200)

        user_id = alias["user_id"]

        # Save to database
        email_id = await self.db.log_received_email(
            alias_address=to_address,
            user_id=user_id,
            sender=parsed_email["sender"],
            subject=parsed_email["subject"],
            body_text=parsed_email["body_text"],
            body_html=parsed_email["body_html"],
            has_attachments=parsed_email["has_attachments"]
        )

        # Format and deliver to Telegram User
        tg_message = format_telegram_email_message(parsed_email, to_address)

        try:
            await self.bot_app.bot.send_message(
                chat_id=user_id,
                text=tg_message,
                parse_mode="HTML"
            )
            logger.info(f"Delivered email #{email_id} to Telegram User {user_id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message to user {user_id}: {e}")

        return web.json_response({"status": "delivered", "email_id": email_id})

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, WEBHOOK_HOST, WEBHOOK_PORT)
        await site.start()
        logger.info(f"🚀 Inbound Email Webhook Server running at http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/webhook/email")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
