import os
import aiosqlite
import random
import string
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Any

from config import DATABASE_PATH, DEFAULT_DOMAINS, ADMIN_IDS
from database.models import (
    CREATE_USERS_TABLE,
    CREATE_DOMAINS_TABLE,
    CREATE_ALIASES_TABLE,
    CREATE_EMAILS_TABLE,
    CREATE_INDEXES
)

logger = logging.getLogger(__name__)

def generate_security_key() -> str:
    chars = string.ascii_uppercase + string.digits
    rand = "".join(random.choice(chars) for _ in range(6))
    return f"KEY-{rand}"

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        # Parent directory is guaranteed by config.py

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_USERS_TABLE)
            await db.execute(CREATE_DOMAINS_TABLE)
            await db.execute(CREATE_ALIASES_TABLE)
            await db.execute(CREATE_EMAILS_TABLE)
            for idx in CREATE_INDEXES:
                await db.execute(idx)
            await db.commit()

            # Ensure columns exist (migration safeguards)
            try:
                await db.execute("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0;")
                await db.commit()
            except Exception:
                pass

            try:
                await db.execute("ALTER TABLE email_aliases ADD COLUMN security_key TEXT DEFAULT 'KEY-DEFAULT';")
                await db.commit()
            except Exception:
                pass

            # Seed default domains if empty
            async with db.execute("SELECT COUNT(*) FROM domains") as cursor:
                count = (await cursor.fetchone())[0]
                if count == 0:
                    for domain in DEFAULT_DOMAINS:
                        try:
                            await db.execute(
                                "INSERT INTO domains (domain_name, is_active) VALUES (?, 1)",
                                (domain.lower().strip(),)
                            )
                        except Exception as e:
                            logger.warning(f"Error seeding domain {domain}: {e}")
                    await db.commit()

    async def register_user(self, telegram_id: int, username: str = None, first_name: str = None) -> bool:
        is_owner_or_admin = 1 if telegram_id in ADMIN_IDS else 0
        is_approved = 1 if is_owner_or_admin else 0

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
                existing = await cur.fetchone()

            if not existing:
                await db.execute("""
                    INSERT INTO users (telegram_id, username, first_name, is_admin, is_approved)
                    VALUES (?, ?, ?, ?, ?)
                """, (telegram_id, username, first_name, is_owner_or_admin, is_approved))
                await db.commit()
                return not is_owner_or_admin
            else:
                await db.execute("""
                    UPDATE users SET 
                        username = ?, 
                        first_name = ?, 
                        is_admin = CASE WHEN telegram_id IN ({}) THEN 1 ELSE is_admin END,
                        is_approved = CASE WHEN telegram_id IN ({}) THEN 1 ELSE is_approved END
                    WHERE telegram_id = ?
                """.format(
                    ",".join(map(str, ADMIN_IDS)) if ADMIN_IDS else "0",
                    ",".join(map(str, ADMIN_IDS)) if ADMIN_IDS else "0"
                ), (username, first_name, telegram_id))
                await db.commit()
                return False

    async def is_user_approved(self, telegram_id: int) -> bool:
        if ADMIN_IDS and telegram_id in ADMIN_IDS:
            return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_approved FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
                row = await cur.fetchone()
                return bool(row[0]) if row else False

    async def approve_user(self, telegram_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("UPDATE users SET is_approved = 1 WHERE telegram_id = ?", (telegram_id,))
            await db.commit()
            return cur.rowcount > 0

    async def revoke_user(self, telegram_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("UPDATE users SET is_approved = 0 WHERE telegram_id = ? AND is_admin = 0", (telegram_id,))
            await db.commit()
            return cur.rowcount > 0

    async def get_all_users(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users ORDER BY created_at DESC") as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def get_active_domains(self) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT domain_name FROM domains WHERE is_active = 1") as cursor:
                rows = await cursor.fetchall()
                return [row["domain_name"] for row in rows]

    async def add_domain(self, domain_name: str, added_by: int) -> bool:
        domain_clean = domain_name.lower().strip()
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO domains (domain_name, added_by, is_active) VALUES (?, ?, 1)",
                    (domain_clean, added_by)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def delete_domain(self, domain_name: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM domains WHERE domain_name = ?", (domain_name.lower().strip(),))
            await db.commit()
            return cursor.rowcount > 0

    async def create_alias(
        self,
        user_id: int,
        address: str,
        domain: str,
        mail_type: str,
        duration_minutes: Optional[int] = None,
        custom_key: Optional[str] = None
    ) -> Dict[str, Any]:
        address_clean = address.lower().strip()
        sec_key = custom_key.strip().upper() if custom_key else generate_security_key()
        expires_at = None
        if mail_type == 'temp':
            minutes = duration_minutes if duration_minutes else 60
            expires_at = (datetime.utcnow() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                cursor = await db.execute("""
                    INSERT INTO email_aliases (address, user_id, domain, mail_type, security_key, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (address_clean, user_id, domain.lower(), mail_type, sec_key, expires_at))
                await db.commit()
                alias_id = cursor.lastrowid
                
                async with db.execute("SELECT * FROM email_aliases WHERE id = ?", (alias_id,)) as cur:
                    row = await cur.fetchone()
                    return dict(row)
            except aiosqlite.IntegrityError:
                raise ValueError("An email alias with this address already exists.")

    async def login_with_security_key(self, user_id: int, address: str, security_key: str) -> Optional[Dict[str, Any]]:
        address_clean = address.lower().strip()
        key_clean = security_key.strip().upper()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM email_aliases WHERE address = ? AND UPPER(security_key) = ?",
                (address_clean, key_clean)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                alias_dict = dict(row)
                await db.execute(
                    "UPDATE email_aliases SET user_id = ?, is_active = 1 WHERE id = ?",
                    (user_id, alias_dict["id"])
                )
                await db.execute(
                    "UPDATE received_emails SET user_id = ? WHERE alias_address = ?",
                    (user_id, address_clean)
                )
                await db.commit()

                alias_dict["user_id"] = user_id
                alias_dict["is_active"] = 1
                return alias_dict

    async def get_user_aliases(self, user_id: int) -> List[Dict[str, Any]]:
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT * FROM email_aliases 
                WHERE user_id = ? AND is_active = 1 
                AND (mail_type = 'permanent' OR expires_at > ?)
                ORDER BY id DESC
            """
            async with db.execute(query, (user_id, now_str)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_alias(self, address: str) -> Optional[Dict[str, Any]]:
        address_clean = address.lower().strip()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT * FROM email_aliases 
                WHERE address = ? AND is_active = 1 
                AND (mail_type = 'permanent' OR expires_at > ?)
            """
            async with db.execute(query, (address_clean, now_str)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def delete_alias(self, alias_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE email_aliases SET is_active = 0 WHERE id = ? AND user_id = ?",
                (alias_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def extend_alias_expiry(self, alias_id: int, user_id: int, hours: int = 24) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM email_aliases WHERE id = ? AND user_id = ? AND mail_type = 'temp'",
                (alias_id, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                curr_expiry = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
                now = datetime.utcnow()
                base_time = curr_expiry if curr_expiry > now else now
                new_expiry = base_time + timedelta(hours=hours)
                new_expiry_str = new_expiry.strftime("%Y-%m-%d %H:%M:%S")

                await db.execute(
                    "UPDATE email_aliases SET expires_at = ?, is_active = 1 WHERE id = ?",
                    (new_expiry_str, alias_id)
                )
                await db.commit()
                return new_expiry_str

    async def log_received_email(
        self,
        alias_address: str,
        user_id: int,
        sender: str,
        subject: str,
        body_text: str,
        body_html: str,
        has_attachments: bool = False
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO received_emails (alias_address, user_id, sender, subject, body_text, body_html, has_attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (alias_address.lower(), user_id, sender, subject, body_text, body_html, 1 if has_attachments else 0))
            
            await db.execute(
                "UPDATE email_aliases SET received_count = received_count + 1 WHERE address = ?",
                (alias_address.lower(),)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_user_emails(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT * FROM received_emails 
                WHERE user_id = ? 
                ORDER BY id DESC LIMIT ?
            """
            async with db.execute(query, (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_email_by_id(self, email_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM received_emails WHERE id = ? AND user_id = ?",
                (email_id, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def cleanup_expired_aliases(self) -> int:
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE email_aliases 
                SET is_active = 0 
                WHERE mail_type = 'temp' AND expires_at <= ? AND is_active = 1
            """, (now_str,))
            await db.commit()
            return cursor.rowcount

    async def get_stats(self) -> Dict[str, int]:
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            async with db.execute("SELECT COUNT(*) FROM users") as c:
                stats["users"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_approved = 1") as c:
                stats["approved_users"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM domains WHERE is_active = 1") as c:
                stats["domains"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM email_aliases WHERE mail_type = 'temp' AND is_active = 1") as c:
                stats["temp_aliases"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM email_aliases WHERE mail_type = 'permanent' AND is_active = 1") as c:
                stats["perm_aliases"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM received_emails") as c:
                stats["total_emails"] = (await c.fetchone())[0]
            return stats
