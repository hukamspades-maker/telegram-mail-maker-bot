import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Telegram Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8603872187").split(",") if x.strip().isdigit()]

# Default System Domains
DEFAULT_DOMAINS = [d.strip().lower() for d in os.getenv("DEFAULT_DOMAINS", "hukam.bond").split(",") if d.strip()]

# Webhook Server Settings (Uses Railway PORT dynamically if deployed)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8080")))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "jamesbond_hukam_secret_key")

# IMAP Configuration (Optional)
IMAP_ENABLED = os.getenv("IMAP_ENABLED", "false").lower() in ("true", "1", "yes")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.hukam.bond")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "catchall@hukam.bond")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "secret")
IMAP_POLL_INTERVAL = int(os.getenv("IMAP_POLL_INTERVAL", "15"))

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "mail_bot.db"))

# App Settings
CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "5"))
