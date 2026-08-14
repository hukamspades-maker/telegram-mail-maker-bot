import asyncio
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN, CLEANUP_INTERVAL_MINUTES
from database.db_manager import DatabaseManager
from services.webhook_service import WebhookService

from bot.handlers.start import start_handler
from bot.handlers.create_mail import (
    handle_quick_mail,
    handle_custom_mail_start,
    receive_custom_prefix,
    handle_login_key_start,
    receive_login_input,
    cancel_custom_prefix,
    WAITING_CUSTOM_PREFIX,
    WAITING_LOGIN_INPUT
)
from bot.handlers.my_emails import (
    handle_list_aliases,
    handle_copy_alias,
    handle_delete_alias
)
from bot.handlers.admin import (
    handle_admin_panel,
    handle_users_list,
    handle_approve_user_callback,
    handle_revoke_user_callback
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def periodic_cleanup_task(db: DatabaseManager):
    while True:
        try:
            await db.cleanup_expired_aliases()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(CLEANUP_INTERVAL_MINUTES * 60)

async def post_init(application: Application):
    db: DatabaseManager = application.bot_data["db"]
    await db.init_db()
    
    webhook_service = WebhookService(db, application)
    await webhook_service.start()
    application.bot_data["webhook_service"] = webhook_service

    asyncio.create_task(periodic_cleanup_task(db))
    logger.info("🚀 Telegram Mail Maker Bot successfully initialized!")

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN is not configured!")
        return

    db = DatabaseManager()

    builder = Application.builder().token(BOT_TOKEN).post_init(post_init)
    app = builder.build()
    app.bot_data["db"] = db

    custom_prefix_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_custom_mail_start, pattern=r"^mail_custom$")
        ],
        states={
            WAITING_CUSTOM_PREFIX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_prefix)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_custom_prefix)]
    )

    login_key_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_login_key_start, pattern=r"^mail_login_key$")
        ],
        states={
            WAITING_LOGIN_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_login_input)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_custom_prefix)]
    )

    app.add_handler(CommandHandler(["start", "menu"], start_handler))
    app.add_handler(CommandHandler("admin", handle_admin_panel))

    app.add_handler(custom_prefix_conv)
    app.add_handler(login_key_conv)

    app.add_handler(CallbackQueryHandler(start_handler, pattern=r"^main_menu$"))
    app.add_handler(CallbackQueryHandler(handle_quick_mail, pattern=r"^mail_quick$"))

    app.add_handler(CallbackQueryHandler(handle_list_aliases, pattern=r"^mail_list$"))
    app.add_handler(CallbackQueryHandler(handle_copy_alias, pattern=r"^copy:"))
    app.add_handler(CallbackQueryHandler(handle_delete_alias, pattern=r"^del:"))

    app.add_handler(CallbackQueryHandler(handle_admin_panel, pattern=r"^admin_panel$"))
    app.add_handler(CallbackQueryHandler(handle_users_list, pattern=r"^admin_users_list$"))
    app.add_handler(CallbackQueryHandler(handle_approve_user_callback, pattern=r"^admin_approve:"))
    app.add_handler(CallbackQueryHandler(handle_revoke_user_callback, pattern=r"^admin_revoke:"))

    logger.info("Starting Telegram Bot Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
