import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from bot.keyboards import get_back_button

logger = logging.getLogger(__name__)

async def handle_list_aliases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db: DatabaseManager = context.bot_data["db"]
    user_id = query.from_user.id

    aliases = await db.get_user_aliases(user_id)

    if not aliases:
        kbd = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⚡ Quick Random Mail", callback_data="select_domain:quick"),
                InlineKeyboardButton("✏️ Custom Prefix Mail", callback_data="select_domain:custom")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])
        await query.edit_message_text(
            "📬 <b>You have no active email addresses!</b>\n\n"
            "Choose an option below to create your first email address:",
            reply_markup=kbd,
            parse_mode="HTML"
        )
        return

    text = f"📬 <b>Your Active Email Addresses ({len(aliases)}):</b>\n\n"
    buttons = []

    for idx, a in enumerate(aliases, 1):
        address = a["address"]
        sec_key = a.get("security_key", "N/A")
        received = a["received_count"]
        domain = a.get("domain", address.split("@")[-1])
        text += f"<b>{idx}. <code>{html.escape(address)}</code></b>\n   🔑 Key: <code>{sec_key}</code> | Received: {received}\n\n"
        
        buttons.append([
            InlineKeyboardButton(f"📋 Copy #{idx}", callback_data=f"copy:{address}"),
            InlineKeyboardButton(f"🗑️ Delete #{idx}", callback_data=f"del:{a['id']}")
        ])

    buttons.append([
        InlineKeyboardButton("⚡ Create New Email", callback_data="select_domain:quick"),
        InlineKeyboardButton("🔑 Restore Email", callback_data="mail_login_key")
    ])
    buttons.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

async def handle_copy_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _, address = query.data.split(":", 1)
    await query.answer(text=f"Copied: {address}", show_alert=True)

async def handle_delete_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db: DatabaseManager = context.bot_data["db"]
    _, alias_id_str = query.data.split(":", 1)
    alias_id = int(alias_id_str)

    success = await db.delete_alias(alias_id, query.from_user.id)
    if success:
        await query.answer("Deleted email address!", show_alert=True)
        await handle_list_aliases(update, context)
    else:
        await query.answer("Could not delete address.", show_alert=True)
