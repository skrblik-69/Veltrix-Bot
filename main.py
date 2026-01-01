import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
import logging
from database import Database
from utils.logging import setup_logging

# Nastavení logování
setup_logging()
logger = logging.getLogger(__name__)

# Načtení konfigurace
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Konfigurační soubor config.json nebyl nalezen!")
        return None

class TrueBlueBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.members = True
        
        self.config = load_config()
        if not self.config:
            raise Exception("Nepodařilo se načíst konfiguraci!")
        
        super().__init__(
            command_prefix=self.config['prefix'],
            intents=intents,
            help_command=None,
            case_insensitive=True,
            owner_ids=set(map(int, self.config.get('owner_ids', [])))
        )
        
        self.db = Database()
        self.mdt_data_path = "mdt/"
    
    async def setup_hook(self):
        """Inicializace databáze a načtení cogs"""
        await self.db.setup()
        
        # Vytvoření složky pro MDT data
        os.makedirs(self.mdt_data_path, exist_ok=True)
        
        # Načtení všech cogs
        cogs = [
            'cogs.moderation',
            'cogs.automod', 
            'cogs.tickets',
            'cogs.mdt',
            'cogs.utility'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Načten cog: {cog}")
            except Exception as e:
                logger.error(f"Chyba při načítání cog {cog}: {e}")
    
    async def on_ready(self):
        """Event když se bot připojí"""
        logger.info(f"{self.user} je připojen a připraven!")
        logger.info(f"Owners: {self.owner_ids}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"/nápověda | TrueBlue APP"
            )
        )
        
        # Synchronizace slash příkazů
        try:
            synced = await self.tree.sync()
            logger.info(f"Synchronizováno {len(synced)} slash příkazů")
        except Exception as e:
            logger.error(f"Chyba při synchronizaci slash příkazů: {e}")
    
    async def on_member_join(self, member):
        """Event při příchodu nového člena"""
        if 'Utility' in self.cogs:
            await self.cogs['Utility'].on_member_join(member)

async def main():
    """Hlavní funkce pro spuštění bota"""
    bot = TrueBlueBot()
    
    # Získání Discord tokenu z environment proměnných
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN nebyl nalezen v environment proměnných!")
        return
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Neplatný Discord token!")
    except Exception as e:
        logger.error(f"Chyba při spuštění bota: {e}")

if __name__ == "__main__":
    asyncio.run(main())