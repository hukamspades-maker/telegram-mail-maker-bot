from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import KeyboardButtonStyle
from typing import List

def get_main_menu_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("Quick Random Email", callback_data="do_mail:quick:hukam.bond", style=KeyboardButtonStyle.PRIMARY),
            InlineKeyboardButton("Custom Prefix Email", callback_data="do_mail:custom:hukam.bond", style=KeyboardButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton("My Active Emails", callback_data="mail_list", style=KeyboardButtonStyle.SUCCESS),
            InlineKeyboardButton("Login / Restore Email", callback_data="mail_login_key", style=KeyboardButtonStyle.SUCCESS)
        ],
        [
            InlineKeyboardButton("Help & Info", callback_data="mail_help", style=KeyboardButtonStyle.DANGER)
        ]
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("Owner Admin Control", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def get_domain_selection_keyboard(action_type: str, domains: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    for d in domains:
        buttons.append([InlineKeyboardButton(f"@{d}", callback_data=f"do_mail:{action_type}:{d}", style=KeyboardButtonStyle.PRIMARY)])
    buttons.append([InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def get_back_button(back_target: str = "main_menu") -> InlineKeyboardMarkup:
    label = "Back to Main Menu" if back_target == "main_menu" else "Back"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=back_target)]])

