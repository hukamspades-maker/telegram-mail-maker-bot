from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

def get_main_menu_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("⚡ Quick Random Email", callback_data="select_domain:quick"),
            InlineKeyboardButton("✏️ Custom Prefix Email", callback_data="select_domain:custom")
        ],
        [
            InlineKeyboardButton("📬 My Active Emails", callback_data="mail_list"),
            InlineKeyboardButton("🔑 Login / Restore Email", callback_data="mail_login_key")
        ],
        [
            InlineKeyboardButton("ℹ️ Help & Info", callback_data="mail_help")
        ]
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("👑 Owner Admin Control", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def get_domain_selection_keyboard(action_type: str, domains: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    for d in domains:
        buttons.append([InlineKeyboardButton(f"🌐 @{d}", callback_data=f"do_mail:{action_type}:{d}")])
    buttons.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def get_back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]])
