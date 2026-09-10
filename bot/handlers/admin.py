import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import KeyboardButtonStyle
from telegram.ext import ContextTypes, ConversationHandler

from database.db_manager import DatabaseManager
from config import ADMIN_IDS
from bot.keyboards import get_back_button

logger = logging.getLogger(__name__)

WAITING_ADD_DOMAIN = 10

def is_admin(user_id: int) -> bool:
    return not ADMIN_IDS or user_id in ADMIN_IDS

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("⚠️ Access restricted to Bot Owner.", show_alert=True)
        else:
            await update.message.reply_text("⚠️ Access restricted to Bot Owner.")
        return

    db: DatabaseManager = context.bot_data["db"]
    stats = await db.get_stats()

    admin_text = (
        "👑 <b>Owner Management Dashboard</b>\n"
        "<i>Owner ID: <code>8603872187</code></i>\n\n"
        f"👥 <b>Total Users:</b> {stats['users']} ({stats['approved_users']} Approved)\n"
        f"🌐 <b>Active Domains:</b> {stats['domains']}\n"
        f"⏳ <b>Active Temp Emails:</b> {stats['temp_aliases']}\n"
        f"♾️ <b>Active Perm Emails:</b> {stats['perm_aliases']}\n"
        f"📩 <b>Total Delivered Emails:</b> {stats['total_emails']}\n\n"
        "Select an action below:"
    )

    kbd = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Manage Allowed Users", callback_data="admin_users_list", style=KeyboardButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("Add Domain", callback_data="admin_add_domain", style=KeyboardButtonStyle.SUCCESS),
            InlineKeyboardButton("Remove Domain", callback_data="admin_remove_domain", style=KeyboardButtonStyle.DANGER)
        ],
        [
            InlineKeyboardButton("Run Expiry Cleanup", callback_data="admin_run_cleanup")
        ],
        [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
    ])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(admin_text, reply_markup=kbd, parse_mode="HTML")
    else:
        await update.message.reply_text(admin_text, reply_markup=kbd, parse_mode="HTML")

async def handle_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    db: DatabaseManager = context.bot_data["db"]
    users = await db.get_all_users()

    text = "👥 <b>Registered Bot Users:</b>\n\n"
    buttons = []

    for u in users:
        uid = u["telegram_id"]
        uname = f"@{u['username']}" if u["username"] else u["first_name"] or str(uid)
        
        if uid in ADMIN_IDS:
            badge = "👑 Owner"
        elif u["is_approved"]:
            badge = "✅ Approved"
        else:
            badge = "🔒 Pending"

        text += f"• <b>{uname}</b> (<code>{uid}</code>) — {badge}\n"

        if uid not in ADMIN_IDS:
            if u["is_approved"]:
                buttons.append([InlineKeyboardButton(f"Revoke {uname}", callback_data=f"admin_revoke:{uid}", style=KeyboardButtonStyle.DANGER)])
            else:
                buttons.append([InlineKeyboardButton(f"Grant {uname}", callback_data=f"admin_approve:{uid}", style=KeyboardButtonStyle.SUCCESS)])

    buttons.append([InlineKeyboardButton("Back to Admin", callback_data="admin_panel")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

async def handle_approve_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    db: DatabaseManager = context.bot_data["db"]
    _, target_id_str = query.data.split(":", 1)
    target_id = int(target_id_str)

    await db.approve_user(target_id)
    await query.answer(f"User {target_id} approved!", show_alert=True)

    # Notify approved user
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="🎉 <b>Access Granted by Bot Owner!</b>\nYou can now create emails on <code>hukam.bond</code>. Type /start to open the menu!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not notify user {target_id}: {e}")

    await handle_admin_panel(update, context)

async def handle_revoke_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    db: DatabaseManager = context.bot_data["db"]
    _, target_id_str = query.data.split(":", 1)
    target_id = int(target_id_str)

    await db.revoke_user(target_id)
    await query.answer(f"User {target_id} access revoked.", show_alert=True)
    await handle_admin_panel(update, context)

async def start_add_domain_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    await query.edit_message_text(
        "➕ <b>Add New Custom Domain</b>\n\nPlease send the domain name (e.g. <code>mydomain.com</code>):",
        reply_markup=get_back_button("admin_panel"),
        parse_mode="HTML"
    )
    return WAITING_ADD_DOMAIN

async def receive_add_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END

    db: DatabaseManager = context.bot_data["db"]
    domain_input = update.message.text.strip().lower()

    if "." not in domain_input or len(domain_input) < 4:
        await update.message.reply_text("❌ Invalid domain format. Example: <code>mydomain.com</code>", parse_mode="HTML")
        return WAITING_ADD_DOMAIN

    success = await db.add_domain(domain_input, user_id)
    if success:
        await update.message.reply_text(
            f"✅ <b>Domain <code>@{domain_input}</code> added!</b>",
            reply_markup=get_back_button("admin_panel"),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"⚠️ Domain <code>@{domain_input}</code> already exists.",
            reply_markup=get_back_button("admin_panel"),
            parse_mode="HTML"
        )

    return ConversationHandler.END

async def handle_remove_domain_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return

    db: DatabaseManager = context.bot_data["db"]
    domains = await db.get_active_domains()

    if not domains:
        await query.edit_message_text("No active domains to remove.", reply_markup=get_back_button("admin_panel"))
        return

    buttons = []
    for d in domains:
        buttons.append([InlineKeyboardButton(f"Delete @{d}", callback_data=f"del_domain:{d}", style=KeyboardButtonStyle.DANGER)])
    buttons.append([InlineKeyboardButton("Back to Admin", callback_data="admin_panel")])

    await query.edit_message_text(
        "🗑️ <b>Select domain to remove:</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )

async def handle_delete_domain_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    db: DatabaseManager = context.bot_data["db"]
    _, domain_name = query.data.split(":", 1)

    success = await db.delete_domain(domain_name)
    if success:
        await query.answer(f"Removed domain @{domain_name}", show_alert=True)
    else:
        await query.answer("Could not remove domain.", show_alert=True)

    await handle_admin_panel(update, context)

async def handle_manual_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    db: DatabaseManager = context.bot_data["db"]
    cleaned_count = await db.cleanup_expired_aliases()
    await query.answer(f"Cleanup complete! Deactivated {cleaned_count} expired temp emails.", show_alert=True)
    await handle_admin_panel(update, context)
