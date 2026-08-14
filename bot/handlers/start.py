from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from database.db_manager import DatabaseManager
from bot.keyboards import get_main_menu_keyboard
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: DatabaseManager = context.bot_data["db"]
    user = update.effective_user

    new_pending = await db.register_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    is_approved = await db.is_user_approved(user.id)
    is_admin = user.id in ADMIN_IDS

    if not is_approved:
        if new_pending and ADMIN_IDS:
            owner_id = ADMIN_IDS[0]
            try:
                kbd = InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"✅ Grant Access to {user.first_name}", callback_data=f"admin_approve:{user.id}")
                ]])
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=(
                        f"🔔 <b>New Access Request!</b>\n"
                        f"👤 User: {user.first_name} (@{user.username or 'N/A'})\n"
                        f"🆔 ID: <code>{user.id}</code>"
                    ),
                    reply_markup=kbd,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify owner: {e}")

        restricted_msg = (
            f"🔒 <b>Access Restricted!</b>\n\n"
            f"Only authorized users approved by Owner can create emails on <code>hukam.bond</code>.\n\n"
            f"🆔 <b>Your ID:</b> <code>{user.id}</code>"
        )
        if update.callback_query:
            await update.callback_query.answer("⚠️ Access restricted.", show_alert=True)
            await update.callback_query.edit_message_text(restricted_msg, parse_mode="HTML")
        else:
            await update.message.reply_text(restricted_msg, parse_mode="HTML")
        return

    welcome_text = (
        f"👑 <b>JAMES BOND MAIL — hukam.bond</b>\n\n"
        f"Create custom email addresses on <code>hukam.bond</code> and receive emails/OTPs instantly in Telegram!\n\n"
        f"Choose an option below:"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(is_admin),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(is_admin),
            parse_mode="HTML"
        )
