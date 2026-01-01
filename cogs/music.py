import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import yt_dlp as youtube_dl
from collections import deque
import random

logger = logging.getLogger(__name__)

# Konfigurace yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': 'in_playlist',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Song:
    def __init__(self, source, requester):
        self.source = source
        self.requester = requester
        self.title = source.title
        self.url = source.url
        self.duration = source.duration
        self.thumbnail = source.thumbnail

class MusicQueue:
    def __init__(self):
        self._queue = deque()
        self.current = None
        self.volume = 0.5
        self.repeat = False
        self.loop = False
        self.shuffle = False

    def __len__(self):
        return len(self._queue)

    def add(self, song):
        self._queue.append(song)

    def next(self):
        if not self._queue:
            return None

        if self.loop and self.current:
            return Song(self.current.source, self.current.requester)

        if self.shuffle:
            song = random.choice(list(self._queue))
            self._queue.remove(song)
        else:
            song = self._queue.popleft()

        if self.repeat:
            self._queue.append(song)

        self.current = song
        return song

    def clear(self):
        self._queue.clear()
        self.current = None

    def get_queue_list(self):
        return list(self._queue)

    def remove(self, index):
        if 0 <= index < len(self._queue):
            return self._queue.remove(self._queue[index])
        return None

class MusicControls(discord.ui.View):
    def __init__(self, bot, timeout=180):
        super().__init__(timeout=timeout)
        self.bot = bot

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog('Music')
        await cog.pause(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog('Music')
        await cog.resume(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog('Music')
        await cog.skip(interaction)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary)
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog('Music')
        await cog.shuffle(interaction)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog('Music')
        await cog.stop(interaction)

class Music(commands.Cog):
    """Moderní hudební přehrávač pro Discord s YouTube podporou"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.voice_clients = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def ensure_voice(self, interaction: discord.Interaction):
        """Zajistí, že bot je v hlasovém kanálu"""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ **Nejsi připojen do hlasového kanálu!**", ephemeral=True)
            return None

        channel = interaction.user.voice.channel

        if interaction.guild.id in self.voice_clients:
            voice_client = self.voice_clients[interaction.guild.id]
            if voice_client.channel != channel:
                await voice_client.move_to(channel)
        else:
            try:
                voice_client = await channel.connect()
                self.voice_clients[interaction.guild.id] = voice_client
            except discord.ClientException:
                await interaction.response.send_message("❌ **Bot je již připojen do jiného kanálu!**", ephemeral=True)
                return None
            except discord.Forbidden:
                await interaction.response.send_message("❌ **Nemám oprávnění připojit se do tohoto kanálu!**", ephemeral=True)
                return None

        return self.voice_clients[interaction.guild.id]

    async def play_next(self, guild_id, interaction=None):
        """Přehraje další píseň z fronty"""
        queue = self.get_queue(guild_id)
        voice_client = self.voice_clients.get(guild_id)

        if not voice_client or not voice_client.is_connected():
            return

        if voice_client.is_playing():
            voice_client.stop()

        next_song = queue.next()
        if not next_song:
            if interaction:
                embed = discord.Embed(
                    title="⏹️ Hudba ukončena",
                    description="Fronta je prázdná. Přidej další písně pomocí `/přehrát`",
                    color=0x95a5a6
                )
                await interaction.channel.send(embed=embed)
            return

        try:
            voice_client.play(next_song.source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(guild_id), self.bot.loop
            ))
            
            voice_client.source.volume = queue.volume

            # Embed pro aktuálně hrající píseň
            embed = discord.Embed(
                title="🎵 Nyní hraje",
                description=f"[**{next_song.title}**]({next_song.url})",
                color=0x3498db
            )
            
            if next_song.duration:
                minutes, seconds = divmod(next_song.duration, 60)
                embed.add_field(name="Délka", value=f"{minutes}:{seconds:02d}", inline=True)
            
            embed.add_field(name="Přidal", value=next_song.requester.mention, inline=True)
            embed.add_field(name="Ve frontě", value=f"{len(queue)} písní", inline=True)
            
            if next_song.thumbnail:
                embed.set_thumbnail(url=next_song.thumbnail)
            
            view = MusicControls(self.bot)
            
            if interaction:
                await interaction.channel.send(embed=embed, view=view)
            else:
                channel = voice_client.channel
                # Najdi nějaký textový kanál ve stejné kategorii
                text_channel = discord.utils.get(channel.guild.text_channels, 
                                                category=channel.category, 
                                                position=0)
                if text_channel:
                    await text_channel.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Chyba při přehrávání: {e}")
            if interaction:
                await interaction.followup.send("❌ **Nastala chyba při přehrávání!**", ephemeral=True)

    @app_commands.command(name="přehrát", description="Přehraje hudbu z YouTube")
    @app_commands.describe(dotaz="Název písně nebo URL")
    async def play(self, interaction: discord.Interaction, dotaz: str):
        """Přehraje hudbu z YouTube"""
        await interaction.response.defer()
        
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        try:
            # Ověření fronty
            queue = self.get_queue(interaction.guild.id)
            max_queue = self.bot.config['music']['max_queue_length']
            
            if len(queue) >= max_queue:
                await interaction.followup.send(f"❌ **Fronta je plná! Maximum je {max_queue} písní.**", ephemeral=True)
                return

            # Získání informací o písni
            async with interaction.channel.typing():
                try:
                    data = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, lambda: ytdl.extract_info(f"ytsearch:{dotaz}", download=False)
                        ), timeout=10
                    )
                    
                    if 'entries' in data:
                        info = data['entries'][0]
                    else:
                        info = data
                    
                    # Vytvoření zdroje
                    source = await YTDLSource.from_url(info['webpage_url'], loop=self.bot.loop, stream=True)
                    song = Song(source, interaction.user)
                    
                    # Přidání do fronty
                    queue.add(song)
                    
                    # Embed pro přidanou píseň
                    embed = discord.Embed(
                        title="✅ Přidáno do fronty",
                        description=f"[**{song.title}**]({song.url})",
                        color=0x2ecc71
                    )
                    
                    if song.duration:
                        minutes, seconds = divmod(song.duration, 60)
                        embed.add_field(name="Délka", value=f"{minutes}:{seconds:02d}", inline=True)
                    
                    embed.add_field(name="Pozice ve frontě", value=f"{len(queue)}", inline=True)
                    embed.add_field(name="Přidal", value=interaction.user.mention, inline=True)
                    
                    if song.thumbnail:
                        embed.set_thumbnail(url=song.thumbnail)
                    
                    await interaction.followup.send(embed=embed)
                    
                    # Spustit přehrávání pokud nic nehraje
                    if not voice_client.is_playing():
                        await self.play_next(interaction.guild.id, interaction)
                        
                except asyncio.TimeoutError:
                    await interaction.followup.send("❌ **Vyhledávání trvalo příliš dlouho!**", ephemeral=True)
                except Exception as e:
                    logger.error(f"Chyba při vyhledávání: {e}")
                    await interaction.followup.send("❌ **Nepodařilo se najít tuto píseň!**", ephemeral=True)
                    
        except Exception as e:
            logger.error(f"Chyba v play příkazu: {e}")
            await interaction.followup.send("❌ **Nastala chyba při přehrávání hudby!**", ephemeral=True)

    @app_commands.command(name="pozastavit", description="Pozastaví přehrávání hudby")
    async def pause(self, interaction: discord.Interaction):
        """Pozastaví přehrávání hudby"""
        voice_client = self.voice_clients.get(interaction.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("❌ **Nic se momentálně nepřehrává!**", ephemeral=True)
            return
        
        if voice_client.is_paused():
            await interaction.response.send_message("❌ **Hudba je již pozastavena!**", ephemeral=True)
            return
        
        voice_client.pause()
        
        embed = discord.Embed(
            title="⏸️ Hudba pozastavena",
            description="Použij `/pokračovat` pro obnovení přehrávání",
            color=0xf39c12
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pokračovat", description="Obnoví přehrávání hudby")
    async def resume(self, interaction: discord.Interaction):
        """Obnoví přehrávání hudby"""
        voice_client = self.voice_clients.get(interaction.guild.id)
        
        if not voice_client or not voice_client.is_paused():
            await interaction.response.send_message("❌ **Hudba není pozastavena!**", ephemeral=True)
            return
        
        voice_client.resume()
        
        embed = discord.Embed(
            title="▶️ Hudba obnovena",
            color=0x2ecc71
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="přeskočit", description="Přeskočí aktuální píseň")
    @app_commands.describe(pozice="Pozice písně k přeskočení (volitelné)")
    async def skip(self, interaction: discord.Interaction, pozice: int = None):
        """Přeskočí píseň"""
        voice_client = self.voice_clients.get(interaction.guild.id)
        queue = self.get_queue(interaction.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message("❌ **Nic se momentálně nepřehrává!**", ephemeral=True)
            return
        
        if pozice and 1 <= pozice <= len(queue):
            # Přeskočit na konkrétní pozici
            removed_song = queue.remove(pozice - 1)
            if removed_song:
                embed = discord.Embed(
                    title="⏭️ Píseň odstraněna z fronty",
                    description=f"**{removed_song.title}**",
                    color=0xe74c3c
                )
                await interaction.response.send_message(embed=embed)
        else:
            # Přeskočit aktuální píseň
            voice_client.stop()
            
            embed = discord.Embed(
                title="⏭️ Píseň přeskočena",
                color=0x3498db
            )
            await interaction.response.send_message(embed=embed)
        
        # Přehrát další píseň
        await self.play_next(interaction.guild.id, interaction)

    @app_commands.command(name="zastavit", description="Zastaví hudbu a vyčistí frontu")
    async def stop(self, interaction: discord.Interaction):
        """Zastaví hudbu a vyčistí frontu"""
        voice_client = self.voice_clients.get(interaction.guild.id)
        queue = self.get_queue(interaction.guild.id)
        
        if voice_client and voice_client.is_playing():
            voice_client.stop()
        
        queue.clear()
        
        embed = discord.Embed(
            title="⏹️ Hudba zastavena",
            description="Fronta byla vyčištěna",
            color=0xe74c3c
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fronta", description="Zobrazí aktuální frontu písní")
    async def queue_info(self, interaction: discord.Interaction):
        """Zobrazí aktuální frontu"""
        queue = self.get_queue(interaction.guild.id)
        
        if not queue.current and len(queue) == 0:
            await interaction.response.send_message("❌ **Fronta je prázdná!**", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎵 Hudební fronta",
            color=0x3498db
        )
        
        # Aktuálně hrající
        if queue.current:
            embed.add_field(
                name="▶️ Nyní hraje",
                value=f"[**{queue.current.title}**]({queue.current.url})\n"
                      f"Přidal: {queue.current.requester.mention}",
                inline=False
            )
        
        # Fronta
        if len(queue) > 0:
            queue_list = ""
            for i, song in enumerate(queue.get_queue_list()[:10], 1):
                queue_list += f"`{i}.` [{song.title[:40]}]({song.url})\n"
            
            if len(queue) > 10:
                queue_list += f"\n... a dalších **{len(queue) - 10}** písní"
            
            embed.add_field(
                name=f"📋 Ve frontě ({len(queue)} písní)",
                value=queue_list,
                inline=False
            )
        
        # Nastavení
        settings_text = f"**🔂 Opakování:** {'Zapnuto' if queue.repeat else 'Vypnuto'}\n"
        settings_text += f"**🔁 Smyčka:** {'Zapnuto' if queue.loop else 'Vypnuto'}\n"
        settings_text += f"**🔀 Náhodně:** {'Zapnuto' if queue.shuffle else 'Vypnuto'}\n"
        settings_text += f"**🔊 Hlasitost:** {int(queue.volume * 100)}%"
        
        embed.add_field(name="⚙️ Nastavení", value=settings_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="zamíchat", description="Zamíchá frontu písní")
    async def shuffle_queue(self, interaction: discord.Interaction):
        """Zamíchá frontu"""
        queue = self.get_queue(interaction.guild.id)
        
        if len(queue) < 2:
            await interaction.response.send_message("❌ **Ve frontě musí být alespoň 2 písně!**", ephemeral=True)
            return
        
        queue.shuffle = not queue.shuffle
        
        embed = discord.Embed(
            title="🔀 Fronta zamíchána" if queue.shuffle else "🔀 Míchání vypnuto",
            description=f"Náhodné přehrávání je nyní **{'zapnuto' if queue.shuffle else 'vypnuto'}**",
            color=0x9b59b6
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hlasitost", description="Nastaví hlasitost přehrávání")
    @app_commands.describe(hlasitost="Hlasitost v % (1-100)")
    async def set_volume(self, interaction: discord.Interaction, hlasitost: int):
        """Nastaví hlasitost"""
        if hlasitost < 1 or hlasitost > 100:
            await interaction.response.send_message("❌ **Hlasitost musí být mezi 1-100%!**", ephemeral=True)
            return
        
        queue = self.get_queue(interaction.guild.id)
        voice_client = self.voice_clients.get(interaction.guild.id)
        
        queue.volume = hlasitost / 100
        
        if voice_client and voice_client.source:
            voice_client.source.volume = queue.volume
        
        embed = discord.Embed(
            title="🔊 Hlasitost nastavena",
            description=f"Hlasitost nastavena na **{hlasitost}%**",
            color=0x2ecc71
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="opakovat", description="Zapne/vypne opakování fronty")
    async def toggle_repeat(self, interaction: discord.Interaction):
        """Přepne opakování fronty"""
        queue = self.get_queue(interaction.guild.id)
        queue.repeat = not queue.repeat
        
        embed = discord.Embed(
            title="🔂 Opakování " + ("zapnuto" if queue.repeat else "vypnuto"),
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="smyčka", description="Zapne/vypne smyčku aktuální písně")
    async def toggle_loop(self, interaction: discord.Interaction):
        """Přepne smyčku aktuální písně"""
        queue = self.get_queue(interaction.guild.id)
        queue.loop = not queue.loop
        
        embed = discord.Embed(
            title="🔁 Smyčka " + ("zapnuta" if queue.loop else "vypnuta"),
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="odpojit", description="Odpojí bota z hlasového kanálu")
    async def disconnect(self, interaction: discord.Interaction):
        """Odpojí bota z hlasového kanálu"""
        voice_client = self.voice_clients.get(interaction.guild.id)
        
        if not voice_client:
            await interaction.response.send_message("❌ **Bot není připojen do žádného hlasového kanálu!**", ephemeral=True)
            return
        
        # Vyčištění fronty
        queue = self.get_queue(interaction.guild.id)
        queue.clear()
        
        # Odpojení
        await voice_client.disconnect()
        del self.voice_clients[interaction.guild.id]
        
        embed = discord.Embed(
            title="👋 Bot odpojen",
            description="Bot byl odpojen z hlasového kanálu",
            color=0x95a5a6
        )
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Automatické odpojení pokud jsou všichni uživatelé pryč"""
        if member.bot:
            return
        
        guild_id = member.guild.id
        voice_client = self.voice_clients.get(guild_id)
        
        if not voice_client:
            return
        
        # Počkat chvíli a zkontrolovat
        await asyncio.sleep(60)  # 1 minuta
        
        if voice_client.is_connected():
            channel = voice_client.channel
            # Spočítat pouze reálné uživatele (ne bota)
            human_members = [m for m in channel.members if not m.bot]
            
            if len(human_members) == 0:
                # Vyčistit frontu
                queue = self.get_queue(guild_id)
                queue.clear()
                
                # Odpojit
                await voice_client.disconnect()
                del self.voice_clients[guild_id]
                
                # Oznámení do nějakého textového kanálu
                try:
                    text_channel = discord.utils.get(channel.guild.text_channels, 
                                                    category=channel.category, 
                                                    position=0)
                    if text_channel:
                        embed = discord.Embed(
                            title="👋 Auto-odpojení",
                            description="Bot byl automaticky odpojen z hlasového kanálu, protože v něm nikdo nezůstal.",
                            color=0x95a5a6
                        )
                        await text_channel.send(embed=embed)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Music(bot))