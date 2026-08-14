import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from bot.keyboards import get_back_button

async def handle_list_domains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db: DatabaseManager = context.bot_data["db"]

    domains = await db.get_active_domains()

    if not domains:
        text = "🌐 <b>No custom domains currently linked to the system!</b>"
    else:
        domain_items = "\n".join([f"• <code>@{html.escape(d)}</code>" for d in domains])
        text = (
            f"🌐 <b>Active Custom Domains ({len(domains)}):</b>\n\n"
            f"{domain_items}\n\n"
            f"<i>You can generate unlimited emails on any of the active domains listed above!</i>"
        )

    kbd = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Read Custom Domain Setup Guide", callback_data="domain_setup_guide")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ])

    await query.edit_message_text(text, reply_markup=kbd, parse_mode="HTML")

async def handle_domain_setup_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    guide_text = (
        "🛠️ <b>Custom Domain Setup Guide</b>\n\n"
        "To use your own domain (e.g. <code>yourdomain.com</code>) with this bot:\n\n"
        "<b>Option A: Cloudflare Email Routing (Recommended & Free)</b>\n"
        "1. Add your domain to Cloudflare DNS.\n"
        "2. Enable <b>Email Routing</b> in Cloudflare Dashboard.\n"
        "3. Create a Catch-all Routing Rule (`*@yourdomain.com`) pointing to the Cloudflare Worker script provided in `cloudflare/email_worker.js`.\n"
        "4. Set Worker environment variable `WEBHOOK_URL` to your bot server IP/domain.\n\n"
        "<b>Option B: Host Catch-All (cPanel / Namecheap / Hostinger)</b>\n"
        "1. Create a catch-all email mailbox on your host (e.g., `catchall@yourdomain.com`).\n"
        "2. Set `IMAP_ENABLED=true` in `.env` with your IMAP credentials.\n"
        "3. Add your domain in `/admin` domain settings!"
    )

    await query.edit_message_text(
        guide_text,
        reply_markup=get_back_button("mail_domains_list"),
        parse_mode="HTML"
    )
