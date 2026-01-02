import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
import json
import logging
import random
import re

logger = logging.getLogger(__name__)

class Utility(commands.Cog):
    """Užitečné nástroje a příkazy"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
    
    # ========== PING ==========
    @app_commands.command(name="ping", description="Zobrazí ping bota")
    async def ping_slash(self, interaction: discord.Interaction):
        """Zobrazí ping bota"""
        start = datetime.utcnow()
        
        embed = discord.Embed(
            title="🏓 Měření ping...",
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)
        
        end = datetime.utcnow()
        api_ping = round(self.bot.latency * 1000, 2)
        message_ping = round((end - start).total_seconds() * 1000, 2)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x2ecc71,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="⚡ API Ping", value=f"**{api_ping}ms**", inline=True)
        embed.add_field(name="💬 Message Ping", value=f"**{message_ping}ms**", inline=True)
        
        # Kvalita spojení
        if api_ping < 100:
            quality = "🟢 Výborné"
        elif api_ping < 200:
            quality = "🟡 Dobré"
        elif api_ping < 500:
            quality = "🟠 Průměrné"
        else:
            quality = "🔴 Špatné"
        
        embed.add_field(name="📊 Kvalita", value=quality, inline=True)
        
        await interaction.edit_original_response(embed=embed)
    
    # ========== SERVER INFO ==========
    @app_commands.command(name="serverinfo", description="Zobrazí informace o serveru")
    async def serverinfo_slash(self, interaction: discord.Interaction):
        """Zobrazí informace o serveru"""
        guild = interaction.guild
        
        # Vytvoření embedu
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Základní informace
        embed.add_field(
            name="🏷️ Informace",
            value=f"**Vlastník:** {guild.owner.mention if guild.owner else 'Neznámý'}\n"
                  f"**ID:** `{guild.id}`\n"
                  f"**Vytvořen:** <t:{int(guild.created_at.timestamp())}:D>\n"
                  f"**Boost level:** {guild.premium_tier}",
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
            name="📺 Kanály",
            value=f"**Textové:** {text_channels}\n"
                  f"**Hlasové:** {voice_channels}\n"
                  f"**Kategorie:** {categories}\n"
                  f"**Role:** {len(guild.roles)}",
            inline=True
        )
        
        # Boosty
        if guild.premium_subscription_count > 0:
            embed.add_field(
                name="✨ Boosty",
                value=f"**Počet:** {guild.premium_subscription_count}\n"
                      f"**Boostéři:** {len(guild.premium_subscribers)}\n"
                      f"**Level:** {guild.premium_tier}",
                inline=True
            )
        
        # Emoji a stickery
        embed.add_field(
            name="🎨 Emoji & Stickery",
            value=f"**Emoji:** {len(guild.emojis)}/{guild.emoji_limit}\n"
                  f"**Stickery:** {len(guild.stickers)}/{guild.sticker_limit}",
            inline=True
        )
        
        # Funkce serveru
        features = []
        if guild.features:
            feature_names = {
                'ANIMATED_ICON': 'Animated Icon',
                'BANNER': 'Banner',
                'COMMERCE': 'Commerce',
                'COMMUNITY': 'Community',
                'DISCOVERABLE': 'Discoverable',
                'FEATURABLE': 'Featurable',
                'INVITE_SPLASH': 'Invite Splash',
                'MEMBER_VERIFICATION_GATE_ENABLED': 'Verification Gate',
                'MONETIZATION_ENABLED': 'Monetization',
                'MORE_STICKERS': 'More Stickers',
                'NEWS': 'News Channels',
                'PARTNERED': 'Partnered',
                'PREVIEW_ENABLED': 'Preview',
                'PRIVATE_THREADS': 'Private Threads',
                'ROLE_ICONS': 'Role Icons',
                'TICKETED_EVENTS': 'Ticketed Events',
                'VANITY_URL': 'Vanity URL',
                'VERIFIED': 'Verified',
                'VIP_REGIONS': 'VIP Regions',
                'WELCOME_SCREEN_ENABLED': 'Welcome Screen'
            }
            
            for feature in guild.features[:5]:
                features.append(f"✓ {feature_names.get(feature, feature)}")
        
        if features:
            embed.add_field(
                name="✨ Funkce",
                value="\n".join(features),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    # ========== USER INFO ==========
    @app_commands.command(name="userinfo", description="Zobrazí informace o uživateli")
    @app_commands.describe(uživatel="Uživatel (nechte prázdné pro sebe)")
    async def userinfo_slash(self, interaction: discord.Interaction, uživatel: discord.Member = None):
        """Zobrazí informace o uživateli"""
        user = uživatel or interaction.user
        
        # Vytvoření embedu
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color if user.color != discord.Color.default() else 0x3498db,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Základní informace
        embed.add_field(
            name="🏷️ Účet",
            value=f"**Jméno:** {user}\n"
                  f"**ID:** `{user.id}`\n"
                  f"**Bot:** {'✅ Ano' if user.bot else '❌ Ne'}\n"
                  f"**Vytvořen:** <t:{int(user.created_at.timestamp())}:R>",
            inline=True
        )
        
        # Server informace
        embed.add_field(
            name="📅 Server",
            value=f"**Přezdívka:** {user.nick or 'Žádná'}\n"
                  f"**Připojen:** <t:{int(user.joined_at.timestamp())}:R>\n"
                  f"**Nejvyšší role:** {user.top_role.mention}",
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
            for activity in user.activities:
                if isinstance(activity, discord.Game):
                    activity_text = f"🎮 Hraje {activity.name}"
                    break
                elif isinstance(activity, discord.Streaming):
                    activity_text = f"📺 Streamuje {activity.name}"
                    break
                elif isinstance(activity, discord.Activity):
                    if activity.type == discord.ActivityType.listening:
                        activity_text = f"🎵 Poslouchá {activity.name}"
                    elif activity.type == discord.ActivityType.watching:
                        activity_text = f"📺 Sleduje {activity.name}"
                    else:
                        activity_text = f"🎯 {activity.name}"
                    break
                elif isinstance(activity, discord.CustomActivity):
                    activity_text = f"💭 {activity.name}"
                    break
        
        embed.add_field(
            name="💫 Stav",
            value=f"**Status:** {status_emoji.get(user.status, '❓')}\n"
                  f"**Aktivita:** {activity_text}",
            inline=True
        )
        
        # Role (max 10)
        roles = [role.mention for role in user.roles[1:] if role != interaction.guild.default_role]
        if roles:
            roles_text = ", ".join(roles[:10])
            if len(roles) > 10:
                roles_text += f" (+{len(roles) - 10})"
        else:
            roles_text = "Žádné role"
        
        embed.add_field(
            name=f"🎭 Role ({len(user.roles) - 1})",
            value=roles_text[:1024],
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ========== AVATAR ==========
    @app_commands.command(name="avatar", description="Zobrazí avatar uživatele")
    @app_commands.describe(uživatel="Uživatel (nechte prázdné pro sebe)")
    async def avatar_slash(self, interaction: discord.Interaction, uživatel: discord.Member = None):
        """Zobrazí avatar uživatele"""
        user = uživatel or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ Avatar uživatele {user.display_name}",
            color=user.color if user.color != discord.Color.default() else 0x3498db
        )
        
        embed.set_image(url=user.display_avatar.url)
        
        # Formáty avataru
        formats = ['png', 'jpg', 'webp']
        if user.display_avatar.is_animated():
            formats.append('gif')
        
        links = " | ".join(f"[{fmt.upper()}]({user.display_avatar.with_format(fmt).url})" for fmt in formats)
        
        embed.add_field(name="🔗 Stáhnout", value=links, inline=False)
        embed.set_footer(text=f"ID: {user.id}")
        
        await interaction.response.send_message(embed=embed)
    
    # ========== SAY ==========
    @app_commands.command(name="say", description="Pošle zprávu jako bot")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(zpráva="Zpráva k odeslání")
    async def say_slash(self, interaction: discord.Interaction, zpráva: str):
        """Pošle zprávu jako bot"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Smazat příkaz
            await interaction.delete_original_response()
            
            # Odeslat zprávu
            await interaction.channel.send(zpráva)
            
        except Exception as e:
            logger.error(f"Chyba v say příkazu: {e}")
            await interaction.followup.send("❌ **Nastala chyba při odesílání zprávy!**", ephemeral=True)
    
    # ========== EMBED ==========
    @app_commands.command(name="embed", description="Vytvoří embed zprávu")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(titulek="Titulek embedu", popis="Popis embedu", barva="Barva v hex (např. #3498db)")
    async def embed_slash(self, interaction: discord.Interaction, titulek: str, popis: str, barva: str = None):
        """Vytvoří embed zprávu"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parsování barvy
            color = 0x3498db  # Výchozí
            if barva:
                try:
                    if barva.startswith('#'):
                        barva = barva[1:]
                    color = int(barva, 16)
                except:
                    color = 0x3498db
            
            # Vytvoření embedu
            embed = discord.Embed(
                title=titulek,
                description=popis,
                color=color,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text=f"Vytvořil {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            
            # Smazat příkaz
            await interaction.delete_original_response()
            
            # Odeslat embed
            await interaction.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba v embed příkazu: {e}")
            await interaction.followup.send("❌ **Nastala chyba při vytváření embedu!**", ephemeral=True)
    
    # ========== POLL ==========
    @app_commands.command(name="hlasování", description="Vytvoří hlasování")
    @app_commands.describe(otázka="Otázka pro hlasování", možnost1="První možnost", možnost2="Druhá možnost")
    async def poll_slash(self, interaction: discord.Interaction, otázka: str, možnost1: str, možnost2: str):
        """Vytvoří hlasování"""
        await interaction.response.defer()
        
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        embed = discord.Embed(
            title="📊 Hlasování",
            description=f"**{otázka}**",
            color=0x3498db,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="1️⃣", value=možnost1, inline=False)
        embed.add_field(name="2️⃣", value=možnost2, inline=False)
        
        embed.set_footer(text=f"Vytvořil {interaction.user.display_name}")
        
        message = await interaction.followup.send(embed=embed)
        
        # Přidání reakcí
        await message.add_reaction('1️⃣')
        await message.add_reaction('2️⃣')
    
    # ========== REMIND ==========
    @app_commands.command(name="připomeň", description="Nastaví připomínku")
    @app_commands.describe(čas="Čas (např. 10m, 1h, 2d30m)", zpráva="Zpráva připomínky")
    async def remind_slash(self, interaction: discord.Interaction, čas: str, zpráva: str):
        """Nastaví připomínku"""
        await interaction.response.defer()
        
        try:
            # Parsování času
            time_units = {
                's': 1, 'sec': 1, 'sekund': 1,
                'm': 60, 'min': 60, 'minut': 60,
                'h': 3600, 'hod': 3600, 'hodin': 3600,
                'd': 86400, 'den': 86400, 'dní': 86400
            }
            
            total_seconds = 0
            pattern = r'(\d+)\s*([a-zA-Záčďéěíňóřšťúůýž]+)'
            matches = re.findall(pattern, čas.lower())
            
            if not matches:
                await interaction.followup.send("❌ **Neplatný formát času!**\nPoužij např: `10m`, `1h30m`, `2d`", ephemeral=True)
                return
            
            for amount, unit in matches:
                if unit in time_units:
                    total_seconds += int(amount) * time_units[unit]
                else:
                    # Zkontrolovat zkrácené formy
                    for key in time_units:
                        if key.startswith(unit):
                            total_seconds += int(amount) * time_units[key]
                            break
            
            if total_seconds < 10:
                await interaction.followup.send("❌ **Minimální čas je 10 sekund!**", ephemeral=True)
                return
            
            if total_seconds > 2592000:  # 30 dní
                await interaction.followup.send("❌ **Maximální čas je 30 dní!**", ephemeral=True)
                return
            
            # Formátování času pro zobrazení
            if total_seconds < 60:
                display_time = f"{total_seconds} sekund"
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                display_time = f"{minutes} minut"
            elif total_seconds < 86400:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                display_time = f"{hours} hodin"
                if minutes > 0:
                    display_time += f" {minutes} minut"
            else:
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                display_time = f"{days} dní"
                if hours > 0:
                    display_time += f" {hours} hodin"
            
            # Uložení připomínky
            reminder_id = f"{interaction.user.id}_{datetime.now().timestamp()}"
            self.reminders[reminder_id] = {
                'user_id': interaction.user.id,
                'channel_id': interaction.channel.id,
                'message': zpráva,
                'ends_at': datetime.now() + timedelta(seconds=total_seconds),
                'original_message': f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{interaction.id}"
            }
            
            # Potvrzení
            embed = discord.Embed(
                title="⏰ Připomínka nastavena",
                description=f"**Za:** {display_time}\n**Zpráva:** {zpráva}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            embed.set_footer(text="Připomenu ti to v tomto kanálu")
            
            await interaction.followup.send(embed=embed)
            
            # Spustit časovač
            await asyncio.sleep(total_seconds)
            
            # Odeslat připomínku
            if reminder_id in self.reminders:
                reminder = self.reminders.pop(reminder_id)
                
                embed = discord.Embed(
                    title="⏰ Připomínka!",
                    description=f"**{zpráva}**\n\n[Původní zpráva]({reminder['original_message']})",
                    color=0xe74c3c,
                    timestamp=datetime.utcnow()
                )
                
                try:
                    channel = self.bot.get_channel(reminder['channel_id'])
                    if channel:
                        await channel.send(f"<@{reminder['user_id']}>", embed=embed)
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Chyba v remind příkazu: {e}")
            await interaction.followup.send("❌ **Nastala chyba při nastavování připomínky!**", ephemeral=True)
    
    # ========== RANDOM ==========
    @app_commands.command(name="náhodně", description="Vygeneruje náhodné číslo")
    @app_commands.describe(od="Od (výchozí: 1)", do="Do (výchozí: 100)")
    async def random_slash(self, interaction: discord.Interaction, od: int = 1, do: int = 100):
        """Vygeneruje náhodné číslo"""
        if od >= do:
            await interaction.response.send_message("❌ **Číslo 'od' musí být menší než 'do'!**", ephemeral=True)
            return
        
        number = random.randint(od, do)
        
        embed = discord.Embed(
            title="🎲 Náhodné číslo",
            description=f"**Rozsah:** {od} - {do}\n**Výsledek:** **{number}**",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ========== COIN FLIP ==========
    @app_commands.command(name="mince", description="Hodí mincí")
    async def coinflip_slash(self, interaction: discord.Interaction):
        """Hodí mincí"""
        result = random.choice(['Panna', 'Orel'])
        emoji = '👑' if result == 'Orel' else '👸'
        
        embed = discord.Embed(
            title=f"{emoji} Hod mincí",
            description=f"**Výsledek:** **{result}**",
            color=0xf1c40f
        )
        
        await interaction.response.send_message(embed=embed)
    
    # ========== 8BALL ==========
    @app_commands.command(name="koule", description="Magická 8 koule odpoví na tvou otázku")
    @app_commands.describe(otázka="Tvá otázka")
    async def eightball_slash(self, interaction: discord.Interaction, otázka: str):
        """Magická 8 koule"""
        responses = [
            "Ano, určitě! ✅",
            "Je to jisté. ✅",
            "Bez pochyb. ✅",
            "Ano, rozhodně. ✅",
            "Můžeš se na to spolehnout. ✅",
            "Jak já to vidím, ano. ✅",
            "Nejspíš. ✅",
            "Výhled dobrý. ✅",
            "Ano. ✅",
            "Známky naznačují ano. ✅",
            
            "Odpověď mlhavá, zkus znovu. 🔄",
            "Zeptej se později. 🔄",
            "Lépe ti to nyní neprozradím. 🔄",
            "Teď to nedokážu předpovědět. 🔄",
            "Soustřeď se a zeptej se znovu. 🔄",
            
            "Nepočítej s tím. ❌",
            "Moje odpověď je ne. ❌",
            "Moje zdroje říkají ne. ❌",
            "Výhled není tak dobrý. ❌",
            "Velmi pochybné. ❌"
        ]
        
        answer = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magická 8 koule",
            color=0x2c3e50
        )
        
        embed.add_field(name="❓ Otázka", value=otázka, inline=False)
        embed.add_field(name="🎱 Odpověď", value=answer, inline=False)
        embed.set_footer(text=f"Pro {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
    # ========== TRY ==========
    @app_commands.command(name="try", description="Odpoví ano/ne")
    @app_commands.describe(otázka="Tvá otázka")
    async def try_slash(self, interaction: discord.Interaction, otázka: str):
        """/try"""
        responses = [
            "Ano ✅",
            "Ne ❌"
        ]
        
        answer = random.choice(responses)
        
        embed = discord.Embed(
            title="❓ /Try ",
            color=0x2c3e50
        )
        
        embed.add_field(name="❓ Odpověď", value=answer, inline=False)
        embed.set_footer(text=f"🔄 Pro {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
    # ========== HELP ==========
    @app_commands.command(name="nápověda", description="Zobrazí nápovědu k příkazům")
    @app_commands.describe(kategorie="Kategorie příkazů")
    @app_commands.choices(kategorie=[
        app_commands.Choice(name="🛡️ Moderace", value="moderation"),
        app_commands.Choice(name="🎫 Tikety", value="tickets"),
        app_commands.Choice(name="🎵 Hudba", value="music"),
        app_commands.Choice(name="📋 MDT", value="mdt"),
        app_commands.Choice(name="⚙️ Utility", value="utility")
    ])
    async def help_slash(self, interaction: discord.Interaction, kategorie: str = None):
        """Zobrazí nápovědu k příkazům"""
        if not kategorie:
            # Hlavní nápověda
            embed = discord.Embed(
                title="🔷 VeltrixAPP - Nápověda",
                description="Vítej v nápovědě Veltrix bota! Vyber kategorii pomocí menu níže.",
                color=0x3498db
            )
            
            embed.add_field(
                name="📋 Kategorie příkazů",
                value="🛡️ **Moderace** - Moderační příkazy\n"
                      "🎫 **Tikety** - Systém support tiketů\n"
                      "🎵 **Hudba** - Přehrávání hudby z YouTube\n"
                      "📋 **MDT** - Policejní databáze a občanky\n"
                      "⚙️ **Utility** - Užitečné nástroje",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Rychlé příkazy",
                value="`/ping` - Zkontroluj ping bota\n"
                      "`/serverinfo` - Informace o serveru\n"
                      "`/userinfo` - Informace o uživateli\n"
                      "`/avatar` - Zobrazí avatar\n"
                      "`/nápověda <kategorie>` - Detailní nápověda",
                inline=False
            )
            
            embed.set_footer(text=f"Celkem příkazů: {len(self.bot.tree.get_commands())}")
            
            await interaction.response.send_message(embed=embed)
        else:
            # Detailní nápověda podle kategorie
            category_info = {
                'moderation': {
                    'title': '🛡️ Moderace',
                    'description': 'Moderační příkazy pro správu serveru',
                    'commands': [
                        ('/vykopnout', 'Vykopne člena ze serveru'),
                        ('/ban', 'Zabanuje člena na serveru'),
                        ('/ztišit', 'Ztíší člena (timeout)'),
                        ('/zrušit_ztišení', 'Zruší ztišení člena'),
                        ('/smazat', 'Smaže zprávy v kanálu'),
                        ('/varování', 'Udělí varování členovi'),
                        ('/zamknout', 'Zamkne kanál'),
                        ('/odemknout', 'Odemkne kanál'),
                        ('/zpomalit', 'Nastaví slowmode')
                    ]
                },
                'tickets': {
                    'title': '🎫 Tikety',
                    'description': 'Systém support tiketů a žádostí',
                    'commands': [
                        ('/ticket_panel', 'Vytvoří panel pro tikety'),
                        ('/uzavřit_ticket', 'Uzavře aktuální ticket'),
                        ('/ticket_stats', 'Zobrazí statistiky tiketů')
                    ]
                },
                'music': {
                    'title': '🎵 Hudba',
                    'description': 'Hudební přehrávač s YouTube podporou',
                    'commands': [
                        ('/přehrát', 'Přehraje hudbu z YouTube'),
                        ('/pozastavit', 'Pozastaví přehrávání'),
                        ('/pokračovat', 'Obnoví přehrávání'),
                        ('/přeskočit', 'Přeskočí píseň'),
                        ('/zastavit', 'Zastaví hudbu'),
                        ('/fronta', 'Zobrazí frontu písní'),
                        ('/hlasitost', 'Nastaví hlasitost'),
                        ('/odpojit', 'Odpojí bota z hlasového kanálu')
                    ]
                },
                'mdt': {
                    'title': '📋 MDT Systém',
                    'description': 'Policejní databáze a systém občanek',
                    'commands': [
                        ('/obcanka', 'Vytvoří občanský průkaz'),
                        ('/mdt_panel', 'Vytvoří MDT panel'),
                        ('/mdt_hledat', 'Hledá v MDT databázi'),
                        ('/mdt_zaznam', 'Přidá záznam k občanovi'),
                        ('/pokuta', 'Vystaví pokutu'),
                        ('/vezeni', 'Zadrží občana do vězení'),
                        ('/mdt_info', 'Zobrazí info o občanovi')
                    ]
                },
                'utility': {
                    'title': '⚙️ Utility',
                    'description': 'Užitečné nástroje a příkazy',
                    'commands': [
                        ('/ping', 'Zobrazí ping bota'),
                        ('/serverinfo', 'Informace o serveru'),
                        ('/userinfo', 'Informace o uživateli'),
                        ('/avatar', 'Zobrazí avatar'),
                        ('/say', 'Pošle zprávu jako bot'),
                        ('/embed', 'Vytvoří embed zprávu'),
                        ('/hlasování', 'Vytvoří hlasování'),
                        ('/připomeň', 'Nastaví připomínku'),
                        ('/náhodně', 'Vygeneruje náhodné číslo'),
                        ('/mince', 'Hodí mincí'),
                        ('/koule', 'Magická 8 koule'),
                        ('/try', 'Odpoví ano/ne'),
                        ('/rep', 'Dej/Oddělej nekomu rep (ve vývoji)')
                    ]
                }
            }
            
            info = category_info.get(kategorie, {'title': 'Neplatná kategorie', 'description': '', 'commands': []})
            
            embed = discord.Embed(
                title=f"{info['title']} - Příkazy",
                description=info['description'],
                color=0x3498db
            )
            
            for command, description in info['commands']:
                embed.add_field(name=command, value=description, inline=False)
            
            embed.set_footer(text="VeltrixAPP | /nápověda pro hlavní menu")
            
            await interaction.response.send_message(embed=embed)
    
    # ========== WELCOME SYSTEM ==========
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event při příchodu nového člena"""
        try:
            channel_id = self.bot.config['welcome'].get('channel_id')
            if not channel_id:
                return
            
            channel = member.guild.get_channel(int(channel_id))
            if not channel:
                return
            
            embed = discord.Embed(
                title="👋 Vítej na serveru!",
                description=f"Ahoj {member.mention}!\nVítej na **{member.guild.name}**! 🎉",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="📊 Statistiky", value=f"**Počet členů:** {member.guild.member_count}")
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba v welcome systému: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Event při odchodu člena"""
        try:
            channel_id = self.bot.config['welcome'].get('goodbye_channel_id')
            if not channel_id:
                return
            
            channel = member.guild.get_channel(int(channel_id))
            if not channel:
                return
            
            embed = discord.Embed(
                title="👋 Člen odešel",
                description=f"{member.name} opustil server. 😢",
                color=0xe74c3c,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="📊 Statistiky", value=f"**Zbývá členů:** {member.guild.member_count}")
            
            if member.joined_at:
                days_in_server = (datetime.utcnow() - member.joined_at).days
                embed.add_field(name="📅 Na serveru", value=f"{days_in_server} dní")
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"ID: {member.id}")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba v goodbye systému: {e}")

async def setup(bot):
    await bot.add_cog(Utility(bot))