import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

# ---------- Mapy ----------
CHANNEL_MAP = {
    "hledane_vozidlo": [1404114823813398652],
    "hledana_osoba": [1404114823813398651],
    "registrace_vozidla": [1407640363157688346],
    "registrace_zbrane": [1407640256882409472],
    "zatknuti": [1407640462600179772],
    "obcanka": [140764011319787939],
    "pokuta": [1408770577040281682]
}

CATEGORY_MAP = {
    "A": 1404114823813398656,
    "B": 1404114824090091684,
    "C": 1404114824090091686,
    "D": 1404114824090091690,
    "E": 1404114824090091691,
    "F": 1404114824090091692,
    "G": 1404114824253804667,
    "H": 1404114824253804668,
    "I": 1404114824253804669,
    "J": 1404114824253804670,
    "K": 1404114824253804673,
    "L": 1404114824253804675,
    "M": 1404114824446869558,
    "N": 1404114824446869560,
    "O": 1404114824446869561,
    "P": 1404114824446869562,
    "Q": 1404114824908247205,
    "R": 1404114824908247201,
    "S": 1404114824908247204,
    "T": 1404114824908247206,
    "U": 1404114824908247207,
    "V": 1404114824908247208,
    "W": 1404114824908247209,
    "X": 1404114825088471131,
    "Y": 1404114825088471132,
    "Z": 1404114825088471133
}

RP_GUILD_ID = 1407364800949784606
MDT_GUILD_ID = 1404114823465140326

def get_czech_time():
    """Vrátí aktuální čas v českém formátu"""
    cet = pytz.timezone('Europe/Prague')
    now = datetime.now(cet)
    return now.strftime("%d.%m.%Y %H:%M:%S")

# ---------- Modal ----------
class MDTModal(discord.ui.Modal):
    def __init__(self, typ, fields, title, color, channel_ids, bot):
        super().__init__(title=title)
        self.fields = fields
        self.color = color
        self.channel_ids = channel_ids
        self.bot = bot
        for field_name, prompt in fields:
            self.add_item(discord.ui.TextInput(
                label=field_name,
                placeholder=prompt,
                required=True,
                style=discord.TextStyle.short,
                max_length=100
            ))

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=self.title, color=self.color)
        for i, (field_name, _) in enumerate(self.fields):
            embed.add_field(name=field_name, value=self.children[i].value, inline=False)
        
        # Aktualizovaný footer podle požadavků
        embed.set_footer(
            text=f"Vytvořeno v {get_czech_time()} | Vyhlásil: {interaction.user.display_name} | Server: Veltrix"
        )

        sent = False
        for channel_id in self.channel_ids:
            channel = interaction.guild.get_channel(channel_id)
            if channel and channel.permissions_for(interaction.guild.get_member(self.bot.user.id)).send_messages:
                await channel.send(embed=embed)
                sent = True

        if sent:
            await interaction.response.send_message("✅ Embed byl odeslán.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Žádný kanál nenalezen nebo nemám práva.", ephemeral=True)

