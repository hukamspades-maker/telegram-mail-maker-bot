import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Telegram Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8603872187").split(",") if x.strip().isdigit()]

# Default System Domains
DEFAULT_DOMAINS = [d.strip().lower() for d in os.getenv("DEFAULT_DOMAINS", "hukam.bond,jattjames.bond").split(",") if d.strip()]

# Webhook Server Settings (Uses Railway PORT dynamically if deployed)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("PORT", os.getenv("WEBHOOK_PORT", "8080")))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "jamesbond_hukam_secret_key")

# Database Configuration
default_db_dir = BASE_DIR / "data"
os.makedirs(default_db_dir, exist_ok=True)

DATABASE_PATH = os.getenv("DATABASE_PATH", str(default_db_dir / "mail_bot.db"))
db_parent = os.path.dirname(os.path.abspath(DATABASE_PATH))
if db_parent:
    os.makedirs(db_parent, exist_ok=True)

# App Settings
CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "5"))
