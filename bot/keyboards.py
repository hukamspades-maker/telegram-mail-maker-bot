from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("⚡ Quick Random Mail", callback_data="mail_quick"),
            InlineKeyboardButton("✏️ Custom Prefix Mail", callback_data="mail_custom")
        ],
        [
            InlineKeyboardButton("📋 My Emails", callback_data="mail_list"),
            InlineKeyboardButton("🔑 Login / Restore Email", callback_data="mail_login_key")
        ]
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("👑 Owner Users Control", callback_data="admin_users_list")])
    return InlineKeyboardMarkup(buttons)

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]])
