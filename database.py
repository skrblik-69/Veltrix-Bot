import sqlite3
import asyncio
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "trueblue.db"):
        self.db_path = db_path
        self._connection = None
    
    async def setup(self):
        """Inicializace databáze a vytvoření tabulek"""
        try:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            await self._create_tables()
            logger.info("Databáze byla úspěšně inicializována")
        except Exception as e:
            logger.error(f"Chyba při inicializaci databáze: {e}")
            raise
    
    async def _create_tables(self):
        """Vytvoření všech potřebných tabulek"""
        if not self._connection:
            raise Exception("Databáze není připojena")
            
        tables = [
            # Uživatelé a ekonomika
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                balance INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                daily_last TIMESTAMP,
                work_last TIMESTAMP,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Moderační logy
            """
            CREATE TABLE IF NOT EXISTS mod_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                duration INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Tikety
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                closed_by INTEGER
            )
            """,
            
            # Nastavení guildy
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                mod_log_channel INTEGER,
                mute_role INTEGER,
                automod_enabled INTEGER DEFAULT 1,
                welcome_channel INTEGER,
                goodbye_channel INTEGER,
                welcome_message TEXT,
                goodbye_message TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Auto-mod varování
            """
            CREATE TABLE IF NOT EXISTS automod_warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                warning_type TEXT NOT NULL,
                message_count INTEGER DEFAULT 1,
                last_warning TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Hudební fronty
            """
            CREATE TABLE IF NOT EXISTS music_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                requester_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        cursor = self._connection.cursor()
        for table_sql in tables:
            cursor.execute(table_sql)
        self._connection.commit()
    
    # Ekonomické funkce
    async def get_user_economy(self, user_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """Získání ekonomických dat uživatele"""
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        result = cursor.fetchone()
        return dict(result) if result else None
    
    async def create_user_economy(self, user_id: int, guild_id: int) -> bool:
        """Vytvoření ekonomického profilu uživatele"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, guild_id) VALUES (?, ?)",
                (user_id, guild_id)
            )
            self._connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Chyba při vytváření uživatelského profilu: {e}")
            return False
    
    async def update_balance(self, user_id: int, guild_id: int, amount: int) -> bool:
        """Aktualizace zůstatku uživatele"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ? AND guild_id = ?",
                (amount, user_id, guild_id)
            )
            self._connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Chyba při aktualizaci zůstatku: {e}")
            return False
    
    # Moderační funkce
    async def add_mod_log(self, guild_id: int, user_id: int, moderator_id: int, 
                         action: str, reason: str = None, duration: int = None) -> bool:
        """Přidání moderačního logu"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                """INSERT INTO mod_logs (guild_id, user_id, moderator_id, action, reason, duration)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (guild_id, user_id, moderator_id, action, reason, duration)
            )
            self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Chyba při přidávání mod logu: {e}")
            return False
    
    async def get_user_warnings(self, user_id: int, guild_id: int) -> int:
        """Získání počtu varování uživatele"""
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT warnings FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    
    async def add_warning(self, user_id: int, guild_id: int) -> bool:
        """Přidání varování uživateli"""
        try:
            await self.create_user_economy(user_id, guild_id)
            cursor = self._connection.cursor()
            cursor.execute(
                "UPDATE users SET warnings = warnings + 1 WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            )
            self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Chyba při přidávání varování: {e}")
            return False
    
    # Ticket funkce
    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int, category: str) -> bool:
        """Vytvoření nového tiketu"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "INSERT INTO tickets (guild_id, channel_id, user_id, category) VALUES (?, ?, ?, ?)",
                (guild_id, channel_id, user_id, category)
            )
            self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Chyba při vytváření tiketu: {e}")
            return False
    
    async def close_ticket(self, channel_id: int, closed_by: int) -> bool:
        """Uzavření tiketu"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP, closed_by = ? WHERE channel_id = ?",
                (closed_by, channel_id)
            )
            self._connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Chyba při uzavírání tiketu: {e}")
            return False
    
    # Guild nastavení
    async def get_guild_settings(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Získání nastavení guildy"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    async def update_guild_setting(self, guild_id: int, setting: str, value: Any) -> bool:
        """Aktualizace nastavení guildy"""
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                f"INSERT OR REPLACE INTO guild_settings (guild_id, {setting}) VALUES (?, ?)",
                (guild_id, value)
            )
            self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Chyba při aktualizaci nastavení guildy: {e}")
            return False
    
    def close(self):
        """Uzavření databázového spojení"""
        if self._connection:
            self._connection.close()
