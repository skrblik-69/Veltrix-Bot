import discord
from discord.ext import commands
from discord import app_commands
import re
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class AutoMod(commands.Cog):
    """Automatická moderace pro detekci spamu a nevhodného obsahu"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_detection = defaultdict(lambda: deque(maxlen=10))
        self.user_warnings = defaultdict(int)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Kontrola každé zprávy na spam a nevhodný obsah"""
        if message.author.bot or not message.guild:
            return
        
        # Kontrola oprávnění - moderátoři jsou vynecháni
        if message.author.guild_permissions.manage_messages:
            return
        
        # Načtení nastavení
        settings = await self.bot.db.get_guild_settings(message.guild.id)
        if not settings or not settings.get('automod_enabled', True):
            return
        
        # Kontroly
        checks = [
            self._check_spam,
            self._check_bad_words,
            self._check_excessive_mentions,
            self._check_excessive_emojis,
            self._check_excessive_caps,
            self._check_repeated_characters
        ]
        
        for check in checks:
            if await check(message):
                return
    
    async def _check_spam(self, message):
        """Detekce spamu"""
        user_id = message.author.id
        guild_id = message.guild.id
        now = datetime.utcnow()
        
        # Přidání časového razítka
        self.spam_detection[f"{guild_id}_{user_id}"].append(now)
        
        # Kontrola rychlosti zpráv
        spam_threshold = self.bot.config['automod']['spam_threshold']
        spam_timeframe = self.bot.config['automod']['spam_timeframe']
        
        recent_messages = [
            timestamp for timestamp in self.spam_detection[f"{guild_id}_{user_id}"]
            if (now - timestamp).total_seconds() < spam_timeframe
        ]
        
        if len(recent_messages) >= spam_threshold:
            await self._handle_spam_violation(message, "Detekce spamu")
            return True
        
        return False
    
    async def _check_bad_words(self, message):
        """Kontrola na zakázaná slova"""
        bad_words = self.bot.config['automod']['bad_words']
        if not bad_words:
            return False
        
        content = message.content.lower()
        
        for word in bad_words:
            if word.lower() in content:
                await self._handle_content_violation(message, f"Nevhodné slovo: {word}")
                return True
        
        return False
    
    async def _check_excessive_mentions(self, message):
        """Kontrola na příliš mnoho zmínek"""
        max_mentions = self.bot.config['automod']['max_mentions']
        total_mentions = len(message.mentions) + len(message.role_mentions)
        
        if total_mentions > max_mentions:
            await self._handle_content_violation(message, f"Příliš mnoho zmínek ({total_mentions}/{max_mentions})")
            return True
        
        return False
    
    async def _check_excessive_emojis(self, message):
        """Kontrola na příliš mnoho emoji"""
        max_emojis = self.bot.config['automod']['max_emojis']
        
        # Počítání emoji
        custom_emojis = len(re.findall(r'<:\w*:\d*>', message.content))
        unicode_emojis = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', message.content))
        
        total_emojis = custom_emojis + unicode_emojis
        
        if total_emojis > max_emojis:
            await self._handle_content_violation(message, f"Příliš mnoho emoji ({total_emojis}/{max_emojis})")
            return True
        
        return False
    
    async def _check_excessive_caps(self, message):
        """Kontrola na příliš mnoho velkých písmen"""
        if len(message.content) < 5:
            return False
        
        max_caps_percentage = self.bot.config['automod']['max_caps_percentage']
        
        letters = [char for char in message.content if char.isalpha()]
        if not letters:
            return False
        
        caps_count = sum(1 for char in letters if char.isupper())
        caps_percentage = (caps_count / len(letters)) * 100
        
        if caps_percentage > max_caps_percentage:
            await self._handle_content_violation(message, f"Příliš mnoho velkých písmen ({caps_percentage:.1f}%)")
            return True
        
        return False
    
    async def _check_repeated_characters(self, message):
        """Kontrola na opakující se znaky"""
        if re.search(r'(.)\1{3,}', message.content):
            await self._handle_content_violation(message, "Opakující se znaky")
            return True
        
        return False
    
    async def _handle_spam_violation(self, message, reason):
        """Zpracování spam porušení"""
        try:
            await message.delete()
            
            user_key = f"{message.guild.id}_{message.author.id}"
            self.user_warnings[user_key] += 1
            warnings = self.user_warnings[user_key]
            
            if warnings == 1:
                embed = discord.Embed(
                    title="⚠️ Auto-moderace",
                    description=f"{message.author.mention}, tvá zpráva byla smazána.\n**Důvod:** {reason}",
                    color=0xf39c12
                )
                await message.channel.send(embed=embed, delete_after=10)
                
            elif warnings == 2:
                try:
                    await message.author.timeout(timedelta(minutes=5), reason=f"Auto-moderace: {reason}")
                    embed = discord.Embed(
                        title="🔇 Auto-moderace",
                        description=f"{message.author.mention} byl ztišen na 5 minut.\n**Důvod:** {reason}",
                        color=0xe74c3c
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                except:
                    pass
                    
            elif warnings >= 3:
                try:
                    await message.author.timeout(timedelta(minutes=30), reason=f"Auto-moderace: {reason}")
                    embed = discord.Embed(
                        title="🔇 Auto-moderace",
                        description=f"{message.author.mention} byl ztišen na 30 minut.\n**Důvod:** {reason} (opakované porušení)",
                        color=0x992d22
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                except:
                    pass
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                message.guild.id, message.author.id, self.bot.user.id, 
                "automod", f"{reason} - varování #{warnings}"
            )
            
        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"Chyba při zpracování spam porušení: {e}")
    
    async def _handle_content_violation(self, message, reason):
        """Zpracování porušení obsahu"""
        try:
            await message.delete()
            
            embed = discord.Embed(
                title="⚠️ Auto-moderace",
                description=f"{message.author.mention}, tvá zpráva byla smazána.\n**Důvod:** {reason}",
                color=0xf39c12
            )
            await message.channel.send(embed=embed, delete_after=8)
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                message.guild.id, message.author.id, self.bot.user.id, 
                "automod", reason
            )
            
        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"Chyba při zpracování porušení obsahu: {e}")
    
    @app_commands.command(name="automod", description="Nastavení auto-moderace")
    @app_commands.default_permissions(manage_guild=True)
    async def automod_settings(self, interaction: discord.Interaction):
        """Zobrazí nastavení auto-moderace"""
        settings = await self.bot.db.get_guild_settings(interaction.guild.id)
        automod_enabled = settings.get('automod_enabled', True) if settings else True
        
        embed = discord.Embed(
            title="🤖 Nastavení Auto-moderace",
            description=f"**Stav:** {'🟢 Zapnuto' if automod_enabled else '🔴 Vypnuto'}",
            color=0x3498db
        )
        
        embed.add_field(
            name="⚙️ Aktuální nastavení",
            value=f"• Spam práh: {self.bot.config['automod']['spam_threshold']} zpráv/{self.bot.config['automod']['spam_timeframe']}s\n"
                  f"• Max. zmínky: {self.bot.config['automod']['max_mentions']}\n"
                  f"• Max. emoji: {self.bot.config['automod']['max_emojis']}\n"
                  f"• Max. velká písmena: {self.bot.config['automod']['max_caps_percentage']}%",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))