# ---------- MDT Panel ----------
class MDTPanel(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='🚗 Hledané vozidlo', style=discord.ButtonStyle.danger, custom_id="mdt:hledane_vozidlo")
    async def hledane_vozidlo(self, interaction: discord.Interaction, button: discord.ui.Button):
        fields = [
            ("🚙 Typ vozidla", "Zadej typ vozidla"),
            ("🏷️ Název vozidla", "Zadej název vozidla"),
            ("🔢 SPZ", "Zadej SPZ"),
            ("📍 Posledný vizuální kontakt", "Zadej poslední vizuální kontakt")
        ]
        modal = MDTModal("hledane_vozidlo", fields, "**Předloha na hledané vozidlo**", 0xff0000, CHANNEL_MAP["hledane_vozidlo"], self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='👤 Hledaná osoba', style=discord.ButtonStyle.danger, custom_id="mdt:hledana_osoba")
    async def hledana_osoba(self, interaction: discord.Interaction, button: discord.ui.Button):
        fields = [
            ("👨 Jméno", "Zadej jméno"),
            ("👨 Příjmení", "Zadej příjmení"),
            ("📅 Datum narození", "Zadej datum narození"),
            ("👁️ Poslední vidění", "Zadej poslední vidění"),
            ("📝 Popis osoby", "Zadej popis osoby")
        ]
        modal = MDTModal("hledana_osoba", fields, "**Předloha na hledanou osobu**", 0xff0000, CHANNEL_MAP["hledana_osoba"], self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='🚗 Registrace vozidla', style=discord.ButtonStyle.success, custom_id="mdt:registrace_vozidla")
    async def registrace_vozidla(self, interaction: discord.Interaction, button: discord.ui.Button):
        fields = [
            ("🚙 Typ auta", "Zadej typ auta"),
            ("🏷️ Model auta", "Zadej model auta"),
            ("🎨 Barva", "Zadej barvu"),
            ("🔢 SPZ", "Zadej SPZ")
        ]
        modal = MDTModal("registrace_vozidla", fields, "**Předloha na registraci vozidla**", 0x00ff00, CHANNEL_MAP["registrace_vozidla"], self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='🔫 Registrace zbraně', style=discord.ButtonStyle.secondary, custom_id="mdt:registrace_zbrane")
    async def registrace_zbrane(self, interaction: discord.Interaction, button: discord.ui.Button):
        fields = [
            ("🔫 Model zbraně", "Zadej model zbraně"),
            ("🔢 Sériové číslo", "Zadej sériové číslo")
        ]
        modal = MDTModal("registrace_zbrane", fields, "**Předloha na registraci zbraně**", 0x808080, CHANNEL_MAP["registrace_zbrane"], self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='🚔 Zatknutí', style=discord.ButtonStyle.primary, custom_id="mdt:zatknuti")
    async def zatknuti(self, interaction: discord.Interaction, button: discord.ui.Button):
        fields = [
            ("👨 Jméno", "Zadej jméno"),
            ("👨 Příjmení", "Zadej příjmení"),
            ("📅 Datum narození", "Zadej datum narození"),
            ("❓ Důvod", "Zadej důvod")
        ]
        modal = MDTModal("zatknuti", fields, "**Předloha na zatknutí**", 0x0099ff, CHANNEL_MAP["zatknuti"], self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='💸 Pokuta', style=discord.ButtonStyle.primary, custom_id="mdt:pokuta")
    async def pokuta(self, interaction: discord.Interaction, button: discord.ui.Button):
        fields = [
            ("👨 Jméno", "Zadej jméno"),
            ("👨 Příjmení", "Zadej příjmení"),
            ("📅 Datum narození", "Zadej datum narození"),
            ("❓ Důvod", "Zadej důvod pokuty"),
            ("💵 Částka", "Zadej částku")
        ]
        modal = MDTModal("pokuta", fields, "**Předloha na pokutu**", 0x0099ff, CHANNEL_MAP["pokuta"], self.bot)
        await interaction.response.send_modal(modal)

