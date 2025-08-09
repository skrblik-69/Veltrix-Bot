import discord
from discord.ext import commands
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
        # Používáme pouze základní intents bez privileged
        intents = discord.Intents.default()
        # intents.message_content = True  # Tento je také privileged
        intents.voice_states = True
        
        self.config = load_config()
        if not self.config:
            raise Exception("Nepodařilo se načíst konfiguraci!")
        
        super().__init__(
            command_prefix=self.config['prefix'],
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.db = Database()
    
    async def setup_hook(self):
        """Inicializace databáze a načtení cogs"""
        await self.db.setup()
        
        # Načtení všech cogs
        cogs = [
            'cogs.moderation',
            'cogs.automod', 
            'cogs.tickets',
            'cogs.economy',
            'cogs.music',
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
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{self.config.get('prefix', '!')}nápověda | TrueBlue APP"
            )
        )
        
        # Synchronizace slash příkazů
        try:
            synced = await self.tree.sync()
            logger.info(f"Synchronizováno {len(synced)} slash příkazů")
        except Exception as e:
            logger.error(f"Chyba při synchronizaci slash příkazů: {e}")
    
    async def on_message(self, message):
        """Zpracování zpráv"""
        if message.author.bot:
            return
            
        # Auto-moderace se zpracuje v automod cogu
        await self.process_commands(message)
    
    async def on_command_error(self, ctx, error):
        """Globální error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Nemáš dostatečná oprávnění pro tento příkaz!**")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ **Bot nemá dostatečná oprávnění pro provedení této akce!**")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ **Chybí povinný argument:** `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ **Neplatný argument! Zkontroluj formát příkazu.**")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ **Příkaz je na cooldownu! Zkus to za {error.retry_after:.1f} sekund.**")
        else:
            logger.error(f"Neočekávaná chyba v příkazu {ctx.command}: {error}")
            await ctx.send("❌ **Nastala neočekávaná chyba! Kontaktuj administrátora.**")

# Nápověda příkaz
@commands.command(name='nápověda', aliases=['help', 'pomoc'])
async def help_command(ctx, kategorie=None):
    """Zobrazí nápovědu k příkazům"""
    embed = discord.Embed(
        title="🔷 TrueBlue APP - Nápověda",
        description="Komplexní Discord bot pro moderaci, ekonomiku, hudbu a tikety",
        color=0x3498db
    )
    
    if not kategorie:
        embed.add_field(
            name="📋 Dostupné kategorie",
            value="🛡️ `moderace` - Moderační příkazy\n"
                  "🎫 `tikety` - Systém support tiketů\n"
                  "💰 `ekonomika` - Ekonomický systém\n"
                  "🎵 `hudba` - Přehrávání hudby\n"
                  "⚙️ `utility` - Užitečné nástroje\n\n"
                  f"Použij `{ctx.prefix}nápověda <kategorie>` pro detailní nápovědu",
            inline=False
        )
    else:
        # Zde by byly detaily podle kategorie
        embed.add_field(
            name=f"Kategorie: {kategorie}",
            value="Detailní nápověda k jednotlivým kategoriím je implementována v příslušných cogs.",
            inline=False
        )
    
    embed.set_footer(text="TrueBlue APP | Made by Skrblík")
    await ctx.send(embed=embed)

async def main():
    """Hlavní funkce pro spuštění bota"""
    bot = TrueBlueBot()
    bot.add_command(help_command)
    
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
