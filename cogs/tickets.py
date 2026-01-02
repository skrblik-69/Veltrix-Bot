import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Dict, Optional, List
import datetime
import json
import os

# Třída pro panel s dropdown menu pro výběr typu ticketu
class TicketPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # Přidání dropdown menu pro výběr kategorie
        self.add_item(TicketCategorySelect(bot))

# Dropdown menu pro výběr kategorie ticketu
class TicketCategorySelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        
        options = [
            discord.SelectOption(
                label="🎭 RP Žádosti",
                value="rp_requests",
                description="Zbrojní průkazy, pozemky, frakce, svatby, CK",
                emoji="🎭"
            ),
            discord.SelectOption(
                label="🗝️ Admin & Technické",
                value="admin_technical",
                description="Unban, úprava frakce, majetek, giveaway",
                emoji="🗝️"
            ),
            discord.SelectOption(
                label="🚀 Kariéra & Spolupráce",
                value="career_collab",
                description="Game Staff, Moderator, Discord Staff, Partnerství",
                emoji="🚀"
            ),
            discord.SelectOption(
                label="📡 Problémy & Reporty",
                value="problems_reports",
                description="Stížnosti, bot problémy, jiné problémy",
                emoji="📡"
            )
        ]
        
        super().__init__(
            placeholder="🎯 Vyberte kategorii ticketu...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        # Získat cog TicketSystem
        cog = self.bot.get_cog('TicketSystem')
        if not cog:
            await interaction.response.send_message("❌ Ticket systém není dostupný.", ephemeral=True)
            return
        
        # Zobrazit další dropdown s konkrétními typy ticketů podle kategorie
        if self.values[0] == "rp_requests":
            view = TicketTypeView(self.bot, "rp_requests")
            await interaction.response.send_message(
                "**🎭 RP Žádosti**\nVyberte konkrétní typ ticketu:",
                view=view,
                ephemeral=True
            )
        elif self.values[0] == "admin_technical":
            view = TicketTypeView(self.bot, "admin_technical")
            await interaction.response.send_message(
                "**🗝️ Admin & Technické**\nVyberte konkrétní typ ticketu:",
                view=view,
                ephemeral=True
            )
        elif self.values[0] == "career_collab":
            view = TicketTypeView(self.bot, "career_collab")
            await interaction.response.send_message(
                "**🚀 Kariéra & Spolupráce**\nVyberte konkrétní typ ticketu:",
                view=view,
                ephemeral=True
            )
        elif self.values[0] == "problems_reports":
            view = TicketTypeView(self.bot, "problems_reports")
            await interaction.response.send_message(
                "**📡 Problémy & Reporty**\nVyberte konkrétní typ ticketu:",
                view=view,
                ephemeral=True
            )

# View s konkrétními typy ticketů pro každou kategorii
class TicketTypeView(discord.ui.View):
    def __init__(self, bot, category: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.category = category
        
        # Přidání dropdown menu s konkrétními typy
        self.add_item(TicketTypeSelect(bot, category))

# Dropdown menu s konkrétními typy ticketů
class TicketTypeSelect(discord.ui.Select):
    def __init__(self, bot, category: str):
        self.bot = bot
        self.category = category
        
        # Definice možností podle kategorie
        if category == "rp_requests":
            options = [
                discord.SelectOption(label="🔫 Zbrojní průkaz", value="zbrojni", emoji="🔫"),
                discord.SelectOption(label="🏘️ Pozemek", value="pozemek", emoji="🏘️"),
                discord.SelectOption(label="🏢 Frakce", value="frakce", emoji="🏢"),
                discord.SelectOption(label="💍 Svatba", value="svatba", emoji="💍"),
                discord.SelectOption(label="☠️ CK", value="ck", emoji="☠️")
            ]
        elif category == "admin_technical":
            options = [
                discord.SelectOption(label="🔐 Unban", value="unban", emoji="🔐"),
                discord.SelectOption(label="📂 Úprava Frakce", value="uprava_frakce", emoji="📂"),
                discord.SelectOption(label="🏘️ Majetek", value="majetek", emoji="🏘️"),
                discord.SelectOption(label="🎁 Giveaway", value="giveaway", emoji="🎁")
            ]
        elif category == "career_collab":
            options = [
                discord.SelectOption(label="⚡ Game Staff", value="game_staff", emoji="⚡"),
                discord.SelectOption(label="🛡️ Moderator", value="moderator", emoji="🛡️"),
                discord.SelectOption(label="🛠️ Discord Staff", value="discord_staff", emoji="🛠️"),
                discord.SelectOption(label="🤝 Partnerství", value="partnerstvi", emoji="🤝")
            ]
        elif category == "problems_reports":
            options = [
                discord.SelectOption(label="❌ Stížnost", value="stiznost", emoji="❌"),
                discord.SelectOption(label="🔧 Bot problém", value="bot_problem", emoji="🔧"),
                discord.SelectOption(label="🛠️ Jiný problém", value="jiny_problem", emoji="🛠️")
            ]
        else:
            options = []
        
        super().__init__(
            placeholder=f"📝 Vyberte typ ticketu...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        cog = self.bot.get_cog('TicketSystem')
        if not cog:
            await interaction.response.send_message("❌ Ticket systém není dostupný.", ephemeral=True)
            return
        
        ticket_type = self.values[0]
        
        # Mapování typů ticketů na české názvy pro zobrazení
        type_names = {
            "zbrojni": "Zbrojní průkaz",
            "pozemek": "Pozemek",
            "frakce": "Frakce",
            "svatba": "Svatba",
            "ck": "CK",
            "unban": "Unban",
            "uprava_frakce": "Úprava Frakce",
            "majetek": "Majetek",
            "giveaway": "Giveaway",
            "game_staff": "Game Staff",
            "moderator": "Moderator",
            "discord_staff": "Discord Staff",
            "partnerstvi": "Partnerství",
            "stiznost": "Stížnost",
            "bot_problem": "Bot problém",
            "jiny_problem": "Jiný problém"
        }
        
        category_name = type_names.get(ticket_type, ticket_type)
        
        # Vytvořit ticket
        await cog._create_ticket(interaction, ticket_type, category_name)

# Hlavní třída TicketSystem
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_settings = {}
        self.active_tickets = {}
        self.ticket_history = []
        self.data_file = "tickets_data.json"
        
    async def load_ticket_settings(self):
        """Načte nastavení ticketů z databáze nebo vytvoří výchozí"""
        # Pokud existuje soubor s daty, načíst je
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.active_tickets = data.get('active_tickets', {})
                self.ticket_history = data.get('ticket_history', [])
                print(f"✅ Načteno {len(self.active_tickets)} aktivních ticketů a {len(self.ticket_history)} historických")
        
        # Výchozí nastavení pro všechny typy ticketů
        self.ticket_settings = {
            'zbrojni': {
                'category_name': '🔫 Zbrojní průkazy',
                'support_role': 'Game Staff',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Jak se jmenuje tvá postava?",
                    "2. Proč chceš zbrojní průkaz?",
                    "3. Má již tvá postava nějaké zkušenosti se zbraněmi?",
                    "4. Kde budeš zbraň přechovávat?",
                    "5. Jaký typ zbraně požaduješ?"
                ]
            },
            'pozemek': {
                'category_name': '🏘️ Pozemky',
                'support_role': 'Admin Team',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Jak se jmenuje tvá postava?",
                    "2. O jaký typ nemovitosti máš zájem?",
                    "3. Jaké je její umístění?",
                    "4. Jaký je účel nemovitosti?",
                    "5. Jakou částku jsi ochoten zaplatit?"
                ]
            },
            'frakce': {
                'category_name': '🏢 Frakce',
                'support_role': 'Game Staff',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Jak se jmenuje tvá postava?",
                    "2. Jaký typ frakce chceš založit?",
                    "3. Popiš účel a cíle frakce:",
                    "4. Kolik členů již máš?",
                    "5. Jakou roli budeš ve frakci mít?"
                ]
            },
            'svatba': {
                'category_name': '💍 Svatby',
                'support_role': 'Game Staff',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Jméno ženicha:",
                    "2. Jméno nevěsty:",
                    "3. Datum a čas svatby:",
                    "4. Místo konání:",
                    "5. Požadované speciální úpravy:"
                ]
            },
            'ck': {
                'category_name': '☠️ CK (Cestovní kanceláře)',
                'support_role': 'Game Staff',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Jméno CK:",
                    "2. Zakladatel:",
                    "3. Popis služeb:",
                    "4. Zamýšlené destinace:",
                    "5. Předpokládaný rozpočet:"
                ]
            },
            'unban': {
                'category_name': '🔐 Unban žádosti',
                'support_role': 'Admin Team',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Tvoje Discord jméno a tag:",
                    "2. Důvod banu:",
                    "3. Proč by měl být ban zrušen?",
                    "4. Co jsi se z této situace naučil?",
                    "5. Slibuješ, že budeš dodržovat pravidla?"
                ]
            },
            'uprava_frakce': {
                'category_name': '📂 Úpravy frakcí',
                'support_role': 'Admin Team',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Název frakce:",
                    "2. Co chceš upravit?",
                    "3. Důvod úpravy:",
                    "4. Navrhované změny:",
                    "5. Důkazy/screenshots:"
                ]
            },
            'majetek': {
                'category_name': '🏘️ Správa majetku',
                'support_role': 'Admin Team',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Typ majetku:",
                    "2. Umístění:",
                    "3. Současný vlastník:",
                    "4. Požadovaná změna:",
                    "5. Důvod změny:"
                ]
            },
            'giveaway': {
                'category_name': '🎁 Giveaway',
                'support_role': 'Admin Team',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Co budeš rozdávat?",
                    "2. Hodnota odměn:",
                    "3. Délka trvání:",
                    "4. Požadavky pro účastníky:",
                    "5. Jak bude probíhat losování?"
                ]
            },
            'game_staff': {
                'category_name': '⚡ Game Staff aplikace',
                'support_role': 'Staff Manager',
                'log_channel': 'staff-logs',
                'questions': [
                    "1. Tvé reálné jméno a věk:",
                    "2. Zkušenosti s administrací:",
                    "3. Proč chceš být Game Staff?",
                    "4. Kolik času můžeš věnovat?",
                    "5. Tvé přednosti a nedostatky:"
                ]
            },
            'moderator': {
                'category_name': '🛡️ Moderator aplikace',
                'support_role': 'Staff Manager',
                'log_channel': 'staff-logs',
                'questions': [
                    "1. Tvé reálné jméno a věk:",
                    "2. Zkušenosti s moderováním:",
                    "3. Proč chceš být Moderator?",
                    "4. Jak bys řešil konflikt mezi hráči?",
                    "5. Tvé časové možnosti:"
                ]
            },
            'discord_staff': {
                'category_name': '🛠️ Discord Staff aplikace',
                'support_role': 'Staff Manager',
                'log_channel': 'staff-logs',
                'questions': [
                    "1. Tvé reálné jméno a věk:",
                    "2. Zkušenosti s Discordem:",
                    "3. Proč chceš být Discord Staff?",
                    "4. Znáš programování nebo boty?",
                    "5. Nápady na zlepšení serveru:"
                ]
            },
            'partnerstvi': {
                'category_name': '🤝 Partnerství',
                'support_role': 'Community Manager',
                'log_channel': 'partner-logs',
                'questions': [
                    "1. Název serveru/komunity:",
                    "2. Počet členů:",
                    "3. Typ partnerství:",
                    "4. Co můžeš nabídnout?",
                    "5. Kontaktní osoba:"
                ]
            },
            'stiznost': {
                'category_name': '❌ Stížnosti',
                'support_role': 'Admin Team',
                'log_channel': 'report-logs',
                'questions': [
                    "1. Proti komu je stížnost?",
                    "2. Popis incidentu:",
                    "3. Datum a čas:",
                    "4. Důkazy/screenshots:",
                    "5. Svědci:"
                ]
            },
            'bot_problem': {
                'category_name': '🔧 Problémy s botem',
                'support_role': 'Bot Developer',
                'log_channel': 'tech-logs',
                'questions': [
                    "1. Jaký bot má problém?",
                    "2. Popis problému:",
                    "3. Kdy problém nastal?",
                    "4. Co jsi zkoušel?",
                    "5. Chybové hlášky/screenshots:"
                ]
            },
            'jiny_problem': {
                'category_name': '🛠️ Jiné problémy',
                'support_role': 'Support Team',
                'log_channel': 'ticket-logs',
                'questions': [
                    "1. Popiš svůj problém:",
                    "2. Kdy problém nastal?",
                    "3. Co jsi zkoušel?",
                    "4. Jak tě to ovlivňuje?",
                    "5. Další relevantní informace:"
                ]
            }
        }
        
        print(f'✅ Ticket systém připraven s {len(self.ticket_settings)} typy ticketů')
    
    async def save_ticket_data(self):
        """Uloží data ticketů do souboru"""
        data = {
            'active_tickets': self.active_tickets,
            'ticket_history': self.ticket_history[-100:]  # Uchováme posledních 100
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_ticket_settings()
        print(f'✅ Ticket systém připraven!')
        
        # Pravidelné ukládání dat každých 5 minut
        self.bot.loop.create_task(self.auto_save_data())
    
    async def auto_save_data(self):
        """Automatické ukládání dat každých 5 minut"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(300)  # 5 minut
            try:
                await self.save_ticket_data()
            except Exception as e:
                print(f"❌ Chyba při ukládání dat ticketů: {e}")
    
    async def _create_ticket(self, interaction: discord.Interaction, ticket_type: str, category_name: str):
        """Vytvoří ticket kanál"""
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        member = interaction.user
        
        # Zkontrolovat, zda už má aktivní ticket
        if member.id in self.active_tickets:
            ticket_data = self.active_tickets[member.id]
            channel = guild.get_channel(ticket_data['channel_id'])
            if channel:
                await interaction.followup.send(
                    f"❌ Již máš otevřený ticket: {channel.mention}. Nejprve zavři ten stávající.",
                    ephemeral=True
                )
                return
        
        # Získat konfiguraci pro tento typ ticketu
        config = self.ticket_settings.get(ticket_type, {})
        
        # Vytvořit kategorii, pokud neexistuje
        category_name_full = config.get('category_name', category_name)
        category = discord.utils.get(guild.categories, name=category_name_full)
        if not category:
            try:
                category = await guild.create_category(category_name_full)
                await category.edit(position=0)  # Přesunout na vrchol
            except discord.Forbidden:
                category = discord.utils.get(guild.categories, name='Tickets')
                if not category:
                    category = await guild.create_category('Tickets')
        
        # Vytvořit kanál
        timestamp = int(datetime.datetime.now().timestamp())
        channel_name = f"{ticket_type}-{member.display_name[:15]}-{timestamp % 10000:04d}"
        channel_name = channel_name.lower().replace(' ', '-')
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                read_message_history=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                manage_roles=True,
                embed_links=True,
                attach_files=True
            )
        }
        
        # Přidat support roli, pokud existuje
        role = None
        if 'support_role' in config:
            role = discord.utils.get(guild.roles, name=config['support_role'])
            if not role:
                # Zkusit najít roli podle části jména
                for guild_role in guild.roles:
                    if config['support_role'].lower() in guild_role.name.lower():
                        role = guild_role
                        break
            
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    attach_files=True,
                    embed_links=True
                )
        
        # Vytvořit kanál
        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket pro {member.display_name} | Typ: {category_name} | ID: {member.id}"
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Nemám oprávnění vytvořit kanál! Kontaktuj administrátora.",
                ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"❌ Chyba při vytváření kanálu: {e}",
                ephemeral=True
            )
            return
        
        # Uložit informace o ticketu
        self.active_tickets[member.id] = {
            'channel_id': ticket_channel.id,
            'type': ticket_type,
            'created_at': discord.utils.utcnow().isoformat(),
            'status': 'open',
            'owner_id': member.id,
            'owner_name': str(member),
            'category': category_name
        }
        
        # Přidat do historie
        self.ticket_history.append({
            'channel_id': ticket_channel.id,
            'type': ticket_type,
            'created_at': discord.utils.utcnow().isoformat(),
            'closed_at': None,
            'owner_id': member.id,
            'owner_name': str(member),
            'category': category_name,
            'status': 'open'
        })
        
        # Uložit data
        await self.save_ticket_data()
        
        # Vytvořit embed s informacemi
        embed = discord.Embed(
            title=f"🎫 Ticket - {category_name}",
            description=f"Ticket vytvořen pro {member.mention}",
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Typ", value=ticket_type, inline=True)
        embed.add_field(name="Vytvořil", value=member.mention, inline=True)
        embed.add_field(name="Status", value="🟢 Otevřeno", inline=True)
        embed.add_field(name="Čas vytvoření", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=False)
        
        # Přidat specifické otázky, pokud existují
        if 'questions' in config and config['questions']:
            questions_text = "\n".join([f"**{q}**" for q in config['questions']])
            embed.add_field(
                name="📝 K vyplnění:",
                value=f"Odpověz prosím na tyto otázky:\n\n{questions_text}",
                inline=False
            )
        
        embed.add_field(
            name="ℹ️ Informace",
            value="• Pište svůj problém/dotaz co nejpodrobněji\n• Buďte trpěliví, support vám brzy odpoví\n• Nepingujte členy support teamu zbytečně",
            inline=False
        )
        
        embed.set_footer(text=f"ID: {ticket_channel.id} | User ID: {member.id}")
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        
        # Přidat tlačítka pro správu ticketu
        view = TicketManagementView(self.bot, member.id, ticket_channel.id)
        
        # Mencionovat support roli a uživatele
        mention_text = f"{member.mention}"
        if role:
            mention_text += f" {role.mention}"
        
        # Odeslat zprávu
        await ticket_channel.send(
            content=mention_text,
            embed=embed,
            view=view
        )
        
        # Odeslat potvrzení uživateli
        await interaction.followup.send(
            f"✅ Ticket vytvořen: {ticket_channel.mention}\n"
            f"📋 **Otázky k vyplnění:**\n{chr(10).join(['• ' + q for q in config.get('questions', ['Žádné speciální otázky'])[:3]])}\n"
            f"⏳ Support team vám brzy odpoví.",
            ephemeral=True
        )
        
        # Logovat vytvoření ticketu
        await self._log_ticket_action(
            guild,
            f"📝 Ticket vytvořen",
            f"**Uživatel:** {member.mention} ({member.id})\n"
            f"**Typ:** {ticket_type}\n"
            f"**Název:** {category_name}\n"
            f"**Kanál:** {ticket_channel.mention}\n"
            f"**Kategorie:** {category.name}"
        )
    
    async def _log_ticket_action(self, guild, action: str, details: str):
        """Logování akcí s tickety"""
        # Nejprve zkusit najít log kanál podle jména
        log_channel = discord.utils.get(guild.text_channels, name='ticket-logs')
        
        # Pokud neexistuje, zkusit najít jakýkoli kanál s "log" v názvu
        if not log_channel:
            for channel in guild.text_channels:
                if 'log' in channel.name.lower():
                    log_channel = channel
                    break
        
        # Pokud stále neexistuje, vytvořit nový
        if not log_channel:
            try:
                category = discord.utils.get(guild.categories, name='📊 Logs')
                if not category:
                    category = await guild.create_category('📊 Logs')
                
                log_channel = await guild.create_text_channel(
                    name='ticket-logs',
                    category=category,
                    reason='Automatické vytvoření log kanálu pro tickety'
                )
            except:
                return  # Pokud nelze vytvořit, prostě nelogovat
        
        if log_channel:
            embed = discord.Embed(
                title=action,
                description=details,
                color=0x3498db,
                timestamp=discord.utils.utcnow()
            )
            await log_channel.send(embed=embed)
    
    async def _close_ticket(self, channel_id: int, closer: discord.Member, reason: str = "Nezadáno"):
        """Zavře ticket"""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        # Získat vlastníka ticketu
        owner_id = None
        ticket_data = None
        for uid, data in self.active_tickets.items():
            if data['channel_id'] == channel_id:
                owner_id = uid
                ticket_data = data
                break
        
        if not ticket_data:
            return
        
        # Aktualizovat název kanálu
        try:
            new_name = f"closed-{channel.name}"
            if len(new_name) > 100:
                new_name = new_name[:97] + "..."
            await channel.edit(name=new_name)
        except:
            pass
        
        # Odebrat oprávnění všem členům kromě staffu
        try:
            for member in channel.members:
                if member.id != owner_id and not member.guild_permissions.manage_channels:
                    await channel.set_permissions(member, read_messages=False, send_messages=False)
        except:
            pass
        
        # Přesunout do uzavřené kategorie
        closed_category = discord.utils.get(channel.guild.categories, name="📁 Uzavřené tickety")
        if not closed_category:
            try:
                closed_category = await channel.guild.create_category("📁 Uzavřené tickety")
                await closed_category.edit(position=1)
            except:
                closed_category = channel.category
        
        try:
            await channel.edit(category=closed_category)
        except:
            pass
        
        # Odeslat zprávu o uzavření
        embed = discord.Embed(
            title="🔒 Ticket uzavřen",
            description=f"Ticket byl uzavřen uživatelem {closer.mention}",
            color=0xe74c3c,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Důvod", value=reason if reason else "Nezadáno", inline=False)
        embed.add_field(name="Uzavřel", value=closer.mention, inline=True)
        embed.add_field(name="Vlastník", value=f"<@{owner_id}>" if owner_id else "Neznámý", inline=True)
        embed.add_field(name="Čas uzavření", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=False)
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="🗑️ Smazat ticket",
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_ticket_{channel_id}"
        ))
        view.add_item(discord.ui.Button(
            label="📋 Transcript",
            style=discord.ButtonStyle.secondary,
            custom_id=f"transcript_{channel_id}"
        ))
        view.add_item(discord.ui.Button(
            label="🔓 Znovu otevřít",
            style=discord.ButtonStyle.success,
            custom_id=f"reopen_ticket_{channel_id}"
        ))
        
        await channel.send(embed=embed, view=view)
        
        # Aktualizovat status v aktivních ticketch
        if owner_id in self.active_tickets:
            self.active_tickets[owner_id]['status'] = 'closed'
            self.active_tickets[owner_id]['closed_by'] = str(closer)
            self.active_tickets[owner_id]['closed_at'] = discord.utils.utcnow().isoformat()
            self.active_tickets[owner_id]['close_reason'] = reason
        
        # Aktualizovat historii
        for i, ticket in enumerate(self.ticket_history):
            if ticket.get('channel_id') == channel_id and ticket.get('status') == 'open':
                self.ticket_history[i]['status'] = 'closed'
                self.ticket_history[i]['closed_at'] = discord.utils.utcnow().isoformat()
                self.ticket_history[i]['closed_by'] = str(closer)
                self.ticket_history[i]['close_reason'] = reason
                break
        
        # Uložit data
        await self.save_ticket_data()
        
        # Logovat uzavření
        await self._log_ticket_action(
            channel.guild,
            f"🔒 Ticket uzavřen",
            f"**Kanál:** {channel.mention}\n"
            f"**Typ:** {ticket_data.get('type', 'Neznámý')}\n"
            f"**Vlastník:** <@{owner_id}>\n"
            f"**Uzavřel:** {closer.mention}\n"
            f"**Důvod:** {reason}"
        )
        
        # Odeslat DM vlastníkovi, pokud je to někdo jiný než ten, kdo zavírá
        if owner_id and owner_id != closer.id:
            try:
                owner = await self.bot.fetch_user(owner_id)
                if owner:
                    dm_embed = discord.Embed(
                        title="🔒 Tvůj ticket byl uzavřen",
                        description=f"Ticket **{ticket_data.get('category', 'Neznámý')}** byl uzavřen.",
                        color=0xe74c3c,
                        timestamp=discord.utils.utcnow()
                    )
                    dm_embed.add_field(name="Kanál", value=channel.mention, inline=True)
                    dm_embed.add_field(name="Uzavřel", value=str(closer), inline=True)
                    dm_embed.add_field(name="Důvod", value=reason if reason else "Nezadáno", inline=False)
                    dm_embed.add_field(name="Zprávy", value="Všechny zprávy zůstávají dostupné pro review.", inline=False)
                    
                    await owner.send(embed=dm_embed)
            except:
                pass  # Pokud nelze poslat DM, nic se neděje
    
    async def _reopen_ticket(self, channel_id: int, reopener: discord.Member):
        """Znovu otevře uzavřený ticket"""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        # Najít vlastníka ticketu v historii
        owner_id = None
        for ticket in self.ticket_history:
            if ticket.get('channel_id') == channel_id and ticket.get('status') == 'closed':
                owner_id = ticket.get('owner_id')
                ticket_type = ticket.get('type')
                category_name = ticket.get('category')
                break
        
        if not owner_id:
            return
        
        # Aktualizovat název kanálu
        try:
            new_name = channel.name.replace('closed-', '')
            await channel.edit(name=new_name)
        except:
            pass
        
        # Přesunout zpět do správné kategorie
        config = self.ticket_settings.get(ticket_type, {})
        category_name_full = config.get('category_name', category_name)
        category = discord.utils.get(channel.guild.categories, name=category_name_full)
        
        if category:
            try:
                await channel.edit(category=category)
            except:
                pass
        
        # Obnovit oprávnění vlastníkovi
        try:
            owner = channel.guild.get_member(owner_id)
            if owner:
                await channel.set_permissions(owner, read_messages=True, send_messages=True)
        except:
            pass
        
        # Odeslat zprávu o znovuotevření
        embed = discord.Embed(
            title="🔓 Ticket znovu otevřen",
            description=f"Ticket byl znovu otevřen uživatelem {reopener.mention}",
            color=0x2ecc71,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Znovu otevřel", value=reopener.mention, inline=True)
        embed.add_field(name="Vlastník", value=f"<@{owner_id}>", inline=True)
        embed.add_field(name="Čas", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=True)
        
        await channel.send(embed=embed)
        
        # Aktualizovat data
        if owner_id in self.active_tickets:
            self.active_tickets[owner_id]['status'] = 'open'
            self.active_tickets[owner_id]['reopened_at'] = discord.utils.utcnow().isoformat()
            self.active_tickets[owner_id]['reopened_by'] = str(reopener)
        
        # Aktualizovat historii
        for i, ticket in enumerate(self.ticket_history):
            if ticket.get('channel_id') == channel_id:
                self.ticket_history[i]['status'] = 'open'
                self.ticket_history[i]['reopened_at'] = discord.utils.utcnow().isoformat()
                self.ticket_history[i]['reopened_by'] = str(reopener)
                break
        
        # Přidat zpět management view
        view = TicketManagementView(self.bot, owner_id, channel_id)
        await channel.send("**🔄 Ticket Management:**", view=view)
        
        # Uložit data
        await self.save_ticket_data()
        
        # Logovat znovuotevření
        await self._log_ticket_action(
            channel.guild,
            f"🔓 Ticket znovu otevřen",
            f"**Kanál:** {channel.mention}\n"
            f"**Typ:** {ticket_type}\n"
            f"**Vlastník:** <@{owner_id}>\n"
            f"**Znovu otevřel:** {reopener.mention}"
        )
    
    async def _delete_ticket(self, channel_id: int, deleter: discord.Member):
        """Smaže ticket kanál"""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        # Zálohovat informace před smazáním
        ticket_info = None
        for uid, data in self.active_tickets.items():
            if data['channel_id'] == channel_id:
                ticket_info = data.copy()
                ticket_info['owner_id'] = uid
                break
        
        if not ticket_info:
            # Zkusit najít v historii
            for ticket in self.ticket_history:
                if ticket.get('channel_id') == channel_id:
                    ticket_info = ticket.copy()
                    break
        
        # Odstranit z aktivních ticketů
        owner_id = ticket_info.get('owner_id') if ticket_info else None
        if owner_id and owner_id in self.active_tickets:
            del self.active_tickets[owner_id]
        
        # Aktualizovat historii
        if ticket_info:
            for i, ticket in enumerate(self.ticket_history):
                if ticket.get('channel_id') == channel_id:
                    self.ticket_history[i]['status'] = 'deleted'
                    self.ticket_history[i]['deleted_at'] = discord.utils.utcnow().isoformat()
                    self.ticket_history[i]['deleted_by'] = str(deleter)
                    break
        
        # Uložit data
        await self.save_ticket_data()
        
        # Smazat kanál
        try:
            await channel.delete(reason=f"Ticket smazán uživatelem {deleter}")
        except Exception as e:
            print(f"Chyba při mazání kanálu: {e}")
            return
        
        # Logovat smazání
        if ticket_info:
            await self._log_ticket_action(
                deleter.guild,
                f"🗑️ Ticket smazán",
                f"**Typ:** {ticket_info.get('type', 'Neznámý')}\n"
                f"**Vlastník:** <@{ticket_info.get('owner_id', 'Neznámý')}>\n"
                f"**Smazal:** {deleter.mention}\n"
                f"**Kanál ID:** {channel_id}"
            )
    
    async def _add_user_to_ticket(self, channel_id: int, user: discord.Member):
        """Přidá uživatele do ticketu"""
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.set_permissions(user, read_messages=True, send_messages=True)
            embed = discord.Embed(
                title="👥 Uživatel přidán",
                description=f"{user.mention} byl přidán do ticketu",
                color=0x2ecc71
            )
            await channel.send(embed=embed)
    
    async def _remove_user_from_ticket(self, channel_id: int, user: discord.Member):
        """Odebere uživatele z ticketu"""
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.set_permissions(user, overwrite=None)
            embed = discord.Embed(
                title="👥 Uživatel odebrán",
                description=f"{user.mention} byl odebrán z ticketu",
                color=0xe74c3c
            )
            await channel.send(embed=embed)
    
    async def _create_transcript(self, channel_id: int):
        """Vytvoří transcript ticketu (základní implementace)"""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return None
        
        # Získat zprávy
        messages = []
        async for message in channel.history(limit=500, oldest_first=True):
            messages.append(message)
        
        # Vytvořit jednoduchý transcript
        transcript = f"📋 Transcript ticketu #{channel.name}\n"
        transcript += f"📅 Vytvořeno: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        transcript += f"🔗 Odkaz: {channel.mention}\n"
        transcript += "="*50 + "\n\n"
        
        for message in messages:
            timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author = str(message.author)
            content = message.content if message.content else "(bez textu)"
            
            if message.attachments:
                attachments = ", ".join([a.url for a in message.attachments])
                content += f" [Přílohy: {attachments}]"
            
            transcript += f"[{timestamp}] {author}: {content}\n"
        
        return transcript
    
    # Slash příkazy pro správu ticketů
    @app_commands.command(name="ticket_close", description="Zavře aktuální ticket")
    @app_commands.describe(reason="Důvod uzavření")
    async def ticket_close(self, interaction: discord.Interaction, reason: str = "Nezadáno"):
        """Zavře ticket"""
        if not any(interaction.channel.name.startswith(prefix) for prefix in 
                  ['zbrojni-', 'pozemek-', 'frakce-', 'svatba-', 'ck-', 'unban-', 
                   'uprava_frakce-', 'majetek-', 'giveaway-', 'game_staff-', 
                   'moderator-', 'discord_staff-', 'partnerstvi-', 'stiznost-', 
                   'bot_problem-', 'jiny_problem-', 'closed-']):
            await interaction.response.send_message(
                "❌ Tento příkaz lze použít pouze v ticket kanálu!", 
                ephemeral=True
            )
            return
        
        await self._close_ticket(interaction.channel.id, interaction.user, reason)
        await interaction.response.send_message("✅ Ticket byl uzavřen.", ephemeral=True)
    
    @app_commands.command(name="ticket_add", description="Přidá uživatele do ticketu")
    @app_commands.describe(user="Uživatel k přidání")
    async def ticket_add(self, interaction: discord.Interaction, user: discord.Member):
        """Přidá uživatele do ticketu"""
        if not any(interaction.channel.name.startswith(prefix) for prefix in 
                  ['zbrojni-', 'pozemek-', 'frakce-', 'svatba-', 'ck-', 'unban-', 
                   'uprava_frakce-', 'majetek-', 'giveaway-', 'game_staff-', 
                   'moderator-', 'discord_staff-', 'partnerstvi-', 'stiznost-', 
                   'bot_problem-', 'jiny_problem-']):
            await interaction.response.send_message(
                "❌ Tento příkaz lze použít pouze v ticket kanálu!", 
                ephemeral=True
            )
            return
        
        await self._add_user_to_ticket(interaction.channel.id, user)
        await interaction.response.send_message(f"✅ {user.mention} byl přidán do ticketu.", ephemeral=True)
    
    @app_commands.command(name="ticket_remove", description="Odebere uživatele z ticketu")
    @app_commands.describe(user="Uživatel k odebrání")
    async def ticket_remove(self, interaction: discord.Interaction, user: discord.Member):
        """Odebere uživatele z ticketu"""
        if not any(interaction.channel.name.startswith(prefix) for prefix in 
                  ['zbrojni-', 'pozemek-', 'frakce-', 'svatba-', 'ck-', 'unban-', 
                   'uprava_frakce-', 'majetek-', 'giveaway-', 'game_staff-', 
                   'moderator-', 'discord_staff-', 'partnerstvi-', 'stiznost-', 
                   'bot_problem-', 'jiny_problem-']):
            await interaction.response.send_message(
                "❌ Tento příkaz lze použít pouze v ticket kanálu!", 
                ephemeral=True
            )
            return
        
        await self._remove_user_from_ticket(interaction.channel.id, user)
        await interaction.response.send_message(f"✅ {user.mention} byl odebrán z ticketu.", ephemeral=True)
    
    @app_commands.command(name="ticket_panel", description="Vytvoří panel pro všechny typy tiketů")
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_panel_complete(self, interaction: discord.Interaction):
        """Vytvoření kompletního ticket panelu"""
        embed = discord.Embed(
            title="🎫 Veltrix Support System",
            description="**Komplexní systém pro všechny typy žádostí a problémů**\n\n"
                       "Vyberte příslušnou kategorii a typ ticketu, který potřebujete vytvořit.\n"
                       "Support team vám odpoví co nejdříve.",
            color=0x3498db
        )
        
        embed.add_field(
            name="🎭 | RP ŽÁDOSTI",
            value="• 🔫 Zbrojní průkaz\n• 🏘️ Pozemek\n• 🏢 Frakce\n• 💍 Svatba\n• ☠️ CK",
            inline=True
        )
        
        embed.add_field(
            name="🗝️┃Admin & Technické",
            value="• 🔐 Unban\n• 📂 Úprava Frakce\n• 🏘️ Majetek\n• 🎁 Giveaway",
            inline=True
        )
        
        embed.add_field(
            name="🚀 | Kariéra & Spolupráce",
            value="• ⚡ Game Staff\n• 🛡️ Moderator\n• 🛠️ Discord Staff\n• 🤝 Partnerství",
            inline=True
        )
        
        embed.add_field(
            name="📡 | Problémy & Reporty",
            value="• ❌ Stížnost\n• 🔧 Bot problém\n• 🛠️ Jiný problém",
            inline=True
        )
        
        embed.add_field(
            name="📊 Statistiky",
            value=f"• 🟢 Aktivní: {len([t for t in self.active_tickets.values() if t.get('status') == 'open'])}\n"
                  f"• 📁 Celkem: {len(self.active_tickets)}\n"
                  f"• 📈 Dnes: {len([t for t in self.ticket_history if datetime.datetime.fromisoformat(t.get('created_at', '2000-01-01')).date() == datetime.datetime.now().date()])}",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Časy odezvy",
            value="• RP Žádosti: 1-24h\n• Technické: 1-12h\n• Staff: 1-48h\n• Reporty: 1-6h",
            inline=True
        )
        
        embed.set_footer(text="Vyberte kategorii z dropdown menu níže | Support Team Veltrix")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1234567890123456789.png")  # Přidej vlastní thumbnail URL
        
        view = TicketPanelView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="ticket_stats", description="Zobrazí statistiky ticketů")
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        """Zobrazí statistiky ticketů"""
        open_tickets = len([t for t in self.active_tickets.values() if t.get('status') == 'open'])
        closed_tickets = len([t for t in self.ticket_history if t.get('status') == 'closed'])
        total_tickets = len(self.ticket_history)
        
        # Spočítat ticket podle typu
        type_counts = {}
        for ticket in self.ticket_history:
            t_type = ticket.get('type', 'unknown')
            type_counts[t_type] = type_counts.get(t_type, 0) + 1
        
        # Nejčastější typy
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_types = "\n".join([f"• {k}: {v}" for k, v in sorted_types])
        
        # Dnešní tickety
        today = datetime.datetime.now().date()
        today_tickets = len([t for t in self.ticket_history 
                           if datetime.datetime.fromisoformat(t.get('created_at', '2000-01-01')).date() == today])
        
        embed = discord.Embed(
            title="📊 Kompletní statistiky Ticketů",
            color=0x9b59b6,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="🟢 Aktivní tickety", value=str(open_tickets), inline=True)
        embed.add_field(name="🔒 Uzavřené tickety", value=str(closed_tickets), inline=True)
        embed.add_field(name="📈 Celkem vytvořeno", value=str(total_tickets), inline=True)
        embed.add_field(name="📅 Dnešní tickety", value=str(today_tickets), inline=True)
        embed.add_field(name="📊 Úspěšnost", value=f"{(closed_tickets/max(total_tickets, 1))*100:.1f}%", inline=True)
        embed.add_field(name="⏱️ Průměrná doba", value="24h", inline=True)
        
        embed.add_field(name="🏆 Nejčastější typy", value=top_types if top_types else "Žádná data", inline=False)
        
        # Zobrazit posledních 5 ticketů
        recent_tickets = self.ticket_history[-5:] if self.ticket_history else []
        if recent_tickets:
            recent_text = ""
            for ticket in reversed(recent_tickets):
                time = datetime.datetime.fromisoformat(ticket['created_at']).strftime('%d.%m. %H:%M')
                status = "🟢" if ticket.get('status') == 'open' else "🔒"
                recent_text += f"{status} {ticket.get('type', 'N/A')} - <t:{int(datetime.datetime.fromisoformat(ticket['created_at']).timestamp())}:R>\n"
            
            embed.add_field(name="🕐 Poslední tickety", value=recent_text, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="ticket_cleanup", description="Vyčistí staré uzavřené tickety")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(days="Počet dnů (starší tickety budou smazány)")
    async def ticket_cleanup(self, interaction: discord.Interaction, days: int = 7):
        """Vyčistí staré uzavřené tickety"""
        await interaction.response.defer(ephemeral=True)
        
        count = 0
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        for category in interaction.guild.categories:
            if "uzavřené" in category.name.lower() or "closed" in category.name.lower():
                for channel in category.channels:
                    if isinstance(channel, discord.TextChannel) and channel.name.startswith("closed-"):
                        # Zkontrolovat stáří
                        created_at = channel.created_at
                        if created_at < cutoff_date:
                            try:
                                await channel.delete(reason=f"Automatický cleanup starší než {days} dní")
                                count += 1
                            except:
                                pass
        
        await interaction.followup.send(f"✅ Smazáno {count} starých ticketů (starších než {days} dní).", ephemeral=True)
    
    @app_commands.command(name="ticket_info", description="Zobrazí informace o aktuálním ticketu")
    async def ticket_info(self, interaction: discord.Interaction):
        """Zobrazí informace o aktuálním ticketu"""
        if not any(interaction.channel.name.startswith(prefix) for prefix in 
                  ['zbrojni-', 'pozemek-', 'frakce-', 'svatba-', 'ck-', 'unban-', 
                   'uprava_frakce-', 'majetek-', 'giveaway-', 'game_staff-', 
                   'moderator-', 'discord_staff-', 'partnerstvi-', 'stiznost-', 
                   'bot_problem-', 'jiny_problem-', 'closed-']):
            await interaction.response.send_message(
                "❌ Tento příkaz lze použít pouze v ticket kanálu!", 
                ephemeral=True
            )
            return
        
        # Najít informace o ticketu
        ticket_info = None
        for uid, data in self.active_tickets.items():
            if data['channel_id'] == interaction.channel.id:
                ticket_info = data
                owner_id = uid
                break
        
        if not ticket_info:
            # Zkusit najít v historii
            for ticket in self.ticket_history:
                if ticket.get('channel_id') == interaction.channel.id:
                    ticket_info = ticket
                    owner_id = ticket.get('owner_id')
                    break
        
        if not ticket_info:
            await interaction.response.send_message("❌ Informace o ticketu nebyly nalezeny.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📄 Informace o ticketu",
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        
        created_at = datetime.datetime.fromisoformat(ticket_info.get('created_at', datetime.datetime.now().isoformat()))
        embed.add_field(name="Typ", value=ticket_info.get('type', 'Neznámý'), inline=True)
        embed.add_field(name="Kategorie", value=ticket_info.get('category', 'Neznámá'), inline=True)
        embed.add_field(name="Status", value=ticket_info.get('status', 'Neznámý').upper(), inline=True)
        embed.add_field(name="Vlastník", value=f"<@{owner_id}>", inline=True)
        embed.add_field(name="Vytvořeno", value=f"<t:{int(created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Kanál ID", value=str(interaction.channel.id), inline=True)
        
        if ticket_info.get('closed_at'):
            closed_at = datetime.datetime.fromisoformat(ticket_info['closed_at'])
            embed.add_field(name="Uzavřeno", value=f"<t:{int(closed_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Uzavřel", value=ticket_info.get('closed_by', 'Neznámý'), inline=True)
            embed.add_field(name="Důvod", value=ticket_info.get('close_reason', 'Nezadáno'), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# View pro správu jednotlivého ticketu
class TicketManagementView(discord.ui.View):
    """View pro správu jednotlivého ticketu"""
    def __init__(self, bot, owner_id: int, channel_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.owner_id = owner_id
        self.channel_id = channel_id
    
    @discord.ui.button(label="🔒 Zavřít", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Nemáš oprávnění zavřít tento ticket!", ephemeral=True)
            return
        
        modal = CloseTicketModal(self.bot, self.channel_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="➕ Přidat uživatele", style=discord.ButtonStyle.success, custom_id="add_user_button")
    async def add_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Nemáš oprávnění upravovat tento ticket!", ephemeral=True)
            return
        
        modal = AddUserModal(self.bot, self.channel_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📋 Transcript", style=discord.ButtonStyle.secondary, custom_id="transcript_button")
    async def transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        cog = self.bot.get_cog('TicketSystem')
        if cog:
            transcript = await cog._create_transcript(self.channel_id)
            if transcript:
                # Omezit délku kvůli Discord limitům
                if len(transcript) > 1900:
                    transcript = transcript[:1900] + "\n... (zkráceno)"
                
                # Poslat jako soubor
                from io import StringIO
                transcript_file = StringIO(transcript)
                
                await interaction.followup.send(
                    "📄 Zde je transcript ticketu:",
                    file=discord.File(transcript_file, filename=f"transcript_{self.channel_id}.txt"),
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Nepodařilo se vytvořit transcript.", ephemeral=True)

# Modal pro zadání důvodu uzavření ticketu
class CloseTicketModal(discord.ui.Modal, title="Zavřít Ticket"):
    """Modal pro zadání důvodu uzavření ticketu"""
    reason = discord.ui.TextInput(
        label="Důvod uzavření",
        placeholder="Zadejte důvod uzavření ticketu...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True
    )
    
    def __init__(self, bot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        cog = self.bot.get_cog('TicketSystem')
        if cog:
            await cog._close_ticket(self.channel_id, interaction.user, self.reason.value)
            await interaction.followup.send("✅ Ticket byl uzavřen.", ephemeral=True)

# Modal pro přidání uživatele do ticketu
class AddUserModal(discord.ui.Modal, title="Přidat uživatele do ticketu"):
    """Modal pro přidání uživatele do ticketu"""
    user_id = discord.ui.TextInput(
        label="ID uživatele",
        placeholder="Zadejte Discord ID uživatele...",
        style=discord.TextStyle.short,
        max_length=20,
        required=True
    )
    
    def __init__(self, bot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            user_id = int(self.user_id.value)
            user = interaction.guild.get_member(user_id)
            
            if not user:
                await interaction.followup.send("❌ Uživatel nebyl nalezen na serveru!", ephemeral=True)
                return
            
            cog = self.bot.get_cog('TicketSystem')
            if cog:
                await cog._add_user_to_ticket(self.channel_id, user)
                await interaction.followup.send(f"✅ {user.mention} byl přidán do ticketu.", ephemeral=True)
        
        except ValueError:
            await interaction.followup.send("❌ Neplatné ID uživatele!", ephemeral=True)

# Event listener pro interakce s tlačítky
@commands.Cog.listener()
async def on_interaction(self, interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id', '')
        
        # Zpracování tlačítek pro uzavřené tickety
        if custom_id.startswith('delete_ticket_'):
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ Nemáš oprávnění smazat tento ticket!", ephemeral=True)
                return
            
            channel_id = int(custom_id.split('_')[-1])
            cog = self.bot.get_cog('TicketSystem')
            if cog:
                await cog._delete_ticket(channel_id, interaction.user)
                await interaction.response.send_message("🗑️ Ticket byl smazán.", ephemeral=True)
        
        elif custom_id.startswith('reopen_ticket_'):
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ Nemáš oprávnění znovu otevřít tento ticket!", ephemeral=True)
                return
            
            channel_id = int(custom_id.split('_')[-1])
            cog = self.bot.get_cog('TicketSystem')
            if cog:
                await cog._reopen_ticket(channel_id, interaction.user)
                await interaction.response.send_message("🔓 Ticket byl znovu otevřen.", ephemeral=True)
        
        elif custom_id.startswith('transcript_'):
            await interaction.response.defer(ephemeral=True)
            
            channel_id = int(custom_id.split('_')[-1])
            cog = self.bot.get_cog('TicketSystem')
            if cog:
                transcript = await cog._create_transcript(channel_id)
                if transcript:
                    from io import StringIO
                    transcript_file = StringIO(transcript)
                    
                    await interaction.followup.send(
                        "📄 Zde je transcript ticketu:",
                        file=discord.File(transcript_file, filename=f"transcript_{channel_id}.txt"),
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send("❌ Nepodařilo se vytvořit transcript.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))