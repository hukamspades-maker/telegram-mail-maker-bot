import random
import string
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database.db_manager import DatabaseManager
from bot.keyboards import get_back_button

logger = logging.getLogger(__name__)

WAITING_CUSTOM_PREFIX = 1
WAITING_LOGIN_INPUT = 2
DOMAIN = "hukam.bond"

def generate_random_prefix(length: int = 6) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

async def handle_quick_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db: DatabaseManager = context.bot_data["db"]

    prefix = f"mail_{generate_random_prefix(6)}"
    full_address = f"{prefix}@{DOMAIN}"

    try:
        alias = await db.create_alias(
            user_id=query.from_user.id,
            address=full_address,
            domain=DOMAIN,
            mail_type='permanent'
        )

        sec_key = alias.get("security_key", "KEY-XXXXXX")

        msg = (
            f"✅ <b>Email Created!</b>\n\n"
            f"📬 <b>Address:</b> <code>{full_address}</code>\n"
            f"🔑 <b>Security Key:</b> <code>{sec_key}</code>\n\n"
            f"⚠️ <i>Save your Security Key! You can use it to log into or restore this email anytime.</i>\n\n"
            f"📩 <i>Any email or OTP sent to this address will land directly in this chat!</i>"
        )

        kbd = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Address", callback_data=f"copy:{full_address}")],
            [InlineKeyboardButton("🗑️ Delete Address", callback_data=f"del:{alias['id']}")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])

        await query.edit_message_text(msg, reply_markup=kbd, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error creating quick mail: {e}")
        await query.edit_message_text(f"❌ Error creating email: {e}", reply_markup=get_back_button())

async def handle_custom_mail_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        f"✏️ <b>Enter custom username prefix for @{DOMAIN}:</b>\n\n"
        f"<i>Example: type <code>james</code> to get <code>james@{DOMAIN}</code></i>",
        parse_mode="HTML"
    )
    return WAITING_CUSTOM_PREFIX

async def receive_custom_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: DatabaseManager = context.bot_data["db"]
    user_input = update.message.text.strip().lower()

    clean_prefix = "".join(c for c in user_input if c.isalnum() or c in "._-")
    if not clean_prefix:
        await update.message.reply_text("❌ Invalid username. Please send letters, numbers, or dots.")
        return WAITING_CUSTOM_PREFIX

    full_address = f"{clean_prefix}@{DOMAIN}"

    try:
        alias = await db.create_alias(
            user_id=update.effective_user.id,
            address=full_address,
            domain=DOMAIN,
            mail_type='permanent'
        )

        sec_key = alias.get("security_key", "KEY-XXXXXX")

        msg = (
            f"🎉 <b>Custom Email Created!</b>\n\n"
            f"📬 <b>Address:</b> <code>{full_address}</code>\n"
            f"🔑 <b>Security Key:</b> <code>{sec_key}</code>\n\n"
            f"⚠️ <i>Save your Security Key! You can use it to log into or restore this email anytime.</i>\n\n"
            f"📩 <i>Any email or OTP sent to this address will arrive here instantly!</i>"
        )

        kbd = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Address", callback_data=f"copy:{full_address}")],
            [InlineKeyboardButton("🗑️ Delete Address", callback_data=f"del:{alias['id']}")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])

        await update.message.reply_text(msg, reply_markup=kbd, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error creating custom email: {e}", reply_markup=get_back_button())

    return ConversationHandler.END

async def handle_login_key_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        f"🔑 <b>Login / Restore Email Address</b>\n\n"
        f"Please send your email address and Security Key in this format:\n\n"
        f"<code>email@hukam.bond KEY-XXXXXX</code>\n\n"
        f"<i>Example: <code>james@hukam.bond KEY-8A9X2M</code></i>",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    return WAITING_LOGIN_INPUT

async def receive_login_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: DatabaseManager = context.bot_data["db"]
    user_input = update.message.text.strip()
    parts = user_input.split()

    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Invalid format!\nPlease send format: <code>email@hukam.bond KEY-XXXXXX</code>",
            parse_mode="HTML"
        )
        return WAITING_LOGIN_INPUT

    email_addr = parts[0].lower().strip()
    sec_key = parts[1].upper().strip()

    alias = await db.login_with_security_key(update.effective_user.id, email_addr, sec_key)

    if alias:
        await update.message.reply_text(
            f"🎉 <b>Success! Logged in & Restored Email:</b>\n\n"
            f"📬 <b>Address:</b> <code>{email_addr}</code>\n"
            f"🔑 <b>Security Key:</b> <code>{sec_key}</code>\n\n"
            f"📩 <i>Any email or OTP sent to this address will now land in your chat!</i>",
            reply_markup=get_back_button(),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            f"❌ <b>Login Failed!</b>\nIncorrect email address or Security Key. Please re-check and try again.",
            reply_markup=get_back_button(),
            parse_mode="HTML"
        )
        return ConversationHandler.END

async def cancel_custom_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=get_back_button())
    return ConversationHandler.END
