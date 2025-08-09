import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class Utility(commands.Cog):
    """Užitečné nástroje pro správu serveru"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event při příchodu nového člena"""
        try:
            # Získání nastavení z databáze
            settings = await self.bot.db.get_guild_settings(member.guild.id)
            if not settings or not settings.get('welcome_channel'):
                return
            
            welcome_channel = member.guild.get_channel(settings['welcome_channel'])
            if not welcome_channel:
                return
            
            # Vlastní welcome zpráva nebo výchozí
            welcome_msg = settings.get('welcome_message', 
                                     f"Vítej na serveru {member.guild.name}, {member.mention}! 🎉")
            
            # Vytvoření embed zprávy
            embed = discord.Embed(
                title="👋 Nový člen!",
                description=welcome_msg.format(
                    user=member.mention,
                    username=member.name,
                    server=member.guild.name,
                    count=len(member.guild.members)
                ),
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(
                name="📊 Statistiky",
                value=f"**Účet vytvořen:** <t:{int(member.created_at.timestamp())}:R>\n"
                      f"**Člen číslo:** {len(member.guild.members)}",
                inline=True
            )
            
            embed.set_footer(text=f"ID: {member.id}")
            
            await welcome_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba v welcome systému: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Event při odchodu člena"""
        try:
            # Získání nastavení z databáze
            settings = await self.bot.db.get_guild_settings(member.guild.id)
            if not settings or not settings.get('goodbye_channel'):
                return
            
            goodbye_channel = member.guild.get_channel(settings['goodbye_channel'])
            if not goodbye_channel:
                return
            
            # Vlastní goodbye zpráva nebo výchozí
            goodbye_msg = settings.get('goodbye_message', 
                                      f"{member.name} opustil server. 😢")
            
            # Vytvoření embed zprávy
            embed = discord.Embed(
                title="👋 Člen odešel",
                description=goodbye_msg.format(
                    user=member.name,
                    username=member.name,
                    server=member.guild.name,
                    count=len(member.guild.members)
                ),
                color=0xe74c3c,
                timestamp=datetime.utcnow()
            )
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(
                name="📊 Statistiky",
                value=f"**Připojen:** <t:{int(member.joined_at.timestamp())}:R>\n"
                      f"**Zbývá členů:** {len(member.guild.members)}",
                inline=True
            )
            
            embed.set_footer(text=f"ID: {member.id}")
            
            await goodbye_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba v goodbye systému: {e}")
    
    @commands.hybrid_command(name='serverinfo', aliases=['server'])
    async def server_info(self, ctx):
        """Zobrazí informace o serveru"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 Informace o serveru",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Základní informace
        embed.add_field(
            name="🏷️ Základní info",
            value=f"**Název:** {guild.name}\n"
                  f"**ID:** {guild.id}\n"
                  f"**Vlastník:** {guild.owner.mention if guild.owner else 'Neznámý'}\n"
                  f"**Vytvořen:** <t:{int(guild.created_at.timestamp())}:R>",
            inline=True
        )
        
        # Statistiky členů
        bots = sum(1 for member in guild.members if member.bot)
        humans = len(guild.members) - bots
        
        embed.add_field(
            name="👥 Členové",
            value=f"**Celkem:** {len(guild.members):,}\n"
                  f"**Lidé:** {humans:,}\n"
                  f"**Boti:** {bots:,}\n"
                  f"**Online:** {sum(1 for m in guild.members if m.status != discord.Status.offline):,}",
            inline=True
        )
        
        # Kanály a role
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="📺 Kanály a role",
            value=f"**Textové:** {text_channels}\n"
                  f"**Hlasové:** {voice_channels}\n"
                  f"**Kategorie:** {categories}\n"
                  f"**Role:** {len(guild.roles)}",
            inline=True
        )
        
        # Funkce serveru
        features = []
        if guild.premium_tier > 0:
            features.append(f"Nitro Boost Level {guild.premium_tier}")
        if guild.verification_level != discord.VerificationLevel.none:
            features.append(f"Ověření: {guild.verification_level.name.title()}")
        if guild.explicit_content_filter != discord.ContentFilter.disabled:
            features.append("Filtr obsahu aktivní")
        
        if features:
            embed.add_field(
                name="✨ Funkce",
                value="\n".join(features),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='userinfo', aliases=['user'])
    async def user_info(self, ctx, uživatel: discord.Member = None):
        """Zobrazí informace o uživateli"""
        user = uživatel or ctx.author
        
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color if user.color != discord.Color.default() else 0x3498db,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Základní informace
        embed.add_field(
            name="🏷️ Základní info",
            value=f"**Uživatelské jméno:** {user}\n"
                  f"**ID:** {user.id}\n"
                  f"**Přezdívka:** {user.nick or 'Žádná'}\n"
                  f"**Bot:** {'✅ Ano' if user.bot else '❌ Ne'}",
            inline=True
        )
        
        # Datumy
        embed.add_field(
            name="📅 Datumy",
            value=f"**Vytvořen:** <t:{int(user.created_at.timestamp())}:R>\n"
                  f"**Připojen:** <t:{int(user.joined_at.timestamp())}:R>",
            inline=True
        )
        
        # Status a aktivita
        status_emoji = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Nečinný",
            discord.Status.dnd: "🔴 Nerušit",
            discord.Status.offline: "⚫ Offline"
        }
        
        activity_text = "Žádná"
        if user.activities:
            activity = user.activities[0]
            if isinstance(activity, discord.Game):
                activity_text = f"🎮 Hraje {activity.name}"
            elif isinstance(activity, discord.Streaming):
                activity_text = f"📺 Streamuje {activity.name}"
            elif isinstance(activity, discord.Activity):
                activity_text = f"🎯 {activity.name}"
        
        embed.add_field(
            name="💫 Status",
            value=f"**Status:** {status_emoji.get(user.status, '❓ Neznámý')}\n"
                  f"**Aktivita:** {activity_text}",
            inline=True
        )
        
        # Role (pouze top 10)
        roles = [role.mention for role in user.roles[1:] if role != ctx.guild.default_role]
        if roles:
            roles_text = ", ".join(roles[:10])
            if len(roles) > 10:
                roles_text += f" a dalších {len(roles) - 10}"
        else:
            roles_text = "Žádné role"
        
        embed.add_field(
            name=f"🎭 Role ({len(user.roles) - 1})",
            value=roles_text,
            inline=False
        )
        
        # Oprávnění (pouze admin a moderační)
        perms = []
        if user.guild_permissions.administrator:
            perms.append("👑 Administrator")
        if user.guild_permissions.manage_guild:
            perms.append("⚙️ Správa serveru")
        if user.guild_permissions.manage_channels:
            perms.append("📺 Správa kanálů")
        if user.guild_permissions.manage_messages:
            perms.append("💬 Správa zpráv")
        if user.guild_permissions.kick_members:
            perms.append("🦶 Vykopávání")
        if user.guild_permissions.ban_members:
            perms.append("🔨 Banování")
        
        if perms:
            embed.add_field(
                name="🛡️ Klíčová oprávnění",
                value="\n".join(perms[:5]),
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='avatar', aliases=['av'])
    async def avatar(self, ctx, uživatel: discord.Member = None):
        """Zobrazí avatar uživatele"""
        user = uživatel or ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ Avatar uživatele {user.display_name}",
            color=user.color if user.color != discord.Color.default() else 0x3498db
        )
        
        embed.set_image(url=user.display_avatar.url)
        
        embed.add_field(
            name="🔗 Odkazy",
            value=f"[PNG]({user.display_avatar.with_format('png').url}) | "
                  f"[JPG]({user.display_avatar.with_format('jpg').url}) | "
                  f"[WEBP]({user.display_avatar.with_format('webp').url})",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='ping')
    async def ping(self, ctx):
        """Zobrazí ping bota"""
        start_time = datetime.utcnow()
        message = await ctx.send("🏓 Pinguji...")
        end_time = datetime.utcnow()
        
        api_ping = round(self.bot.latency * 1000, 2)
        message_ping = round((end_time - start_time).total_seconds() * 1000, 2)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x2ecc71,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⚡ API Ping",
            value=f"**{api_ping}ms**",
            inline=True
        )
        
        embed.add_field(
            name="💬 Message Ping",
            value=f"**{message_ping}ms**",
            inline=True
        )
        
        # Určení kvality spojení
        if api_ping < 100:
            quality = "🟢 Výborné"
        elif api_ping < 200:
            quality = "🟡 Dobré"
        elif api_ping < 500:
            quality = "🟠 Slabé"
        else:
            quality = "🔴 Velmi špatné"
        
        embed.add_field(
            name="📊 Kvalita spojení",
            value=quality,
            inline=True
        )
        
        await message.edit(content=None, embed=embed)
    
    @commands.hybrid_command(name='say', aliases=['echo'])
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, zpráva: str):
        """Nechá bota napsat zprávu"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        await ctx.send(zpráva)
    
    @commands.hybrid_command(name='embed')
    @commands.has_permissions(manage_messages=True)
    async def create_embed(self, ctx, titulek: str, *, obsah: str):
        """Vytvoří embed zprávu"""
        try:
            await ctx.message.delete()
        except:
            pass
        
        embed = discord.Embed(
            title=titulek,
            description=obsah,
            color=self.bot.config['embed_color'],
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text=f"Vytvořeno uživatelem {ctx.author.display_name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='poll', aliases=['hlasování'])
    async def poll(self, ctx, *, argumenty: str):
        """Vytvoří hlasování - použij: !poll "Otázka?" "Možnost 1" "Možnost 2" """
        import shlex
        
        try:
            # Parsování argumentů v uvozovkách
            parts = shlex.split(argumenty)
        except ValueError:
            return await ctx.send("❌ **Použij uvozovky kolem otázky a možností!** Příklad: `!poll \"Otázka?\" \"Možnost 1\" \"Možnost 2\"`")
        
        if len(parts) < 3:
            return await ctx.send("❌ **Musíš zadat otázku a alespoň 2 možnosti!** Příklad: `!poll \"Otázka?\" \"Možnost 1\" \"Možnost 2\"`")
        
        otázka = parts[0]
        možnosti = parts[1:]
        
        if len(možnosti) > 10:
            return await ctx.send("❌ **Maximum je 10 možností!**")
        
        embed = discord.Embed(
            title="📊 Hlasování",
            description=f"**{otázka}**",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        možnosti_text = ""
        for i, možnost in enumerate(možnosti):
            možnosti_text += f"{reactions[i]} {možnost}\n"
        
        embed.add_field(
            name="Možnosti:",
            value=možnosti_text,
            inline=False
        )
        
        embed.set_footer(text=f"Hlasování spustil {ctx.author.display_name}")
        
        try:
            await ctx.message.delete()
        except:
            pass
        
        poll_msg = await ctx.send(embed=embed)
        
        # Přidání reakcí
        for i in range(len(možnosti)):
            await poll_msg.add_reaction(reactions[i])
    
    @commands.hybrid_command(name='remind', aliases=['připomeň'])
    async def remind(self, ctx, čas: str, *, připomínka: str):
        """Připomene ti něco za určitý čas"""
        try:
            # Parsování času
            time_units = {
                's': 1, 'sec': 1, 'sekund': 1,
                'm': 60, 'min': 60, 'minut': 60,
                'h': 3600, 'hour': 3600, 'hodin': 3600,
                'd': 86400, 'day': 86400, 'den': 86400, 'dní': 86400
            }
            
            total_seconds = 0
            čas = čas.lower()
            
            # Jednoduchý parser pro formáty typu "10m", "1h30m", "2d"
            import re
            time_pattern = r'(\d+)([smhd]|sec|min|hour|day|sekund|minut|hodin|den|dní)'
            matches = re.findall(time_pattern, čas)
            
            if not matches:
                return await ctx.send("❌ **Neplatný formát času! Použij např: 10m, 1h30m, 2d**")
            
            for amount, unit in matches:
                if unit in time_units:
                    total_seconds += int(amount) * time_units[unit]
            
            if total_seconds < 10:
                return await ctx.send("❌ **Minimum je 10 sekund!**")
            
            if total_seconds > 2592000:  # 30 dní
                return await ctx.send("❌ **Maximum je 30 dní!**")
            
            # Vytvoření embed zprávy
            embed = discord.Embed(
                title="⏰ Připomínka nastavena",
                description=f"**Připomenu ti za:** {čas}\n**Zpráva:** {připomínka}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
            
            # Čekání
            await asyncio.sleep(total_seconds)
            
            # Poslání připomínky
            remind_embed = discord.Embed(
                title="⏰ Připomínka!",
                description=f"**Připomínka:** {připomínka}\n\n"
                           f"[Přejdi na původní zprávu]({ctx.message.jump_url})",
                color=0xe74c3c,
                timestamp=datetime.utcnow()
            )
            
            try:
                await ctx.author.send(embed=remind_embed)
            except discord.Forbidden:
                await ctx.send(f"{ctx.author.mention}", embed=remind_embed)
                
        except ValueError:
            await ctx.send("❌ **Neplatný formát času!**")
        except Exception as e:
            logger.error(f"Chyba v remind příkazu: {e}")
            await ctx.send("❌ **Nastala chyba při nastavování připomínky!**")
    
    @commands.hybrid_command(name='nastavení', aliases=['settings'])
    @commands.has_permissions(manage_guild=True)
    async def guild_settings(self, ctx, nastavení: str = None, *, hodnota: str = None):
        """Správa nastavení serveru"""
        if not nastavení:
            # Zobrazení aktuálních nastavení
            settings = await self.bot.db.get_guild_settings(ctx.guild.id)
            
            embed = discord.Embed(
                title="⚙️ Nastavení serveru",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            
            # Aktuální nastavení
            prefix = settings.get('prefix', '!') if settings else '!'
            mod_channel = ctx.guild.get_channel(settings.get('mod_log_channel')) if settings and settings.get('mod_log_channel') else None
            welcome_channel = ctx.guild.get_channel(settings.get('welcome_channel')) if settings and settings.get('welcome_channel') else None
            goodbye_channel = ctx.guild.get_channel(settings.get('goodbye_channel')) if settings and settings.get('goodbye_channel') else None
            automod = settings.get('automod_enabled', True) if settings else True
            
            embed.add_field(
                name="🎯 Aktuální nastavení",
                value=f"**Prefix:** `{prefix}`\n"
                      f"**Mod log kanál:** {mod_channel.mention if mod_channel else 'Nenastaveno'}\n"
                      f"**Auto-moderace:** {'🟢 Zapnuto' if automod else '🔴 Vypnuto'}\n"
                      f"**Welcome kanál:** {welcome_channel.mention if welcome_channel else 'Nenastaveno'}\n"
                      f"**Goodbye kanál:** {goodbye_channel.mention if goodbye_channel else 'Nenastaveno'}",
                inline=False
            )
            
            embed.add_field(
                name="📋 Dostupná nastavení",
                value="`prefix <nový_prefix>` - Změna prefixu\n"
                      "`mod_log <#kanál>` - Nastavení mod log kanálu\n"
                      "`automod <true/false>` - Zapnutí/vypnutí auto-moderace\n"
                      "`welcome <#kanál>` - Nastavení welcome kanálu\n"
                      "`goodbye <#kanál>` - Nastavení goodbye kanálu\n"
                      "`welcome_msg <zpráva>` - Vlastní welcome zpráva\n"
                      "`goodbye_msg <zpráva>` - Vlastní goodbye zpráva",
                inline=False
            )
            
            return await ctx.send(embed=embed)
        
        # Změna nastavení
        if nastavení.lower() == 'prefix':
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat nový prefix!**")
            
            if len(hodnota) > 5:
                return await ctx.send("❌ **Prefix může mít maximálně 5 znaků!**")
            
            await self.bot.db.update_guild_setting(ctx.guild.id, 'prefix', hodnota)
            await ctx.send(f"✅ **Prefix byl změněn na:** `{hodnota}`")
            
        elif nastavení.lower() == 'mod_log':
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat kanál!**")
            
            try:
                channel = await commands.TextChannelConverter().convert(ctx, hodnota)
                await self.bot.db.update_guild_setting(ctx.guild.id, 'mod_log_channel', channel.id)
                await ctx.send(f"✅ **Mod log kanál byl nastaven na:** {channel.mention}")
            except commands.ChannelNotFound:
                await ctx.send("❌ **Kanál nebyl nalezen!**")
                
        elif nastavení.lower() == 'automod':
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat true/false!**")
            
            if hodnota.lower() in ['true', '1', 'ano', 'zapnuto']:
                await self.bot.db.update_guild_setting(ctx.guild.id, 'automod_enabled', 1)
                await ctx.send("✅ **Auto-moderace byla zapnuta!**")
            elif hodnota.lower() in ['false', '0', 'ne', 'vypnuto']:
                await self.bot.db.update_guild_setting(ctx.guild.id, 'automod_enabled', 0)
                await ctx.send("✅ **Auto-moderace byla vypnuta!**")
            else:
                await ctx.send("❌ **Neplatná hodnota! Použij: true/false**")
                
        elif nastavení.lower() in ['welcome', 'příchod']:
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat kanál!**")
            
            try:
                channel = await commands.TextChannelConverter().convert(ctx, hodnota)
                await self.bot.db.update_guild_setting(ctx.guild.id, 'welcome_channel', channel.id)
                await ctx.send(f"✅ **Welcome kanál byl nastaven na:** {channel.mention}")
            except commands.ChannelNotFound:
                await ctx.send("❌ **Kanál nebyl nalezen!**")
                
        elif nastavení.lower() in ['goodbye', 'odchod']:
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat kanál!**")
            
            try:
                channel = await commands.TextChannelConverter().convert(ctx, hodnota)
                await self.bot.db.update_guild_setting(ctx.guild.id, 'goodbye_channel', channel.id)
                await ctx.send(f"✅ **Goodbye kanál byl nastaven na:** {channel.mention}")
            except commands.ChannelNotFound:
                await ctx.send("❌ **Kanál nebyl nalezen!**")
                
        elif nastavení.lower() in ['welcome_msg', 'příchod_zpráva']:
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat zprávu!**")
            
            await self.bot.db.update_guild_setting(ctx.guild.id, 'welcome_message', hodnota)
            await ctx.send(f"✅ **Welcome zpráva byla nastavena!**\n\n**Dostupné proměnné:**\n"
                          "`{user}` - mention uživatele\n"
                          "`{username}` - jméno uživatele\n"
                          "`{server}` - název serveru\n"
                          "`{count}` - počet členů")
            
        elif nastavení.lower() in ['goodbye_msg', 'odchod_zpráva']:
            if not hodnota:
                return await ctx.send("❌ **Musíš zadat zprávu!**")
            
            await self.bot.db.update_guild_setting(ctx.guild.id, 'goodbye_message', hodnota)
            await ctx.send(f"✅ **Goodbye zpráva byla nastavena!**\n\n**Dostupné proměnné:**\n"
                          "`{user}` - jméno uživatele\n"
                          "`{username}` - jméno uživatele\n"
                          "`{server}` - název serveru\n"
                          "`{count}` - počet členů")
        else:
            await ctx.send("❌ **Neplatné nastavení! Použij `!nastavení` pro zobrazení dostupných možností.**")

async def setup(bot):
    await bot.add_cog(Utility(bot))
