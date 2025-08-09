import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

class TicketView(discord.ui.View):
    """View pro ticket systém s tlačítky"""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label='🆘Podpora🆘', style=discord.ButtonStyle.primary, custom_id='ticket_general')
    async def general_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, 'obecny', '🆘Podpora🆘')
    
    @discord.ui.button(label='☠️CK☠️', style=discord.ButtonStyle.danger, custom_id='ticket_bug')
    async def bug_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, 'bug', '')
    
    @discord.ui.button(label='💼Frakce💼', style=discord.ButtonStyle.success, custom_id='ticket_complaint')
    async def frakce_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, 'navr', '💼Frakce💼')
    
    @discord.ui.button(label='😾Stížnost😾', style=discord.ButtonStyle.secondary, custom_id='ticket_complaintstaff')
    async def complaint_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, 'stiznost', '😾Stížnost😾')
    
    async def _create_ticket(self, interaction: discord.Interaction, category: str, category_name: str):
        """Vytvoří nový ticket"""
        try:
            # Kontrola, zda uživatel již nemá otevřený ticket
            guild = interaction.guild
            existing_channel = discord.utils.get(
                guild.text_channels, 
                name=f"ticket-{interaction.user.name.lower()}-{interaction.user.discriminator}"
            )
            
            if existing_channel:
                return await interaction.response.send_message(
                    "❌ **Již máš otevřený ticket!** " + existing_channel.mention,
                    ephemeral=True
                )
            
            # Hledání kategorie pro tikety
            category_channel = discord.utils.get(
                guild.categories, 
                name="🆘 | PODPORA | 🆘"
            )
            
            if not category_channel:
                return await interaction.response.send_message(
                    "❌ **Kategorie '🆘 | PODPORA | 🆘' nebyla nalezena! Kontaktuj administrátora.**",
                    ephemeral=True
                )
            
            # Vytvoření ticket kanálu
            channel_name = f"ticket-{interaction.user.name.lower()}-{interaction.user.discriminator}"
            
            # Nastavení oprávnění
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True, attach_files=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True, manage_messages=True
                )
            }
            
            # Přidání support rolí pokud existují
            support_roles = []
            role_names = [name.strip() for name in self.bot.config['tickets']['support_role'].split(',')]
            
            for role_name in role_names:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    support_roles.append(role)
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True, send_messages=True
                    )
            
            ticket_channel = await guild.create_text_channel(
                channel_name,
                category=category_channel,
                overwrites=overwrites,
                reason=f"Ticket vytvořen uživatelem {interaction.user}"
            )
            
            # Uložení do databáze
            await self.bot.db.create_ticket(
                guild.id, ticket_channel.id, interaction.user.id, category
            )
            
            # Vytvoření ticket view pro uzavření
            close_view = TicketCloseView(self.bot)
            
            # Úvodní zpráva v ticketu
            embed = discord.Embed(
                title=f"🎫 {category_name}",
                description=f"Ahoj {interaction.user.mention}!\n\n"
                           "Tvůj ticket byl úspěšně vytvořen. Support team ti brzy odpoví.\n"
                           "Prosím popište svůj problém nebo dotaz co nejpodrobněji.\n\n"
                           "Pro uzavření ticketu použij tlačítko níže.",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id}")
            
            # Vytvoření mention stringu pro všechny support role
            support_mentions = " ".join([role.mention for role in support_roles]) if support_roles else ""
            
            await ticket_channel.send(
                content=f"{interaction.user.mention}" + (f" {support_mentions}" if support_mentions else ""),
                embed=embed,
                view=close_view
            )
            
            await interaction.response.send_message(
                f"✅ **Tvůj ticket byl vytvořen!** {ticket_channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Chyba při vytváření ticketu: {e}")
            await interaction.response.send_message(
                "❌ **Nastala chyba při vytváření ticketu!**",
                ephemeral=True
            )

