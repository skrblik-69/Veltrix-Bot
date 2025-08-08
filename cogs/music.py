import discord
from discord.ext import commands
import asyncio
import logging
import aiohttp
import re
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class MusicQueue:
    """Třída pro správu hudební fronty"""
    
    def __init__(self):
        self.queue = []
        self.current = None
        self.volume = 0.5
        self.repeat = False
        self.loop = False
    
    def add(self, song):
        """Přidá píseň do fronty"""
        self.queue.append(song)
    
    def next(self):
        """Získá další píseň z fronty"""
        if self.loop and self.current:
            return self.current
        
        if self.queue:
            song = self.queue.pop(0)
            if self.repeat:
                self.queue.append(song)
            self.current = song
            return song
        return None
    
    def clear(self):
        """Vyčistí frontu"""
        self.queue.clear()
        self.current = None
    
    def shuffle(self):
        """Zamíchá frontu"""
        import random
        random.shuffle(self.queue)

class Music(commands.Cog):
    """Hudební přehrávač pro Discord"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # guild_id: MusicQueue
        self.voice_clients = {}  # guild_id: VoiceClient
    
    def get_queue(self, guild_id):
        """Získá frontu pro guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]
    
    async def join_voice_channel(self, ctx):
        """Připojí bota do hlasového kanálu"""
        if not ctx.author.voice:
            await ctx.send("❌ **Musíš být připojen do hlasového kanálu!**")
            return None
        
        channel = ctx.author.voice.channel
        
        if ctx.guild.id in self.voice_clients:
            voice_client = self.voice_clients[ctx.guild.id]
            if voice_client.channel != channel:
                await voice_client.move_to(channel)
        else:
            try:
                voice_client = await channel.connect()
                self.voice_clients[ctx.guild.id] = voice_client
            except discord.ClientException:
                await ctx.send("❌ **Bot je již připojen do jiného kanálu!**")
                return None
            except discord.Forbidden:
                await ctx.send("❌ **Bot nemá oprávnění k připojení do tohoto kanálu!**")
                return None
        
        return self.voice_clients[ctx.guild.id]
    
    async def search_youtube(self, query):
        """Vyhledá video na YouTube (zjednodušená verze)"""
        # V produkci by se použilo youtube-dl nebo yt-dlp
        # Pro demonstraci vrátíme mock data
        return {
            'url': f'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'title': f'🎵 {query}',
            'duration': '3:32',
            'thumbnail': 'https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg'
        }
    
    async def play_next(self, ctx):
        """Přehraje další píseň ve frontě"""
        queue = self.get_queue(ctx.guild.id)
        voice_client = self.voice_clients.get(ctx.guild.id)
        
        if not voice_client or not voice_client.is_connected():
            return
        
        next_song = queue.next()
        if not next_song:
            embed = discord.Embed(
                title="⏹️ Fronta je prázdná",
                description="Přidej další písně pomocí `!přehrát <název>`",
                color=0x95a5a6
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # V produkci by se zde použil skutečný audio source
            # source = discord.FFmpegPCMAudio(next_song['url'])
            # voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            
            # Pro demonstraci simulujeme přehrávání
            embed = discord.Embed(
                title="🎵 Nyní hraje",
                description=f"**{next_song['title']}**",
                color=0x3498db
            )
            embed.add_field(name="Délka", value=next_song['duration'], inline=True)
            embed.add_field(name="Ve frontě", value=f"{len(queue.queue)} písní", inline=True)
            embed.set_thumbnail(url=next_song['thumbnail'])
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při přehrávání: {e}")
            await ctx.send("❌ **Nastala chyba při přehrávání!**")
    
    @commands.hybrid_command(name='přehrát', aliases=['play', 'p'])
    async def play(self, ctx, *, dotaz: str):
        """Přehraje hudbu z YouTube"""
        voice_client = await self.join_voice_channel(ctx)
        if not voice_client:
            return
        
        # Zobrazení "hledání" zprávy
        search_msg = await ctx.send("🔍 **Hledám...**")
        
        try:
            # Vyhledání písně
            song_info = await self.search_youtube(dotaz)
            queue = self.get_queue(ctx.guild.id)
            
            # Kontrola délky fronty
            max_queue = self.bot.config['music']['max_queue_length']
            if len(queue.queue) >= max_queue:
                await search_msg.edit(content=f"❌ **Fronta je plná! Maximum: {max_queue} písní**")
                return
            
            # Přidání do fronty
            queue.add(song_info)
            
            # Pokud nic nehraje, spustí přehrávání
            if not voice_client.is_playing():
                await search_msg.delete()
                await self.play_next(ctx)
            else:
                embed = discord.Embed(
                    title="✅ Přidáno do fronty",
                    description=f"**{song_info['title']}**\n\n"
                               f"**Pozice ve frontě:** {len(queue.queue)}\n"
                               f"**Délka:** {song_info['duration']}",
                    color=0x2ecc71
                )
                embed.set_thumbnail(url=song_info['thumbnail'])
                await search_msg.edit(content=None, embed=embed)
                
        except Exception as e:
            logger.error(f"Chyba při hledání písně: {e}")
            await search_msg.edit(content="❌ **Nastala chyba při hledání písně!**")
    
    @commands.hybrid_command(name='pozastavit', aliases=['pause'])
    async def pause(self, ctx):
        """Pozastaví přehrávání"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            return await ctx.send("❌ **Nic se nepřehrává!**")
        
        voice_client.pause()
        
        embed = discord.Embed(
            title="⏸️ Přehrávání pozastaveno",
            description="Použij `!pokračovat` pro obnovení přehrávání",
            color=0xf39c12
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='pokračovat', aliases=['resume', 'continue'])
    async def resume(self, ctx):
        """Obnoví přehrávání"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        
        if not voice_client or not voice_client.is_paused():
            return await ctx.send("❌ **Přehrávání není pozastaveno!**")
        
        voice_client.resume()
        
        embed = discord.Embed(
            title="▶️ Přehrávání obnoveno",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='přeskočit', aliases=['skip', 's'])
    async def skip(self, ctx):
        """Přeskočí aktuální píseň"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        
        if not voice_client or not voice_client.is_playing():
            return await ctx.send("❌ **Nic se nepřehrává!**")
        
        voice_client.stop()  # Automaticky spustí další píseň
        
        embed = discord.Embed(
            title="⏭️ Píseň přeskočena",
            color=0x3498db
        )
        await ctx.send(embed=embed)
        
        # Přehrát další píseň
        await self.play_next(ctx)
    
    @commands.hybrid_command(name='zastavit', aliases=['stop'])
    async def stop(self, ctx):
        """Zastaví přehrávání a vyčistí frontu"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        
        if voice_client and voice_client.is_playing():
            voice_client.stop()
        
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        
        embed = discord.Embed(
            title="⏹️ Přehrávání zastaveno",
            description="Fronta byla vyčištěna",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='fronta', aliases=['queue', 'q'])
    async def queue_info(self, ctx):
        """Zobrazí aktuální frontu"""
        queue = self.get_queue(ctx.guild.id)
        
        if not queue.current and not queue.queue:
            return await ctx.send("❌ **Fronta je prázdná!**")
        
        embed = discord.Embed(
            title="🎵 Hudební fronta",
            color=0x3498db
        )
        
        if queue.current:
            embed.add_field(
                name="▶️ Nyní hraje",
                value=f"**{queue.current['title']}**",
                inline=False
            )
        
        if queue.queue:
            queue_list = ""
            for i, song in enumerate(queue.queue[:10], 1):
                queue_list += f"`{i}.` {song['title']}\n"
            
            if len(queue.queue) > 10:
                queue_list += f"... a dalších {len(queue.queue) - 10} písní"
            
            embed.add_field(
                name=f"📋 Ve frontě ({len(queue.queue)} písní)",
                value=queue_list,
                inline=False
            )
        
        embed.add_field(
            name="⚙️ Nastavení",
            value=f"**Opakování:** {'🔂 Zapnuto' if queue.repeat else '❌ Vypnuto'}\n"
                  f"**Smyčka:** {'🔁 Zapnuto' if queue.loop else '❌ Vypnuto'}\n"
                  f"**Hlasitost:** {int(queue.volume * 100)}%",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='zamíchat', aliases=['shuffle'])
    async def shuffle(self, ctx):
        """Zamíchá frontu"""
        queue = self.get_queue(ctx.guild.id)
        
        if len(queue.queue) < 2:
            return await ctx.send("❌ **Ve frontě musí být alespoň 2 písně pro zamíchání!**")
        
        queue.shuffle()
        
        embed = discord.Embed(
            title="🔀 Fronta zamíchána",
            description=f"Zamícháno {len(queue.queue)} písní",
            color=0x9b59b6
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='hlasitost', aliases=['volume', 'vol'])
    async def volume(self, ctx, hlasitost: int = None):
        """Nastaví nebo zobrazí hlasitost"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        queue = self.get_queue(ctx.guild.id)
        
        if hlasitost is None:
            embed = discord.Embed(
                title="🔊 Hlasitost",
                description=f"Aktuální hlasitost: **{int(queue.volume * 100)}%**",
                color=0x3498db
            )
            return await ctx.send(embed=embed)
        
        if hlasitost < 0 or hlasitost > 100:
            return await ctx.send("❌ **Hlasitost musí být mezi 0-100!**")
        
        queue.volume = hlasitost / 100
        
        if voice_client and hasattr(voice_client.source, 'volume'):
            voice_client.source.volume = queue.volume
        
        embed = discord.Embed(
            title="🔊 Hlasitost nastavena",
            description=f"Hlasitost nastavena na **{hlasitost}%**",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='odpojit', aliases=['disconnect', 'leave'])
    async def disconnect(self, ctx):
        """Odpojí bota z hlasového kanálu"""
        voice_client = self.voice_clients.get(ctx.guild.id)
        
        if not voice_client:
            return await ctx.send("❌ **Bot není připojen k žádnému hlasovému kanálu!**")
        
        # Vyčištění fronty a odpojení
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        
        await voice_client.disconnect()
        del self.voice_clients[ctx.guild.id]
        
        embed = discord.Embed(
            title="👋 Bot odpojen",
            description="Bot byl odpojen z hlasového kanálu",
            color=0x95a5a6
        )
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Automatické odpojení když jsou všichni uživatelé pryč"""
        if member == self.bot.user:
            return
        
        voice_client = self.voice_clients.get(member.guild.id)
        if not voice_client:
            return
        
        # Počkat moment a zkontrolovat kanál
        await asyncio.sleep(5)
        
        if voice_client.channel:
            members = [m for m in voice_client.channel.members if not m.bot]
            if not members:
                queue = self.get_queue(member.guild.id)
                queue.clear()
                await voice_client.disconnect()
                if member.guild.id in self.voice_clients:
                    del self.voice_clients[member.guild.id]

async def setup(bot):
    await bot.add_cog(Music(bot))
