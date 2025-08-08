import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    """Moderační příkazy pro správu serveru"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='vykopnout', aliases=['kick'])
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, člen: discord.Member, *, důvod="Nebyl uveden důvod"):
        """Vykopne člena ze serveru"""
        if člen.top_role >= ctx.author.top_role:
            return await ctx.send("❌ **Nemůžeš vykopnout člena s vyšší nebo stejnou rolí!**")
        
        if člen == ctx.guild.owner:
            return await ctx.send("❌ **Nemůžeš vykopnout vlastníka serveru!**")
        
        try:
            # Pošleme DM před vykopnutím
            try:
                embed = discord.Embed(
                    title="🦶 Byl jsi vykopnut",
                    description=f"**Server:** {ctx.guild.name}\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                    color=0xe74c3c,
                    timestamp=datetime.utcnow()
                )
                await člen.send(embed=embed)
            except:
                pass
            
            await člen.kick(reason=f"Vykopnut moderátorem {ctx.author}: {důvod}")
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                ctx.guild.id, člen.id, ctx.author.id, "kick", důvod
            )
            
            embed = discord.Embed(
                title="✅ Člen vykopnut",
                description=f"**Člen:** {člen} (`{člen.id}`)\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            
            # Log kanál
            await self._send_mod_log(ctx.guild, "kick", člen, ctx.author, důvod)
            
        except discord.Forbidden:
            await ctx.send("❌ **Nemám oprávnění k vykopnutí tohoto člena!**")
        except Exception as e:
            logger.error(f"Chyba při vykopávání: {e}")
            await ctx.send("❌ **Nastala chyba při vykopávání člena!**")
    
    @commands.hybrid_command(name='ban', aliases=['zabanovat'])
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, člen: discord.Member, *, důvod="Nebyl uveden důvod"):
        """Zabanuje člena na serveru"""
        if člen.top_role >= ctx.author.top_role:
            return await ctx.send("❌ **Nemůžeš zabanovat člena s vyšší nebo stejnou rolí!**")
        
        if člen == ctx.guild.owner:
            return await ctx.send("❌ **Nemůžeš zabanovat vlastníka serveru!**")
        
        try:
            # Pošleme DM před banem
            try:
                embed = discord.Embed(
                    title="🔨 Byl jsi zabanován",
                    description=f"**Server:** {ctx.guild.name}\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                    color=0x992d22,
                    timestamp=datetime.utcnow()
                )
                await člen.send(embed=embed)
            except:
                pass
            
            await člen.ban(reason=f"Zabanován moderátorem {ctx.author}: {důvod}")
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                ctx.guild.id, člen.id, ctx.author.id, "ban", důvod
            )
            
            embed = discord.Embed(
                title="✅ Člen zabanován",
                description=f"**Člen:** {člen} (`{člen.id}`)\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            
            # Log kanál
            await self._send_mod_log(ctx.guild, "ban", člen, ctx.author, důvod)
            
        except discord.Forbidden:
            await ctx.send("❌ **Nemám oprávnění k zabanování tohoto člena!**")
        except Exception as e:
            logger.error(f"Chyba při banování: {e}")
            await ctx.send("❌ **Nastala chyba při banování člena!**")
    
    @commands.hybrid_command(name='unban', aliases=['odbanovat'])
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx, uživatel_id: str, *, důvod="Nebyl uveden důvod"):
        """Odbanuje uživatele podle ID"""
        try:
            user_id = int(uživatel_id)
            user = await self.bot.fetch_user(user_id)
            
            await ctx.guild.unban(user, reason=f"Odbanován moderátorem {ctx.author}: {důvod}")
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                ctx.guild.id, user.id, ctx.author.id, "unban", důvod
            )
            
            embed = discord.Embed(
                title="✅ Uživatel odbanován",
                description=f"**Uživatel:** {user} (`{user.id}`)\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ **Neplatné ID uživatele!**")
        except discord.NotFound:
            await ctx.send("❌ **Uživatel nebyl nalezen nebo není zabanován!**")
        except Exception as e:
            logger.error(f"Chyba při odbanování: {e}")
            await ctx.send("❌ **Nastala chyba při odbanování uživatele!**")
    
    @commands.hybrid_command(name='ztišit', aliases=['mute'])
    @commands.has_permissions(manage_messages=True)
    async def mute_member(self, ctx, člen: discord.Member, doba: str = None, *, důvod="Nebyl uveden důvod"):
        """Ztíší člena (timeout)"""
        if člen.top_role >= ctx.author.top_role:
            return await ctx.send("❌ **Nemůžeš ztišit člena s vyšší nebo stejnou rolí!**")
        
        # Parsování času
        duration = None
        if doba:
            try:
                duration = self._parse_time(doba)
            except ValueError:
                return await ctx.send("❌ **Neplatný formát času! Použij např. 10m, 1h, 1d**")
        else:
            duration = timedelta(minutes=10)  # Výchozí 10 minut
        
        try:
            await člen.timeout(duration, reason=důvod)
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                ctx.guild.id, člen.id, ctx.author.id, "mute", důvod, int(duration.total_seconds())
            )
            
            embed = discord.Embed(
                title="🔇 Člen ztišen",
                description=f"**Člen:** {člen}\n**Doba:** {doba or '10m'}\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                color=0xf39c12,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            
            # Log kanál
            await self._send_mod_log(ctx.guild, "mute", člen, ctx.author, důvod, doba)
            
        except discord.Forbidden:
            await ctx.send("❌ **Nemám oprávnění k ztišení tohoto člena!**")
        except Exception as e:
            logger.error(f"Chyba při ztišení: {e}")
            await ctx.send("❌ **Nastala chyba při ztišení člena!**")
    
    @commands.hybrid_command(name='zrušit_ztišení', aliases=['unmute'])
    @commands.has_permissions(manage_messages=True)
    async def unmute_member(self, ctx, člen: discord.Member, *, důvod="Nebyl uveden důvod"):
        """Zruší ztišení člena"""
        try:
            await člen.timeout(None, reason=důvod)
            
            # Log do databáze
            await self.bot.db.add_mod_log(
                ctx.guild.id, člen.id, ctx.author.id, "unmute", důvod
            )
            
            embed = discord.Embed(
                title="🔊 Ztišení zrušeno",
                description=f"**Člen:** {člen}\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při rušení ztišení: {e}")
            await ctx.send("❌ **Nastala chyba při rušení ztišení!**")
    
    @commands.hybrid_command(name='varování', aliases=['warn'])
    @commands.has_permissions(manage_messages=True)
    async def warn_member(self, ctx, člen: discord.Member, *, důvod="Nebyl uveden důvod"):
        """Udělí varování členovi"""
        try:
            # Přidání varování do DB
            await self.bot.db.add_warning(člen.id, ctx.guild.id)
            await self.bot.db.add_mod_log(
                ctx.guild.id, člen.id, ctx.author.id, "warn", důvod
            )
            
            # Získání celkového počtu varování
            warnings_count = await self.bot.db.get_user_warnings(člen.id, ctx.guild.id)
            
            # Pošleme DM
            try:
                embed = discord.Embed(
                    title="⚠️ Obdržel jsi varování",
                    description=f"**Server:** {ctx.guild.name}\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}\n**Celkem varování:** {warnings_count}",
                    color=0xf39c12,
                    timestamp=datetime.utcnow()
                )
                await člen.send(embed=embed)
            except:
                pass
            
            embed = discord.Embed(
                title="⚠️ Varování uděleno",
                description=f"**Člen:** {člen}\n**Důvod:** {důvod}\n**Moderátor:** {ctx.author}\n**Celkem varování:** {warnings_count}",
                color=0xf39c12,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed)
            
            # Automatická akce při více varováních
            if warnings_count >= 3:
                try:
                    await člen.timeout(timedelta(hours=1), reason="3+ varování - automatické ztišení")
                    await ctx.send(f"🔇 **{člen} byl automaticky ztišen na 1 hodinu (3+ varování)!**")
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Chyba při udělování varování: {e}")
            await ctx.send("❌ **Nastala chyba při udělování varování!**")
    
    @commands.hybrid_command(name='smazat', aliases=['clear', 'purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, počet: int = 10):
        """Smaže určitý počet zpráv"""
        if počet <= 0 or počet > 100:
            return await ctx.send("❌ **Můžeš smazat 1-100 zpráv najednou!**")
        
        try:
            deleted = await ctx.channel.purge(limit=počet + 1)  # +1 pro příkaz samotný
            
            embed = discord.Embed(
                title="🧹 Zprávy smazány",
                description=f"**Smazáno:** {len(deleted) - 1} zpráv\n**Moderátor:** {ctx.author}",
                color=0x2ecc71
            )
            
            msg = await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            await ctx.send("❌ **Nemám oprávnění ke smazání zpráv!**")
        except Exception as e:
            logger.error(f"Chyba při mazání zpráv: {e}")
            await ctx.send("❌ **Nastala chyba při mazání zpráv!**")
    
    def _parse_time(self, time_str: str) -> timedelta:
        """Parsuje čas ze stringu (např. 10m, 1h, 2d)"""
        time_str = time_str.lower().strip()
        
        if time_str.endswith('s'):
            return timedelta(seconds=int(time_str[:-1]))
        elif time_str.endswith('m'):
            return timedelta(minutes=int(time_str[:-1]))
        elif time_str.endswith('h'):
            return timedelta(hours=int(time_str[:-1]))
        elif time_str.endswith('d'):
            return timedelta(days=int(time_str[:-1]))
        else:
            raise ValueError("Neplatný formát času")
    
    async def _send_mod_log(self, guild, action, user, moderator, reason, duration=None):
        """Pošle moderační log do log kanálu"""
        try:
            settings = await self.bot.db.get_guild_settings(guild.id)
            if not settings or not settings.get('mod_log_channel'):
                return
            
            channel = guild.get_channel(settings['mod_log_channel'])
            if not channel:
                return
            
            color_map = {
                'kick': 0xe74c3c,
                'ban': 0x992d22,
                'mute': 0xf39c12,
                'warn': 0xf39c12,
                'unmute': 0x2ecc71,
                'unban': 0x2ecc71
            }
            
            action_names = {
                'kick': '🦶 Vykopnutí',
                'ban': '🔨 Ban',
                'mute': '🔇 Ztišení',
                'warn': '⚠️ Varování',
                'unmute': '🔊 Zrušení ztišení',
                'unban': '✅ Odbanování'
            }
            
            embed = discord.Embed(
                title=action_names.get(action, f"📋 {action.title()}"),
                color=color_map.get(action, 0x3498db),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Uživatel", value=f"{user} (`{user.id}`)", inline=True)
            embed.add_field(name="Moderátor", value=f"{moderator} (`{moderator.id}`)", inline=True)
            embed.add_field(name="Důvod", value=reason, inline=False)
            
            if duration:
                embed.add_field(name="Doba", value=duration, inline=True)
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při odesílání mod logu: {e}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