# ---------- Občanka Modal ----------
class ObcankaModal(discord.ui.Modal, title="🪪 Vytvořit občanku"):
    jmeno = discord.ui.TextInput(
        label="Jméno",
        placeholder="Zadejte jméno postavy",
        required=True,
        max_length=50
    )
    
    prijmeni = discord.ui.TextInput(
        label="Příjmení",
        placeholder="Zadejte příjmení postavy",
        required=True,
        max_length=50
    )
    
    datum_narozeni = discord.ui.TextInput(
        label="Datum narození",
        placeholder="DD.MM.YYYY",
        required=True,
        max_length=10
    )
    
    misto_narozeni = discord.ui.TextInput(
        label="Místo narození",
        placeholder="Zadejte místo narození",
        required=True,
        max_length=100
    )
    
    lore = discord.ui.TextInput(
        label="Lore",
        placeholder="Zadejte lore postavy",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.guild.id != RP_GUILD_ID:
            await interaction.followup.send("❌ Tento příkaz lze použít pouze na RP serveru.", ephemeral=True)
            return

        first_letter = self.prijmeni.value[0].upper()
        if first_letter not in CATEGORY_MAP:
            await interaction.followup.send(f"❌ Kategorie pro písmeno `{first_letter}` neexistuje na MDT serveru.", ephemeral=True)
            return

        mdt_guild = self.bot.get_guild(MDT_GUILD_ID)
        if not mdt_guild:
            await interaction.followup.send("❌ Nepodařilo se najít MDT server.", ephemeral=True)
            return

        category = mdt_guild.get_channel(CATEGORY_MAP[first_letter])
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send(f"❌ Kategorie pro `{first_letter}` nenalezena na MDT serveru.", ephemeral=True)
            return

        # Název kanálu
        channel_name = f"{self.jmeno.value.lower()}-{self.prijmeni.value.lower()}"
        channel = discord.utils.get(mdt_guild.channels, name=channel_name)
        if not channel:
            channel = await mdt_guild.create_text_channel(channel_name, category=category)

        # Embed občanky s aktualizovaným footrem
        embed = discord.Embed(title="🪪 Občanský průkaz", color=0x3498db)
        embed.add_field(name="👨 Jméno", value=self.jmeno.value, inline=True)
        embed.add_field(name="👨 Příjmení", value=self.prijmeni.value, inline=True)
        embed.add_field(name="📅 Datum narození", value=self.datum_narozeni.value, inline=True)
        embed.add_field(name="📍 Místo narození", value=self.misto_narozeni.value, inline=True)
        embed.add_field(name="📜 Lore", value=self.lore.value, inline=False)
        embed.set_footer(
            text=f"Vytvořeno v {get_czech_time()} | Vytvořil: {interaction.user.display_name} | Server: Veltrix"
        )
        await channel.send(embed=embed)

        # Nastavení přezdívky
        try:
            await interaction.user.edit(nick=f"{self.jmeno.value} {self.prijmeni.value} || Roblox Jméno")
        except discord.Forbidden:
            pass  # nedostatečná oprávnění

        # Potvrzení
        confirm_embed = discord.Embed(
            title="✅ Občanka vytvořena",
            description=f"Občanka pro **{self.jmeno.value} {self.prijmeni.value}** byla vytvořena na MDT serveru v kanálu {channel.mention}.",
            color=0x00ff00
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

# ---------- Cog ----------
class MDTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"✅ MDT Cog loaded!")

    @commands.Cog.listener()
    async def on_ready(self):
        # Přidání persistent view
        self.bot.add_view(MDTPanel(self.bot))
        print(f"✅ MDT Panel view registered!")

    @app_commands.command(name="mdt", description="Zobrazí MDT panel pro vytváření předloh")
    async def mdt_command(self, interaction: discord.Interaction):
        """Slash command pro MDT panel"""
        embed = discord.Embed(
            title="🚔 MDT Panel - Výběr předlohy",
            description="Klikněte na tlačítko pro výběr typu předlohy:",
            color=0x0099ff
        )
        embed.set_footer(text="Server: Veltrix")
        view = MDTPanel(self.bot)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="obcanka", description="Vytvoří občanku na MDT serveru")
    async def obcanka_slash(self, interaction: discord.Interaction):
        """Slash command pro vytvoření občanky"""
        modal = ObcankaModal(self.bot)
        await interaction.response.send_modal(modal)

    # Legacy prefix command pro kompatibilitu
    @commands.command(name="mdt")
    async def mdt_prefix(self, ctx):
        """Prefix command pro MDT panel"""
        embed = discord.Embed(
            title="🚔 MDT Panel - Výběr předlohy",
            description="Klikněte na tlačítko pro výběr typu předlohy:",
            color=0x0099ff
        )
        embed.set_footer(text="Server: Veltrix")
        view = MDTPanel(self.bot)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="obcanka")
    async def obcanka_prefix(self, ctx):
        """Prefix command pro vytvoření občanky (přesměruje na modal)"""
        modal = ObcankaModal(self.bot)
        await ctx.send("📝 Použijte prosím slash command `/obcanka` nebo klikněte zde:", view=discord.ui.View().add_item(
            discord.ui.Button(label="Vytvořit občanku", style=discord.ButtonStyle.primary, custom_id="open_obcanka_modal")
        ))

async def setup(bot):
    await bot.add_cog(MDTCog(bot))