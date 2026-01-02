import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Dict, Optional

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_settings = {}
        self.active_tickets = {}
        
    async def load_ticket_settings(self):
        # Toto by mohlo být načítání z databáze
        # Pro demonstraci používám pevná nastavení
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
            # Přidej další konfigurace pro všechny typy ticketů
        }
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_ticket_settings()
        print(f'✅ Ticket systém připraven!')
    
    async def _create_ticket(self, interaction: discord.Interaction, ticket_type: str, category_name: str):
        """Vytvoří ticket kanál"""
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        member = interaction.user
        
        # Zkontrolovat, zda už má aktivní ticket
        if member.id in self.active_tickets:
            await interaction.followup.send(
                "❌ Již máš otevřený ticket. Nejprve zavři ten stávající.",
                ephemeral=True
            )
            return
        
        # Získat konfiguraci pro tento typ ticketu
        config = self.ticket_settings.get(ticket_type, {})
        
        # Vytvořit kategorii, pokud neexistuje
        category = discord.utils.get(guild.categories, name=config.get('category_name', category_name))
        if not category:
            category = await guild.create_category(config.get('category_name', category_name))
        
        # Vytvořit kanál
        channel_name = f"{ticket_type}-{member.display_name[:20]}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True
            )
        }
        
        # Přidat support roli, pokud existuje
        if 'support_role' in config:
            role = discord.utils.get(guild.roles, name=config['support_role'])
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True
                )
        
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites
        )
        
        # Uložit informace o ticketu
        self.active_tickets[member.id] = {
            'channel_id': ticket_channel.id,
            'type': ticket_type,
            'created_at': discord.utils.utcnow(),
            'status': 'open'
        }
        
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
        
        # Přidat specifické otázky, pokud existují
        if 'questions' in config and config['questions']:
            questions_text = "\n".join([f"• {q}" for q in config['questions']])
            embed.add_field(
                name="📝 K vyplnění:",
                value=f"Odpověz prosím na tyto otázky:\n{questions_text}",
                inline=False
            )
        
        embed.set_footer(text=f"ID: {ticket_channel.id}")
        
        # Přidat tlačítka pro správu ticketu
        view = TicketManagementView(self.bot, member.id)
        
        # Odeslat zprávu
        await ticket_channel.send(
            content=f"{member.mention} {role.mention if role else ''}",
            embed=embed,
            view=view
        )
        
        # Odeslat potvrzení uživateli
        await interaction.followup.send(
            f"✅ Ticket vytvořen: {ticket_channel.mention}",
            ephemeral=True
        )
        
        # Logovat vytvoření ticketu
        await self._log_ticket_action(
            guild,
            f"📝 Ticket vytvořen",
            f"**Uživatel:** {member.mention} ({member.id})\n"
            f"**Typ:** {ticket_type}\n"
            f"**Kanál:** {ticket_channel.mention}\n"
            f"**Kategorie:** {category_name}"
        )
    
    async def _log_ticket_action(self, guild, action: str, details: str):
        """Logování akcí s tickety"""
        log_channel = discord.utils.get(guild.text_channels, name='ticket-logs')
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
        for uid, data in self.active_tickets.items():
            if data['channel_id'] == channel_id:
                owner_id = uid
                break
        
        # Aktualizovat název kanálu
        await channel.edit(name=f"closed-{channel.name}")
        
        # Odebrat oprávnění všem kromě administrátorů
        overwrites = channel.overwrites
        for target, overwrite in overwrites.items():
            if isinstance(target, discord.Member):
                if target.id != owner_id and not target.guild_permissions.manage_channels:
                    await channel.set_permissions(target, read_messages=False)
        
        # Přesunout do uzavřené kategorie
        closed_category = discord.utils.get(channel.guild.categories, name="📁 Uzavřené tickety")
        if not closed_category:
            closed_category = await channel.guild.create_category("📁 Uzavřené tickety")
        
        await channel.edit(category=closed_category)
        
        # Odeslat zprávu o uzavření
        embed = discord.Embed(
            title="🔒 Ticket uzavřen",
            description=f"Ticket byl uzavřen uživatelem {closer.mention}",
            color=0xe74c3c,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Důvod", value=reason, inline=False)
        embed.add_field(name="Uzavřel", value=closer.mention, inline=True)
        embed.add_field(name="Čas", value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>", inline=True)
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Smazat ticket",
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_ticket_{channel_id}"
        ))
        
        await channel.send(embed=embed, view=view)
        
        # Odstranit z aktivních ticketů
        if owner_id in self.active_tickets:
            del self.active_tickets[owner_id]
        
        # Logovat uzavření
        await self._log_ticket_action(
            channel.guild,
            f"🔒 Ticket uzavřen",
            f"**Kanál:** {channel.mention}\n"
            f"**Uzavřel:** {closer.mention}\n"
            f"**Důvod:** {reason}"
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
    
    # Slash příkazy pro správu ticketů
    @app_commands.command(name="ticket_close", description="Zavře aktuální ticket")
    @app_commands.describe(reason="Důvod uzavření")
    async def ticket_close(self, interaction: discord.Interaction, reason: str = "Nezadáno"):
        """Zavře ticket"""
        if not interaction.channel.name.startswith(tuple(['zbrojni-', 'pozemek-', 'frakce-', 'svatba-', 'ck-', 'unban-', 'uprava_frakce-', 'majetek-', 'giveaway-', 'game_staff-', 'moderator-', 'discord_staff-', 'partnerstvi-', 'stiznost-', 'bot_problem-', 'jiny_problem-'])):
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v ticket kanálu!", ephemeral=True)
            return
        
        await self._close_ticket(interaction.channel.id, interaction.user, reason)
        await interaction.response.send_message("✅ Ticket byl uzavřen.", ephemeral=True)
    
    @app_commands.command(name="ticket_add", description="Přidá uživatele do ticketu")
    @app_commands.describe(user="Uživatel k přidání")
    async def ticket_add(self, interaction: discord.Interaction, user: discord.Member):
        """Přidá uživatele do ticketu"""
        await self._add_user_to_ticket(interaction.channel.id, user)
        await interaction.response.send_message(f"✅ {user.mention} byl přidán do ticketu.", ephemeral=True)
    
    @app_commands.command(name="ticket_remove", description="Odebere uživatele z ticketu")
    @app_commands.describe(user="Uživatel k odebrání")
    async def ticket_remove(self, interaction: discord.Interaction, user: discord.Member):
        """Odebere uživatele z ticketu"""
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
        
        embed.set_footer(text="Vyberte kategorii z dropdown menu níže")
        
        view = TicketPanelView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)
    
    # Příkaz pro statistiky ticketů
    @app_commands.command(name="ticket_stats", description="Zobrazí statistiky ticketů")
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        """Zobrazí statistiky ticketů"""
        open_tickets = len([t for t in self.active_tickets.values() if t['status'] == 'open'])
        total_tickets = len(self.active_tickets)
        
        embed = discord.Embed(
            title="📊 Statistiky Ticketů",
            color=0x9b59b6,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(name="Aktivní tickety", value=str(open_tickets), inline=True)
        embed.add_field(name="Celkem vytvořeno", value=str(total_tickets), inline=True)
        embed.add_field(name="Systém status", value="🟢 Online", inline=True)
        
        if total_tickets > 0:
            types_count = {}
            for ticket in self.active_tickets.values():
                types_count[ticket['type']] = types_count.get(ticket['type'], 0) + 1
            
            types_text = "\n".join([f"• {k}: {v}" for k, v in types_count.items()])
            embed.add_field(name="Typy ticketů", value=types_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

class TicketManagementView(discord.ui.View):
    """View pro správu jednotlivého ticketu"""
    def __init__(self, bot, owner_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.owner_id = owner_id
    
    @discord.ui.button(label="🔒 Zavřít", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Nemáš oprávnění zavřít tento ticket!", ephemeral=True)
            return
        
        modal = CloseTicketModal(self.bot, interaction.channel.id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="➕ Přidat uživatele", style=discord.ButtonStyle.success, custom_id="add_user")
    async def add_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Nemáš oprávnění upravovat tento ticket!", ephemeral=True)
            return
        
        modal = AddUserModal(self.bot, interaction.channel.id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📋 Transcript", style=discord.ButtonStyle.secondary, custom_id="transcript")
    async def transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Zde by byla implementace generování transcriptu
        # Pro demonstraci pouze informativní zpráva
        await interaction.followup.send("📝 Funkce transcriptu bude implementována brzy!", ephemeral=True)

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
        # Zpracování tlačítek pro uzavřené tickety
        if interaction.data['custom_id'].startswith('delete_ticket_'):
            if not interaction.user.guild_permissions.manage_channels:
                await interaction.response.send_message("❌ Nemáš oprávnění smazat tento ticket!", ephemeral=True)
                return
            
            channel_id = int(interaction.data['custom_id'].split('_')[-1])
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                # Zálohovat zprávy před smazáním (mohl by být transcript)
                await interaction.response.send_message("🗑️ Mazání ticketu...", ephemeral=True)
                await asyncio.sleep(2)
                await channel.delete()
            else:
                await interaction.response.send_message("❌ Kanál již neexistuje!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))