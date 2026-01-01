import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import logging
from utils.helpers import parse_time_string, format_time_delta

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    """Moderační příkazy pro správu serveru"""
    
    def __init__(self, bot):
        self.bot = bot
    
    # ========== KICK ==========
    @app_commands.command(name="vykopnout", description="Vykopne člena ze serveru")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(člen="Člen k vykopnutí", důvod="Důvod vykopnutí")
    async def kick_slash(self, interaction: discord.Interaction, člen: discord.Member, důvod: str = "Nebyl uveden důvod"):
        """Vykopne člena ze serveru"""
        await interaction.response.defer()
        
        # Kontroly
        if člen.top_role >= interaction.user.top_role:
            await interaction.followup.send("❌ **Nemůžeš vykopnout člena s vyšší nebo stejnou rolí!**", ephemeral=True)
            return
        
        if člen == interaction.guild.owner:
            await interaction.followup.send("❌ **Nemůžeš vykopnout vlastníka serveru!**", ephemeral=True)
            return
        
        if člen == interaction.user:
            await interaction.followup.send("❌ **Nemůžeš vykopnout sám sebe!**", ephemeral=True)
            return
        
        try:
            # DM před vykopnutím
            try:
                embed = discord.Embed(
                    title="🦶 Byl jsi vykopnut",
                    description=f"**Server:** {interaction.guild.name}\n**Důvod:** {důvod}",
                    color=0xe74c3c,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Moderátor: {interaction.user}")
                await člen.send(embed=embed)
            except:
                pass
            
            # Vykopnutí
            await člen.kick(reason=f"{interaction.user}: {důvod}")
            
            # Log embed
            embed = discord.Embed(
                title="✅ Člen vykopnut",
                description=f"**Člen:** {člen.mention}\n**ID:** `{člen.id}`\n**Důvod:** {důvod}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Moderátor: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
            # Mod log
            await self._send_mod_log(interaction.guild, "kick", člen, interaction.user, důvod)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ **Nemám oprávnění k vykopnutí tohoto člena!**", ephemeral=True)
        except Exception as e:
            logger.error(f"Chyba při vykopávání: {e}")
            await interaction.followup.send("❌ **Nastala chyba při vykopávání!**", ephemeral=True)
    
    # ========== BAN ==========
    @app_commands.command(name="ban", description="Zabanuje člena na serveru")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(člen="Člen k zabanování", důvod="Důvod banu", smazat_zprávy="Smazat zprávy (dny)")
    async def ban_slash(self, interaction: discord.Interaction, člen: discord.Member, 
                       důvod: str = "Nebyl uveden důvod", smazat_zprávy: int = 0):
        """Zabanuje člena na serveru"""
        await interaction.response.defer()
        
        # Kontroly
        if člen.top_role >= interaction.user.top_role:
            await interaction.followup.send("❌ **Nemůžeš zabanovat člena s vyšší nebo stejnou rolí!**", ephemeral=True)
            return
        
        if člen == interaction.guild.owner:
            await interaction.followup.send("❌ **Nemůžeš zabanovat vlastníka serveru!**", ephemeral=True)
            return
        
        if člen == interaction.user:
            await interaction.followup.send("❌ **Nemůžeš zabanovat sám sebe!**", ephemeral=True)
            return
        
        try:
            # DM před banem
            try:
                embed = discord.Embed(
                    title="🔨 Byl jsi zabanován",
                    description=f"**Server:** {interaction.guild.name}\n**Důvod:** {důvod}",
                    color=0x992d22,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Moderátor: {interaction.user}")
                await člen.send(embed=embed)
            except:
                pass
            
            # Ban
            delete_days = max(0, min(7, smazat_zprávy))
            await člen.ban(reason=f"{interaction.user}: {důvod}", delete_message_days=delete_days)
            
            # Log embed
            embed = discord.Embed(
                title="✅ Člen zabanován",
                description=f"**Člen:** {člen.mention}\n**ID:** `{člen.id}`\n**Důvod:** {důvod}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            if delete_days > 0:
                embed.add_field(name="Smazané zprávy", value=f"{delete_days} dní", inline=True)
            
            embed.set_footer(text=f"Moderátor: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
            # Mod log
            await self._send_mod_log(interaction.guild, "ban", člen, interaction.user, důvod)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ **Nemám oprávnění k zabanování tohoto člena!**", ephemeral=True)
        except Exception as e:
            logger.error(f"Chyba při banování: {e}")
            await interaction.followup.send("❌ **Nastala chyba při banování!**", ephemeral=True)
    
    # ========== TIMEOUT ==========
    @app_commands.command(name="ztišit", description="Ztíší člena (timeout)")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(člen="Člen k ztišení", doba="Doba ztišení (např. 10m, 1h, 2d)", důvod="Důvod ztišení")
    async def timeout_slash(self, interaction: discord.Interaction, člen: discord.Member, 
                           doba: str, důvod: str = "Nebyl uveden důvod"):
        """Ztíší člena (timeout)"""
        await interaction.response.defer()
        
        # Kontroly
        if člen.top_role >= interaction.user.top_role:
            await interaction.followup.send("❌ **Nemůžeš ztišit člena s vyšší nebo stejnou rolí!**", ephemeral=True)
            return
        
        if člen == interaction.guild.owner:
            await interaction.followup.send("❌ **Nemůžeš ztišit vlastníka serveru!**", ephemeral=True)
            return
        
        if člen == interaction.user:
            await interaction.followup.send("❌ **Nemůžeš ztišit sám sebe!**", ephemeral=True)
            return
        
        try:
            # Parsování času
            duration = parse_time_string(doba)
            
            # Max timeout 28 dní
            if duration > timedelta(days=28):
                await interaction.followup.send("❌ **Maximální doba timeoutu je 28 dní!**", ephemeral=True)
                return
            
            # Timeout
            await člen.timeout(duration, reason=f"{interaction.user}: {důvod}")
            
            # Formátování času pro zobrazení
            formatted_duration = format_time_delta(duration)
            
            # Log embed
            embed = discord.Embed(
                title="🔇 Člen ztišen",
                description=f"**Člen:** {člen.mention}\n**Doba:** {formatted_duration}\n**Důvod:** {důvod}",
                color=0xf39c12,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Moderátor: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
            # Mod log
            await self._send_mod_log(interaction.guild, "timeout", člen, interaction.user, důvod, formatted_duration)
            
        except Exception as e:
            logger.error(f"Chyba při ztišení: {e}")
            await interaction.followup.send(f"❌ **Chyba: {str(e)}**", ephemeral=True)
    
    # ========== UNTIMEOUT ==========
    @app_commands.command(name="zrušit_ztišení", description="Zruší ztišení člena")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(člen="Člen ke zrušení ztišení", důvod="Důvod zrušení")
    async def untimeout_slash(self, interaction: discord.Interaction, člen: discord.Member, 
                             důvod: str = "Nebyl uveden důvod"):
        """Zruší ztišení člena"""
        await interaction.response.defer()
        
        if not člen.is_timed_out():
            await interaction.followup.send("❌ **Tento člen není ztišen!**", ephemeral=True)
            return
        
        try:
            # Zrušení timeoutu
            await člen.timeout(None, reason=f"{interaction.user}: {důvod}")
            
            embed = discord.Embed(
                title="🔊 Ztišení zrušeno",
                description=f"**Člen:** {člen.mention}\n**Důvod:** {důvod}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Moderátor: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
            # Mod log
            await self._send_mod_log(interaction.guild, "untimeout", člen, interaction.user, důvod)
            
        except Exception as e:
            logger.error(f"Chyba při rušení ztišení: {e}")
            await interaction.followup.send("❌ **Nastala chyba při rušení ztišení!**", ephemeral=True)
    
    # ========== CLEAR ==========
    @app_commands.command(name="smazat", description="Smaže zprávy v kanálu")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(počet="Počet zpráv ke smazání (1-100)")
    async def clear_slash(self, interaction: discord.Interaction, počet: app_commands.Range[int, 1, 100]):
        """Smaže zprávy v kanálu"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=počet)
            
            embed = discord.Embed(
                title="🧹 Zprávy smazány",
                description=f"**Smazáno:** {len(deleted)} zpráv",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Moderátor: {interaction.user}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ **Nemám oprávnění ke smazání zpráv!**", ephemeral=True)
        except Exception as e:
            logger.error(f"Chyba při mazání zpráv: {e}")
            await interaction.followup.send("❌ **Nastala chyba při mazání zpráv!**", ephemeral=True)
    
    # ========== WARN ==========
    @app_commands.command(name="varování", description="Udělí varování členovi")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(člen="Člen k varování", důvod="Důvod varování")
    async def warn_slash(self, interaction: discord.Interaction, člen: discord.Member, 
                        důvod: str = "Nebyl uveden důvod"):
        """Udělí varování členovi"""
        await interaction.response.defer()
        
        # Kontroly
        if člen.top_role >= interaction.user.top_role:
            await interaction.followup.send("❌ **Nemůžeš varovat člena s vyšší nebo stejnou rolí!**", ephemeral=True)
            return
        
        if člen == interaction.user:
            await interaction.followup.send("❌ **Nemůžeš varovat sám sebe!**", ephemeral=True)
            return
        
        try:
            # DM s varováním
            try:
                embed = discord.Embed(
                    title="⚠️ Obdržel jsi varování",
                    description=f"**Server:** {interaction.guild.name}\n**Důvod:** {důvod}",
                    color=0xf39c12,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Moderátor: {interaction.user}")
                await člen.send(embed=embed)
            except:
                pass
            
            # Log embed
            embed = discord.Embed(
                title="⚠️ Varování uděleno",
                description=f"**Člen:** {člen.mention}\n**Důvod:** {důvod}",
                color=0xf39c12,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Moderátor: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
            # Mod log
            await self._send_mod_log(interaction.guild, "warn", člen, interaction.user, důvod)
            
        except Exception as e:
            logger.error(f"Chyba při udělování varování: {e}")
            await interaction.followup.send("❌ **Nastala chyba při udělování varování!**", ephemeral=True)
    
    # ========== LOCK/UNLOCK ==========
    @app_commands.command(name="zamknout", description="Zamkne aktuální kanál")
    @app_commands.default_permissions(manage_channels=True)
    async def lock_slash(self, interaction: discord.Interaction):
        """Zamkne aktuální kanál"""
        await interaction.response.defer()
        
        try:
            overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = False
            await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(
                title="🔒 Kanál zamčen",
                description="Tento kanál byl zamčen. Pouze administrátoři mohou psát.",
                color=0xe74c3c
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při zamčení kanálu: {e}")
            await interaction.followup.send("❌ **Nastala chyba při zamčení kanálu!**", ephemeral=True)
    
    @app_commands.command(name="odemknout", description="Odemkne aktuální kanál")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock_slash(self, interaction: discord.Interaction):
        """Odemkne aktuální kanál"""
        await interaction.response.defer()
        
        try:
            overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
            overwrite.send_messages = True
            await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            
            embed = discord.Embed(
                title="🔓 Kanál odemčen",
                description="Tento kanál byl odemčen. Všichni mohou psát.",
                color=0x2ecc71
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při odemčení kanálu: {e}")
            await interaction.followup.send("❌ **Nastala chyba při odemčení kanálu!**", ephemeral=True)
    
    # ========== SLOWMODE ==========
    @app_commands.command(name="zpomalit", description="Nastaví slowmode v kanálu")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.describe(doba="Doba slowmode v sekundách (0-21600)")
    async def slowmode_slash(self, interaction: discord.Interaction, doba: app_commands.Range[int, 0, 21600]):
        """Nastaví slowmode v kanálu"""
        await interaction.response.defer()
        
        try:
            await interaction.channel.edit(slowmode_delay=doba)
            
            if doba == 0:
                embed = discord.Embed(
                    title="🐢 Slowmode vypnut",
                    description="Slowmode byl vypnut v tomto kanálu.",
                    color=0x2ecc71
                )
            else:
                minutes, seconds = divmod(doba, 60)
                hours, minutes = divmod(minutes, 60)
                
                time_str = ""
                if hours > 0:
                    time_str += f"{hours}h "
                if minutes > 0:
                    time_str += f"{minutes}m "
                if seconds > 0:
                    time_str += f"{seconds}s"
                
                embed = discord.Embed(
                    title="🐢 Slowmode nastaven",
                    description=f"Slowmode nastaven na **{time_str.strip()}**",
                    color=0xf39c12
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při nastavení slowmode: {e}")
            await interaction.followup.send("❌ **Nastala chyba při nastavení slowmode!**", ephemeral=True)
    
    # ========== MOD LOG ==========
    async def _send_mod_log(self, guild, action, user, moderator, reason, duration=None):
        """Pošle moderační log do log kanálu"""
        try:
            # ID log kanálu z configu
            log_channel_id = self.bot.config.get('mod_log_channel')
            if not log_channel_id:
                return
            
            channel = guild.get_channel(int(log_channel_id))
            if not channel:
                return
            
            # Barvy a emoji
            color_map = {
                'kick': 0xe74c3c,
                'ban': 0x992d22,
                'timeout': 0xf39c12,
                'untimeout': 0x2ecc71,
                'warn': 0xf39c12,
                'mute': 0xf39c12,
                'unmute': 0x2ecc71
            }
            
            action_names = {
                'kick': '🦶 Vykopnutí',
                'ban': '🔨 Ban',
                'timeout': '🔇 Timeout',
                'untimeout': '🔊 Zrušení timeoutu',
                'warn': '⚠️ Varování',
                'mute': '🔇 Ztišení',
                'unmute': '🔊 Zrušení ztišení'
            }
            
            embed = discord.Embed(
                title=action_names.get(action, f"📋 {action}"),
                color=color_map.get(action, 0x3498db),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="👤 Uživatel", value=f"{user.mention}\n`{user.id}`", inline=True)
            embed.add_field(name="🛡️ Moderátor", value=f"{moderator.mention}\n`{moderator.id}`", inline=True)
            embed.add_field(name="📝 Důvod", value=reason, inline=False)
            
            if duration:
                embed.add_field(name="⏰ Doba", value=duration, inline=True)
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při odesílání mod logu: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))