class TicketCloseView(discord.ui.View):
    """View pro uzavření ticketu"""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label='🔒 Uzavřít ticket', style=discord.ButtonStyle.danger, custom_id='close_ticket')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Uzavře ticket"""
        # Kontrola oprávnění
        if not (interaction.user.guild_permissions.manage_channels or 
                interaction.channel.name.endswith(f"-{interaction.user.name.lower()}-{interaction.user.discriminator}")):
            return await interaction.response.send_message(
                "❌ **Nemáš oprávnění k uzavření tohoto ticketu!**",
                ephemeral=True
            )
        
        await interaction.response.send_message("🔒 **Uzavírám ticket...**")
        
        # Vytvoření transcript (zjednodušené)
        embed = discord.Embed(
            title="🔒 Ticket uzavřen",
            description=f"Ticket byl uzavřen uživatelem {interaction.user.mention}",
            color=0xe74c3c,
            timestamp=datetime.utcnow()
        )
        
        await interaction.followup.send(embed=embed)
        
        # Uložení do databáze
        await self.bot.db.close_ticket(interaction.channel.id, interaction.user.id)
        
        # Smazání kanálu po 5 sekundách
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket uzavřen uživatelem {interaction.user}")
        except:
            pass

class Tickets(commands.Cog):
    """Systém support tiketů"""
    
    def __init__(self, bot):
        self.bot = bot
        # Registrace persistent views
        bot.add_view(TicketView(bot))
        bot.add_view(TicketCloseView(bot))
    
    @commands.hybrid_command(name='ticket-panel', aliases=['ticket_setup'])
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx):
        """Vytvoří panel pro vytváření tiketů"""
        embed = discord.Embed(
            title="🎫 Support Tikety",
            description="Vítej v našem support systému!\n\n"
                       "Pokud potřebuješ pomoc, máš dotaz nebo chceš nahlásit problém, "
                       "klikni na příslušné tlačítko níže a vytvoř si ticket.\n\n"
                       "**Typy tiketů:**\n"
                       "📋 **Obecný dotaz** - Běžné otázky a dotazy\n"
                       "🐛 **Bug report** - Nahlášení chyb nebo problémů\n"
                       "💡 **Návrh** - Nápady na vylepšení\n"
                       "⚠️ **Stížnost** - Stížnosti na uživatele nebo obsah\n\n"
                       "**Pravidla:**\n"
                       "• Jeden ticket na uživatele\n"
                       "• Buď trpělivý, support team ti odpoví co nejdříve\n"
                       "• Neposkytuj citlivé informace ve veřejných kanálech",
            color=0x3498db
        )
        
        embed.set_footer(text="TrueBlue APP Support System")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        view = TicketView(self.bot)
        await ctx.send(embed=embed, view=view)
        
        # Smazání příkazu
        try:
            await ctx.message.delete()
        except:
            pass
    
    @commands.hybrid_command(name='uzavřit-ticket', aliases=['close'])
    async def force_close_ticket(self, ctx, důvod: str = "Nebyl uveden důvod"):
        """Násilně uzavře ticket (pouze moderátoři)"""
        if not ctx.channel.name.startswith('ticket-'):
            return await ctx.send("❌ **Tento příkaz lze použít pouze v ticket kanálech!**")
        
        if not ctx.author.guild_permissions.manage_channels:
            return await ctx.send("❌ **Nemáš oprávnění k uzavření ticketu!**")
        
        embed = discord.Embed(
            title="🔒 Ticket uzavřen moderátorem",
            description=f"**Moderátor:** {ctx.author.mention}\n**Důvod:** {důvod}",
            color=0xe74c3c,
            timestamp=datetime.utcnow()
        )
        
        await ctx.send(embed=embed)
        
        # Uložení do databáze
        await self.bot.db.close_ticket(ctx.channel.id, ctx.author.id)
        
        # Smazání kanálu po 5 sekundách
        await asyncio.sleep(5)
        try:
            await ctx.channel.delete(reason=f"Ticket uzavřen moderátorem {ctx.author}: {důvod}")
        except:
            pass
    
    @commands.hybrid_command(name='ticket-stats', aliases=['tikety'])
    @commands.has_permissions(manage_guild=True)
    async def ticket_stats(self, ctx):
        """Zobrazí statistiky tiketů"""
        try:
            # Zde by byla implementace statistik z databáze
            # Pro zjednodušení zobrazíme základní informace
            
            embed = discord.Embed(
                title="📊 Statistiky tiketů",
                description="Přehled ticket systému na serveru",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            
            # Počet otevřených tiketů
            ticket_channels = [
                channel for channel in ctx.guild.text_channels 
                if channel.name.startswith('ticket-')
            ]
            
            embed.add_field(
                name="📈 Aktuální stav",
                value=f"**Otevřené tikety:** {len(ticket_channels)}\n"
                      f"**Ticket kategorie:** 🆘 | PODPORA | 🆘\n"
                      f"**Support role:** {self.bot.config['tickets']['support_role']}",
                inline=True
            )
            
            embed.add_field(
                name="⚙️ Nastavení",
                value="• Automatické uzavírání po neaktivitě: ❌\n"
                      "• Transcript systém: ❌\n"
                      "• Hodnocení podpory: ❌",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při zobrazování ticket statistik: {e}")
            await ctx.send("❌ **Nastala chyba při načítání statistik!**")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
