import aiosqlite
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = "data/trueblue.db"
    
    async def setup(self):
        """Inicializace databáze a vytvoření tabulek"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Tabulka pro nastavení serverů
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS guild_settings (
                        guild_id INTEGER PRIMARY KEY,
                        prefix TEXT DEFAULT '!',
                        mod_log_channel INTEGER,
                        welcome_channel INTEGER,
                        goodbye_channel INTEGER,
                        automod_enabled INTEGER DEFAULT 1,
                        welcome_message TEXT,
                        goodbye_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabulka pro tikety
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS tickets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        channel_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        ticket_type TEXT NOT NULL,
                        status TEXT DEFAULT 'open',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        closed_at TIMESTAMP,
                        closed_by INTEGER,
                        transcript TEXT,
                        UNIQUE(channel_id)
                    )
                ''')
                
                # Tabulka pro moderační logy
                await db.execute('''
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
                ''')
                
                # Tabulka pro varování
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS warnings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        moderator_id INTEGER NOT NULL,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.commit()
                logger.info("Databáze inicializována")
                
        except Exception as e:
            logger.error(f"Chyba při inicializaci databáze: {e}")
            raise
    
    # ========== GUILD SETTINGS ==========
    async def get_guild_settings(self, guild_id):
        """Získá nastavení guildy"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM guild_settings WHERE guild_id = ?",
                    (guild_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Chyba při získávání nastavení guildy: {e}")
            return None
    
    async def update_guild_setting(self, guild_id, key, value):
        """Aktualizuje nastavení guildy"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Zkontrolovat, zda guild již existuje
                settings = await self.get_guild_settings(guild_id)
                
                if settings:
                    # Aktualizovat existující
                    await db.execute(
                        f"UPDATE guild_settings SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
                        (value, guild_id)
                    )
                else:
                    # Vytvořit nový záznam
                    await db.execute(
                        f"INSERT INTO guild_settings (guild_id, {key}) VALUES (?, ?)",
                        (guild_id, value)
                    )
                
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Chyba při aktualizaci nastavení: {e}")
            return False
    
    # ========== TICKETS ==========
    async def create_ticket(self, guild_id, channel_id, user_id, ticket_type):
        """Vytvoří nový ticket"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO tickets (guild_id, channel_id, user_id, ticket_type) VALUES (?, ?, ?, ?)",
                    (guild_id, channel_id, user_id, ticket_type)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Chyba při vytváření ticketu: {e}")
            return False
    
    async def close_ticket(self, channel_id, closed_by):
        """Uzavře ticket"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE tickets SET status = 'closed', closed_at = CURRENT_TIMESTAMP, closed_by = ? WHERE channel_id = ?",
                    (closed_by, channel_id)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Chyba při uzavírání ticketu: {e}")
            return False
    
    # ========== MOD LOGS ==========
    async def add_mod_log(self, guild_id, user_id, moderator_id, action, reason, duration=None):
        """Přidá moderační log"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO mod_logs (guild_id, user_id, moderator_id, action, reason, duration) VALUES (?, ?, ?, ?, ?, ?)",
                    (guild_id, user_id, moderator_id, action, reason, duration)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Chyba při přidávání mod logu: {e}")
            return False
    
    async def get_user_mod_logs(self, guild_id, user_id, limit=10):
        """Získá moderační logy uživatele"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM mod_logs WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (guild_id, user_id, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Chyba při získávání mod logů: {e}")
            return []
    
    # ========== WARNINGS ==========
    async def add_warning(self, guild_id, user_id, moderator_id, reason):
        """Přidá varování uživateli"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                    (guild_id, user_id, moderator_id, reason)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Chyba při přidávání varování: {e}")
            return False
    
    async def get_user_warnings(self, guild_id, user_id):
        """Získá varování uživatele"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT COUNT(*) as count FROM warnings WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except Exception as e:
            logger.error(f"Chyba při získávání varování: {e}")
            return 0
    
    async def clear_warnings(self, guild_id, user_id):
        """Vymaže varování uživatele"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
                    (guild_id, user_id)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Chyba při mazání varování: {e}")
            return False