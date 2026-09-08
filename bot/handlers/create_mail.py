import random
import string
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database.db_manager import DatabaseManager
from bot.keyboards import get_back_button, get_domain_selection_keyboard

logger = logging.getLogger(__name__)

WAITING_CUSTOM_PREFIX = 1
WAITING_LOGIN_INPUT = 2

def generate_random_prefix(length: int = 6) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

async def handle_select_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db: DatabaseManager = context.bot_data["db"]

    _, action_type = query.data.split(":", 1)
    active_domains = await db.get_active_domains()

    if not active_domains:
        active_domains = ["hukam.bond", "jattjames.bond"]

    title = "⚡ <b>Select Domain for Quick Random Email:</b>" if action_type == "quick" else "✏️ <b>Select Domain for Custom Prefix Email:</b>"
    msg = (
        f"{title}\n\n"
        f"Choose which domain you want your new email created on:"
    )

    await query.edit_message_text(
        msg,
        reply_markup=get_domain_selection_keyboard(action_type, active_domains),
        parse_mode="HTML"
    )

async def handle_quick_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db: DatabaseManager = context.bot_data["db"]

    # Pattern: do_mail:quick:domain.com
    parts = query.data.split(":")
    selected_domain = parts[2] if len(parts) > 2 else "hukam.bond"

    prefix = f"mail_{generate_random_prefix(6)}"
    full_address = f"{prefix}@{selected_domain}"

    try:
        alias = await db.create_alias(
            user_id=query.from_user.id,
            address=full_address,
            domain=selected_domain,
            mail_type='permanent'
        )

        sec_key = alias.get("security_key", "KEY-XXXXXX")

        msg = (
            f"🎉 <b>New Email Created!</b>\n\n"
            f"📬 <b>Address:</b> <code>{full_address}</code>\n"
            f"🔑 <b>Security Key:</b> <code>{sec_key}</code>\n\n"
            f"⚠️ <i>Save your Security Key! You can use it to log into or restore this email anytime.</i>\n\n"
            f"📩 <i>Any email or OTP sent to this address will land directly in this chat!</i>"
        )

        kbd = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Address", callback_data=f"copy:{full_address}")],
            [
                InlineKeyboardButton("🗑️ Delete Address", callback_data=f"del:{alias['id']}"),
                InlineKeyboardButton("➕ Create Another", callback_data="select_domain:quick")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])

        await query.edit_message_text(msg, reply_markup=kbd, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error creating quick mail: {e}")
        await query.edit_message_text(f"❌ Error creating email: {e}", reply_markup=get_back_button())

async def handle_custom_mail_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Pattern: do_mail:custom:domain.com
    parts = query.data.split(":")
    selected_domain = parts[2] if len(parts) > 2 else "hukam.bond"

    context.user_data["selected_domain"] = selected_domain

    await query.edit_message_text(
        f"✏️ <b>Enter custom username prefix for @{selected_domain}:</b>\n\n"
        f"<i>Example: type <code>james</code> to create <code>james@{selected_domain}</code></i>",
        parse_mode="HTML"
    )
    return WAITING_CUSTOM_PREFIX

async def receive_custom_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: DatabaseManager = context.bot_data["db"]
    selected_domain = context.user_data.get("selected_domain", "hukam.bond")

    user_input = update.message.text.strip().lower()
    clean_prefix = "".join(c for c in user_input if c.isalnum() or c in "._-")
    if not clean_prefix:
        await update.message.reply_text("❌ Invalid username prefix. Please send letters, numbers, or dots.")
        return WAITING_CUSTOM_PREFIX

    full_address = f"{clean_prefix}@{selected_domain}"

    try:
        alias = await db.create_alias(
            user_id=update.effective_user.id,
            address=full_address,
            domain=selected_domain,
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
            [
                InlineKeyboardButton("🗑️ Delete Address", callback_data=f"del:{alias['id']}"),
                InlineKeyboardButton("➕ Create Another", callback_data="select_domain:custom")
            ],
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
        f"<code>email@domain.com KEY-XXXXXX</code>\n\n"
        f"<i>Example: <code>james@jattjames.bond KEY-8A9X2M</code></i>",
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
            "❌ Invalid format!\nPlease send format: <code>email@domain.com KEY-XXXXXX</code>",
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
