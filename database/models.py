CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    is_admin BOOLEAN DEFAULT 0,
    is_approved BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_DOMAINS_TABLE = """
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_name TEXT UNIQUE NOT NULL,
    added_by INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ALIASES_TABLE = """
CREATE TABLE IF NOT EXISTS email_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    domain TEXT NOT NULL,
    mail_type TEXT NOT NULL CHECK(mail_type IN ('temp', 'permanent')),
    security_key TEXT NOT NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    received_count INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(telegram_id)
);
"""

CREATE_EMAILS_TABLE = """
CREATE TABLE IF NOT EXISTS received_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_address TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    sender TEXT NOT NULL,
    subject TEXT,
    body_text TEXT,
    body_html TEXT,
    has_attachments BOOLEAN DEFAULT 0,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(telegram_id)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_alias_address ON email_aliases(address);",
    "CREATE INDEX IF NOT EXISTS idx_alias_user ON email_aliases(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_emails_alias ON received_emails(alias_address);",
    "CREATE INDEX IF NOT EXISTS idx_emails_user ON received_emails(user_id);"
]
