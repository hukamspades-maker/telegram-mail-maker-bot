from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import KeyboardButtonStyle
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
                    InlineKeyboardButton(f"Grant Access to {user.first_name}", callback_data=f"admin_approve:{user.id}", style=KeyboardButtonStyle.SUCCESS)
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
            f"Only authorized users approved by Owner can create emails.\n\n"
            f"🆔 <b>Your ID:</b> <code>{user.id}</code>"
        )
        if update.callback_query:
            await update.callback_query.answer("⚠️ Access restricted.", show_alert=True)
            await update.callback_query.edit_message_text(restricted_msg, parse_mode="HTML")
        else:
            await update.message.reply_text(restricted_msg, parse_mode="HTML")
        return

    active_domains = await db.get_active_domains()
    domain_list_str = ", ".join([f"<code>{d}</code>" for d in active_domains])

    welcome_text = (
        f"👑 <b>JAMES BOND MAIL MAKER ⚡️</b>\n\n"
        f"Create custom temporary & permanent email addresses on your custom domains ({domain_list_str})!\n\n"
        f"✨ <b>Features:</b>\n"
        f"• ⚡ Instant OTP Extraction & Highlighting\n"
        f"• 🔗 1-Tap Action / Sign-in Link Buttons\n"
        f"• 📎 Original PDF Document Forwarding\n"
        f"• 📄 Rich Interactive .html Email Attachments\n"
        f"• 🔐 Security Key Login & Email Recovery\n\n"
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

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    help_text = (
        f"<b>JAMES BOND MAIL — USER GUIDE & HELP</b>\n\n"
        f"<b>1. How to create an email:</b>\n"
        f"• Tap <b>Quick Random Email</b> to get an instant random address.\n"
        f"• Tap <b>Custom Prefix Email</b> to choose a custom username (e.g. <code>user@hukam.bond</code>).\n\n"
        f"<b>2. Domain:</b>\n"
        f"Emails are powered by verified domain <code>hukam.bond</code>.\n\n"
        f"<b>3. Receiving Emails & OTPs:</b>\n"
        f"Any email, OTP code, sign-in link, or PDF document sent to your created email addresses will arrive directly in this chat.\n\n"
        f"<b>4. Security Keys & Email Recovery:</b>\n"
        f"Every created email comes with a unique <b>Security Key</b> (e.g. <code>KEY-8X9A2M</code>). "
        f"If you lose access or want to log in on another device, use <b>Login / Restore Email</b>.\n\n"
        f"<i>For admin inquiries or support, contact the bot owner.</i>"
    )

    kbd = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")]])

    if query:
        await query.edit_message_text(help_text, reply_markup=kbd, parse_mode="HTML")
    else:
        await update.message.reply_text(help_text, reply_markup=kbd, parse_mode="HTML")
