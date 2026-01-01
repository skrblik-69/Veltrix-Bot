# Do existujícího tickets.py přidej tento dropdown systém:

class TicketDropdown(discord.ui.Select):
    def __init__(self, bot, category: str):
        self.bot = bot
        self.category = category
        
        # Definice možností podle kategorie
        options_map = {
            'rp_requests': [
                discord.SelectOption(label="🔫 Zbrojní průkaz", value="zbrojni", description="Když chceš legálně držet zbraň."),
                discord.SelectOption(label="🏘️ Pozemek", value="pozemek", description="Dům, bar nebo podnik v tvých rukou."),
                discord.SelectOption(label="🏢 Frakce", value="frakce", description="Žádost o vlastní organizaci či skupinu"),
                discord.SelectOption(label="💍 Svatba", value="svatba", description="Oficiální stvrzený svazek v RP."),
                discord.SelectOption(label="☠️ CK (Character Kill)", value="ck", description="Trvalé ukončení postavy.")
            ],
            'admin_requests': [
                discord.SelectOption(label="🔐 Unban", value="unban", description="Žádost o odbanování"),
                discord.SelectOption(label="📂 Úprava Frakce", value="uprava_frakce", description="Úprava existující frakce"),
                discord.SelectOption(label="🏘️ Majetek", value="majetek", description="Správa majetku"),
                discord.SelectOption(label="🎁 Giveaway (vyzvednutí)", value="giveaway", description="Vyzvednutí výhry")
            ],
            'career': [
                discord.SelectOption(label="⚡ Nábor - Game Staff", value="game_staff", description="Přidej se k Game Staffu"),
                discord.SelectOption(label="🛡️ Nábor - Moderator Team", value="moderator", description="Přidej se k Moderátorům"),
                discord.SelectOption(label="🛠️ Nábor - Discord Staff", value="discord_staff", description="Přidej se k Discord Staffu"),
                discord.SelectOption(label="🤝 Partnerství", value="partnerstvi", description="Návrh na spolupráci")
            ],
            'problems': [
                discord.SelectOption(label="❌ Stížnost na Člena", value="stiznost", description="Stížnost na člena (chování, atd...)"),
                discord.SelectOption(label="🔧 Problémy s Botem", value="bot_problem", description="Nahlásit problém s botem"),
                discord.SelectOption(label="🛠️ Jiný problém", value="jiny_problem", description="Jiný problém či dotaz")
            ]
        }
        
        options = options_map.get(category, [])
        placeholder_map = {
            'rp_requests': '🎭 | RP ŽÁDOSTI',
            'admin_requests': '🗝️┃Admin & Technické Žádosti',
            'career': '🚀 | Kariéra & Spolupráce',
            'problems': '📡 | Problémy & Reporty'
        }
        
        super().__init__(
            placeholder=placeholder_map.get(category, 'Vyber možnost'),
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.bot.cogs['Tickets']._create_ticket(interaction, self.values[0], self.placeholder)

class TicketPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # Přidání dropdownů
        self.add_item(TicketDropdown(bot, 'rp_requests'))
        self.add_item(TicketDropdown(bot, 'admin_requests'))
        self.add_item(TicketDropdown(bot, 'career'))
        self.add_item(TicketDropdown(bot, 'problems'))

# V Tickets cog přidej:
@app_commands.command(name="ticket_panel", description="Vytvoří panel pro všechny typy tiketů")
@app_commands.default_permissions(manage_guild=True)
async def ticket_panel_complete(self, interaction: discord.Interaction):
    """Vytvoření kompletního ticket panelu"""
    embed = discord.Embed(
        title="🎫 TrueBlue Support System",
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