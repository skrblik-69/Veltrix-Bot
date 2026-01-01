import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
from datetime import datetime
import logging
import asyncio
from typing import Optional
import shlex

logger = logging.getLogger(__name__)

class CitizenModal(discord.ui.Modal, title="📝 Vytvoření občanky"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.jmeno = discord.ui.TextInput(
            label="Celé jméno postavy",
            placeholder="Zadejte jméno a příjmení (např. Petr Pavel)",
            min_length=3,
            max_length=50,
            required=True
        )
        
        self.datum_narozeni = discord.ui.TextInput(
            label="Datum narození",
            placeholder="DD.MM.YYYY (např. 06.07.2000)",
            min_length=8,
            max_length=10,
            required=True
        )
        
        self.pohlavi = discord.ui.Select(
            placeholder="Vyber pohlaví",
            options=[
                discord.SelectOption(label="Muž", value="muž", emoji="👨"),
                discord.SelectOption(label="Žena", value="žena", emoji="👩"),
                discord.SelectOption(label="Jiné", value="jiné", emoji="⚧️")
            ]
        )
        
        self.adresa = discord.ui.TextInput(
            label="Adresa bydliště",
            placeholder="Město, stát (např. Arizona, USA)",
            min_length=3,
            max_length=100,
            required=True
        )
        
        self.add_item(self.jmeno)
        self.add_item(self.datum_narozeni)
        self.add_item(self.pohlavi)
        self.add_item(self.adresa)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validace data
            try:
                day, month, year = map(int, self.datum_narozeni.value.split('.'))
                birth_date = datetime(year, month, day)
                if birth_date > datetime.now():
                    raise ValueError
            except:
                await interaction.followup.send("❌ **Neplatné datum narození! Použij formát DD.MM.YYYY**", ephemeral=True)
                return
            
            # Uložení dat do JSON v mdt složce
            citizen_data = {
                'discord_id': interaction.user.id,
                'discord_name': str(interaction.user),
                'discord_display_name': interaction.user.display_name,
                'character_name': self.jmeno.value,
                'birth_date': self.datum_narozeni.value,
                'gender': self.pohlavi.values[0] if self.pohlavi.values else "neuvedeno",
                'address': self.adresa.value,
                'created_at': datetime.now().isoformat(),
                'citizen_id': f"C{interaction.user.id:08d}",
                'records': [],
                'fines': [],
                'warrants': []
            }
            
            # Uložení do mdt složky
            filename = f"{citizen_data['citizen_id']}.json"
            filepath = os.path.join(self.bot.mdt_data_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(citizen_data, f, ensure_ascii=False, indent=2)
            
            # Vytvoření kanálu na MDT serveru
            mdt_server = self.bot.get_guild(int(self.bot.config['mdt']['mdt_server_id']))
            if mdt_server:
                # Vytvoření kategorie A-Z
                first_letter = self.jmeno.value[0].upper()
                if self.bot.config['mdt']['alphabet_categories']:
                    category_name = f"{first_letter} - {first_letter}"
                else:
                    category_name = "📁 MDT Záznamy"
                
                # Najdi kategorii
                category = discord.utils.get(mdt_server.categories, name=category_name)
                if not category:
                    # Vytvoř kategorii
                    category = await mdt_server.create_category(category_name)
                
                # Vytvoř kanál pro občana
                channel_name = f"{self.jmeno.value.lower().replace(' ', '-')}"
                existing_channel = discord.utils.get(category.channels, name=channel_name)
                
                if not existing_channel:
                    # Vytvoření kanálu
                    overwrites = {
                        mdt_server.default_role: discord.PermissionOverwrite(read_messages=False),
                        mdt_server.me: discord.PermissionOverwrite(
                            read_messages=True, send_messages=True, manage_messages=True
                        )
                    }
                    
                    # Přidání police role
                    police_role_id = self.bot.config['mdt'].get('police_role_id')
                    if police_role_id:
                        police_role = mdt_server.get_role(int(police_role_id))
                        if police_role:
                            overwrites[police_role] = discord.PermissionOverwrite(
                                read_messages=True, send_messages=True
                            )
                    
                    # Přidání admin role
                    admin_role_id = self.bot.config['mdt'].get('admin_role_id')
                    if admin_role_id:
                        admin_role = mdt_server.get_role(int(admin_role_id))
                        if admin_role:
                            overwrites[admin_role] = discord.PermissionOverwrite(
                                read_messages=True, send_messages=True, manage_messages=True
                            )
                    
                    citizen_channel = await category.create_text_channel(
                        name=channel_name,
                        topic=f"📋 MDT: {self.jmeno.value} | ID: {citizen_data['citizen_id']} | Discord: {interaction.user.display_name}",
                        overwrites=overwrites,
                        reason=f"Vytvořeno přes občanku uživatelem {interaction.user}"
                    )
                    
                    # Vytvoř embed s informacemi
                    embed = discord.Embed(
                        title="📋 MDT Záznam - Občanský průkaz",
                        description=f"**ID:** `{citizen_data['citizen_id']}`",
                        color=0x3498db,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(name="👤 Jméno postavy", value=self.jmeno.value, inline=True)
                    embed.add_field(name="🎂 Datum narození", value=self.datum_narozeni.value, inline=True)
                    embed.add_field(name="⚤ Pohlaví", value=citizen_data['gender'], inline=True)
                    embed.add_field(name="🏠 Adresa", value=self.adresa.value, inline=False)
                    embed.add_field(name="💻 Discord", value=f"{interaction.user.mention}\n`{interaction.user}`", inline=True)
                    embed.add_field(name="📅 Vytvořeno", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
                    
                    embed.set_footer(text=f"Discord ID: {interaction.user.id}")
                    
                    message = await citizen_channel.send(embed=embed)
                    
                    # Připnutí zprávy
                    try:
                        await message.pin()
                    except:
                        pass
                    
                    # Přidání zprávy pro další záznamy
                    separator = await citizen_channel.send("─" * 50 + "\n**📝 Další záznamy:**")
                    
            # Přidání role občana na hlavním serveru
            main_server = self.bot.get_guild(int(self.bot.config['mdt']['main_server_id']))
            if main_server:
                member = main_server.get_member(interaction.user.id)
                if member:
                    citizen_role_id = self.bot.config['mdt'].get('citizen_role_id')
                    if citizen_role_id:
                        role = main_server.get_role(int(citizen_role_id))
                        if role and role not in member.roles:
                            await member.add_roles(role)
            
            # Odpověď uživateli
            embed = discord.Embed(
                title="✅ Občanka vytvořena!",
                description=f"**Jméno:** {self.jmeno.value}\n"
                          f"**Datum narození:** {self.datum_narozeni.value}\n"
                          f"**Pohlaví:** {citizen_data['gender']}\n"
                          f"**Adresa:** {self.adresa.value}\n"
                          f"**Občanské ID:** `{citizen_data['citizen_id']}`",
                color=0x2ecc71
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Chyba při vytváření občanky: {e}")
            await interaction.followup.send(f"❌ **Nastala chyba při vytváření občanky!**\n```{str(e)}```", ephemeral=True)

class MDTView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="📝 Vytvořit občanku", style=discord.ButtonStyle.primary, custom_id="mdt:create_citizen")
    async def create_citizen(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Vytvoření občanky"""
        # Kontrola, zda uživatel již má občanku
        citizen_id = f"C{interaction.user.id:08d}"
        filepath = os.path.join(self.bot.mdt_data_path, f"{citizen_id}.json")
        
        if os.path.exists(filepath):
            await interaction.response.send_message(
                "❌ **Již máš vytvořenou občanku!**",
                ephemeral=True
            )
            return
        
        await interaction.response.send_modal(CitizenModal(self.bot))

class MDT(commands.Cog):
    """MDT systém pro správu občanek a policejní databázi"""
    
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(MDTView(bot))
    
    @app_commands.command(name="obcanka", description="Vytvoření občanského průkazu")
    async def obcanka(self, interaction: discord.Interaction):
        """Vytvoření občanky"""
        view = MDTView(self.bot)
        await interaction.response.send_message(
            "📋 **Vytvoření občanského průkazu**\n\n"
            "Klikni na tlačítko níže pro vytvoření občanky.\n"
            "Po vytvoření bude automaticky vytvořen záznam v MDT systému.",
            view=view,
            ephemeral=True
        )
    
    @app_commands.command(name="mdt_panel", description="Vytvoření MDT panelu")
    @app_commands.default_permissions(administrator=True)
    async def mdt_panel(self, interaction: discord.Interaction):
        """Vytvoření panelu pro MDT systém"""
        embed = discord.Embed(
            title="📋 MDT Systém - Policejní databáze",
            description="**Systém pro správu občanek a policejních záznamů**\n\n"
                       "📝 **Vytvoření občanky** - Získej občanský průkaz\n"
                       "🔍 **Hledání záznamů** - Vyhledávání v databázi\n"
                       "🚨 **Policejní záznamy** - Přidání záznamů k občanům\n"
                       "💰 **Pokuty** - Evidence pokut a přestupků\n"
                       "⚖️ **Soudní řízení** - Soudní záznamy a rozsudky",
            color=0x3498db
        )
        
        embed.set_footer(text="TrueBlue APP - Policejní databáze")
        
        view = MDTView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="mdt_hledat", description="Hledání v MDT databázi")
    @app_commands.describe(jmeno="Jméno pro hledání")
    async def mdt_search(self, interaction: discord.Interaction, jmeno: str):
        """Hledání v MDT databázi"""
        await interaction.response.defer()
        
        results = []
        
        for filename in os.listdir(self.bot.mdt_data_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.bot.mdt_data_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if jmeno.lower() in data['character_name'].lower():
                        results.append(data)
        
        if results:
            embed = discord.Embed(
                title="🔍 Výsledky hledání v MDT",
                description=f"**Hledaný výraz:** `{jmeno}`\n**Nalezeno:** {len(results)} záznamů",
                color=0x3498db
            )
            
            for i, result in enumerate(results[:5], 1):
                embed.add_field(
                    name=f"{i}. {result['character_name']}",
                    value=f"**ID:** `{result['citizen_id']}`\n"
                          f"**Věk:** {self._calculate_age(result['birth_date'])}\n"
                          f"**Adresa:** {result['address']}",
                    inline=False
                )
            
            if len(results) > 5:
                embed.set_footer(text=f"Zobrazeno 5 z {len(results)} výsledků")
        else:
            embed = discord.Embed(
                title="🔍 Výsledky hledání v MDT",
                description=f"**Hledaný výraz:** `{jmeno}`\n**Nalezeno:** 0 záznamů",
                color=0xe74c3c
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="mdt_zaznam", description="Přidání záznamu k občanovi")
    @app_commands.describe(obcan_id="ID občana (např. C12345678)", typ="Typ záznamu", popis="Popis záznamu")
    @app_commands.choices(typ=[
        app_commands.Choice(name="🚨 Přestupek", value="offense"),
        app_commands.Choice(name="💰 Pokuta", value="fine"),
        app_commands.Choice(name="⚖️ Soudní řízení", value="court"),
        app_commands.Choice(name="✅ Pozitivní záznam", value="positive"),
        app_commands.Choice(name="⚠️ Varování", value="warning"),
        app_commands.Choice(name="🔫 Zbraně", value="weapons"),
        app_commands.Choice(name="🚗 Vozidlo", value="vehicle"),
        app_commands.Choice(name="🏠 Majetek", value="property")
    ])
    @app_commands.default_permissions(manage_messages=True)
    async def add_record(self, interaction: discord.Interaction, obcan_id: str, typ: str, popis: str):
        """Přidání záznamu k občanovi"""
        await interaction.response.defer()
        
        # Kontrola formátu ID
        if not obcan_id.startswith('C') or not obcan_id[1:].isdigit():
            await interaction.followup.send("❌ **Neplatný formát ID! Použij C následované čísly (např. C12345678)**", ephemeral=True)
            return
        
        filepath = os.path.join(self.bot.mdt_data_path, f"{obcan_id}.json")
        
        if not os.path.exists(filepath):
            await interaction.followup.send("❌ **Občan s tímto ID nebyl nalezen!**", ephemeral=True)
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            citizen_data = json.load(f)
        
        # Přidání záznamu
        if 'records' not in citizen_data:
            citizen_data['records'] = []
        
        record = {
            'id': len(citizen_data['records']) + 1,
            'type': typ,
            'description': popis,
            'added_by': interaction.user.id,
            'added_by_name': str(interaction.user),
            'added_at': datetime.now().isoformat(),
            'timestamp': int(datetime.now().timestamp())
        }
        
        citizen_data['records'].append(record)
        
        # Uložení
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(citizen_data, f, ensure_ascii=False, indent=2)
        
        # Oznámení na MDT serveru
        mdt_server = self.bot.get_guild(int(self.bot.config['mdt']['mdt_server_id']))
        if mdt_server:
            first_letter = citizen_data['character_name'][0].upper()
            if self.bot.config['mdt']['alphabet_categories']:
                category_name = f"{first_letter} - {first_letter}"
            else:
                category_name = "📁 MDT Záznamy"
            
            category = discord.utils.get(mdt_server.categories, name=category_name)
            if category:
                channel_name = f"{citizen_data['character_name'].lower().replace(' ', '-')}"
                channel = discord.utils.get(category.channels, name=channel_name)
                
                if channel:
                    type_emojis = {
                        'offense': '🚨',
                        'fine': '💰',
                        'court': '⚖️',
                        'positive': '✅',
                        'warning': '⚠️',
                        'weapons': '🔫',
                        'vehicle': '🚗',
                        'property': '🏠'
                    }
                    
                    type_names = {
                        'offense': 'Přestupek',
                        'fine': 'Pokuta',
                        'court': 'Soudní řízení',
                        'positive': 'Pozitivní záznam',
                        'warning': 'Varování',
                        'weapons': 'Zbraně',
                        'vehicle': 'Vozidlo',
                        'property': 'Majetek'
                    }
                    
                    embed = discord.Embed(
                        title=f"{type_emojis.get(typ, '📝')} {type_names.get(typ, 'Záznam')} #{record['id']}",
                        description=f"**Popis:** {popis}\n**Přidal:** {interaction.user.mention}\n**Datum:** <t:{record['timestamp']}:R>",
                        color=0x3498db,
                        timestamp=datetime.now()
                    )
                    
                    embed.set_footer(text=f"Občan: {citizen_data['character_name']} | ID: {citizen_data['citizen_id']}")
                    
                    await channel.send(embed=embed)
        
        # Odpověď
        embed = discord.Embed(
            title="✅ Záznam přidán",
            description=f"**Občan:** {citizen_data['character_name']}\n"
                       f"**ID:** `{citizen_data['citizen_id']}`\n"
                       f"**Typ:** {typ}\n"
                       f"**Popis:** {popis}",
            color=0x2ecc71
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="pokuta", description="Vystavení pokuty občanovi")
    @app_commands.describe(obcan_id="ID občana", castka="Částka pokuty", duvod="Důvod pokuty")
    @app_commands.default_permissions(manage_messages=True)
    async def issue_fine(self, interaction: discord.Interaction, obcan_id: str, castka: int, duvod: str):
        """Vystavení pokuty"""
        await interaction.response.defer()
        
        if not obcan_id.startswith('C') or not obcan_id[1:].isdigit():
            await interaction.followup.send("❌ **Neplatný formát ID!**", ephemeral=True)
            return
        
        filepath = os.path.join(self.bot.mdt_data_path, f"{obcan_id}.json")
        
        if not os.path.exists(filepath):
            await interaction.followup.send("❌ **Občan s tímto ID nebyl nalezen!**", ephemeral=True)
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            citizen_data = json.load(f)
        
        # Přidání pokuty
        if 'fines' not in citizen_data:
            citizen_data['fines'] = []
        
        fine = {
            'id': len(citizen_data['fines']) + 1,
            'amount': castka,
            'reason': duvod,
            'issued_by': interaction.user.id,
            'issued_by_name': str(interaction.user),
            'issued_at': datetime.now().isoformat(),
            'timestamp': int(datetime.now().timestamp()),
            'paid': False,
            'paid_at': None
        }
        
        citizen_data['fines'].append(fine)
        
        # Uložení
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(citizen_data, f, ensure_ascii=False, indent=2)
        
        # Oznámení na MDT serveru
        mdt_server = self.bot.get_guild(int(self.bot.config['mdt']['mdt_server_id']))
        if mdt_server:
            first_letter = citizen_data['character_name'][0].upper()
            if self.bot.config['mdt']['alphabet_categories']:
                category_name = f"{first_letter} - {first_letter}"
            else:
                category_name = "📁 MDT Záznamy"
            
            category = discord.utils.get(mdt_server.categories, name=category_name)
            if category:
                channel_name = f"{citizen_data['character_name'].lower().replace(' ', '-')}"
                channel = discord.utils.get(category.channels, name=channel_name)
                
                if channel:
                    embed = discord.Embed(
                        title=f"💰 Pokuta #{fine['id']}",
                        description=f"**Částka:** ${castka:,}\n**Důvod:** {duvod}\n**Vystavil:** {interaction.user.mention}\n**Datum:** <t:{fine['timestamp']}:R>",
                        color=0xe74c3c,
                        timestamp=datetime.now()
                    )
                    
                    embed.set_footer(text=f"Občan: {citizen_data['character_name']} | Status: Nezaplaceno")
                    
                    await channel.send(embed=embed)
        
        # Odpověď
        embed = discord.Embed(
            title="💰 Pokuta vystavena",
            description=f"**Občan:** {citizen_data['character_name']}\n"
                       f"**Částka:** ${castka:,}\n"
                       f"**Důvod:** {duvod}\n"
                       f"**ID pokuty:** #{fine['id']}",
            color=0xf39c12
        )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="vezeni", description="Zadržení občana do vězení")
    @app_commands.describe(obcan_id="ID občana", doba="Doba vězení (např. 1h, 30m, 2d)", duvod="Důvod zadržení")
    @app_commands.default_permissions(manage_messages=True)
    async def jail(self, interaction: discord.Interaction, obcan_id: str, doba: str, duvod: str):
        """Zadržení občana do vězení"""
        await interaction.response.defer()
        
        if not obcan_id.startswith('C') or not obcan_id[1:].isdigit():
            await interaction.followup.send("❌ **Neplatný formát ID!**", ephemeral=True)
            return
        
        filepath = os.path.join(self.bot.mdt_data_path, f"{obcan_id}.json")
        
        if not os.path.exists(filepath):
            await interaction.followup.send("❌ **Občan s tímto ID nebyl nalezen!**", ephemeral=True)
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            citizen_data = json.load(f)
        
        # Parsování času
        seconds = 0
        time_pattern = r'(\d+)([smhd])'
        matches = re.findall(time_pattern, doba.lower())
        
        if not matches:
            await interaction.followup.send("❌ **Neplatný formát času! Použij např. 1h, 30m, 2d**", ephemeral=True)
            return
        
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        for amount, unit in matches:
            seconds += int(amount) * time_units[unit]
        
        # Přidání záznamu o vězení
        if 'jail_records' not in citizen_data:
            citizen_data['jail_records'] = []
        
        jail_record = {
            'id': len(citizen_data['jail_records']) + 1,
            'duration': seconds,
            'duration_text': doba,
            'reason': duvod,
            'jailed_by': interaction.user.id,
            'jailed_by_name': str(interaction.user),
            'jailed_at': datetime.now().isoformat(),
            'timestamp': int(datetime.now().timestamp()),
            'released': False,
            'released_at': None
        }
        
        citizen_data['jail_records'].append(jail_record)
        
        # Uložení
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(citizen_data, f, ensure_ascii=False, indent=2)
        
        # Oznámení na MDT serveru
        mdt_server = self.bot.get_guild(int(self.bot.config['mdt']['mdt_server_id']))
        if mdt_server:
            first_letter = citizen_data['character_name'][0].upper()
            if self.bot.config['mdt']['alphabet_categories']:
                category_name = f"{first_letter} - {first_letter}"
            else:
                category_name = "📁 MDT Záznamy"
            
            category = discord.utils.get(mdt_server.categories, name=category_name)
            if category:
                channel_name = f"{citizen_data['character_name'].lower().replace(' ', '-')}"
                channel = discord.utils.get(category.channels, name=channel_name)
                
                if channel:
                    embed = discord.Embed(
                        title=f"🔒 Zadržení do vězení #{jail_record['id']}",
                        description=f"**Doba:** {doba}\n**Důvod:** {duvod}\n**Zadržel:** {interaction.user.mention}\n**Datum:** <t:{jail_record['timestamp']}:R>",
                        color=0x992d22,
                        timestamp=datetime.now()
                    )
                    
                    release_time = datetime.now().timestamp() + seconds
                    embed.add_field(name="🕐 Propuštění", value=f"<t:{int(release_time)}:R>", inline=True)
                    
                    embed.set_footer(text=f"Občan: {citizen_data['character_name']} | Status: Ve vězení")
                    
                    await channel.send(embed=embed)
        
        # Odpověď
        embed = discord.Embed(
            title="🔒 Občan zadržen do vězení",
            description=f"**Občan:** {citizen_data['character_name']}\n"
                       f"**Doba:** {doba}\n"
                       f"**Důvod:** {duvod}\n"
                       f"**ID zadržení:** #{jail_record['id']}",
            color=0x992d22
        )
        
        await interaction.followup.send(embed=embed)
    
    def _calculate_age(self, birth_date_str: str) -> str:
        """Vypočítá věk z data narození"""
        try:
            day, month, year = map(int, birth_date_str.split('.'))
            birth_date = datetime(year, month, day)
            today = datetime.now()
            
            age = today.year - birth_date.year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            return f"{age} let"
        except:
            return "Neznámý"
    
    @app_commands.command(name="mdt_info", description="Zobrazení informací o občanovi")
    @app_commands.describe(obcan_id="ID občana (např. C12345678)")
    async def mdt_info(self, interaction: discord.Interaction, obcan_id: str):
        """Zobrazení informací o občanovi"""
        await interaction.response.defer()
        
        if not obcan_id.startswith('C') or not obcan_id[1:].isdigit():
            await interaction.followup.send("❌ **Neplatný formát ID!**", ephemeral=True)
            return
        
        filepath = os.path.join(self.bot.mdt_data_path, f"{obcan_id}.json")
        
        if not os.path.exists(filepath):
            await interaction.followup.send("❌ **Občan s tímto ID nebyl nalezen!**", ephemeral=True)
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            citizen_data = json.load(f)
        
        # Vytvoření embedu
        embed = discord.Embed(
            title=f"📋 MDT Informace - {citizen_data['character_name']}",
            description=f"**ID:** `{citizen_data['citizen_id']}`",
            color=0x3498db
        )
        
        embed.add_field(name="👤 Jméno postavy", value=citizen_data['character_name'], inline=True)
        embed.add_field(name="🎂 Datum narození", value=citizen_data['birth_date'], inline=True)
        embed.add_field(name="⚤ Pohlaví", value=citizen_data['gender'], inline=True)
        embed.add_field(name="🏠 Adresa", value=citizen_data['address'], inline=False)
        embed.add_field(name="💻 Discord", value=f"{citizen_data['discord_name']}\n`{citizen_data['discord_id']}`", inline=True)
        embed.add_field(name="📅 Vytvořeno", value=f"<t:{int(datetime.fromisoformat(citizen_data['created_at']).timestamp())}:R>", inline=True)
        
        # Počty záznamů
        total_records = len(citizen_data.get('records', []))
        total_fines = len(citizen_data.get('fines', []))
        unpaid_fines = sum(1 for f in citizen_data.get('fines', []) if not f.get('paid', False))
        jail_records = len(citizen_data.get('jail_records', []))
        
        embed.add_field(
            name="📊 Statistiky",
            value=f"**Záznamy:** {total_records}\n**Pokuty:** {total_fines} ({unpaid_fines} nezaplaceno)\n**Vězení:** {jail_records}",
            inline=False
        )
        
        # Aktuální pokuty
        if unpaid_fines > 0:
            fines_text = ""
            for fine in citizen_data.get('fines', []):
                if not fine.get('paid', False):
                    fines_text += f"• #{fine['id']}: ${fine['amount']:,} - {fine['reason']}\n"
            
            if fines_text:
                embed.add_field(name="💰 Aktivní pokuty", value=fines_text[:1024], inline=False)
        
        # Poslední záznamy (max 3)
        recent_records = citizen_data.get('records', [])[-3:]
        if recent_records:
            records_text = ""
            for record in recent_records:
                type_names = {
                    'offense': '🚨 Přestupek',
                    'fine': '💰 Pokuta',
                    'court': '⚖️ Soud',
                    'positive': '✅ Pozitivní',
                    'warning': '⚠️ Varování'
                }
                records_text += f"• #{record['id']}: {type_names.get(record['type'], record['type'])} - {record['description'][:50]}...\n"
            
            if records_text:
                embed.add_field(name="📝 Poslední záznamy", value=records_text, inline=False)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MDT(bot))