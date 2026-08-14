# 📬 Telegram Custom Domain Mail Maker Bot

A powerful, full-featured Telegram Bot to generate **unlimited temporary and permanent email addresses** on your custom domains. Incoming emails are processed in real-time and delivered straight into your Telegram chat with clean formatting and inline controls.

---

## ✨ Features

- ⚡ **1-Tap Quick Temp Mail**: Instantly generate random temporary email addresses with configurable expiry (10m, 1h, 24h, 7d).
- ✨ **Custom Username Support**: Create specific email prefixes (e.g. `john.sales@yourdomain.com` or `dev-test@mydomain.io`).
- ♾️ **Permanent Email Generation**: Create persistent aliases that never expire.
- 📩 **Real-Time Telegram Inbox**: Receive incoming emails directly in your Telegram chat with HTML/text cleaning, sender badges, and attachment lists.
- 🌐 **Multi-Domain Support**: Manage and create emails across multiple custom domains.
- ⚙️ **Admin Panel**: Manage system domains, monitor statistics, and run manual expiry cleanup.
- 🆓 **Zero-Cost Cloudflare Worker Integration**: Ingest unlimited emails for free without maintaining expensive mail servers!

---

## 📁 Project Structure

```
telegram-mail-maker-bot/
├── config.py                 # Bot configuration & environment variables
├── main.py                   # Main bot launcher (Telegram Bot + Webhook listener)
├── requirements.txt          # Python package dependencies
├── .env.example              # Sample environment configuration
├── database/
│   ├── models.py             # SQLite database schemas
│   └── db_manager.py         # Async SQLite database CRUD operations
├── bot/
│   ├── handlers/
│   │   ├── start.py          # /start & main menu commands
│   │   ├── create_mail.py    # Temp & Permanent mail creation wizards
│   │   ├── my_emails.py      # Active email management & copy/delete/extend
│   │   ├── domains.py        # Custom domain setup guides
│   │   └── admin.py          # System admin panel
│   └── keyboards.py          # Interactive inline keyboards
├── services/
│   ├── email_parser.py       # MIME parser & HTML-to-Telegram converter
│   ├── webhook_service.py    # Inbound email HTTP Webhook server (aiohttp)
│   └── imap_service.py       # Catch-All IMAP poller fallback
└── cloudflare/
    └── email_worker.js       # Deployable Cloudflare Email Worker snippet
```

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python 3.9+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- A Custom Domain (managed on Cloudflare or standard hosting)

### 2. Install Dependencies
```bash
cd telegram-mail-maker-bot
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your settings:
```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
ADMIN_IDS=YOUR_TELEGRAM_ID
DEFAULT_DOMAINS=yourcustomdomain.com,anotherdomain.io
WEBHOOK_PORT=8080
WEBHOOK_SECRET=your-secret-token
```

---

## 🌐 Custom Domain Setup (Choose Option A or B)

### Option A: Cloudflare Email Routing (Recommended & 100% Free)
1. Go to **Cloudflare Dashboard** -> Select your Domain -> **Email Routing**.
2. Enable Email Routing (Cloudflare will automatically configure MX and SPF records).
3. Go to **Workers & Pages** -> **Create Worker**.
4. Paste the code from `cloudflare/email_worker.js` into the worker editor.
5. In Worker **Settings** -> **Variables**, add:
   - `WEBHOOK_URL`: `https://your-server-ip-or-domain:8080/webhook/email`
   - `WEBHOOK_SECRET`: Matches `WEBHOOK_SECRET` in `.env`
6. In **Email Routing** -> **Routing Rules** -> **Catch-all Rule**:
   - Action: **Send to Worker**
   - Destination: Select your created Worker.

---

### Option B: Catch-All IMAP Inbox (cPanel / Hostinger / Namecheap)
1. Create a catch-all mailbox on your hosting provider (e.g. `catchall@yourdomain.com`).
2. Update `.env`:
   ```env
   IMAP_ENABLED=true
   IMAP_HOST=imap.yourdomain.com
   IMAP_PORT=993
   IMAP_USER=catchall@yourdomain.com
   IMAP_PASSWORD=your_password
   ```

---

## 🏃 Running the Bot

Run the main launcher:
```bash
python main.py
```

The bot will start Telegram polling, launch the inbound Webhook server on port 8080, and initiate the auto-cleanup background task!

---

## 🧪 Testing Verification

You can verify the database schema and email parser by running:
```bash
python -c "import asyncio, database.db_manager as db; asyncio.run(db.DatabaseManager().init_db()); print('Database OK!')"
```
